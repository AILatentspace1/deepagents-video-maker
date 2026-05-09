"""Artifact gates / ratify checks."""

from __future__ import annotations

import re
import json
from pathlib import Path

from .models import RatifyCheck, RatifyResult


def ratify_script(
    script_path: str | Path,
    contract_path: str | Path,
) -> RatifyResult:
    script = Path(script_path)
    contract = Path(contract_path)
    checks: list[RatifyCheck] = []

    script_exists = script.exists() and script.is_file()
    checks.append(RatifyCheck("script_exists", script_exists, f"{script} exists={script_exists}"))
    contract_exists = contract.exists() and contract.is_file()
    checks.append(
        RatifyCheck("contract_exists", contract_exists, f"{contract} exists={contract_exists}")
    )
    if not (script_exists and contract_exists):
        return _result(checks)

    text = script.read_text(encoding="utf-8")
    scene_blocks = re.findall(r"(?ms)^##\s+Scene\b.*?(?=^##\s+Scene\b|\Z)", text)
    script_scene_count = len(scene_blocks)
    checks.append(
        RatifyCheck(
            "script_min_scenes",
            script_scene_count > 0,
            f"script_scene_count={script_scene_count}",
            {"script_scene_count": script_scene_count},
        )
    )

    try:
        data = json.loads(contract.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        checks.append(RatifyCheck("contract_parseable", False, f"json error: {exc}"))
        return _result(checks)
    checks.append(RatifyCheck("contract_parseable", True, "json parseable"))

    if not isinstance(data, dict):
        checks.append(
            RatifyCheck(
                "contract_is_object",
                False,
                f"script contract top-level must be object, got {type(data).__name__}",
            )
        )
        return _result(checks)
    checks.append(RatifyCheck("contract_is_object", True, "script contract top-level is object"))

    target = data.get("target_scene_count", {})
    min_scenes = int(target.get("min", 1)) if isinstance(target, dict) else 1
    max_scenes = int(target.get("max", 999)) if isinstance(target, dict) else 999
    checks.append(
        RatifyCheck(
            "scene_count_in_contract_range",
            min_scenes <= script_scene_count <= max_scenes,
            f"script_scene_count={script_scene_count}, expected={min_scenes}..{max_scenes}",
            {"script_scene_count": script_scene_count, "min": min_scenes, "max": max_scenes},
        )
    )

    type_re = re.compile(r"(?m)^type:\s*(\w+)")
    scene_types: list[str] = []
    for block in scene_blocks:
        type_match = type_re.search(block)
        scene_type = type_match.group(1) if type_match else ""
        if re.search(r"(?m)^Type:", block) or re.search(r"(?m)^Scene intent:", block):
            checks.append(
                RatifyCheck(
                    "scene_canonical_field_names",
                    False,
                    "scene fields must use canonical lowercase keys: type:, scene_intent:, content_brief:",
                )
            )
            return _result(checks)
        if not scene_type:
            checks.append(
                RatifyCheck("scene_type_required", False, "scene missing canonical type: field")
            )
            return _result(checks)
        if scene_type:
            scene_types.append(scene_type)
        if scene_type in {"narration", "data_card", "quote_card", "diagram_walkthrough"}:
            for required in ("scene_intent:", "content_brief:"):
                if required not in block:
                    checks.append(
                        RatifyCheck(
                            "scene_required_fields",
                            False,
                            f"{scene_type} scene missing {required}",
                        )
                    )
                    return _result(checks)
            for forbidden in ("layer_hint:", "beats:"):
                if forbidden in block:
                    checks.append(
                        RatifyCheck(
                            "scene_forbidden_fields",
                            False,
                            f"{scene_type} scene contains forbidden {forbidden}",
                        )
                    )
                    return _result(checks)
        if scene_type == "data_card":
            if "data_semantic:" not in block or not (
                re.search(r"(?m)^(items|source_items):", block)
            ):
                checks.append(
                    RatifyCheck(
                        "data_card_grounding",
                        False,
                        "data_card scene missing source-grounded data_semantic/items",
                    )
                )
                return _result(checks)
        if scene_type == "narration" and "data_semantic:" in block:
            checks.append(
                RatifyCheck(
                    "narration_no_data_semantic",
                    False,
                    "narration scene must not include data_semantic",
                )
            )
            return _result(checks)
    if _has_too_many_consecutive(scene_types, max_count=3):
        checks.append(
            RatifyCheck(
                "max_consecutive_same_type",
                False,
                "more than 3 consecutive scenes use the same type",
                {"scene_types": scene_types},
            )
        )
        return _result(checks)
    checks.append(RatifyCheck("max_consecutive_same_type", True, "scene type repetition OK"))
    checks.append(
        RatifyCheck("script_business_rules", True, "scene_intent/content_brief/no-layer_hint OK")
    )
    return _result(checks)


def ratify_source_manifest(manifest_path: str | Path, *, source: str) -> RatifyResult:
    path = Path(manifest_path)
    checks: list[RatifyCheck] = []
    exists = path.exists() and path.is_file()
    checks.append(RatifyCheck("manifest_exists", exists, f"{path} exists={exists}"))
    if not exists:
        return _result(checks)

    text = path.read_text(encoding="utf-8")
    checks.append(RatifyCheck("has_title", "# Source Manifest" in text, "has # Source Manifest"))
    checks.append(RatifyCheck("has_items", "## Items" in text, "has ## Items"))
    checks.append(RatifyCheck("has_path", "- path:" in text, "has at least one path item"))
    error_items = re.findall(r"(?m)^- note:\s*ERROR:\s*(.+)$", text)
    checks.append(
        RatifyCheck(
            "has_no_error_items",
            not error_items,
            "; ".join(error_items) if error_items else "no error items",
            {"error_items": error_items},
        )
    )
    if source == "websearch":
        checks.append(RatifyCheck("has_url", bool(re.search(r"https?://", text)), "websearch requires URL"))
    if source in {"folder", "local-file", "local_file"}:
        paths = [
            match.strip()
            for match in re.findall(r"(?m)^- path:\s*(.+)$", text)
            if match.strip() and not re.match(r"https?://", match.strip())
        ]
        missing = [item for item in paths if not Path(item).exists()]
        checks.append(
            RatifyCheck(
                "local_paths_exist",
                not missing,
                f"missing local paths: {missing}" if missing else "all local paths exist",
                {"missing": missing},
            )
        )
    return _result(checks)


def _has_too_many_consecutive(values: list[str], *, max_count: int) -> bool:
    previous = None
    count = 0
    for value in values:
        if value == previous:
            count += 1
        else:
            previous = value
            count = 1
        if count > max_count:
            return True
    return False


def _result(checks: list[RatifyCheck]) -> RatifyResult:
    issues = [check.message for check in checks if not check.passed]
    passed = not issues
    return RatifyResult(
        passed=passed,
        checks=checks,
        issues=issues,
        next_action="complete_milestone" if passed else "retry_milestone",
    )

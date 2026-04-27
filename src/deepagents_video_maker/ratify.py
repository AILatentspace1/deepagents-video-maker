"""Artifact gates / ratify checks."""

from __future__ import annotations

import re
import json
from pathlib import Path

from .models import RatifyCheck, RatifyResult


def ratify_research(
    research_path: str | Path,
    *,
    source: str,
    min_chars: int = 800,
    min_headings: int = 3,
) -> RatifyResult:
    path = Path(research_path)
    checks: list[RatifyCheck] = []

    exists = path.exists() and path.is_file()
    checks.append(RatifyCheck("exists", exists, f"{path} exists={exists}"))
    if not exists:
        return _result(checks)

    content = path.read_text(encoding="utf-8")
    char_count = len(content)
    heading_count = len(re.findall(r"(?m)^##\s+", content))
    url_count = len(re.findall(r"https?://", content))

    checks.append(
        RatifyCheck(
            "min_chars",
            char_count > min_chars,
            f"char_count={char_count}, required>{min_chars}",
            {"char_count": char_count},
        )
    )
    checks.append(
        RatifyCheck(
            "min_headings",
            heading_count >= min_headings,
            f"heading_count={heading_count}, required>={min_headings}",
            {"heading_count": heading_count},
        )
    )
    # Accept both "local-file" and "local_file" spellings
    if source not in ("local-file", "local_file"):
        checks.append(
            RatifyCheck(
                "min_urls",
                url_count >= 1,
                "non-local-file research requires at least one URL",
                {"url_count": url_count},
            )
        )
    else:
        checks.append(
            RatifyCheck(
                "min_urls",
                True,
                "local-file source skips URL requirement",
                {"url_count": url_count, "skipped": True},
            )
        )
    return _result(checks)


def ratify_script(
    script_path: str | Path,
    manifest_path: str | Path,
) -> RatifyResult:
    script = Path(script_path)
    manifest = Path(manifest_path)
    checks: list[RatifyCheck] = []

    script_exists = script.exists() and script.is_file()
    checks.append(RatifyCheck("script_exists", script_exists, f"{script} exists={script_exists}"))
    manifest_exists = manifest.exists() and manifest.is_file()
    checks.append(
        RatifyCheck("manifest_exists", manifest_exists, f"{manifest} exists={manifest_exists}")
    )
    if not (script_exists and manifest_exists):
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
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        checks.append(RatifyCheck("manifest_parseable", False, f"json error: {exc}"))
        return _result(checks)
    checks.append(RatifyCheck("manifest_parseable", True, "json parseable"))

    if not isinstance(data, dict):
        checks.append(
            RatifyCheck(
                "manifest_is_object",
                False,
                f"manifest top-level must be object, got {type(data).__name__}",
            )
        )
        return _result(checks)
    checks.append(RatifyCheck("manifest_is_object", True, "manifest top-level is object"))

    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        checks.append(RatifyCheck("manifest_has_scenes", False, "manifest.scenes missing/empty"))
        return _result(checks)
    checks.append(RatifyCheck("manifest_has_scenes", True, f"manifest_scene_count={len(scenes)}"))

    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            checks.append(RatifyCheck(f"scene_{idx}_is_object", False, f"scene[{idx}] not an object"))
            return _result(checks)
        for field in ("id", "narration", "duration"):
            if field not in scene:
                checks.append(
                    RatifyCheck(
                        f"manifest_scene_{idx}_field_{field}",
                        False,
                        f"scene[{idx}] missing field={field}",
                    )
                )
                return _result(checks)
        duration = scene.get("duration")
        if not isinstance(duration, (int, float)) or duration <= 0:
            checks.append(
                RatifyCheck(
                    f"scene_{idx}_duration",
                    False,
                    f"scene[{idx}].duration must be positive number, got {duration!r}",
                )
            )
            return _result(checks)

    ids = [scene.get("id") for scene in scenes]
    if len(set(ids)) != len(ids):
        checks.append(RatifyCheck("scene_ids_unique", False, f"duplicate scene ids: {ids}"))
        return _result(checks)
    checks.append(RatifyCheck("scene_ids_unique", True, "all scene ids unique"))

    checks.append(
        RatifyCheck(
            "scene_count_match",
            len(scenes) == script_scene_count,
            f"manifest={len(scenes)} script={script_scene_count}",
            {"manifest_scene_count": len(scenes), "script_scene_count": script_scene_count},
        )
    )

    type_re = re.compile(r"(?m)^type:\s*(\w+)")
    for block in scene_blocks:
        type_match = type_re.search(block)
        scene_type = type_match.group(1) if type_match else ""
        if scene_type in {"narration", "data_card", "quote_card"}:
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
    checks.append(
        RatifyCheck("script_business_rules", True, "scene_intent/content_brief/no-layer_hint OK")
    )
    return _result(checks)


def _result(checks: list[RatifyCheck]) -> RatifyResult:
    issues = [check.message for check in checks if not check.passed]
    passed = not issues
    return RatifyResult(
        passed=passed,
        checks=checks,
        issues=issues,
        next_action="complete_milestone" if passed else "retry_milestone",
    )

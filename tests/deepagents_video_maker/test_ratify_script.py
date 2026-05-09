from pathlib import Path
import json

from deepagents_video_maker.ratify import ratify_script, ratify_source_manifest


def _write_script(tmp_path: Path, scene_count=1) -> Path:
    lines = []
    for i in range(1, scene_count + 1):
        lines.append(
            f"## Scene {i}\n"
            "type: narration\n"
            "narration: x\n"
            "scene_intent: hook\n"
            "content_brief: brief\n"
        )
    path = tmp_path / "script.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_contract(tmp_path: Path, min_scenes=1, max_scenes=3) -> Path:
    path = tmp_path / "script-contract.json"
    path.write_text(
        json.dumps({"version": 2, "target_scene_count": {"min": min_scenes, "max": max_scenes}}),
        encoding="utf-8",
    )
    return path


def test_ratify_script_passes_with_script_and_contract(tmp_path):
    result = ratify_script(_write_script(tmp_path, 2), _write_contract(tmp_path, 1, 3))
    assert result.passed


def test_ratify_script_fails_when_scene_count_outside_contract(tmp_path):
    result = ratify_script(_write_script(tmp_path, 4), _write_contract(tmp_path, 1, 3))
    assert not result.passed
    assert any(c.id == "scene_count_in_contract_range" and not c.passed for c in result.checks)


def test_ratify_script_fails_when_contract_is_list(tmp_path):
    bad = tmp_path / "script-contract.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    result = ratify_script(_write_script(tmp_path), bad)
    assert not result.passed
    assert any(c.id == "contract_is_object" and not c.passed for c in result.checks)


def test_ratify_script_fails_when_contract_missing(tmp_path):
    result = ratify_script(_write_script(tmp_path), tmp_path / "missing-contract.json")
    assert not result.passed
    assert any(c.id == "contract_exists" and not c.passed for c in result.checks)


def test_ratify_script_rejects_forbidden_layer_hint(tmp_path):
    script = tmp_path / "script.md"
    script.write_text(
        "## Scene 1\n"
        "type: narration\n"
        "narration: hi\n"
        "scene_intent: hook\n"
        "content_brief: x\n"
        "layer_hint: bad\n",
        encoding="utf-8",
    )
    result = ratify_script(script, _write_contract(tmp_path))
    assert not result.passed
    assert any(c.id == "scene_forbidden_fields" and not c.passed for c in result.checks)


def test_ratify_script_rejects_noncanonical_title_case_fields(tmp_path):
    script = tmp_path / "script.md"
    script.write_text(
        "## Scene 1\n"
        "Type: narration\n"
        "Scene intent: hook\n"
        "Narration: hi\n",
        encoding="utf-8",
    )

    result = ratify_script(script, _write_contract(tmp_path))

    assert not result.passed
    assert any(c.id == "scene_canonical_field_names" and not c.passed for c in result.checks)


def test_ratify_script_requires_content_brief_for_diagram_walkthrough(tmp_path):
    script = tmp_path / "script.md"
    script.write_text(
        "## Scene 1\n"
        "type: diagram_walkthrough\n"
        "scene_intent: architecture\n",
        encoding="utf-8",
    )

    result = ratify_script(script, _write_contract(tmp_path))

    assert not result.passed
    assert any(c.id == "scene_required_fields" and not c.passed for c in result.checks)


def test_ratify_script_rejects_too_many_consecutive_same_scene_types(tmp_path):
    script = tmp_path / "script.md"
    script.write_text(
        "\n".join(
            [
                "## Scene 1\ntype: narration\nscene_intent: hook\ncontent_brief: one",
                "## Scene 2\ntype: narration\nscene_intent: setup\ncontent_brief: two",
                "## Scene 3\ntype: narration\nscene_intent: development\ncontent_brief: three",
                "## Scene 4\ntype: narration\nscene_intent: climax\ncontent_brief: four",
            ]
        ),
        encoding="utf-8",
    )

    result = ratify_script(script, _write_contract(tmp_path, 1, 8))

    assert not result.passed
    assert any(c.id == "max_consecutive_same_type" and not c.passed for c in result.checks)


def test_ratify_script_rejects_data_card_without_grounded_data_semantic(tmp_path):
    script = tmp_path / "script.md"
    script.write_text(
        "## Scene 1\n"
        "type: data_card\n"
        "scene_intent: show metric\n"
        "content_brief: metric brief\n",
        encoding="utf-8",
    )

    result = ratify_script(script, _write_contract(tmp_path))

    assert not result.passed
    assert any(c.id == "data_card_grounding" and not c.passed for c in result.checks)


def test_ratify_script_rejects_narration_with_data_semantic(tmp_path):
    script = tmp_path / "script.md"
    script.write_text(
        "## Scene 1\n"
        "type: narration\n"
        "scene_intent: hook\n"
        "content_brief: intro\n"
        "data_semantic: should not be here\n",
        encoding="utf-8",
    )

    result = ratify_script(script, _write_contract(tmp_path))

    assert not result.passed
    assert any(c.id == "narration_no_data_semantic" and not c.passed for c in result.checks)


def test_ratify_source_manifest_requires_title_items_and_path(tmp_path):
    brief = tmp_path / "brief.md"
    brief.write_text("# Brief\n", encoding="utf-8")
    manifest = tmp_path / "source-manifest.md"
    manifest.write_text(
        f"# Source Manifest\n\n## Items\n- path: {brief}\n",
        encoding="utf-8",
    )
    assert ratify_source_manifest(manifest, source="folder").passed

    bad = tmp_path / "bad.md"
    bad.write_text("# Source Manifest\n", encoding="utf-8")
    assert not ratify_source_manifest(bad, source="folder").passed


def test_ratify_source_manifest_requires_existing_local_paths(tmp_path):
    existing = tmp_path / "brief.md"
    existing.write_text("# Brief\n", encoding="utf-8")
    manifest = tmp_path / "source-manifest.md"
    manifest.write_text(
        "# Source Manifest\n\n## Items\n"
        f"- path: {existing}\n"
        "- path: {}\n".format(tmp_path / "missing.md"),
        encoding="utf-8",
    )

    result = ratify_source_manifest(manifest, source="folder")

    assert not result.passed
    assert any(c.id == "local_paths_exist" and not c.passed for c in result.checks)

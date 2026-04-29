from pathlib import Path
import json

from deepagents_video_maker.ratify import ratify_script


def _write_script(tmp_path: Path, scene_count: int = 3) -> Path:
    text = "# Script\n\n"
    for i in range(1, scene_count + 1):
        text += (
            f"## Scene {i}\n"
            f"type: narration\n"
            f"narration: hello scene {i}\n"
            f"scene_intent: setup\n"
            f"content_brief: brief {i}\n\n"
        )
    path = tmp_path / "script.md"
    path.write_text(text, encoding="utf-8")
    return path


def _write_manifest(tmp_path: Path, scene_count: int = 3) -> Path:
    data = {
        "scenes": [
            {"id": f"scene-{i}", "narration": f"hello scene {i}", "duration": 6}
            for i in range(1, scene_count + 1)
        ]
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_ratify_script_passes_when_complete(tmp_path):
    script = _write_script(tmp_path, scene_count=3)
    manifest = _write_manifest(tmp_path, scene_count=3)
    result = ratify_script(script, manifest)
    assert result.passed, result.issues


def test_ratify_script_fails_when_script_missing(tmp_path):
    manifest = _write_manifest(tmp_path)
    result = ratify_script(tmp_path / "missing.md", manifest)
    assert not result.passed
    assert any("exists" in c.id and not c.passed for c in result.checks)


def test_ratify_script_fails_when_manifest_invalid(tmp_path):
    script = _write_script(tmp_path)
    bad = tmp_path / "manifest.json"
    bad.write_text("not json", encoding="utf-8")
    result = ratify_script(script, bad)
    assert not result.passed


def test_ratify_script_fails_when_scene_count_mismatches(tmp_path):
    script = _write_script(tmp_path, scene_count=3)
    manifest = _write_manifest(tmp_path, scene_count=2)
    result = ratify_script(script, manifest)
    assert not result.passed


def test_ratify_script_fails_when_manifest_is_list(tmp_path):
    script = _write_script(tmp_path)
    bad = tmp_path / "manifest.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    result = ratify_script(script, bad)
    assert not result.passed
    assert any(c.id == "manifest_is_object" and not c.passed for c in result.checks)


def test_ratify_script_fails_when_duration_invalid(tmp_path):
    script = _write_script(tmp_path, scene_count=1)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"scenes": [{"id": "s1", "narration": "x", "duration": -1}]}), encoding="utf-8")
    result = ratify_script(script, manifest)
    assert not result.passed


def test_ratify_script_fails_when_scene_missing_intent(tmp_path):
    script = tmp_path / "script.md"
    script.write_text("## Scene 1\ntype: narration\nnarration: x\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"scenes": [{"id": "s1", "narration": "x", "duration": 5}]}), encoding="utf-8")
    result = ratify_script(script, manifest)
    assert not result.passed


def test_ratify_script_fails_when_scene_uses_layer_hint(tmp_path):
    script = tmp_path / "script.md"
    script.write_text(
        "## Scene 1\ntype: narration\nnarration: x\nscene_intent: hook\ncontent_brief: y\nlayer_hint: bg\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"scenes": [{"id": "s1", "narration": "x", "duration": 5}]}), encoding="utf-8")
    result = ratify_script(script, manifest)
    assert not result.passed


def test_ratify_script_fails_when_manifest_missing(tmp_path):
    script = _write_script(tmp_path)
    result = ratify_script(script, tmp_path / "missing_manifest.json")
    assert not result.passed
    assert any("manifest_exists" == c.id and not c.passed for c in result.checks)


def test_ratify_script_fails_when_scene_ids_duplicate(tmp_path):
    script = _write_script(tmp_path, scene_count=2)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"scenes": [
            {"id": "scene-dup", "narration": "a", "duration": 5},
            {"id": "scene-dup", "narration": "b", "duration": 5},
        ]}),
        encoding="utf-8",
    )
    result = ratify_script(script, manifest)
    assert not result.passed
    assert any(c.id == "scene_ids_unique" and not c.passed for c in result.checks)

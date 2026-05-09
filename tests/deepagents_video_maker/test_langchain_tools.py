from pathlib import Path

from deepagents_video_maker.langchain_tools import (
    vm_build_remotion_task,
    vm_build_publish_readiness_report,
    vm_build_scriptwriter_task,
    vm_init_video_session,
    vm_package_render_output,
    vm_ratify_build_scenes,
    vm_ratify_render_package,
    vm_render_remotion_project,
    vm_parse_video_request,
    vm_ratify_script,
    vm_ratify_source_intake,
    vm_start_build_scenes,
    vm_start_render_package,
    vm_start_script,
    vm_start_source_intake,
)


PROMPT = r'''
topic=LLM video benchmark
source=folder
source_folder=E:\workspace\video-maker-v2
duration=3-5min
style=professional
aspectRatio=16:9
'''


def _invoke(tool, *args, **kwargs):
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs if kwargs else dict(args=args))
    return tool(*args, **kwargs)


def _make_source_folder(tmp_path: Path) -> Path:
    source = tmp_path / "v2-source"
    source.mkdir()
    (source / "brief.md").write_text("# Brief\nUse these facts.\n", encoding="utf-8")
    (source / "stats.csv").write_text("model,score\nA,9\n", encoding="utf-8")
    return source


def test_vm_parse_video_request_returns_v2_jsonable_goal():
    result = _invoke(vm_parse_video_request, prompt=PROMPT)

    assert result["topic"] == "LLM video benchmark"
    assert result["source"] == "folder"
    assert result["source_folder"] == r"E:\workspace\video-maker-v2"
    assert result["eval_mode"] == "none"


def test_source_intake_tool_sequence_creates_manifest_without_research(tmp_path: Path):
    source = _make_source_folder(tmp_path)
    init = _invoke(
        vm_init_video_session,
        topic="LLM video benchmark",
        source="folder",
        source_folder=str(source),
        duration="3-5min",
        style="professional",
        aspect_ratio="16:9",
        root_dir=str(tmp_path),
        timestamp="20260425-120000",
    )
    output_dir = init["output_dir"]
    assert init["video_maker"]["outputDir"] == output_dir
    assert init["video_maker"]["milestones"][0]["id"] == "source_intake"

    started = _invoke(vm_start_source_intake, output_dir=output_dir)
    assert started["run"]["milestone"] == "source_intake"
    assert started["video_maker"]["milestones"][0]["status"] == "in_progress"

    ratified = _invoke(vm_ratify_source_intake, output_dir=output_dir)

    manifest = Path(output_dir) / "artifacts" / "source" / "source-manifest.md"
    assert ratified["result"]["passed"] is True
    assert ratified["video_maker"]["milestones"][0]["status"] == "completed"
    assert manifest.is_file()
    text = manifest.read_text(encoding="utf-8")
    assert "# Source Manifest" in text
    assert "brief.md" in text
    assert "stats.csv" in text
    assert not (Path(output_dir) / "artifacts" / "research").exists()


def test_script_task_uses_source_manifest_and_contract_without_research(tmp_path: Path):
    source = _make_source_folder(tmp_path)
    init = _invoke(
        vm_init_video_session,
        topic="script from folder",
        source="folder",
        source_folder=str(source),
        root_dir=str(tmp_path),
        timestamp="20260427-110100",
    )
    output_dir = init["output_dir"]
    _invoke(vm_start_source_intake, output_dir=output_dir)
    _invoke(vm_ratify_source_intake, output_dir=output_dir)
    started = _invoke(vm_start_script, output_dir=output_dir)

    task = _invoke(vm_build_scriptwriter_task, output_dir=output_dir, run_number=1)

    assert task["subagent_type"] == "scriptwriter"
    assert "source_manifest_file" in task["description"]
    assert "script-contract.json" in task["description"]
    assert "research_file" not in task["description"]
    assert Path(started["run"]["run_dir"]).exists()


def test_ratify_script_accepts_script_and_contract_without_manifest_json(tmp_path: Path):
    source = _make_source_folder(tmp_path)
    init = _invoke(
        vm_init_video_session,
        topic="script ratify v2",
        source="folder",
        source_folder=str(source),
        root_dir=str(tmp_path),
        timestamp="20260427-110200",
    )
    output_dir = init["output_dir"]
    _invoke(vm_start_source_intake, output_dir=output_dir)
    _invoke(vm_ratify_source_intake, output_dir=output_dir)
    started = _invoke(vm_start_script, output_dir=output_dir)
    run_dir = Path(started["run"]["run_dir"])
    (run_dir / "script.md").write_text(
        "## Scene 1\ntype: narration\nnarration: hi\nscene_intent: hook\ncontent_brief: brief\n",
        encoding="utf-8",
    )

    result = _invoke(vm_ratify_script, output_dir=output_dir, run_number=1)

    assert result["result"]["passed"] is True
    assert not (run_dir / "manifest.json").exists()


def test_ratify_script_tool_uses_explicit_run_number(tmp_path: Path):
    source = _make_source_folder(tmp_path)
    init = _invoke(
        vm_init_video_session,
        topic="script retry ratify v2",
        source="folder",
        source_folder=str(source),
        root_dir=str(tmp_path),
        timestamp="20260427-110300",
    )
    output_dir = init["output_dir"]
    _invoke(vm_start_source_intake, output_dir=output_dir)
    _invoke(vm_ratify_source_intake, output_dir=output_dir)
    started = _invoke(vm_start_script, output_dir=output_dir)
    run_1_dir = Path(started["run"]["run_dir"])
    (run_1_dir / "script.md").write_text(
        "## Scene 1\n- **type**: narration\n",
        encoding="utf-8",
    )
    run_2 = _invoke(vm_build_scriptwriter_task, output_dir=output_dir, run_number=2)
    run_2_dir = Path(run_2["run_dir"])
    (run_2_dir / "script.md").write_text(
        "## Scene 1\n"
        "type: narration\n"
        "narration: hi\n"
        "scene_intent: hook\n"
        "content_brief: brief\n",
        encoding="utf-8",
    )

    result = _invoke(vm_ratify_script, output_dir=output_dir, run_number=2)

    assert result["result"]["passed"] is True
    assert "current_run: 2" in (Path(output_dir) / "state.yaml").read_text(encoding="utf-8")
    assert (Path(output_dir) / "ratify" / "script-run-2.json").is_file()


def test_build_langchain_tools_exposes_v2_tools_only():
    from deepagents_video_maker.langchain_tools import build_langchain_tools

    names = {t.name for t in build_langchain_tools()}
    assert {
        "vm_start_source_intake",
        "vm_ratify_source_intake",
        "vm_start_script",
        "vm_build_scriptwriter_task",
        "vm_ratify_script",
        "vm_start_build_scenes",
        "vm_build_remotion_task",
        "vm_ratify_build_scenes",
        "vm_start_render_package",
        "vm_render_remotion_project",
        "vm_package_render_output",
        "vm_ratify_render_package",
        "vm_build_publish_readiness_report",
    }.issubset(names)
    assert "vm_start_research" not in names
    assert "vm_build_researcher_task" not in names


def test_build_render_tool_sequence_requires_approval_and_packages_outputs(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "deepagents_video_maker.build_render_flow._probe_duration",
        lambda path: (0, "90.0\n", ""),
    )
    source = _make_source_folder(tmp_path)
    init = _invoke(
        vm_init_video_session,
        topic="render native tools",
        source="folder",
        source_folder=str(source),
        root_dir=str(tmp_path),
        timestamp="20260427-120000",
    )
    output_dir = init["output_dir"]
    _invoke(vm_start_source_intake, output_dir=output_dir)
    _invoke(vm_ratify_source_intake, output_dir=output_dir)
    started_script = _invoke(vm_start_script, output_dir=output_dir)
    script_dir = Path(started_script["run"]["run_dir"])
    (script_dir / "script.md").write_text(
        "## Scene 1\ntype: narration\nnarration: hi\nscene_intent: hook\ncontent_brief: brief\n",
        encoding="utf-8",
    )
    _invoke(vm_ratify_script, output_dir=output_dir)

    blocked = _invoke(vm_start_build_scenes, output_dir=output_dir, script_approved=False)
    assert "error" in blocked

    started_build = _invoke(vm_start_build_scenes, output_dir=output_dir, script_approved=True)
    assert started_build["run"]["milestone"] == "build_scenes"
    task = _invoke(vm_build_remotion_task, output_dir=output_dir)
    assert task["subagent_type"] == "remotion-builder"

    project = Path(output_dir) / "remotion-project"
    (project / "src").mkdir(parents=True)
    (project / "package.json").write_text('{"scripts":{}}', encoding="utf-8")
    (project / "src" / "index.ts").write_text("export {};\n", encoding="utf-8")
    assert _invoke(vm_ratify_build_scenes, output_dir=output_dir)["result"]["passed"] is True

    assert _invoke(vm_start_render_package, output_dir=output_dir)["run"]["milestone"] == "render_package"
    out_dir = project / "out"
    out_dir.mkdir(parents=True)
    (out_dir / "video.mp4").write_bytes(b"fake video")
    (out_dir / "thumbnail.jpg").write_bytes(b"fake thumb")
    package_result = _invoke(vm_package_render_output, output_dir=output_dir)
    assert package_result["final_video_exists"] is True
    assert _invoke(vm_ratify_render_package, output_dir=output_dir)["result"]["passed"] is True
    readiness = _invoke(
        vm_build_publish_readiness_report,
        output_dir=output_dir,
        decision="not_reviewed",
        notes="Golden path render exists; publish taste review pending.",
    )
    assert readiness["status"] == "not_reviewed"
    assert (Path(output_dir) / "final" / "publish-readiness.md").is_file()

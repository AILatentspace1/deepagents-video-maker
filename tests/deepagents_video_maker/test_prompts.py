import pytest

from deepagents_video_maker.prompts import load_prompt, load_subagent_prompt


def test_producer_prompt_contains_v2_controller_protocol_and_hard_rules():
    prompt = load_prompt("producer")

    assert "video-maker-v2" in prompt
    assert "Controller protocol" in prompt
    assert "vm_start_source_intake" in prompt
    assert 'task(subagent_type="scriptwriter"' in prompt
    assert "source-manifest.md" in prompt
    assert "research.md" in prompt
    assert "不再支持旧" in prompt


def test_producer_prompt_bans_pseudo_tool_calls():
    prompt = load_prompt("producer")

    assert "<sop_invocation>" in prompt
    assert '<invoke name="task">' in prompt
    assert "DSML" in prompt
    assert "禁止" in prompt


def test_producer_prompt_bans_controller_self_repair_loops():
    prompt = load_prompt("producer")

    assert "edit_file" in prompt
    assert "write_file" in prompt
    assert "block_for_user" in prompt
    assert "每个 artifact gate 最多一次自动 retry" in prompt
    assert "禁止继续循环调用 LLM/tool" in prompt


def test_v2_scriptwriter_prompt_has_input_and_output_contract():
    prompt = load_subagent_prompt("scriptwriter")

    assert "Input contract" in prompt
    assert "Output contract" in prompt
    assert "source_manifest_file" in prompt
    assert "contract_file" in prompt
    assert "blocking_issues" in prompt
    assert "manifest.json" in prompt


def test_missing_prompt_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_prompt("subagents/not-a-real-agent")

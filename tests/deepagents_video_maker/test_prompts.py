import pytest

from deepagents_video_maker.prompts import load_prompt, load_subagent_prompt


SUBAGENTS = [
    "researcher",
    "scriptwriter",
    "evaluator",
    "reviewer",
    "editor",
    "scene-batch-generator",
    "scene-patch-generator",
]


def test_producer_prompt_contains_controller_protocol_and_hard_rules():
    prompt = load_prompt("producer")

    assert "Controller protocol" in prompt
    assert "Protocol boundary" in prompt
    assert "Typed tools required" in prompt
    assert 'task(subagent_type="researcher")' in prompt
    assert "artifact gate" in prompt
    assert "research.md" in prompt
    assert "不能进入 script" in prompt


def test_producer_prompt_bans_pseudo_tool_calls():
    prompt = load_prompt("producer")

    assert "<sop_invocation>" in prompt
    assert '<invoke name="task">' in prompt
    assert "DSML" in prompt
    assert "禁止" in prompt


@pytest.mark.parametrize("name", SUBAGENTS)
def test_subagent_prompt_has_input_and_output_contract(name: str):
    prompt = load_subagent_prompt(name)

    assert "Input contract" in prompt
    assert "Output contract" in prompt
    assert "blocking_issues" in prompt


def test_researcher_prompt_requires_research_artifact():
    prompt = load_subagent_prompt("researcher")

    assert "research.md" in prompt
    assert "research_path" in prompt
    assert "section_count" in prompt
    assert "visual_strategy" in prompt


def test_missing_prompt_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_prompt("subagents/not-a-real-agent")


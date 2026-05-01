"""Tests for the Phase 1 training data flywheel (training_data module)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deepagents_video_maker.models import EvalSample
from deepagents_video_maker.training_data import (
    append_eval_sample,
    eval_samples_path,
    load_eval_samples,
)


def _sample(eval_round: int = 0, eval_score: float = 72.5, eval_pass: bool = False) -> EvalSample:
    return EvalSample(
        session_id="20260501-120000-video-test-topic",
        topic="test topic",
        style="professional",
        duration="1-3min",
        eval_round=eval_round,
        script_text="## Scene 1\nnarration: hello world\n",
        eval_score=eval_score,
        eval_pass=eval_pass,
        dimensions=[{"name": "narrative_flow", "score": 72, "weight": 0.25}],
        iteration_fixes=[{"priority": 1, "target": "scene_1", "action": "improve transition"}],
        contract_violations=[],
    )


class TestEvalSamplesPath:
    def test_returns_training_jsonl_inside_output_dir(self, tmp_path: Path):
        path = eval_samples_path(tmp_path)
        assert path == tmp_path / "training" / "eval-samples.jsonl"

    def test_accepts_string_path(self, tmp_path: Path):
        path = eval_samples_path(str(tmp_path))
        assert path.parent.name == "training"
        assert path.name == "eval-samples.jsonl"


class TestAppendEvalSample:
    def test_creates_file_and_directory(self, tmp_path: Path):
        sample = _sample()
        path = append_eval_sample(tmp_path, sample)
        assert path.exists()
        assert path.parent.name == "training"

    def test_file_contains_valid_json_line(self, tmp_path: Path):
        sample = _sample()
        append_eval_sample(tmp_path, sample)
        content = eval_samples_path(tmp_path).read_text(encoding="utf-8")
        lines = [l for l in content.splitlines() if l.strip()]
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["topic"] == "test topic"
        assert data["eval_score"] == 72.5
        assert data["eval_pass"] is False
        assert data["eval_round"] == 0

    def test_multiple_appends_produce_multiple_lines(self, tmp_path: Path):
        append_eval_sample(tmp_path, _sample(eval_round=0, eval_score=72.5))
        append_eval_sample(tmp_path, _sample(eval_round=1, eval_score=80.0, eval_pass=True))
        lines = [
            l
            for l in eval_samples_path(tmp_path).read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]
        assert len(lines) == 2
        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first["eval_round"] == 0
        assert second["eval_round"] == 1
        assert second["eval_pass"] is True

    def test_returns_path_of_written_file(self, tmp_path: Path):
        path = append_eval_sample(tmp_path, _sample())
        assert path == eval_samples_path(tmp_path)

    def test_idempotent_on_existing_directory(self, tmp_path: Path):
        # Call twice — should not raise even if directory already exists.
        append_eval_sample(tmp_path, _sample())
        append_eval_sample(tmp_path, _sample(eval_round=1))
        assert eval_samples_path(tmp_path).exists()


class TestLoadEvalSamples:
    def test_returns_empty_list_when_file_missing(self, tmp_path: Path):
        samples = load_eval_samples(tmp_path)
        assert samples == []

    def test_round_trips_single_sample(self, tmp_path: Path):
        original = _sample(eval_round=0, eval_score=77.3, eval_pass=False)
        append_eval_sample(tmp_path, original)
        loaded = load_eval_samples(tmp_path)
        assert len(loaded) == 1
        s = loaded[0]
        assert s.session_id == original.session_id
        assert s.topic == original.topic
        assert s.eval_score == original.eval_score
        assert s.eval_pass is False
        assert len(s.dimensions) == 1
        assert len(s.iteration_fixes) == 1
        assert s.contract_violations == []

    def test_round_trips_multiple_samples(self, tmp_path: Path):
        for i in range(3):
            append_eval_sample(tmp_path, _sample(eval_round=i, eval_score=60.0 + i * 10))
        loaded = load_eval_samples(tmp_path)
        assert len(loaded) == 3
        assert [s.eval_round for s in loaded] == [0, 1, 2]
        assert [s.eval_score for s in loaded] == [60.0, 70.0, 80.0]

    def test_skips_blank_lines(self, tmp_path: Path):
        path = eval_samples_path(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        sample = _sample()
        path.write_text(
            "\n" + json.dumps({"session_id": sample.session_id, "topic": sample.topic,
                               "style": sample.style, "duration": sample.duration,
                               "eval_round": 0, "script_text": sample.script_text,
                               "eval_score": 72.5, "eval_pass": False,
                               "dimensions": [], "iteration_fixes": [],
                               "contract_violations": [], "timestamp": "2026-05-01T00:00:00"}) + "\n\n",
            encoding="utf-8",
        )
        loaded = load_eval_samples(tmp_path)
        assert len(loaded) == 1


class TestVmRecordEvalSampleTool:
    """Integration: the LangChain tool wrapper calls append_eval_sample correctly."""

    def test_tool_returns_recorded_and_path(self, tmp_path: Path):
        from deepagents_video_maker.langchain_tools import vm_record_eval_sample

        kwargs = dict(
            output_dir=str(tmp_path),
            session_id="20260501-test",
            topic="tool test",
            style="casual",
            duration="3-5min",
            eval_round=1,
            script_text="## Scene 1\nnarration: hi\n",
            eval_score=83.0,
            eval_pass=True,
            dimensions=[{"name": "pacing", "score": 85, "weight": 0.20}],
            iteration_fixes=[],
            contract_violations=[],
        )
        if hasattr(vm_record_eval_sample, "invoke"):
            result = vm_record_eval_sample.invoke(kwargs)
        else:
            result = vm_record_eval_sample(**kwargs)

        assert result["recorded"] is True
        assert "eval-samples.jsonl" in result["path"]

        samples = load_eval_samples(tmp_path)
        assert len(samples) == 1
        assert samples[0].topic == "tool test"
        assert samples[0].eval_score == 83.0
        assert samples[0].eval_pass is True

    def test_tool_registered_in_build_langchain_tools(self):
        from deepagents_video_maker.langchain_tools import build_langchain_tools

        names = {t.name for t in build_langchain_tools()}
        assert "vm_record_eval_sample" in names

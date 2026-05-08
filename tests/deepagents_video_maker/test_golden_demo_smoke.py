from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.run_golden_demo_smoke import run


def test_golden_demo_smoke_reaches_script_checkpoint_without_network(tmp_path: Path):
    output_dir = run(tmp_path, timestamp="20260507-000000")

    manifest = output_dir / "artifacts" / "source" / "source-manifest.md"
    script = output_dir / "artifacts" / "script" / "run-1" / "script.md"
    contract = output_dir / "artifacts" / "script" / "run-1" / "script-contract.json"
    state = output_dir / "state.yaml"

    assert manifest.is_file()
    assert "brief.md" in manifest.read_text(encoding="utf-8")
    assert script.is_file()
    assert contract.is_file()
    state_text = state.read_text(encoding="utf-8")
    assert "id: source_intake" in state_text
    assert "id: script" in state_text
    assert "status: completed" in state_text

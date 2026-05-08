from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.deepagents_video_maker import to_virtual_path


def test_to_virtual_path_accepts_windows_extended_length_project_paths():
    raw = (
        r"\\?\E:\workspace\deepagents-video-maker\output\demo"
        r"\remotion-project\src\components\FadeTransition.tsx"
    )

    assert (
        to_virtual_path(raw)
        == "/output/demo/remotion-project/src/components/FadeTransition.tsx"
    )

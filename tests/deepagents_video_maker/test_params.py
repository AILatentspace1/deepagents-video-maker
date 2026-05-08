from deepagents_video_maker.params import parse_video_request


def test_parse_video_request_accepts_folder_source_and_source_folder():
    goal = parse_video_request(
        r'''
        topic=LLM video benchmark
        source=folder
        source_folder=E:\workspace\video-maker-v2
        duration=3-5min
        style=professional
        aspectRatio=16:9
        '''
    )

    assert goal.topic == "LLM video benchmark"
    assert goal.source == "folder"
    assert goal.source_folder == r"E:\workspace\video-maker-v2"
    assert goal.aspect_ratio == "16:9"
    assert goal.eval_mode == "none"
    assert goal.composition_mode == "none"


def test_slug_is_stable_for_mixed_topic():
    goal = parse_video_request("topic=介绍 video-maker-v2 skill")

    assert goal.slug() == "介绍-video-maker-v2-skill"


def test_parse_video_request_defaults_to_manual_source_for_free_text():
    goal = parse_video_request("介绍一个没有显式 source 的视频")

    assert goal.source == "manual"

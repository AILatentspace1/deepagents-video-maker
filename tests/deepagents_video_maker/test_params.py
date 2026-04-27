from deepagents_video_maker.params import parse_video_request


def test_parse_video_request_derives_defaults():
    goal = parse_video_request(
        """
        topic=介绍 video-maker skill；
        source=local-file；
        local_file=/docs/ARCHITECTURE-VIDEO-MAKER.md；
        duration=1-3min；
        style=professional；
        aspectRatio=16:9；
        quality_threshold=0；
        eval_mode=gan；
        """
    )

    assert goal.topic == "介绍 video-maker skill"
    assert goal.source == "local-file"
    assert goal.local_file == "/docs/ARCHITECTURE-VIDEO-MAKER.md"
    assert goal.aspect_ratio == "16:9"
    assert goal.quality_threshold == 0
    assert goal.research_depth == "light"
    assert goal.template == "news-clean"
    assert goal.lut_style == "news_neutral"
    assert goal.visual_strategy == "image_light"


def test_slug_is_stable_for_mixed_topic():
    goal = parse_video_request("topic=介绍 video-maker skill")

    assert goal.slug() == "介绍-video-maker-skill"


def test_parse_video_request_accepts_comma_separated_pairs():
    goal = parse_video_request(
        "topic=介绍 video-maker skill, source=local-file, "
        "local_file=/docs/ARCHITECTURE-VIDEO-MAKER.md"
    )

    assert goal.topic == "介绍 video-maker skill"
    assert goal.source == "local-file"
    assert goal.local_file == "/docs/ARCHITECTURE-VIDEO-MAKER.md"

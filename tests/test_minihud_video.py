from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.minihud_video import pipeline
from scripts.minihud_video.pipeline import (
    BUILD_DIR,
    DECK_PATH,
    build_slide_url,
    slide_path,
)
from scripts.minihud_video.audio import (
    Cue,
    format_srt_time,
    merge_cues,
    parse_srt,
    split_cue,
    wrap_caption,
)
from scripts.minihud_video.storyboard import (
    SEGMENTS,
    TRANSITION_SECONDS,
    encoded_seconds,
    render_requests,
    timeline,
    total_base_seconds,
)


ROOT = Path(__file__).resolve().parents[1]


class AudioTest(unittest.TestCase):
    def test_srt_parser_and_formatter(self):
        source = "1\n00:00:00,500 --> 00:00:02,000\n第一句字幕\n"
        cue = parse_srt(source)[0]
        self.assertEqual(cue, Cue(0.5, 2.0, "第一句字幕"))
        self.assertEqual(format_srt_time(62.345), "00:01:02,345")

    def test_chinese_caption_wraps_to_two_lines(self):
        wrapped = wrap_caption(
            "一次只开一层看见问题现场处理关闭复查",
            width=10,
        )
        self.assertEqual(wrapped.count("\n"), 1)
        self.assertLessEqual(max(map(len, wrapped.splitlines())), 10)

    def test_merge_cues_uses_crossfade_timeline(self):
        merged = merge_cues(
            [[Cue(0.0, 1.0, "第一段")], [Cue(0.0, 1.0, "第二段")]],
            starts=[0.0, 3.05],
        )
        self.assertEqual(merged[1], Cue(3.05, 4.05, "第二段"))

    def test_long_cue_splits_before_wrapping(self):
        source = Cue(
            0.0,
            4.0,
            "一二三四五六七八九十一二三四五六七八九十"
            "一二三四五六七八九十一二三四五六七八九十",
        )
        parts = split_cue(source, width=10)
        self.assertEqual(len(parts), 2)
        self.assertTrue(all(part.text.count("\n") <= 1 for part in parts))
        self.assertTrue(
            all(max(map(len, part.text.splitlines())) <= 10 for part in parts)
        )


class SlidePipelineTest(unittest.TestCase):
    def test_voice_command_dispatches_and_prints_outputs(self):
        output = Path("narration.mp3")
        with (
            patch("sys.argv", ["pipeline", "voice"]),
            patch.object(
                pipeline,
                "render_voice",
                return_value=(output,),
            ) as render_voice,
            patch("builtins.print") as print_output,
        ):
            pipeline.main()
        render_voice.assert_called_once_with()
        print_output.assert_called_once_with(output)

    def test_render_voice_explains_missing_edge_tts_environment(self):
        with TemporaryDirectory() as directory:
            edge_tts = Path(directory) / "edge-tts"
            with patch.object(pipeline, "EDGE_TTS", edge_tts):
                with self.assertRaisesRegex(RuntimeError, "edge-tts==7.2.8"):
                    pipeline.render_voice()

    def test_slide_url_is_local_and_encodes_export_state(self):
        url = build_slide_url(6, "range:chunk")
        self.assertTrue(url.startswith("file:"))
        self.assertIn("export=1", url)
        self.assertIn("slide=6", url)
        self.assertIn("state=range%3Achunk", url)

    def test_slide_path_is_stable(self):
        self.assertEqual(
            slide_path("range-chunk"),
            BUILD_DIR / "slides/range-chunk.png",
        )
        self.assertTrue(DECK_PATH.is_file())


class StoryboardTest(unittest.TestCase):
    def test_storyboard_has_exact_timing_and_unique_ids(self):
        self.assertEqual(len(SEGMENTS), 19)
        self.assertEqual(len({segment.id for segment in SEGMENTS}), 19)
        self.assertAlmostEqual(total_base_seconds(), 210.0, places=3)
        self.assertAlmostEqual(encoded_seconds(), 205.5, places=3)
        self.assertEqual(TRANSITION_SECONDS, 0.25)

    def test_narration_matches_approved_scope(self):
        copy = "".join(segment.narration for segment in SEGMENTS)
        self.assertEqual(len(copy), 840)
        for phrase in (
            "问题",
            "Servux",
            "按住 Shift",
            "Mob Cap 是数量上限",
            "先收藏",
            "实用的 Minecraft 模组和生存技巧",
        ):
            self.assertIn(phrase, copy)
        for forbidden in ("15 种", "下一期", "自动建造", "服务器许可"):
            self.assertNotIn(forbidden, copy)

    def test_timeline_accounts_for_crossfades(self):
        items = timeline()
        self.assertEqual(items[0].start, 0)
        self.assertAlmostEqual(items[1].start, 3.05, places=3)
        self.assertAlmostEqual(items[-1].end, 205.5, places=3)

    def test_every_render_request_has_a_supported_slide(self):
        requests = render_requests()
        self.assertEqual(len(requests), 19)
        self.assertTrue(all(1 <= item["slide"] <= 8 for item in requests))
        self.assertEqual(requests[-2]["state"], "video:install")
        self.assertEqual(requests[-1]["state"], "video:outro")

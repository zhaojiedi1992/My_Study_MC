from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts.tweakeroo_video import audio
from scripts.tweakeroo_video.audio import (
    Cue,
    choose_voice,
    format_srt_time,
    merge_cues,
    parse_srt,
    split_cue,
)
from scripts.tweakeroo_video.pipeline import (
    BUILD_DIR,
    DECK_PATH,
    build_slide_url,
    slide_path,
)
from scripts.tweakeroo_video.storyboard import (
    PREVIEW_SEGMENT_IDS,
    SEGMENTS,
    encoded_seconds,
    render_requests,
    timeline,
    total_base_seconds,
)


ROOT = Path(__file__).resolve().parents[1]


class StoryboardTest(unittest.TestCase):
    def test_timeline_is_exactly_two_hundred_seconds(self):
        self.assertEqual(len(SEGMENTS), 20)
        self.assertAlmostEqual(total_base_seconds(), 204.75)
        self.assertAlmostEqual(encoded_seconds(), 200.0)
        self.assertAlmostEqual(timeline()[0].start, 0.0)
        self.assertAlmostEqual(timeline()[-1].end, 200.0)

    def test_hook_and_feature_order_are_fixed(self):
        self.assertEqual(
            [segment.id for segment in SEGMENTS[:3]],
            ["hook-soul", "hook-restock", "hook-gamma"],
        )
        chapters = []
        for segment in SEGMENTS:
            if segment.chapter not in chapters:
                chapters.append(segment.chapter)
        feature_order = (
            "灵魂出窍",
            "鞘翅与胸甲",
            "自动补货",
            "快速左右键",
            "Gamma 亮度",
        )
        positions = [chapters.index(name) for name in feature_order]
        self.assertEqual(positions, sorted(positions))

    def test_copy_contains_conversion_and_safety_contract(self):
        copy = "".join(segment.narration for segment in SEGMENTS)
        for phrase in (
            "不念配置表",
            "翻译成人话",
            "快捷键",
            "服务器规则",
            "刷怪规则",
            "关注我",
        ):
            self.assertIn(phrase, copy)
        self.assertNotIn("三连", copy)
        self.assertNotIn("必装", copy)

    def test_preview_exercises_hook_explanation_and_joke(self):
        self.assertEqual(
            PREVIEW_SEGMENT_IDS,
            ("hook-soul", "soul-effect", "gamma-on"),
        )

    def test_render_requests_have_valid_deck_states(self):
        requests = render_requests()
        self.assertEqual(len(requests), len(SEGMENTS))
        required = {
            (2, "config"),
            (2, "effect"),
            (3, "auto"),
            (3, "chestplate"),
            (4, "config"),
            (4, "threshold"),
            (4, "done"),
            (5, "left"),
            (5, "right"),
            (6, "config"),
            (6, "off"),
            (6, "on"),
        }
        self.assertTrue(
            required.issubset(
                {(item["slide"], item["state"]) for item in requests}
            )
        )


class AudioTest(unittest.TestCase):
    def test_voice_selection_prefers_conversational_male_voice(self):
        voices = (
            "zh-CN-YunyangNeural Male News\n"
            "zh-CN-YunxiNeural Male Novel\n"
            "zh-CN-YunjianNeural Male Sports\n"
        )
        with patch.object(
            audio.subprocess,
            "run",
            return_value=Mock(stdout=voices),
        ):
            self.assertEqual(
                choose_voice(Path("edge-tts")),
                "zh-CN-YunxiNeural",
            )

    def test_srt_parser_and_time_formatter(self):
        cue = parse_srt(
            "1\n00:00:00,500 --> 00:00:02,000\n第一句字幕\n"
        )[0]
        self.assertEqual(cue, Cue(0.5, 2.0, "第一句字幕"))
        self.assertEqual(format_srt_time(62.345), "00:01:02,345")

    def test_caption_is_at_most_two_lines_of_eighteen_characters(self):
        cue = Cue(
            0.0,
            8.0,
            "安装时让游戏Tweakeroo和MaLiLib版本对应服务器规则优先",
        )
        captions = split_cue(cue)
        for caption in captions:
            lines = caption.text.splitlines()
            self.assertLessEqual(len(lines), 2)
            self.assertTrue(all(len(line) <= 18 for line in lines))
            flattened = caption.text.replace("\n", "")
            self.assertNotIn("Tweake", flattened[-6:])

    def test_merged_cues_follow_crossfade_timeline(self):
        merged = merge_cues(
            [
                [Cue(0.0, 1.0, "第一段")],
                [Cue(0.0, 1.0, "第二段")],
            ],
            [0.0, 2.75],
        )
        self.assertEqual(merged[1], Cue(2.75, 3.75, "第二段"))

    def test_generate_voice_uses_approved_prosody(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)

            def fake_run(command, **_kwargs):
                if "--list-voices" in command:
                    return Mock(stdout="zh-CN-YunxiNeural Male Novel\n")
                if "--write-media" in command:
                    media = Path(command[command.index("--write-media") + 1])
                    srt = Path(
                        command[command.index("--write-subtitles") + 1]
                    )
                    media.write_bytes(b"mp3")
                    srt.write_text(
                        "1\n00:00:00,100 --> 00:00:01,000\n试听字幕\n",
                        encoding="utf-8",
                    )
                return Mock(stdout="")

            with (
                patch.object(audio, "probe_duration", return_value=2.4),
                patch.object(
                    audio.subprocess,
                    "run",
                    side_effect=fake_run,
                ) as run,
            ):
                audio.generate_segment_voice(
                    build_dir,
                    Path("edge-tts"),
                    SEGMENTS[:1],
                )

            command = next(
                call.args[0]
                for call in run.call_args_list
                if "--write-media" in call.args[0]
            )
            self.assertIn("--rate=-2%", command)
            self.assertIn("--pitch=+0Hz", command)
            self.assertIn("zh-CN-YunxiNeural", command)


class PipelineTest(unittest.TestCase):
    def test_deck_and_build_paths_are_isolated(self):
        self.assertEqual(
            DECK_PATH,
            ROOT / "source/MOD介绍/tweakeroo/index.html",
        )
        self.assertEqual(BUILD_DIR, ROOT / "build/tweakeroo-video")
        self.assertNotIn("minihud", str(BUILD_DIR).lower())

    def test_slide_url_is_deterministic_and_exported(self):
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(build_slide_url(4, "done"))
        query = parse_qs(parsed.query)
        self.assertEqual(
            query,
            {
                "export": ["1"],
                "slide": ["4"],
                "state": ["done"],
            },
        )

    def test_slide_output_uses_segment_id(self):
        self.assertEqual(
            slide_path("restock-done"),
            BUILD_DIR / "slides/restock-done.png",
        )


if __name__ == "__main__":
    unittest.main()

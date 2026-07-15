from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts.minihud_video import audio, pipeline
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

    def test_long_cue_prefers_semantic_boundaries_and_proportional_timing(self):
        source = Cue(
            1.0,
            5.6,
            "第一句稍微长一些，需要在这里停顿，服务器支持。",
        )

        parts = split_cue(source, width=9)

        self.assertEqual(
            [part.text.replace("\n", "") for part in parts],
            ["第一句稍微长一些，需要在这里停顿，", "服务器支持。"],
        )
        self.assertAlmostEqual(parts[0].end, 4.4, places=6)
        self.assertAlmostEqual(parts[1].start, 4.4, places=6)
        self.assertEqual(parts[-1].end, source.end)

    def test_caption_splitting_keeps_nearby_latin_and_chinese_tokens(self):
        source = Cue(
            0.0,
            8.2,
            "FPS 看客户端，延迟和 TPS、MSPT 看联机状态；"
            "精确数据还要看服务器支持。",
        )

        flattened = [
            part.text.replace("\n", "") for part in split_cue(source)
        ]

        self.assertTrue(any("TPS" in part for part in flattened))
        self.assertTrue(any("服务器" in part for part in flattened))
        self.assertFalse(any(part.endswith("服") for part in flattened))
        self.assertFalse(any(part in {"T", "PS。"} for part in flattened))

    def test_caption_wrapping_keeps_latin_tokens_at_nearby_boundaries(self):
        source = Cue(
            0.0,
            6.0,
            "安装只要记住：Fabric Loader，加上版本匹配的 MiniHUD "
            "和 MaLiLib。",
        )

        lines = [line for part in split_cue(source) for line in part.text.splitlines()]

        for token in ("Fabric", "Loader", "MiniHUD", "MaLiLib"):
            with self.subTest(token=token):
                self.assertTrue(any(token in line for line in lines))

    def test_production_captions_enforce_two_lines_of_eighteen_characters(self):
        sources = (
            Cue(
                0.0,
                8.0,
                "结构被海水或山体挡住时，打开结构主边界和组成部分，"
                "就能看清整体与内部。",
            ),
            Cue(
                0.0,
                8.0,
                "机器效率不对，再查看光照、生成距离、Mob Cap、"
                "实体数量、延迟和 TPS。",
            ),
        )

        captions = [part.text for cue in sources for part in split_cue(cue)]

        self.assertTrue(all(len(caption.splitlines()) <= 2 for caption in captions))
        self.assertTrue(
            all(
                len(line) <= 18
                for caption in captions
                for line in caption.splitlines()
            )
        )

    def test_merge_cues_trims_upstream_overlap_without_zero_length_cues(self):
        merged = merge_cues(
            [[Cue(0.1, 4.0, "第一句"), Cue(3.95, 5.0, "第二句")]],
            starts=[10.0],
        )

        self.assertEqual(merged[0], Cue(10.1, 13.95, "第一句"))
        self.assertEqual(merged[1], Cue(13.95, 15.0, "第二句"))
        self.assertTrue(all(cue.end > cue.start for cue in merged))
        self.assertTrue(
            all(left.end <= right.start for left, right in zip(merged, merged[1:]))
        )

    def test_srt_parser_rejects_empty_malformed_and_textless_input(self):
        invalid_sources = (
            ("", "empty"),
            ("1\nnot a timing line\n字幕\n", "timing"),
            ("1\n00:00:00,100 --> 00:00:00,200\n", "text"),
        )

        for source, message in invalid_sources:
            with self.subTest(message=message):
                with self.assertRaisesRegex(RuntimeError, message):
                    parse_srt(source)

    def test_srt_parser_rejects_nonpositive_and_unordered_cues(self):
        invalid_sources = (
            (
                "1\n00:00:01,000 --> 00:00:01,000\n零时长\n",
                "positive",
            ),
            (
                "1\n00:00:02,000 --> 00:00:03,000\n第二句\n\n"
                "2\n00:00:01,000 --> 00:00:04,000\n第一句\n",
                "ordered",
            ),
        )

        for source, message in invalid_sources:
            with self.subTest(message=message):
                with self.assertRaisesRegex(RuntimeError, message):
                    parse_srt(source)

    def test_choose_voice_prefers_yunyang_then_falls_back_to_yunjian(self):
        edge_tts = Path("edge-tts")
        cases = (
            (
                "zh-CN-YunjianNeural Male\nzh-CN-YunyangNeural Male\n",
                "zh-CN-YunyangNeural",
            ),
            ("zh-CN-YunjianNeural Male\n", "zh-CN-YunjianNeural"),
        )

        for voices, expected in cases:
            with self.subTest(expected=expected):
                with patch.object(
                    audio.subprocess,
                    "run",
                    return_value=Mock(stdout=voices),
                ):
                    self.assertEqual(audio.choose_voice(edge_tts), expected)

    def test_generate_voice_rejects_empty_segment_srt(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)

            def write_empty_srt(command, **_kwargs):
                media = Path(command[command.index("--write-media") + 1])
                srt = Path(command[command.index("--write-subtitles") + 1])
                media.write_bytes(b"mp3")
                srt.write_text("", encoding="utf-8")
                return Mock(returncode=0)

            with (
                patch.object(audio, "SEGMENTS", SEGMENTS[:1]),
                patch.object(audio, "choose_voice", return_value=audio.VOICES[0]),
                patch.object(audio, "probe_duration", return_value=0.2),
                patch.object(audio.subprocess, "run", side_effect=write_empty_srt),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"hook-structure.*empty",
                ):
                    audio.generate_voice(build_dir, Path("edge-tts"))

    def test_generate_voice_rejects_segment_srt_past_crossfade_budget(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)

            def write_late_srt(command, **_kwargs):
                media = Path(command[command.index("--write-media") + 1])
                srt = Path(command[command.index("--write-subtitles") + 1])
                media.write_bytes(b"mp3")
                srt.write_text(
                    "1\n00:00:00,100 --> 00:00:03,100\n越界字幕\n",
                    encoding="utf-8",
                )
                return Mock(returncode=0)

            with (
                patch.object(audio, "SEGMENTS", SEGMENTS[:2]),
                patch.object(audio, "choose_voice", return_value=audio.VOICES[0]),
                patch.object(audio, "probe_duration", return_value=0.2),
                patch.object(audio.subprocess, "run", side_effect=write_late_srt),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"hook-structure.*3\.05",
                ):
                    audio.generate_voice(build_dir, Path("edge-tts"))

    def test_generate_voice_rejects_narration_past_crossfade_budget(self):
        with TemporaryDirectory() as directory:
            with (
                patch.object(audio, "SEGMENTS", SEGMENTS[:2]),
                patch.object(audio, "choose_voice", return_value=audio.VOICES[0]),
                patch.object(audio, "probe_duration", return_value=3.06),
                patch.object(audio.subprocess, "run", return_value=Mock()),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"hook-structure.*3\.06s.*3\.05s",
                ):
                    audio.generate_voice(Path(directory), Path("edge-tts"))

    def test_generate_voice_rejects_merged_srt_past_encoded_timeline(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)

            def write_valid_srt(command, **_kwargs):
                media = Path(command[command.index("--write-media") + 1])
                srt = Path(command[command.index("--write-subtitles") + 1])
                media.write_bytes(b"mp3")
                srt.write_text(
                    "1\n00:00:00,100 --> 00:00:00,200\n片尾字幕\n",
                    encoding="utf-8",
                )
                return Mock(returncode=0)

            with (
                patch.object(audio, "SEGMENTS", SEGMENTS[-1:]),
                patch.object(audio, "choose_voice", return_value=audio.VOICES[0]),
                patch.object(audio, "probe_duration", return_value=0.2),
                patch.object(audio, "timeline", return_value=(Mock(start=205.4),)),
                patch.object(audio.subprocess, "run", side_effect=write_valid_srt),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"Merged subtitles.*205\.50",
                ):
                    audio.generate_voice(build_dir, Path("edge-tts"))

    def test_generate_voice_creates_all_artifacts_with_fixed_prosody(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)
            narration_by_id = {
                segment.id: segment.narration for segment in SEGMENTS
            }
            commands = []

            def write_outputs(command, **_kwargs):
                commands.append(command)
                media = Path(command[command.index("--write-media") + 1])
                srt = Path(command[command.index("--write-subtitles") + 1])
                media.write_bytes(b"mp3")
                srt.write_text(
                    "1\n00:00:00,100 --> 00:00:00,200\n"
                    f"{narration_by_id[media.stem]}\n",
                    encoding="utf-8",
                )
                return Mock(returncode=0)

            with (
                patch.object(audio, "choose_voice", return_value=audio.VOICES[0]),
                patch.object(audio, "probe_duration", return_value=0.2),
                patch.object(audio.subprocess, "run", side_effect=write_outputs),
            ):
                outputs = audio.generate_voice(build_dir, Path("edge-tts"))

            merged_path = (
                build_dir / "subtitles/minihud-bilibili.zh-CN.srt"
            )
            merged_source = merged_path.read_text(encoding="utf-8")
            merged = parse_srt(merged_source)
            merged_text = re.sub(r"\s+", "", "".join(cue.text for cue in merged))
            source_text = re.sub(
                r"\s+",
                "",
                "".join(segment.narration for segment in SEGMENTS),
            )

            self.assertEqual(len(outputs), 19)
            self.assertTrue(all(path.is_file() for path in outputs))
            self.assertEqual(len(list((build_dir / "narration").glob("*.srt"))), 19)
            self.assertTrue(merged_path.is_file())
            self.assertEqual(merged_text, source_text)
            self.assertTrue(
                all(left.end <= right.start for left, right in zip(merged, merged[1:]))
            )
            for block in re.split(r"\n\s*\n", merged_source.strip()):
                lines = block.splitlines()
                timing_index = next(
                    index for index, line in enumerate(lines) if "-->" in line
                )
                caption_lines = lines[timing_index + 1 :]
                self.assertLessEqual(len(caption_lines), 2)
                self.assertTrue(all(len(line) <= 18 for line in caption_lines))
            self.assertEqual(len(commands), 19)
            for command in commands:
                self.assertIn("--voice", command)
                self.assertIn(audio.VOICES[0], command)
                self.assertIn("--rate=-4%", command)
                self.assertIn("--pitch=-4Hz", command)


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
        timing_sensitive_copy = {
            segment.id: segment.narration
            for segment in SEGMENTS
            if segment.id in {"hook-structure", "hook-shape", "range-spawn"}
        }
        self.assertEqual(
            timing_sensitive_copy,
            {
                "hook-structure": "结构被挡，看不清范围？",
                "hook-shape": "圆心半径，还靠目测？",
                "range-spawn": "刷怪距离看球，挂机点更直观。",
            },
        )
        self.assertEqual(len(copy), 819)
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

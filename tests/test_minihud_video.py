from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, call, patch

from scripts.minihud_video import audio, pipeline, video
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
from scripts.minihud_video.publishing import build_publish_markdown, chapter_lines
from scripts.minihud_video.storyboard import (
    SEGMENTS,
    TRANSITION_SECONDS,
    encoded_seconds,
    render_requests,
    timeline,
    total_base_seconds,
)
from scripts.minihud_video.video import build_transition_filter, motion_filter


ROOT = Path(__file__).resolve().parents[1]


class PublishingTest(unittest.TestCase):
    def test_cover_source_has_approved_copy_and_dimensions(self):
        source = (ROOT / "scripts/minihud_video/cover.html").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "width:1600px",
            "height:1000px",
            "一个 MOD",
            "看清隐藏规则",
            "6 个实用场景",
        ):
            self.assertIn(phrase, source)
        self.assertLessEqual(source.count("<img"), 2)

    def test_publish_copy_is_complete_and_honest(self):
        copy = build_publish_markdown()
        for phrase in (
            "MiniHUD",
            "Minecraft Java 版 26.2",
            "Fabric Loader",
            "MaLiLib",
            "Servux",
            "不同版本",
            "收藏",
            "置顶评论",
        ):
            self.assertIn(phrase, copy)
        self.assertNotIn("下一期", copy)
        self.assertNotIn("15 种", copy)

    def test_pinned_comment_includes_scene_index_and_chapter_clocks(self):
        pinned_comment = build_publish_markdown().split(
            "## 置顶评论建议\n\n",
            maxsplit=1,
        )[1]

        for scene_label in (
            "迷路看信息 HUD",
            "遮挡看结构边界",
            "选址看环境覆盖",
            "估算看范围参考",
            "施工看形状参考",
            "整理和排查看预览与性能信息",
        ):
            self.assertIn(scene_label, pinned_comment)

        chapters = chapter_lines()
        self.assertIn(chapters[0], pinned_comment)
        self.assertIn(chapters[-1], pinned_comment)

    def test_chapters_are_monotonic(self):
        lines = chapter_lines()
        self.assertEqual(lines[0], "00:00 冷开场")
        self.assertTrue(any("结构边界" in line for line in lines))
        self.assertTrue(lines[-1].endswith("收藏与关注"))

        timestamps = []
        for line in lines:
            match = re.fullmatch(r"(\d{2}):(\d{2}) .+", line)
            self.assertIsNotNone(match, f"invalid chapter line: {line}")
            minutes, seconds = map(int, match.groups())
            self.assertLess(seconds, 60, f"invalid chapter clock: {line}")
            timestamps.append(minutes * 60 + seconds)
        self.assertTrue(
            all(first < second for first, second in zip(timestamps, timestamps[1:])),
            f"chapter clocks must be strictly increasing: {timestamps}",
        )


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

    def test_choose_voice_prefers_yunjian_then_falls_back_to_yunxi(self):
        edge_tts = Path("edge-tts")
        cases = (
            (
                "zh-CN-YunxiNeural Male\nzh-CN-YunjianNeural Male\n",
                "zh-CN-YunjianNeural",
            ),
            ("zh-CN-YunxiNeural Male\n", "zh-CN-YunxiNeural"),
        )

        for voices, expected in cases:
            with self.subTest(expected=expected):
                with patch.object(
                    audio.subprocess,
                    "run",
                    return_value=Mock(stdout=voices),
                ):
                    self.assertEqual(audio.choose_voice(edge_tts), expected)

    def test_generate_voice_rejects_more_than_one_second_of_tail_silence(self):
        with TemporaryDirectory() as directory:
            with (
                patch.object(audio, "SEGMENTS", SEGMENTS[:1]),
                patch.object(audio, "choose_voice", return_value=audio.VOICES[0]),
                patch.object(audio, "probe_duration", return_value=3.1),
                patch.object(audio.subprocess, "run", return_value=Mock()),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"hook-structure.*1\.20s.*1\.00s",
                ):
                    audio.generate_voice(Path(directory), Path("edge-tts"))

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
                patch.object(audio, "probe_duration", return_value=3.5),
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
                    "1\n00:00:00,100 --> 00:00:04,100\n越界字幕\n",
                    encoding="utf-8",
                )
                return Mock(returncode=0)

            with (
                patch.object(audio, "SEGMENTS", SEGMENTS[:2]),
                patch.object(audio, "choose_voice", return_value=audio.VOICES[0]),
                patch.object(audio, "probe_duration", return_value=3.5),
                patch.object(audio.subprocess, "run", side_effect=write_late_srt),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"hook-structure.*4\.05",
                ):
                    audio.generate_voice(build_dir, Path("edge-tts"))

    def test_generate_voice_rejects_narration_past_crossfade_budget(self):
        with TemporaryDirectory() as directory:
            with (
                patch.object(audio, "SEGMENTS", SEGMENTS[:2]),
                patch.object(audio, "choose_voice", return_value=audio.VOICES[0]),
                patch.object(audio, "probe_duration", return_value=4.06),
                patch.object(audio.subprocess, "run", return_value=Mock()),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"hook-structure.*4\.06s.*4\.05s",
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
                patch.object(audio, "probe_duration", return_value=12.5),
                patch.object(audio, "timeline", return_value=(Mock(start=192.8),)),
                patch.object(audio.subprocess, "run", side_effect=write_valid_srt),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"Merged subtitles.*193\.00",
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
                patch.object(
                    audio,
                    "probe_duration",
                    side_effect=[
                        segment.seconds
                        - (TRANSITION_SECONDS if index < len(SEGMENTS) - 1 else 0)
                        - 0.5
                        for index, segment in enumerate(SEGMENTS)
                    ],
                ),
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
                self.assertIn("--rate=-2%", command)
                self.assertIn("--pitch=-2Hz", command)


class VideoFilterTest(unittest.TestCase):
    def test_motion_filters_are_deterministic(self):
        self.assertIn("zoompan", motion_filter("push"))
        self.assertIn("zoompan", motion_filter("pull"))
        self.assertIn("scale=1920:1080", motion_filter("still"))
        with self.assertRaises(ValueError):
            motion_filter("spin")

    def test_transition_offsets_account_for_crossfades(self):
        graph, video_label, audio_label = build_transition_filter(
            [3.3, 3.3, 3.4],
            0.25,
        )

        self.assertIn("offset=3.050", graph)
        self.assertIn("offset=6.100", graph)
        self.assertEqual(video_label, "[v2]")
        self.assertEqual(audio_label, "[a2]")

    def test_segments_use_fixed_duration_and_click_only_at_chapter_start(self):
        render_segments = getattr(video, "render_segments", None)
        self.assertIsNotNone(render_segments, "render_segments() must exist")
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)
            segments = (
                SEGMENTS[0],
                SEGMENTS[1],
                next(segment for segment in SEGMENTS if segment.id == "intro"),
            )
            with (
                patch.object(video, "SEGMENTS", segments),
                patch("subprocess.run") as run,
            ):
                outputs = render_segments(build_dir)

        self.assertEqual(
            outputs,
            tuple(
                build_dir / "segments" / f"{segment.id}.mp4"
                for segment in segments
            ),
        )
        self.assertEqual(run.call_count, len(segments))
        graphs = []
        for invocation, segment in zip(
            run.call_args_list,
            segments,
            strict=True,
        ):
            command = invocation.args[0]
            graph = command[command.index("-filter_complex") + 1]
            graphs.append(graph)
            self.assertEqual(command[command.index("-t") + 1], str(segment.seconds))
            self.assertIn(f"apad=pad_dur={segment.seconds}", graph)
            self.assertIn(f"atrim=0:{segment.seconds}", graph)
            self.assertEqual(invocation.kwargs, {"check": True})
        self.assertIn("sine=frequency=760", graphs[0])
        self.assertNotIn("sine=frequency=760", graphs[1])
        self.assertIn("sine=frequency=760", graphs[2])

    def test_master_crossfades_then_creates_loudness_normalized_clean_copy(self):
        compose_master = getattr(video, "compose_master", None)
        self.assertIsNotNone(compose_master, "compose_master() must exist")
        analysis = Mock()
        analysis.stderr = (
            "FFmpeg diagnostics\n"
            '{"input_i":"-25.86","input_tp":"-4.77",'
            '"input_lra":"6.70","input_thresh":"-36.31",'
            '"target_offset":"1.35"}\n'
        )
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)
            segments = SEGMENTS[:3]
            with (
                patch.object(video, "SEGMENTS", segments),
                patch(
                    "subprocess.run",
                    side_effect=(Mock(), analysis, Mock()),
                ) as run,
            ):
                clean = compose_master(build_dir)

        master = build_dir / "minihud-bilibili-master.mp4"
        self.assertEqual(clean, build_dir / "minihud-bilibili-clean.mp4")
        self.assertEqual(run.call_count, 3)
        master_command = run.call_args_list[0].args[0]
        master_graph = master_command[master_command.index("-filter_complex") + 1]
        self.assertEqual(master_command.count("-i"), len(segments))
        self.assertIn("xfade=transition=fade:duration=0.250", master_graph)
        self.assertIn("acrossfade=d=0.250", master_graph)
        self.assertEqual(Path(master_command[-1]), master)
        analysis_command = run.call_args_list[1].args[0]
        analysis_filter = analysis_command[analysis_command.index("-af") + 1]
        self.assertEqual(
            analysis_filter,
            "loudnorm=I=-16:TP=-2:LRA=11:print_format=json",
        )
        self.assertEqual(
            run.call_args_list[1].kwargs,
            {"check": True, "capture_output": True, "text": True},
        )
        clean_command = run.call_args_list[2].args[0]
        self.assertEqual(clean_command[clean_command.index("-c:v") + 1], "copy")
        clean_filter = clean_command[clean_command.index("-af") + 1]
        self.assertIn("loudnorm=I=-16:TP=-2:LRA=11", clean_filter)
        self.assertIn("measured_I=-25.86", clean_filter)
        self.assertIn("measured_TP=-4.77", clean_filter)
        self.assertIn("measured_LRA=6.70", clean_filter)
        self.assertIn("measured_thresh=-36.31", clean_filter)
        self.assertIn("offset=1.35", clean_filter)
        self.assertIn("linear=true", clean_filter)
        self.assertEqual(Path(clean_command[-1]), clean)
        self.assertEqual(run.call_args_list[0].kwargs, {"check": True})
        self.assertEqual(run.call_args_list[2].kwargs, {"check": True})

    def test_subtitle_release_uses_readable_style_and_clean_audio(self):
        burn_subtitles = getattr(video, "burn_subtitles", None)
        self.assertIsNotNone(burn_subtitles, "burn_subtitles() must exist")
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)
            clean = build_dir / "minihud-bilibili-clean.mp4"
            with patch("subprocess.run") as run:
                output = burn_subtitles(build_dir, clean)

        self.assertEqual(output, build_dir / "minihud-bilibili.mp4")
        command = run.call_args.args[0]
        subtitle_filter = command[command.index("-vf") + 1]
        self.assertIn("subtitles=", subtitle_filter)
        style_source = subtitle_filter.split("force_style='", 1)[1].rsplit("'", 1)[0]
        style = dict(item.split("=", 1) for item in style_source.split(","))
        self.assertEqual(style["FontName"], "Noto Sans CJK SC")
        self.assertEqual(style["FontSize"], "30")
        self.assertEqual(style["Outline"], "1.5")
        self.assertEqual(style["Alignment"], "2")
        self.assertEqual(style["MarginV"], "44")
        self.assertEqual(command[command.index("-c:a") + 1], "copy")
        self.assertEqual(run.call_args.kwargs, {"check": True})

    def test_contact_sheet_samples_release_into_twelve_tiles(self):
        create_contact_sheet = getattr(video, "create_contact_sheet", None)
        self.assertIsNotNone(
            create_contact_sheet,
            "create_contact_sheet() must exist",
        )
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)
            with patch("subprocess.run") as run:
                output = create_contact_sheet(build_dir)

        self.assertEqual(output, build_dir / "final-contact.png")
        command = run.call_args.args[0]
        self.assertEqual(
            command[command.index("-vf") + 1],
            "fps=1/18,scale=480:270,tile=4x3",
        )
        self.assertEqual(Path(command[-1]), output)
        self.assertEqual(run.call_args.kwargs, {"check": True})


class SlidePipelineTest(unittest.TestCase):
    def test_render_cover_runs_chrome_and_jpeg_conversion(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)
            cover = build_dir / "cover.html"
            cover.write_text("<!doctype html>", encoding="utf-8")
            with (
                patch.object(pipeline, "BUILD_DIR", build_dir),
                patch.object(pipeline, "COVER_PATH", cover),
                patch.object(pipeline.subprocess, "run") as run,
            ):
                outputs = pipeline.render_cover()

        png = build_dir / "minihud-cover-1600x1000.png"
        jpg = build_dir / "minihud-cover-1600x1000.jpg"
        raw_png = build_dir / "minihud-cover-raw-1600x1087.png"
        self.assertEqual(outputs, (png, jpg))
        self.assertEqual(run.call_count, 3)
        chrome_command = run.call_args_list[0].args[0]
        self.assertIn("--window-size=1600,1087", chrome_command)
        self.assertIn(f"--screenshot={raw_png}", chrome_command)
        self.assertEqual(chrome_command[-1], cover.resolve().as_uri())
        self.assertEqual(run.call_args_list[0].kwargs, {"check": True})

        crop_command = run.call_args_list[1].args[0]
        self.assertEqual(
            crop_command,
            [
                "/usr/bin/ffmpeg",
                "-y",
                "-i",
                str(raw_png),
                "-vf",
                "crop=1600:1000:0:0",
                "-frames:v",
                "1",
                "-update",
                "1",
                str(png),
            ],
        )
        self.assertEqual(run.call_args_list[1].kwargs, {"check": True})

        jpeg_command = run.call_args_list[2].args[0]
        self.assertEqual(
            jpeg_command,
            [
                "/usr/bin/ffmpeg",
                "-y",
                "-i",
                str(png),
                "-frames:v",
                "1",
                "-update",
                "1",
                "-q:v",
                "2",
                str(jpg),
            ],
        )
        self.assertEqual(run.call_args_list[2].kwargs, {"check": True})

    def test_write_publish_guide_uses_build_directory(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)
            with patch.object(pipeline, "BUILD_DIR", build_dir):
                output = pipeline.write_publish_guide()

            self.assertEqual(output, build_dir / "bilibili-publish.md")
            self.assertEqual(output.read_text(encoding="utf-8"), build_publish_markdown())

    def test_cover_and_publish_commands_dispatch_and_print(self):
        cover_outputs = (Path("cover.png"), Path("cover.jpg"))
        publish_output = Path("publish.md")
        with (
            patch("sys.argv", ["pipeline", "cover"]),
            patch.object(pipeline, "render_cover", return_value=cover_outputs) as cover,
            patch("builtins.print") as print_output,
        ):
            pipeline.main()
        cover.assert_called_once_with()
        self.assertEqual(print_output.call_args_list, [call(path) for path in cover_outputs])

        with (
            patch("sys.argv", ["pipeline", "publish"]),
            patch.object(pipeline, "write_publish_guide", return_value=publish_output) as publish,
            patch("builtins.print") as print_output,
        ):
            pipeline.main()
        publish.assert_called_once_with()
        print_output.assert_called_once_with(publish_output)

    def test_all_command_runs_actions_in_delivery_order(self):
        actions = {
            "render_slides": (Path("slide.png"),),
            "render_voice": (Path("voice.mp3"),),
            "render_video": (Path("video.mp4"),),
            "render_cover": (Path("cover.png"), Path("cover.jpg")),
            "write_publish_guide": Path("publish.md"),
        }
        with (
            patch("sys.argv", ["pipeline", "all"]),
            patch.object(pipeline, "render_slides", return_value=actions["render_slides"]) as slides,
            patch.object(pipeline, "render_voice", return_value=actions["render_voice"]) as voice,
            patch.object(pipeline, "render_video", return_value=actions["render_video"]) as video,
            patch.object(pipeline, "render_cover", return_value=actions["render_cover"]) as cover,
            patch.object(pipeline, "write_publish_guide", return_value=actions["write_publish_guide"]) as publish,
            patch("builtins.print") as print_output,
        ):
            pipeline.main()

        slides.assert_called_once_with()
        voice.assert_called_once_with()
        video.assert_called_once_with()
        cover.assert_called_once_with()
        publish.assert_called_once_with()
        self.assertEqual(
            print_output.call_args_list,
            [
                call("slides", actions["render_slides"]),
                call("voice", actions["render_voice"]),
                call("video", actions["render_video"]),
                call("cover", actions["render_cover"]),
                call("publish", actions["write_publish_guide"]),
            ],
        )

    def test_render_video_builds_clean_captioned_and_contact_outputs(self):
        self.assertTrue(
            all(
                hasattr(pipeline, name)
                for name in (
                    "render_segments",
                    "compose_master",
                    "burn_subtitles",
                    "create_contact_sheet",
                    "render_video",
                )
            ),
            "pipeline video functions must be wired",
        )
        clean = Path("clean.mp4")
        captioned = Path("captioned.mp4")
        contact = Path("contact.png")
        with (
            patch.object(pipeline, "render_segments") as render_segments,
            patch.object(pipeline, "compose_master", return_value=clean) as compose,
            patch.object(
                pipeline,
                "burn_subtitles",
                return_value=captioned,
            ) as burn,
            patch.object(
                pipeline,
                "create_contact_sheet",
                return_value=contact,
            ) as create_contact,
        ):
            outputs = pipeline.render_video()

        self.assertEqual(outputs, (clean, captioned, contact))
        render_segments.assert_called_once_with(BUILD_DIR)
        compose.assert_called_once_with(BUILD_DIR)
        burn.assert_called_once_with(BUILD_DIR, clean)
        create_contact.assert_called_once_with(BUILD_DIR)

    def test_video_command_dispatches_and_prints_outputs(self):
        self.assertTrue(
            hasattr(pipeline, "render_video"),
            "render_video() must exist",
        )
        outputs = (Path("clean.mp4"), Path("captioned.mp4"), Path("contact.png"))
        with (
            patch("sys.argv", ["pipeline", "video"]),
            patch.object(pipeline, "render_video", return_value=outputs) as render_video,
            patch("builtins.print") as print_output,
        ):
            pipeline.main()

        render_video.assert_called_once_with()
        self.assertEqual(print_output.call_args_list, [call(path) for path in outputs])

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
        self.assertEqual(
            tuple(segment.seconds for segment in SEGMENTS),
            (
                4.3, 4.1, 4.5, 11.6, 12.4, 10.5, 13.9, 20.0, 8.3,
                13.7, 6.3, 5.6, 11.4, 9.3, 10.6, 12.9, 11.8, 13.2, 13.0,
            ),
        )
        self.assertAlmostEqual(total_base_seconds(), 197.4, places=3)
        self.assertAlmostEqual(encoded_seconds(), 192.9, places=3)
        self.assertTrue(180 <= encoded_seconds() <= 195)
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
                "range-spawn": "刷怪距离看球形范围，挂机点会直观很多。",
            },
        )
        self.assertEqual(len(copy), 847)
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
        self.assertAlmostEqual(items[1].start, 4.05, places=3)
        self.assertAlmostEqual(items[-1].end, 192.9, places=3)

    def test_every_render_request_has_a_supported_slide(self):
        requests = render_requests()
        self.assertEqual(len(requests), 19)
        self.assertTrue(all(1 <= item["slide"] <= 8 for item in requests))
        self.assertEqual(requests[-2]["state"], "video:install")
        self.assertEqual(requests[-1]["state"], "video:outro")

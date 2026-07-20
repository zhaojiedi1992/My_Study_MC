from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts.tweakeroo_video import audio, pipeline
from scripts.tweakeroo_video.audio import (
    PITCH,
    RATE,
    Cue,
    VoicePart,
    choose_voice,
    compose_voice_parts,
    format_srt_time,
    merge_cues,
    part_starts,
    parse_srt,
    split_cue,
    voice_parts,
)
from scripts.tweakeroo_video.pipeline import (
    BUILD_DIR,
    DECK_PATH,
    build_slide_url,
    render_cover,
    render_video,
    slide_path,
    verify_delivery,
    write_publish_guide,
)
from scripts.tweakeroo_video.publishing import (
    build_publish_markdown,
    chapter_lines,
)
from scripts.tweakeroo_video.storyboard import (
    PREVIEW_SEGMENT_IDS,
    SEGMENTS,
    Segment,
    encoded_seconds,
    render_requests,
    timeline,
    total_base_seconds,
)
from scripts.tweakeroo_video.video import (
    build_transition_filter,
    motion_filter,
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

    def test_hook_voice_lines_fit_one_short_breath(self):
        self.assertEqual(
            [segment.narration for segment in SEGMENTS[:3]],
            ["灵魂出窍。", "方块补上。", "矿洞看清。"],
        )

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
        soul_effect = next(
            segment for segment in SEGMENTS if segment.id == "soul-effect"
        )
        self.assertIn("看完，切回来", soul_effect.narration)

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
    def test_preview_profiles_use_restrained_dynamic_prosody(self):
        preview = {
            segment.id: voice_parts(segment)
            for segment in SEGMENTS
            if segment.id in PREVIEW_SEGMENT_IDS
        }
        self.assertEqual(
            preview["hook-soul"],
            (VoicePart("灵魂出窍。", "+6%", "+2Hz", 180),),
        )
        all_parts = tuple(
            part for parts in preview.values() for part in parts
        )
        self.assertIn("-4%", {part.rate for part in all_parts})
        self.assertIn("-2Hz", {part.pitch for part in all_parts})
        self.assertGreater(len({part.pause_ms for part in all_parts}), 3)
        self.assertTrue(
            all(120 <= part.pause_ms <= 360 for part in all_parts)
        )

    def test_unknown_segment_keeps_neutral_fallback(self):
        unknown = Segment(
            "unknown",
            "测试",
            3.0,
            1,
            "default",
            "still",
            "未知分镜。",
        )
        self.assertEqual(
            voice_parts(unknown),
            (VoicePart(unknown.narration, RATE, PITCH, 0),),
        )

    def test_every_segment_has_explicit_dynamic_voice_parts(self):
        fallback_profiles = []
        for segment in SEGMENTS:
            parts = voice_parts(segment)
            fallback = (VoicePart(segment.narration, RATE, PITCH, 0),)
            if parts == fallback:
                fallback_profiles.append(segment.id)
        self.assertEqual(fallback_profiles, [])

    def test_dynamic_parts_preserve_words_and_stay_restrained(self):
        def spoken_words(value):
            return re.sub(r"[^\w]", "", value, flags=re.UNICODE)

        rates = set()
        pitches = set()
        pauses = set()
        for segment in SEGMENTS:
            parts = voice_parts(segment)
            self.assertEqual(
                spoken_words("".join(part.text for part in parts)),
                spoken_words(segment.narration),
                segment.id,
            )
            rates.update(part.rate for part in parts)
            pitches.update(part.pitch for part in parts)
            pauses.update(part.pause_ms for part in parts)
            self.assertTrue(
                all(120 <= part.pause_ms <= 360 for part in parts),
                segment.id,
            )

        for segment_id in (
            "hook-soul",
            "hook-restock",
            "hook-gamma",
        ):
            segment = next(
                item for item in SEGMENTS if item.id == segment_id
            )
            self.assertEqual(voice_parts(segment)[0].rate, "+6%")
            self.assertEqual(voice_parts(segment)[0].pitch, "+2Hz")
        self.assertTrue(
            {"+2%", "+1%", "+0%", "-1%", "-2%"} <= rates
        )
        self.assertIn("-4%", rates)
        self.assertTrue(
            {"+1Hz", "+0Hz", "-1Hz", "-2Hz"} <= pitches
        )
        self.assertGreaterEqual(len(pauses), 6)

    def test_part_starts_include_unequal_inserted_pauses(self):
        parts = (
            VoicePart("第一句。", "+1%", "+1Hz", 140),
            VoicePart("第二句。", "-1%", "+0Hz", 280),
            VoicePart("第三句。", "-3%", "-1Hz", 180),
        )
        self.assertEqual(
            part_starts([1.0, 2.0, 1.5], parts),
            [0.0, 1.14, 3.42],
        )

    def test_tts_part_uses_its_own_rate_pitch_and_three_attempt_retry(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "part.mp3"
            srt = root / "part.srt"
            part = VoicePart("灵魂出窍。", "+6%", "+2Hz", 180)
            attempts = 0

            def flaky_run(command, **_kwargs):
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    raise subprocess.CalledProcessError(1, command)
                media.write_bytes(b"mp3")
                srt.write_text(
                    "1\n00:00:00,100 --> 00:00:01,000\n灵魂出窍。\n",
                    encoding="utf-8",
                )
                return Mock()

            with (
                patch.object(
                    audio.subprocess,
                    "run",
                    side_effect=flaky_run,
                ) as run,
                patch.object(audio.time, "sleep") as sleep,
            ):
                audio._generate_tts_part(
                    Path("edge-tts"),
                    "zh-CN-YunxiNeural",
                    part,
                    media,
                    srt,
                )

        command = run.call_args_list[-1].args[0]
        self.assertEqual(attempts, 2)
        self.assertIn("--rate=+6%", command)
        self.assertIn("--pitch=+2Hz", command)
        sleep.assert_called_once_with(1)

    def test_part_subtitles_are_shifted_after_audio_and_pause(self):
        groups = [
            [Cue(0.1, 0.9, "第一句。")],
            [Cue(0.1, 1.2, "第二句。")],
        ]
        parts = (
            VoicePart("第一句。", "+1%", "+1Hz", 320),
            VoicePart("第二句。", "-2%", "+0Hz", 220),
        )
        merged = merge_cues(
            groups,
            part_starts([1.0, 1.3], parts),
        )
        self.assertAlmostEqual(merged[1].start, 1.42)
        self.assertGreaterEqual(merged[1].start, merged[0].end)

    def test_voice_part_composition_inserts_each_requested_pause(self):
        parts = (
            VoicePart("第一句。", "+1%", "+1Hz", 140),
            VoicePart("第二句。", "-1%", "+0Hz", 280),
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            media = [root / "01.mp3", root / "02.mp3"]
            output = root / "segment.mp3"
            with patch.object(audio.subprocess, "run") as run:
                compose_voice_parts(
                    media,
                    [1.0, 2.0],
                    parts,
                    output,
                )

        command = run.call_args.args[0]
        graph = command[command.index("-filter_complex") + 1]
        self.assertIn("apad=pad_dur=0.140", graph)
        self.assertIn("apad=pad_dur=0.280", graph)
        self.assertIn("concat=n=2:v=0:a=1", graph)
        self.assertEqual(command[-1], str(output))

    def test_voice_part_trim_removes_only_trailing_silence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.mp3"
            output = root / "trimmed.mp3"
            with patch.object(audio.subprocess, "run") as run:
                audio.trim_voice_part(source, output)

        command = run.call_args.args[0]
        audio_filter = command[command.index("-af") + 1]
        self.assertTrue(audio_filter.startswith("areverse,"))
        self.assertTrue(audio_filter.endswith(",areverse"))
        self.assertIn("start_silence=0.08", audio_filter)
        self.assertEqual(command[-1], str(output))

    def test_trimmed_part_cues_end_with_trimmed_audio(self):
        cues = [
            Cue(0.1, 1.0, "第一句。"),
            Cue(0.95, 3.1, "第二句。"),
        ]
        fitted = audio.fit_part_cues(cues, 2.2)
        self.assertEqual(fitted[0], cues[0])
        self.assertEqual(fitted[1], Cue(0.95, 2.2, "第二句。"))

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

    def test_generate_voice_uses_dynamic_hook_prosody(self):
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
                    text = command[command.index("--text") + 1]
                    media.parent.mkdir(parents=True, exist_ok=True)
                    media.write_bytes(b"mp3")
                    srt.write_text(
                        f"1\n00:00:00,100 --> 00:00:01,000\n{text}\n",
                        encoding="utf-8",
                    )
                return Mock(stdout="")

            def fake_duration(path):
                return 2.4 if path.parent.name == "parts" else 2.58

            with (
                patch.object(
                    audio,
                    "probe_duration",
                    side_effect=fake_duration,
                ),
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
        self.assertIn("--rate=+6%", command)
        self.assertIn("--pitch=+2Hz", command)
        self.assertIn("zh-CN-YunxiNeural", command)

    def test_long_preview_segment_synthesizes_and_merges_three_parts(self):
        soul_effect = next(
            segment for segment in SEGMENTS if segment.id == "soul-effect"
        )
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
                    text = command[command.index("--text") + 1]
                    media.parent.mkdir(parents=True, exist_ok=True)
                    media.write_bytes(b"mp3")
                    srt.write_text(
                        f"1\n00:00:00,100 --> 00:00:00,900\n{text}\n",
                        encoding="utf-8",
                    )
                return Mock(stdout="")

            def fake_duration(path):
                return 3.0 if path.parent.name == "parts" else 9.6

            with (
                patch.object(
                    audio,
                    "probe_duration",
                    side_effect=fake_duration,
                ),
                patch.object(
                    audio.subprocess,
                    "run",
                    side_effect=fake_run,
                ) as run,
            ):
                audio.generate_segment_voice(
                    build_dir,
                    Path("edge-tts"),
                    (soul_effect,),
                )

            tts_commands = [
                call.args[0]
                for call in run.call_args_list
                if "--write-media" in call.args[0]
            ]
            trim_commands = [
                call.args[0]
                for call in run.call_args_list
                if "-af" in call.args[0]
                and "silenceremove" in call.args[0][
                    call.args[0].index("-af") + 1
                ]
            ]
            merged = (
                build_dir / "narration/soul-effect.srt"
            ).read_text(encoding="utf-8")

        self.assertEqual(len(tts_commands), 3)
        self.assertEqual(len(trim_commands), 3)
        compact = merged.replace("\n", "")
        for text in (
            "按下之后，人留在原地。",
            "视角出去转一圈。看建筑，查路线，都不用本人跑过去加班。",
            "看完，切回来。",
        ):
            self.assertIn(text, compact)
        self.assertLess(
            merged.index("按下之后"),
            merged.index("视角出去"),
        )
        self.assertLess(merged.index("视角出去"), merged.index("看完"))

    def test_segment_voice_retries_one_transient_tts_failure(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)
            tts_attempts = 0

            def flaky_run(command, **_kwargs):
                nonlocal tts_attempts
                if "--list-voices" in command:
                    return Mock(stdout="zh-CN-YunxiNeural Male Novel\n")
                if "--write-media" in command:
                    tts_attempts += 1
                    if tts_attempts == 1:
                        raise subprocess.CalledProcessError(1, command)
                    media = Path(command[command.index("--write-media") + 1])
                    srt = Path(
                        command[command.index("--write-subtitles") + 1]
                    )
                    media.write_bytes(b"mp3")
                    srt.write_text(
                        "1\n00:00:00,100 --> 00:00:01,000\n灵魂出窍\n",
                        encoding="utf-8",
                    )
                return Mock(stdout="")

            with (
                patch.object(audio, "probe_duration", return_value=2.1),
                patch.object(audio.subprocess, "run", side_effect=flaky_run),
                patch.object(audio.time, "sleep") as sleep,
            ):
                audio.generate_segment_voice(
                    build_dir,
                    Path("edge-tts"),
                    SEGMENTS[:1],
                )
        self.assertEqual(tts_attempts, 2)
        sleep.assert_called_once_with(1)


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

    def test_slide_capture_retries_one_transient_chrome_timeout(self):
        request = {"id": "hook-soul", "slide": 2, "state": "effect"}
        with TemporaryDirectory() as directory:
            with (
                patch.object(pipeline, "BUILD_DIR", Path(directory)),
                patch.object(
                    pipeline,
                    "render_requests",
                    return_value=[request],
                ),
                patch.object(
                    pipeline.subprocess,
                    "run",
                    side_effect=(
                        subprocess.TimeoutExpired(
                            cmd="chrome",
                            timeout=30,
                        ),
                        Mock(),
                    ),
                ) as run,
                patch.object(
                    pipeline,
                    "probe_media",
                    return_value={
                        "streams": [{"width": 1920, "height": 1080}]
                    },
                ),
            ):
                outputs = pipeline.render_slides()
        self.assertEqual(len(outputs), 1)
        self.assertEqual(run.call_count, 2)
        self.assertTrue(
            all(call.kwargs["timeout"] == 30 for call in run.call_args_list)
        )

    def test_publish_guide_is_written_inside_build_directory(self):
        with TemporaryDirectory() as directory:
            with patch.object(pipeline, "BUILD_DIR", Path(directory)):
                output = write_publish_guide()
            self.assertEqual(output, Path(directory) / "bilibili-publish.md")
            self.assertIn(
                "Tweakeroo 不只会灵魂出窍",
                output.read_text(encoding="utf-8"),
            )

    def test_render_cover_dispatches_both_ratios(self):
        with TemporaryDirectory() as directory:
            with (
                patch.object(pipeline, "BUILD_DIR", Path(directory)),
                patch.object(pipeline.subprocess, "run") as run,
            ):
                outputs = render_cover()
        self.assertEqual(len(outputs), 4)
        self.assertEqual(run.call_count, 6)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertTrue(
            any("--window-size=1600,1087" in command for command in commands)
        )
        self.assertTrue(
            any("--window-size=1600,1287" in command for command in commands)
        )

    def test_render_video_returns_clean_release_and_contact_sheet(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)
            clean = build_dir / "tweakeroo-bilibili-clean.mp4"
            release = build_dir / "tweakeroo-bilibili.mp4"
            contact = build_dir / "final-contact.png"
            with (
                patch.object(pipeline, "BUILD_DIR", build_dir),
                patch.object(pipeline, "render_segments") as segments,
                patch.object(
                    pipeline,
                    "compose_master",
                    return_value=clean,
                ),
                patch.object(
                    pipeline,
                    "burn_subtitles",
                    return_value=release,
                ),
                patch.object(
                    pipeline,
                    "create_contact_sheet",
                    return_value=contact,
                ),
            ):
                outputs = render_video()
        segments.assert_called_once_with(build_dir)
        self.assertEqual(outputs, (clean, release, contact))

    def test_delivery_verification_rejects_missing_outputs(self):
        with TemporaryDirectory() as directory:
            with patch.object(pipeline, "BUILD_DIR", Path(directory)):
                with self.assertRaisesRegex(RuntimeError, "Missing delivery"):
                    verify_delivery()


class PublishingTest(unittest.TestCase):
    def test_cover_sources_have_click_contract_and_exact_dimensions(self):
        cases = (
            ("cover.html", "width:1600px", "height:1000px"),
            ("cover-4x3.html", "width:1600px", "height:1200px"),
        )
        for filename, width, height in cases:
            source = (
                ROOT / "scripts/tweakeroo_video" / filename
            ).read_text(encoding="utf-8")
            for phrase in (
                width,
                height,
                "别再",
                "手动了",
                "Tweakeroo · 5 个高频功能",
                "自动补货",
                "快速换甲",
                "矿洞提亮",
            ):
                self.assertIn(phrase, source)
            self.assertLessEqual(source.count("<img"), 2)

    def test_publish_copy_is_searchable_specific_and_conversion_focused(self):
        copy = build_publish_markdown()
        for phrase in (
            "Tweakeroo 不只会灵魂出窍！自动补货、换胸甲这 5 个功能真省事",
            "Minecraft Java 版 26.2",
            "Tweakeroo 26.2-0.29.2",
            "MaLiLib 0.29.2",
            "不同版本",
            "服务器规则",
            "收藏",
            "关注",
            "你原来完全没用过的是哪一个",
        ):
            self.assertIn(phrase, copy)
        self.assertNotIn("必装", copy)
        self.assertNotIn("无敌", copy)

    def test_chapters_are_strictly_increasing(self):
        clocks = []
        for line in chapter_lines():
            clock, _ = line.split(" ", 1)
            minutes, seconds = map(int, clock.split(":"))
            self.assertLess(seconds, 60)
            clocks.append(minutes * 60 + seconds)
        self.assertTrue(all(a < b for a, b in zip(clocks, clocks[1:])))


class VideoTest(unittest.TestCase):
    def test_motion_filters_preserve_1080p_and_thirty_fps(self):
        for name in ("still", "push", "pull"):
            source = motion_filter(name)
            self.assertIn("1920", source)
            self.assertIn("1080", source)
            self.assertIn("fps=30", source)
        with self.assertRaises(ValueError):
            motion_filter("spin")

    def test_transition_graph_has_video_and_audio_crossfades(self):
        graph, video_label, audio_label = build_transition_filter(
            [3.0, 3.0, 3.0],
            0.25,
        )
        self.assertEqual(
            graph.count("xfade=transition=fade:duration=0.25"),
            2,
        )
        self.assertEqual(graph.count("acrossfade=d=0.25"), 2)
        self.assertTrue(video_label.startswith("[v"))
        self.assertTrue(audio_label.startswith("[a"))

    def test_subtitle_style_is_pc_video_readable(self):
        source = (
            ROOT / "scripts/tweakeroo_video/video.py"
        ).read_text(encoding="utf-8")
        for phrase in (
            "Noto Sans CJK SC",
            "FontSize=20",
            "MarginV=30",
            "loudnorm=I=-16:TP=-1",
        ):
            self.assertIn(phrase, source)


class CliContractTest(unittest.TestCase):
    def test_pipeline_exposes_all_production_actions_and_voice_gate(self):
        source = (
            ROOT / "scripts/tweakeroo_video/pipeline.py"
        ).read_text(encoding="utf-8")
        for action in (
            '"slides"',
            '"voice-preview"',
            '"voice"',
            '"video"',
            '"cover"',
            '"publish"',
            '"verify"',
            '"all"',
        ):
            self.assertIn(action, source)
        self.assertIn("--voice-approved", source)
        self.assertIn("approve voice-preview.mp3", source)
        self.assertIn('if __name__ == "__main__"', source)


if __name__ == "__main__":
    unittest.main()

# Tweakeroo Dynamic Narration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fixed whole-segment TTS cadence with a Yunxi-based, restrained conversational preview that uses semantic voice parts, varied prosody, unequal pauses, and correctly shifted subtitles.

**Architecture:** `audio.py` owns a small `VoicePart` model and preview-specific delivery profiles. Each part is synthesized independently, then a focused composition helper inserts silence, merges actual SRT timings, and emits the existing segment-level MP3/SRT interface so the full video pipeline remains compatible.

**Tech Stack:** Python 3.12 standard library, `unittest`, Edge TTS 7.2.8, FFmpeg, FFprobe.

## Global Constraints

- Keep `zh-CN-YunxiNeural` as the first-choice voice.
- Use the confirmed restrained conversational style, not an energetic presenter voice.
- Hook delivery is approximately `+6%` and `+2Hz`; ordinary explanation varies only slightly; Gamma punchline is approximately `-4%` and `-2Hz`.
- Pauses vary between 120 and 360 ms and follow meaning rather than a fixed interval.
- Generate only the approximately 25-second preview in this round; do not generate full narration or video.
- Keep existing three-attempt TTS retry, segment-duration, subtitle-width, and tail-silence protections.
- Do not modify or commit the user's existing MiniHUD changes or `.gitignore` change.

## File Structure

- Modify `scripts/tweakeroo_video/audio.py`: voice-part data, dynamic profile selection, part synthesis, audio concatenation, and subtitle-offset composition.
- Modify `tests/test_tweakeroo_video.py`: behavior tests for delivery profiles, subtitle offsets, TTS part calls, retries, and compatibility.
- Create build artifacts only under `build/tweakeroo-video/`: preserve the first preview as `voice-preview-fixed-original.mp3`, then write the new audition to the existing `voice-preview.mp3` contract.

---

### Task 1: Model the restrained conversational delivery

**Files:**
- Modify: `scripts/tweakeroo_video/audio.py`
- Test: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Produces: `VoicePart(text: str, rate: str, pitch: str, pause_ms: int)`.
- Produces: `voice_parts(segment: Segment) -> tuple[VoicePart, ...]`.
- Preserves: segments without a dynamic profile fall back to one part using `RATE`, `PITCH`, and zero inserted pause.

- [ ] **Step 1: Write the failing delivery-profile tests**

Add `PITCH`, `RATE`, `VoicePart`, and `voice_parts` to the import list in `tests/test_tweakeroo_video.py`, then add:

```python
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

    def test_non_preview_segment_keeps_neutral_fallback(self):
        intro = next(segment for segment in SEGMENTS if segment.id == "intro")
        self.assertEqual(
            voice_parts(intro),
            (VoicePart(intro.narration, RATE, PITCH, 0),),
        )
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
python -m unittest \
  tests.test_tweakeroo_video.AudioTest.test_preview_profiles_use_restrained_dynamic_prosody \
  tests.test_tweakeroo_video.AudioTest.test_non_preview_segment_keeps_neutral_fallback -v
```

Expected: both tests error because `VoicePart` and `voice_parts` do not exist.

- [ ] **Step 3: Add the minimal model and three preview profiles**

In `scripts/tweakeroo_video/audio.py`, add after `Cue`:

```python
@dataclass(frozen=True)
class VoicePart:
    text: str
    rate: str
    pitch: str
    pause_ms: int


_DYNAMIC_VOICE_PARTS = {
    "hook-soul": (
        VoicePart("灵魂出窍。", "+6%", "+2Hz", 180),
    ),
    "soul-effect": (
        VoicePart("按下之后，人留在原地。", "+1%", "+1Hz", 140),
        VoicePart(
            "视角出去转一圈。看建筑，查路线，都不用本人跑过去加班。",
            "-1%",
            "+0Hz",
            280,
        ),
        VoicePart("看完，切回来。", "-3%", "-1Hz", 180),
    ),
    "gamma-on": (
        VoicePart(
            "开启后，方块和道路立刻清楚很多。",
            "+1%",
            "+1Hz",
            320,
        ),
        VoicePart("不过，矿洞是亮了。", "-2%", "+0Hz", 220),
        VoicePart(
            "刷怪规则并没有被你说服。该插的火把，还是得插。",
            "-4%",
            "-2Hz",
            160,
        ),
    ),
}


def voice_parts(segment: Segment) -> tuple[VoicePart, ...]:
    return _DYNAMIC_VOICE_PARTS.get(
        segment.id,
        (VoicePart(segment.narration, RATE, PITCH, 0),),
    )
```

- [ ] **Step 4: Run the tests and verify GREEN**

Run the Step 2 command again.

Expected: both tests pass.

- [ ] **Step 5: Commit the profile model**

```bash
git add -- scripts/tweakeroo_video/audio.py tests/test_tweakeroo_video.py
git commit -m "feat: model dynamic Tweakeroo voice delivery"
```

---

### Task 2: Compose independently synthesized parts and shifted subtitles

**Files:**
- Modify: `scripts/tweakeroo_video/audio.py`
- Test: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Produces: `part_starts(durations: list[float], parts: tuple[VoicePart, ...]) -> list[float]`.
- Produces: `compose_voice_parts(media_paths: list[Path], durations: list[float], parts: tuple[VoicePart, ...], output: Path) -> None`.
- Produces: `_generate_tts_part(edge_tts: Path, voice: str, part: VoicePart, media: Path, srt: Path) -> None` with the existing three-attempt retry.
- Consumes: existing `merge_cues`, `cues_to_srt`, `probe_duration`, `FFMPEG`, and `time.sleep`.

- [ ] **Step 1: Write failing tests for timing and real command construction**

Add `part_starts` to the `scripts.tweakeroo_video.audio` import list in the test file, then add:

```python
    def test_part_starts_include_unequal_inserted_pauses(self):
        parts = (
            VoicePart("第一句。", "+1%", "+1Hz", 140),
            VoicePart("第二句。", "-1%", "+0Hz", 280),
            VoicePart("第三句。", "-3%", "-1Hz", 180),
        )
        self.assertEqual(part_starts([1.0, 2.0, 1.5], parts), [0.0, 1.14, 3.42])

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
                patch.object(audio.subprocess, "run", side_effect=flaky_run) as run,
                patch.object(audio.time, "sleep") as sleep,
            ):
                audio._generate_tts_part(
                    Path("edge-tts"), "zh-CN-YunxiNeural", part, media, srt
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
        merged = merge_cues(groups, part_starts([1.0, 1.3], parts))
        self.assertEqual(merged[1].start, 1.42)
        self.assertGreaterEqual(merged[1].start, merged[0].end)
```

- [ ] **Step 2: Run the three tests and verify RED**

Run:

```bash
python -m unittest \
  tests.test_tweakeroo_video.AudioTest.test_part_starts_include_unequal_inserted_pauses \
  tests.test_tweakeroo_video.AudioTest.test_tts_part_uses_its_own_rate_pitch_and_three_attempt_retry \
  tests.test_tweakeroo_video.AudioTest.test_part_subtitles_are_shifted_after_audio_and_pause -v
```

Expected: tests error because `part_starts` and `_generate_tts_part` do not exist.

- [ ] **Step 3: Implement part timing, TTS retry, and FFmpeg composition**

Add to `scripts/tweakeroo_video/audio.py`:

```python
def part_starts(
    durations: list[float],
    parts: tuple[VoicePart, ...],
) -> list[float]:
    if len(durations) != len(parts):
        raise ValueError("Voice-part durations and definitions differ")
    starts = []
    cursor = 0.0
    for duration, part in zip(durations, parts, strict=True):
        if duration <= 0:
            raise ValueError("Voice-part duration must be positive")
        starts.append(round(cursor, 6))
        cursor += duration + part.pause_ms / 1000
    return starts


def _generate_tts_part(
    edge_tts: Path,
    voice: str,
    part: VoicePart,
    media: Path,
    srt: Path,
) -> None:
    command = [
        str(edge_tts),
        "--voice", voice,
        f"--rate={part.rate}",
        f"--pitch={part.pitch}",
        "--text", part.text,
        "--write-media", str(media),
        "--write-subtitles", str(srt),
    ]
    for attempt in range(3):
        try:
            subprocess.run(command, check=True)
            return
        except subprocess.CalledProcessError:
            if attempt == 2:
                raise
            time.sleep(1)


def compose_voice_parts(
    media_paths: list[Path],
    durations: list[float],
    parts: tuple[VoicePart, ...],
    output: Path,
) -> None:
    if not (len(media_paths) == len(durations) == len(parts)):
        raise ValueError("Voice-part media, durations, and definitions differ")
    command = [FFMPEG, "-y"]
    graph = []
    labels = []
    for index, (media, duration, part) in enumerate(
        zip(media_paths, durations, parts, strict=True)
    ):
        command.extend(["-i", str(media)])
        end = duration + part.pause_ms / 1000
        label = f"part{index}"
        graph.append(
            f"[{index}:a]aresample=24000,aformat=channel_layouts=mono,"
            f"apad=pad_dur={part.pause_ms / 1000:.3f},"
            f"atrim=0:{end:.6f}[{label}]"
        )
        labels.append(f"[{label}]")
    graph.append(
        "".join(labels)
        + f"concat=n={len(labels)}:v=0:a=1[voice]"
    )
    command.extend([
        "-filter_complex", ";".join(graph),
        "-map", "[voice]", "-c:a", "libmp3lame", "-b:a", "192k",
        str(output),
    ])
    subprocess.run(command, check=True)
```

- [ ] **Step 4: Run the tests and verify GREEN**

Run the Step 2 command again.

Expected: all three tests pass.

- [ ] **Step 5: Commit the part-composition helpers**

```bash
git add -- scripts/tweakeroo_video/audio.py tests/test_tweakeroo_video.py
git commit -m "feat: compose dynamic Tweakeroo voice parts"
```

---

### Task 3: Integrate dynamic parts with the existing segment interface

**Files:**
- Modify: `scripts/tweakeroo_video/audio.py`
- Modify: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Changes: `generate_segment_voice(...)` synthesizes every `voice_parts(segment)`, writes `narration/parts/<segment>-NN.mp3|srt`, and emits the same `narration/<segment>.mp3|srt` outputs as before.
- Preserves: `generate_voice_preview(build_dir, edge_tts) -> Path`, `generate_voice(...)`, and `compose_narration(...)` signatures.

- [ ] **Step 1: Replace the fixed-prosody test with failing dynamic integration tests**

Replace `test_generate_voice_uses_approved_prosody` and add the long-part test below. The fake isolates only Edge TTS and FFmpeg; the assertions inspect the real segment SRT produced by `generate_segment_voice`:

```python
    def test_generate_voice_uses_dynamic_hook_prosody(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)

            def fake_run(command, **_kwargs):
                if "--list-voices" in command:
                    return Mock(stdout="zh-CN-YunxiNeural Male Novel\n")
                if "--write-media" in command:
                    media = Path(command[command.index("--write-media") + 1])
                    srt = Path(command[command.index("--write-subtitles") + 1])
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
                patch.object(audio, "probe_duration", side_effect=fake_duration),
                patch.object(audio.subprocess, "run", side_effect=fake_run) as run,
            ):
                audio.generate_segment_voice(
                    build_dir, Path("edge-tts"), SEGMENTS[:1]
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
                    srt = Path(command[command.index("--write-subtitles") + 1])
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
                patch.object(audio, "probe_duration", side_effect=fake_duration),
                patch.object(audio.subprocess, "run", side_effect=fake_run) as run,
            ):
                audio.generate_segment_voice(
                    build_dir, Path("edge-tts"), (soul_effect,)
                )

            tts_commands = [
                call.args[0]
                for call in run.call_args_list
                if "--write-media" in call.args[0]
            ]
            merged = (
                build_dir / "narration/soul-effect.srt"
            ).read_text(encoding="utf-8")

        self.assertEqual(len(tts_commands), 3)
        for text in (
            "按下之后，人留在原地。",
            "视角出去转一圈。看建筑，查路线，都不用本人跑过去加班。",
            "看完，切回来。",
        ):
            self.assertIn(text, merged)
        self.assertLess(
            merged.index("按下之后"),
            merged.index("视角出去"),
        )
        self.assertLess(merged.index("视角出去"), merged.index("看完"))
```

- [ ] **Step 2: Run the integration tests and verify RED**

Run:

```bash
python -m unittest \
  tests.test_tweakeroo_video.AudioTest.test_generate_voice_uses_dynamic_hook_prosody \
  tests.test_tweakeroo_video.AudioTest.test_long_preview_segment_synthesizes_and_merges_three_parts -v
```

Expected: FAIL because `generate_segment_voice` still synthesizes the entire segment once with fixed `RATE` and `PITCH`.

- [ ] **Step 3: Refactor `generate_segment_voice` to use parts**

Replace `generate_segment_voice` with:

```python
def generate_segment_voice(
    build_dir: Path,
    edge_tts: Path,
    segments: tuple[Segment, ...],
) -> tuple[Path, ...]:
    narration_dir = build_dir / "narration"
    parts_dir = narration_dir / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    voice = choose_voice(edge_tts)
    outputs = []
    for segment in segments:
        parts = voice_parts(segment)
        part_media = []
        part_cues = []
        durations = []
        for index, part in enumerate(parts, 1):
            media = parts_dir / f"{segment.id}-{index:02d}.mp3"
            srt = parts_dir / f"{segment.id}-{index:02d}.srt"
            _generate_tts_part(edge_tts, voice, part, media, srt)
            part_media.append(media)
            durations.append(probe_duration(media))
            part_cues.append(
                parse_srt(srt.read_text(encoding="utf-8"), f"{segment.id} part {index}")
            )

        output_media = narration_dir / f"{segment.id}.mp3"
        output_srt = narration_dir / f"{segment.id}.srt"
        starts = part_starts(durations, parts)
        compose_voice_parts(part_media, durations, parts, output_media)
        cues = merge_cues(part_cues, starts)
        output_srt.write_text(cues_to_srt(cues), encoding="utf-8")

        duration = probe_duration(output_media)
        allowed = _allowed_voice_seconds(segment)
        if duration <= 0 or duration > allowed + 1e-9:
            raise RuntimeError(
                f"Narration {segment.id} is {duration:.2f}s; "
                f"allowed maximum is {allowed:.2f}s"
            )
        tail = allowed - duration
        if tail > MAX_TAIL_SILENCE_SECONDS:
            raise RuntimeError(
                f"Narration {segment.id} leaves {tail:.2f}s tail; "
                f"maximum is {MAX_TAIL_SILENCE_SECONDS:.2f}s"
            )
        final_cues = parse_srt(
            output_srt.read_text(encoding="utf-8"), segment.id
        )
        validate_cues(
            final_cues,
            segment.id,
            max_end=allowed,
            allow_overlaps=True,
        )
        outputs.append(output_media)
    return tuple(outputs)
```

- [ ] **Step 4: Run focused and full Tweakeroo tests**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.AudioTest -v
python -m unittest tests.test_tweakeroo_video -v
```

Expected: all AudioTest tests pass, then all Tweakeroo video tests pass with no errors.

- [ ] **Step 5: Commit integration**

```bash
git add -- scripts/tweakeroo_video/audio.py tests/test_tweakeroo_video.py
git commit -m "feat: synthesize Tweakeroo narration by semantic part"
```

---

### Task 4: Generate and verify the second-round audition

**Files:**
- Preserve: `build/tweakeroo-video/voice-preview-fixed-original.mp3`
- Regenerate: `build/tweakeroo-video/voice-preview.mp3`
- Inspect: `build/tweakeroo-video/narration/parts/`

**Interfaces:**
- Consumes: `python -m scripts.tweakeroo_video.pipeline voice-preview`.
- Produces: the new 20–27 second dynamic Yunxi audition at the existing preview path.

- [ ] **Step 1: Preserve the first audition without overwriting an existing backup**

Run:

```bash
cp --no-clobber --preserve=all \
  build/tweakeroo-video/voice-preview.mp3 \
  build/tweakeroo-video/voice-preview-fixed-original.mp3
```

Expected: both files exist and the backup retains the first audition.

- [ ] **Step 2: Generate only the dynamic preview**

Run:

```bash
python -m scripts.tweakeroo_video.pipeline voice-preview
```

Expected: Edge TTS generates seven semantic parts and FFmpeg writes `build/tweakeroo-video/voice-preview.mp3`; no full narration or video command runs.

- [ ] **Step 3: Verify media and subtitle contracts**

Run:

```bash
ffprobe -v error \
  -show_entries format=duration,bit_rate \
  -show_entries stream=codec_name,sample_rate,channels \
  -of default=nw=1 \
  build/tweakeroo-video/voice-preview.mp3
python -m unittest tests.test_tweakeroo_video -v
```

Expected: MP3 audio, positive bitrate, duration between 20 and 27 seconds, and all Tweakeroo video tests pass.

- [ ] **Step 4: Inspect delivery boundaries before handoff**

Listen for these exact acceptance points:

1. “灵魂出窍” is quick and lightly lifted, not shouted.
2. The soul explanation has a natural action → use → punchline curve.
3. Gamma pauses at “不过”, then lands the server-rule joke more slowly and lower.
4. No word is clipped at a part boundary, and pauses do not sound like disconnected recordings.

If a boundary is clipped or disconnected, change only that part's wording, rate, pitch, or pause and repeat Task 4. Do not add post-processing speed changes.

- [ ] **Step 5: Commit any final source-only tuning**

If Task 4 required a source adjustment:

```bash
git add -- scripts/tweakeroo_video/audio.py tests/test_tweakeroo_video.py
git commit -m "fix: tune restrained Tweakeroo voice cadence"
```

Do not commit `build/tweakeroo-video/` media.

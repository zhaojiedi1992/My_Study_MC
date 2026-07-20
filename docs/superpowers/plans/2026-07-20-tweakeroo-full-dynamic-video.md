# Tweakeroo Full Dynamic Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the approved restrained Yunxi delivery to all 20 storyboard segments and produce the complete verified Bilibili video package.

**Architecture:** Keep `storyboard.py` as the timeline and narration source of truth while `audio.py` explicitly describes how every segment is spoken through `VoicePart` tuples. Reuse the tested per-part TTS, trailing-silence trim, controlled pause, subtitle-offset, segment-duration, video-composition, and delivery-verification pipeline.

**Tech Stack:** Python 3.12, `unittest`, Edge TTS 7.2.8, FFmpeg 6.1, FFprobe, headless Chrome, HTML/CSS presentation source.

## Global Constraints

- Use `zh-CN-YunxiNeural` and the user-approved restrained conversational style.
- All 20 segment IDs must have explicit dynamic profiles; no segment may use the fixed whole-segment fallback.
- Use only small ordinary-explanation variation, approximately `-2%` to `+2%`; reserve `+6%/+2Hz` for the three hook lines and `-4%/-2Hz` for punchlines or strict reminders.
- Every configured pause must be 120–360 ms and pauses must not all share one value.
- Preserve narration meaning exactly; punctuation may change for delivery, but normalized words may not be added, removed, or reordered.
- Do not apply whole-file post-generation speed changes.
- Keep each segment inside its existing allowed timeline and retain 0–1.5 seconds of visual tail.
- Produce 1920×1080, 30 fps, H.264/AAC video of 196–205 seconds, approximately `-16 LUFS`, with true peak no higher than `-1 dBTP`.
- Do not modify or commit `.gitignore` or any file under `scripts/minihud_video/` or `tests/test_minihud_video.py`.

## File Structure

- Modify `scripts/tweakeroo_video/audio.py`: expand `_DYNAMIC_VOICE_PARTS` to all 20 storyboard segments.
- Modify `tests/test_tweakeroo_video.py`: verify full profile coverage, word preservation, dynamic range, and pause range.
- Generate under `build/tweakeroo-video/`: complete narration, merged SRT, segment videos, clean master, subtitle release, contact sheet, covers, and publishing guide.
- Preserve `build/tweakeroo-video/voice-preview-dynamic-yunxi.mp3` as the approved voice reference.

---

### Task 1: Define explicit delivery for all 20 segments

**Files:**
- Modify: `scripts/tweakeroo_video/audio.py`
- Test: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Consumes: `SEGMENTS`, `VoicePart`, and `voice_parts(segment)`.
- Produces: `_DYNAMIC_VOICE_PARTS` with a key for every `Segment.id`.
- Preserves: concatenated `VoicePart.text` matches `Segment.narration` after punctuation and whitespace normalization.

- [ ] **Step 1: Write failing full-profile tests**

Add `import re` to `tests/test_tweakeroo_video.py`, then add:

```python
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

        for segment_id in ("hook-soul", "hook-restock", "hook-gamma"):
            segment = next(item for item in SEGMENTS if item.id == segment_id)
            self.assertEqual(voice_parts(segment)[0].rate, "+6%")
            self.assertEqual(voice_parts(segment)[0].pitch, "+2Hz")
        self.assertTrue({"+2%", "+1%", "+0%", "-1%", "-2%"} <= rates)
        self.assertIn("-4%", rates)
        self.assertTrue({"+1Hz", "+0Hz", "-1Hz", "-2Hz"} <= pitches)
        self.assertGreaterEqual(len(pauses), 6)
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
python3 -m unittest \
  tests.test_tweakeroo_video.AudioTest.test_every_segment_has_explicit_dynamic_voice_parts \
  tests.test_tweakeroo_video.AudioTest.test_dynamic_parts_preserve_words_and_stay_restrained -v
```

Expected: `test_every_segment_has_explicit_dynamic_voice_parts` fails with the 17 segment IDs that still use the fallback, and the preservation test fails because those fallbacks have a zero pause.

- [ ] **Step 3: Replace `_DYNAMIC_VOICE_PARTS` with the complete map**

Use the following exact profiles in `scripts/tweakeroo_video/audio.py`:

```python
_DYNAMIC_VOICE_PARTS = {
    "hook-soul": (
        VoicePart("灵魂出窍。", "+6%", "+2Hz", 180),
    ),
    "hook-restock": (
        VoicePart("方块补上。", "+6%", "+2Hz", 180),
    ),
    "hook-gamma": (
        VoicePart("矿洞看清。", "+6%", "+2Hz", 180),
    ),
    "intro": (
        VoicePart("这就是 Tweakeroo。", "+2%", "+1Hz", 160),
        VoicePart("这里不念配置表。", "+0%", "+0Hz", 220),
        VoicePart(
            "只挑真正能用上的场景，把几十页设置翻译成人话。",
            "-1%", "+0Hz", 180,
        ),
    ),
    "soul-config": (
        VoicePart("第一个，灵魂出窍。", "+2%", "+1Hz", 180),
        VoicePart("先给它配个顺手的快捷键。", "+0%", "+0Hz", 200),
        VoicePart("我这里是，左 Alt 加 C。", "-1%", "+0Hz", 220),
        VoicePart(
            "你用自己不冲突、又记得住的就行。",
            "-2%", "-1Hz", 180,
        ),
    ),
    "soul-effect": (
        VoicePart("按下之后，人留在原地。", "+1%", "+1Hz", 140),
        VoicePart(
            "视角出去转一圈。看建筑，查路线，都不用本人跑过去加班。",
            "-1%", "+0Hz", 280,
        ),
        VoicePart("看完，切回来。", "-3%", "-1Hz", 180),
    ),
    "elytra-auto": (
        VoicePart("第二个，自动切换鞘翅。", "+2%", "+1Hz", 180),
        VoicePart("先打开自动鞘翅选项。", "+0%", "+0Hz", 180),
        VoicePart(
            "飞行时，让模组帮你处理装备切换。",
            "-1%", "+0Hz", 160,
        ),
    ),
    "elytra-chest": (
        VoicePart(
            "再给胸甲交换设个快捷键。我这里是，左 Alt 加 W。",
            "+0%", "+0Hz", 220,
        ),
        VoicePart("落地后按一下，换回胸甲。", "+1%", "+0Hz", 200),
        VoicePart(
            "至少，苦力怕不会替你提醒。",
            "-3%", "-1Hz", 280,
        ),
        VoicePart(
            "快捷键只是示例，按自己的键位改。",
            "-1%", "-1Hz", 160,
        ),
    ),
    "restock-config": (
        VoicePart("第三个，自动补货。", "+2%", "+1Hz", 180),
        VoicePart(
            "开启预先补货，再设置触发阈值。",
            "+0%", "+0Hz", 200,
        ),
        VoicePart(
            "我这里用六，只是演示，不是标准答案。",
            "-2%", "-1Hz", 160,
        ),
    ),
    "restock-threshold": (
        VoicePart("手里的同类方块，接近阈值。", "+1%", "+0Hz", 160),
        VoicePart("模组就会去背包里，找补给。", "+0%", "+0Hz", 220),
        VoicePart(
            "连续建造时，不用等最后一个放完，才开背包。",
            "-1%", "-1Hz", 160,
        ),
    ),
    "restock-done": (
        VoicePart("你看，数量从七，补到十九。", "+2%", "+1Hz", 180),
        VoicePart("手里的建筑节奏，没断。", "+0%", "+0Hz", 220),
        VoicePart(
            "背包里的同类物品，终于知道主动来上班了。",
            "-3%", "-1Hz", 180,
        ),
    ),
    "click-left": (
        VoicePart("第四个，快速点击。", "+2%", "+1Hz", 160),
        VoicePart("左键和右键，分开设置。", "+0%", "+0Hz", 180),
        VoicePart(
            "快速左键适合重复挖掘或攻击测试。",
            "-1%", "+0Hz", 220,
        ),
        VoicePart("次数别一上来拉满。", "-3%", "-1Hz", 160),
    ),
    "click-right": (
        VoicePart(
            "快速右键适合连续放置或交互。",
            "+1%", "+0Hz", 180,
        ),
        VoicePart(
            "它只是重复输入，不是万能加速器。",
            "-1%", "-1Hz", 220,
        ),
        VoicePart("单人随你调。", "+1%", "+0Hz", 180),
        VoicePart("多人服先看规则。", "-2%", "-1Hz", 240),
        VoicePart(
            "别把连点器，当机关枪。",
            "-4%", "-2Hz", 160,
        ),
    ),
    "gamma-config": (
        VoicePart("第五个，Gamma 亮度。", "+2%", "+1Hz", 160),
        VoicePart("打开覆盖并设置数值。", "+0%", "+0Hz", 180),
        VoicePart(
            "我这里用十六，先从看得舒服开始。",
            "-1%", "+0Hz", 160,
        ),
    ),
    "gamma-off": (
        VoicePart(
            "关闭时，夜里和矿洞保留原本的昏暗。",
            "+0%", "+0Hz", 220,
        ),
        VoicePart("氛围很到位。", "+1%", "+1Hz", 180),
        VoicePart(
            "找路，也确实有点费眼睛。",
            "-3%", "-1Hz", 160,
        ),
    ),
    "gamma-on": (
        VoicePart(
            "开启后，方块和道路立刻清楚很多。",
            "+1%", "+1Hz", 320,
        ),
        VoicePart("不过，矿洞是亮了。", "-2%", "+0Hz", 220),
        VoicePart(
            "刷怪规则并没有被你说服。该插的火把，还是得插。",
            "-4%", "-2Hz", 160,
        ),
    ),
    "setup": (
        VoicePart(
            "想照着设置，只记住这条路线。",
            "+1%", "+0Hz", 180,
        ),
        VoicePart("X 加 C，进配置。", "+0%", "+0Hz", 180),
        VoicePart(
            "搜索功能名，打开开关，再设置快捷键和参数。",
            "-1%", "+0Hz", 220,
        ),
        VoicePart(
            "一次只改一个，回游戏确认效果。",
            "+0%", "+0Hz", 240,
        ),
        VoicePart(
            "别在菜单里，把自己调迷路。",
            "-3%", "-1Hz", 160,
        ),
    ),
    "install": (
        VoicePart(
            "安装时，让游戏、Tweakeroo 和 MaLiLib 版本对应。",
            "-1%", "+0Hz", 220,
        ),
        VoicePart(
            "它是客户端模组，但服务器规则优先。",
            "-2%", "-1Hz", 240,
        ),
        VoicePart(
            "自动操作和连点，使用前先看说明。",
            "-2%", "-1Hz", 160,
        ),
    ),
    "recap": (
        VoicePart(
            "灵魂出窍，换甲，补货，连点，Gamma。",
            "+2%", "+1Hz", 180,
        ),
        VoicePart("五项都在这里。", "+0%", "+0Hz", 180),
        VoicePart(
            "先收藏，设置时回来对照。",
            "-1%", "+0Hz", 160,
        ),
    ),
    "outro": (
        VoicePart(
            "不想装完模组，还自己翻几十页菜单？",
            "+1%", "+1Hz", 220,
        ),
        VoicePart("就关注我。", "-1%", "+0Hz", 200),
        VoicePart(
            "我继续把复杂配置翻译成人话。",
            "+0%", "+0Hz", 220,
        ),
        VoicePart(
            "评论告诉我，这五个里，你没用过哪一个。",
            "-1%", "-1Hz", 160,
        ),
    ),
}
```

- [ ] **Step 4: Run focused and full tests**

Run:

```bash
python3 -m unittest \
  tests.test_tweakeroo_video.AudioTest.test_every_segment_has_explicit_dynamic_voice_parts \
  tests.test_tweakeroo_video.AudioTest.test_dynamic_parts_preserve_words_and_stay_restrained -v
python3 -m unittest tests.test_tweakeroo_video -v
```

Expected: both focused tests pass, followed by all Tweakeroo tests passing.

- [ ] **Step 5: Commit the full delivery map**

```bash
git add -- scripts/tweakeroo_video/audio.py tests/test_tweakeroo_video.py
git commit -m "feat: extend dynamic Tweakeroo voice to full video"
```

---

### Task 2: Generate and validate complete narration and SRT

**Files:**
- Generate: `build/tweakeroo-video/narration/*.mp3`
- Generate: `build/tweakeroo-video/narration/*.srt`
- Generate: `build/tweakeroo-video/subtitles/tweakeroo.zh-CN.srt`
- Generate: `build/tweakeroo-video/tweakeroo-narration.mp3`

**Interfaces:**
- Consumes: `python3 -m scripts.tweakeroo_video.pipeline voice --voice-approved`.
- Produces: 20 segment MP3/SRT pairs, merged full-timeline SRT, and a 200-second narration track.

- [ ] **Step 1: Generate full approved narration**

Run:

```bash
python3 -m scripts.tweakeroo_video.pipeline voice --voice-approved
```

Expected: every segment completes its duration and tail checks; the command prints 20 segment MP3 paths, the merged SRT path, and `tweakeroo-narration.mp3`.

- [ ] **Step 2: Verify generated counts and media duration**

Run:

```bash
find build/tweakeroo-video/narration -maxdepth 1 -name '*.mp3' | wc -l
find build/tweakeroo-video/narration -maxdepth 1 -name '*.srt' | wc -l
ffprobe -v error -show_entries format=duration,bit_rate \
  -show_entries stream=codec_name,sample_rate,channels \
  -of default=nw=1 build/tweakeroo-video/tweakeroo-narration.mp3
```

Expected: `20`, `20`, MP3 audio, 48 kHz stereo composed narration, and duration 200 seconds within MP3 container tolerance.

- [ ] **Step 3: Re-run the full Tweakeroo tests after real TTS generation**

Run:

```bash
python3 -m unittest tests.test_tweakeroo_video -v
```

Expected: all tests pass.

---

### Task 3: Render the clean master and subtitle release

**Files:**
- Generate: `build/tweakeroo-video/segments/*.mp4`
- Generate: `build/tweakeroo-video/tweakeroo-bilibili-clean.mp4`
- Generate: `build/tweakeroo-video/tweakeroo-bilibili.mp4`
- Generate: `build/tweakeroo-video/final-contact.png`

**Interfaces:**
- Consumes: existing 20 slide PNGs, segment narration, merged SRT, and the storyboard timeline.
- Produces: clean master, burned-subtitle release, and a 4×3 visual contact sheet.

- [ ] **Step 1: Render all segment videos and both masters**

Run:

```bash
python3 -m scripts.tweakeroo_video.pipeline video
```

Expected: 20 segment MP4 files and the three listed delivery outputs are printed; FFmpeg exits zero.

- [ ] **Step 2: Verify both video stream contracts**

Run once for each master:

```bash
ffprobe -v error -show_streams -show_format -of json \
  build/tweakeroo-video/tweakeroo-bilibili-clean.mp4
ffprobe -v error -show_streams -show_format -of json \
  build/tweakeroo-video/tweakeroo-bilibili.mp4
```

Expected: both are 1920×1080, 30 fps, H.264 video with AAC audio and 196–205 seconds duration.

- [ ] **Step 3: Inspect the final contact sheet**

Open `build/tweakeroo-video/final-contact.png` with the local image viewer. Confirm all 12 tiles contain intentional video frames with no black frame, broken screenshot, unexpected crop, missing Chinese text, or subtitle outside the safe area.

---

### Task 4: Refresh packaging and run final delivery verification

**Files:**
- Regenerate: `build/tweakeroo-video/tweakeroo-cover-1600x1000.png|jpg`
- Regenerate: `build/tweakeroo-video/tweakeroo-cover-1600x1200.png|jpg`
- Regenerate: `build/tweakeroo-video/bilibili-publish.md`
- Verify: all files required by `verify_delivery()`.

**Interfaces:**
- Consumes: existing approved cover HTML, publishing copy, final videos, source screenshots, and loudness analyzer.
- Produces: a complete upload-ready Bilibili package.

- [ ] **Step 1: Refresh covers and publishing guide**

Run:

```bash
python3 -m scripts.tweakeroo_video.pipeline cover
python3 -m scripts.tweakeroo_video.pipeline publish
```

Expected: four cover files and `bilibili-publish.md` are printed.

- [ ] **Step 2: Run the delivery verifier**

Run:

```bash
python3 -m scripts.tweakeroo_video.pipeline verify
```

Expected: JSON reports valid clean/release streams, 10 source images, integrated loudness between -17 and -15 LUFS, and true peak no higher than -1 dBTP.

- [ ] **Step 3: Run presentation, browser, and video tests**

Run:

```bash
python3 -m unittest \
  tests.test_tweakeroo_presentation \
  tests.test_tweakeroo_video -v
node --test tests/tweakeroo_presentation_browser_test.cjs
```

Expected: all Python and browser tests pass.

- [ ] **Step 4: Confirm source scope and deliverable list**

Run:

```bash
git status --short
git log -n 8 --pretty=format:'%h %s'
ls -lh \
  build/tweakeroo-video/tweakeroo-bilibili.mp4 \
  build/tweakeroo-video/tweakeroo-bilibili-clean.mp4 \
  build/tweakeroo-video/tweakeroo-narration.mp3 \
  build/tweakeroo-video/subtitles/tweakeroo.zh-CN.srt \
  build/tweakeroo-video/tweakeroo-cover-1600x1000.png \
  build/tweakeroo-video/tweakeroo-cover-1600x1200.png \
  build/tweakeroo-video/bilibili-publish.md \
  build/tweakeroo-video/final-contact.png
```

Expected: source status shows only the user's pre-existing `.gitignore` and MiniHUD changes; all eight delivery paths exist and are non-empty.


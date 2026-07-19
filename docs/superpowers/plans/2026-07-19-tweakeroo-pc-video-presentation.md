# Tweakeroo PC Video Presentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline, PC-only, eight-slide Tweakeroo HTML presentation that foregrounds all ten supplied screenshots and exposes deterministic interactive/video-export states.

**Architecture:** Keep the deliverable as one self-contained `index.html` beside the supplied PNG files. A small state controller owns the active slide, each feature page's media state, focus zoom, keyboard navigation, URL query synchronization, and export mode; Python tests validate the static contract, while a Chrome DevTools Protocol test validates runtime behavior and 16:9 layouts.

**Tech Stack:** Semantic HTML5, inline CSS, vanilla JavaScript, Python `unittest`, Node.js with headless Google Chrome over CDP.

## Global Constraints

- Create exactly eight slides in `source/MOD介绍/tweakeroo/index.html`.
- Feature order is fixed: 灵魂出窍 → 自动切换鞘翅与胸甲 → 自动补货 → 快速点击 → Gamma.
- Target PC viewports are `1920×1080` and `1280×720`; mobile layout and touch navigation are out of scope.
- Use all ten existing `2880×1800` PNG files without renaming or modifying them.
- Keep screenshot media at roughly 68%–74% of each feature page's content width.
- Keep the page offline: no remote fonts, stylesheets, scripts, images, video, or iframe resources.
- Support `slide`, `state`, and `export` query parameters with stable refresh behavior.
- Export mode hides navigation and interaction hints without shifting the 16:9 composition.
- User keybindings `Left Alt + C` and `Left Alt + W` are examples, not mod defaults.
- Fast-click multiplayer risk and Gamma's client-only light boundary remain visibly stated.

---

### Task 1: Static presentation contract and eight-slide content

**Files:**
- Create: `tests/test_tweakeroo_presentation.py`
- Create: `source/MOD介绍/tweakeroo/index.html`

**Interfaces:**
- Consumes: the ten PNG files already present in `source/MOD介绍/tweakeroo/`.
- Produces: eight unique `.slide` sections with IDs `s1` through `s8`, local image references, ordered feature copy, `#deck`, and `#nav` containers.

- [ ] **Step 1: Write the failing static contract test**

Create `tests/test_tweakeroo_presentation.py` with:

```python
from html.parser import HTMLParser
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "source/MOD介绍/tweakeroo/index.html"

EXPECTED_IMAGES = {
    "灵魂出窍配置.png", "开启灵魂出窍.png", "自动鞘翅配置.png",
    "自动补货.png", "使用到阈值了.png", "自动补货完毕.png",
    "连点配置.png", "gama亮度修改.png", "关闭ganma的.png",
    "启用ganam的.png",
}


class DeckParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slide_ids = []
        self.assets = []
        self.image_alts = []
        self.ids = set()
        self.text = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)
        if "slide" in values.get("class", "").split():
            self.slide_ids.append(element_id)
        if tag in {"img", "script", "link", "video", "audio", "source", "iframe"}:
            target = values.get("src") or values.get("href")
            if target:
                self.assets.append(target)
        if tag == "img":
            self.image_alts.append(values.get("alt", ""))

    def handle_data(self, data):
        self.text.append(data)


class TweakerooPresentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        cls.parser = DeckParser()
        cls.parser.feed(cls.html)
        cls.copy = re.sub(r"\s+", " ", " ".join(cls.parser.text))

    def test_has_exactly_eight_unique_slides(self):
        self.assertEqual(self.parser.slide_ids, [f"s{index}" for index in range(1, 9)])

    def test_feature_order_and_required_copy(self):
        phrases = ("灵魂出窍", "自动切换鞘翅", "自动补货", "快速点击", "Gamma 亮度")
        positions = [self.copy.index(phrase) for phrase in phrases]
        self.assertEqual(positions, sorted(positions))
        for phrase in ("Left Alt + C", "Left Alt + W", "阈值 6", "点击次数 10", "不会改变真实光照"):
            self.assertIn(phrase, self.copy)

    def test_all_supplied_images_are_used_and_native_size(self):
        image_assets = {asset for asset in self.parser.assets if asset.endswith(".png")}
        self.assertEqual(image_assets, EXPECTED_IMAGES)
        for name in EXPECTED_IMAGES:
            path = HTML_PATH.parent / name
            self.assertTrue(path.is_file(), name)
            with path.open("rb") as stream:
                stream.read(16)
                width, height = struct.unpack(">II", stream.read(8))
            self.assertEqual((width, height), (2880, 1800), name)

    def test_is_offline_and_pc_only(self):
        remote = [asset for asset in self.parser.assets if asset.startswith(("http:", "https:", "//"))]
        self.assertEqual(remote, [])
        self.assertNotIn("@media(max-width", self.html.replace(" ", ""))
        self.assertTrue({"deck", "nav"}.issubset(self.parser.ids))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the static test and verify it fails**

Run:

```bash
python -m unittest tests.test_tweakeroo_presentation -v
```

Expected: ERROR with `FileNotFoundError` for `source/MOD介绍/tweakeroo/index.html`.

- [ ] **Step 3: Create the minimal semantic deck**

Create `source/MOD介绍/tweakeroo/index.html` with:

```html
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tweakeroo｜五个实用功能</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#020711;color:#f8fafc}
body{font-family:"Microsoft YaHei","Noto Sans SC",system-ui,sans-serif}
#deck{position:fixed;inset:0}.slide{position:absolute;inset:0;display:none}.slide.active{display:flex}
#nav{position:fixed;left:50%;bottom:18px;transform:translateX(-50%)}
</style>
</head>
<body>
<main id="deck">
  <section class="slide active" id="s1"><h1>Tweakeroo</h1><p>观察 · 飞行 · 续航 · 连点 · 亮度</p><img src="开启灵魂出窍.png" alt="灵魂出窍时玩家留在原地"></section>
  <section class="slide" id="s2"><h2>01 灵魂出窍</h2><p>示例快捷键 Left Alt + C</p><img src="灵魂出窍配置.png" alt="灵魂出窍快捷键配置"><img src="开启灵魂出窍.png" alt="开启灵魂出窍后的游戏效果"></section>
  <section class="slide" id="s3"><h2>02 自动切换鞘翅</h2><p>胸甲交换示例 Left Alt + W</p><img src="自动鞘翅配置.png" alt="自动切换鞘翅与胸甲快捷键配置"></section>
  <section class="slide" id="s4"><h2>03 自动补货</h2><p>提前补货，阈值 6</p><img src="自动补货.png" alt="自动补货参数配置"><img src="使用到阈值了.png" alt="物品数量到达补货阈值"><img src="自动补货完毕.png" alt="自动补货完成后的物品数量"></section>
  <section class="slide" id="s5"><h2>04 快速点击</h2><p>左右键独立设置，当前点击次数 10。多人服先确认规则。</p><img src="连点配置.png" alt="快速左右键连点配置"></section>
  <section class="slide" id="s6"><h2>05 Gamma 亮度</h2><p>看清矿洞，但不会改变真实光照。</p><img src="gama亮度修改.png" alt="Gamma 亮度参数配置"><img src="关闭ganma的.png" alt="Gamma 关闭效果"><img src="启用ganam的.png" alt="Gamma 开启效果"></section>
  <section class="slide" id="s7"><h2>快速上手</h2><p>X + C 打开配置，再设置开关、快捷键和参数。</p></section>
  <section class="slide" id="s8"><h2>安装与多人边界</h2><p>Minecraft 26.2 · Fabric · Tweakeroo 26.2-0.29.2 · MaLiLib 0.29.2</p></section>
</main>
<nav id="nav" aria-label="幻灯片导航"></nav>
</body>
</html>
```

- [ ] **Step 4: Run the static test and verify it passes**

Run:

```bash
python -m unittest tests.test_tweakeroo_presentation -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit the static contract and deck shell**

```bash
git add -- tests/test_tweakeroo_presentation.py source/MOD介绍/tweakeroo/index.html source/MOD介绍/tweakeroo/*.png
git commit -m "feat: add Tweakeroo presentation content shell"
```

---

### Task 2: Screenshot-first layout, focus animation, and deterministic state controller

**Files:**
- Modify: `tests/test_tweakeroo_presentation.py`
- Modify: `source/MOD介绍/tweakeroo/index.html`

**Interfaces:**
- Consumes: slide IDs `s1`–`s8` and state keys `effect/config`, `auto/chestplate`, `config/threshold/done`, `left/right`, `off/on/config`.
- Produces: `go(index: number, options?: {sync?: boolean}): void`, `setFeatureState(slideNumber: number, state: string, options?: {sync?: boolean}): void`, `resetFocus(): void`, and `applyQuery(): void`.

- [ ] **Step 1: Extend the static test for interaction hooks and video state**

Add these tests to `TweakerooPresentationTest`:

```python
    def test_interaction_and_video_contract(self):
        for token in (
            "function go(", "function setFeatureState(", "function resetFocus(",
            "function applyQuery(", "history.replaceState", "ArrowRight",
            "PageDown", "data-state", "data-focus", "body.export",
        ):
            self.assertIn(token, self.html)

    def test_feature_pages_are_screenshot_first(self):
        for slide_id in ("s2", "s3", "s4", "s5", "s6"):
            match = re.search(
                rf'<section[^>]+id="{slide_id}".*?</section>',
                self.html,
                re.S,
            )
            self.assertIsNotNone(match)
            self.assertIn("media-stage", match.group(0))
            self.assertIn("feature-copy", match.group(0))
        self.assertIn("grid-template-columns:minmax(0,2.25fr) minmax(300px,.9fr)", self.html)
        self.assertIn("transform:scale(", self.html)
```

- [ ] **Step 2: Run the targeted tests and verify they fail**

Run:

```bash
python -m unittest tests.test_tweakeroo_presentation.TweakerooPresentationTest.test_interaction_and_video_contract tests.test_tweakeroo_presentation.TweakerooPresentationTest.test_feature_pages_are_screenshot_first -v
```

Expected: both tests fail because the state controller and screenshot-first layout do not exist.

- [ ] **Step 3: Implement the state controller**

Add this controller at the end of `index.html`:

```html
<script>
const slides=[...document.querySelectorAll(".slide")];
const stateBySlide=new Map([[2,"effect"],[3,"auto"],[4,"config"],[5,"left"],[6,"off"]]);
let cur=0;

function syncUrl(){
  const url=new URL(location.href);
  url.searchParams.set("slide",String(cur+1));
  const state=stateBySlide.get(cur+1);
  if(state)url.searchParams.set("state",state);else url.searchParams.delete("state");
  history.replaceState(null,"",url);
}

function go(index,{sync=true}={}){
  cur=Math.max(0,Math.min(slides.length-1,index));
  slides.forEach((slide,slideIndex)=>{
    const active=slideIndex===cur;
    slide.classList.toggle("active",active);
    slide.inert=!active;
    slide.setAttribute("aria-hidden",String(!active));
  });
  document.querySelectorAll(".dot").forEach((dot,indexValue)=>dot.classList.toggle("on",indexValue===cur));
  if(sync)syncUrl();
}

function setFeatureState(slideNumber,state,{sync=true}={}){
  const slide=document.getElementById("s"+slideNumber);
  const allowed=[...slide.querySelectorAll("[data-state]")].map(button=>button.dataset.state);
  if(!allowed.includes(state))state=allowed[0];
  stateBySlide.set(slideNumber,state);
  slide.dataset.view=state;
  slide.querySelectorAll("[data-state]").forEach(button=>{
    const selected=button.dataset.state===state;
    button.classList.toggle("selected",selected);
    button.setAttribute("aria-pressed",String(selected));
  });
  if(sync)syncUrl();
}

function resetFocus(){
  const slide=slides[cur];
  slide.removeAttribute("data-focus");
  slide.querySelectorAll("[data-focus]").forEach(button=>button.setAttribute("aria-pressed","false"));
  syncUrl();
}

function applyQuery(){
  const params=new URLSearchParams(location.search);
  document.body.classList.toggle("export",params.get("export")==="1");
  const requested=Math.max(1,Math.min(slides.length,Number(params.get("slide"))||1));
  go(requested-1,{sync:false});
  const state=params.get("state");
  if(state&&stateBySlide.has(requested))setFeatureState(requested,state,{sync:false});
}

document.addEventListener("keydown",event=>{
  if(event.key==="Escape"){resetFocus();return}
  if(["ArrowRight","PageDown"].includes(event.key)||(event.key===" "&&!event.target.closest("button"))){event.preventDefault();go(cur+1)}
  if(["ArrowLeft","PageUp"].includes(event.key)){event.preventDefault();go(cur-1)}
});

document.querySelectorAll("[data-state]").forEach(button=>button.addEventListener("click",()=>{
  setFeatureState(Number(button.closest(".slide").id.slice(1)),button.dataset.state);
}));
applyQuery();
</script>
```

Add per-slide `data-view` attributes, state buttons, focus buttons, media layers, and a `.feature-layout` grid using:

```css
.feature-layout{display:grid;grid-template-columns:minmax(0,2.25fr) minmax(300px,.9fr);gap:24px;width:min(1440px,92vw);height:min(720px,74vh)}
.media-stage{position:relative;min-width:0;overflow:hidden;border:1px solid #ffffff2b;border-radius:22px;background:#020711}
.media-layer{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transform:scale(1.045);transition:opacity .34s ease,transform .8s cubic-bezier(.22,1,.36,1)}
.media-layer.active{opacity:1;transform:scale(1)}
.media-stage.focused .media-layer.active{transform:scale(1.6);transform-origin:var(--focus-x,50%) var(--focus-y,50%)}
.feature-copy{display:flex;flex-direction:column;min-width:300px;padding:26px;border:1px solid #ffffff24;border-radius:22px;background:#081321e8}
```

- [ ] **Step 4: Run the static suite and verify it passes**

Run:

```bash
python -m unittest tests.test_tweakeroo_presentation -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit interaction and image presentation behavior**

```bash
git add -- tests/test_tweakeroo_presentation.py source/MOD介绍/tweakeroo/index.html
git commit -m "feat: add Tweakeroo image states and focus animation"
```

---

### Task 3: Headless-browser verification for PC layouts and video export

**Files:**
- Create: `tests/tweakeroo_presentation_browser_test.cjs`
- Modify: `source/MOD介绍/tweakeroo/index.html`

**Interfaces:**
- Consumes: global `slides`, `cur`, `go`, `setFeatureState`, and URL query parameters.
- Produces: deterministic browser behavior at `1920×1080` and `1280×720`, plus `/tmp/tweakeroo-slide-*.png` review renders.

- [ ] **Step 1: Write the failing browser assertions**

Create `tests/tweakeroo_presentation_browser_test.cjs` using headless `google-chrome --remote-debugging-pipe`. The test must:

```javascript
const requiredStates = [
  { slide: 2, state: "config" },
  { slide: 3, state: "chestplate" },
  { slide: 4, state: "done" },
  { slide: 5, state: "right" },
  { slide: 6, state: "on" },
];
```

Construct the local URL with `pathToFileURL(path.resolve("source/MOD介绍/tweakeroo/index.html"))`, append `?slide=N&state=STATE`, and assert that `cur === N - 1`, the matching slide is active, its `data-view` equals `STATE`, all images have `naturalWidth === 2880`, and no runtime console errors occurred.

At both target viewports, iterate through all eight slides and evaluate:

```javascript
({
  documentOverflow: document.documentElement.scrollWidth > innerWidth ||
                    document.documentElement.scrollHeight > innerHeight,
  slideOverflow: document.querySelector(".slide.active").scrollWidth > innerWidth ||
                 document.querySelector(".slide.active").scrollHeight > innerHeight,
})
```

Assert both values are false.

Navigate to `?export=1&slide=6&state=on`; assert `body.export` is present, `#nav` is hidden, animations are disabled, and the active slide's bounding rectangle is unchanged from non-export mode.

- [ ] **Step 2: Run the browser test and verify it fails**

Run:

```bash
node tests/tweakeroo_presentation_browser_test.cjs
```

Expected: FAIL on at least one missing state, layout assertion, or export-mode assertion.

- [ ] **Step 3: Finish PC sizing and export behavior**

Add:

```css
body.export *{animation:none!important;transition:none!important}
body.export #nav,body.export .interaction-hint{visibility:hidden}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
```

Ensure `.slide` uses fixed viewport-relative padding, `.feature-layout` remains within both target viewports, every long line wraps, and no mobile breakpoint is added.

Capture representative screenshots in the browser test:

```javascript
const shot = await send("Page.captureScreenshot", { format: "png" }, sessionId);
fs.writeFileSync("/tmp/tweakeroo-slide-6-on.png", Buffer.from(shot.data, "base64"));
```

- [ ] **Step 4: Run all presentation verification**

Run:

```bash
python -m unittest tests.test_tweakeroo_presentation -v
node tests/tweakeroo_presentation_browser_test.cjs
python -m unittest discover -s tests -v
```

Expected: Tweakeroo static tests pass, browser test exits 0 with a JSON summary, and the repository test suite passes without new failures.

- [ ] **Step 5: Inspect representative PC renders**

Open and visually inspect:

```text
/tmp/tweakeroo-slide-2-effect.png
/tmp/tweakeroo-slide-3-chestplate.png
/tmp/tweakeroo-slide-4-done.png
/tmp/tweakeroo-slide-6-on.png
```

Confirm screenshot prominence, readable captions, stable crop targets, no clipping, and no configuration text hidden behind the side card.

- [ ] **Step 6: Commit the verified presentation**

```bash
git add -- tests/test_tweakeroo_presentation.py tests/tweakeroo_presentation_browser_test.cjs source/MOD介绍/tweakeroo/index.html
git commit -m "test: verify Tweakeroo PC video presentation"
```

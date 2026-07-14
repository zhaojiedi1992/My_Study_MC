# MiniHUD Screenshot Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the existing eight-slide MiniHUD deck around six player scenarios, pair each scenario with real screenshots, and cover all 15 requested shape types without sacrificing offline or mobile behavior.

**Architecture:** Keep the established self-contained HTML/CSS/vanilla-JavaScript deck and its Sphinx entry point. Add optimized local WebP derivatives under the deck's own `assets/screenshots/` directory, use real screenshots as the primary stage visuals, and keep compact CSS diagrams only where one screenshot cannot explain multiple range states. Extend the existing static and Chrome DevTools Protocol tests before changing the deck.

**Tech Stack:** HTML5, CSS, vanilla JavaScript, Python `unittest`, headless Chrome/CDP, FFmpeg WebP encoder, Sphinx `html_extra_path`.

## Global Constraints

- Keep exactly 8 slides: cover, task route, and 6 player scenarios.
- Use the final scenario order: 日常游玩、外出探索、工程选址、机制规划、开始施工、基地管理.
- Include all 15 user-specified shape names verbatim in the HTML.
- Use only local assets; add no network dependency, third-party JavaScript, or video.
- Keep `source/MOD介绍/minihud/minihud.rst` linking to `index.html`.
- Do not expose `/mnt/c/Users/.../minihud.json` or raw configuration identifiers in audience-facing copy.
- Preserve the user's untracked source PNG files and `source/extra/MOD介绍/minihud/videos/`; do not delete or overwrite them.
- Keep keyboard, touch, modal-focus, reduced-motion, export, and mobile-scroll behavior.

---

## File Map

- `tests/test_minihud_presentation.py`: static content, local-asset, accessibility, and source-safety contract.
- `tests/minihud_presentation_browser_test.cjs`: live interaction, screenshot-load, desktop, and mobile contract.
- `source/extra/MOD介绍/minihud/assets/screenshots/*.webp`: optimized presentation-only derivatives.
- `source/extra/MOD介绍/minihud/index.html`: all slide markup, styling, and vanilla JavaScript interactions.
- `source/MOD介绍/minihud/minihud.rst`: Sphinx landing-page scenario summary.

### Task 1: Lock the scenario, screenshot, and shape contract

**Files:**
- Modify: `tests/test_minihud_presentation.py`
- Modify: `tests/minihud_presentation_browser_test.cjs`

**Interfaces:**
- Consumes: the current `DeckParser`, eight-slide DOM, and CDP helpers.
- Produces: assertions for `DeckParser.image_alts: list[str]`, seven required WebP asset paths, `data-shape-group`, and `data-base-view` controls.

- [ ] **Step 1: Extend the static parser and replace the final-scenario assertions**

Add image-alt collection in `DeckParser.__init__` and `handle_starttag`:

```python
self.image_alts = []

if tag == "img":
    self.image_alts.append(values.get("alt", ""))
```

Replace both scenario tuples containing `"完工排查"` with:

```python
scenarios = (
    "日常游玩", "外出探索", "工程选址",
    "机制规划", "开始施工", "基地管理",
)
```

Replace the last task phrase `"快速找到问题"` with `"快速查看与维护"`.

- [ ] **Step 2: Add the complete screenshot and shape tests**

Add these methods to `MiniHudPresentationTest`:

```python
def test_real_screenshots_are_local_accessible_and_present(self):
    required_assets = {
        "assets/screenshots/hud.webp",
        "assets/screenshots/structure.webp",
        "assets/screenshots/biome.webp",
        "assets/screenshots/beacon.webp",
        "assets/screenshots/shape.webp",
        "assets/screenshots/shulker.webp",
        "assets/screenshots/bundle.webp",
    }
    self.assertTrue(required_assets.issubset(set(self.parser.assets)))
    for relative_path in required_assets:
        self.assertTrue((HTML_PATH.parent / relative_path).is_file(), relative_path)
    for phrase in ("信息 HUD", "结构边界", "群系边界", "信标范围", "圆形", "潜影盒", "收纳袋"):
        self.assertTrue(any(phrase in alt for alt in self.parser.image_alts), phrase)

def test_all_fifteen_shape_types_are_present(self):
    shapes = (
        "立方体", "中心立方体", "圆形 / 圆柱体", "直线（方块化）",
        "球体（方块化）", "可调整生成球体", "可生成球体（>24）",
        "可消失球体（>32）", "立即消失球体（>128）",
        "可生成球体（Y 轴裁剪）", "椭球体可生成球体", "圆锥",
        "四棱锥", "方形四棱锥", "八边形棱锥",
    )
    self.assertEqual([shape for shape in shapes if shape not in self.copy], [])

def test_private_config_path_and_raw_keys_are_absent(self):
    for forbidden in (
        "/mnt/c/Users/", "AppData/Roaming/PrismLauncher", "minihud.json",
        "bundleTooltips", "shulkerBoxPreview", "shapeDiamondPyramid",
    ):
        self.assertNotIn(forbidden, self.html)
```

Update `test_scenario_controls_are_present` to require:

```python
for attribute in (
    "data-structure-view", "data-site-layer", "data-range",
    "data-shape-group", "data-base-view",
):
    self.assertIn(attribute, self.html)
```

- [ ] **Step 3: Update the browser interaction expectations**

Replace the existing building control block with:

```javascript
const shapeControlExists = await evaluate(sessionId, `Boolean(document.querySelector('[data-shape-group="spawn"]'))`);
if (!shapeControlExists) throw new Error("Shape group control is missing");
await evaluate(sessionId, `go(6); document.querySelector('[data-shape-group="spawn"]').click()`);
const building = await evaluate(sessionId, `({
  cur,
  selected: document.querySelector('[data-shape-group].selected').dataset.shapeGroup,
  group: document.getElementById('build-stage').dataset.group,
})`);
if (building.cur !== 6 || building.selected !== "spawn" || building.group !== "spawn") {
  throw new Error(`Shape group switch failed: ${JSON.stringify(building)}`);
}
```

Add after page navigation and before the initial-state assertion:

```javascript
const images = await evaluate(sessionId, `Promise.all([...document.images].map((img) =>
  img.complete && img.naturalWidth > 0
    ? Promise.resolve({ src: img.getAttribute('src'), width: img.naturalWidth })
    : new Promise((resolve) => {
        img.addEventListener('load', () => resolve({ src: img.getAttribute('src'), width: img.naturalWidth }), { once: true });
        img.addEventListener('error', () => resolve({ src: img.getAttribute('src'), width: 0 }), { once: true });
      })
))`);
if (images.length < 7 || images.some((item) => item.width === 0)) {
  throw new Error(`Screenshot loading failed: ${JSON.stringify(images)}`);
}
```

Add a base-management interaction assertion:

```javascript
await evaluate(sessionId, `go(7); document.querySelector('[data-base-view="bundle"]').click()`);
const base = await evaluate(sessionId, `({
  selected: document.querySelector('[data-base-view].selected').dataset.baseView,
  view: document.getElementById('check-stage').dataset.view,
})`);
if (base.selected !== "bundle" || base.view !== "bundle") {
  throw new Error(`Base preview switch failed: ${JSON.stringify(base)}`);
}
```

Include `images` and `base` in the final logged object.

- [ ] **Step 4: Run the new contract and confirm the expected failures**

Run:

```bash
python3 -m unittest tests/test_minihud_presentation.py -v
node tests/minihud_presentation_browser_test.cjs
```

Expected: static tests fail because the seven WebP files, `基地管理`, 15 exact shape labels, and new controls do not exist; browser test fails because `data-shape-group="spawn"` does not exist.

- [ ] **Step 5: Commit the failing contract**

```bash
git add tests/test_minihud_presentation.py tests/minihud_presentation_browser_test.cjs
git commit -m "test: define MiniHUD screenshot deck contract"
```

### Task 2: Create presentation-safe screenshot derivatives

**Files:**
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/hud.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/structure.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/biome.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/beacon.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/shape.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/shulker.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/bundle.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/hud-config.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/structure-config.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/renderer-config.webp`
- Create: `source/extra/MOD介绍/minihud/assets/screenshots/shape-config.webp`

**Interfaces:**
- Consumes: user PNGs in `source/MOD介绍/minihud/`.
- Produces: local 1600-pixel-wide WebP assets addressed as `assets/screenshots/<name>.webp` from `index.html`.

- [ ] **Step 1: Create the asset directory**

Run:

```bash
mkdir -p source/extra/MOD介绍/minihud/assets/screenshots
```

Expected: directory exists without modifying source PNGs.

- [ ] **Step 2: Encode the seven effect screenshots**

Run these commands individually:

```bash
ffmpeg -y -i source/MOD介绍/minihud/左上角展示基础信息.png -vf "scale=1600:-2:flags=lanczos" -c:v libwebp -quality 82 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/hud.webp
ffmpeg -y -i source/MOD介绍/minihud/结构效果展示图.png -vf "scale=1600:-2:flags=lanczos" -c:v libwebp -quality 82 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/structure.webp
ffmpeg -y -i source/MOD介绍/minihud/群系边界展示效果图.png -vf "scale=1600:-2:flags=lanczos" -c:v libwebp -quality 82 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/biome.webp
ffmpeg -y -i source/MOD介绍/minihud/信标范围展示.png -vf "scale=1600:-2:flags=lanczos" -c:v libwebp -quality 82 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/beacon.webp
ffmpeg -y -i source/MOD介绍/minihud/形状效果图.png -vf "scale=1600:-2:flags=lanczos" -c:v libwebp -quality 82 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/shape.webp
ffmpeg -y -i source/MOD介绍/minihud/潜影盒预览效果图.png -vf "scale=1600:-2:flags=lanczos" -c:v libwebp -quality 82 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/shulker.webp
ffmpeg -y -i source/MOD介绍/minihud/收纳预览.png -vf "scale=1600:-2:flags=lanczos" -c:v libwebp -quality 82 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/bundle.webp
```

Expected: each output is 1600 pixels wide, preserves its aspect ratio, and is materially smaller than its PNG source.

- [ ] **Step 3: Encode the four configuration screenshots**

Run:

```bash
ffmpeg -y -i source/MOD介绍/minihud/hud信息行设置页面.png -vf "scale=1400:-2:flags=lanczos" -c:v libwebp -quality 80 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/hud-config.webp
ffmpeg -y -i source/MOD介绍/minihud/结构配置.png -vf "scale=1400:-2:flags=lanczos" -c:v libwebp -quality 80 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/structure-config.webp
ffmpeg -y -i source/MOD介绍/minihud/渲染器.png -vf "scale=1400:-2:flags=lanczos" -c:v libwebp -quality 80 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/renderer-config.webp
ffmpeg -y -i source/MOD介绍/minihud/形状配置.png -vf "scale=1400:-2:flags=lanczos" -c:v libwebp -quality 80 -compression_level 6 source/extra/MOD介绍/minihud/assets/screenshots/shape-config.webp
```

Expected: four configuration images exist and remain readable when opened directly.

- [ ] **Step 4: Verify asset dimensions and total weight**

Run:

```bash
file source/extra/MOD介绍/minihud/assets/screenshots/*.webp
du -ch source/extra/MOD介绍/minihud/assets/screenshots/*.webp
```

Expected: all files report WebP; effect images are 1600 pixels wide, config images are 1400 pixels wide, and total size is below 8 MiB.

- [ ] **Step 5: Commit the derivatives only**

```bash
git add source/extra/MOD介绍/minihud/assets/screenshots
git commit -m "feat: add MiniHUD presentation screenshots"
```

### Task 3: Rebuild the deck around screenshot-backed player scenes

**Files:**
- Modify: `source/extra/MOD介绍/minihud/index.html`
- Test: `tests/test_minihud_presentation.py`
- Test: `tests/minihud_presentation_browser_test.cjs`

**Interfaces:**
- Consumes: `assets/screenshots/*.webp` and the existing `go`, modal, keyboard, wheel, and touch APIs.
- Produces: `data-shape-group` controls bound to `#build-stage[data-group]` and `data-base-view` controls bound to `#check-stage[data-view]`.

- [ ] **Step 1: Add the reusable screenshot stage styles**

Add these rules after the current `.visual-stage` rules and remove CSS-only scene rules that are no longer referenced:

```css
.shot{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center;opacity:0;transform:scale(1.015);transition:opacity .28s ease,transform .45s ease;pointer-events:none}
.shot.on{opacity:1;transform:scale(1)}
.shot-shade{position:absolute;inset:0;background:linear-gradient(90deg,transparent 48%,rgba(2,6,23,.3)),linear-gradient(0deg,rgba(2,6,23,.72),transparent 35%);pointer-events:none}
.shot-label{position:absolute;left:14px;bottom:14px;max-width:72%;padding:.52em .72em;border:1px solid rgba(255,255,255,.16);border-radius:9px;background:rgba(2,6,23,.82);color:#fff;font-size:.7rem;font-weight:900;backdrop-filter:blur(8px)}
.shot-watermark{position:absolute;right:13px;top:13px;padding:.35em .58em;border-radius:99px;background:rgba(2,6,23,.72);color:var(--accent);font-size:.62rem;font-weight:950;letter-spacing:.08em}
.group-panel{position:absolute;inset:0;display:none;padding:18px;background:linear-gradient(90deg,rgba(3,7,18,.9),rgba(3,7,18,.12) 72%)}
.group-panel.active{display:flex;flex-direction:column;justify-content:flex-end}
.shape-list{display:flex;flex-wrap:wrap;gap:6px;max-width:92%}.shape-list span{padding:.42em .62em;border:1px solid color-mix(in srgb,var(--shape-color,var(--accent)) 55%,transparent);border-radius:8px;background:rgba(2,6,23,.82);color:#f8fafc;font-size:clamp(.62rem,.78vw,.75rem);font-weight:850}
.detail-media{width:100%;margin:.8em 0 1.2em;border:1px solid rgba(255,255,255,.18);border-radius:12px}
```

For mobile, append:

```css
@media(max-width:600px){.shot-label{max-width:88%}.shape-list{max-width:100%}.shape-list span{font-size:.68rem}}
```

- [ ] **Step 2: Update the task route and six scene headings**

Keep slides `s1`–`s8` and task buttons `go(2)`–`go(7)`. Replace the sixth task label and slide-eight copy with:

```html
<em>06 · 基地管理</em><b>快速查看与维护</b><span>整理收纳、确认目标，并在效率异常时找到线索。</span>
```

Use these scene pills in order: `日常游玩`、`外出探索`、`工程选址`、`机制规划`、`开始施工`、`基地管理`.

- [ ] **Step 3: Replace slides 3–6 primary visuals with real screenshots**

Use the following markup patterns inside each existing `.visual-stage`:

```html
<img class="shot on" src="assets/screenshots/hud.webp" alt="游戏左上角显示时间、坐标、朝向、TPS/MSPT 与群系的信息 HUD">
```

```html
<img class="shot on" src="assets/screenshots/structure.webp" alt="水下结构周围显示 MiniHUD 结构边界">
<img class="shot" data-shot="config" src="assets/screenshots/structure-config.webp" alt="MiniHUD 结构显示配置页面">
```

```html
<img class="shot on" src="assets/screenshots/biome.webp" alt="游戏世界中以绿色覆盖层显示群系边界">
<img class="shot" data-shot="config" src="assets/screenshots/renderer-config.webp" alt="MiniHUD 渲染器覆盖层配置页面">
```

```html
<img class="shot on" src="assets/screenshots/beacon.webp" alt="森林中的信标与 MiniHUD 信标范围覆盖层">
```

Each screenshot stage also gets `.shot-shade`, `.shot-label`, and `.shot-watermark` elements. Preserve the range slide's conduit and spawn CSS diagrams as non-default switchable states.

- [ ] **Step 4: Build the 15-shape construction scene**

Replace slide seven's stage with:

```html
<div class="visual-stage build-stage" id="build-stage" data-group="basic" aria-label="建筑与生成范围形状切换展示">
  <img class="shot on" src="assets/screenshots/shape.webp" alt="游戏世界中使用圆形和圆柱体规划建筑">
  <div class="shot-shade"></div>
  <div class="group-panel active" data-shape-panel="basic"><div class="shape-list"><span>立方体</span><span>中心立方体</span><span>圆形 / 圆柱体</span><span>直线（方块化）</span><span>球体（方块化）</span></div></div>
  <div class="group-panel" data-shape-panel="spawn"><div class="shape-list"><span>可调整生成球体</span><span>可生成球体（&gt;24）</span><span>可消失球体（&gt;32）</span><span>立即消失球体（&gt;128）</span><span>可生成球体（Y 轴裁剪）</span><span>椭球体可生成球体</span></div></div>
  <div class="group-panel" data-shape-panel="pyramid"><div class="shape-list"><span>圆锥</span><span>四棱锥</span><span>方形四棱锥</span><span>八边形棱锥</span></div></div>
  <span class="shot-watermark">真实游戏效果</span>
</div>
```

Use three side-card buttons with `data-shape-group="basic"`, `"spawn"`, and `"pyramid"`. Add a click handler that updates selected state, `build-stage.dataset.group`, and each `[data-shape-panel]` element's `.active` class.

- [ ] **Step 5: Build the base-management scene with two real previews**

Replace slide eight's default stage with:

```html
<div class="visual-stage check-stage" id="check-stage" data-view="shulker" aria-label="基地管理内容切换">
  <img class="shot on" data-base-shot="shulker" src="assets/screenshots/shulker.webp" alt="潜影盒悬停时显示 MiniHUD 潜影盒内容预览">
  <img class="shot" data-base-shot="bundle" src="assets/screenshots/bundle.webp" alt="收纳袋悬停时显示 MiniHUD 收纳袋容量预览">
  <div class="shot-shade"></div>
  <div class="check-panel" data-base-panel="target">村民交易、目标实体、目标方块、蜂巢数量与熔炉经验</div>
  <div class="check-panel" data-base-panel="efficiency">Mob Cap、实体数量、已加载区块、延迟与 TPS/MSPT</div>
</div>
```

Use buttons with `data-base-view="shulker"`, `"bundle"`, `"target"`, and `"efficiency"`. Add a handler that updates `check-stage.dataset.view`, image `.on` state, panel visibility, and selected state. Keep Servux/Carpet as a `.tip`, not a tab.

- [ ] **Step 6: Update the detail modal content**

Add configuration images to the relevant detail bodies with local image markup such as:

```javascript
body:'<img class="detail-media" src="assets/screenshots/shape-config.webp" alt="MiniHUD 形状管理配置页面"><h3>基础形状</h3>...'
```

The shape detail must repeat all 15 exact names. The preview detail must use the title `基地管理：少开界面，快速确认` and group content under 收纳整理、目标检查、效率维护、数据来源. Keep `H`, `H + C`, MaLiLib, Servux, Carpet, 24/32/128 caveats, and “不是远程搜索 / 不使用 /locate”.

- [ ] **Step 7: Run static and browser tests until green**

Run:

```bash
python3 -m unittest tests/test_minihud_presentation.py -v
node tests/minihud_presentation_browser_test.cjs
```

Expected: all static tests pass; browser output reports 8 slides, all screenshot widths above zero, successful structure/range/shape/base switches, no console errors, and a scrollable 390×844 layout.

- [ ] **Step 8: Commit the rebuilt deck**

```bash
git add source/extra/MOD介绍/minihud/index.html
git commit -m "feat: pair MiniHUD scenarios with screenshots"
```

### Task 4: Align the Sphinx landing page and verify the build

**Files:**
- Modify: `source/MOD介绍/minihud/minihud.rst`
- Test: `tests/test_minihud_presentation.py`
- Verify: `source/extra/MOD介绍/minihud/index.html`

**Interfaces:**
- Consumes: final scenario labels and local deck assets.
- Produces: Sphinx entry copy consistent with the deck and a browsable `build/html/MOD介绍/minihud/index.html`.

- [ ] **Step 1: Update the final scenario row**

Replace the old final row with:

```rst
   * - 基地管理：快速查看与维护
     - 用潜影盒、收纳袋、地图和物品栏预览整理物资；结合目标信息、Mob Cap 与 TPS/MSPT 维护基地和机器
```

Keep the other five rows and installation/data-limit guidance.

- [ ] **Step 2: Run the static contract**

Run:

```bash
python3 -m unittest tests/test_minihud_presentation.py -v
```

Expected: all tests pass, including the new six-scenario order in both HTML and RST.

- [ ] **Step 3: Build the Sphinx site**

Run:

```bash
python3 -m sphinx -b html source build/html
```

Expected: exit code 0 and `build/html/MOD介绍/minihud/index.html` exists with `assets/screenshots/*.webp` beside it.

- [ ] **Step 4: Run final browser and whitespace verification**

Run:

```bash
node tests/minihud_presentation_browser_test.cjs
git diff --check
git status --short
```

Expected: browser test passes with no image/console errors; `git diff --check` is silent; only user-owned source PNGs and the pre-existing `videos/` directory remain untracked outside committed implementation files.

- [ ] **Step 5: Commit the landing-page alignment**

```bash
git add source/MOD介绍/minihud/minihud.rst
git commit -m "docs: align MiniHUD guide with base management"
```

- [ ] **Step 6: Start a local preview server**

Run:

```bash
python3 -m http.server 8765 --directory build/html
```

Expected: the server remains running and the preview is available at `http://127.0.0.1:8765/MOD介绍/minihud/index.html`.


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

    def test_interaction_and_video_contract(self):
        for token in (
            "function go(", "function setFeatureState(", "function resetFocus(",
            "function applyQuery(", "history.replaceState", "ArrowRight",
            "PageDown", "data-state", "data-focus", "body.export",
        ):
            self.assertIn(token, self.html)

        state_contract = {
            2: ("effect", "config"),
            3: ("auto", "chestplate"),
            4: ("config", "threshold", "done"),
            5: ("left", "right"),
            6: ("off", "on", "config"),
        }
        for slide_number, expected_states in state_contract.items():
            match = re.search(
                rf'<section[^>]+id="s{slide_number}".*?</section>',
                self.html,
                re.S,
            )
            self.assertIsNotNone(match)
            section = match.group(0)
            self.assertIn(f'data-view="{expected_states[0]}"', section)
            self.assertEqual(
                tuple(re.findall(r'<button[^>]+data-state="([^"]+)"', section)),
                expected_states,
            )

            if slide_number in (3, 5):
                self.assertEqual(section.count('<img class="media-layer'), 1)
                self.assertEqual(section.count("data-focus-x="), len(expected_states))
                self.assertEqual(section.count("data-focus-y="), len(expected_states))
            else:
                self.assertEqual(
                    tuple(re.findall(r'<img[^>]+data-media-state="([^"]+)"', section)),
                    expected_states,
                )

        for token in (
            "layer.dataset.mediaState===state",
            "dataset.focusX",
            "defaultStateBySlide.get(slideNumber)",
            "Math.trunc(Number(index))",
            'Math.trunc(Number(params.get("slide")))',
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

    def test_images_start_complete_and_focus_is_opt_in(self):
        self.assertRegex(self.html, r"\.media-layer\{[^}]*object-fit:contain")
        self.assertRegex(self.html, r"\.cover-media\{[^}]*object-fit:contain")
        for slide_id in ("s3", "s5"):
            start_tag = re.search(rf'<section[^>]+id="{slide_id}"[^>]*>', self.html)
            self.assertIsNotNone(start_tag)
            self.assertNotIn("data-focus=", start_tag.group(0))
            section = re.search(
                rf'<section[^>]+id="{slide_id}".*?</section>',
                self.html,
                re.S,
            )
            self.assertIsNotNone(section)
            self.assertNotIn('class="media-stage focused"', section.group(0))


if __name__ == "__main__":
    unittest.main()

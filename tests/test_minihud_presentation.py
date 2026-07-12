from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "source/extra/MOD介绍/minihud/index.html"
RST_PATH = ROOT / "source/MOD介绍/minihud/minihud.rst"


class DeckParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slide_ids = []
        self.assets = []
        self.detail_keys = []
        self.scene_keys = []
        self.ids = set()
        self.text = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        classes = values.get("class", "").split()
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)
        if "slide" in classes:
            self.slide_ids.append(element_id)
        if tag in {"script", "link", "img", "video", "audio", "source", "iframe"}:
            target = values.get("src") or values.get("href")
            if target:
                self.assets.append(target)
        if "data-detail" in values:
            self.detail_keys.append(values["data-detail"])
        if "data-scene" in values:
            self.scene_keys.append(values["data-scene"])

    def handle_data(self, data):
        self.text.append(data)


class MiniHudPresentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        cls.rst = RST_PATH.read_text(encoding="utf-8")
        cls.parser = DeckParser()
        cls.parser.feed(cls.html)
        cls.copy = re.sub(r"\s+", " ", " ".join(cls.parser.text))

    def test_deck_has_exactly_eight_unique_slides(self):
        self.assertEqual(len(self.parser.slide_ids), 8)
        self.assertEqual(len(set(self.parser.slide_ids)), 8)
        self.assertNotIn(None, self.parser.slide_ids)

    def test_all_feature_groups_are_present(self):
        for phrase in ("信息 HUD", "环境与网格", "范围与边界", "建筑与形状", "预览与检查"):
            self.assertIn(phrase, self.copy)

    def test_scenario_copy_is_comprehensive(self):
        required = (
            "探索", "性能排查", "光照", "群系边界", "信标", "潮涌核心",
            "随机刻", "史莱姆区块", "结构边界", "村民交易", "生成球",
            "方框", "圆柱", "方块线", "地图预览", "潜影盒", "物品栏预览",
            "Servux", "Carpet", "MaLiLib", "TPS/MSPT", "Mob Cap",
        )
        missing = [phrase for phrase in required if phrase not in self.copy]
        self.assertEqual(missing, [])

    def test_interaction_contract_is_semantic(self):
        required_ids = {"deck", "nav", "detail-modal", "detail-title", "detail-body", "detail-close"}
        self.assertTrue(required_ids.issubset(self.parser.ids))
        self.assertGreaterEqual(len(set(self.parser.detail_keys)), 5)
        self.assertTrue({"explore", "build", "performance"}.issubset(self.parser.scene_keys))
        for token in (
            "function go", "function openDetail", "function closeDetail",
            "ArrowRight", "touchstart", "prefers-reduced-motion",
        ):
            self.assertIn(token, self.html)

    def test_media_and_code_are_offline_and_audience_safe(self):
        remote_assets = [
            asset for asset in self.parser.assets
            if asset.startswith(("http://", "https://", "//"))
        ]
        self.assertEqual(remote_assets, [])
        for forbidden in ("InfoToggle.java", "RendererToggle.java", "ShapeType.java", "src/main/java"):
            self.assertNotIn(forbidden, self.html)
        self.assertNotRegex(self.html, r"<button[^>]+disabled[^>]*class=[\"'][^\"']*video")

    def test_rst_links_and_summarizes_the_deck(self):
        for phrase in (
            "index.html", "信息 HUD", "环境与网格", "范围与边界",
            "建筑与形状", "预览与检查", "Servux", "MaLiLib",
        ):
            self.assertIn(phrase, self.rst)


if __name__ == "__main__":
    unittest.main()

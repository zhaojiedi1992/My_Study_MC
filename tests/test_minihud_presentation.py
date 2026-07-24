from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "source/extra/MOD介绍/masa/minihud/index.html"
RST_PATH = ROOT / "source/MOD介绍/masa/minihud/minihud.rst"


class DeckParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slide_ids = []
        self.assets = []
        self.detail_keys = []
        self.scene_keys = []
        self.ids = set()
        self.text = []
        self.image_alts = []

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
        if tag == "img":
            self.image_alts.append(values.get("alt", ""))
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
            "俯仰角", "方块实体", "已加载区块", "Servux", "Carpet",
            "MaLiLib", "TPS/MSPT", "Mob Cap",
        )
        missing = [phrase for phrase in required if phrase not in self.copy]
        self.assertEqual(missing, [])

    def test_six_player_scenarios_drive_the_deck(self):
        scenarios = (
            "日常游玩", "外出探索", "工程选址",
            "机制规划", "开始施工", "基地管理",
        )
        for scene in scenarios:
            self.assertIn(scene, self.copy)
        positions = [self.copy.index(scene) for scene in scenarios]
        self.assertEqual(positions, sorted(positions))
        for task in (
            "总在按 F3", "结构藏进地形", "选址怕踩坑",
            "范围全靠估", "圆心半径难确定", "整理和排查太慢",
        ):
            self.assertIn(task, self.copy)

    def test_examples_support_scenes_without_becoming_scene_titles(self):
        for example in ("林地府邸", "信标", "潮涌核心", "圆形 / 圆柱体"):
            self.assertIn(example, self.copy)
        for slide_title in re.findall(
            r'<h2[^>]*class="sec-title"[^>]*>(.*?)</h2>', self.html, re.S
        ):
            plain = re.sub(r"<[^>]+>", "", slide_title)
            self.assertNotIn("林地府邸", plain)
            self.assertNotIn("信标", plain)

    def test_structure_scene_states_ability_boundary(self):
        for phrase in ("不是远程搜索", "不使用 /locate", "结构主边界", "组成部分"):
            self.assertIn(phrase, self.copy)

    def test_exported_config_informs_visuals_not_student_copy(self):
        for color in (
            "#ff6500", "#e060ff", "#ffb040",
            "#fff040", "#60ff40", "#30b0b0",
        ):
            self.assertIn(color, self.html.lower())
        for raw_name in (
            "overlayBeaconRange", "overlayStructureMainToggle",
            "shapeRenderer", "StructureToggles", "InfoTypeToggles",
        ):
            self.assertNotIn(raw_name, self.html)
        self.assertIn("H + C", self.copy)

    def test_scenario_controls_are_present(self):
        for attribute in (
            "data-structure-view", "data-site-layer", "data-range",
            "data-shape-group", "data-base-view",
        ):
            self.assertIn(attribute, self.html)

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
        for phrase in (
            "信息 HUD", "结构边界", "群系边界", "信标范围",
            "圆形", "潜影盒", "收纳袋",
        ):
            self.assertTrue(any(phrase in alt for alt in self.parser.image_alts), phrase)

    def test_screenshot_assets_keep_native_resolution(self):
        assets = (HTML_PATH.parent / "assets/screenshots").glob("*.webp")
        dimensions = {}
        for asset in assets:
            data = asset.read_bytes()
            codec = data[12:16]
            if codec == b"VP8 ":
                width = int.from_bytes(data[26:28], "little") & 0x3FFF
                height = int.from_bytes(data[28:30], "little") & 0x3FFF
            elif codec == b"VP8L":
                bits = int.from_bytes(data[21:25], "little")
                width = (bits & 0x3FFF) + 1
                height = ((bits >> 14) & 0x3FFF) + 1
            else:
                self.fail(f"Unsupported WebP codec in {asset.name}: {codec!r}")
            dimensions[asset.name] = (width, height)
        self.assertGreaterEqual(len(dimensions), 11)
        self.assertEqual(
            {name: size for name, size in dimensions.items() if size[0] < 2800},
            {},
        )

    def test_all_fifteen_shape_types_are_present(self):
        shapes = (
            "立方体", "中心立方体", "圆形 / 圆柱体", "直线（方块化）",
            "球体（方块化）", "可调整生成球体", "可生成球体（>24）",
            "可消失球体（>32）", "立即消失球体（>128）",
            "可生成球体（Y 轴裁剪）", "椭球体可生成球体", "圆锥",
            "四棱锥", "方形四棱锥", "八边形棱锥",
        )
        self.assertEqual([shape for shape in shapes if shape not in self.copy], [])

    def test_video_copy_is_problem_driven_and_versioned(self):
        required = (
            "一个 MOD", "看清隐藏规则", "遇到什么问题，就开什么功能",
            "Minecraft Java 版 26.2", "Fabric Loader", "按住 Shift",
            "收藏这份问题清单", "实用 Minecraft 模组和生存技巧",
        )
        for phrase in required:
            self.assertIn(phrase, self.copy + " " + self.rst)

    def test_multiplayer_data_copy_is_precise(self):
        for phrase in (
            "多人服需要服务器端 Servux 提供结构数据",
            "精确 TPS/MSPT",
            "Mob Cap 是数量上限，不是空间范围",
        ):
            self.assertIn(phrase, self.copy + " " + self.rst)
        for misleading in (
            "Carpet 或服务器许可",
            "Mob Cap：看玩家周围空间",
            "悬停即可预览",
        ):
            self.assertNotIn(misleading, self.copy + " " + self.rst)

    def test_video_export_states_exist_without_adding_slides(self):
        for token in (
            'data-video-card="install"',
            'data-video-card="outro"',
            'data-range="chunk"',
            "applyRequestedState",
            "video-install",
            "video-outro",
        ):
            self.assertIn(token, self.html)

    def test_private_config_path_and_raw_keys_are_absent(self):
        for forbidden in (
            "/mnt/c/Users/", "AppData/Roaming/PrismLauncher", "minihud.json",
            "bundleTooltips", "shulkerBoxPreview", "shapeDiamondPyramid",
        ):
            self.assertNotIn(forbidden, self.html)

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

    def test_rst_follows_the_six_scenario_route(self):
        scenarios = (
            "日常游玩", "外出探索", "工程选址",
            "机制规划", "开始施工", "基地管理",
        )
        positions = []
        for scene in scenarios:
            self.assertIn(scene, self.rst)
            positions.append(self.rst.index(scene))
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()

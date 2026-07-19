from pathlib import Path
import unittest

from scripts.tweakeroo_video.storyboard import (
    PREVIEW_SEGMENT_IDS,
    SEGMENTS,
    encoded_seconds,
    render_requests,
    timeline,
    total_base_seconds,
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


if __name__ == "__main__":
    unittest.main()

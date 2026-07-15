from pathlib import Path
import unittest

from scripts.minihud_video.pipeline import (
    BUILD_DIR,
    DECK_PATH,
    build_slide_url,
    slide_path,
)
from scripts.minihud_video.storyboard import (
    SEGMENTS,
    TRANSITION_SECONDS,
    encoded_seconds,
    render_requests,
    timeline,
    total_base_seconds,
)


ROOT = Path(__file__).resolve().parents[1]


class SlidePipelineTest(unittest.TestCase):
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
        self.assertAlmostEqual(total_base_seconds(), 210.0, places=3)
        self.assertAlmostEqual(encoded_seconds(), 205.5, places=3)
        self.assertEqual(TRANSITION_SECONDS, 0.25)

    def test_narration_matches_approved_scope(self):
        copy = "".join(segment.narration for segment in SEGMENTS)
        self.assertEqual(len(copy), 840)
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
        self.assertAlmostEqual(items[1].start, 3.05, places=3)
        self.assertAlmostEqual(items[-1].end, 205.5, places=3)

    def test_every_render_request_has_a_supported_slide(self):
        requests = render_requests()
        self.assertEqual(len(requests), 19)
        self.assertTrue(all(1 <= item["slide"] <= 8 for item in requests))
        self.assertEqual(requests[-2]["state"], "video:install")
        self.assertEqual(requests[-1]["state"], "video:outro")

"""Timeline for the InvMove Bilibili video."""

from dataclasses import dataclass


TRANSITION_SECONDS = 0.25
PREVIEW_SEGMENT_IDS = ("hook", "move", "install")


@dataclass(frozen=True)
class Segment:
    id: str
    chapter: str
    seconds: float
    slide: int
    motion: str
    kind: str = "still"
    button_index: int = -1
    click_delay: float = 0.0


@dataclass(frozen=True)
class TimelineItem:
    segment: Segment
    start: float
    end: float


SEGMENTS = (
    Segment("hook", "开场：打开背包，脚步不停", 9.5, 1, "push"),
    Segment("core", "核心能力：把移动带进界面", 13.0, 2, "pull"),
    Segment(
        "blocked",
        "未安装：界面打开就停下",
        7.0,
        3,
        "still",
        kind="demo",
        button_index=0,
        click_delay=1.1,
    ),
    Segment(
        "move",
        "安装后：移动中打开背包",
        9.0,
        4,
        "still",
        kind="demo",
        button_index=0,
        click_delay=1.1,
    ),
    Segment(
        "workbench",
        "安装后：工作台内继续移动",
        6.2,
        4,
        "still",
        kind="demo",
        button_index=1,
        click_delay=1.1,
    ),
    Segment("install", "安装关系：必需与可选", 13.0, 5, "pull"),
)


def encoded_seconds() -> float:
    return sum(segment.seconds for segment in SEGMENTS) - TRANSITION_SECONDS * (
        len(SEGMENTS) - 1
    )


def timeline() -> tuple[TimelineItem, ...]:
    items = []
    cursor = 0.0
    for index, segment in enumerate(SEGMENTS):
        start = cursor
        end = start + segment.seconds
        items.append(TimelineItem(segment, start, end))
        cursor = end - (TRANSITION_SECONDS if index < len(SEGMENTS) - 1 else 0)
    return tuple(items)


def render_requests() -> list[dict[str, object]]:
    return [
        {"id": segment.id, "slide": segment.slide}
        for segment in SEGMENTS
    ]

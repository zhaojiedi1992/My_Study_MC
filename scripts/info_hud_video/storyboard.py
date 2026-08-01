"""Single source of truth for the 信息 HUD Bilibili timeline."""

from dataclasses import dataclass


TRANSITION_SECONDS = 0.25


@dataclass(frozen=True)
class VoicePart:
    text: str
    rate: str
    pitch: str
    pause_ms: int


@dataclass(frozen=True)
class Segment:
    id: str
    chapter: str
    seconds: float
    kind: str
    motion: str
    voice: tuple[VoicePart, ...]
    slide: int | None = None
    state: str | None = None
    source_id: str | None = None
    source_start: float = 0.0


@dataclass(frozen=True)
class TimelineItem:
    segment: Segment
    start: float
    end: float


SEGMENTS = (
    Segment(
        "hook",
        "开场：关键判断提前出现",
        9.2,
        "slide",
        "push",
        (
            VoicePart("生存时最浪费的，不一定是挖矿，而是反复翻界面。", "+2%", "+1Hz", 220),
            VoicePart("这四个信息 HUD，把关键判断提前放到眼前。", "+3%", "+2Hz", 180),
        ),
        slide=1,
    ),
    Segment(
        "layers",
        "四层信息：自己、工具、野怪与准星",
        10.0,
        "slide",
        "pull",
        (
            VoicePart("AppleSkin 看吃下去会补多少。", "+2%", "+1Hz", 170),
            VoicePart("Show Durability 看工具还剩几次。", "+2%", "+1Hz", 170),
            VoicePart("Neat 看周围野怪的血量，Jade 看准星目标。", "+3%", "+2Hz", 180),
        ),
        slide=2,
    ),
    Segment(
        "durability_compare",
        "耐久对比：没装时只能估",
        8.0,
        "slide",
        "push",
        (
            VoicePart("先看耐久的差异。", "+3%", "+2Hz", 180),
            VoicePart("没装时只剩一条颜色，具体还能用几次得自己估。", "+1%", "+0Hz", 160),
        ),
        slide=3,
        state="durability-before",
    ),
    Segment(
        "durability_zoom",
        "耐久对比：数字直接写在图标上",
        7.0,
        "slide",
        "still",
        (
            VoicePart("装上之后，数字直接写在物品图标上。", "+4%", "+2Hz", 170),
            VoicePart("一千五百六十一点，一眼就能换工具。", "+3%", "+1Hz", 160),
        ),
        slide=3,
        state="durability-zoom",
    ),
    Segment(
        "durability_before_live",
        "实录：未安装 Show Durability",
        8.0,
        "demo",
        "still",
        (
            VoicePart("实录里，未安装时得悬停才能判断工具状态。", "+2%", "+1Hz", 180),
            VoicePart("快捷栏没有明确的剩余次数。", "-1%", "-1Hz", 160),
        ),
        source_id="durability_before",
        source_start=1.0,
    ),
    Segment(
        "durability_after_live",
        "实录：安装后显示剩余耐久",
        8.0,
        "demo",
        "still",
        (
            VoicePart("装上后，背包和快捷栏都会出现剩余耐久。", "+3%", "+2Hz", 180),
            VoicePart("物品数量和耐久数字不再混在一起。", "+1%", "+0Hz", 160),
        ),
        source_id="durability_after",
        source_start=1.0,
    ),
    Segment(
        "neat",
        "Neat：清楚周围野怪的血量",
        13.5,
        "demo",
        "still",
        (
            VoicePart("接着是 Neat，它把生命条放到实体头顶。", "+3%", "+2Hz", 180),
            VoicePart("遇到野怪时，扫一眼就清楚周围谁的血量更低。", "+2%", "+1Hz", 170),
            VoicePart("距离、是否遮挡和显示对象，都能自己设。", "-2%", "-1Hz", 160),
        ),
        source_id="neat",
        source_start=13.0,
    ),
    Segment(
        "jade_target",
        "Jade：准星目标的基础信息",
        8.5,
        "demo",
        "still",
        (
            VoicePart("Jade 不铺满全场，准星对着谁，它就讲谁。", "+3%", "+2Hz", 180),
            VoicePart("名称、来源和生命等信息会跟着目标换。", "+1%", "+0Hz", 160),
        ),
        source_id="jade",
        source_start=19.0,
    ),
    Segment(
        "jade_container",
        "Jade：熔炉与容器状态",
        8.5,
        "demo",
        "still",
        (
            VoicePart("对着熔炉和营火，还能看到正在处理的东西。", "+2%", "+1Hz", 180),
            VoicePart("这类内容依赖服务器允许提供数据。", "-2%", "-1Hz", 160),
        ),
        source_id="jade",
        source_start=36.0,
    ),
    Segment(
        "jade_spawner",
        "Jade：刷怪笼等特殊方块",
        8.0,
        "demo",
        "still",
        (
            VoicePart("刷怪笼也有自己的目标信息。", "+2%", "+1Hz", 180),
            VoicePart("它不是透视，更不会绕过服务器权限。", "-3%", "-2Hz", 160),
        ),
        source_id="jade",
        source_start=48.0,
    ),
    Segment(
        "appleskin",
        "AppleSkin：吃之前先看结果",
        13.6,
        "demo",
        "still",
        (
            VoicePart("最后是 AppleSkin。手持食物时，饥饿条会预览吃完后的变化。", "+2%", "+1Hz", 180),
            VoicePart("半透明的预测层，提示饱和度和即将补上的格数。", "+1%", "+0Hz", 170),
            VoicePart("先看结果，再决定现在要不要吃。", "-3%", "-2Hz", 160),
        ),
        source_id="appleskin",
        source_start=12.0,
    ),
    Segment(
        "ending",
        "结尾：按层选择信息 HUD",
        9.0,
        "slide",
        "pull",
        (
            VoicePart("把自己、工具、野怪和准星目标分开看，画面就不会乱。", "-1%", "-1Hz", 180),
            VoicePart("需要哪一层信息，就开哪一个。", "-3%", "-2Hz", 160),
        ),
        slide=1,
    ),
)


def encoded_seconds() -> float:
    return sum(segment.seconds for segment in SEGMENTS) - TRANSITION_SECONDS * (len(SEGMENTS) - 1)


def timeline() -> tuple[TimelineItem, ...]:
    cursor = 0.0
    items = []
    for index, segment in enumerate(SEGMENTS):
        items.append(TimelineItem(segment, cursor, cursor + segment.seconds))
        cursor += segment.seconds
        if index < len(SEGMENTS) - 1:
            cursor -= TRANSITION_SECONDS
    return tuple(items)

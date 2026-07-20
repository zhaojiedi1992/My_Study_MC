"""Single source of truth for the Tweakeroo video timeline."""

from dataclasses import dataclass


TRANSITION_SECONDS = 0.25
PREVIEW_SEGMENT_IDS = ("hook-soul", "soul-effect", "gamma-on")


@dataclass(frozen=True)
class Segment:
    id: str
    chapter: str
    seconds: float
    slide: int
    state: str
    motion: str
    narration: str


@dataclass(frozen=True)
class TimelineItem:
    segment: Segment
    start: float
    end: float


SEGMENTS = (
    Segment(
        "hook-soul",
        "冷开场",
        3.0,
        2,
        "effect",
        "push",
        "灵魂出窍。",
    ),
    Segment(
        "hook-restock",
        "冷开场",
        3.0,
        4,
        "done",
        "pull",
        "方块补上。",
    ),
    Segment(
        "hook-gamma",
        "冷开场",
        3.0,
        6,
        "on",
        "push",
        "矿洞看清。",
    ),
    Segment(
        "intro",
        "这期讲什么",
        10.0,
        1,
        "default",
        "still",
        "这就是 Tweakeroo。这里不念配置表，只挑真正能用上的场景，"
        "把几十页设置翻译成人话。",
    ),
    Segment(
        "soul-config",
        "灵魂出窍",
        11.25,
        2,
        "config",
        "still",
        "第一个，灵魂出窍。先给它配个顺手的快捷键。"
        "我这里是左 Alt 加 C。你用自己不冲突，又记得住的就行。",
    ),
    Segment(
        "soul-effect",
        "灵魂出窍",
        11.0,
        2,
        "effect",
        "push",
        "按下之后，人留在原地，视角出去转一圈。"
        "看建筑，查路线，都不用本人跑过去加班。看完，切回来。",
    ),
    Segment(
        "elytra-auto",
        "鞘翅与胸甲",
        9.5,
        3,
        "auto",
        "still",
        "第二个，自动切换鞘翅。先打开自动鞘翅选项，"
        "飞行时让模组帮你处理装备切换。",
    ),
    Segment(
        "elytra-chest",
        "鞘翅与胸甲",
        15.0,
        3,
        "chestplate",
        "still",
        "再给胸甲交换设个快捷键。我这里是左 Alt 加 W。"
        "落地后按一下换回胸甲，至少苦力怕不会替你提醒。"
        "快捷键只是示例，按自己的键位改。",
    ),
    Segment(
        "restock-config",
        "自动补货",
        10.0,
        4,
        "config",
        "still",
        "第三个，自动补货。开启预先补货，再设置触发阈值。"
        "我这里用六，只是演示，不是标准答案。",
    ),
    Segment(
        "restock-threshold",
        "自动补货",
        11.0,
        4,
        "threshold",
        "push",
        "手里的同类方块接近阈值，模组就会去背包里找补给。"
        "连续建造时，不用等最后一个放完才开背包。",
    ),
    Segment(
        "restock-done",
        "自动补货",
        10.0,
        4,
        "done",
        "pull",
        "你看，数量从七补到十九，手里的建筑节奏没断。"
        "背包里的同类物品，终于知道主动来上班了。",
    ),
    Segment(
        "click-left",
        "快速左右键",
        11.0,
        5,
        "left",
        "still",
        "第四个，快速点击。左键和右键分开设置。"
        "快速左键适合重复挖掘或攻击测试，次数别一上来拉满。",
    ),
    Segment(
        "click-right",
        "快速左右键",
        14.0,
        5,
        "right",
        "still",
        "快速右键适合连续放置或交互。它只是重复输入，不是万能加速器。"
        "单人随你调。多人服先看规则，别把连点器当机关枪。",
    ),
    Segment(
        "gamma-config",
        "Gamma 亮度",
        9.0,
        6,
        "config",
        "still",
        "第五个，Gamma 亮度。打开覆盖并设置数值。"
        "我这里用十六，先从看得舒服开始。",
    ),
    Segment(
        "gamma-off",
        "Gamma 亮度",
        10.0,
        6,
        "off",
        "pull",
        "关闭时，夜里和矿洞保留原本的昏暗。"
        "氛围很到位，找路也确实有点费眼睛。",
    ),
    Segment(
        "gamma-on",
        "Gamma 亮度",
        12.0,
        6,
        "on",
        "push",
        "开启后，方块和道路立刻清楚很多。不过矿洞是亮了，"
        "刷怪规则并没有被你说服，该插的火把还是得插。",
    ),
    Segment(
        "setup",
        "快速上手",
        16.0,
        7,
        "default",
        "still",
        "想照着设置，只记住这条路线。X 加 C 进配置，搜索功能名，"
        "打开开关，再设置快捷键和参数。一次只改一个，回游戏确认效果。"
        "别在菜单里把自己调迷路。",
    ),
    Segment(
        "install",
        "安装与边界",
        12.0,
        8,
        "default",
        "still",
        "安装时，让游戏、Tweakeroo 和 MaLiLib 版本对应。"
        "它是客户端模组，但服务器规则优先。自动操作和连点，使用前先看说明。",
    ),
    Segment(
        "recap",
        "收藏与关注",
        8.25,
        1,
        "default",
        "pull",
        "灵魂出窍，换甲，补货，连点，Gamma。"
        "五项都在这里。先收藏，设置时回来对照。",
    ),
    Segment(
        "outro",
        "收藏与关注",
        12.75,
        8,
        "default",
        "push",
        "不想装完模组，还自己翻几十页菜单，就关注我。"
        "我继续把复杂配置翻译成人话。"
        "评论告诉我，这五个里你没用过哪一个。",
    ),
)


def total_base_seconds() -> float:
    return sum(segment.seconds for segment in SEGMENTS)


def encoded_seconds() -> float:
    return total_base_seconds() - TRANSITION_SECONDS * (len(SEGMENTS) - 1)


def timeline() -> tuple[TimelineItem, ...]:
    items = []
    cursor = 0.0
    for index, segment in enumerate(SEGMENTS):
        start = cursor
        end = start + segment.seconds
        items.append(TimelineItem(segment, start, end))
        if index < len(SEGMENTS) - 1:
            cursor = end - TRANSITION_SECONDS
    return tuple(items)


def render_requests() -> list[dict[str, object]]:
    return [
        {"id": segment.id, "slide": segment.slide, "state": segment.state}
        for segment in SEGMENTS
    ]

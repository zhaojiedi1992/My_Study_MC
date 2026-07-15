from dataclasses import dataclass


TRANSITION_SECONDS = 0.25


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
    Segment("hook-structure", "冷开场", 3.3, 4, "structure:on", "push", "结构藏进地形里，看不清完整范围？"),
    Segment("hook-shape", "冷开场", 3.3, 7, "shape:basic", "pull", "圆心、半径和高度，还在靠目测？"),
    Segment("hook-preview", "冷开场", 3.4, 8, "base:shulker", "push", "潜影盒，也要一个个打开确认？"),
    Segment(
        "intro",
        "MiniHUD 是什么",
        13,
        1,
        "default",
        "push",
        "这就是 MiniHUD。它不会替你建造或找结构，只把原本看不见的信息、边界和范围，直接画进游戏画面。",
    ),
    Segment(
        "problem-map",
        "使用方法",
        13,
        2,
        "default",
        "still",
        "不用背菜单。遇到什么问题，就开对应功能。默认 H 控制总渲染，H 加 C 进入配置，快捷键可以修改。",
    ),
    Segment(
        "info-explore",
        "日常信息",
        11,
        3,
        "info:explore",
        "push",
        "出门怕迷路，就开启坐标、朝向、群系和时间。需要回基地时，可以先设置参考点，再查看距离。",
    ),
    Segment(
        "info-performance",
        "日常信息",
        14,
        3,
        "info:performance",
        "pull",
        "游戏卡顿时，别把所有数字都堆上去。FPS 看客户端，延迟和 TPS、MSPT 看联机状态；精确数据还要看服务器支持。",
    ),
    Segment(
        "structure",
        "结构边界",
        23,
        4,
        "structure:on",
        "push",
        "结构被海水或山体挡住时，打开结构主边界和组成部分，就能看清整体与内部。它只显示已有数据，不会远程找结构，也不会调用 locate。单人读取本地数据，多人服需要 Servux 提供结构数据。",
    ),
    Segment(
        "site-biome",
        "工程选址",
        8,
        5,
        "site:biome",
        "pull",
        "准备建基地或农场，先看群系和区块边界，确认工程有没有跨过关键区域。",
    ),
    Segment(
        "site-guide",
        "工程选址",
        14,
        5,
        "site:guide",
        "push",
        "担心刷怪，再按需要检查光照。一次只开一层，看见问题、现场处理、关闭复查。低光照只是条件之一，不代表一定刷怪。",
    ),
    Segment(
        "range-device",
        "机制范围",
        6,
        6,
        "range:beacon",
        "push",
        "信标、潮涌核心这类装置，适合看盒状覆盖边界。",
    ),
    Segment(
        "range-spawn",
        "机制范围",
        6,
        6,
        "range:spawn",
        "pull",
        "刷怪和消失距离看球形参考，挂机点是否合适会更直观。",
    ),
    Segment(
        "range-chunk",
        "机制范围",
        12,
        6,
        "range:chunk",
        "still",
        "随机刻和出生区块看网格。二十四、三十二、一百二十八格只是常见参考，具体规则仍要看版本和生物。",
    ),
    Segment(
        "build-basic",
        "施工规划",
        9,
        7,
        "shape:basic",
        "push",
        "圆心、半径和占地不好确定，就用圆形、圆柱或方框，先把施工参考线画进世界。",
    ),
    Segment(
        "build-spawn",
        "施工规划",
        11,
        7,
        "shape:spawn",
        "pull",
        "需要判断高度或生成空间，再切换球体和生成球。它们只帮助检查，不会自动放置或拆除方块。",
    ),
    Segment(
        "base-preview",
        "基地管理",
        12,
        8,
        "base:shulker",
        "push",
        "回到基地，默认按住 Shift 悬停，就能预览潜影盒、收纳袋、地图或支持的容器内容，少开很多界面。",
    ),
    Segment(
        "base-efficiency",
        "基地管理",
        15,
        8,
        "base:efficiency",
        "pull",
        "机器效率不对，再查看光照、生成距离、Mob Cap、实体数量、延迟和 TPS。Mob Cap 是数量上限，不是空间范围。",
    ),
    Segment(
        "install",
        "安装与限制",
        18,
        2,
        "video:install",
        "still",
        "安装只要记住：Fabric Loader，加上版本匹配的 MiniHUD 和 MaLiLib。MiniHUD 装客户端；多人结构数据还要服务器支持。",
    ),
    Segment(
        "outro",
        "收藏与关注",
        15,
        8,
        "video:outro",
        "push",
        "遇到这六类问题，就回来按清单找功能。觉得有用先收藏，也欢迎关注我，继续分享实用的 Minecraft 模组和生存技巧。",
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
        cursor = end - (
            TRANSITION_SECONDS if index < len(SEGMENTS) - 1 else 0
        )
    return tuple(items)


def render_requests() -> list[dict[str, object]]:
    return [
        {"id": segment.id, "slide": segment.slide, "state": segment.state}
        for segment in SEGMENTS
    ]

"""Single source of truth for the Xaero intro and original-voice timeline."""

from dataclasses import dataclass


SOURCE_VIDEO = "source/MOD介绍/xaero/小地图+大地图使用说明.mp4"
TRANSITION_SECONDS = 0.0


@dataclass(frozen=True)
class Segment:
    id: str
    chapter: str
    seconds: float
    slide: int | None
    motion: str
    narration: str | None
    rate: str = "+0%"
    pitch: str = "+0Hz"
    kind: str = "slide"


INTRO_SEGMENTS = (
    Segment(
        "hook", "开场：地图解决什么问题", 8.0, 1, "push",
        "装了地图，还是会迷路吗？Xaero 把‘我在哪’和‘我去过哪’，拆成两种尺度。",
        "+1%", "+1Hz",
    ),
    Segment(
        "minimap", "Xaero's Minimap：看眼前", 13.8, 2, "push",
        "Xaero's Minimap 26.4.0，把接近原版风格的小地图、方向显示、周边地形和路径点放进 HUD。移动时抬眼看一眼，就知道下一步往哪走。",
        "+0%", "+1Hz",
    ),
    Segment(
        "worldmap", "Xaero's World Map：看全局", 12.6, 3, "pull",
        "Xaero's World Map 1.44.0，则把探索过的地形逐步记录下来。打开全屏地图，可以看范围、规划路线，也能回看已经走过的世界。",
        "-1%", "+0Hz",
    ),
    Segment(
        "pairing", "路径点：记住目的地", 13.1, 4, "push",
        "两者联动后，同一个路径点，近处用小地图导航，远处用世界地图规划。家、村庄、传送门和农场，都能留下可复用的地点。",
        "+0%", "+0Hz",
    ),
    Segment(
        "handoff", "进入实机操作", 13.1, 5, "still",
        "安装时核对 Minecraft 版本、加载器和模组版本，进入世界后先检查按键绑定。操作细节以实机画面为准，原声完整保留。",
        "-3%", "-1Hz",
    ),
)


def all_segments(source_seconds: float) -> tuple[Segment, ...]:
    return (*INTRO_SEGMENTS, Segment(
        "original", "实机演示：原声讲解", source_seconds, None, "still", None, kind="source"
    ))


def intro_seconds() -> float:
    return sum(segment.seconds for segment in INTRO_SEGMENTS)


def timeline(source_seconds: float) -> list[tuple[Segment, float, float]]:
    cursor = 0.0
    rows = []
    for segment in all_segments(source_seconds):
        rows.append((segment, cursor, cursor + segment.seconds))
        cursor += segment.seconds
    return rows


def clock(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"

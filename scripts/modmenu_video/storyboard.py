"""Single source of truth for the Mod Menu video timeline."""

from dataclasses import dataclass


TRANSITION_SECONDS = 0.25
PREVIEW_SEGMENT_IDS = ("pain-delete", "reveal", "config-no")


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
        "pain-setting",
        "开场",
        8.0,
        1,
        "pain-setting",
        "push",
        "晚上十点四十七。你只是想改一个模组选项。暂停菜单翻了一圈——设置呢？",
    ),
    Segment(
        "pain-jar",
        "开场",
        9.0,
        1,
        "pain-jar",
        "pull",
        "于是退出游戏，打开 mods 文件夹。一排 JAR 整整齐齐，名字看着像同事工号。",
    ),
    Segment(
        "pain-delete",
        "开场",
        9.3,
        1,
        "pain-delete",
        "push",
        "想删一个试试？手又缩回来了。万一它是前置，启动器会用一大片红字，表达它的心情。",
    ),
    Segment(
        "reveal",
        "Mod Menu 登场",
        13.5,
        2,
        "default",
        "push",
        "这时候，Mod Menu 登场。它像游戏里的模组前台：谁装了、谁能设置、入口在哪里，先替你摆到桌面上。",
    ),
    Segment(
        "lookup",
        "找模组",
        13.0,
        2,
        "default",
        "pull",
        "进到列表，先搜名字，再确认版本和依赖，最后点配置。不用再对着文件名做 JAR 考古；那不是生存玩法，是加班玩法。",
    ),
    Segment(
        "config-yes",
        "配置入口",
        12.7,
        3,
        "yes",
        "push",
        "如果模组提供图形设置，配置按钮就能直接把你送到对应页面。Mod Menu 负责带路，真正的选项还是那个模组自己的。",
    ),
    Segment(
        "config-no",
        "配置入口",
        12.7,
        3,
        "no",
        "pull",
        "按钮灰了，也不一定是坏了。可能它只用按键、命令或配置文件。Mod Menu 是前台，不负责装修别人家。",
    ),
    Segment(
        "install",
        "安装建议",
        17.0,
        4,
        "default",
        "still",
        "安装我更推荐交给启动器：依赖会自动解析，游戏和模组版本也更容易对齐。手动拖 JAR 当然能用；但缺了前置时，它也只会陪你一起沉默。",
    ),
    Segment(
        "recap",
        "三步上手",
        15.0,
        5,
        "default",
        "push",
        "以后想改设置，记住三步：打开模组页，搜到目标，再进配置。没有按钮，就看它自己的说明。事情还是那件事，只是终于不用退出游戏找设置了。",
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

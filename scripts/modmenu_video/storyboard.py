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
        "你有没有过这种感觉？模组明明装好了，可我怎么知道它真的生效了？",
    ),
    Segment(
        "pain-jar",
        "确认是否生效",
        9.0,
        1,
        "pain-jar",
        "pull",
        "我以前会先回游戏里找半天。没有提示，也没有人出来报到。最后只好打开 mods 文件夹，对着一排 JAR 发呆。",
    ),
    Segment(
        "pain-delete",
        "确认是否生效",
        9.3,
        1,
        "pain-delete",
        "push",
        "文件名又长又像，谁知道哪个才是它？想重装，又怕删错前置。别猜，先看名单。",
    ),
    Segment(
        "reveal",
        "确认是否生效",
        13.5,
        2,
        "default",
        "push",
        "Mod Menu 就像游戏里那个热心的朋友。它把已经安装的模组，一个个列给你看。能不能找到、版本对不对，先在这里确认。不用再靠猜。",
    ),
    Segment(
        "lookup",
        "确认是否生效",
        13.0,
        2,
        "default",
        "pull",
        "进到列表，搜一下模组名字。只要它在这里出现，客户端就已经认到它了。点开资料，还能看到版本、作者和链接。至少不用再翻文件夹猜了。",
    ),
    Segment(
        "config-yes",
        "打开设置",
        12.7,
        3,
        "yes",
        "push",
        "确认它生效以后，第二个问题来了：设置在哪？如果模组提供图形配置，列表里的按钮会直接带你进去。门后的选项，才是它自己的。",
    ),
    Segment(
        "config-no",
        "打开设置",
        12.7,
        3,
        "no",
        "pull",
        "按钮是灰的，也先别把锅甩给 Mod Menu。有些模组不用图形页面，设置藏在按键、命令，或者 config 文件里。这不是没生效，是入口不一样。",
    ),
    Segment(
        "install",
        "排查与安装",
        17.0,
        4,
        "default",
        "still",
        "遇到‘装了却没反应’，我会查三件事：列表里有没有它，游戏版本和前置对不对，设置说明放在哪。安装交给启动器，能省掉不少麻烦。手动拖 JAR 也能用，出了问题就得自己排查。",
    ),
    Segment(
        "recap",
        "快速总结",
        15.0,
        5,
        "default",
        "push",
        "以后记住这条路线。先去 Mod Menu，看模组有没有报到。看见了，说明客户端认到它了；再点配置，改它自己的选项。没有按钮，就看说明，别在文件夹里猜。",
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

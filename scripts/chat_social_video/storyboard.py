"""Timeline for the five-screen chat/social/privacy Bilibili video."""

from dataclasses import dataclass


TRANSITION_SECONDS = 0.25
PREVIEW_SEGMENT_IDS = ("heads", "reports", "emote")


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
        "overview",
        "开场：四个问题",
        11.5,
        1,
        "default",
        "still",
        "聊天、社交与隐私，不只是美化聊天栏。四个组件，解决认人、回看、签名关联和动作表达。",
    ),
    Segment(
        "heads",
        "Chat Heads：看清是谁",
        13.5,
        2,
        "default",
        "push",
        "多人聊天，光看名字常认不出人。Chat Heads 在消息旁显示玩家头像。支持 UUID 和昵称别名，纯客户端即可。",
    ),
    Segment(
        "history",
        "More Chat History：找回消息",
        15.5,
        3,
        "default",
        "still",
        "聊天刷屏后，错过的消息还能翻回来。More Chat History 把上限从一百条提高到一万六千三百八十四条。安装后自动生效，只保留当前会话。",
    ),
    Segment(
        "reports",
        "No Chat Reports：看清边界",
        17.0,
        4,
        "default",
        "pull",
        "No Chat Reports 处理消息签名，不是聊天内容。服务器允许时，发送未签名消息，减少账号与举报证据关联。客户端和服务端一起部署效果最好；不会隐藏聊天，也不能绕过服务器策略。",
    ),
    Segment(
        "emote",
        "Emotecraft：用动作表达",
        # 1.2 seconds on the PPT, followed by the complete
        # 87.52-second source video.
        89.0,
        5,
        "default",
        "still",
        "",
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

"""Bilibili publishing copy synchronized to the video timeline."""

from scripts.tweakeroo_video.storyboard import timeline


TITLE = (
    "Tweakeroo 不只会灵魂出窍！自动补货、换胸甲这 5 个功能真省事"
)
ALTERNATE_TITLES = (
    "装了 Tweakeroo 还在手动补方块？这 5 个功能真的能省事",
    "别把 Tweakeroo 只当配置菜单！5 个高频功能一次讲明白",
)


def clock(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


def chapter_lines() -> list[str]:
    lines = []
    seen = set()
    for item in timeline():
        if item.segment.chapter in seen:
            continue
        seen.add(item.segment.chapter)
        lines.append(f"{clock(item.start)} {item.segment.chapter}")
    return lines


def build_publish_markdown() -> str:
    alternatives = "\n".join(
        f"- {title}" for title in ALTERNATE_TITLES
    )
    chapters = "\n".join(chapter_lines())
    return f"""# B 站发布信息

## 推荐标题

{TITLE}

## 备选标题

{alternatives}

## 简介

还在手动补方块、换胸甲，进矿洞又被黑得找不到路？这期不念配置表，直接按使用场景讲 Tweakeroo 的五个高频功能：灵魂出窍、自动切换鞘翅与胸甲、自动补货、快速左右键和 Gamma 亮度。

本期演示基于 Minecraft Java 版 26.2、Tweakeroo 26.2-0.29.2 和 MaLiLib 0.29.2。不同版本的菜单、名称和行为可能变化，请使用与游戏版本匹配的文件。Tweakeroo 是客户端模组，但服务器规则始终优先；自动操作和快速点击在多人服使用前，请先阅读服务器说明。

这里不念几十页配置表，只把复杂模组翻译成能直接使用的场景。觉得这份清单有用，可以先收藏；想继续看这种不绕弯的模组用法，欢迎关注。

## 视频章节

{chapters}

## 推荐标签

Minecraft、我的世界、Tweakeroo、Fabric、MaLiLib、模组推荐、生存技巧、建筑辅助

## 置顶评论建议

五项功能速查已经放在章节里，建议先收藏，设置时回来对照。

这五个里面，你原来完全没用过的是哪一个？我先猜自动补货。评论区留一个名字就行。

关注我，后面继续把复杂配置翻译成人话，不用每次装完模组都自己翻几十页菜单。
"""

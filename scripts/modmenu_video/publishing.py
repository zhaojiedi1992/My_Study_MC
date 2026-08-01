"""Bilibili copy synchronized with the Mod Menu storyboard."""

from scripts.modmenu_video.storyboard import timeline


TITLE = "模组装了却没反应？Mod Menu 帮你确认生效、找到设置"
ALTERNATE_TITLES = (
    "不知道模组有没有生效？打开 Mod Menu 看一眼",
    "设置入口藏在哪？Mod Menu 带你从列表找到配置",
)
MODRINTH_URL = "https://modrinth.com/mod/modmenu"
TAGS = (
    "Minecraft",
    "我的世界",
    "Mod Menu",
    "Fabric",
    "模组推荐",
    "客户端模组",
    "整合包",
    "MC教程",
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


def description_text() -> str:
    return f"""模组装进去了，可它到底有没有生效？设置页面又藏在哪里？这两个问题，装模组时几乎人人都遇到过。

这期用一个很实际的路线带你看：先在 Mod Menu 列表里找到目标模组，确认客户端已经认到它；再去找“配置”入口。按钮可用，就直接进入设置；按钮是灰的，也不代表模组没生效，可能它把设置放在按键、命令或 config 文件里。

画面基于 Minecraft Java 版 26.2。不同游戏与模组版本的界面可能略有变化；安装时请让启动器匹配版本并解析依赖。

Modrinth 下载地址：{MODRINTH_URL}"""


def build_publish_markdown() -> str:
    alternatives = "\n".join(f"- {title}" for title in ALTERNATE_TITLES)
    chapters = "\n".join(chapter_lines())
    tags = "、".join(TAGS)
    return f"""# B 站发布信息

## 推荐标题

{TITLE}

## 备选标题

{alternatives}

## 简介

{description_text()}

## 视频章节

{chapters}

## 推荐标签

{tags}

## 置顶评论建议

一句话记住 Mod Menu：先看它有没有报到，再找它自己的设置门。

配置按钮不可用，不一定是坏了；对应模组可能使用按键、命令或配置文件。安装则优先交给启动器，省掉依赖和版本对不上的麻烦。

你装模组时最怕遇到哪一种：找不到设置、缺少前置，还是版本不匹配？
"""

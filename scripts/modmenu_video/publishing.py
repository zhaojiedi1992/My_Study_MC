"""Bilibili copy synchronized with the Mod Menu storyboard."""

from scripts.modmenu_video.storyboard import timeline


TITLE = "装了几十个模组，设置到底藏哪？Mod Menu 一次讲明白"
ALTERNATE_TITLES = (
    "别再退出游戏翻 JAR 了！Mod Menu 到底有什么用？",
    "模组装好了却找不到设置？你可能只差一个 Mod Menu",
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
    alternatives = "\n".join(f"- {title}" for title in ALTERNATE_TITLES)
    chapters = "\n".join(chapter_lines())
    return f"""# B 站发布信息

## 推荐标题

{TITLE}

## 备选标题

{alternatives}

## 简介

想改一个模组选项，却先在暂停菜单里迷路；退出游戏翻开 mods 文件夹，又被一排 JAR 文件劝退——Mod Menu 就是为这种时刻准备的“模组前台”。

这期只讲最有用的三件事：找到已安装的模组、确认信息、打开它真正提供的配置入口。也会说清楚为什么有些“配置”按钮不能点，以及安装时为什么更推荐启动器，而不是手动拖 JAR。

画面基于 Minecraft Java 版 26.2。不同游戏与模组版本的界面可能略有变化；安装时请让启动器匹配版本并解析依赖。

## 视频章节

{chapters}

## 推荐标签

Minecraft、我的世界、Mod Menu、Fabric、模组推荐、客户端模组、整合包、MC教程

## 置顶评论建议

一句话记住 Mod Menu：它负责帮你找到门，不负责装修别人家。

配置按钮不可用，不一定是坏了；对应模组可能使用按键、命令或配置文件。安装则优先交给启动器，省掉依赖和版本对不上的麻烦。

你装模组时最怕遇到哪一种：找不到设置、缺少前置，还是版本不匹配？
"""

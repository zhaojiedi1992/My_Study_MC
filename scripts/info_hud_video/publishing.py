"""Bilibili publishing copy synchronized with the information HUD storyboard."""

from scripts.info_hud_video.storyboard import timeline


TITLE = "4 个信息 HUD，把生存关键判断放到眼前｜Minecraft Fabric MOD"
ALTERNATE_TITLES = (
    "工具还剩几次、野怪多少血？4 个实用 Minecraft 信息 MOD",
    "少翻菜单，多看一眼：AppleSkin、Jade、Neat、耐久显示实录",
)
TAGS = (
    "Minecraft", "我的世界", "Fabric", "Minecraft模组", "MOD推荐",
    "Jade", "AppleSkin", "Neat", "Show Durability", "生存技巧", "客户端MOD",
)


def clock(value: float) -> str:
    total = int(value)
    return f"{total // 60:02d}:{total % 60:02d}"


def chapter_lines() -> list[str]:
    return [f"{clock(item.start)} {item.segment.chapter}" for item in timeline()]


def description_text() -> str:
    return """工具还剩几次、周围野怪还有多少血、食物吃下去能补多少、准星对着的熔炉里有什么？这期用实机录屏，把四种不同层级的信息 HUD 放到同一套生存场景里对比。

AppleSkin 负责进食预览；Show Durability 把剩余耐久写到物品图标上；Neat 让你清楚周围野怪的血量；Jade 则显示准星当前目标的方块、实体与容器信息。

下载地址（Modrinth）：
- AppleSkin：https://modrinth.com/mod/appleskin
- Jade：https://modrinth.com/mod/jade
- Neat：https://modrinth.com/mod/neat
- Show Durability：请按 Minecraft 与 Fabric 版本选择对应发布文件

视频以 Minecraft Java 版 26.2 / Fabric 实录为基线。不同版本的界面和默认按键可能不同；Jade 的容器内容、实体效果等服务端数据，需要单人世界或服务器端兼容并允许提供。所有 MOD 均只增加信息显示，不绕过服务器权限或游戏规则。"""


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

这四个 MOD 不是重复堆 HUD：AppleSkin 看自己，Show Durability 看工具，Neat 看周围野怪，Jade 看准星目标。

你最希望游戏直接显示哪一种信息？
"""

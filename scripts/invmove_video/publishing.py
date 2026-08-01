"""Bilibili publishing copy synchronized with the InvMove storyboard."""

from scripts.invmove_video.storyboard import timeline


TITLE = "打开背包还能继续走？InvMove 让脚步不停｜Minecraft MOD"
ALTERNATE_TITLES = (
    "整理背包不用停！InvMove 实机前后对比",
    "Minecraft 打开工作台还能走？这个客户端 MOD 很实用",
)
TAGS = (
    "Minecraft", "我的世界", "InvMove", "Fabric", "Minecraft模组",
    "MOD推荐", "客户端MOD", "背包整理", "生存技巧", "效率工具",
)


def clock(value: float) -> str:
    total = int(value)
    return f"{total // 60:02d}:{total % 60:02d}"


def chapter_lines() -> list[str]:
    return [f"{clock(item.start)} {item.segment.chapter}" for item in timeline()]


def description_text() -> str:
    return """打开背包或工作台时，角色只能停在原地？InvMove 把移动控制带进游戏界面，让你在整理物品、查看合成栏时继续前进。

这期用三段实录直接对比：未安装时，背包界面一打开角色就停下；安装后，可以在移动中打开背包，也可以在工作台界面内继续移动。最后简单说明 Fabric 26.2 下的依赖和可选组件。

下载地址（Modrinth）：
- InvMove：https://modrinth.com/mod/invmove
- Cloth Config：https://modrinth.com/mod/cloth-config
- InvMoveCompats：https://modrinth.com/mod/invmovecompats

不同 Minecraft 版本请选择对应构建。公共服务器可能使用反作弊策略，使用前请先确认服务器规则。"""


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

InvMove 最直接的变化，就是少掉“开界面必须先停下”这一步。

你更常在哪个界面里想继续移动：背包、工作台，还是箱子？
"""

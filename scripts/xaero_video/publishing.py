"""Bilibili copy for the Xaero map-set video."""

TITLE = "还在 Minecraft 里迷路？Xaero 小地图 + 世界地图实机教学"
ALTERNATE_TITLES = (
    "Xaero 小地图+世界地图怎么用？路径点联动实机演示",
    "Xaero's Minimap 26.4.0 + World Map 1.44.0 使用说明",
)
TAGS = (
    "Minecraft", "我的世界", "Xaero's Minimap", "Xaero's World Map",
    "小地图", "世界地图", "路径点", "模组教程", "Fabric", "生存实用模组",
)
MINIMAP_URL = "https://modrinth.com/mod/xaeros-minimap"
WORLDMAP_URL = "https://modrinth.com/mod/xaeros-world-map"


def chapter_lines() -> list[str]:
    return [
        "00:00 开场：地图解决什么问题",
        "00:08 小地图：看眼前",
        "00:21 世界地图：看全局",
        "00:34 路径点：记住目的地",
        "00:47 使用前检查：按键与版本",
        "01:00 实机：小地图 HUD 效果",
        "01:09 实机：Mod Menu 检查安装",
        "01:19 实机：确认 Xaero's Minimap",
        "01:29 实机：移动中观察小地图",
        "02:39 实机：打开 Xaero's World Map",
        "02:49 实机：路径点操作菜单",
        "02:59 实机：编辑路径点配置",
        "03:19 实机：回到游戏内导航",
        "04:00 实机：进入按键设置",
        "04:10 实机：设置 Open World Map 快捷键",
        "04:20 实机：检查小地图相关按键",
    ]


def description_text() -> str:
    chapters = "\n".join(chapter_lines())
    return f"""还在 Minecraft 里迷路？这期用实机画面讲清 Xaero 的小地图、世界地图和路径点。

Xaero's Minimap 26.4.0 负责 HUD 小地图、方向、周边地形与路径点；Xaero's World Map 1.44.0 会记录探索过的地形，提供全屏地图和路径点联动。一个看眼前，一个看全局。

01:00 后保留完整实机原声讲解：从 Mod Menu 检查安装，到打开世界地图、创建路径点、调整按键设置，均以录制画面为准。实机段没有叠加第二条配音。

安装前请核对 Minecraft 版本、加载器和 MOD 版本。世界地图只会记录已经探索过的区域，未探索地形不会自动生成。

【时间点】
{chapters}

【下载】
Xaero's Minimap：{MINIMAP_URL}
Xaero's World Map：{WORLDMAP_URL}
"""


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

Minimap 看眼前，World Map 看全局，Waypoint 记住目的地。

本期实机段保留原声；如果你的版本中快捷键和画面位置不同，请以游戏内按键设置为准。你平时最常用路径点标记什么地方？
"""

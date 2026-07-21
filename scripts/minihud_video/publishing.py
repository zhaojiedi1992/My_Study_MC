"""Publishing metadata for the MiniHUD Bilibili release.

The chapter list is derived from the same storyboard timeline used to render
the video, so chapter timestamps remain synchronized when segment timings are
updated.
"""

from scripts.minihud_video.storyboard import timeline


def clock(seconds: float) -> str:
    """Format a timeline offset as a Bilibili-compatible ``MM:SS`` clock."""

    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


def chapter_lines() -> list[str]:
    """Return one chapter line for each chapter's first timeline item."""

    lines = []
    seen = set()
    for item in timeline():
        if item.segment.chapter in seen:
            continue
        seen.add(item.segment.chapter)
        lines.append(f"{clock(item.start)} {item.segment.chapter}")
    return lines


def build_publish_markdown() -> str:
    """Build the title, description, chapters, tags, and pinned comment."""

    chapters = "\n".join(chapter_lines())
    return f"""# B 站发布信息

## 推荐标题

请把F3扣掉！MiniHUD把结构、范围、刷怪距离直接画出来

## 简介

结构藏进地形、装置范围只能靠估、圆心半径不好确定、潜影盒还要逐个打开？本期不背菜单，直接按六类常见问题介绍 MiniHUD：遇到什么问题，开启什么功能，以及画面会得到什么结果。

本视频以 **Minecraft Java 版 26.2** 和与其匹配的最新 MiniHUD、MaLiLib 为功能基线。不同版本的核心思路相通，但具体菜单、功能数量和规则可能不同，请以对应版本下载页为准。

安装关系：Fabric Loader + MiniHUD + MaLiLib。MiniHUD 安装在客户端；多人服真实结构边界需要服务器端 Servux 提供数据，精确性能信息也取决于服务器支持。

官方项目：
- MiniHUD：https://github.com/maruohon/minihud
- Modrinth：https://modrinth.com/mod/minihud
- CurseForge：https://www.curseforge.com/minecraft/mc-mods/minihud

## 视频章节

{chapters}

## 推荐标签

Minecraft、我的世界、MiniHUD、Fabric、MaLiLib、模组推荐、生存技巧、技术生存、建筑辅助

## 置顶评论建议

这期不背菜单，按“遇到问题 → 开功能 → 看结果”整理，建议先收藏：

00:00 冷开场
00:35 日常信息｜迷路看信息 HUD
00:59 结构边界｜遮挡看结构边界
01:19 工程选址｜选址看环境覆盖
01:40 机制范围｜估算看范围参考
02:03 施工规划｜施工看形状参考
02:22 基地管理｜整理和排查看预览与性能信息
02:59 收藏与关注

你最常遇到哪类问题，最想先用哪个功能？评论区聊聊。觉得有用就点个关注，后面按问题回来查，不用再翻菜单。
"""

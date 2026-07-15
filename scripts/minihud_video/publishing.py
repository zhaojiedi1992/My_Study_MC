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

一个 MOD 看清 Minecraft 隐藏规则｜MiniHUD 6 个实用场景

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

六类问题速查：迷路看信息 HUD；遮挡看结构边界；选址看环境覆盖；估算看范围参考；施工看形状参考；整理和排查看预览与性能信息。

章节时间轴：
{chapters}

建议先收藏，需要时按问题回来找功能。
"""

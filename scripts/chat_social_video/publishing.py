"""Bilibili copy synchronized with the chat/social storyboard."""

from scripts.chat_social_video.storyboard import timeline


TITLE = "聊天、社交与隐私：4 个 Minecraft 客户端 MOD 一次讲清"
ALTERNATE_TITLES = (
    "聊天头像、历史回看、No Chat Reports、Emotecraft 怎么用？",
    "Minecraft 聊天栏实用 MOD：认人、回看、隐私和动作表达",
)


def clock(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


def chapter_lines() -> list[str]:
    return [f"{item.start and clock(item.start) or '00:00'} {item.segment.chapter}" for item in timeline()]


def build_publish_markdown() -> str:
    alternatives = "\n".join(f"- {title}" for title in ALTERNATE_TITLES)
    chapters = "\n".join(chapter_lines())
    return f"""# B 站发布信息

## 推荐标题

{TITLE}

## 备选标题

{alternatives}

## 简介

这期把聊天、社交与隐私相关的 4 个 Minecraft 客户端 MOD 放在一起：Chat Heads 让你一眼认出发言者，More Chat History 让聊天栏可以翻得更远，No Chat Reports 解释消息签名和服务器边界，Emotecraft 则用动作补充文字与语音。

最后一屏会在 PPT 内点击“最大化播放”，完整播放 Emotecraft 的内置视频演示。视频内容以 Minecraft Java 版 26.2 / Fabric 整合包为基线；不同版本和服务器配置可能有差异。

## MOD 下载地址（Modrinth）

- Chat Heads：https://modrinth.com/mod/chat-heads
- More Chat History：https://modrinth.com/mod/morechathistory
- No Chat Reports：https://modrinth.com/mod/no-chat-reports
- Emotecraft：https://modrinth.com/plugin/emotecraft

## 视频章节

{chapters}

## 推荐标签

Minecraft、我的世界、Fabric、Chat Heads、More Chat History、No Chat Reports、Emotecraft、客户端 MOD、聊天 MOD、整合包

## 置顶评论建议

四个组件的定位可以这样记：Chat Heads 负责“看清是谁”，More Chat History 负责“找回消息”，No Chat Reports 负责“看清签名边界”，Emotecraft 负责“用动作表达”。

你更想先看哪一类：聊天界面、历史回看、隐私设置，还是玩家动作？
"""

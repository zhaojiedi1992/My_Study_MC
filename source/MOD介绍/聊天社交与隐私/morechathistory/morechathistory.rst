More Chat History - 保留更多聊天历史
===========================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#15803d;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       打开 More Chat History 核心演示
     </a>
   </p>

More Chat History 是一款功能非常单一的客户端 MOD：它把聊天历史上限从原版的 100 提高到 16,384，让玩家可以向上翻看更早的消息。

适用场景
------------

* 服务器公告、玩家聊天和命令回复连续刷屏时，找回刚才错过的内容。
* 执行输出较多的命令后，继续回看前面的结果。
* 多人聊天较活跃时，减少早期消息很快被挤出可回看范围的情况。

安装后不会出现新按钮或配置页。模组直接扩展客户端的聊天队列，启动游戏后自动生效。

它不是永久聊天日志
--------------------

More Chat History 扩展的是当前客户端保留在内存中的聊天队列，不是完整的聊天存档工具：

* 不会把聊天自动导出为文本文件。
* 不提供搜索、分类、书签或筛选。
* 不保证跨游戏重启或换服后继续保留。
* 不会改变服务器保存的聊天记录和管理规则。

它适合的是“人还在游戏里，想把聊天栏往上多翻一会儿”这个简单需求。

版本与安装
------------

本整合包使用 **More Chat History 2.0.0**，对应 Minecraft 26.1–26.2。该版本是 Fabric 客户端 MOD，将 JAR 放入客户端 ``mods`` 目录后重启游戏即可，服务器无需安装。

Modrinth 版本页未列出必需的其他 MOD 依赖。16,384 是模组内置的固定上限，没有游戏内调整项。

官方项目
------------

* Modrinth：https://modrinth.com/mod/morechathistory
* GitHub：https://github.com/JackFredMods/MoreChatHistory
* 聊天队列扩展代码：https://github.com/JackFredMods/MoreChatHistory/blob/main/src/client/java/red/jackf/morechathistory/mixins/ChatComponentMixin.java

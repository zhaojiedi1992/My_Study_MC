Chat Heads - 在聊天消息旁显示玩家头像
==============================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#db2777;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       打开 Chat Heads 核心演示
     </a>
   </p>

Chat Heads 是一款纯客户端聊天界面 MOD。它会在玩家消息旁显示对应的皮肤头像，让玩家在多人聊天中更容易分辨是谁在说话。

核心体验
------------

* 在聊天行或玩家名前显示 8×8 风格的皮肤头像。
* 聊天人数较多时，可以通过头像快速找到某位玩家的发言。
* 只改变本机看到的聊天界面，不修改消息内容，服务器和其他玩家无需安装。

模组会优先根据消息携带的 UUID 识别发言者，并用文本推理辅助判断。某些服务器会改写聊天格式、使用昵称或发送不准确的 UUID，因此头像偶尔可能匹配错误。

常用设置
------------

* **渲染位置**：在整条聊天行前显示，或紧贴玩家名显示。
* **发送者检测**：可选仅 UUID、UUID 加自动推理，或仅自动推理。
* **玩家名昵称**：把服务器昵称手动绑定到真实玩家名，用于纠正头像。
* **显示效果**：可调整阴影、系统消息处理和头像立体感。

如果头像在某个服务器上经常识别错误，可先将“发送者检测”改为“仅自动推理正确玩家”，再为特殊昵称添加手动对应关系。

版本与安装
------------

本整合包使用 **Chat Heads 1.2.4**，该构建支持 Minecraft 26.1–26.2。将对应的 Fabric JAR 放入客户端 ``mods`` 目录并重启游戏，即可使用默认设置。

在 Fabric 上，安装 Cloth Config 和 Mod Menu 后可以方便地打开图形化设置。没有图形化设置依赖时，模组仍可按默认设置运行。

.. note::

   整合包清单记录的是 1.2.4。上游已于 2026-07-22 发布 1.2.5，但不应只根据文档单独替换整合包 JAR；更新时应统一检查版本与兼容性。

功能边界
------------

Chat Heads 不会增加聊天历史、翻译消息、改变聊天举报状态，也不会改动服务器的聊天规则。

官方项目
------------

* Modrinth：https://modrinth.com/mod/chat-heads
* GitHub：https://github.com/dzwdz/chat_heads
* 1.2.4 源码：https://github.com/dzwdz/chat_heads/tree/1.2.4-26.1

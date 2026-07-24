No Chat Reports - 减少聊天消息的账号签名
====================================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#0891b2;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       打开 No Chat Reports 核心演示
     </a>
   </p>

No Chat Reports 主要处理 Minecraft 1.19 以后的玩家聊天签名。原版多人聊天消息可以携带加密签名，用来证明某条消息来自特定账号，也是玩家聊天举报机制的基础之一。

核心作用
------------

客户端安装后，No Chat Reports 会阻止客户端向服务器提供账号公钥，并在服务器允许时发送未签名的消息。这会让相关消息缺少可与 Microsoft 账号关联的签名证据。

安装位置不同，效果也不同：

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - 安装位置
     - 主要效果
   * - 只装客户端
     - 尝试发送未签名消息。客户端是否能保持未签名状态，取决于服务器是否允许。
   * - 只装服务器
     - 服务器在转发前去除消息签名，为加入的玩家统一处理聊天。
   * - 客户端和服务器都安装
     - 客户端不发送签名，服务器也不强制验证，功能最完整。

必须了解的边界
----------------

* 它改变的是消息签名，不会加密或隐藏普通聊天内容。
* 它不会阻止服务器保存聊天日志，也不影响服务器按自身规则禁言或处罚玩家。
* 服务器强制聊天签名时，模组会显示警告或调整签名模式；它不会强行绕过服务器要求。
* Realms 不属于该模组能够阻止聊天举报的环境。

版本与安装
------------

本整合包使用 **No Chat Reports 2.20.1**，对应 Minecraft 26.2。Fabric 版需要 Fabric API。Cloth Config 和 Mod Menu 可用于打开图形化设置，但不是核心功能的前提。

下载时应根据 Minecraft 版本和加载器选择文件，不要混用 Fabric、Forge 或 NeoForge 构建。

官方项目
------------

* Modrinth：https://modrinth.com/mod/no-chat-reports
* GitHub：https://github.com/Aizistral-Studios/No-Chat-Reports
* 本文核对提交：https://github.com/Aizistral-Studios/No-Chat-Reports/commit/3bd0d546e9eb363317bbf0191672722f52c2461e

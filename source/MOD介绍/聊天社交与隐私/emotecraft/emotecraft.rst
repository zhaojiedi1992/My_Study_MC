Emotecraft - 玩家动作与表情轮盘
====================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#9333ea;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       打开 Emotecraft 核心演示
     </a>
   </p>

Emotecraft 为玩家模型增加可播放的动作表情。玩家可以用表情轮盘挥手、舞蹈或播放自定义动画，用视觉动作补充文字和语音交流。

基本用法
------------

* 默认按 ``B`` 打开表情选择轮盘。
* 模组自带挥手等基础动作。
* 自定义动作文件可放入 ``.minecraft/emotes`` 目录。
* 创作者可以使用 Blockbench 或 Blender 制作自定义动作。

Emotecraft 改变的是玩家模型动画，不会在聊天栏中插入 Unicode 表情，也不会改变服务器聊天格式。

多人游戏要求
----------------

完整的多人同步需要服务器提供 Emotecraft MOD 或对应插件，并且观看动作的玩家客户端也需要安装。

安装了 Emotecraft 的客户端仍可以连接原版服务器，但默认情况下动作不会在其他玩家之间同步。因此，它适合作为整合包和配套服务器共同部署的社交功能。

版本、依赖与稳定性
----------------------

本文以 **Emotecraft 3.4.0-b.build.161** 为基线，对应 Minecraft 26.2。Modrinth 将该构建标记为 **Beta**，在整合包中更新前应先测试玩家模型、第一人称渲染和动画类 MOD 的兼容性。

* **Player Animation Library** 是该版本的必需依赖。
* Searchables 和 Bendable Cuboids 是 Modrinth 列出的可选依赖。
* 应使用与 Minecraft 26.2 和 Fabric 对应的构建，并从官方项目页下载。

官方项目
------------

* Modrinth：https://modrinth.com/mod/emotecraft
* GitHub：https://github.com/KosmX/emotes
* 使用与动作制作文档：https://docs.zigythebird.com/emotecraft/

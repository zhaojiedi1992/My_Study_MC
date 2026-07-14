MiniHUD - 信息、边界与范围可视化
====================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#0891b2;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       🎮 打开 MiniHUD PPT 风格演示
     </a>
   </p>

MiniHUD 是 maruohon（Masa）开发的客户端信息与覆盖层 MOD。它把玩家关心的信息、网格、范围和边界直接显示在游戏画面中，帮助玩家少开完整 F3、少做手工测量，并在建造前先看清空间规则。适合第一次接触 MiniHUD 的同学按任务了解功能，而不是从一长串配置名称开始背。

按使用场景选择
------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 玩家任务
     - MiniHUD 如何帮忙
   * - 日常游玩：随时掌握信息
     - 用 **信息 HUD** 查看坐标、方向、群系、时间与性能信息；只保留当前任务需要的几行
   * - 外出探索：看清结构
     - 在可用数据范围内显示结构主边界和组成部分；它不会远程搜索结构，也不使用 ``/locate``
   * - 工程选址：检查环境
     - 用 **环境与网格** 查看光照、方块网格、区块、群系和可生成区域
   * - 机制规划：确认范围
     - 用 **范围与边界** 查看信标、潮涌核心、随机刻，以及生物生成与消失距离
   * - 开始施工：画出设计
     - 用 **建筑与形状** 创建立方体、圆柱、方块线、球体、生成范围和多种棱锥，辅助占地、半径与高度规划
   * - 基地管理：快速查看与维护
     - 用潜影盒、收纳袋、地图和物品栏 **预览与检查** 整理物资；结合目标信息、Mob Cap 与 TPS/MSPT 维护基地和机器

推荐使用方法
------------------------

#. 按默认 ``H + C`` 打开配置，先说明自己要解决的问题。
#. 只启用当前场景需要的信息行或覆盖层，不要一次全部打开。
#. 根据颜色、数字和线框判断范围，回到现场处理。
#. 按默认 ``H`` 临时关闭主渲染，检查结果并保持画面清楚。

多人游戏限制
------------------------

MiniHUD 是客户端 MOD，但客户端并不总能得到世界的全部数据：

- 单人世界通常可以直接读取本地数据。
- 史莱姆区块等种子相关功能需要正确的世界种子。
- 结构边界、Mob Cap、精确 TPS/MSPT 或部分实体数据在多人服上可能需要 **Servux**、**Carpet** 或服务器许可。
- 服务器没有提供数据时，功能可能不显示、不完整或只能估算；应遵守服务器规则。

安装与官方项目
------------------------

- 安装与当前 Minecraft 版本匹配的 **MiniHUD** 和 **MaLiLib**。
- 默认 ``H`` 控制主渲染，``H + C`` 打开配置；快捷键可以修改。
- 作者：maruohon（Masa）
- GitHub：https://github.com/maruohon/minihud/
- CurseForge：https://www.curseforge.com/minecraft/mc-mods/minihud
- Modrinth：https://modrinth.com/mod/minihud

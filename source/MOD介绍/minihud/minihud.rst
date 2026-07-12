MiniHUD - 信息、边界与范围可视化
====================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#0891b2;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       🎮 打开 MiniHUD PPT 风格演示
     </a>
   </p>

MiniHUD 是 maruohon（Masa）开发的客户端信息与覆盖层 MOD。它把玩家关心的信息、网格、范围和边界直接显示在游戏画面中，帮助玩家少开完整 F3、少做手工测量，并在建造前先看清空间规则。

按使用场景选择
------------------------

.. list-table::
   :header-rows: 1
   :widths: 22 34 44

   * - 我现在要做什么
     - 推荐功能分类
     - 可以解决什么问题
   * - 探索、定位或排查性能
     - 信息 HUD
     - 查看坐标、朝向、群系、光照、目标方块、FPS、内存、延迟和可获得的 TPS/MSPT、Mob Cap 等信息
   * - 检查照明和空间位置
     - 环境与网格
     - 显示光照、方块网格、区块边界、群系边界和区域文件边界
   * - 规划农场和装置
     - 范围与边界
     - 查看史莱姆区块、随机刻、生成与消失范围、结构边界、信标和潮涌核心范围
   * - 规划大型建筑
     - 建筑与形状
     - 创建方框、圆柱、方块线、球体与可调生成球，标记中心、半径、高度和施工范围
   * - 快速确认物品或实体内容
     - 预览与检查
     - 预览地图、潜影盒和支持的物品栏，并查看村民交易或目标实体信息

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

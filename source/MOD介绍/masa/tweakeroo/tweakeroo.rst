Tweakeroo：把高频操作拆成可控的客户端微调
================================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#57A64E;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       打开 Tweakeroo PPT 风格演示
     </a>
   </p>

Tweakeroo 是 MASA 系列的大型客户端微调集合。它把许多独立的行为开关、数值项和快捷键集中在一个配置界面中；本页聚焦现有演示展示的五项功能，而不是把它误写成只有五项能力的 MOD。

版本口径
----------

当前整合包记录的版本为 **Tweakeroo 0.29.2（Minecraft 26.2）**，并需要同版本的 **MaLiLib**。上游公开仓库没有对应 ``0.29.2`` 的 26.2 源码标签：本文逐文件核对的是最接近的公开现代 Fabric 分支 ``pre-rewrite/fabric/1.21.1-masa``、提交 ``a348bca``，再与 26.2 发布物元数据交叉核对。因此下面明确描述这些功能的实现和默认逻辑，但不把该公开分支冒充为 26.2 的逐文件镜像。

打开配置
----------

公开源码中 ``Open Config GUI`` 的默认组合键为 ``X`` 后接 ``C``。不少功能本身默认**未绑定**或默认关闭：先进入配置页搜索功能名，按需启用并设置不会与其他 MOD 冲突的快捷键。现有演示里出现的键位是录制实例，不等同于官方默认键位。

演示中的五项功能
------------------

.. list-table::
   :header-rows: 1
   :widths: 22 48 30

   * - 功能
     - 源码确认的行为
     - 使用边界
   * - 灵魂出窍（Free Camera）
     - 让镜头与本体视角分离，以自由相机观察已加载区域；切换世界或维度时会关闭。默认可配置为阻止本体输入/移动。
     - 本体并未随镜头瞬移；仅用于观察。公共服务器须遵守规则，不能当作规避可见性限制的方式。
   * - 自动切换鞘翅
     - 起飞/滑翔时尝试装备可用鞘翅；落地后可换回之前胸甲。另有“胸甲与鞘翅互换”热键，公开默认未绑定。
     - 需要背包中有可用物品，且其他装备管理 MOD 可能造成交互差异。
   * - 手持物自动补货
     - 手持堆叠耗尽后从背包补充；可预补货。公开默认的预补货阈值为 6，范围 1—64，且遵守限制列表。
     - 只是在客户端按规则整理已有物品；容器同步、服务器规则和其他库存 MOD 都可能影响结果。
   * - 左右快速点击
     - 左键和右键是两项独立开关，可改变连续攻击或使用操作的触发节奏。
     - 服务器仍有冷却、频率限制与反作弊；不要将它理解为绕过服务端机制。
   * - Gamma 亮度覆盖
     - 临时覆盖客户端 gamma；公开配置范围 0—32，默认覆盖值 16；关闭时会恢复原先 gamma。
     - 只改变本地画面可见度，不改变光照、刷怪或服务器世界状态。

使用顺序建议
--------------

1. 按 ``X``、``C`` 打开菜单，先只启用一个功能测试。
2. 给常用功能绑定专用快捷键；默认未绑定不代表功能故障。
3. 自动补货与鞘翅切换先在单人世界测试库存摆放和装备回换是否符合预期。
4. 画面过暗才启用 Gamma 覆盖；截图或录制完成后关闭，以免误判真实光照。
5. 多人服先看规则；对自由相机、快速点击等项目尤其谨慎。

为什么不能只看 PPT 的效果
----------------------------

PPT 截图展示的是一次特定配置下的结果。Tweakeroo 的大部分内容是“功能开关 + 参数 + 热键”的组合：例如自由相机、自动鞘翅、左右快速点击在公开默认配置里均为关闭，快捷键也可能为空；Gamma 的数值和补货阈值则能调整。实际游戏中应以当前版本的配置页为准，避免照抄截图中的键位或阈值。

源码依据
----------

* `热键定义 <https://github.com/maruohon/tweakeroo/blob/a348bcabe83a291824ba1717a0912068e71bfa16/src/main/java/fi/dy/masa/tweakeroo/config/Hotkeys.java>`_
* `功能开关定义 <https://github.com/maruohon/tweakeroo/blob/a348bcabe83a291824ba1717a0912068e71bfa16/src/main/java/fi/dy/masa/tweakeroo/config/FeatureToggle.java>`_
* `Gamma、预补货等配置 <https://github.com/maruohon/tweakeroo/blob/a348bcabe83a291824ba1717a0912068e71bfa16/src/main/java/fi/dy/masa/tweakeroo/config/Configs.java>`_
* `鞘翅、补货和相机相关实现 <https://github.com/maruohon/tweakeroo>`_

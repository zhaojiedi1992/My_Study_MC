Mod Menu：已安装 MOD 的前台与配置入口
==========================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#7759c6;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       打开 Mod Menu 图文演示
     </a>
   </p>

Mod Menu 把加载器已经识别到的 MOD 做成一个可搜索、可查看、可导航的客户端界面。它不是运行时 MOD 开关器，也不会替其他 MOD 凭空生成配置页；它的作用是让已有的模组、元数据和设置入口更容易找到。

本文按上游 v20.0.1、提交 74098c6（2026-07-09）逐文件整理，对应当前整合包的 Mod Menu 20.0.1。

功能清单
----------

* **入口与列表**：在主菜单和暂停菜单加入“模组”按钮或图标；可调整按钮样式、位置、模组数量显示、紧凑列表与前置库可见性。
* **详情卡**：显示加载器提供的名称、版本、图标、描述、作者、许可证、链接及模组附加的徽章。信息丰富程度取决于原 MOD 是否提供元数据或接入 API。
* **搜索与过滤**：搜索名称、本地化名称、MOD ID、描述、摘要、作者；还可用 library、modpack、client、configurable、update 等属性筛选。名称/ID 中三字符以上的匹配优先级更高。
* **父子与前置关系**：列表能折叠/呈现父子 MOD，按设置隐藏普通前置库，减少整合包内大量依赖项带来的干扰。
* **配置入口**：当目标 MOD 已注册配置屏幕时，详情卡或列表的“配置”入口会跳转过去；快速配置能减少反复打开详情页的步骤。
* **更新检查**：可按设置的频道检查 Modrinth 更新，并显示可用状态；这是提示功能，不会自动下载或安装更新。
* **拖放 JAR**：允许时可把 MOD JAR 拖到游戏窗口，由界面复制到 mods 目录并提示重启；它不是依赖解析器，也不会保证新 JAR 与当前游戏兼容。

一分钟上手
------------

1. 在主菜单或暂停菜单打开“模组”。
2. 在搜索框输入 MOD 名称、ID 或作者，选中结果查看版本、说明、链接和许可证。
3. 看到“配置”按钮时再点击进入对应 MOD 的设置；没有按钮通常表示该 MOD 没有注册可打开的配置页面。
4. 整合包列表太长时，先隐藏普通前置库或保留“仅可配置前置库”。
5. 需要更新时查看提示与频道，但下载前自行核对 Minecraft、加载器和依赖版本。

配置与边界
------------

普通设置可在 Mod Menu 自己的配置页中调节，包括入口样式、列表排序、链接/许可证/徽章显示、翻译、更新检查、快速配置和拖放安装。更少用的高级项保存在 ``config/modmenu.json`` ，例如隐藏指定 MOD、隐藏指定配置入口、对某 MOD 禁用更新检查、禁用拖放；不熟悉 JSON 时无需手动修改。

它的边界同样重要：

* Mod Menu 只能打开已注册的配置页，不能“让所有 MOD 都变得可配置”。
* 它展示的是启动时已加载的 MOD，不能在游戏中安全地启停 MOD。
* 版本/更新信息是辅助判断，不是兼容性担保，更不是应用商店。
* ``fabric.mod.json`` 将它标为 ``client`` ；服务器不需要安装。

源码依据
----------

* `配置项与高级设置 <https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/config/ModMenuConfig.java>`_
* `搜索规则 <https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/util/mod/ModSearch.java>`_
* `主界面、详情与拖放处理 <https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/gui/ModsScreen.java>`_
* `暂停菜单和主菜单入口 <https://github.com/TerraformersMC/ModMenu/tree/v20.0.1/src/main/java/com/terraformersmc/modmenu/mixin>`_
* `官方仓库 <https://github.com/TerraformersMC/ModMenu/tree/v20.0.1>`_

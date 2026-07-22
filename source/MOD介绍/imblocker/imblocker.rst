IMBlocker - 让游戏操作与中文输入不再互相打架
================================================

IMBlocker 是一个客户端输入法控制 MOD：当玩家正在操作游戏界面时自动屏蔽输入法，需要聊天、搜索或编辑文字时再自动启用。它针对的是中文输入法在 Minecraft 中最常见的尴尬——输入法开着会抢走快捷键，输入法关着又无法顺畅输入中文。

文档基线与官方来源
--------------------

本文只以官方 GitHub 仓库 ``master`` 分支当前最新源码为准，不以整合包中已有 JAR 的版本号或旧版配置作为说明基线。本文整理时对应的最新提交为：

* 提交：``7e1464df7d86079c471f23d4e1d56beca0ec35``
* 日期：2026-06-26
* 提交说明：``Add command prefix regex config``。
* 上游构建版本字段：5.6.0-dev（源码中的开发版本标记）

官方仓库当前 Fabric 元数据声明的 Minecraft 范围为 ``>=1.17 <=1.21.8``，并要求 Java 17 或更高版本。安装时应以下载到的具体构建文件、加载器和 Minecraft 版本为准；不能仅凭仓库 ``master`` 推断它一定兼容某个整合包版本。

官方资料：

* 仓库与 README：https://github.com/reserveword/IMBlocker
* 最新提交：https://github.com/reserveword/IMBlocker/commit/7e1464df7d86079c471f23d4e1d56beca0ec35
* Fabric 模组元数据：https://github.com/reserveword/IMBlocker/blob/master/fabric/src/client/resources/fabric.mod.json
* 核心配置源码：https://github.com/reserveword/IMBlocker/blob/master/common/src/main/java/io/github/reserveword/imblocker/common/IMBlockerAutoConfig.java
* 焦点管理源码：https://github.com/reserveword/IMBlocker/blob/master/common/src/main/java/io/github/reserveword/imblocker/common/gui/FocusManager.java
* 聊天命令识别源码：https://github.com/reserveword/IMBlocker/blob/master/fabric/src/client/java/io/github/reserveword/imblocker/mixin/ChatScreenMixin.java
* 平台输入法实现：https://github.com/reserveword/IMBlocker/tree/master/common/src/main/java/io/github/reserveword/imblocker/common
* 更新日志：https://github.com/reserveword/IMBlocker/blob/master/CHANGELOG.md

它解决了哪些痛点
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 游戏中的痛点
     - IMBlocker 的处理方式
   * - 中文输入法一直开启时，``WASD``、``E``、``Q`` 或 MOD 快捷键被输入法/候选框抢走
     - 检测到当前焦点不是文字输入组件时，自动关闭或屏蔽输入法，让按键回到游戏操作。
   * - 聊天、JEI/REI/EMI 搜索、告示牌等文字界面需要反复切换输入法
     - 识别真正接收文本的组件，在文字框获得焦点时自动启用输入法。
   * - 每次发命令前都要手动切到英文，普通聊天又想保持中文
     - 监测聊天内容是否匹配命令前缀；命令默认切到英文状态，普通聊天使用设定的首选中英文状态。
   * - Windows 候选框出现在屏幕角落，或独占全屏时根本看不到
     - 跟踪文本光标位置并调整合成字体；Windows 还提供实验性的游戏内候选框渲染。
   * - Linux 候选词框出现时，退格、方向键等控制按键漏进游戏
     - 通过 GLFW 回调级键盘补丁拦截这类泄漏，减少误操作和“锁键”。

核心功能
--------

自动按“等效焦点”切换
~~~~~~~~~~~~~~~~~~~~~~

Minecraft 没有统一的 GUI 焦点管理机制。IMBlocker 使用 Mixin 监听已知 GUI 组件的焦点变化，并建立自己的焦点管理系统：

* 文本框、代码编辑器、搜索框等希望接收文字字符的组件，获得焦点后请求输入法。
* 游戏操作界面、按钮、列表等希望接收原始键盘输入的组件，获得焦点后屏蔽输入法。
* 模组的焦点请求不可靠时，IMBlocker 会过滤无效请求，只把实际接收键盘输入的“等效焦点组件”作为判断依据。

这样切换的依据是当前输入上下文，而不是简单地“打开 GUI 就开输入法”或“进入世界就关输入法”。

聊天、命令与中英文状态
~~~~~~~~~~~~~~~~~~~~~~~~

在聊天栏中，最新源码通过 ``IMBlockerConfig.isCommand(...)`` 判断文本是否为命令：

* 默认命令前缀正则为 ``^/``，例如 ``/give``、``/tp`` 会被识别为命令。
* 命令状态会把文本框的首选状态设为英文，避免中文输入法干扰命令和参数。
* 普通聊天使用“首选中英文状态”设置；默认是 ``CJK``（中文输入法状态）。习惯用拼音搜索的玩家可以改为 ``ENG``。
* “命令前缀正则表达式”是最新 master 新增的高级选项。如果服务器或 MOD 使用其他前缀，可按 Java 正则表达式修改，例如 ``^[/!]`` 同时匹配 ``/`` 和 ``!`` 开头的文本。

英文状态有两种实现方式：

* ``CONVERSION_STATUS``：直接切换输入法的中英文转换状态，Windows 默认使用此方式。
* ``DISABLE_IM``：用关闭输入法表示英文状态，再通过解锁按键恢复输入法；非 Windows 默认使用此方式。

Windows
~~~~~~~

Windows 实现直接调用系统 IME 接口，包含以下与候选框有关的处理：

* 跟踪文本光标，把系统候选框定位到 Minecraft 文本框附近。
* 根据游戏界面缩放调整合成字符串字体大小。
* “游戏内输入法”是实验性选项，主要用于独占全屏无法显示系统候选框的情况。它会在游戏窗口内绘制预编辑文字和候选词；如果系统候选框正常可见，优先使用系统候选框。

官方 README 还记录了一个 Windows/GLFW 已知问题：游戏窗口创建时若没有获得焦点，第一次获得焦点可能不会触发回调，导致输入状态看起来被锁住。遇到这种情况，让游戏窗口先失去焦点，再重新点回游戏窗口即可。

Linux
~~~~~

Linux 端支持基本的输入法开关控制，并会检测当前运行的是 IBus 还是 Fcitx5：

* IBus 默认通过 ``ibus engine`` 切换，开启参数为 ``libpinyin``，关闭参数为 ``xkb:us::eng``。
* Fcitx5 默认通过 ``fcitx5-remote`` 切换，开启参数为 ``-o``，关闭参数为 ``-c``，开启状态标识符为 ``2``。
* 如果发行版或输入法配置不同，可以在 Linux 兼容设置中改写这些命令参数。
* “回调级键盘补丁”默认开启，用于阻止候选词框显示时的控制键泄漏。若候选框因退格清空预编辑文字后关闭而出现按键不响应，官方提示可按 ``Esc`` 或输入任意字符解除状态。
* “进入临时英文状态的命令”和“退出临时英文状态的命令”可填入自定义命令，用于处理桌面环境没有统一中英文切换接口的情况。

macOS
~~~~~~

macOS 实现会在输入法被屏蔽时丢弃 Cocoa 的预编辑文本事件，在需要输入文字时恢复事件传递。因此它主要负责“是否允许文字事件进入游戏”，中英文转换仍取决于系统输入法本身。

配置说明
--------

配置入口通常是 Mod Menu 中的 IMBlocker 配置页面；官方 Fabric 元数据将 Cloth Config 列为可选建议依赖，若没有配置界面，可先安装与游戏版本匹配的 Cloth Config。

基础设置
~~~~~~~~

* **屏幕白名单**：某些 Screen（例如书与笔、告示牌或第三方自定义编辑界面）不会正常发出焦点请求。将其类名加入白名单后，打开该 Screen 时会主动启用输入法。官方源码还内置了少量默认白名单，默认项目不会因误删而失效。
* **GUI 屏幕记录**：临时记录出现过的 Screen 类名，并在屏幕左上角显示类名，方便复制到白名单。排查完后可以关闭记录功能。
* **英文状态实现方式**：优先保持默认值；只有自动切换英文失败时，才尝试 ``DISABLE_IM``，并使用默认右 ``Shift`` 解锁输入法。
* **首选中英文状态**：文本框获得焦点时的初始状态。``CJK`` 适合直接输入中文，``ENG`` 适合经常用拼音搜索的玩家。

高级设置
~~~~~~~~

* **使用模拟字符定位焦点**：通过发送一个模拟字符来定位真正焦点组件，精度更高；但未过滤模拟字符的第三方界面可能收到这个字符。遇到界面出现多余字符时关闭此选项。
* **命令前缀正则表达式**：默认 ``^/``。这是正则表达式，不是普通字符串列表；修改后应覆盖实际命令格式并避免过宽匹配。

Windows 兼容设置
~~~~~~~~~~~~~~~~~

* **转换状态 API**：关闭后，``CONVERSION_STATUS`` 方式不能切换中英文。
* **文本光标位置跟踪**：修复候选框无法贴近文本框的问题；出现候选框定位异常时优先保持开启。
* **合成字符串字体格式调整**：让候选框中的预编辑文字更贴近游戏界面缩放。
* **游戏内输入法**：实验性功能，仅在独占全屏无法显示系统候选框时考虑开启。

Linux 兼容设置
~~~~~~~~~~~~~~~

除了键盘补丁和临时英文状态命令外，IBus/Fcitx5 的开启、关闭参数及状态标识符都可以按本机终端命令结果调整。官方中文语言文件给出的验证方法是：

* IBus：在终端执行 ``ibus engine <参数>``，确认参数能切换到目标输入法或英文引擎。
* Fcitx5：执行 ``fcitx5-remote <参数>``，确认开启、关闭和状态查询结果。

自定义 GUI 与屏幕白名单
------------------------

官方 README 列出的自定义 GUI 兼容对象包括：

* `Roughly Enough Items <https://github.com/shedaniel/RoughlyEnoughItems>`_
* `EMI <https://github.com/emilyploszaj/emi>`_
* `Axiom <https://axiom.moulberry.com/>`_
* `Replay Mod <https://www.replaymod.com/>`_
* `FTB Library <https://github.com/FTBTeam/FTB-Library>`_
* `Meteor Client <https://www.meteorclient.com/>`_
* `LibGui <https://github.com/CottonMC/LibGui>`_
* `Reese's Sodium Options <https://github.com/FlashyReese/reeses-sodium-options>`_
* `BlockUI <https://github.com/ldtteam/BlockUI>`_
* `SuperMartijn642's Core Lib <https://github.com/SuperMartijn642/SuperMartijn642sCoreLib>`_
* `Notes <https://github.com/MattCzyr/Notes>`_
* `Essential Mod <https://essential.gg/>`_
* `Armourer's Workshop <https://github.com/Armourers-Workshop/Armourers-Workshop>`_
* `ModernUI <https://github.com/BloCamLimb/ModernUI-MC>`_

如果某个第三方 GUI 仍然无法自动切换：

#. 开启 GUI 屏幕记录，打开目标界面并记下左上角显示的类名。
#. 将类名加入屏幕白名单；类名中包含模组前缀时也可以直接粘贴完整记录。
#. 重新打开界面验证输入法状态。仍无法识别时，可将复现信息提交到官方 `Issue #13 <https://github.com/reserveword/IMBlocker/issues/13>`_。

常见问题
--------

**Q：为什么进入世界后按键还是像被输入法抢走？**

A：先确认游戏窗口确实获得焦点，再检查 IMBlocker 是否识别到了当前 GUI。Windows 首次获得窗口焦点可能触发 GLFW 已知问题，先切到其他窗口再切回游戏；第三方界面则按“GUI 屏幕记录 + 白名单”流程处理。

**Q：聊天能打中文，但输入 ``/`` 命令时仍然是中文状态怎么办？**

A：检查高级设置中的命令前缀正则是否为 ``^/``，以及输入法是否支持所选的英文状态实现方式。使用 ``!`` 等前缀的服务器，可改成 ``^[/!]`` 等匹配规则。

**Q：自动切到英文后，怎样临时恢复中文输入？**

A：在 ``DISABLE_IM`` 方式下，默认右 ``Shift`` 是“解锁输入法”按键；如果按键冲突，可在控制设置中修改 ``解锁输入法``。

**Q：候选框位置不对或独占全屏看不到，是否需要打开游戏内输入法？**

A：Windows 先保持“文本光标位置跟踪”和“合成字符串字体格式调整”开启。只有独占全屏无法显示系统候选框时，再尝试开启实验性的“游戏内输入法”。

**Q：开启模拟字符后，某些界面多出一个字符怎么办？**

A：这是官方明确提示的副作用：未过滤模拟字符的界面可能收到它。关闭“使用模拟字符定位焦点”，或为该界面补充兼容后再使用。

**Q：Linux 候选框出现时方向键、退格等按键会影响游戏怎么办？**

A：确认“回调级键盘补丁”已开启；如果候选框因退格清空预编辑文字后卡住，按 ``Esc`` 或输入任意字符解除状态。IBus/Fcitx5 参数也应按终端实际输出校准。

**Q：这是服务端 MOD 吗？**

A：不是。官方 Fabric 元数据将运行环境标记为 ``client``，它只控制本机游戏窗口和本机输入法；多人服务器通常不需要安装，但仍应遵守服务器对客户端 MOD 的规定。

限制与排查顺序
--------------

IMBlocker 需要通过注入或白名单了解 GUI 的焦点行为，未被注入且使用独立组件框架的第三方界面可能无法自动识别。建议按以下顺序排查：

#. 先确认安装的是与当前加载器、Minecraft 版本相匹配的官方构建。
#. 确认游戏窗口焦点正常，尤其是 Windows 启动后的第一次切回。
#. 确认输入法平台（Windows IME、IBus、Fcitx5）和对应参数可在系统层面正常切换。
#. 对单个异常界面使用屏幕记录和白名单，不要一开始就打开模拟字符。
#. 仍有问题时，记录操作系统、输入法、游戏版本、加载器和异常 GUI 类名，再向官方仓库反馈。

相关项目
--------

* GitHub：https://github.com/reserveword/IMBlocker
* GitHub Releases：https://github.com/reserveword/IMBlocker/releases
* Modrinth（发布文件与仓库 master 可能不同步）：https://modrinth.com/mod/imblocker-original

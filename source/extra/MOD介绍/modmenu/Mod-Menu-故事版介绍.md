# Mod Menu：给模组城装上一间前台

> 本文不把 Mod Menu 讲成一张枯燥的功能表。我们跟着一位刚装好整合包的玩家，看看这间“模组前台”到底在忙什么。
>
> 内容已核对官方源码 `v20.0.1`（Minecraft 26.2），核对日期为 2026-07-22。不同 Minecraft 版本的界面可能略有差别，但核心定位相同。

## 开场：小林的模组箱失控了

小林刚组好一个 Fabric 客户端。游戏能启动，光影在跑，地图也能打开，可他已经记不清 `mods` 文件夹里那几十个 JAR 各自是做什么的了。

他想找到某个小地图的配置，却遇到了一串问题：

- 模组的正式名字叫什么？
- 它是普通功能模组，还是其他模组需要的前置库？
- 它有没有图形配置页？
- 作者的官网、源码和问题反馈页在哪里？
- 现在装的版本是不是已经过时了？

Mod Menu 就在这时候出场了。

它没有加入新方块，也没有为玩家增加一种超能力。它只是在 Minecraft 里摆上一张干净的桌子，然后说：

> “你装的模组，我来帮你认、找、查和打开。”

## 第一幕：主菜单多了一扇门

安装 Mod Menu 后，主菜单会出现进入“模组”页面的按钮或图标，暂停菜单也可以放置入口。默认还会把已加载的模组数量显示在标题画面。

小林点开这扇门，终于不用退出游戏、翻文件夹，再拿文件名一个个猜了。

这个入口不是固定死的。Mod Menu 自己的设置里可以调整：

- 主菜单显示为小图标、独立按钮、与 Realms 并排，或替换 Realms 按钮。
- 暂停菜单使用小图标，或插入一个完整宽度的按钮。
- 模组总数显示在标题画面、模组按钮、两处都显示，或完全不显示。
- 在“按键设置”中给“打开模组菜单”绑定快捷键。源码中这个按键默认未绑定，不存在一个适用所有人的“默认快捷键”。

## 第二幕：左边是名册，右边是档案

模组页面很像一间小型档案室。

左半边是模组名册：图标、名字和一句简介排成列表。选中某个模组后，右半边就摊开它的完整档案：

- 模组名称、图标、版本号与模组 ID；
- 作者和贡献者；
- 详细介绍；
- 官网与问题反馈页；
- 源代码、自定义链接和许可证；
- 该模组有没有可用的配置页。

这些资料不是 Mod Menu 在网上临时搜出来的。它主要读取模组 JAR 内的 `fabric.mod.json` 或 Quilt 元数据，再加上模组作者通过 Mod Menu API 提供的信息。所以，某个项目没有官网按钮或介绍太简略，往往是因为原模组没有提供这份资料，而不是 Mod Menu 把它弄丢了。

### 搜索框比看上去更聪明一点

小林不记得小地图的全名，只记得作者名字。他把作者名输进搜索框，目标模组依然出现了。

从源码看，搜索会检查：

- 原始模组名、本地化后的名称和模组 ID；
- 详细介绍与短摘要；
- 作者名；
- “前置”“客户端”“可配置”“有更新”等属性关键词。

名称和 ID 命中的结果会优先排在前面。它不是互联网搜索引擎，也不会自动纠正拼写，但对一个几十乃至上百个模组的客户端来说，已经足够好用。

### 过滤器负责把“幕后人员”收起来

很多玩家会被 Fabric API 拆分出来的大量模块、语言库和前置库淹没。Mod Menu 为这些项目设置了“前置”徽章，并且允许玩家选择：

- 显示所有前置库；
- 完全隐藏前置库；
- 只显示那些“自己也有配置页”的前置库。

列表还能按 A–Z、Z–A 或“有更新”排序，并在标准列表与紧凑列表之间切换。

## 第三幕：“配置”按钮是一把通用门铃

小林选中小地图模组，右上角的“配置”按钮亮了起来。他点下去，进入了小地图自己的设置界面。

这里有一条非常重要的边界：

> Mod Menu 负责“找到并打开配置页”，但配置页本身通常由那个模组，或 Cloth Config 这类配置库提供。

如果原模组没有接入 Mod Menu API，也没有其他模组代它提供配置页，那么 Mod Menu 不会凭空造出一套选项。有些模组仍需要手动编辑 `config` 文件，或在自己的按键菜单中设置。

Mod Menu 还提供了两种“快速配置”方式：

- 鼠标移到可配置模组的图标上，点击覆盖在图标上的配置标记；
- 快速双击该模组的列表项。

如果某个模组的配置页在打开时报错，Mod Menu 会捕获异常，禁用这个入口并给出提示。官方中文文案还特别说明：这类错误应该报告给对应模组，而不是 Mod Menu。

## 第四幕：一枚小徽章，就是一句身份说明

小林注意到，有些模组名字后面跟着彩色徽章。这些徽章不是装饰，而是让玩家一眼看懂它的身份：

- **前置（Library）**：主要供其他模组调用；
- **客户端（Client）**：元数据声明它只需在客户端运行；
- **已过时（Deprecated）**：为兼容老版本而保留的旧模块；
- **Forge**：标记经 Patchwork 处理的 Forge/FML 模组；
- **整合包（Modpack）**：由整合包标记的组件；
- **Minecraft**：基础游戏本身。

模组作者还可以把多个子模块挂在同一个父项目下。于是 Fabric API 这类拆成许多部件的项目，可以像文件夹一样展开和收起，不再把主列表挤得到处都是零件。

它甚至支持模组名、摘要和详细介绍的本地化。装有 Text Placeholder API 时，介绍文字还可以使用 QuickText 格式。这就是为什么同样一个模组，在准备充分的情况下，能像一张正经的中文资料卡，而不只是一个英文文件名。

## 第五幕：前台还会提醒“有新版本了”

过了几天，小林再次启动游戏，发现模组按钮角上多了一枚更新标记。点进去后，有新版本的模组也带着同样的提示，详情区会给出版本与下载链接。

Mod Menu `v20.0.1` 的内置更新检查大致是这样工作的：

1. 为可检查的模组 JAR 计算 SHA-512 哈希；
2. 把哈希、Minecraft 版本、加载器类型和用户选择的更新频道发给 Modrinth API；
3. 比较当前文件与匹配版本的哈希和发布时间；
4. 如果发现更新，在列表与详情页标记，并把下载链接指向对应的 Modrinth 版本页。

模组也可以提供自己的更新检查器。Mod Menu 本身就代表 Fabric Loader 接入了 Fabric 的版本服务。

玩家可以关闭更新检查、隐藏入口上的更新标记，或选择只看正式版、同时接收测试版，以及接收所有 Alpha/Beta/Release 版本。

不过，它是“更新提醒”，不是“一键自动更新器”。点击下载会前往网页，不会在背景偷偷替换你的 JAR。官方文案也把更新检查标为实验性功能，网络、平台 API、非 Modrinth 来源以及模组作者的元数据，都可能影响结果。

## 第六幕：把 JAR 直接交给前台

小林又下载了一个新模组。这次他没有再寻找实例的 `mods` 目录，而是直接把 JAR 拖进 Mod Menu 窗口。

Mod Menu 会检查模组元数据：在 Fabric 环境下识别 `fabric.mod.json`，在 Quilt 环境下还会识别 `quilt.mod.json`。然后它列出即将复制的文件，并等待玩家确认。复制成功后，它会提醒重启游戏才能加载。页面底部也有“打开模组文件夹”按钮。

这个功能解决的是“把文件放对位置”，不是完整的包管理：

- 它不会自动解决缺少的前置依赖；
- 不会替你判断所有版本冲突；
- 不会让刚放入的模组热加载；
- 也不会覆盖同名文件来“强制更新”。

对新手来说，使用 Prism Launcher、Modrinth App 这类启动器管理依赖和版本，仍然更稳妥。

## 第七幕：前台也有自己的装修选项

小林最后在列表里选中了 Mod Menu 自己，然后点下“配置”。原来这间前台还可以按自己的习惯装修。

除了前面提到的菜单入口、过滤、列表密度和更新选项，还可以调整：

- 是否把子模组、前置库和隐藏模组计入总数；
- 是否显示徽章、模组链接、许可证和贡献者名单；
- 模组名和介绍使用本地化文本，还是保留原始文本；
- 是否启用快速配置；
- 是否显示一些基于模组数量的小彩蛋。

少数高级选项只保存在 `config/modmenu.json` 中，例如隐藏指定模组、隐藏指定配置入口、对指定模组禁用更新检查，或关闭拖放安装。这些更适合整合包作者和熟悉 JSON 的玩家，普通用户不需要为了“设置得更彻底”去硬改。

## 揭秘：这间前台怎么知道这么多？

把技术过程压缩成一条好懂的路线，大概是：

```text
Fabric / Quilt Loader 提供已加载模组
                 ↓
Mod Menu 读取名称、版本、图标、作者、链接等元数据
                 ↓
叠加 Mod Menu API 提供的配置页、更新检查和徽章
                 ↓
组织成可搜索、可过滤、可展开的界面
```

所以 Mod Menu 能不能显示一个模组的丰富信息，不只取决于 Mod Menu，也取决于原模组作者提供了多少元数据，以及有没有接入它的 API。

## 四个常见误会

| 误会 | 实际情况 |
| --- | --- |
| “有 Mod Menu 就能配置所有模组” | 只能打开已经由对应模组或其他配置库注册的配置页。 |
| “可以在列表里开关模组” | 它是查看和导航菜单，不是运行时模组启停器。 |
| “它是模组商店” | 它可以提示更新、接收拖入的 JAR，但不会在游戏里搜索和一键安装整个 Modrinth 市场。 |
| “服务器也必须安装” | Mod Menu 是客户端模组，Modrinth 标记为客户端必需、服务器端不支持。它不需要放到服务器。 |

## 安装与一分钟上手

### 安装前先确认

- 它用于 **Minecraft: Java Edition**。
- 官方支持 **Fabric** 与 **Quilt**。
- Mod Menu 长期提供了多个 Minecraft 版本的构建，但每个 JAR 都应与当前 Minecraft 版本匹配。本文核对的 `20.0.1` 对应 Minecraft `26.2`。
- 通过 Modrinth 或启动器安装时，跟随对应版本页的依赖提示。`20.0.1` 的 Modrinth 版本页列出 Fabric API 和 Text Placeholder API，其他 Minecraft 版本不要直接照搬这份清单。
- 项目采用 MIT License。

### 上手路线

1. 进入主菜单，点击“模组”按钮或图标。
2. 先用搜索框输入模组名、ID 或作者名。
3. 点击左侧项目，在右侧查看版本、介绍、链接和许可证。
4. “配置”按钮可用时，点击它进入该模组提供的设置页。
5. 列表太乱时，把前置库设为隐藏或“只显示可配置的前置”。
6. 最后再打开 Mod Menu 自己的配置，调整入口样式、紧凑列表和更新频道。

## 尾声：它不是最热闹的模组，却是很好的管家

小林最后并没有从 Mod Menu 里得到一把新武器，也没解锁一个新维度。他只是终于知道，自己的客户端里到底住着谁，它们各自负责什么，要去哪里设置，又该去哪里求助。

这就是 Mod Menu 的价值：

> **它不生产每个模组的功能，它让每个模组更容易被看见、被理解、被配置。**

## 资料口径与源码索引

### 官方项目

- Modrinth：<https://modrinth.com/mod/modmenu>
- GitHub：<https://github.com/TerraformersMC/ModMenu>
- `v20.0.1` 源码标签：<https://github.com/TerraformersMC/ModMenu/tree/v20.0.1>
- 本文核对提交：[`74098c61626d2beb3c2ff146261aac52c34206bc`](https://github.com/TerraformersMC/ModMenu/commit/74098c61626d2beb3c2ff146261aac52c34206bc)

### 功能对应的主要代码

- 初始化、读取模组、配置页注册：[`ModMenu.java`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/ModMenu.java)
- 主界面、详情区、拖放安装：[`ModsScreen.java`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/gui/ModsScreen.java)
- 列表、前置过滤、父子模组：[`ModListWidget.java`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/gui/widget/ModListWidget.java)
- 搜索规则：[`ModSearch.java`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/util/mod/ModSearch.java)
- 快速配置：[`ModListEntry.java`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/gui/widget/entries/ModListEntry.java)
- 描述、链接、许可证与更新信息：[`DescriptionListWidget.java`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/gui/widget/DescriptionListWidget.java)
- Mod Menu 可见设置与高级设置：[`ModMenuConfig.java`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/config/ModMenuConfig.java)
- 更新检查：[`UpdateCheckerUtil.java`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/util/UpdateCheckerUtil.java)
- 模组作者的接入能力：[`ModMenuApi.java`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/java/com/terraformersmc/modmenu/api/ModMenuApi.java)
- 项目元信息、客户端定位与许可证：[`fabric.mod.json`](https://github.com/TerraformersMC/ModMenu/blob/v20.0.1/src/main/resources/fabric.mod.json)

---

> 后续如果要把这篇文章做成视频或交互页，画面主线可以固定为：“主菜单入口 → 搜索一个模组 → 打开资料卡 → 进入配置 → 识别前置徽章 → 查看更新 → 拖入新 JAR”。

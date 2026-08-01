# Just Enough Items（JEI）：把配方查询放进游戏里

> 本文按 JEI 官方仓库 `26.2` 分支和当前 HSDS 26.2 整合包清单整理。JEI 的重点是物品查询、配方查看、书签和配方转移，不是自动建造器，也不是完整的模组管理器。
>
> 当前整合包清单版本：`30.11.0.67`。

## 一句话理解

JEI 就是游戏里的配方前台：你在物品列表里搜名字，点进去看用途和合成方式，把常查条目标成书签，必要时还能把材料直接塞进对应容器。它也给模组作者留了一套接口。

## 功能总览

| 功能 | 作用 |
| --- | --- |
| 物品列表 | 在物品面板里搜索、翻页、滚动和筛选 |
| 配方查看 | 按分类标签切换配方页，查看材料、结果和催化方块 |
| 书签 | 把常用物品或配方固定下来，并支持拖拽重排 |
| 历史记录 | 记住最近看过的条目，方便回看 |
| 配方转移 | 在支持的容器里自动填写材料槽位 |
| 给物品 / 删物品 | 在有权限时把条目直接送进背包、快捷栏或删除 |
| 聊天链接 | 聊天里的 JEI 链接可以直接跳到对应配方 |

## 主要功能

### 1. 物品列表与搜索

- JEI 会把可浏览的条目放进一个独立列表。
- 搜索栏支持按名称、模组名、模组 ID、标签、tooltip 和条目别名快速筛选。
- 搜索栏位置和配方窗高度都能配置，不是固定死的。
- 当搜索词清空时，列表会回到第一页。
- 搜索范围还能细调：模组 ID、模组别名、条目别名、简短模组名和进阶 tooltip 都有独立开关。

### 2. 配方窗口

- 配方窗口不是单一列表，而是按 recipe category 分页显示。
- 顶部和底部的标签页用于切换不同配方分类。
- 左侧会显示当前分类能用到的催化方块或工作站，比如能做这个配方的容器/工作台类型。
- 当你从某个物品或配方进入 JEI 时，它会把焦点放在对应条目上，再展开相关配方。

### 3. 书签

- 书签分两类：物品书签和配方书签。
- 书签栏可以开关、拖拽和重排。
- 默认书签提示只显示预览图；需要的话还能额外显示组成材料。
- 看配方结果时，默认会把输出当成配方书签处理，而不是只记一个产物图标。

### 4. 历史记录

- JEI 会记录最近查过的条目，按最近使用优先排列。
- 历史栏默认关闭，打开后可放在左侧或右侧。
- 历史栏默认最多 2 行、100 条，可再按需要调大，避免把界面挤满。

### 5. 给物品、删物品和快捷栏

- `Give Mode` 默认是 `MOUSE_PICKUP`，也就是把物品送到鼠标手上。
- 也可以切成直接进背包。
- 还有一个“把物品送到快捷栏”的热键路径。
- 这些能力都走服务器权限检查；没权限时会提示并关闭当前容器。
- 所以它不是“单机能用、多人就默认作弊成功”的那种逻辑。

### 6. 聊天里的 JEI 链接

- JEI 还接了聊天界面。
- 聊天消息里如果带有 JEI 生成的物品链接，点它就能直接打开对应配方。
- 原版 `show item` 类型的聊天悬停也会被接入到 JEI 的可点击条目里。

## 进阶设置

- `lowMemorySlowSearch`：低内存模式下用更省内存的搜索方式。
- `catchRenderErrors`：渲染出错时尽量兜住，不让界面直接炸掉。
- `lookupFluidContents`：允许查询流体内容。
- `lookupBlockTags`：允许查询方块标签。
- `showTagRecipes`：显示 tag 相关配方。
- `showCreativeTabNames`：在相关界面显示创造模式标签页名称。
- `showHiddenIngredients`：显示被隐藏的条目。
- `ingredientsSummaryEnabled`：在配方 GUI 里显示材料摘要。

## 安装与边界

- 官方 `26.2` 分支的构建信息写的是 `Minecraft 26.2`、`Fabric Loader 0.19.3`、`Fabric API 0.155.0+26.2`、`Java 25+`。
- Fabric 版 `fabric.mod.json` 注册了 `main`、`client` 和 `jei_mod_plugin` 入口。
- 日常使用以客户端体验为主，但给物品、删物品和配方转移会和服务器权限打交道。
- 服务器不开权限时，基础的查配方、看用途、收藏书签仍然是 JEI 最核心的价值。

## 适合谁

- 想少翻 wiki 的生存玩家
- 做整合包、想统一配方入口的玩家
- 需要从物品反查配方链的技术玩家
- 做教程、录屏和演示视频的人

## 源码依据

- 官方仓库说明：<https://github.com/mezz/JustEnoughItems/blob/26.2/README.md>
- 构建与依赖：<https://github.com/mezz/JustEnoughItems/blob/26.2/gradle.properties>
- 物品列表与搜索：<https://github.com/mezz/JustEnoughItems/blob/26.2/Gui/src/main/java/mezz/jei/gui/overlay/IngredientListOverlay.java>
- 搜索面板控制：<https://github.com/mezz/JustEnoughItems/blob/26.2/Gui/src/main/java/mezz/jei/gui/overlay/IngredientListOverlayController.java>
- 配方窗口主逻辑：<https://github.com/mezz/JustEnoughItems/blob/26.2/Gui/src/main/java/mezz/jei/gui/recipes/RecipeGuiLogic.java>
- 配方窗口界面：<https://github.com/mezz/JustEnoughItems/blob/26.2/Gui/src/main/java/mezz/jei/gui/recipes/RecipesGui.java>
- 书签：<https://github.com/mezz/JustEnoughItems/blob/26.2/Gui/src/main/java/mezz/jei/gui/overlay/bookmarks/BookmarkOverlay.java>
- 历史记录：<https://github.com/mezz/JustEnoughItems/blob/26.2/Gui/src/main/java/mezz/jei/gui/overlay/bookmarks/history/LookupHistoryOverlay.java>
- 配方转移：<https://github.com/mezz/JustEnoughItems/blob/26.2/Common/src/main/java/mezz/jei/common/network/packets/PacketRecipeTransfer.java>
- 给物品 / 删物品：<https://github.com/mezz/JustEnoughItems/blob/26.2/Common/src/main/java/mezz/jei/common/network/packets/PacketGiveItemStack.java>
- 给物品 / 删物品：<https://github.com/mezz/JustEnoughItems/blob/26.2/Common/src/main/java/mezz/jei/common/network/packets/PacketDeletePlayerItem.java>
- 权限请求：<https://github.com/mezz/JustEnoughItems/blob/26.2/Common/src/main/java/mezz/jei/common/network/packets/PacketRequestCheatPermission.java>
- 聊天链接：<https://github.com/mezz/JustEnoughItems/blob/26.2/Common/src/main/java/mezz/jei/common/chat/JeiChatItemLinks.java>
- 聊天跳转：<https://github.com/mezz/JustEnoughItems/blob/26.2/Common/src/main/java/mezz/jei/common/chat/JeiChatItemLinkRecipeLookup.java>

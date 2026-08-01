InvMove：打开界面也能继续移动
================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#3e7cb1;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       打开 InvMove 图文与实机演示
     </a>
   </p>

InvMove 让玩家在背包、箱子、工作台及其他非暂停界面打开时，仍可使用指定的移动按键。它解决的是“查看或整理物品时角色被迫停住”的操作问题，不会替玩家自动移动或绕过服务器规则。

本文按上游 v0.9.5、提交 430dab1（2026-06-16）的 26.2 源码整理；它与当前整合包清单中的 InvMove 0.9.5 对应。

功能清单
----------

* **界面中持续读取移动输入**：客户端每次更新本地玩家输入后，InvMove 会根据当前 Screen 与配置决定是否保留移动键状态。因此可以边打开普通 GUI 边前进、转向、跳跃或疾跑。
* **按键逐项许可**：移动、跳跃、潜行、下坐骑/离开载具等不是强制绑在一起。默认允许跳跃；下坐骑默认关闭，避免在整理界面时误操作。
* **文本框保护**：默认在文本输入框取得焦点时停用移动，以免输入文字时角色意外走动。这个开关可按需要关闭。
* **逐个界面配置**：可为特定 MOD 的界面保存是否允许移动、允许哪些键、是否隐藏背景；未知界面也有独立的默认规则，而不是一刀切。
* **背景遮罩控制**：能隐藏非暂停 Screen 的原版半透明背景，方便边移动边观察世界；暂停界面与未知界面可分别配置。
* **调试信息**：配置中提供调试覆盖层选项，方便确认当前界面被识别为哪个模块及采用了哪条规则。

配置方式与保存位置
--------------------

通常通过 Mod Menu 打开 InvMove 配置页。全局设置保存在 ``config/invmove.json`` ；被识别的模块按 ``config/invmove/<module>.json`` 保存，无法识别的界面则使用 ``config/invmove/unrecognized.json`` 。这意味着你可以只让背包、箱子等熟悉界面支持移动，而为陌生的第三方 GUI 保留更保守的规则。

初次使用建议：先保留“文本框禁用移动”和“下坐骑关闭”，在单人世界测试常用容器；若某个界面按钮会与移动冲突，再为该界面单独禁用移动或缩小允许按键范围。

依赖与兼容
------------

* **Cloth Config**：Fabric 26.2 元数据中的必需依赖。
* **Fabric Key Mapping API**：上游列为推荐项，不是硬依赖；缺失时不要假定切换快捷键一定可用。
* **Mod Menu**：提供方便的配置入口，但 InvMove 本体不依赖它才能工作。
* **InvMoveCompats**：REI、JEI、EMI 等配方查看器的额外兼容已拆分到这个配套 MOD；需要时再安装。

多人服注意事项
----------------

InvMove 是 ``client`` 环境 MOD，不要求服务器安装，也不会修改服务器的移动规则。但有些公共服务器的反作弊会把“打开容器时移动”视为异常输入；进入多人服前应查看规则，遇到误判则为相关界面关闭 InvMove。它不是用来规避服务器限制的工具。

源码依据
----------

* `配置、默认值与分界面保存 <https://github.com/PieKing1215/InvMove/blob/430dab1190b88f3d147b4a5cea2ec1fd008e4cb4/common/src/main/java/me/pieking1215/invmove/InvMoveConfig.java>`_
* `玩家输入接管 <https://github.com/PieKing1215/InvMove/blob/430dab1190b88f3d147b4a5cea2ec1fd008e4cb4/common/src/main/java/me/pieking1215/invmove/mixin/client/MovementMixin.java>`_
* `界面背景遮罩处理 <https://github.com/PieKing1215/InvMove/blob/430dab1190b88f3d147b4a5cea2ec1fd008e4cb4/common/src/main/java/me/pieking1215/invmove/mixin/client/BackgroundMixin.java>`_
* `官方仓库与兼容说明 <https://github.com/PieKing1215/InvMove>`_

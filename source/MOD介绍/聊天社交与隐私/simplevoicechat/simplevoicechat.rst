Simple Voice Chat - 距离语音与群组通话
===============================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#0f766e;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       打开 Simple Voice Chat 核心演示
     </a>
   </p>

Simple Voice Chat 为 Minecraft 加入游戏内语音聊天。玩家可以像在合作游戏中一样直接说话，声音会根据与其他玩家的距离和方向播放。

核心功能
------------

* **距离语音**：离得越近听得越清楚，并支持三维方向感。
* **按键说话与语音激活**：可选按住快捷键说话，或由麦克风音量自动激活。
* **悄悄话**：降低声音可被听到的距离。
* **群组语音**：创建可设密码的语音群组，不受玩家所在位置限制。
* **单独音量调整**：为不同玩家分别设置音量，也可以静音自己或屏蔽他人。

默认按 ``V`` 打开语音聊天界面，可以在其中选择麦克风和播放设备、测试声音、管理群组以及调整其他玩家的音量。

服务器要求
------------

Simple Voice Chat 不是只把 JAR 放进客户端就能在任意服务器上使用的语音工具。要让语音功能实际连接：

* 玩家客户端需要安装 Simple Voice Chat。
* 服务器需要安装对应的 MOD 或插件，并完成语音服务配置。
* 默认使用 ``24454/UDP``，服务器防火墙和网络入站规则需要放行该端口；端口可在服务器配置中修改。

如果服务器没有提供语音支持，客户端仍然可以进入服务器，但不能使用游戏内语音。

隐私与录音提示
----------------

模组支持 AES 加密，但官方明确表示不对其安全性作保证。它还支持录音和独立音轨；服务器管理者应告知玩家语音规则，玩家也应了解语音可能被其他参与者录制。

版本与安装
------------

本文以 **Simple Voice Chat 2.6.21+26.2** 的 Fabric 正式版为基线，对应 Minecraft 26.2。该版本没有列出必需的其他 MOD 依赖；Cloth Config 和 Mod Menu 可选，用于改善图形化配置入口。

官方项目
------------

* Modrinth：https://modrinth.com/mod/simple-voice-chat
* GitHub：https://github.com/henkelmax/simple-voice-chat
* 官方 Wiki：https://modrepo.de/minecraft/voicechat/wiki
* 服务器设置：https://modrepo.de/minecraft/voicechat/wiki/setup

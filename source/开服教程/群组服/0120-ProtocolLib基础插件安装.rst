==================================================
ProtocolLib基础插件安装
==================================================

ProtocolLib 是一个专为 Minecraft 服务器开发的核心插件，主要用于拦截、修改和发送游戏网络数据包（Protocol）。
它为开发者提供了底层网络协议的访问能力，允许创建高度自定义的服务器功能，是许多高级插件（如物品展示、自定义实体、数据包级别的反作弊系统）的基础依赖。

插件简介
==================================================
- 支持绝大多数 Paper/Spigot/Bukkit 版本
- 允许插件直接操作 Minecraft 协议数据包
- 是物品展示、反作弊、粒子特效、虚拟实体等高级插件的前置依赖
- 免费开源，长期维护

.. image:: https://raw.githubusercontent.com/dmulloy2/ProtocolLib/master/logo.png
   :width: 300px
   :align: center

关键链接
==================================================
- SpigotMC: https://www.spigotmc.org/resources/protocollib.1997/
- GitHub: https://github.com/dmulloy2/ProtocolLib
- CI下载: https://ci.dmulloy2.net/job/ProtocolLib/

安装步骤
==================================================
1. 从 SpigotMC 或 CI 下载 ProtocolLib 的 jar 包
2. 放到所有分区的 plugins 目录（如 /home/mc/instances/dl1/plugins/）
3. 重启所有服务端，确认 ProtocolLib 正常加载

.. code-block:: bash

    wget https://ci.dmulloy2.net/job/ProtocolLib/lastSuccessfulBuild/artifact/target/ProtocolLib.jar
    cp ProtocolLib.jar /home/mc/instances/dl1/plugins/
    cp ProtocolLib.jar /home/mc/instances/dp1/plugins/
    cp ProtocolLib.jar /home/mc/instances/sc1/plugins/
    cp ProtocolLib.jar /home/mc/instances/sc2/plugins/
    # 重启所有服务端

配置说明
==================================================
- ProtocolLib 无需复杂配置，安装即用
- 所有依赖 ProtocolLib 的插件需与其版本兼容
- 如遇兼容性问题，优先升级 ProtocolLib 到最新版本

权限配置
==================================================
这个插件，目前没有啥权限授予的， 不过还是创建一个虚拟组。 

.. code-block:: bash 

    /lp creategroup g_protocollib 0 g_protocollib
    /lp group default parent add g_protocollib

常见问题 QA
==================================================
:Q1: ProtocolLib 安装后无效？  
:A1: 检查服务端版本是否兼容，查看 `/plugins` 列表和服务端日志。

:Q2: 某些插件报 ProtocolLib 版本不兼容？  
:A2: 升级 ProtocolLib 到最新版本，或联系插件作者获取兼容版本。

:Q3: ProtocolLib 需要配置吗？  
:A3: 无需配置，安装即用，所有功能由其他插件实现。


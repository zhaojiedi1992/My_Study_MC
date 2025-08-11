==================================================
Vault基础插件安装
==================================================

Vault 是 Minecraft 服务器最常用的经济、权限、聊天 API 桥接插件，几乎所有经济类、权限类、聊天类插件都依赖 Vault，属于必须前置安装的基础插件。

插件简介
==================================================
Vault 不是一个经济系统本身，而是为插件开发者提供统一的接口，方便各种经济、权限、聊天插件互相兼容和调用。  
它简化了插件间的对接流程，是群组服、经济服、权限服的标准依赖。

- 支持主流经济插件（EssentialsX、CMI、PlayerPoints 等）
- 支持主流权限插件（LuckPerms、PermissionsEx 等）
- 支持主流聊天插件（ChatEx、EssentialsChat 等）
- 免费开源，长期维护

.. image:: https://raw.githubusercontent.com/MilkBowl/Vault/master/logo.png
   :width: 300px
   :align: center

关键链接
==================================================
- SpigotMC: https://www.spigotmc.org/resources/vault.34315/
- GitHub: https://github.com/MilkBowl/Vault
- Wiki文档: https://github.com/MilkBowl/Vault/wiki

安装步骤
==================================================
1. 从 SpigotMC 或 GitHub 下载 Vault 的 jar 包
2. 放到所有分区和 Proxy 的 plugins 目录
3. 重启所有服务端，确认 Vault 正常加载

.. code-block:: bash

    wget https://cdn.spigotmc.org/Vault.jar
    cp Vault.jar /home/mc/instances/dl1/plugins/
    cp Vault.jar /home/mc/instances/dp1/plugins/
    cp Vault.jar /home/mc/instances/sc1/plugins/
    cp Vault.jar /home/mc/instances/sc2/plugins/
    cp Vault.jar /home/mc/instances/proxy/plugins/
    # 重启所有服务端



配置说明
==================================================
- Vault 无需复杂配置，安装即用
- 具体经济、权限、聊天功能由其他插件实现（如 EssentialsX、LuckPerms、CMI 等）
- Vault 仅作为接口桥接，确保所有依赖插件都已安装



权限配置
==================================================
这个插件，目前没有啥权限授予的， 不过还是创建一个虚拟组。 

.. code-block:: bash 

    /lp creategroup g_vault 0 g_vault
    /lp group default parent add g_vault

补充说明
==================================================
Vault 只是定义了接口，具体的经济实现还是依赖其他组件。  
如 EssentialsX 已自带经济系统（EssentialsX Economy），无需单独安装如 xEconomy。  
只需保证 Vault 与经济插件、权限插件同时安装即可。

常见问题 QA
==================================================
:Q1: Vault 安装后无效？  
:A1: 检查是否已安装经济/权限插件，Vault 仅作为桥接接口，需配合其他插件使用。

:Q2: 经济/权限命令报错找不到 Vault？  
:A2: 检查 Vault 是否已放入 plugins 目录并加载，查看 `/plugins` 列表和服务端日志。

:Q3: Vault 需要配置吗？  
:A3: 无需配置，安装即用，所有功能由其他插件实现。

:Q4: Vault 支持哪些经济插件？  
:A4: 支持 EssentialsX、CMI、PlayerPoints、Gringotts Economy 等主流经济插件。

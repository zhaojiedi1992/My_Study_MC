==================================================
PlaceholderAPI基础插件安装
==================================================

PlaceholderAPI 是 Minecraft 服务器最常用的变量支持插件，允许其他插件通过统一格式显示各种信息（如玩家、服务器、经济、权限等），是菜单、聊天、公告等功能的基础依赖。

插件简介
==================================================
- 支持 230+ 扩展，覆盖主流插件
- 统一变量格式，便于跨插件调用
- 支持 Proxy 和所有分区
- 免费开源，长期维护

.. image:: https://wiki.placeholderapi.com/assets/images/papi-banner.png
   :width: 600px
   :align: center

关键链接
==================================================
- SpigotMC: https://www.spigotmc.org/resources/placeholderapi.6245/
- 官方文档: https://wiki.placeholderapi.com/users/commands/
- 扩展列表: https://api.extendedclip.com/all/
- 变量列表: https://wiki.placeholderapi.com/users/placeholder-list/#standalone

安装步骤
==================================================
1. 下载 PlaceholderAPI jar 包，放到所有分区和 Proxy 的 plugins 目录
2. 重启所有服务端，确认插件正常加载
3. 无需复杂配置，config.yml 默认即可

.. code-block:: bash

    # 下载并安装
    wget https://cdn.spigotmc.org/PlaceholderAPI.jar
    cp PlaceholderAPI.jar /home/mc/instances/dl1/plugins/
    cp PlaceholderAPI.jar /home/mc/instances/dp1/plugins/
    cp PlaceholderAPI.jar /home/mc/instances/sc1/plugins/
    cp PlaceholderAPI.jar /home/mc/instances/sc2/plugins/
    cp PlaceholderAPI.jar /home/mc/instances/proxy/plugins/
    # 重启所有服务端

配置修改
==================================================
- 一般无需修改 config.yml
- 可根据分区设置 server_name 字段，便于变量区分
- 推荐所有分区都安装，保证变量同步

常见扩展
==================================================
.. csv-table:: PlaceholderAPI扩展列表
   :header: "扩展名称", "功能描述"
   :widths: 25, 75
   :delim: ,

   "`Player <https://api.extendedclip.com/expansions/player/>`_", "玩家相关变量，如名称、UUID、在线时间、游戏模式等"
   "`Server <https://api.extendedclip.com/expansions/server/>`_", "服务器相关变量，如在线人数、TPS、MOTD等"
   "`LuckPerms <https://api.extendedclip.com/expansions/luckperms/>`_", "权限插件变量，如玩家组、前缀、后缀等"
   "`Vault <https://api.extendedclip.com/expansions/vault/>`_", "经济/权限/物品变量，如余额、权限组等"
   "`PlayerPoints <https://api.extendedclip.com/expansions/playerpoints/>`_", "点数插件变量，显示玩家点数和排名"
   "`CheckItem <https://api.extendedclip.com/expansions/checkitem/>`_", "物品检查相关变量，如手持物品、背包物品数量"
   "`Essentials <https://api.extendedclip.com/expansions/essentials/>`_", "Essentials插件变量，如家、飞行状态、AFK等"

扩展安装与管理
==================================================
.. code-block:: bash

    # 方式1：游戏内命令安装扩展
    /papi ecloud download Player
    /papi ecloud download LuckPerms
    /papi ecloud download Vault
    /papi ecloud download Essentials

    # 方式2：手动下载扩展，放到 /plugins/PlaceholderAPI/expansions/ 目录

    # 安装后需重载变量
    /papi reload

变量解析与调试
==================================================
.. code-block:: bash

    # 解析变量，调试输出
    /papi parse mc__panda %player_name%
    # 输出：mc__panda

.. note:: 这是一个非常实用的 debug 工具，推荐用于变量测试。

变量搜索与文档
==================================================
- 官方变量列表：https://wiki.placeholderapi.com/users/placeholder-list/#standalone
- 各插件官方文档通常也有详细变量说明


权限配置
==================================================
这个插件，目前没有啥权限授予的， 不过还是创建一个虚拟组。 

.. code-block:: bash 

    /lp creategroup g_placeholderapi 0 g_placeholderapi
    /lp group default parent add g_placeholderapi


常见问题 QA
==================================================
:Q1:  安装后变量无效？  
:A1:  检查扩展是否已安装，执行 `/papi reload`，确认插件已加载。

:Q2:  某些变量解析为空？  
:A2:  对应插件未安装或未启用扩展，需补充相关插件和扩展。

:Q3:  Proxy 端需要安装吗？  
:A3:  推荐所有分区和 Proxy 都安装，保证变量同步。

:Q4:  如何批量安装扩展？  
:A4:  可用脚本或游戏内命令批量下载所有常用扩展。

优化建议
==================================================
- 所有分区统一安装 PlaceholderAPI，避免变量失效
- 定期更新扩展，保证兼容性
- 结合 LuckPerms、Vault、Essentials 等插件，发挥最大变量能力

.. note::
   PlaceholderAPI 是菜单、聊天、公告等功能的基础依赖，建议优先安装
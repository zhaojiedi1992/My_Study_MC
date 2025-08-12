==================================================
PlayerPoints 插件安装
==================================================
PlayerPoints 是一款常用的点券/积分插件，支持玩家点数管理、排行榜、兑换、奖励等功能，广泛用于商城、活动、签到等场景。

插件简介
==================================================
- 支持点券积分管理、排行榜、兑换、奖励等功能
- 可与 Vault、PlaceholderAPI 等插件联动
- 支持 MySQL 数据库后端，性能优异
- 免费开源，长期维护

.. image:: https://user-images.githubusercontent.com/13331708/120893363-7e6e2c80-c5f2-11eb-9e7b-6e9e2b1a4e7b.png
   :width: 400px
   :align: center

关键链接
==================================================
- SpigotMC: https://www.spigotmc.org/resources/playerpoints.80745/
- GitHub: https://github.com/Rosewood-Development/PlayerPoints
- 官方文档: https://github.com/Rosewood-Development/PlayerPoints/wiki

安装步骤
==================================================
1. 下载 PlayerPoints.jar，放到所有分区的 plugins 目录
2. 重启服务端，生成默认配置文件

.. code-block:: bash

    wget https://github.com/Blackixx/PlayerPoints/releases/latest/download/PlayerPoints.jar
    cp PlayerPoints.jar /home/mc/instances/dl1/plugins/
    cp PlayerPoints.jar /home/mc/instances/dp1/plugins/
    cp PlayerPoints.jar /home/mc/instances/sc1/plugins/
    cp PlayerPoints.jar /home/mc/instances/sc2/plugins/
    # 重启所有服务端

创建数据库
==================================================
.. code-block:: sql 

    CREATE DATABASE d_playerpoint CHARACTER SET utf8 COLLATE utf8_general_ci;

配置修改
==================================================
主要需修改数据库连接部分，其他配置可按需调整。

.. code-block:: diff

    # config.yml 数据库配置差异
    10c10
    <   type: SQLITE
    ---
    >   type: MYSQL
    13,16c13,16
    <   host: "localhost"
    <   port: 3306
    <   database: "playerpoints"
    <   username: "root"
    <   password: ""
    ---
    >   host: "127.0.0.1"
    >   port: 3306
    >   database: "d_playerpoint"
    >   username: "mc"
    >   password: "mc_panda_142857"

权限配置
==================================================
这里不建议给普通用户playerpoint的权限， 积分和金币不一样， 不支持转账这些操作。 
如果你有需要，可以参考官方文档适当给一些权限。



常见问题 QA
==================================================
:Q1: 点券数据不同步？  
:A1: 检查所有分区是否都安装 PlayerPoints，数据库配置是否一致。

:Q2: 玩家无法使用 pay/give 命令？  
:A2: 检查 LuckPerms 权限配置，确认已授权相关命令权限。

:Q3: 数据库连接失败？  
:A3: 检查数据库地址、用户名、密码、端口等配置，查看服务端日志。

:Q4: PlaceholderAPI 变量无效？  
:A4: 检查 PlaceholderAPI 是否安装并加载 PlayerPoints 扩展。

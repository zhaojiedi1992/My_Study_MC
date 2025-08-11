==================================================
WorldEdit基础插件的安装
==================================================
WorldEdit 是一款强大的 Minecraft 地图编辑工具，被称为「创世神」，允许玩家通过简单命令快速进行方块设计、地形改造和区域复制粘贴等操作。
FastAsyncWorldEdit (FAWE) 是 WorldEdit 的高性能分支，在速度和内存效率上有显著提升，同时完全兼容原版 WorldEdit API。

插件简介
==================================================
- 支持主流 Paper/Spigot/Bukkit 版本
- 提供高效的批量方块操作、区域编辑、刷图等功能
- FAWE 性能更优，适合大型地图和高并发环境
- 免费开源，长期维护

.. image:: https://intellectualsites.github.io/WorldEdit/images/logo.png
   :width: 300px
   :align: center

关键链接
==================================================
- SpigotMC: https://www.spigotmc.org/resources/fastasyncworldedit.13932
- GitHub: https://github.com/IntellectualSites/FastAsyncWorldEdit
- CI下载: https://ci.athion.net/job/FastAsyncWorldEdit/
- 官方文档: https://intellectualsites.gitbook.io/fastasyncworldedit/getting-started/installation

安装步骤
==================================================
1. 从 SpigotMC 或 CI 下载 FAWE 的 jar 包
2. 放到所有分区的 plugins 目录（如 /home/mc/instances/dl1/plugins/）
3. 重启所有服务端，确认 FAWE 正常加载

.. code-block:: bash

    wget https://ci.athion.net/job/FastAsyncWorldEdit/lastSuccessfulBuild/artifact/target/FastAsyncWorldEdit.jar
    cp FastAsyncWorldEdit.jar /home/mc/instances/dl1/plugins/
    cp FastAsyncWorldEdit.jar /home/mc/instances/dp1/plugins/
    cp FastAsyncWorldEdit.jar /home/mc/instances/sc1/plugins/
    cp FastAsyncWorldEdit.jar /home/mc/instances/sc2/plugins/
    # 重启所有服务端

.. warning::  
   FAWE 可以直接替代 WorldEdit，请勿同时安装两者，避免冲突。

配置说明
==================================================
- FAWE 默认配置即可满足大多数需求
- 可根据服务器性能和地图规模调整 config.yml，详见官方文档
- 支持自定义刷图、限制操作区域、性能优化等高级配置

权限配置
==================================================
这个插件，we这个插件， 一般只有owner才给自己的权限的。


常见问题 QA
==================================================
:Q1: 安装后命令无效？  
:A1: 检查服务端版本是否兼容，确认只安装了 FAWE 或 WorldEdit 其中之一。

:Q2: 批量操作卡顿或崩服？  
:A2: 优先使用 FAWE，调整 config.yml 的性能参数，合理分配服务器资源。

:Q3: 命令权限不足？  
:A3: 配置 LuckPerms 或其他权限插件，赋予玩家 worldedit.* 或 fawe.* 权限。

:Q4: 如何备份/恢复地图？  
:A4: 建议定期使用 FAWE/WorldEdit 的导出/导入功能，或直接备份 world 文件夹。

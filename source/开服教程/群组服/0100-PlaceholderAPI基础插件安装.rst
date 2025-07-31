==================================================
PlaceholderAPI基础插件安装
==================================================

服务端需要很多插件的， 插件和插件是有依赖关系，PlaceholderAPI是一个支持变量的插件， 非常重要，我们需要前置安装一下。

- `placeholderapi <https://www.spigotmc.org/resources/placeholderapi.6245/>`_ 
- `帮助文档 <https://wiki.placeholderapi.com/users/commands/>`_ 

介绍
==================================================
PlaceholderAPI 是 Spigot 服务器的插件，它允许服务器所有者以统一的格式显示来自各种插件的信息。 对特定插件的支持由插件本身或通过扩展提供。 
扩展可以通过 PAPI 扩展云在ecloud下载。 目前有超过 230 多个扩展支持各种插件，例如 Essentials、Factions、LuckPerms 和 Vault。
安装到paper端，我们先安装到主城区域。安装比较简单，直接将jar包放到plugins重启服务器即可。



安装插件
================================================== 
proxy + 分区都要安装， 放置到plugin目录即可， 然后重启。 
Placeholder本身的config.yml文件没有啥可以修改的。 这个插件提供变量能力支持，具体的变量需要其他的下载。我们通过ecloud进行下载。

配置修改
================================================== 

.. code-block:: bash 

    # 修改下server_name 字段， 后面获取一些场景要使用这个placehold
    # 生存一区为sc1 
    # 生产2区位sc2
    # 登录1区位dl1
    # proxy 为proxy 
    # 地皮一区为dp1

常见扩展
==================================================

.. csv-table:: PlaceholderAPI扩展列表
   :header: "扩展名称", "功能描述"
   :widths: 25, 75
   :delim: ,

   "`Player <https://api.extendedclip.com/expansions/player/>`_", "提供玩家相关的占位符，如名称、UUID、在线时间、游戏模式等"
   "`Server <https://api.extendedclip.com/expansions/server/>`_", "提供服务器相关的占位符，如在线玩家数、TPS、服务器名称、MOTD等"
   "`LuckPerms <https://api.extendedclip.com/expansions/luckperms/>`_", "提供基于LuckPerms权限插件的占位符，如玩家组、权限节点、前缀后缀等"
   "`Vault <https://api.extendedclip.com/expansions/vault/>`_", "提供基于Vault经济/权限/物品插件的占位符，如玩家余额、权限组等"
   "`PlayerPoints <https://api.extendedclip.com/expansions/playerpoints/>`_", "提供PlayerPoints插件的占位符，显示玩家点数和排名等"
   "`CheckItem <https://api.extendedclip.com/expansions/checkitem/>`_", "提供物品检查相关的占位符，如玩家手持物品、背包物品数量等"
   "`Essentials <https://api.extendedclip.com/expansions/essentials/>`_", "提供Essentials插件的占位符，如玩家家的位置、飞行状态、AFK状态等"

安装扩展
================================================== 

.. code-block:: bash 

    # 方式1: 终端里面的安装方式，如果直接下载放到extension 那也是一样的。 
    /papi ecloud download Player

    # 方式2： 通过ecloud https://api.extendedclip.com/all/ 搜索，然后进行下载，放到/plugins/PlaceholderAPI/expansions/下

    # 重载变量,上面的2个方式都是仅仅下载，生效不生效还是需要执行reload命令的。
    /papi reload 


解析变量
==================================================  
安装好了之后，可以在游戏内通过

.. code-block:: bash 

    /papi parse mc__panda %player_name%
    # 会输出mc__panda 

.. note:: 这是一个非常好的一个debug的工具。


搜索变量
==================================================  
这个地方是placeholder 和其他的插件注册的变量， 可以参考一下， 插件维度，一般在插件的具体官方文档里面也有placeholder api的详细介绍。 
`placeholder api list <https://wiki.placeholderapi.com/users/placeholder-list/#standalone>`_ 



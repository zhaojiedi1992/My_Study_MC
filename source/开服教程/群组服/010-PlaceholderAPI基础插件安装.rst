==================================================
PlaceholderAPI基础插件安装
==================================================

服务端需要很多插件的， 插件和插件是有依赖关系，PlaceholderAPI是一个支持变量的插件， 非常重要，我们需要前置安装一下。

`placeholderapi <https://www.spigotmc.org/resources/placeholderapi.6245/>`_ 
`帮助文档 <https://wiki.placeholderapi.com/users/commands/>`_ 

介绍
==================================================

PlaceholderAPI 是 Spigot 服务器的插件，它允许服务器所有者以统一的格式显示来自各种插件的信息。 对特定插件的支持由插件本身或通过扩展提供。 
扩展可以通过 PAPI 扩展云在ecloud下载。 目前有超过 230 多个扩展支持各种插件，例如 Essentials、Factions、LuckPerms 和 Vault。
安装到paper端，我们先安装到主城区域。安装比较简单，直接将jar包放到plugins重启服务器即可。

Placeholder本身的config.yml文件没有啥可以修改的。 这个插件提供变量能力支持，具体的变量需要其他的下载。我们通过ecloud进行下载。

常见插件

- player: https://api.extendedclip.com/expansions/player/
- server: https://api.extendedclip.com/expansions/server/
- luckperm: https://api.extendedclip.com/expansions/luckperms/
- vault: https://api.extendedclip.com/expansions/vault/
- playerpoints: https://api.extendedclip.com/expansions/playerpoints/
- checkItem: https://api.extendedclip.com/expansions/checkitem/
- essentials: https://api.extendedclip.com/expansions/essentials/

下载好插件，放到/home/mc/instances/zc/plugins/PlaceholderAPI/expansions 目录即可。

下载完毕，建议将分区进行一次重启操作，或者执行一次papi reload。

安装
================================================== 
proxy + 分区都要安装， 放置到plugin目录即可， 然后重启。 


安装api 
================================================== 

.. code-block:: bash 

    # 终端里面的安装方式，如果直接下载放到extension 那也是一样的。 
    /papi ecloud download Player


解析变量
==================================================  
安装好了之后，可以在游戏内通过

.. code-block:: bash 

    /papi parse mc__panda %player_name%
    # 会输出mc__panda 
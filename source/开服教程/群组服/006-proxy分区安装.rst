==================================================
proxy分区安装.rst
==================================================


proxy安装
==================================================


.. code-block:: bash 

    # 从paper官方地址进行下载，复制下最新的url即可。 https://papermc.io/downloads/velocity
    wget https://fill-data.papermc.io/v1/objects/f82780ce33035ebe3d6ea7981f0e6e8a3e41a64f2080ef5c0f1266fada03cbee/velocity-3.4.0-SNAPSHOT-522.jar
    # 创建proxy目录
    mkdir /home/mc/instances/proxy
    # 复制jar
    cp velocity-3.4.0-SNAPSHOT-522.jar /home/mc/instances/proxy/proxy.jar
    # 进入目录，启动，获取默认配置
    cd /home/mc/instances/proxy/
    ls
    # 启动一次
    java -jar proxy.jar


修改配置文件
==================================================

.. code-block:: bash 

    # 备份默认的文件。 养成好习惯， 后面的备份要带日期格式化。
    cp velocity.toml velocity.toml.default
    
    root@mc:/home/mc/instances/proxy# diff velocity.toml velocity.toml.default
    16c16
    < online-mode = false
    ---
    > online-mode = true
    37c37
    < player-info-forwarding-mode = "modern"
    ---
    > player-info-forwarding-mode = "NONE"
    80,83c80,82
    < login = "127.0.0.1:10000"
    < dp1 = "127.0.0.1:20001"
    < sc1 = "127.0.0.1:30001"
    < sc2 = "127.0.0.1:30002"
    ---
    > lobby = "127.0.0.1:30066"
    > factions = "127.0.0.1:30067"
    > minigames = "127.0.0.1:30068"
    87c86
    <     "login"
    ---
    >     "lobby"
    91a91,99
    > "lobby.example.com" = [
    >     "lobby"
    > ]
    > "factions.example.com" = [
    >     "factions"
    > ]
    > "minigames.example.com" = [
    >     "minigames"
    > ]
    117c125
    < tcp-fast-open = true
    ---
    > tcp-fast-open = false



配置联动
==================================================

`refer <https://docs.papermc.io/velocity/player-information-forwarding/>`_ 


.. code-block:: bash 

    # 设置proxy->子服务器的认证信息
    echo "panda_mc_142857" >forwarding.secret

    cd /home/mc/instances/login 
    cp config/paper-global.yml config/paper-global.yml.default

    # root@mc:/home/mc/instances/login# diff config/paper-global.yml config/paper-global.yml.default
    113c113
    <     online-mode: false
    ---
    >     online-mode: true
    116,118c116,118
    <     enabled: true
    <     online-mode: false
    <     secret: panda_mc_142857
    ---
    >     enabled: false
    >     online-mode: true
    >     secret: ''

    # 同样要修改下对应的sc1, sc2 ,dp1 的， 

    # 重启所有的服务器
    systemctl restart mc_proxy mc_dp1 mc_login mc_sc1 mc_sc2 
    # 这里定义一个别名到/etc/profile文件中， 后面重启所有服务，方便一些。
    # 需要将下面alias的文件行补充到/etc/profile文件中。 
    root@mc:/home/mc/instances/dp1# tail -n 2 /etc/profile
    alias mc_restart="systemctl restart mc_proxy mc_dp1 mc_login mc_sc1 mc_sc2"
    # 让文件生效
    source /etc/profile 


验证效果
==================================================

通过执行/server sc2 就可以从login分区切换到sc2(生存2区了)

.. image:: ./imgs/切换分区.jpg


    
常见问题QA
==================================================

- Q1：  java.lang.IllegalStateException: Backend server is online-mode!
- A1:  你的后端配置online-mode是true的，需要修改server.properties里面的online-mode为false 


- Q2: lost connection: Unable to verify player details
- A2: proxy 和分区的secret不正确，核对vel的forwarding.secret 文件和，paper的config/paper-global文件的key是否一致。
  
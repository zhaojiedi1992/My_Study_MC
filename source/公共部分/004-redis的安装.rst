.. _redis安装:


.. note:: 这里是开服需要的， 如果只是普通游戏玩家， 不用看这个文档。 


==================================================
redis的安装
==================================================
开服的时候有些插件是需要使用redis来进行数据同步的， 需要安装redis。 可以先不做安装，需要的时候在安装即可。 




centos上安装 redis
==================================================

.. code-block:: bash 

    # 安装数据库软件
    yum search redis-server
    yum install redis-server 
    vim /etc/redis/redis.conf  
    # 找到这一行的requirepass ，
    requirepass mc_panda_14285
    # 开启机器
    systemctl enable redis 
    systemctl start redis 




windows上安装 redis server 
==================================================
从这个地方下载安装即可。

`redis download <https://github.com/tporadowski/redis/releases>`_


debian上安装 redis
==================================================

.. code-block:: bash 

    # 安装数据库软件
    apt search redis-server
    apt install redis-server 
    vim /etc/redis/redis.conf  
    # 找到这一行的requirepass ，
    requirepass mc_panda_14285
    # 开启机器
    systemctl enable redis 
    systemctl start redis 

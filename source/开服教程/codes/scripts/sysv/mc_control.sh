#!/bin/bash
# chkconfig: 2345 20 80
. /etc/init.d/functions
name=$(echo "$(basename $0)" |sed 's@mc_@@g')
echo "mc=$name"

host=127.0.0.1
rcon_code=panda142857
mcrcon_cmd="/home/mc/mcrcon/mcrcon"
java_cmd="/usr/bin/java"
mc_instance_dir="/home/mc/instances"
log_file=$mc_instance_dir/$name/nohup.log

jar_name=" $name.jar"

# 这里配置要根据你的规划端口来， 
#    "代理端口", "proxy", "25565", "无"
#    "主城区/登录区", "login", "10000", "11000"
#    "地皮1区", "dp1", "20001", "21001"
#    "生存1区", "sc1", "30001", "31001"
#    "生存2区", "sc2", "30002", "31002"
get_rcon_port(){
	local area=$1
	case $area in 
		proxy)  echo 0;;
		login) echo 11000;;
		dp1)  echo 21001;;
		sc1)  echo 31001;;
		sc2)  echo 31002;;
		*)   echo 0;;
	esac
}
get_jvm(){
	local area=$1
	case $area in 
		bc)  echo " -Xms1G -Xmx1G ";;
		login)  echo " -Xms1G -Xmx1G ";;
		dp1)  echo " -Xms1G -Xmx1G ";;
		sc1)  echo " -Xms2G -Xmx2G ";;
		sc2)  echo " -Xms2G -Xmx2G ";;
		*)  echo " -Xms1G -Xmx1G ";;
	esac
}


base_dir=${mc_instance_dir}/$name
mcrcon_pre="${mcrcon_cmd} -H $host -p ${rcon_code} -P $(get_rcon_port $name)  "
mc_exist(){
	ps aux |grep "${jar_name}" |grep -v grep | >/dev/null
}

status(){
	mc_exist
	if [ $? -eq 0 ]; then
		echo "$name running"
	else
		echo "$name stopped"
	fi
}
start() {
	cd $base_dir
	echo "$base_dir"
	if [ "X$name" == "Xs5" ] ; then
		cd server
	fi
	nohup ${java_cmd} $(get_jvm $name) -jar $name.jar --nogui >>${log_file} 2>>${log_file} &
}

stop() {
	cd $base_dir

	mc_exist 
	if [ $? -ne 0 ]; then
		return
	fi
	if [ X$name == X"bc" ] ; then 
		stop_kill
		return 
	fi
	if [ X$name == X"wtf" ] ; then 
		stop_kill
		return 
	fi
	conn "bc 分区$name准备重启5s..." 
	sleep 5
	conn "save-all"
	sleep 5
	conn "stop"
	sleep 5
	for i in $(seq 1 10); do 
		mc_exist 
		if [ $? -ne 0 ] ; then 
			return 
		else
			sleep 1
		fi
	done
	stop_kill
}
stop_kill(){
	cd $base_dir 
	ps aux |grep "${jar_name}" |grep -v grep |awk '{print $2}' |while read pid ; do
		kill -9 $pid
	done
}
conn() {
	cd $base_dir
	cmd="$1"
	$mcrcon_pre  "$cmd"
}

case "$1" in 
    conn)
       cmd="$2"
       conn "$cmd"
       ;;
    start)
       start
       ;;
    stop)
       stop
       ;;
    restart)
       stop
       start
       ;;
    status)
	    status
       ;;
    *)
       echo "Usage: $0 {start|stop|status|restart|conn}"
esac

exit 0 
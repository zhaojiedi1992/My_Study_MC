cmd="$1"
cat server.txt |while read server ; do
	echo "server=$server"
	/etc/init.d/mc_${server} conn "$cmd"
	sleep 1
done

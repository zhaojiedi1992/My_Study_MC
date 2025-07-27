base_dir="/home/mc/instances"
server_list="dl1 dp1 sc1 sc2"

cd "$(dirname "$0")"
for server in $server_list; do
  echo "$server"
  cp config.yml $base_dir/$server/plugins/DeluxeMenus/
  cp -r gui_menus $base_dir/$server/plugins/DeluxeMenus/
done

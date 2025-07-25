#!/bin/bash
mysql_pre="mysql -ppanda142857 PlayerDataSQL -e"
cmd_unlock="update PlayerDataSQL set locked=0;"
${mysql_pre} "${cmd_unlock}"

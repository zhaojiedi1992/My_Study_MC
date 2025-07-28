#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
COMMAND_FILE="$SCRIPT_DIR/command.list.txt"
SERVER_FILE="$SCRIPT_DIR/server.txt"

# 处理命令函数
process_command() {
    local cmd="$1"
    # 去除前导空格
    cmd=$(echo "$cmd" | sed 's/^[[:space:]]*//')
    # 替换/lp开头的为lp
    if [[ "$cmd" == /lp* ]]; then
        cmd="lp${cmd:3}"
    fi
    echo "$cmd"
}

# 检查server.txt文件是否存在
if [ ! -f "$SERVER_FILE" ]; then
    echo "错误: 服务器列表文件 $SERVER_FILE 不存在"
    exit 1
fi

# 如果有参数直接处理
if [ $# -gt 0 ]; then
    cmd=$(process_command "$1")
    while read -r server || [ -n "$server" ]; do
        # 跳过空行和注释行(以#开头的行)
        if [[ -z "$server" || "$server" =~ ^# ]]; then
            continue
        fi
        echo "server=$server"
        /etc/init.d/mc_"$server" conn "$cmd"
        sleep 1
    done < "$SERVER_FILE"
else
    # 检查命令文件是否存在
    if [ ! -f "$COMMAND_FILE" ]; then
        echo "错误: 命令文件 $COMMAND_FILE 不存在"
        exit 1
    fi
    
    # 逐行读取命令文件并执行
    while read -r cmd || [ -n "$cmd" ]; do
        # 跳过空行和注释行
        if [[ -z "$cmd" || "$cmd" =~ ^# ]]; then
            continue
        fi
        
        cmd=$(process_command "$cmd")
        
        # 对每个服务器执行当前命令
        while read -r server || [ -n "$server" ]; do
            # 跳过空行和注释行
            if [[ -z "$server" || "$server" =~ ^# ]]; then
                continue
            fi
            echo "server=$server 执行命令: $cmd"
            /etc/init.d/mc_"$server" conn "$cmd"
            sleep 1
        done < "$SERVER_FILE"
        
    done < "$COMMAND_FILE"
fi

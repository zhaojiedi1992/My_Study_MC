#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
COMMAND_FILE="$SCRIPT_DIR/command.list.txt"

# 处理命令函数
process_command() {
    local cmd="$1"
    # 去除前导空格
    cmd=$(echo "$cmd" | sed 's/^[[:space:]]*//')
    # 替换/lp开头的为lp
    if [[ "$cmd" == /lp* ]]; then
        cmd="lp${cmd:3}"
    fi
    # 执行命令
    echo "start: $cmd" 
    /etc/init.d/mc_dl1 conn "$cmd"
}

# 如果有参数直接执行
if [ $# -gt 0 ]; then
    process_command "$1"
else
    # 检查命令文件是否存在
    if [ ! -f "$COMMAND_FILE" ]; then
        echo "错误: 命令文件 $COMMAND_FILE 不存在"
        exit 1
    fi
    
    # 逐行读取文件并执行
    while IFS= read -r line || [ -n "$line" ]; do
        # 跳过空行
        if [ -z "$line" ]; then
            continue
        fi
	# 等待1s，避免错误
	sleep 0.5
        process_command "$line"
    done < "$COMMAND_FILE"
fi

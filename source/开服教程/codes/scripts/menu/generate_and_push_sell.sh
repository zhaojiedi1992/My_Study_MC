#!/bin/bash
cd "$(dirname "$0")"

# 定义文件路径
HEADER="sell_header_template.yml"
ITEM_TEMPLATE="sell_item_template.yml"
CSV="sell.csv"
OUTPUT="gui_menus/sell.yml"
TEMP_FILE=$(mktemp)  # 临时文件用于中间处理

# 检查模板文件是否存在
for file in "$HEADER" "$ITEM_TEMPLATE" "$CSV"; do
    if [ ! -f "$file" ]; then
        echo "错误：未找到模板文件 $file"
        exit 1
    fi
done

# 检查bc工具是否安装（用于小数计算）
if ! command -v bc &> /dev/null; then
    echo "错误：需要安装bc工具，请执行：sudo apt install bc"
    exit 1
fi

# 创建输出目录
mkdir -p "$(dirname "$OUTPUT")"

# 写入头部配置
cat "$HEADER" > "$OUTPUT"

# 读取CSV数据并处理
tail -n +2 "$CSV" | while IFS=',' read -r item_name material display_name price_per_unit slot; do
    echo "处理物品: $item_name"

    # 计算衍生变量
    item_name_lower=$(echo "$item_name" | tr 'A-Z' 'a-z')
    price_per_stack=$(echo "scale=2; $price_per_unit * 64" | bc)
    
    # 关键修复：转义特殊字符（&、$、/等）
    # 对display_name中的&进行转义（替换为\&）
    display_name_escaped=$(echo "$display_name" | sed 's/&/\\&/g')
    # 其他变量也做转义处理，确保安全
    item_name_escaped=$(echo "$item_name" | sed 's/&/\\&/g; s/\$/\\$/g')
    material_escaped=$(echo "$material" | sed 's/&/\\&/g; s/\$/\\$/g')
    
    # 先将模板复制到临时文件
    cp "$ITEM_TEMPLATE" "$TEMP_FILE"
    
    # 按顺序替换变量（先替换含特殊字符的）
    sed -i.bak "s/{{display_name}}/$display_name_escaped/g" "$TEMP_FILE"
    sed -i.bak "s/{{item_name}}/$item_name_escaped/g" "$TEMP_FILE"
    sed -i.bak "s/{{item_name_lower}}/$item_name_lower/g" "$TEMP_FILE"
    sed -i.bak "s/{{material}}/$material_escaped/g" "$TEMP_FILE"
    sed -i.bak "s/{{price_per_unit}}/$price_per_unit/g" "$TEMP_FILE"
    sed -i.bak "s/{{price_per_stack}}/$price_per_stack/g" "$TEMP_FILE"
    sed -i.bak "s/{{slot}}/$slot/g" "$TEMP_FILE"
    rm -f "${TEMP_FILE}.bak"  # 删除备份文件
    
    # 检查是否有未替换的变量
    if grep -q '{{' "$TEMP_FILE"; then
        echo "警告：物品 $item_name 存在未替换的变量："
        grep '{{' "$TEMP_FILE"
    fi
    
    # 将处理后的内容追加到输出文件
    cat "$TEMP_FILE" >> "$OUTPUT"
    echo "" >> "$OUTPUT"  # 物品间空行分隔
done

# 清理临时文件
rm -f "$TEMP_FILE"

echo "配置文件生成成功：$OUTPUT"

bash push_to_dir.sh

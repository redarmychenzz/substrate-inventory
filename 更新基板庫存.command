#!/bin/bash
cd "$(dirname "$0")"

echo "==============================="
echo "  基板庫存網頁更新工具"
echo "==============================="
echo ""

# 檢查 Python 和 requests
if ! command -v python3 &> /dev/null; then
    echo "✗ 找不到 python3，請先安裝 Python"
    read -p "按 Enter 關閉..."
    exit 1
fi

python3 -c "import requests" 2>/dev/null || {
    echo "正在安裝必要套件..."
    pip3 install requests --quiet
}

echo "正在從 Google Sheets 讀取最新資料..."
echo ""
python3 inject_data.py

echo ""
if [ -f "substrate_inventory_static.html" ]; then
    echo "==============================="
    echo "✓ 完成！請將下方檔案上傳到 SharePoint："
    echo ""
    echo "  $(pwd)/substrate_inventory_static.html"
    echo ""
    # 自動在 Finder 中顯示該檔案
    open -R "substrate_inventory_static.html"
    echo "（已在 Finder 中開啟檔案位置）"
    echo "==============================="
else
    echo "✗ 輸出檔案不存在，請確認錯誤訊息"
fi

echo ""
read -p "按 Enter 關閉視窗..."

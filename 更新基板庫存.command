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

if [ $? -eq 0 ]; then
    echo ""
    echo "正在上傳到 GitHub..."
    git add index.html
    git commit -m "更新庫存資料 $(date '+%Y/%m/%d %H:%M')"
    git push
    if [ $? -eq 0 ]; then
        echo "✓ 已上傳，網頁約 1 分鐘後更新"
        echo "  網址：https://redarmychenzz.github.io/substrate-inventory/"
    else
        echo "✗ 上傳失敗，請確認網路連線"
    fi
else
    echo "✗ 輸出檔案不存在，請確認錯誤訊息"
fi

echo ""
read -p "按 Enter 關閉視窗..."

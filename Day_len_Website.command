#!/bin/bash

# Navigate to the project directory
cd "/Users/danghong/Documents/The1ight/Notes Maker"

# Kích hoạt môi trường ảo
source venv/bin/activate

# Chạy script tự động push
python3 auto_push.py

# Đợi người dùng đọc thông báo
read -p "Nhấn Enter để thoát..."

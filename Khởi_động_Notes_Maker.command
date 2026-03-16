#!/bin/bash
cd "/Users/danghong/Documents/The1ight/Notes Maker"
source venv/bin/activate

echo "======================================================="
echo "🚀 Đang khởi động phần mềm Notes Maker..."
echo "🕒 Vui lòng đợi khoảng 3 giây..."
echo "⚠️ LƯU Ý: KHÔNG ĐÓNG cửa sổ màu đen này trong lúc dùng web."
echo "🔗 Dành cho trường hợp khẩn cấp nếu mất trang: Bạn cứ mở Chrome/Safari, gõ: http://localhost:8501"
echo "======================================================="

# 1. Dọn dẹp tàn dư (Nếu lần trước bạn đóng web không đúng cách làm kẹt mạng)
lsof -ti:8501 | xargs kill -9 2>/dev/null

# 2. Buộc macOS tự động mở trình duyệt sau 3 giây (khi server đã kịp chạy)
(sleep 3 && open http://localhost:8501) &

# 3. Chạy app ở chế độ Headless và Ép buộc chạy đúng cổng 8501
streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

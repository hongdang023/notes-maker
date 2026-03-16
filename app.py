import streamlit as st
import yt_dlp
from google import genai
from google.genai import types
import os
import time
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from daymai_cookie_scraper import extract_daymai_video_with_cookie

# Load biến môi trường
load_dotenv()

# Cấu hình API key
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# Thiết lập thư mục lưu trữ tạm thời và lịch sử
TEMP_DIR = "temp_audio"
HISTORY_FILE = "history.json"
for directory in [TEMP_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Khởi tạo history.json nếu chưa có
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_to_history(zoom_url, notes_content):
    history = load_history()
    new_entry = {
        "id": str(int(time.time())),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": zoom_url,
        "content": notes_content
    }
    history.insert(0, new_entry) # Lưu mới nhất lên đầu
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

# --- Các hàm xử lý cốt lõi ---

def download_audio_from_zoom(url, passcode=""):
    """Tải audio từ link Zoom (hoặc link video bất kỳ hỗ trợ yt-dlp)"""
    # Xoá các file cũ trong thư mục tạm
    for file in os.listdir(TEMP_DIR):
        try:
            os.remove(os.path.join(TEMP_DIR, file))
        except:
            pass
            
    # Cấu hình yt-dlp để chỉ tải audio tốt nhất
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{TEMP_DIR}/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'no_warnings': True,
        'ffmpeg_location': '/opt/homebrew/bin/ffmpeg' if os.path.exists('/opt/homebrew/bin/ffmpeg') else '/usr/local/bin/ffmpeg',
    }
    
    # Nếu có mật khẩu
    if passcode:
        ydl_opts['video_password'] = passcode
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Find the downloaded file
            for file in os.listdir(TEMP_DIR):
                if file.endswith('.mp3'):
                    return os.path.join(TEMP_DIR, file)
            # Dành cho trường hợp máy chưa cài FFmpeg để convert sang mp3
            for file in os.listdir(TEMP_DIR):
                if file.endswith('.m4a') or file.endswith('.webm') or file.endswith('.mp4'):
                    return os.path.join(TEMP_DIR, file)
            return None
    except Exception as e:
        st.error(f"Lỗi khi tải video: {e}")
        return None

def process_with_gemini(audio_path):
    """Đẩy file lên Gemini và yêu cầu tạo Study Notes theo Format chuẩn"""
    try:
        # Upload file lên Gemini
        st.info("Đang tải file âm thanh lên não bộ AI Gemini...")
        audio_file = client.files.upload(file=audio_path)
        
        # Chờ file được xử lý trên server Google
        st.info("AI đang nghe và xử lý âm thanh (có thể mất 1-3 phút tùy độ dài video)...")
        while True:
            file_info = client.files.get(name=audio_file.name)
            if file_info.state == "PROCESSING":
                time.sleep(5)
            elif file_info.state == "FAILED":
                st.error("Google AI bị lỗi khi đọc file âm thanh này.")
                return None
            else:
                break
            
        # Prompt chuẩn đã được thiết kế kỹ để tránh bịa chuyện
        prompt = """
Bạn là một trợ lý học tập xuất sắc. Nhiệm vụ của bạn là nghe đoạn Audio của buổi học/buổi họp này và viết ra một bản Study Notes hoàn chỉnh.

LƯU Ý CỰC KỲ QUAN TRỌNG:
1. KHÔNG ĐƯỢC BỊA CHUYỆN. Chỉ sử dụng thông tin CÓ TRONG AUDIO. Nếu không nhắc đến, cứ bỏ qua.
2. Viết bằng tiếng Việt dễ hiểu, chuyên nghiệp.

ĐỊNH DẠNG BẮT BUỘC THEO CẤU TRÚC SAU:

# 📝 [Tạo một Tiêu đề phù hợp cho buổi học]

## 🎯 1. Tóm tắt chung (Executive Summary)
[Viết 1 đoạn tóm tắt ngắn từ 3-5 câu về mục tiêu và nội dung chính của cả buổi].

## 💡 2. Các điểm nhấn quan trọng (Key Takeaways)
[Liệt kê gạch đầu dòng 3-5 bài học cốt lõi hoặc kết luận quan trọng nhất].
- 
- 
- 

## 📖 3. Nội dung chi tiết
[Hãy chia nội dung file âm thanh thành các phần/chủ đề lớn được thảo luận. Với mỗi chủ đề, tóm tắt chi tiết luận điểm, ví dụ được nhắc đến].
### [Tên Chủ đề 1]
- ...
### [Tên Chủ đề 2]
- ...

## 🚀 4. Hành động cần làm (Action Items)
[Liệt kê các dặn dò, bài tập, kế hoạch hành động tiếp theo được nhắc đến ở cuối buổi] (Nếu không có, hãy ghi: "Không có nghiệp vụ bắt buộc nào được ghi nhận").
"""
        st.info("AI đang viết tóm tắt Study Notes... Sắp xong rồi!")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                audio_file,
                prompt
            ],
            config=types.GenerateContentConfig(
                 temperature=0.2, # Giảm sáng tạo để tăng độ chính xác
            )
        )
        
        # Dọn dẹp file trên server AI
        try:
            client.files.delete(name=audio_file.name)
        except:
            pass
            
        return response.text
        
    except Exception as e:
        st.error(f"Lỗi phần AI Gemini: {e}")
        return None

# --- Giao diện Web ---

st.set_page_config(page_title="Notes Maker", page_icon="📝", layout="wide")

st.title("📝 Zoom to PDF Study Notes")

if not client:
    st.error("Chưa có API Key. Xin hãy kiểm tra lại file .env")
    st.stop()

# Layout Tabs
tab_create, tab_history = st.tabs(["🚀 Tạo Notes Mới", "📚 Lịch sử Notes"])

with tab_create:
    st.markdown("Chỉ cần dán link Zoom (hoặc Video), AI sẽ tự học và làm báo cáo chi tiết cho bạn!")
    
    # Check if link is Daymai to show extra field
    zoom_url = st.text_input("🔗 Dán Link Video / Zoom vào đây:")
    
    is_daymai = "daymai" in zoom_url.lower() if zoom_url else False
    
    daymai_cookie = ""
    if is_daymai:
        st.info("💡 **Phát hiện link Daymai:** Hệ thống cần mượn 'phiên đăng nhập' của bạn để tải video.")
        with st.expander("🔑 Hướng dẫn lấy Mã Phiên (Cookie) - Mất 5 giây"):
            st.markdown("""
            1. Bạn mở trình duyệt Chrome, trang mà bạn đang xem video đó.
            2. Nhấn phím **F12** (hoặc chuột phải chọn **Kiểm tra/Inspect**).
            3. Chọn tab **Console** ở phía trên.
            4. Dán dòng lệnh này vào và nhấn Enter: `copy(document.cookie)`
            5. Quay lại đây và **Dán (Ctrl+V)** vào ô dưới nhé!
            """)
        daymai_cookie = st.text_area("🎫 Dán Mã Phiên (Cookie) của bạn vào đây:", help="Mã này bắt đầu bằng 'csrftoken=...' hoặc tương tự")
        
    col1, col2 = st.columns([1, 1])
    with col1:
        passcode = st.text_input("🔑 Passcode (nếu link Zoom có pass):", type="password")
    with col2:
        pass

    if "audio_path" not in st.session_state:
        st.session_state.audio_path = None

    if st.button("🚀 BƯỚC 1: Tải Audio từ Video", type="primary"):
        if not zoom_url:
            st.warning("Vui lòng dán Link Video!")
        elif is_daymai and not daymai_cookie:
            st.error("Vui lòng dán Cookie để tiếp tục với link Daymai!")
        else:
            with st.spinner("Đang tải âm thanh..."):
                final_video_url = zoom_url
                if is_daymai:
                    st.info("Đang giải mã luồng video Daymai...")
                    extracted_url = extract_daymai_video_with_cookie(zoom_url, daymai_cookie)
                    if extracted_url:
                        final_video_url = extracted_url
                    else:
                        st.error("❌ Không thể giải mã link Daymai. Có thể Cookie đã hết hạn hoặc sai.")
                        st.stop()
                
                audio_path = download_audio_from_zoom(final_video_url, passcode)
                if audio_path:
                    st.session_state.audio_path = audio_path
                    st.success(f"✅ Đã tải thành công file âm thanh.")
                else:
                    st.error("❌ Không lấy được âm thanh. Hãy kiểm tra lại link hoặc Passcode.")

    if st.session_state.audio_path:
        st.markdown("---")
        st.subheader("BƯỚC 2: Chọn Cách Tóm Tắt")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("👉 CÁCH 1: Dùng NotebookLM (Khuyên dùng, Miễn phí)")
            st.markdown("Tải file âm thanh về máy và Upload trực tiếp vào [NotebookLM](https://notebooklm.google.com/) để chat và tóm tắt mà không lo bị giới hạn API Quota của Google.")
            with open(st.session_state.audio_path, "rb") as f:
                st.download_button(
                    label="💾 Tải Audio (.mp3) về máy",
                    data=f,
                    file_name=os.path.basename(st.session_state.audio_path),
                    mime="audio/mpeg"
                )
            
            st.markdown("👇 **Copy Prompt dưới đây dán vào NotebookLM:**")
            prompt_text = (
                "Nhiệm vụ của bạn là nghe đoạn Audio của buổi học này và viết ra một bản Study Notes hoàn chỉnh theo yêu cầu sau:\n\n"
                "LƯU Ý CỰC KỲ QUAN TRỌNG:\n"
                "1. KHÔNG ĐƯỢC BỊA CHUYỆN. Chỉ sử dụng thông tin CÓ TRONG AUDIO. Nếu không nhắc đến, cứ bỏ qua.\n"
                "2. Viết bằng tiếng Việt dễ hiểu, chuyên nghiệp.\n\n"
                "ĐỊNH DẠNG BẮT BUỘC THEO CẤU TRÚC SAU (Trả về Markdown chuẩn):\n"
                "# 📝 [Tạo một Tiêu đề phù hợp cho buổi học]\n"
                "## 🎯 1. Tóm tắt chung (Executive Summary)\n"
                "[1 đoạn tóm tắt ngắn từ 3-5 câu về mục tiêu và nội dung chính]\n"
                "## 💡 2. Các điểm nhấn quan trọng (Key Takeaways)\n"
                "[3-5 bullet points bài học cốt lõi]\n"
                "## 📖 3. Nội dung chi tiết\n"
                "[Chia nội dung thành các chủ đề lớn. Tương ứng mỗi chủ đề là luận điểm và ví dụ]\n"
                "## 🚀 4. Hành động cần làm (Action Items)\n"
                "[Các bài tập, dặn dò cuối buổi. Nếu không có ghi: \"Không có\"]"
            )
            st.code(prompt_text, language="markdown")
                
        with col2:
            st.info("👉 CÁCH 2: Dùng Gemini API (Tự động)")
            st.markdown("Hệ thống sẽ tự động gọi API Gemini để phân tích. (Có thể gặp lỗi 429 nếu tài khoản của bạn hết hạn mức gọi API).")
            if st.button("🤖 Chạy AI Gemini Tự động"):
                with st.spinner("AI đang xử lý..."):
                    notes = process_with_gemini(st.session_state.audio_path)
                    if notes:
                        st.success("🎉 Hoàn thành!")
                        st.session_state['current_notes'] = notes
                        save_to_history(zoom_url, notes)

    # Khối hiển thị và chỉnh sửa Note
    if 'current_notes' in st.session_state:
        st.divider()
        st.subheader("Bản nháp Notes (Bạn có thể tinh chỉnh lại text ở ô dưới nếu muốn)")
        
        # Cho phép user chỉnh sửa bản Markdown
        edited_notes = st.text_area("Chỉnh sửa nội dung Markdown", value=st.session_state['current_notes'], height=400)
        
        st.divider()
        st.subheader("Bản xem trước (Preview) & Xuất PDF")
        
        # Render thử bản xem trước thật đẹp
        st.markdown(edited_notes)
        
        # Hướng dẫn xuất PDF
        st.info("💡 **CÁCH LƯU FILE PDF CHUẨN VÀ ĐẸP NHẤT:**\n1. Bạn nhấn tổ hợp phím **`Cmd + P`** trên bàn phím Mac của bạn.\n2. Ở mục **Destination** (Máy in/Printer), bạn chọn **`Save as PDF`**.\n3. Nhấn **Save**! Trình duyệt sẽ in đoạn Preview này ra PDF cực đẹp giữ nguyên hoàn toàn Format!")

with tab_history:
    st.markdown("Xem lại các bài Notes cũ của bạn. Dữ liệu được lưu an toàn tuyệt đối trên máy Mac của bạn.")
    history = load_history()
    
    if not history:
        st.info("Trống! Bạn chưa tạo bài Notes nào.")
    else:
        for item in history:
            url_str = str(item.get('url', ''))
            with st.expander(f"🕒 {item.get('date', '')} - Link: {url_str[:50]}..."):
                st.markdown(item.get("content", ""))

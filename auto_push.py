import os
import subprocess
import time

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ({e.returncode}):\n{e.stderr}")
        return False

print("🚀 Đang kiểm tra thay đổi mã nguồn...")
if not run_command("git status --porcelain"):
    print("❌ Lỗi kiểm tra Git.")
    exit(1)
    
status_output = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True).stdout.strip()

if not status_output:
    print("✅ Không có thay đổi nào mới. Mã nguồn đã được cập nhật bản mới nhất trên Github.")
    time.sleep(3)
    exit(0)

print("\n--- Có thay đổi tìm thấy ---")
print(status_output)
print("----------------------------\n")

print("📦 Đang thêm các file thay đổi vào Git...")
run_command("git add .")

commit_msg = f"Auto commit cập nhật tính năng - {time.strftime('%Y-%m-%d %H:%M:%S')}"
print(f"📝 Đang commit với lời nhắn: '{commit_msg}'...")
run_command(f"git commit -m \"{commit_msg}\"")

print("☁️ Đang đẩy code lên Github (Và kích hoạt Streamlit Cloud tự cập nhật)...")
if run_command("git push -u origin main"):
    print("\n🎉 THÀNH CÔNG! Mã nguồn đã được đẩy lên Github.")
    print("⏳ Streamlit Cloud sẽ tự động tải phiên bản mới này và cập nhật trên Website trong khoảng 1-2 phút.")
else:
    print("\n❌ LỖI: Không thể Push code. Vui lòng kiểm tra lại kết nối mạng hoặc quyền truy cập Github.")

print("\nCửa sổ này sẽ tự đóng sau 10 giây...")
time.sleep(10)

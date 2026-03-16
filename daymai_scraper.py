import undetected_chromedriver as uc
import os
import time
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

def get_daymai_m3u8(video_url):
    print(f"Bắt đầu quy trình tự động bẻ khóa Daymai cho link: {video_url}")
    DAYMAI_USER = os.getenv("DAYMAI_USER")
    DAYMAI_PASS = os.getenv("DAYMAI_PASS")

    if not DAYMAI_USER or not DAYMAI_PASS:
        print("Lỗi: Thiếu tài khoản Daymai trong cấu hình.")
        return None

    # undetected-chromedriver tự động bypass hầu hết bot detection
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Để uc tự động tìm driver phù hợp với browser v146
    driver = uc.Chrome(options=options)
    
    try:
        print("1. Đang truy cập trang chủ Daymai/The1ight để lấy Cookie phiên làm việc...")
        driver.get("https://daymai.vn/user/login")
        time.sleep(7)
        print(f"Tiêu đề trang: {driver.title}")
        
        # Check for Cloudflare or blank
        if not driver.title or "Just a moment" in driver.title:
            print("⚠️ Phát hiện lớp bảo mật (Cloudflare/Bot detect). Đang thử chờ thêm...")
            time.sleep(10)

        # Kiểm tra xem có khung login không
        try:
            print("2. Đang tự động điền thông tin đăng nhập...")
            username_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Tên đăng nhập"], #username'))
            )
            password_field = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="Nhập mật khẩu"], #password')
            
            username_field.send_keys(DAYMAI_USER)
            password_field.send_keys(DAYMAI_PASS)
            
            # Tìm nút đăng nhập
            login_button = driver.find_element(By.CSS_SELECTOR, "button.btn-login, .login-button")
            login_button.click()
            
            print("3. Đã bấm Đăng nhập. Chờ thiết lập phiên làm việc...")
            time.sleep(10)
        except Exception as e:
            print(f"Lỗi login/Không thấy form: {e}")
            print("Mã nguồn trang (500 ký tự đầu):", driver.page_source[:500])
        
        print(f"4. Truy cập trang danh sách ghi hình: https://daymai.vn/meet/past")
        driver.get("https://daymai.vn/meet/past")
        time.sleep(10)
        print(f"Link hiện tại: {driver.current_url}")
        print(f"Tiêu đề trang record: {driver.title}")
        
        # Check if we are still on the login page or blank
        if "login" in driver.current_url.lower():
            print(f"❌ Vẫn bị kẹt ở trang Login hoặc Redirect. Link: {driver.current_url}")
            try:
                error_msg = driver.find_element(By.CSS_SELECTOR, ".alert-danger, .error-message").text
                print(f"Lỗi hiển thị trên web: {error_msg}")
            except:
                pass
        
        video_id = video_url.split('/')[-2] if '/' in video_url else ""
        print(f"5. Đang tìm nút Play cho Video ID: {video_id}")
        
        try:
            play_links = driver.find_elements(By.CSS_SELECTOR, f"a[href*='{video_id}']")
            if not play_links:
                driver.get(video_url)
            else:
                driver.execute_script("arguments[0].click();", play_links[0])
                print("Đã click vào nút Play.")
        except Exception as e:
            print(f"Lỗi điều hướng: {e}")
            driver.get(video_url)
            
        time.sleep(15) 
        driver.save_screenshot("daymai_final_debug.png")
        
        video_source_url = None
        try:
            download_btn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a#downloadButton, .downloadBtn, a[download]"))
            )
            video_source_url = download_btn.get_attribute("href")
            if video_source_url:
                print(f"✅ Tìm thấy link tải trực tiếp: {video_source_url[:80]}...")
                return video_source_url
        except Exception as e:
            print(f"Không thấy nút Download: {e}")

        # Nếu không có nút download, thử lấy từ video tag
        try:
            video_tag = driver.find_element(By.TAG_NAME, "video")
            video_source_url = video_tag.get_attribute("src")
            if video_source_url:
                print(f"✅ Tìm thấy link từ thẻ video: {video_source_url[:80]}...")
                return video_source_url
        except:
            pass

        print("❌ Không tìm thấy luồng video bằng cách quét DOM.")
        return None
            
    except Exception as e:
        print(f"Lỗi kịch bản: {e}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    # Test link
    test_link = "https://vc.daymai.vn/api/show/play/Z2JoZZaflms/r1OkmMLcOZp-eFNsVZWmwJpmlpdiZ5SglG5ma5eTao-hwmpqbVOv"
    result = get_daymai_m3u8(test_link)
    print(f"\nKẾT QUẢ CUỐI CÙNG: {result}")

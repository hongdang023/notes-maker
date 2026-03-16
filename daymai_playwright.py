import os
import time
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

load_dotenv()

async def get_daymai_source_playwright(video_url):
    print(f"Bắt đầu quy trình Playwright cho link: {video_url}")
    DAYMAI_USER = os.getenv("DAYMAI_USER")
    DAYMAI_PASS = os.getenv("DAYMAI_PASS")

    if not DAYMAI_USER or not DAYMAI_PASS:
        print("Lỗi: Thiếu tài khoản Daymai.")
        return None

    async with async_playwright() as p:
        # Khởi tạo browser
        browser = await p.chromium.launch(headless=True)
        # Sử dụng context với User Agent xịn
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        
        # Apply stealth chuẩn
        await Stealth().apply_stealth_async(page)

        video_source_url = None

        # Network Interception
        async def handle_request(request):
            nonlocal video_source_url
            url = request.url
            if ('.mp4' in url or '.m4a' in url) and ('s3' in url or 'cloud' in url):
                if not video_source_url:
                     video_source_url = url
                     print(f"🎯 Đã bắt được link từ Network: {url[:60]}...")
            elif '.m3u8' in url and not video_source_url:
                video_source_url = url
                print(f"🎯 Đã bắt được link m3u8 từ Network: {url[:60]}...")

        page.on("request", handle_request)

        try:
            print("1. Đang truy cập trang Login...")
            await page.goto("https://daymai.vn/user/login", wait_until="networkidle")
            
            print("2. Điền thông tin đăng nhập...")
            await page.fill('input[placeholder="Tên đăng nhập"], #username', DAYMAI_USER)
            await page.fill('input[placeholder="Nhập mật khẩu"], #password', DAYMAI_PASS)
            await page.click('button.btn-login, .login-button')
            
            # Đợi chuyển hướng (thường là sang /g hoặc dashboard)
            await page.wait_for_timeout(7000)
            print(f"3. Sau login, URL hiện tại: {page.url}")

            if "login" in page.url and "logout" not in page.url:
                print("❌ Login có vẻ không thành công.")
                await page.screenshot(path="login_fail.png")
            
            print(f"4. Truy cập link video: {video_url}")
            # Chờ video page tải xong
            await page.goto(video_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(15000) # Đợi player load kỹ

            # Chụp ảnh debug
            await page.screenshot(path="playwright_debug.png")
            
            # Print page source snippet if blank
            content = await page.content()
            if len(content) < 500:
                print(f"⚠️ Cảnh báo: Trang có vẻ trống (Length: {len(content)})")
                print("Mã nguồn:", content)

            # Thử mọi cách tìm link trong DOM
            # 1. Nút download
            download_btn = await page.query_selector("a#downloadButton, .downloadBtn, a[download]")
            if download_btn:
                video_source_url = await download_btn.get_attribute("href")
            
            # 2. Thẻ video
            if not video_source_url:
                video_tag = await page.query_selector("video")
                if video_tag:
                    video_source_url = await video_tag.get_attribute("src")

            if video_source_url:
                print(f"🎉 THÀNH CÔNG: {video_source_url[:80]}...")
                return video_source_url
            else:
                print("❌ Không tìm thấy luồng video qua DOM/Network.")
                return None

        except Exception as e:
            print(f"Lỗi thực thi: {e}")
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    url = "https://vc.daymai.vn/api/show/play/Z2JoZZaflms/r1OkmMLcOZp-eFNsVZWmwJpmlpdiZ5SglG5ma5eTao-hwmpqbVOv"
    result = asyncio.run(get_daymai_source_playwright(url))
    print(f"\nFinal Result: {result}")

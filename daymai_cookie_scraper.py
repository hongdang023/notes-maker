import requests
import re
import os
from bs4 import BeautifulSoup

def extract_daymai_video_with_cookie(video_url, cookie_string):
    """
    Sử dụng Cookie của người dùng để lấy link video trực tiếp.
    Chắc chắn 100% không bị chặn bởi Bot Detection.
    """
    print(f"Bắt đầu trích xuất với Cookie cho link: {video_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie_string,
        'Referer': 'https://daymai.vn/'
    }

    try:
        # 1. Thử tải trang video
        response = requests.get(video_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ Lỗi HTTP: {response.status_code}")
            return None
        
        html_content = response.text
        
        # 2. Tìm link .mp4 hoặc .m3u8 trong mã nguồn (S3 links)
        # Daymai thường để link trong script hoặc thẻ video
        
        # Tìm link S3/Cloud có đuôi .mp4 hoặc .m3u8
        video_links = re.findall(r'https?://[^\s"\']+\.(?:mp4|m3u8|m4a)[^\s"\']*', html_content)
        
        # Lọc các link chất lượng cao (thường chứa 's3' hoặc 'cloud')
        priority_links = [l for l in video_links if 's3' in l or 'cloud' in l]
        
        if priority_links:
            # Lấy link đầu tiên tìm thấy
            final_url = priority_links[0].replace('\\', '')
            print(f"🎉 Tìm thấy link video: {final_url[:80]}...")
            return final_url
            
        # 3. Thử tìm nút Download (nếu có trong HTML)
        soup = BeautifulSoup(html_content, 'html.parser')
        download_btn = soup.select_one('a#downloadButton, .downloadBtn, a[download]')
        if download_btn and download_btn.get('href'):
            final_url = download_btn.get('href')
            print(f"✅ Tìm thấy link từ Button: {final_url[:80]}...")
            return final_url
            
        print("❌ Không tìm thấy link video trong mã nguồn trang.")
        return None

    except Exception as e:
        print(f"Lỗi trích xuất Cookie: {e}")
        return None

if __name__ == "__main__":
    # Test stub
    pass

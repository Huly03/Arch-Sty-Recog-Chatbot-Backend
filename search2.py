import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googletrans import Translator
import os
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse

MAX_URL_LENGTH = 2000  # Giới hạn độ dài URL
import os
import time
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from urllib.parse import urlparse

SIM_THRESHOLD = 0.60

# Danh sách các domain cần loại trừ
EXCLUDED_DOMAINS = [
    "google.com",
    "accounts.google.com",
    "policies.google.com",
    "support.google.com",
    "myactivity.google.com",
    "www.google.com.vn",
    "www.google.com",
]

def is_valid_article_url(url):
    try:
        domain = urlparse(url).netloc
        for excluded in EXCLUDED_DOMAINS:
            if excluded in domain:
                return False
        return True
    except:
        return False

def extract_info_from_article(page_url):
    try:
        response = requests.get(page_url, timeout=5)
        if response.status_code != 200:
            return {"description": "Không rõ", "source_page": page_url}

        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        description = " ".join([p.text.strip() for p in paragraphs]) if paragraphs else "Không rõ"

        return {
            "description": description,
            "source_page": page_url
        }
    except Exception as e:
        return {
            "description": f"Lỗi phân tích bài báo: {e}",
            "source_page": page_url
        }

def search_google_and_extract_info(query):
    print(f"🔍 Đang tìm kiếm bài báo từ Google với từ khóa: {query}...")

    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    # chrome_options.add_argument("--headless=new")  # Bỏ comment nếu muốn chạy ẩn

    driver = uc.Chrome(options=chrome_options)

    try:
        driver.get("https://www.google.com/")
        driver.maximize_window()
        time.sleep(2)

        # Tìm kiếm trên Google với từ khóa nhập vào
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.send_keys(query)
        search_box.submit()  # Bấm Enter để tìm kiếm
        time.sleep(3)  # Tăng thời gian chờ để trang tải xong

        # Lấy danh sách các liên kết bài báo liên quan
        article_links = driver.find_elements(By.XPATH, '//a[contains(@href, "http")]')

        seen_domains = set()
        matched_articles = []

        for link in article_links:
            url = link.get_attribute("href")
            if not url:
                continue

            domain = urlparse(url).netloc
            if domain in seen_domains:
                continue

            if not is_valid_article_url(url):
                continue

            seen_domains.add(domain)

            article_info = extract_info_from_article(url)
            article_info["source_page"] = url
            matched_articles.append(article_info)

            if len(matched_articles) >= 10:
                break

        driver.quit()

        return {
            "source": "Google Search (Selenium)",
            "matched_articles": matched_articles
        }

    except Exception as ex:
        driver.quit()
        return {"error": f"Lỗi khi tìm kiếm: {ex}"}

# Ví dụ chạy:
if __name__ == "__main__":
    query = input("Nhập từ khóa tìm kiếm: ")  # Nhập từ khóa tìm kiếm
    result = search_google_and_extract_info(query)
    print(result)

def truncate_text(text, max_length=MAX_URL_LENGTH):
    if len(text) > max_length:
        return text[:max_length]
    return text

async def translate_text(text, src='en', dest='vi'):
    text = truncate_text(text)
    translator = Translator()
    # Sử dụng async/await để đợi dịch
    translated = await translator.translate(text, src=src, dest=dest)
    return translated.text

async def search_and_scrape(keywords):
    # Tạo URL Wikipedia tiếng Anh với từ khóa người dùng nhập
    base_url = "https://en.wikipedia.org/wiki/"
    wikipedia_url = base_url + urllib.parse.quote(keywords)

    # Cấu hình trình duyệt Selenium (không hiển thị cửa sổ trình duyệt)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Chạy ở chế độ ẩn danh (không mở cửa sổ trình duyệt)

    # Khởi tạo WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Mở trang Wikipedia
    driver.get(wikipedia_url)

    try:
        # Chờ thẻ chứa nội dung chính xuất hiện (chờ cho đến khi thẻ 'mw-parser-output' có mặt)
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'mw-parser-output'))
        WebDriverWait(driver, 10).until(element_present)

        # Tìm nội dung trong thẻ 'mw-parser-output'
        main_content = driver.find_element(By.CLASS_NAME, 'mw-parser-output')

        # Trích xuất văn bản từ nội dung chính
        body_text = main_content.text
        body_text = truncate_text(body_text)

        # Dịch văn bản sang tiếng Việt
        translated_text = await translate_text(body_text, src='en', dest='vi')

        # Tạo thư mục và lưu văn bản vào tệp
        output_dir = 'demo/data_in'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        base_filename = f"{keywords.replace(' ', '_')}"  # Thêm từ khóa vào tên tệp
        output_file_path = os.path.join(output_dir, f"{base_filename}.txt")

        # Lưu văn bản đã dịch vào tệp
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(translated_text)

        print(f"Văn bản đã được dịch và lưu vào tệp: {output_file_path}")

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

    finally:
        # Đóng trình duyệt
        driver.quit()


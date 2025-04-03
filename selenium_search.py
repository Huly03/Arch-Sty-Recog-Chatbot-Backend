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

def search_google_and_extract_info(image_path):
    print("🔍 Đang tìm kiếm bài báo từ Google Image...")

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

        # Click nút camera
        camera_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Search by image"]'))
        )
        camera_button.click()
        time.sleep(2)

        # Upload ảnh
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="file"]'))
        )
        abs_path = os.path.abspath(image_path)
        file_input.send_keys(abs_path)
        time.sleep(5)  # Tùy chỉnh lại nếu mạng chậm

        # Chuyển sang tab "About this image"
        about_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "About this image")]'))
        )
        about_tab.click()
        time.sleep(3)

        # Lấy danh sách bài báo liên quan
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
            "source": "Google Image (Selenium)",
            "matched_articles": matched_articles
        }

    except Exception as ex:
        driver.quit()
        return {"error": f"Lỗi khi tìm kiếm: {ex}"}
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import undetected_chromedriver as uc
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
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

        # Log nội dung đã trích xuất
        app.logger.info(f"Extracted {len(paragraphs)} paragraphs from {page_url}")

        description = " ".join([p.text.strip() for p in paragraphs]) if paragraphs else "Không rõ"

        return {
            "description": description,
            "source_page": page_url
        }
    except Exception as e:
        app.logger.error(f"Error extracting article from {page_url}: {str(e)}")
        return {
            "description": f"Lỗi phân tích bài báo: {e}",
            "source_page": page_url
        }


@app.route('/search', methods=['POST'])
def search_google_and_extract_info():
    if request.is_json:
        data = request.get_json()
        query = data.get("query", "")
        if not query:
            return jsonify({"error": "Không có từ khóa tìm kiếm"}), 400

        app.logger.info(f"Received query: {query}")  # Log từ khóa tìm kiếm

        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")

        driver = uc.Chrome(options=chrome_options)

        try:
            driver.get("https://www.google.com/")
            driver.maximize_window()
            time.sleep(2)

            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.send_keys(query)
            search_box.submit()
            time.sleep(3)

            # Lấy tất cả các liên kết bài báo
            article_links = driver.find_elements(By.XPATH, '//a[contains(@href, "http")]')

            app.logger.info(f"Found {len(article_links)} links on Google search.")  # Log số lượng liên kết tìm được

            seen_domains = set()
            matched_articles = []

            for link in article_links:
                url = link.get_attribute("href")
                if not url:
                    continue

                app.logger.info(f"Checking URL: {url}")  # Log từng liên kết đang được kiểm tra

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

            app.logger.info(f"Matched articles: {matched_articles}")  # Log kết quả tìm kiếm

            return jsonify({
                "source": "Google Search (Selenium)",
                "matched_articles": matched_articles
            })

        except Exception as ex:
            driver.quit()
            app.logger.error(f"Error during search: {str(ex)}")
            return jsonify({"error": f"Lỗi khi tìm kiếm: {str(ex)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)


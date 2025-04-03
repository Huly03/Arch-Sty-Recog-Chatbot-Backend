import os
import time
import json
from flask import Flask, request, jsonify, render_template, send_file
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

def search_google_by_text(query):
    print(f"🔍 Đang tìm kiếm bài báo từ Google với chuỗi: {query}")

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

        # Nhập chuỗi tìm kiếm vào ô tìm kiếm của Google
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.send_keys(query)
        search_box.submit()
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
            "source": "Google Search (Selenium)",
            "matched_articles": matched_articles
        }

    except Exception as ex:
        driver.quit()
        return {"error": f"Lỗi khi tìm kiếm: {ex}"}

def process_keywords_from_file(file_path):
    # Đọc các từ khóa từ file TXT
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            queries = file.readlines()

        for query in queries:
            query = query.strip()
            if query:
                result = search_google_by_text(query)
                # Lưu kết quả vào file
                save_article_to_file(query, result)
                time.sleep(5)  # Để tránh bị block quá nhanh

    except Exception as e:
        print(f"Lỗi khi xử lý file: {e}")

def save_article_to_file(query, result):
    try:
        # Tạo tên file từ từ khóa
        file_name = f"{query}.txt"
        file_path = os.path.join('demo', 'data_in', file_name)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Chuyển kết quả thành chuỗi văn bản
        file_content = f"Query: {query}\n\nSource: {result.get('source', 'Unknown')}\n\nMatched Articles:\n"
        for article in result.get("matched_articles", []):
            file_content += f"Source Page: {article['source_page']}\nDescription: {article['description']}\n\n"
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(file_content)
        print(f"Đã lưu kết quả vào: {file_path}")

    except Exception as e:
        print(f"Lỗi khi lưu bài báo: {e}")

# Flask API
download = Flask(__name__)

@download.route('/')
def index():
    return render_template('index.html')

@download.route('/search_by_text', methods=['GET'])
def search_by_text():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "No query provided."}), 400

    result = search_google_by_text(query)
    return jsonify(result)

if __name__ == '__main__':
    # Đường dẫn tới file chứa danh sách từ khóa
    keywords_file = 'D:/CodePy/python_rag_llm_base_public-main/keywords.txt'
    process_keywords_from_file(keywords_file)
    
    # Chạy Flask app
    download.run(debug=True)

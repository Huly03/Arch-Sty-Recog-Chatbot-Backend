import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service  # Cập nhật đúng Service cho Edge
from selenium.webdriver.edge.options import Options
from bs4 import BeautifulSoup

# Hàm cắt đoạn văn bản nếu dài quá
def truncate_text(text, max_length=2000):
    return text[:max_length] if len(text) > max_length else text

# Hàm kiểm tra và tạo tên tệp mới nếu đã tồn tại
def get_unique_filename(base_filename, output_dir):
    count = 1
    filename = f"{base_filename}.txt"
    while os.path.exists(os.path.join(output_dir, filename)):
        filename = f"{base_filename}_{count}.txt"
        count += 1
    return filename

# Hàm tìm kiếm và trích xuất văn bản từ các bài báo
def search_and_scrape(query):
    # Cấu hình Selenium WebDriver với Microsoft Edge
    edge_options = Options()
    edge_options.add_argument("--headless")  # Chạy nền, không hiện trình duyệt
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("user-agent=Mozilla/5.0 ...")  # User-agent giả

    # Đường dẫn đến Microsoft Edge WebDriver
    webdriver_path = r'C:/edgedriver/msedgedriver.exe'  # Cập nhật đường dẫn tới WebDriver của bạn

    # Tạo Service cho WebDriver Edge
    service = Service(webdriver_path)

    # Tạo trình điều khiển trình duyệt Microsoft Edge
    driver = webdriver.Edge(service=service, options=edge_options)

    # Tìm kiếm trên Google
    search_url = f"https://www.google.com/search?q=Phong+cách+kiến+trúc+{query}"
    driver.get(search_url)
    time.sleep(5)  # Tăng thời gian chờ để trang tải xong

    # Lấy các liên kết từ các kết quả tìm kiếm trên Google
    result_links = []
    elements = driver.find_elements(By.XPATH, "//div[@class='rc']//h3//ancestor::a")

    # Kiểm tra xem có phần tử nào không
    if len(elements) == 0:
        print("❌ Không tìm thấy kết quả tìm kiếm nào.")
        driver.quit()
        return
    else:
        print(f"Tìm thấy {len(elements)} kết quả.")

    # Lấy tất cả các kết quả từ trang đầu tiên
    for element in elements:
        link = element.get_attribute("href")
        result_links.append(link)

    if not result_links:
        print("❌ Không tìm thấy kết quả phù hợp.")
        driver.quit()
        return

    all_text = ""
    for url in result_links:
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Trích xuất văn bản từ các thẻ <p>, <li>, <h1>, <h2>, <h3>, <h4>, <h5>, <h6>
            for tag in soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                content = tag.get_text(separator="\n", strip=True)
                if content:
                    all_text += content + "\n"

        except Exception as e:
            print(f"Lỗi khi truy cập {url}: {e}")

    if all_text.strip():
        # Cắt gọn nếu quá dài
        all_text = truncate_text(all_text)

        # Lưu văn bản
        output_dir = 'demo/data_in'
        os.makedirs(output_dir, exist_ok=True)

        base_filename = f"search_results_{query.replace(' ', '_')}"
        unique_filename = get_unique_filename(base_filename, output_dir)
        output_path = os.path.join(output_dir, unique_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(all_text)

        print(f"✅ Văn bản đã lưu: {output_path}")
    else:
        print("⚠️ Không trích xuất được nội dung từ các bài báo.")

    driver.quit()

# Ví dụ chạy:
if __name__ == "__main__":
    search_and_scrape("Tân cổ điển")
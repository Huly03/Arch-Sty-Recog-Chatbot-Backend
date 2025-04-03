from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import os

def test_google_image_search_with_upload(image_path):
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    # chrome_options.add_argument("--headless=new")  # Bỏ comment nếu cần chạy ẩn

    driver = uc.Chrome(options=chrome_options)

    try:
        print("🔍 Đang mở Google...")
        driver.get("https://google.com/")
        driver.maximize_window()
        
        # Click vào biểu tượng camera
        print("📸 Đang tìm biểu tượng camera...")
        time.sleep(2)
        camera_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Search by image"]'))
        )
        camera_button.click()
        print("✅ Đã click camera")

        # Đợi input file hiện ra
        print("📤 Đang tìm thẻ input để upload ảnh...")
        time.sleep(2)
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="file"]'))
        )

        # Upload ảnh
        abs_path = os.path.abspath(image_path)
        print(f"📤 Upload ảnh từ: {abs_path}")
        file_input.send_keys(abs_path)

        print("✅ Ảnh đã được tải lên thành công!")
        time.sleep(10)  # Cho bạn thời gian quan sát kết quả

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")
        #driver.quit()

if __name__ == "__main__":
    # Thay bằng đường dẫn ảnh thật trên máy bạn
    test_google_image_search_with_upload("D:/LuanVanTotNghiep/NhanDienThongTinTranh/images (1).jpg")

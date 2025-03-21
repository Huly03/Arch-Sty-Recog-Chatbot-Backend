import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

def search_and_scrape(keywords):
    # Tạo URL tìm kiếm Google với từ khóa người dùng nhập
    search_query = urllib.parse.quote(keywords)
    search_url = f"https://www.google.com/search?q={search_query}"

    # Tải trang kết quả tìm kiếm Google
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Tìm các liên kết trong kết quả tìm kiếm
    search_results = soup.find_all('a', href=True)
    
    # Lọc ra các URL hợp lệ (không phải các liên kết đến các trang Google nội bộ)
    valid_urls = []
    for link in search_results:
        href = link['href']
        if href.startswith('http') and not href.startswith('https://www.google.com') and "support" not in href:
            valid_urls.append(href)

    # Hiển thị các liên kết tìm thấy và yêu cầu người dùng chọn một trang
    # if valid_urls:
    #     print("Các trang web tìm thấy:")
    #     for idx, url in enumerate(valid_urls[:5]):  # Hiển thị tối đa 5 kết quả đầu tiên
    #         print(f"{idx + 1}. {url}")

    #     # Yêu cầu người dùng chọn trang web
    #     while True:
    #         try:
    #             choice = int(input(f"Chọn một trang (1-{len(valid_urls[:5])}): ")) - 1
    #             if choice < 0 or choice >= len(valid_urls[:5]):
    #                 print("Lựa chọn không hợp lệ. Vui lòng chọn lại.")
    #             else:
    #                 break  # Thoát vòng lặp khi có lựa chọn hợp lệ
    #         except ValueError:
    #             print("Vui lòng nhập số hợp lệ.")
    #             continue

    #     # Lấy URL của trang người dùng chọn
    #     selected_url = valid_urls[choice]
    #     print(f"Truy cập vào trang: {selected_url}")

    #     # Truy cập vào trang web
    #     page_response = requests.get(selected_url)
    #     page_soup = BeautifulSoup(page_response.text, 'html.parser')

    #     # Lấy tất cả nội dung văn bản trong thẻ <body>
    #     body_text = page_soup.find('body').get_text(separator="\n", strip=True)
        
    #     # Tạo thư mục data_in nếu chưa tồn tại
    #     if not os.path.exists('data_in'):
    #         os.makedirs('data_in')

    #     # Tạo tên tệp với số tăng dần
    #     base_filename = f"{keywords.replace(' ', '_')}"  # Thay dấu cách bằng dấu gạch dưới
    #     counter = 1
    #     output_file_path = os.path.join('data_in', f"{base_filename}_{counter}.txt")
        
    #     # Kiểm tra và tăng dần số đếm nếu tệp đã tồn tại
    #     while os.path.exists(output_file_path):
    #         counter += 1
    #         output_file_path = os.path.join('data_in', f"{base_filename}_{counter}.txt")

    #     # Mở tệp và ghi dữ liệu vào
    #     with open(output_file_path, 'w', encoding='utf-8') as file:
    #         file.write(body_text)

    #     print(f"Văn bản đã được lưu vào tệp: {output_file_path}")

    # else:
    #     print("Không tìm thấy liên kết hợp lệ trong kết quả tìm kiếm.")



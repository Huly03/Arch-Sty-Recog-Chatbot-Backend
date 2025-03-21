import webbrowser
from chatbot.services.files_chat_agent import FilesChatAgent  # noqa: E402
from app.config import settings
from chatbot.services.search_architecture import search_and_scrape

# Cấu hình LLM (Ví dụ: OpenAI hoặc Google Gemini)
settings.LLM_NAME = "gemini"  # Chuyển từ OpenAI sang Google Gemini (nếu cần)

# Nhập phong cách kiến trúc từ người dùng
style_architecture = input("Nhập phong cách kiến trúc bạn muốn tìm kiếm: ")

# Tạo URL tìm kiếm Google với từ khóa người dùng nhập
search_url = f"https://www.google.com/search?q=+Phong cách kiến trúc+{style_architecture}"

# Mở trình duyệt với kết quả tìm kiếm
webbrowser.open(search_url)

# Tạo đối tượng FilesChatAgent và gọi API để tìm kiếm các tài liệu liên quan
# chat = FilesChatAgent("demo/data_vector").get_workflow().compile().invoke(
#     input={
#         "question": style_architecture,  # Câu hỏi là phong cách kiến trúc người dùng nhập
#     }
# )

# In kết quả trả về (các bài báo hoặc tài liệu liên quan)
print("Kết quả tìm kiếm liên quan đến phong cách kiến trúc:", style_architecture)
#print(chat)

# Hiển thị câu trả lời được tạo từ chatbot
#print("generation", chat["generation"])
search_and_scrape(style_architecture)

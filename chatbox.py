import os
from chatbot.services.files_chat_agent import FilesChatAgent  # noqa: E402
from app.config import Settings
from search import search_and_scrape
from chatbot.utils.llm import LLM  # LLM để tóm tắt
import asyncio
from ingestion.ingestion import Ingestion
from googletrans import Translator
from langdetect import detect  # Thêm thư viện để nhận diện ngôn ngữ
from download import search_google_by_text, save_article_to_file  
async def translate_to_vietnamese(text):
    # Khởi tạo trình dịch
    translator = Translator()
    # Dịch văn bản sang tiếng Việt và đợi kết quả trả về
    translated = await translator.translate(text, src='en', dest='vi')
    return translated.text

async def convert_txt_to_vector():
    # Đường dẫn đến thư mục chứa file .txt và thư mục lưu file vector
    input_folder = "demo/data_in"
    vector_store_folder = "demo/data_vector"
    
    # Thực hiện quá trình ingestion để chuyển file .txt thành vector
    try:
        print("Bắt đầu quá trình ingestion để chuyển file .txt thành vector...")
        Ingestion("gemini").ingestion_folder(
            path_input_folder=input_folder,
            path_vector_store=vector_store_folder
        )
        print("Quá trình ingestion đã hoàn thành. Các file đã được chuyển thành vector.")
    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình ingestion: {e}")

async def run_chatbot():
    while True:
        # Cấu hình LLM (Ví dụ: OpenAI hoặc Google Gemini)
        Settings.LLM_NAME = "gemini"  # Chuyển từ OpenAI sang Google Gemini (nếu cần)
        
        style_architecture = input("Nhập phong cách kiến trúc bạn muốn tìm kiếm: ")
        
        if style_architecture == "thoát":
            print("Thoát chương trình.")
            break

        # Kiểm tra xem style_architecture có trong data_vector không
        chat = FilesChatAgent("demo/data_vector").get_workflow().compile().invoke(
            input={"question": style_architecture}
        )

        if isinstance(chat, list):
            chat = "\n".join([str(item) for item in chat])  # Nếu là danh sách, nối các phần tử thành chuỗi
        elif isinstance(chat, dict):
            chat = str(chat)  # Nếu là từ điển, chuyển thành chuỗi
        elif not isinstance(chat, str):
            print("Lỗi: Dữ liệu trả về không phải là chuỗi văn bản hợp lệ.")
            continue

        # Kiểm tra nếu chat không có dữ liệu hợp lệ
        if not chat or chat.strip() == "Tôi có thể giúp gì cho bạn về công ty?":
            print(f"Không tìm thấy dữ liệu cho {style_architecture} trong data_vector. Đang tìm kiếm từ Google...")
            
            # Tìm kiếm từ Google và lưu kết quả vào file
            result = search_google_by_text(style_architecture)
            save_article_to_file(style_architecture, result)  # Lưu kết quả vào file
            print(f"Kết quả đã được lưu lại với từ khóa: {style_architecture}")

            # Chuyển đổi các file .txt thành vector
            await convert_txt_to_vector()
            print("Quá trình chuyển đổi file .txt thành vector đã hoàn thành.")
            
            # Sau khi chuyển đổi, truy vấn lại và in ra kết quả
            chat = FilesChatAgent("demo/data_vector").get_workflow().compile().invoke(
                input={"question": style_architecture}
            )

            if isinstance(chat, list):
                chat = "\n".join([str(item) for item in chat])
            elif isinstance(chat, dict):
                chat = str(chat)

            print(f"Chatbot đã trả lời với kết quả sau khi chuyển đổi vector: {chat}")
        else:
            print("Chatbot đã trả lời với kết quả từ data_vector:", chat)

        # Kiểm tra nếu chat là chuỗi và chuyển nó thành kiểu dữ liệu phù hợp
        documents = []
        if isinstance(chat, str):
            # Nếu là chuỗi, không thể sử dụng .get() để lấy "generation", phải xử lý khác
            documents = [chat]  # Chuyển thành danh sách với một phần tử là chuỗi
        elif isinstance(chat, dict):
            # Nếu là từ điển, kiểm tra "generation"
            documents = chat.get("generation", [])  # Lấy dữ liệu từ chatbot để tóm tắt

        while True:
            # Nhập từ khóa mỗi lần từ người dùng
            query = input(f"Nhập từ khóa hoặc câu hỏi liên quan đến {style_architecture}:").lower()
            
            # Kiểm tra xem người dùng có nhập "tiếng Việt" không
            if query == "tiếng việt":
                translated_chat = await translate_to_vietnamese(chat)
                print("Câu trả lời (tiếng Việt):", translated_chat)
                if query == "tóm tắt":
                    print("Đang tóm tắt...")

                    # Sử dụng LLM để tạo tóm tắt từ dữ liệu vector đã lưu
                    llm = LLM().get_llm(Settings.LLM_NAME)
                    
                    context = "\n".join(doc for doc in translated_chat)  # Kết hợp các chuỗi văn bản

                    # Định dạng đầu vào cho LLM để tạo tóm tắt
                    messages = [
                        {"role": "system", "content": "Tóm tắt đoạn văn sau:"},
                        {"role": "user", "content": context}
                    ]
                    
                    # Gửi vào mô hình để tạo tóm tắt
                    summary = llm.invoke(messages)  # Sử dụng invoke thay vì gọi trực tiếp
                    print("Tóm tắt:", summary)

            # Kiểm tra nếu người dùng nhập "khác"
            elif query == "khác":
                break
            
            # Kiểm tra nếu người dùng yêu cầu tóm tắt
            elif query == "tóm tắt":
                print("Đang tóm tắt...")

                # Sử dụng LLM để tạo tóm tắt từ dữ liệu vector đã lưu
                llm = LLM().get_llm(Settings.LLM_NAME)
                
                context = "\n".join(doc for doc in documents)  # Kết hợp các chuỗi văn bản

                # Định dạng đầu vào cho LLM để tạo tóm tắt
                messages = [
                    {"role": "system", "content": "Tóm tắt đoạn văn sau:"},
                    {"role": "user", "content": context}
                ]
                
                # Gửi vào mô hình để tạo tóm tắt
                summary = llm.invoke(messages)  # Sử dụng invoke thay vì gọi trực tiếp
                print("Tóm tắt:", summary)
            # Kiểm tra nếu người dùng yêu cầu "tiếp tục"
            elif query == "tiếp tục":
                break
            # Điều kiện else xử lý tìm kiếm tài liệu
            else:
                print(f"Tìm kiếm tài liệu liên quan đến '{query}' trong vector store...")

                if documents:
                    print(f"Các tài liệu liên quan đến '{query}':")
                    for idx, doc in enumerate(documents, start=1):
                        print(f"{idx}. {doc[:500]}...")  # Hiển thị một phần của tài liệu
                else:
                    print("Không tìm thấy tài liệu liên quan.")

if __name__ == "__main__":
     asyncio.run(run_chatbot())
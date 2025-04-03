from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import logging
import asyncio
from googletrans import Translator
from chatbot.services.files_chat_agent import FilesChatAgent  # noqa: E402
from app.config import Settings
from ingestion.ingestion import Ingestion
from chatbot.utils.llm import LLM  # LLM để tóm tắt
from download import search_google_by_text, save_article_to_file

# Thiết lập logging
logging.basicConfig(level=logging.DEBUG)

# Tạo ứng dụng Flask
app = Flask(__name__)

# Cấu hình CORS cho phép tất cả các domain
CORS(app)  # Cho phép tất cả các domain gửi yêu cầu đến Flask API

# Hàm dịch văn bản sang tiếng Việt
def translate_to_vietnamese(text):
    translator = Translator()
    translated = translator.translate(text, src='en', dest='vi')
    return translated.text

# Hàm chuyển file .txt thành vector (sử dụng quá trình ingestion)
def convert_txt_to_vector():
    # Đường dẫn đến thư mục chứa file .txt và thư mục lưu file vector
    input_folder = "demo/data_in"
    vector_store_folder = "demo/data_vector"
    
    # Thực hiện quá trình ingestion để chuyển file .txt thành vector
    try:
        logging.info("Bắt đầu quá trình ingestion để chuyển file .txt thành vector...")
        Ingestion("gemini").ingestion_folder(
            path_input_folder=input_folder,
            path_vector_store=vector_store_folder
        )
        logging.info("Quá trình ingestion đã hoàn thành. Các file đã được chuyển thành vector.")
    except Exception as e:
        logging.error(f"Đã xảy ra lỗi trong quá trình ingestion: {e}")

# Hàm chính để chạy chatbot
def run_chatbot(user_input):
    try:
        logging.debug("Received user input for chatbot: %s", user_input)

        # Cấu hình LLM (Ví dụ: OpenAI hoặc Google Gemini)
        Settings.LLM_NAME = "gemini"  # Chuyển từ OpenAI sang Google Gemini (nếu cần)
        
        # Kiểm tra xem style_architecture có trong data_vector không
        chat = FilesChatAgent("demo/data_vector").get_workflow().compile().invoke(
            input={"question": user_input}
        )

        logging.debug("Chatbot returned: %s", chat)

        if isinstance(chat, list):
            chat = "\n".join([str(item) for item in chat])  # Nếu là danh sách, nối các phần tử thành chuỗi
        elif isinstance(chat, dict):
            chat = str(chat)  # Nếu là từ điển, chuyển thành chuỗi
        elif not isinstance(chat, str):
            logging.error("Returned data is not valid: %s", type(chat))
            return "Lỗi: Dữ liệu trả về không phải là chuỗi văn bản hợp lệ."

        # Kiểm tra nếu chat không có dữ liệu hợp lệ
        if not chat or chat.strip() == "Tôi có thể giúp gì cho bạn về công ty?":
            logging.info(f"Không tìm thấy dữ liệu cho {user_input} trong data_vector. Đang tìm kiếm từ Google...")
            
            # Tìm kiếm từ Google và lưu kết quả vào file
            result = search_google_by_text(user_input)
            save_article_to_file(user_input, result)  # Lưu kết quả vào file
            logging.info(f"Kết quả đã được lưu lại với từ khóa: {user_input}")

            # Chuyển đổi các file .txt thành vector
            convert_txt_to_vector()
            logging.info("Quá trình chuyển đổi file .txt thành vector đã hoàn thành.")
            
            # Sau khi chuyển đổi, truy vấn lại và in ra kết quả
            chat = FilesChatAgent("demo/data_vector").get_workflow().compile().invoke(
                input={"question": user_input}
            )

            if isinstance(chat, list):
                chat = "\n".join([str(item) for item in chat])
            elif isinstance(chat, dict):
                chat = str(chat)

            logging.debug("Final chatbot response after conversion: %s", chat)

            return f"Chatbot đã trả lời với kết quả sau khi chuyển đổi vector: {chat}"
        else:
            logging.debug("Chatbot response from data_vector: %s", chat)
            return f"Chatbot đã trả lời với kết quả từ data_vector: {chat}"

    except Exception as e:
        logging.error(f"Lỗi trong quá trình xử lý chatbot: {str(e)}")
        return f"An error occurred while processing the chatbot: {str(e)}"

# API Flask để nhận câu hỏi từ Laravel và trả về kết quả chatbot
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    try:
        # Nhận câu hỏi từ yêu cầu POST (từ Laravel)
        user_input = request.json.get('user_input')
        if not user_input:
            return jsonify({"error": "No input provided"}), 400

        logging.debug("Processing user input: %s", user_input)

        # Gọi hàm run_chatbot từ chatbot.py để xử lý câu hỏi
        chatbot_response = run_chatbot(user_input)  # Chạy trực tiếp trong chatbot_api.py

        logging.debug("Chatbot response: %s", chatbot_response)

        return jsonify({"response": chatbot_response}), 200

    except Exception as e:
        logging.error("Error in chatbot: %s", str(e))
        return jsonify({"error": "An error occurred in chatbot API", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001)  # Chạy Flask trên cổng 5001

import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from flask import Flask, request, jsonify
import io
from PIL import Image
import logging
from googletrans import Translator
from flask_cors import CORS
from chatbot.services.files_chat_agent import FilesChatAgent  # Đảm bảo chatbot được tích hợp đúng cách
from app.config import Settings
from ingestion.ingestion import Ingestion
from chatbot.utils.llm import LLM  # LLM để tóm tắt
from download import search_google_by_text, save_article_to_file

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)

# Tải lại mô hình đã huấn luyện cho nhận diện phong cách kiến trúc
model = tf.keras.models.load_model('architecture.h5')

# Cấu hình đường dẫn tới thư mục chứa ảnh (thư mục đã được sử dụng khi huấn luyện)
train_dir = 'D:/api_base_public-main/Image/archi45_12'  # Thay '/path_to_data' bằng đường dẫn thư mục huấn luyện ảnh của bạn

# Lấy danh sách các lớp (nhãn) từ tên thư mục trong thư mục huấn luyện
class_labels = sorted(os.listdir(train_dir))

# Hàm tiền xử lý ảnh đầu vào
def preprocess_image(img):
    img = img.resize((150, 150))  # Kích thước cần thiết cho mô hình của bạn
    img_array = image.img_to_array(img)  # Chuyển ảnh thành mảng numpy
    img_array = img_array / 255.0  # Chuẩn hóa ảnh về phạm vi [0, 1]
    img_array = np.expand_dims(img_array, axis=0)  # Thêm chiều batch (mô hình yêu cầu input có batch dimension)
    return img_array

# Hàm nhận diện phong cách kiến trúc và trả về top 5 nhãn cùng xác suất
def predict_top_5_architecture_style(img):
    img_array = preprocess_image(img)
    prediction = model.predict(img_array)
    probabilities = prediction[0]
    
    top_5_indices = np.argsort(probabilities)[::-1][:5]
    top_5_labels = [class_labels[i] for i in top_5_indices]
    top_5_probs = [float(probabilities[i]) for i in top_5_indices]
    
    return top_5_labels, top_5_probs

# Hàm dịch văn bản sang tiếng Việt
def translate_to_vietnamese(text):
    translator = Translator()
    translated = translator.translate(text, src='en', dest='vi')
    return translated.text

# Hàm chuyển file .txt thành vector (sử dụng quá trình ingestion)
def convert_txt_to_vector():
    input_folder = "demo/data_in"
    vector_store_folder = "demo/data_vector"
    
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

        Settings.LLM_NAME = "gemini"  # Chuyển từ OpenAI sang Google Gemini (nếu cần)
        
        chat = FilesChatAgent("demo/data_vector").get_workflow().compile().invoke(
            input={"question": user_input}
        )

        logging.debug("Chatbot returned: %s", chat)

        if isinstance(chat, list):
            chat = "\n".join([str(item) for item in chat])
        elif isinstance(chat, dict):
            chat = str(chat)
        elif not isinstance(chat, str):
            logging.error("Returned data is not valid: %s", type(chat))
            return "Lỗi: Dữ liệu trả về không phải là chuỗi văn bản hợp lệ."

        if not chat or chat.strip() == "Tôi có thể giúp gì cho bạn về công ty?":
            logging.info(f"Không tìm thấy dữ liệu cho {user_input} trong data_vector. Đang tìm kiếm từ Google...")
            result = search_google_by_text(user_input)
            save_article_to_file(user_input, result)
            logging.info(f"Kết quả đã được lưu lại với từ khóa: {user_input}")
            
            convert_txt_to_vector()
            logging.info("Quá trình chuyển đổi file .txt thành vector đã hoàn thành.")
            
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

# Tạo ứng dụng Flask
app = Flask(__name__)
CORS(app)  # Cho phép CORS

# API nhận diện phong cách kiến trúc
@app.route('/api/detect', methods=['POST'])
def detect():
    file = request.files['image']
    
    if not file:
        return jsonify({"error": "No image uploaded"}), 400
    
    img = Image.open(io.BytesIO(file.read()))
    top_5_labels, top_5_probs = predict_top_5_architecture_style(img)
    
    return jsonify({
        'top_5_labels': top_5_labels,
        'top_5_probs': top_5_probs
    })

# API chatbot
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    try:
        user_input = request.json.get('user_input')
        if not user_input:
            return jsonify({"error": "No input provided"}), 400

        logging.debug("Processing user input: %s", user_input)
        chatbot_response = run_chatbot(user_input)  # Gọi chatbot.py

        logging.debug("Chatbot response: %s", chatbot_response)

        return jsonify({"response": chatbot_response}), 200

    except Exception as e:
        logging.error("Error in chatbot: %s", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)  # Chạy Flask trên cổng 5000

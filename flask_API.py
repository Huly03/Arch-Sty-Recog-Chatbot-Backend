import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from flask import Flask, request, jsonify
import io
from PIL import Image
from chatbox import run_chatbot  # Gọi chatbot.py

from googletrans import Translator
import logging

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)

# Tải lại mô hình đã huấn luyện cho nhận diện phong cách kiến trúc
model = tf.keras.models.load_model('architecture_VSCode.h5')

# Cấu hình đường dẫn tới thư mục chứa ảnh (thư mục đã được sử dụng khi huấn luyện)
train_dir = 'D:/api_base_public-main/Image/architecture'  # Thay '/path_to_data' bằng đường dẫn thư mục huấn luyện ảnh của bạn

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

# API Flask để nhận ảnh và trả kết quả nhận diện phong cách
app = Flask(__name__)

# Endpoint nhận diện phong cách kiến trúc
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

        # Gọi hàm run_chatbot từ chatbot.py để xử lý câu hỏi
        logging.debug("Processing user input: %s", user_input)
        chatbot_response = run_chatbot(user_input)  # Gọi chatbot.py

        logging.debug("Chatbot response: %s", chatbot_response)

        return jsonify({"response": chatbot_response}), 200

    except Exception as e:
        logging.error("Error in chatbot: %s", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)  # Chạy Flask trên cổng 5000

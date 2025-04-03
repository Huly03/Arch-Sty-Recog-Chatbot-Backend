import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt

# Tải lại mô hình đã huấn luyện
model = tf.keras.models.load_model('architecture_VSCode.h5')

# Cấu hình đường dẫn tới thư mục chứa ảnh (thư mục đã được sử dụng khi huấn luyện)
train_dir = 'D:/api_base_public-main/Image/architecture'  # Thay '/path_to_data' bằng đường dẫn thư mục huấn luyện ảnh của bạn

# Lấy danh sách các lớp (nhãn) từ tên thư mục trong thư mục huấn luyện
class_labels = sorted(os.listdir(train_dir))

# Hàm tiền xử lý ảnh đầu vào
def preprocess_image(img_path):
    # Tải ảnh và thay đổi kích thước về 150x150
    img = image.load_img(img_path, target_size=(150, 150))
    # Chuyển ảnh thành mảng numpy và chuẩn hóa
    img_array = image.img_to_array(img) / 255.0
    # Thêm chiều batch cho ảnh (vì mô hình yêu cầu input có batch size)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

# Hàm nhận diện phong cách kiến trúc và trả về top 5 nhãn cùng xác suất
def predict_top_5_architecture_style(img_path):
    img_array = preprocess_image(img_path)
    
    # Dự đoán lớp phong cách kiến trúc từ mô hình
    prediction = model.predict(img_array)
    
    # Lấy các xác suất và các nhãn
    probabilities = prediction[0]
    
    # Lấy top 5 nhãn với xác suất cao nhất
    top_5_indices = np.argsort(probabilities)[::-1][:5]
    top_5_labels = [class_labels[i] for i in top_5_indices]
    top_5_probs = [probabilities[i] for i in top_5_indices]
    
    return top_5_labels, top_5_probs, top_5_indices[0]

# Hàm duyệt qua các ảnh trong thư mục và hiển thị kết quả
def compare_images_from_folder(folder_path):
    # Lấy tất cả các file ảnh từ thư mục
    img_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    # Tạo một số lượng ảnh tối đa muốn hiển thị
    num_images = min(10, len(img_files))  # Lấy tối đa 10 ảnh từ thư mục

    # Tạo một số lượng subplot phù hợp
    fig, axes = plt.subplots(2, 5, figsize=(15, 8))  # 2 dòng và 5 cột
    axes = axes.ravel()  # Chuyển axes thành mảng 1 chiều để dễ dàng thao tác
    
    correct_predictions = 0
    total_predictions = 0

    # Duyệt qua các ảnh và nhận diện phong cách kiến trúc
    for i in range(num_images):
        img_file = img_files[i]
        img_path = os.path.join(folder_path, img_file)
        
        # Tìm phong cách thực tế từ tên ảnh (tên ảnh chứa phong cách kiến trúc)
        true_class = img_file.split('.')[0]  # Lấy phần tên trước dấu chấm của tên ảnh
        true_class = true_class.replace("_", " ").lower()  # Đảm bảo so sánh đúng, chuyển thành chữ thường và thay "_" thành dấu cách

        # Dự đoán top 5 phong cách kiến trúc của ảnh
        top_5_labels, top_5_probs, predicted_class_index = predict_top_5_architecture_style(img_path)
        
        # Kiểm tra nếu dự đoán đúng
        predicted_class = top_5_labels[0].lower()  # Chuyển dự đoán thành chữ thường để so sánh
        if predicted_class == true_class:  # So sánh giữa phong cách dự đoán và nhãn thực tế
            correct_predictions += 1

        total_predictions += 1
        
        # Hiển thị ảnh và kết quả dự đoán
        img = image.load_img(img_path, target_size=(150, 150))
        axes[i].imshow(img)
        axes[i].axis('off')  # Ẩn trục tọa độ
        axes[i].set_title(f"{top_5_labels[0]} ({top_5_probs[0] * 100:.2f}%)")

    # Tính tỷ lệ đúng
    accuracy = (correct_predictions / total_predictions) * 100
    print(f"Tỷ lệ chính xác: {accuracy:.2f}%")
    
    # Hiển thị toàn bộ hình ảnh trong một cửa sổ
    plt.tight_layout()
    plt.show()

# Chọn thư mục chứa ảnh từ cửa sổ dialog
root = tk.Tk()
root.withdraw()  # Ẩn cửa sổ chính của Tkinter
folder_path = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")

if folder_path:
    # So sánh các ảnh trong thư mục
    compare_images_from_folder(folder_path)
else:
    print("Bạn chưa chọn thư mục.")
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from PIL import Image

# Cấu hình đường dẫn tới thư mục chứa ảnh
train_dir = 'D:/api_base_public-main/Image/archi45_12'  # Đặt đường dẫn đúng tới thư mục chứa ảnh

# Tiền xử lý ảnh: chuẩn hóa kích thước ảnh và chuẩn hóa pixel từ 0-255 về 0-1
train_datagen = ImageDataGenerator(
    rescale=1./255,  # Chuyển đổi giá trị pixel về 0-1
    shear_range=0.2,  # Chỉnh sửa góc xoay ngẫu nhiên
    zoom_range=0.2,   # Phóng đại ngẫu nhiên
    horizontal_flip=True)  # Lật ngang ảnh ngẫu nhiên

train_generator = train_datagen.flow_from_directory(
    train_dir,  # Đường dẫn tới thư mục chứa ảnh
    target_size=(150, 150),  # Đặt lại kích thước ảnh về 150x150
    batch_size=32,  # Số ảnh trong mỗi batch
    class_mode='categorical')  # 'categorical' cho phân loại đa lớp

# Xây dựng mô hình CNN
model = models.Sequential()

# Thêm các lớp Conv2D và MaxPooling2D để trích xuất đặc trưng
model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(150, 150, 3)))
model.add(layers.MaxPooling2D((2, 2)))

model.add(layers.Conv2D(64, (3, 3), activation='relu'))
model.add(layers.MaxPooling2D((2, 2)))

model.add(layers.Conv2D(128, (3, 3), activation='relu'))
model.add(layers.MaxPooling2D((2, 2)))

# Làm phẳng và thêm lớp Dense để phân loại
model.add(layers.Flatten())
model.add(layers.Dense(128, activation='relu'))
model.add(layers.Dense(train_generator.num_classes, activation='softmax'))  # Số lớp bằng số thư mục trong dataset

# Biên dịch mô 
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Huấn luyện mô hình
history = model.fit(
    train_generator,
    steps_per_epoch=train_generator.samples // train_generator.batch_size,
    epochs=10)  # Chạy 10 vòng huấn luyện

# Lưu mô hình đã huấn luyện
model.save('architecture.h5')

print("Mô hình đã được lưu thành công!")

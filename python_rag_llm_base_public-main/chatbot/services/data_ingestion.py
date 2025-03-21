from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os

class DataIngestion:
    """
    Lớp DataIngestion chịu trách nhiệm nạp và chuyển đổi các tệp văn bản thành vector store.
    """

    def __init__(self, input_directory: str, output_directory: str, chunk_size: int = 500, chunk_overlap: int = 50, model_name: str = "sentence-transformers/paraphrase-MiniLM-L6-v2"):
        """
        Khởi tạo lớp DataIngestion với các tham số cấu hình.

        Args:
            input_directory (str): Thư mục chứa các tệp văn bản cần xử lý.
            output_directory (str): Thư mục lưu trữ vector store (FAISS).
            chunk_size (int): Kích thước đoạn văn bản.
            chunk_overlap (int): Độ chồng chéo giữa các đoạn văn bản.
            model_name (str): Tên mô hình embedding.
        """
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name

    def process_documents(self):
        """
        Nạp các tài liệu từ thư mục và chuyển đổi thành vector store.
        """
        # Nạp các tệp văn bản từ thư mục
        loader = DirectoryLoader(self.input_directory, glob='*.txt', loader_cls=lambda path: TextLoader(path, encoding='utf-8'))
        documents = loader.load()

        # Chia nhỏ các tài liệu thành các đoạn văn bản
        text_splitter = CharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        split_docs = text_splitter.split_documents(documents)

        # Chuyển các đoạn văn bản thành vector
        embedding_model = HuggingFaceEmbeddings(model_name=self.model_name)
        vector_db = FAISS.from_documents(split_docs, embedding_model)

        # Lưu vector store vào thư mục đích
        vector_db.save_local(self.output_directory)

        print("✅ Done - Vector store đã được lưu.")

# Sử dụng lớp DataIngestion
if __name__ == "__main__":
    input_dir = "demo/data_in"  # Đường dẫn tới thư mục chứa các tệp văn bản
    output_dir = "demo/data_vector"  # Đường dẫn lưu trữ vector store

    ingestion = DataIngestion(input_dir, output_dir)
    ingestion.process_documents()

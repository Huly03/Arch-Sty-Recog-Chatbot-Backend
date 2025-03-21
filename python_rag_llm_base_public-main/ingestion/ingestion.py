# ingestion.py
from ingestion.service_manager import ServiceManager
from langchain_community.vectorstores import FAISS
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader

class Ingestion:
    def __init__(self, embedding_model_name: str):
        self.chunk_size = 2000
        self.chunk_overlap = self.chunk_size * 0.2
        self.embedding_model = ServiceManager().get_embedding_model(embedding_model_name)

    def ingestion_folder(self, path_input_folder: str, path_vector_store: str):
        all_docs = []
        for root, dirs, files in os.walk(path_input_folder):
            for file in files:
                if file.endswith("txt"):  # Chỉ xử lý các bài báo dạng tệp văn bản
                    file_path = os.path.join(root, file)
                    docs = self.process_txt(file_path, self.chunk_size)
                    all_docs.extend(docs)

        # Lưu vào vector store
        vectorstore = FAISS.from_documents(all_docs, self.embedding_model)
        vectorstore.save_local(path_vector_store)

    def process_txt(self, path_file: str, chunk_size: int):
        documents = TextLoader(path_file, encoding="utf8")
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ".", ",", "", ],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        docs = documents.load_and_split(text_splitter=text_splitter)

        for idx, text in enumerate(docs):
            docs[idx].metadata["file_name"] = os.path.basename(path_file)
            docs[idx].metadata["chunk_size"] = chunk_size
        return docs

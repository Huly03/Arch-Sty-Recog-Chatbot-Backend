import faiss

# Tải chỉ mục FAISS
faiss_index = faiss.read_index('D:/CodePy/python_rag_llm_base_public-main/demo/data_vector/index.faiss')

# Kiểm tra chiều của chỉ mục
print(f"Chiều của chỉ mục FAISS: {faiss_index.d}")

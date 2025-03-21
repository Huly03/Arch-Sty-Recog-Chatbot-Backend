from langchain_community.vectorstores import FAISS
from ingestion.service_manager import ServiceManager
import requests
from bs4 import BeautifulSoup

class Retriever:
    """
    Lớp khởi tạo embedding_model và lấy documents.

    Attributes:
        embedding_model (Any): Mô hình embedding được lấy từ ServiceManager.
        faiss_fetch_k (int): Số lượng document tối đa được lấy trước khi lọc.
    """

    def __init__(self, embedding_model_name: str, faiss_fetch_k: int = 20):
        """
        Khởi tạo lớp Retriever với mô hình embedding.

        Args:
            embedding_model_name (str): Tên mô hình embedding.
            faiss_fetch_k (int, optional): Số lượng document tối đa lấy trước khi lọc. Mặc định là 20.
        """
        self.faiss_fetch_k = faiss_fetch_k
        self.embedding_model = ServiceManager().get_embedding_model(embedding_model_name)

    def set_retriever(self, path_vector_store: str):
        """
        Thiết lập Retriever bằng FAISS từ đường dẫn dữ liệu vector.

        Args:
            path_vector_store (str): Đường dẫn đến kho dữ liệu vector FAISS.

        Returns:
            Retriever: Đối tượng Retriever đã được thiết lập.
        """
        self.retriever = FAISS.load_local(path_vector_store, self.embedding_model, allow_dangerous_deserialization=True)
        return self

    def get_as_retriever(self):
        """
        Lấy đối tượng retriever từ FAISS.

        Returns:
            Any: Đối tượng retriever của FAISS.
        """
        faiss_retriever = self.retriever.as_retriever()
        return faiss_retriever

    def get_documents(self, query: str, num_doc: int = 5):
        """
        Nhận vào câu hỏi và trả về danh sách các document liên quan.

        Args:
            query (str): Câu hỏi cần tìm kiếm.
            num_doc (int, optional): Số lượng document cần lấy. Mặc định là 5.

        Returns:
            List[Any]: Danh sách các document liên quan.
        """
        docs = self.retriever.similarity_search(query, k=num_doc, fetch_k=self.faiss_fetch_k)
        return docs
    def search_architecture_style(self, style: str, num_results: int = 3):
        """
        Tìm kiếm bài viết về phong cách kiến trúc từ trang web.

        Args:
            style (str): Phong cách kiến trúc cần tìm kiếm.
            num_results (int): Số lượng kết quả cần lấy.

        Returns:
            list: Danh sách các bài viết liên quan đến phong cách kiến trúc.
        """
        query = style.replace(" ", "+")
        url = f"https://www.google.com/search?q={query}+architecture+style&num={num_results}"
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Lấy các liên kết bài viết từ kết quả tìm kiếm
        articles = []
        for g in soup.find_all('div', class_='BVG0Nb'):
            link = g.find('a')['href']
            title = g.find('h3').text if g.find('h3') else 'No title'
            articles.append({"title": title, "link": link})

        return articles
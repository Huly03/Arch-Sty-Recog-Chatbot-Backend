from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings


class ServiceManager:
    """
    Quản lý các dịch vụ liên quan đến embeddings.
    """

    def __init__(self) -> None:
        """
        Khởi tạo ServiceManager.
        """
        pass

    def get_embedding_model(self, embedding_model_name: str):
        if embedding_model_name == "gemini":
            return GoogleGenerativeAIEmbeddings(
                google_api_key=settings.KEY_API_GPT,
                model="models/embedding-001"
            )
        return None

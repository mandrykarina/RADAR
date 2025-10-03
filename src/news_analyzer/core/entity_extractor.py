from news_analyzer.models.data_models import ExtractedEntities
from news_analyzer.core.llm_client import LLMClient


class EntityExtractor:
    """Извлечение финансовых сущностей из новостей"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def extract_entities(self, news_text: str) -> ExtractedEntities:
        """Извлечение сущностей через LLM"""
        return await self.llm_client.extract_entities(news_text)
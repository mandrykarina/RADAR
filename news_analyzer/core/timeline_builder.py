from typing import List
from news_analyzer.models.data_models import TimelineEvent
from news_analyzer.core.llm_client import LLMClient


class TimelineBuilder:
    """Построение временной шкалы событий"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def build_timeline(self, news_articles: List) -> List[TimelineEvent]:
        """Построение timeline через LLM"""
        return await self.llm_client.build_timeline(news_articles)
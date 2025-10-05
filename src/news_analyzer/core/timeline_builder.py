"""Асинхронный построитель временных шкал для RADAR"""

import asyncio
from typing import List

from news_analyzer.models.data_models import TimelineEvent
from news_analyzer.core.llm_client import AsyncLLMClient

class TimelineBuilder:
    """Асинхронный построитель временных шкал"""

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm_client = llm_client

    async def build_timeline_async(self, news_articles: List) -> List[TimelineEvent]:
        """АСИНХРОННОЕ построение временной шкалы"""
        return await self.llm_client.build_timeline_async(news_articles)

    def build_timeline(self, news_articles: List) -> List[TimelineEvent]:
        """Синхронная обертка для совместимости"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.create_task(self.build_timeline_async(news_articles))
        else:
            return asyncio.run(self.build_timeline_async(news_articles))

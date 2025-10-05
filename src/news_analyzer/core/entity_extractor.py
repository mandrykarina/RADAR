"""Асинхронный экстрактор сущностей для RADAR с высокой производительностью"""

import asyncio
from typing import List

from news_analyzer.models.data_models import ExtractedEntities
from news_analyzer.core.llm_client import AsyncLLMClient

class EntityExtractor:
    """Асинхронный экстрактор сущностей с кешированием"""

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm_client = llm_client

    async def extract_entities_async(self, text: str) -> ExtractedEntities:
        """АСИНХРОННОЕ извлечение сущностей"""
        return await self.llm_client.extract_entities_async(text)

    def extract_entities(self, text: str) -> ExtractedEntities:
        """Синхронная обертка для совместимости"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.create_task(self.extract_entities_async(text))
        else:
            return asyncio.run(self.extract_entities_async(text))

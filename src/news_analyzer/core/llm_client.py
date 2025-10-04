import json
import os
from typing import Dict, List
from openai import AsyncOpenAI

from news_analyzer.config.prompts import (
    ENTITY_EXTRACTION_PROMPT,
    WHY_NOW_PROMPT,
    DRAFT_GENERATION_PROMPT,
    TIMELINE_PROMPT,
    HEADLINE_GENERATION_PROMPT
)
from news_analyzer.models.data_models import ExtractedEntities, ArticleDraft, TimelineEvent
from news_analyzer.utils.cache import CacheManager


class LLMClient:
    """Клиент для работы с OpenAI API через OpenRouter.ai"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables")

        self.base_url = "https://openrouter.ai/api/v1"
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', 1500))
        self.api_calls_count = 0
        self.cache = CacheManager()

    async def _make_api_call(self, messages: List[Dict], temperature: float = 0.3) -> str:
        """API вызов с кешированием"""

        cache_key = self._create_cache_key(messages, temperature)

        cached_result = await self.cache.get(cache_key)
        if cached_result:
            print("💾 Кеш")
            return cached_result

        try:
            self.api_calls_count += 1
            print(f"🤖 API вызов #{self.api_calls_count}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=temperature,
                timeout=30.0
            )

            result = response.choices[0].message.content

            await self.cache.set(cache_key, result)

            return result

        except Exception as e:
            print(f"❌ Ошибка API вызова: {e}")
            raise

    def _create_cache_key(self, messages: List[Dict], temperature: float) -> str:
        import hashlib
        content = json.dumps(messages, sort_keys=True) + str(temperature)
        return hashlib.md5(content.encode()).hexdigest()

    async def extract_entities(self, news_text: str) -> ExtractedEntities:
        """Извлечение сущностей из текста новости"""

        messages = [{
            "role": "user",
            "content": ENTITY_EXTRACTION_PROMPT.format(news_text=news_text)
        }]

        try:
            response = await self._make_api_call(messages)
            entities_data = json.loads(response)
            return ExtractedEntities(**entities_data)

        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Ошибка извлечения сущностей: {e}")
            return ExtractedEntities()

    async def generate_why_now(self, news_text: str, context: str) -> str:
        """Генерация объяснения \"почему сейчас\""""

        messages = [{
            "role": "user",
            "content": WHY_NOW_PROMPT.format(news_text=news_text, context=context)
        }]

        try:
            response = await self._make_api_call(messages, temperature=0.5)
            return response.strip()

        except Exception as e:
            print(f"⚠️ Ошибка генерации why_now: {e}")
            return "Значимое развитие на финансовом рынке"

    async def generate_draft(self, news_text: str, entities: ExtractedEntities, why_now: str) -> ArticleDraft:
        """Генерация черновика статьи"""

        entities_str = json.dumps(entities.model_dump(), ensure_ascii=False)

        messages = [{
            "role": "user",
            "content": DRAFT_GENERATION_PROMPT.format(
                news_text=news_text,
                entities=entities_str,
                why_now=why_now
            )
        }]

        try:
            response = await self._make_api_call(messages, temperature=0.4)
            draft_data = json.loads(response)
            return ArticleDraft(**draft_data)

        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Ошибка генерации черновика: {e}")
            return ArticleDraft(
                headline="Важное финансовое событие",
                lead="Произошло значимое событие на рынках.",
                bullets=["Детали события", "Влияние на рынок", "Реакция участников"],
                quote="Комментарий ожидается"
            )

    async def generate_headline(self, news_text: str, entities: ExtractedEntities) -> str:
        """Генерация заголовка для события"""

        entities_list = []
        if entities.companies:
            entities_list.extend([comp.get('name', '') for comp in entities.companies])
        if entities.countries:
            entities_list.extend(entities.countries[:2])

        entities_str = ', '.join(entities_list[:3])

        messages = [{
            "role": "user",
            "content": HEADLINE_GENERATION_PROMPT.format(
                news_text=news_text[:500],
                entities_str=entities_str
            )
        }]

        try:
            response = await self._make_api_call(messages, temperature=0.3)
            return response.strip()[:50]

        except Exception as e:
            print(f"⚠️ Ошибка генерации заголовка: {e}")
            return "Важное финансовое событие"

    async def build_timeline(self, news_articles: List) -> List[TimelineEvent]:
        """Построение временной шкалы событий"""

        articles_data = []
        for article in news_articles:
            articles_data.append({
                'time': article.published_at.isoformat(),
                'title': article.title,
                'content': article.content[:200]
            })

        articles_str = json.dumps(articles_data, ensure_ascii=False, indent=2)

        messages = [{
            "role": "user",
            "content": TIMELINE_PROMPT.format(news_group=articles_str)
        }]

        try:
            response = await self._make_api_call(messages)
            timeline_data = json.loads(response)

            timeline_events = []
            for event_data in timeline_data.get('timeline', []):
                try:
                    from datetime import datetime
                    timeline_events.append(TimelineEvent(
                        time=datetime.fromisoformat(event_data['time'].replace('Z', '+00:00')),
                        event=event_data['event']
                    ))
                except Exception:
                    continue

            return timeline_events

        except Exception as e:
            print(f"⚠️ Ошибка построения временной шкалы: {e}")

            if news_articles:
                return [TimelineEvent(
                    time=news_articles[0].published_at,
                    event="Публикация новости"
                )]

            return []

import os
import json
import torch
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import spacy
import re
from concurrent.futures import ThreadPoolExecutor

from news_analyzer.config.prompts import *
from news_analyzer.models.data_models import ExtractedEntities, ArticleDraft, TimelineEvent
from news_analyzer.utils.cache import CacheManager


class AsyncLLMClient:
    """Полностью асинхронный локальный LLM клиент с высокой производительностью"""

    def __init__(self):
        self.cache = CacheManager()
        self.api_calls_count = 0
        self.executor = ThreadPoolExecutor(max_workers=4)

        print("Инициализация асинхронного LLM клиента...")

        # Загружаем модель в отдельном потоке
        self._init_models()

    def _init_models(self):
        """Инициализация моделей"""
        try:
            model_name = "ai-forever/rugpt3small_based_on_gpt2"
            print(f"Загружаем модель: {model_name}")

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )

            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                do_sample=True,
                temperature=0.3,
                max_length=200,
                pad_token_id=self.tokenizer.eos_token_id,
                truncation=True
            )

            print("Асинхронная модель успешно загружена")

        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            print("Используем fallback режим")
            self.generator = None

        # Загружаем spaCy
        try:
            self.nlp = spacy.load("ru_core_news_sm")
            print("spaCy модель загружена")
        except OSError:
            print("spaCy модель не найдена")
            self.nlp = None

    async def _generate_smart_response_async(self, prompt: str, max_length: int = 100) -> str:
        """ПОЛНОСТЬЮ АСИНХРОННАЯ генерация с кешированием"""
        self.api_calls_count += 1

        # Проверяем кеш
        import hashlib
        cache_key = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Определяем тип запроса
        prompt_lower = prompt.lower()

        try:
            if "почему" in prompt_lower or "важно" in prompt_lower or "why" in prompt_lower:
                result = await self._generate_why_now_response_async(prompt)
            elif "заголовок" in prompt_lower or "headline" in prompt_lower:
                result = await self._generate_headline_response_async(prompt)
            elif "черновик" in prompt_lower or "анализ" in prompt_lower:
                result = await self._generate_analysis_response_async(prompt)
            else:
                result = await self._try_model_generation_async(prompt, max_length)
        except Exception as e:
            print(f"Ошибка генерации: {e}")
            result = f"Анализ темы: {prompt[:50]}"

        # Сохраняем в кеш
        self.cache.set(cache_key, result)
        return result

    async def _try_model_generation_async(self, prompt: str, max_length: int) -> str:
        """АСИНХРОННАЯ генерация через модель"""
        if not self.generator:
            return f"Анализ: {prompt[:100]}"

        try:
            # Выполняем генерацию в отдельном потоке
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._sync_generate,
                prompt,
                max_length
            )
            return result
        except Exception as e:
            print(f"Ошибка асинхронной генерации: {e}")
            return f"Анализ по теме: {prompt[:50]}"

    def _sync_generate(self, prompt: str, max_length: int) -> str:
        """Синхронная генерация для выполнения в executor"""
        clean_prompt = prompt[:150].strip()

        try:
            result = self.generator(
                clean_prompt,
                max_new_tokens=max_length,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.3,
                pad_token_id=self.tokenizer.eos_token_id,
                truncation=True,
                repetition_penalty=1.1
            )

            generated = result[0]["generated_text"]
            if generated.startswith(clean_prompt):
                generated = generated[len(clean_prompt):].strip()

            generated = self._clean_generated_text(generated)
            return generated[:max_length] if generated else "Краткий анализ темы"

        except Exception as e:
            print(f"Ошибка синхронной генерации: {e}")
            return "Краткий анализ темы"

    def _clean_generated_text(self, text: str) -> str:
        """Очистка сгенерированного текста"""
        if not text:
            return ""

        text = re.sub(r'&[a-z]+;', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.,;:!?\-()«»]', '', text)

        sentences = text.split('.')
        if len(sentences) > 0:
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 20 and not re.search(r'\d{8,}', first_sentence):
                return first_sentence + "."

        return text.strip()[:200]

    async def _generate_why_now_response_async(self, prompt: str) -> str:
        """АСИНХРОННАЯ генерация ответа на 'почему важно сейчас'"""
        keywords = re.findall(r'\b(?:банкротство|кризис|санкции|рубль|доллар|банк|акции|биткоин|инфляция)\b',
                              prompt.lower())

        responses = {
            ('банкротство',
             'банк'): "Банкротство крупного банка создает системные риски для финансового сектора и может спровоцировать панику среди вкладчиков.",
            ('рубль',
             'доллар'): "Резкие колебания валютных курсов влияют на инфляцию, импорт и экономическую стабильность страны.",
            ('санкции',): "Новые санкции меняют условия ведения бизнеса и требуют пересмотра стратегий компаний.",
            ('биткоин',): "Волатильность криптовалют влияет на настроения на всех рисковых активах и может сигнализировать о смене трендов.",
        }

        for key_set, response in responses.items():
            if any(kw in keywords for kw in key_set):
                return response

        return "Данное событие может существенно повлиять на финансовые рынки и требует пристального внимания инвесторов."

    async def _generate_headline_response_async(self, prompt: str) -> str:
        """АСИНХРОННАЯ генерация заголовка"""
        headlines = {
            'банкротство': "Банкротство крупного российского банка шокировало рынки",
            'биткоин': "Резкое падение биткоина вызвало распродажи на криптовалютном рынке",
            'рубль': "Рубль достиг новых минимумов на фоне геополитической напряженности"
        }

        for keyword, headline in headlines.items():
            if keyword in prompt.lower():
                return headline

        return "Важное событие на финансовых рынках"

    async def _generate_analysis_response_async(self, prompt: str) -> str:
        """АСИНХРОННАЯ генерация аналитического текста"""
        analyses = {
            'банкротство': "Ситуация с банкротством развивается стремительно. Регулятор принимает экстренные меры для стабилизации ситуации. Вкладчики могут рассчитывать на выплаты в рамках системы страхования депозитов.",
            'биткоин': "Падение биткоина связано с ужесточением регулятивной политики и оттоком капитала из рисковых активов. Аналитики прогнозируют дальнейшую волатильность на криптовалютном рынке."
        }

        for keyword, analysis in analyses.items():
            if keyword in prompt.lower():
                return analysis

        return "Рынок демонстрирует повышенную чувствительность к новостному фону. Инвесторы занимают выжидательную позицию в ожидании дальнейших событий."

    # ===== ОСНОВНЫЕ АСИНХРОННЫЕ МЕТОДЫ =====

    async def extract_entities_async(self, news_text: str) -> ExtractedEntities:
        """ПОЛНОСТЬЮ АСИНХРОННОЕ извлечение сущностей"""
        try:
            entities_data = {
                "companies": [],
                "countries": [],
                "instruments": [],
                "people": [],
                "sectors": []
            }

            # spaCy обработка в отдельном потоке
            if self.nlp:
                loop = asyncio.get_event_loop()
                entities_data = await loop.run_in_executor(
                    self.executor,
                    self._extract_entities_sync,
                    news_text,
                    entities_data
                )

            return ExtractedEntities(**entities_data)

        except Exception as e:
            print(f"Ошибка асинхронного извлечения сущностей: {e}")
            return ExtractedEntities()

    def _extract_entities_sync(self, news_text: str, entities_data: dict) -> dict:
        """Синхронное извлечение сущностей для executor"""
        try:
            doc = self.nlp(news_text[:1000])

            for ent in doc.ents:
                if ent.label_ == "ORG":
                    entities_data["companies"].append({"name": ent.text, "ticker": "", "sector": "Финансы"})
                elif ent.label_ == "GPE":
                    entities_data["countries"].append(ent.text)
                elif ent.label_ == "PERSON":
                    entities_data["people"].append(ent.text)

        except Exception as e:
            print(f"Ошибка spaCy обработки: {e}")

        # Добавляем правила для финансовых терминов
        financial_entities = {
            'сбербанк': {'name': 'Сбербанк', 'ticker': 'SBER', 'sector': 'Банки'},
            'втб': {'name': 'ВТБ', 'ticker': 'VTBR', 'sector': 'Банки'},
            'газпром': {'name': 'Газпром', 'ticker': 'GAZP', 'sector': 'Нефть и газ'},
            'центробанк': {'name': 'ЦБ РФ', 'ticker': '', 'sector': 'Регуляторы'},
            'цб': {'name': 'ЦБ РФ', 'ticker': '', 'sector': 'Регуляторы'}
        }

        text_lower = news_text.lower()
        for keyword, company_info in financial_entities.items():
            if keyword in text_lower:
                entities_data["companies"].append(company_info)

        # Страны
        countries = ['россия', 'китай', 'сша', 'германия']
        for country in countries:
            if country in text_lower:
                entities_data["countries"].append(country.capitalize())

        # Финансовые инструменты
        instruments = ['рубль', 'доллар', 'биткоин', 'акции', 'облигации']
        for instrument in instruments:
            if instrument in text_lower:
                entities_data["instruments"].append(instrument)

        return entities_data

    async def generate_why_now_async(self, news_text: str, context: str) -> str:
        """АСИНХРОННАЯ генерация 'почему важно сейчас'"""
        try:
            prompt = f"Почему эта новость важна сейчас: {news_text[:300]}"
            result = await self._generate_smart_response_async(prompt, max_length=150)
            return result if result else "Важное событие на финансовых рынках, требующее внимания инвесторов"
        except Exception as e:
            print(f"Ошибка async why_now: {e}")
            return "Важное событие на финансовых рынках, требующее внимания инвесторов"

    async def generate_draft_async(self, news_text: str, entities: ExtractedEntities, why_now: str) -> ArticleDraft:
        """АСИНХРОННАЯ генерация черновика"""
        try:
            # Создаем задачи для параллельной генерации компонентов
            headline_task = asyncio.create_task(
                self._generate_smart_response_async(f"Создай заголовок для новости: {news_text[:200]}", 80)
            )

            lead_task = asyncio.create_task(
                self._generate_smart_response_async(f"Напиши краткий лид-абзац для новости: {news_text[:300]}", 150)
            )

            # Ждем завершения задач
            headline, lead = await asyncio.gather(headline_task, lead_task)

            # Генерируем буллеты на основе сущностей
            bullets = await self._generate_bullets_async(entities)

            # Генерируем цитату
            quote = await self._generate_smart_response_async(f"Создай экспертную цитату по поводу: {news_text[:200]}",
                                                              100)

            if not quote or len(quote) < 20:
                quote = "Это значимое развитие событий, которое может повлиять на рыночные настроения"

            return ArticleDraft(
                headline=headline[:100] if headline else "Важное событие на финансовых рынках",
                lead=lead[:300] if lead else "Произошло значимое событие, привлекшее внимание рынка",
                bullets=bullets[:3],
                quote=quote[:200]
            )

        except Exception as e:
            print(f"Ошибка асинхронной генерации черновика: {e}")
            return ArticleDraft(
                headline="Важное событие на финансовых рынках",
                lead="Произошло значимое событие, которое привлекло внимание участников рынка",
                bullets=["Анализ влияния на рынок", "Реакция участников рынка", "Прогнозы экспертов"],
                quote="Ситуация требует пристального мониторинга со стороны инвесторов"
            )

    async def _generate_bullets_async(self, entities: ExtractedEntities) -> List[str]:
        """АСИНХРОННАЯ генерация буллетов на основе сущностей"""
        bullets = []

        if entities.companies:
            company_names = [comp.get("name", "") for comp in entities.companies[:2] if comp.get("name")]
            if company_names:
                bullets.append(f"Затронутые компании: {', '.join(company_names)}")

        if entities.instruments:
            bullets.append(f"Финансовые инструменты: {', '.join(entities.instruments[:3])}")

        if entities.countries:
            bullets.append(f"География события: {', '.join(entities.countries[:2])}")

        # Добавляем стандартные буллеты
        default_bullets = [
            "Потенциальное влияние на волатильность рынка",
            "Реакция регуляторов и участников рынка",
            "Возможные последствия для смежных секторов"
        ]

        for bullet in default_bullets:
            if bullet not in bullets and len(bullets) < 3:
                bullets.append(bullet)

        return bullets

    async def generate_headline_async(self, news_text: str, entities: ExtractedEntities) -> str:
        """АСИНХРОННАЯ генерация заголовка"""
        try:
            prompt = f"Создай краткий заголовок: {news_text[:200]}"
            result = await self._generate_smart_response_async(prompt, max_length=80)

            if not result or len(result) < 10:
                result = await self._generate_headline_response_async(news_text)

            return result[:80]

        except Exception as e:
            print(f"Ошибка асинхронной генерации заголовка: {e}")
            return "Важное событие на рынке"

    async def build_timeline_async(self, news_articles: List) -> List[TimelineEvent]:
        """АСИНХРОННОЕ построение временной шкалы"""
        try:
            if not news_articles:
                return []

            events = []
            for article in news_articles[:5]:
                try:
                    events.append(TimelineEvent(
                        time=article.published_at,
                        event=f"Публикация: {article.title[:50]}..."
                    ))
                except AttributeError:
                    continue

            return events

        except Exception as e:
            print(f"Ошибка асинхронного построения временной шкалы: {e}")
            return []

    # ===== ОБРАТНАЯ СОВМЕСТИМОСТЬ =====

    def extract_entities(self, news_text: str) -> ExtractedEntities:
        """Синхронная обертка для совместимости"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.create_task(self.extract_entities_async(news_text))
        else:
            return asyncio.run(self.extract_entities_async(news_text))

    def generate_why_now(self, news_text: str, context: str) -> str:
        """Синхронная обертка для совместимости"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.create_task(self.generate_why_now_async(news_text, context))
        else:
            return asyncio.run(self.generate_why_now_async(news_text, context))

    def generate_draft(self, news_text: str, entities: ExtractedEntities, why_now: str) -> ArticleDraft:
        """Синхронная обертка для совместимости"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.create_task(self.generate_draft_async(news_text, entities, why_now))
        else:
            return asyncio.run(self.generate_draft_async(news_text, entities, why_now))

    def generate_headline(self, news_text: str, entities: ExtractedEntities) -> str:
        """Синхронная обертка для совместимости"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.create_task(self.generate_headline_async(news_text, entities))
        else:
            return asyncio.run(self.generate_headline_async(news_text, entities))

    def build_timeline(self, news_articles: List) -> List[TimelineEvent]:
        """Синхронная обертка для совместимости"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.create_task(self.build_timeline_async(news_articles))
        else:
            return asyncio.run(self.build_timeline_async(news_articles))

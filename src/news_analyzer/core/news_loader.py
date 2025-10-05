"""Обновленный загрузчик новостей для нового JSON формата"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError

from news_analyzer.models.data_models import NewsData, NewsItem


class NewsLoader:
    """Загрузчик новостей с поддержкой нового формата входных данных"""

    def __init__(self):
        self.supported_formats = ['json']

    def load_json(self, file_path: str) -> NewsData:
        """Загрузка новостей из JSON файла в новом формате"""

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Проверяем формат данных
            if isinstance(data, list):
                # Новый формат - прямо массив новостей
                print(f"Обнаружен новый формат: массив из {len(data)} новостей")
                news_data = NewsData.from_list(data)

            elif isinstance(data, dict) and 'news' in data:
                # Старый формат с оберткой
                print(f"Обнаружен старый формат: {len(data.get('news', []))} новостей")
                news_items = []

                for old_item in data['news']:
                    # Конвертируем старый формат в новый
                    new_item = self._convert_old_to_new_format(old_item)
                    news_items.append(new_item)

                news_data = NewsData.from_list(news_items)

            else:
                raise ValueError("Неизвестный формат JSON файла")

            print(f"Загружено и валидировано {len(news_data.news)} новостей")
            return news_data

        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON: {e}")
        except ValidationError as e:
            raise ValueError(f"Ошибка валидации данных: {e}")
        except Exception as e:
            raise RuntimeError(f"Неожиданная ошибка при загрузке: {e}")

    def _convert_old_to_new_format(self, old_item: Dict[str, Any]) -> Dict[str, Any]:
        """Конвертация старого формата в новый"""

        # Извлекаем ID или генерируем
        item_id = old_item.get('id', f"legacy_{hash(old_item.get('title', ''))}")
        if isinstance(item_id, str) and not item_id.isdigit():
            item_id = abs(hash(item_id)) % 10000000

        # Базовая конвертация
        new_item = {
            'id': int(item_id),
            'title': old_item.get('title', 'Без заголовка'),
            'content': old_item.get('content'),
            'url': old_item.get('url', ''),
            'source': old_item.get('source', 'unknown'),
            'author': None,
            'language': 'ru',  # предполагаем русский по умолчанию
            'country': 'RU',
            'category': 'financial',
            'tags': old_item.get('keywords', []),
            'tickers': [],
            'keywords': old_item.get('keywords', []),
            'entities': old_item.get('entities', []),
            'sentiment': None,
            'relevance': None,
            'source_credibility': int(old_item.get('source_credibility', 0.7) * 10),
            'is_duplicate': -1,  # обрабатываем дубликаты позже
            'collected_at': datetime.now().isoformat(),
            'created_at': None,
            'updated_at': None,
            'published_at': old_item.get('published_at')
        }

        # Обрабатываем дубликаты
        if 'duplicate_group' in old_item:
            dup_group = old_item['duplicate_group']
            # Преобразуем строковый ID группы в числовой
            if isinstance(dup_group, str):
                new_item['is_duplicate'] = abs(hash(dup_group)) % 10000
            else:
                new_item['is_duplicate'] = -1

        return new_item

    def validate_news_format(self, data: List[Dict[str, Any]]) -> bool:
        """Валидация корректности формата новостей"""
        required_fields = ['id', 'title', 'url', 'source', 'collected_at']

        for item in data[:5]:  # проверяем первые 5 элементов
            for field in required_fields:
                if field not in item:
                    print(f"Отсутствует обязательное поле: {field}")
                    return False

        return True

    def get_statistics(self, news_data: NewsData) -> Dict[str, Any]:
        """Получение статистики по загруженным новостям"""

        if not news_data.news:
            return {"error": "Нет данных для анализа"}

        # Подсчет дубликатов
        duplicates = {}
        unique_count = 0

        for item in news_data.news:
            if item.is_duplicate == -1:
                unique_count += 1
            else:
                if item.is_duplicate not in duplicates:
                    duplicates[item.is_duplicate] = 0
                duplicates[item.is_duplicate] += 1

        # Источники
        sources = {}
        for item in news_data.news:
            source = item.source
            sources[source] = sources.get(source, 0) + 1

        # Языки
        languages = {}
        for item in news_data.news:
            lang = item.language or 'unknown'
            languages[lang] = languages.get(lang, 0) + 1

        # Категории
        categories = {}
        for item in news_data.news:
            cat = item.category
            categories[cat] = categories.get(cat, 0) + 1

        # Временной диапазон
        timestamps = [item.published_at for item in news_data.news if item.published_at]
        time_range = None
        if timestamps:
            time_range = {
                'earliest': min(timestamps).isoformat(),
                'latest': max(timestamps).isoformat(),
                'span_hours': (max(timestamps) - min(timestamps)).total_seconds() / 3600
            }

        return {
            'total_news': len(news_data.news),
            'unique_news': unique_count,
            'duplicate_groups': len(duplicates),
            'largest_duplicate_group': max(duplicates.values()) if duplicates else 0,
            'sources': dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]),
            'languages': languages,
            'categories': categories,
            'time_range': time_range,
            'avg_credibility': sum(item.source_credibility for item in news_data.news) / len(news_data.news),
            'has_content': sum(1 for item in news_data.news if item.content),
            'has_sentiment': sum(1 for item in news_data.news if item.sentiment is not None)
        }

    def filter_by_credibility(self, news_data: NewsData, min_credibility: int = 6) -> NewsData:
        """Фильтрация новостей по минимальному уровню доверия к источнику"""
        filtered_news = [
            item for item in news_data.news
            if item.source_credibility >= min_credibility
        ]

        print(
            f"Отфильтровано {len(filtered_news)} из {len(news_data.news)} новостей (credibility >= {min_credibility})")

        return NewsData(news=filtered_news, timestamp=news_data.timestamp)

    def filter_by_language(self, news_data: NewsData, languages: List[str]) -> NewsData:
        """Фильтрация новостей по языкам"""
        filtered_news = [
            item for item in news_data.news
            if item.language in languages or item.language is None
        ]

        print(f"Отфильтровано {len(filtered_news)} из {len(news_data.news)} новостей (языки: {languages})")

        return NewsData(news=filtered_news, timestamp=news_data.timestamp)

    def filter_by_category(self, news_data: NewsData, categories: List[str]) -> NewsData:
        """Фильтрация новостей по категориям"""
        filtered_news = [
            item for item in news_data.news
            if item.category in categories
        ]

        print(f"Отфильтровано {len(filtered_news)} из {len(news_data.news)} новостей (категории: {categories})")

        return NewsData(news=filtered_news, timestamp=news_data.timestamp)

    def deduplicate_news(self, news_data: NewsData) -> NewsData:
        """Дедупликация новостей - оставляем по одной из каждой группы дубликатов"""

        seen_groups = set()
        unique_news = []

        for item in news_data.news:
            if item.is_duplicate == -1:
                # Уникальная новость
                unique_news.append(item)
            elif item.is_duplicate not in seen_groups:
                # Первая из группы дубликатов
                unique_news.append(item)
                seen_groups.add(item.is_duplicate)

        print(f"После дедупликации: {len(unique_news)} из {len(news_data.news)} новостей")

        return NewsData(news=unique_news, timestamp=news_data.timestamp)

    def create_sample_data(self, output_path: str):
        """Создание тестовых данных в новом формате - НЕ ИСПОЛЬЗУЕТСЯ"""
        # Этот метод больше не нужен, так как у нас есть готовый test_news.json
        print("Используйте test_news.json для тестовых данных")
        pass
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from pydantic import ValidationError

from news_analyzer.models.data_models import NewsData, NewsItem


class NewsLoader:
    """Загрузчик и валидатор JSON файлов с новостями"""

    def load_json(self, file_path: str) -> NewsData:
        """Загрузка JSON файла"""

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Файл {file_path} не найден")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return self._validate_news_data(data)

        except json.JSONDecodeError as e:
            raise ValueError(f"Некорректный JSON: {e}")
        except ValidationError as e:
            raise ValueError(f"Ошибка валидации: {e}")

    def _validate_news_data(self, data: Dict[str, Any]) -> NewsData:
        """Валидация и конвертация данных"""

        # Конвертация timestamp
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(
                data['timestamp'].replace('Z', '+00:00')
            )

        news_items = []

        for news_dict in data.get('news', []):
            # Конвертация дат
            if isinstance(news_dict.get('published_at'), str):
                news_dict['published_at'] = datetime.fromisoformat(
                    news_dict['published_at'].replace('Z', '+00:00')
                )

            if isinstance(news_dict.get('collected_at'), str):
                news_dict['collected_at'] = datetime.fromisoformat(
                    news_dict['collected_at'].replace('Z', '+00:00')
                )

            try:
                news_item = NewsItem(**news_dict)
                news_items.append(news_item)
            except ValidationError as e:
                print(f"⚠️ Пропуск некорректной новости {news_dict.get('id')}: {e}")
                continue

        return NewsData(timestamp=data['timestamp'], news=news_items)

    def create_sample_data(self, output_path: str):
        """Создание тестовых данных"""

        sample_data = {
            "timestamp": datetime.now().isoformat(),
            "news": [
                {
                    "id": "sample_1",
                    "source": "NewsAPI_bloomberg",
                    "source_credibility": 0.9,
                    "title": "ЦБ РФ неожиданно повысил ключевую ставку до 21%",
                    "content": "Центральный банк России принял решение повысить ключевую ставку с 19% до 21% годовых. Решение стало неожиданным для большинства аналитиков рынка. Повышение связано с ускорением инфляции и необходимостью охлаждения экономики. Рубль укрепился на 2% после объявления.",
                    "url": "https://bloomberg.com/news/cb-rate-increase",
                    "published_at": datetime.now().isoformat(),
                    "keywords": ["ЦБ", "ставка", "инфляция", "рубль"],
                    "entities": ["ЦБ РФ", "Россия", "рубль"],
                    "collected_at": datetime.now().isoformat(),
                    "dedup_hash": "hash_cb_rate",
                    "credibility_score": 0.85,
                    "confirmation_count": 3,
                    "duplicate_group": "cb_rate_oct2025"
                },
                {
                    "id": "sample_2",
                    "source": "NewsAPI_reuters",
                    "source_credibility": 0.95,
                    "title": "Apple объявила о поглощении ИИ-стартапа за $5 млрд",
                    "content": "Компания Apple подтвердила приобретение стартапа в области искусственного интеллекта за 5 миллиардов долларов. Сделка направлена на укрепление позиций в области машинного обучения и голосовых помощников. Акции Apple выросли на 3% после объявления.",
                    "url": "https://reuters.com/apple-ai-acquisition",
                    "published_at": datetime.now().isoformat(),
                    "keywords": ["Apple", "поглощение", "ИИ", "стартап"],
                    "entities": ["Apple Inc.", "AAPL", "США"],
                    "collected_at": datetime.now().isoformat(),
                    "dedup_hash": "hash_apple_ai",
                    "credibility_score": 0.9,
                    "confirmation_count": 2,
                    "duplicate_group": "apple_ai_oct2025"
                }
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)

        print(f"📝 Тестовые данные созданы: {output_path}")
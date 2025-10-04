import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from newspaper import Article
from langdetect import detect
import re
from collections import Counter


# === Папка для хранения нормализованных файлов ===
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "normalized"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# === Карта доверия источников ===
SOURCE_CREDIBILITY = {
    "newsdata": 1,
    "marketaux": 2,
    "newsapi": 3,
    "polygon": 4,
    "finnhub": 5
}


# === Хелпер: генерация ID ===
def generate_id(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# === Хелпер: ключевые слова ===
def extract_keywords(text: str, top_n: int = 10) -> list:
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    common = Counter(words).most_common(top_n)
    return [w for w, _ in common]


# === Шаг 1: загрузка текста по URL ===
def enrich_news_item(news: dict) -> dict:
    """Скачивает текст статьи по URL и дополняет поля."""
    url = news.get("url")
    if not url:
        return news

    try:
        article = Article(url)
        article.download()
        article.parse()

        # Контент
        if not news.get("content") or len(news["content"]) < 100:
            news["content"] = article.text or None

        # Автор
        if not news.get("author"):
            news["author"] = ", ".join(article.authors) if article.authors else None

        # Язык
        if not news.get("language"):
            try:
                news["language"] = detect(article.text[:500]) if article.text else None
            except:
                news["language"] = None

        # Категория (простейшая эвристика по URL)
        if not news.get("category"):
            if "crypto" in url:
                news["category"] = "crypto"
            elif "stock" in url:
                news["category"] = "stocks"
            elif "economy" in url:
                news["category"] = "economy"
            else:
                news["category"] = None

        # Ключевые слова
        if not news.get("keywords"):
            news["keywords"] = extract_keywords(news.get("content", ""), 8)

        # Обновляем время
        news["updated_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        print(f"⚠️ Ошибка загрузки {url[:50]}...: {e}")

    return news


# === Шаг 2: нормализация новости ===
def normalize_news_item(item: dict, source_name: str) -> Dict[str, Any]:
    """Приведение новости к единому формату"""
    unique_str = f"{item.get('title','')}_{item.get('url','')}_{source_name}"
    uid = generate_id(unique_str)

    normalized = {
        "id": uid,
        "title": item.get("title") or None,
        "content": item.get("content") or item.get("description") or None,
        "url": item.get("url") or None,
        "source": source_name,

        "author": item.get("author") or None,
        "language": item.get("language") or None,
        "country": item.get("country") or None,
        "category": item.get("category") or None,
        "tags": item.get("tags") or [],
        "tickers": item.get("tickers") or [],
        "keywords": item.get("keywords") or [],
        "entities": item.get("entities") or [],

        "sentiment": None,
        "relevance": None,
        "hotness": None,

        "source_credibility": SOURCE_CREDIBILITY.get(source_name.lower(), None),
        "credibility_score": None,
        "is_duplicate": -1,

        "collected_at": datetime.utcnow().isoformat(),
        "created_at": None,
        "updated_at": None,
        "published_at": item.get("published_at") or None
    }

    return normalized


# === Шаг 3: пакетная нормализация и сохранение ===
def normalize_batch(raw_data: List[dict], source_name: str, save: bool = True):
    normalized = []
    for item in raw_data:
        norm = normalize_news_item(item, source_name)
        enriched = enrich_news_item(norm)   # <--- ДОПОЛНЕНИЕ
        normalized.append(enriched)

    if save:
        out_file = DATA_DIR / f"normalized_{source_name}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)
        print(f"✅ Сохранено {len(normalized)} новостей → {out_file}")

    return normalized


# === Для ручного теста ===
if __name__ == "__main__":
    # Тестовая новость
    sample = [{
        "title": "Test article about Bitcoin market crash",
        "url": "https://www.cnbc.com/2025/10/04/week-in-review-stocks-jump-despite-shutdown-we-bought-more-of-our-newest-stocks.html",
        "description": "Market crash expected...",
        "published_at": "2025-10-04T12:00:00Z"
    }]

    normalize_batch(sample, "marketaux", save=True)

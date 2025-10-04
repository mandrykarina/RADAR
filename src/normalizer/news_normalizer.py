import os
import json
import hashlib
import time
from datetime import datetime, timezone
from uuid import uuid4
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from langdetect import detect
from collections import Counter
import re

# === Папки ===
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PARSER_DIR = os.path.join(BASE_DIR, "parser")
DATA_DIR = os.path.join(BASE_DIR, "data")
NORMALIZED_DIR = os.path.join(DATA_DIR, "normalized")

os.makedirs(PARSER_DIR, exist_ok=True)
os.makedirs(NORMALIZED_DIR, exist_ok=True)

# === Scraper API (для обхода 401/403) ===
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
SCRAPER_API_URL = f"https://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url=" if SCRAPER_API_KEY else None

# === Уровни доверия источникам ===
SOURCE_CREDIBILITY = {
    "newsdata": 1,
    "marketaux": 2,
    "newsapi": 3,
    "polygon": 4,
    "finnhub": 5
}


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def generate_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def extract_keywords(text: str, top_n: int = 10) -> list:
    """Простое выделение ключевых слов по частоте"""
    text = re.sub(r"[^a-zA-Zа-яА-Я\s]", "", text)
    words = text.lower().split()
    stop_words = {"the", "and", "for", "that", "this", "with", "from", "was", "were", "will", "have", "has", "are"}
    words = [w for w in words if len(w) > 3 and w not in stop_words]
    return [w for w, _ in Counter(words).most_common(top_n)]


def is_truncated_text(text: str) -> bool:
    """Проверяет, усечён ли текст (есть многоточие или фраза [+123 chars])"""
    if not text:
        return True
    if len(text.strip()) < 200:
        return True
    if "..." in text.strip()[-10:]:
        return True
    if re.search(r"\[\+\d+\schars\]", text):
        return True
    return False


def enrich_from_url(article: dict) -> dict:
    """Скачивает текст новости по URL и дополняет недостающие поля"""
    url = article.get("url")
    if not url:
        return article

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }

    # === 1️⃣ Newspaper3k ===
    try:
        art = Article(url)
        art.download()
        art.parse()
        if art.text and len(art.text) > 200:
            article["content"] = art.text.strip()
            if art.authors:
                article["author"] = ", ".join(art.authors)
            if art.publish_date:
                article["published_at"] = art.publish_date.isoformat()

            if not article.get("language"):
                try:
                    article["language"] = detect(art.text[:500])
                except:
                    pass

            article["keywords"] = extract_keywords(art.text)
            print(f"✅ Newspaper3k извлек {len(art.text)} символов из {url[:60]}...")
            return article
    except Exception:
        pass

    # === 2️⃣ Requests + BeautifulSoup ===
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            paragraphs = [p.get_text() for p in soup.find_all("p")]
            text = "\n".join(paragraphs).strip()
            if text:
                article["content"] = text
                article["keywords"] = extract_keywords(text)
                if not article.get("language"):
                    try:
                        article["language"] = detect(text[:500])
                    except:
                        pass
                print(f"✅ BeautifulSoup извлёк {len(text)} символов из {url[:60]}...")
                return article
        elif resp.status_code in (401, 403) and SCRAPER_API_URL:
            # === 3️⃣ ScraperAPI ===
            print(f"⚠️ 401 для {url[:60]}... → ScraperAPI")
            scraper_url = SCRAPER_API_URL + url
            r2 = requests.get(scraper_url, headers=headers, timeout=15)
            if r2.status_code == 200:
                soup = BeautifulSoup(r2.text, "html.parser")
                paragraphs = [p.get_text() for p in soup.find_all("p")]
                text = "\n".join(paragraphs).strip()
                if text:
                    article["content"] = text
                    article["keywords"] = extract_keywords(text)
                    if not article.get("language"):
                        try:
                            article["language"] = detect(text[:500])
                        except:
                            pass
                    print(f"✅ ScraperAPI успешно получил текст ({len(text)} символов)")
                    return article
            else:
                print(f"⚠️ ScraperAPI не помог ({r2.status_code}) для {url[:60]}...")
        else:
            print(f"⚠️ HTTP {resp.status_code} для {url[:60]}...")
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке {url[:60]}...: {e}")

    # === 4️⃣ fallback — хотя бы description ===
    if not article.get("content") and article.get("description"):
        article["content"] = article["description"]

    return article


# === ОСНОВНАЯ НОРМАЛИЗАЦИЯ ===

def normalize_article(article: dict, source: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    uid = article.get("id") or generate_hash(article.get("url", str(uuid4())))
    content = article.get("content") or article.get("description") or None

    normalized = {
        "id": uid,
        "title": article.get("title") or article.get("headline") or None,
        "content": content,
        "url": article.get("url") or None,
        "source": source,
        "author": article.get("author") or None,
        "language": article.get("language") or None,
        "country": article.get("country") or None,
        "category": article.get("category") or None,
        "tags": article.get("tags") or [],
        "tickers": article.get("tickers") or [],
        "keywords": article.get("keywords") or [],
        "entities": article.get("entities") or [],
        "sentiment": None,
        "relevance": None,
        "hotness": None,
        "source_credibility": SOURCE_CREDIBILITY.get(source.lower(), None),
        "credibility_score": None,
        "is_duplicate": -1,
        "collected_at": now,
        "created_at": None,
        "updated_at": None,
        "published_at": article.get("published_at") or None,
    }

    # 🚀 Новый фильтр: проверяем, обрезан ли текст
    if is_truncated_text(normalized["content"]):
        normalized = enrich_from_url(normalized)

    return normalized


def load_articles(file_path: str) -> list:
    """Загружает статьи из JSON"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "filtered_articles" in data:
                return data["filtered_articles"]
            if "raw_data" in data and isinstance(data["raw_data"], dict):
                return data["raw_data"].get("articles", [])
        return []
    except Exception as e:
        print(f"⚠️ Ошибка чтения {file_path}: {e}")
        return []


def normalize_file(input_path: str, output_path: str, source: str):
    """Обрабатывает один JSON-файл"""
    articles = load_articles(input_path)
    normalized = [normalize_article(a, source) for a in articles]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
    print(f"💾 [{source}] {len(normalized)} новостей → {output_path}")


def main(cycles: int = 2, delay: int = 5):
    """Запускает циклическую нормализацию"""
    sources = {
        "newsapi": ("news_newsapi_latest.json", "newsapi.json"),
        "polygon": ("news_polygon_latest.json", "polygon.json"),
        "finnhub": ("news_finnhub_latest.json", "finnhub.json"),
        "marketaux": ("news_marketaux_latest.json", "marketaux.json"),
        "newsdata": ("news_newsdata_latest.json", "newsdata.json"),
    }

    for cycle in range(1, cycles + 1):
        print(f"\n🔁 ЦИКЛ {cycle}/{cycles} ({datetime.now(timezone.utc).strftime('%H:%M:%S')})")
        for source, (input_name, output_name) in sources.items():
            input_path = os.path.join(PARSER_DIR, input_name)
            output_path = os.path.join(NORMALIZED_DIR, output_name)
            normalize_file(input_path, output_path, source)
        if cycle < cycles:
            print(f"⏳ Пауза {delay} сек...\n")
            time.sleep(delay)
    print("\n✅ Все файлы сохранены в data/normalized/")


if __name__ == "__main__":
    main()

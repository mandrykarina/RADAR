# news_normalizer.py
import hashlib
from datetime import datetime
from typing import Dict, Any, List


class NewsNormalizer:
    """Приведение новостей из разных API к единому формату"""

    @staticmethod
    def _make_id(source: str, title: str, url: str) -> str:
        """Создаём хэш-ID (в БД у тебя SERIAL, но для JSON нужен уникальный ключ)"""
        raw_id = f"{source}:{title}:{url}"
        return hashlib.md5(raw_id.encode("utf-8")).hexdigest()

    @staticmethod
    def _now() -> str:
        """Текущее время в ISO"""
        return datetime.utcnow().isoformat()

    @staticmethod
    def _parse_date(date_str: str) -> str:
        try:
            if not date_str:
                return None
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).isoformat()
        except Exception:
            return None

    @classmethod
    def _base(cls, source: str, title: str, url: str, published_at: str) -> Dict[str, Any]:
        """Базовая структура"""
        now = cls._now()
        return {
            "id": cls._make_id(source, title or "", url or ""),
            "title": title,
            "url": url,
            "source": source,
            "publisher": None,
            "content": None,
            "description": None,
            "author": None,
            "source_name": None,
            "language": "en",
            "country": None,
            "category": None,
            "tags": [],
            "tickers": [],
            "sentiment": 0.0,
            "relevance": 0.0,
            "hotness": 0.0,
            "is_duplicate": False,
            "created_at": now,    # время попадания в систему
            "updated_at": now,
            "published_at": published_at or now
        }

    @classmethod
    def normalize_newsapi(cls, article: Dict[str, Any]) -> Dict[str, Any]:
        base = cls._base("newsapi", article.get("title"), article.get("url"),
                         cls._parse_date(article.get("publishedAt")))
        base.update({
            "description": article.get("description"),
            "content": article.get("content"),
            "author": article.get("author"),
            "source_name": article.get("source", {}).get("name")
        })
        return base

    @classmethod
    def normalize_polygon(cls, article: Dict[str, Any]) -> Dict[str, Any]:
        base = cls._base("polygon", article.get("title"), article.get("article_url"),
                         cls._parse_date(article.get("published_utc")))
        base.update({
            "description": article.get("description"),
            "content": article.get("summary"),
            "source_name": article.get("publisher", {}).get("name"),
            "tickers": article.get("tickers", [])
        })
        return base

    @classmethod
    def normalize_finnhub(cls, article: Dict[str, Any]) -> Dict[str, Any]:
        base = cls._base("finnhub", article.get("headline"), article.get("url"),
                         cls._parse_date(str(article.get("datetime"))))
        base.update({
            "description": article.get("summary"),
            "content": article.get("summary"),
            "source_name": article.get("source"),
            "tickers": [article.get("related")] if article.get("related") else []
        })
        return base

    @classmethod
    def normalize_fmp(cls, article: Dict[str, Any]) -> Dict[str, Any]:
        base = cls._base("fmp", article.get("title"), article.get("url"),
                         cls._parse_date(article.get("publishedDate")))
        base.update({
            "description": article.get("text"),
            "content": article.get("text"),
            "source_name": article.get("site"),
            "tickers": article.get("tickers", [])
        })
        return base

    @classmethod
    def normalize_newsdata(cls, article: Dict[str, Any]) -> Dict[str, Any]:
        base = cls._base("newsdata", article.get("title"), article.get("link"),
                         cls._parse_date(article.get("pubDate")))
        base.update({
            "description": article.get("description"),
            "content": article.get("content"),
            "source_name": article.get("source_id"),
            "language": article.get("language")
        })
        return base


def normalize_batch(source: str, data) -> List[Dict[str, Any]]:
    """Нормализация пачки новостей (берём только 20)"""
    normalizer_map = {
        "newsapi": NewsNormalizer.normalize_newsapi,
        "polygon": NewsNormalizer.normalize_polygon,
        "finnhub": NewsNormalizer.normalize_finnhub,
        "fmp": NewsNormalizer.normalize_fmp,
        "newsdata": NewsNormalizer.normalize_newsdata,
    }

    normalize_func = normalizer_map[source]
    articles = []

    if isinstance(data, dict):
        if source == "newsapi":
            articles = data.get("articles", [])
        elif source in ["polygon", "newsdata"]:
            articles = data.get("results", [])
    elif isinstance(data, list):
        articles = data

    return [normalize_func(article) for article in articles[:20]]

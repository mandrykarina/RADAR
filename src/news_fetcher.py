#!/usr/bin/env python3

import time
import json
import os
import threading
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List

from clients.newsapi_client import NewsApiClient
from clients.polygon_client import PolygonClient
from clients.finnhub_client import FinnHubClient
from clients.marketaux_client import MarketAuxClient  # ЗАМЕНИЛ twelve_data
from clients.newsdata_client import NewsDataClient

from config import API_KEYS, RATE_LIMITS, CONTENT_FILTERS, FILTER_SETTINGS, SEARCH_CONFIG


class SurgicalTwelveDataFetcher:
    def __init__(self):
        print("News Fetcher starting...")
        self.clients = {}
        self.request_counts = {
            'newsapi': 0, 'polygon': 0, 'finnhub': 0,
            'marketaux': 0,  # ЗАМЕНИЛ twelve_data
            'newsdata': 0
        }
        self.last_requests = {
            'newsapi': datetime.min, 'polygon': datetime.min, 'finnhub': datetime.min,
            'marketaux': datetime.min,  # ЗАМЕНИЛ twelve_data
            'newsdata': datetime.min
        }
        self.fixed_filenames = {
            'newsapi': 'news_newsapi_latest.json',
            'polygon': 'news_polygon_latest.json',
            'finnhub': 'news_finnhub_latest.json',
            'marketaux': 'news_marketaux_latest.json',  # ЗАМЕНИЛ twelve_data
            'newsdata': 'news_newsdata_latest.json'
        }
        self._init_clients()
        print(f"Clients ready: {len(self.clients)}")

    def _init_clients(self):
        apis = [
            ('newsapi', NewsApiClient),
            ('polygon', PolygonClient),
            ('finnhub', FinnHubClient),
            ('marketaux', MarketAuxClient),  # ЗАМЕНИЛ twelve_data
            ('newsdata', NewsDataClient)
        ]

        for api_name, ClientClass in apis:
            try:
                key = API_KEYS.get(api_name, "")
                if key and not key.startswith("YOUR_"):
                    self.clients[api_name] = ClientClass(key)
                    print(f"{api_name.upper()}")
            except Exception as e:
                print(f"{api_name.upper()}: {e}")

    def can_make_request(self, api_name: str) -> bool:
        try:
            now = datetime.now()
            last = self.last_requests[api_name]
            passed = (now - last).total_seconds()
            return passed >= RATE_LIMITS.get(api_name, 60)
        except:
            return True

    def apply_content_filters(self, articles: List[Dict], api_name: str) -> List[Dict]:
        if not FILTER_SETTINGS.get("apply_filters", True):
            return articles
        if not articles:
            return articles

        filtered_articles = []
        exclude_keywords = [kw.lower() for kw in CONTENT_FILTERS.get("exclude_keywords", [])]
        priority_keywords = [kw.lower() for kw in CONTENT_FILTERS.get("priority_keywords", [])]
        min_title_len = CONTENT_FILTERS.get("min_title_length", 15)
        max_title_len = CONTENT_FILTERS.get("max_title_length", 200)
        min_desc_len = CONTENT_FILTERS.get("min_description_length", 20)

        for article in articles:
            try:
                title = ""
                description = ""

                if api_name == "newsapi":
                    title = article.get("title", "") or ""
                    description = article.get("description", "") or ""
                elif api_name == "polygon":
                    title = article.get("title", "") or ""
                    description = article.get("description", "") or ""
                elif api_name == "finnhub":
                    title = article.get("headline", "") or ""
                    description = article.get("summary", "") or ""
                elif api_name == "marketaux":
                    title = article.get("title", "") or ""
                    description = article.get("description", "") or ""
                elif api_name == "newsdata":
                    title = article.get("title", "") or ""
                    description = article.get("description", "") or ""

                if not title:
                    continue

                title_lower = title.lower()
                desc_lower = description.lower() if description else ""

                # Фильтр 1: Длина заголовка
                if len(title) < min_title_len or len(title) > max_title_len:
                    continue

                # Фильтр 2: Минимальная длина описания
                if description and len(description) < min_desc_len:
                    continue

                # Фильтр 3: Исключаемые слова
                if any(exclude_word in title_lower for exclude_word in exclude_keywords):
                    continue
                if description and any(exclude_word in desc_lower for exclude_word in exclude_keywords):
                    continue

                # Фильтр 4: Приоритетные новости
                if FILTER_SETTINGS.get("mark_priority", True):
                    if any(priority_word in title_lower for priority_word in priority_keywords):
                        article["_priority"] = True

                filtered_articles.append(article)

            except Exception:
                continue

        # Сортировка по приоритету
        if FILTER_SETTINGS.get("sort_by_priority", True):
            filtered_articles.sort(key=lambda x: x.get("_priority", False), reverse=True)

        return filtered_articles

    def fetch_with_timeout(self, api_name: str) -> Dict[str, Any]:
        result = {"source": api_name, "error": "timeout", "articles_count": 0}

        def _fetch():
            nonlocal result
            try:
                print(f"{api_name.upper()}...", end=" ", flush=True)

                if api_name == "newsapi":
                    config = SEARCH_CONFIG.get("newsapi", {})
                    to_date = datetime.now()
                    from_date = to_date - timedelta(hours=24)
                    data = self.clients["newsapi"].get_everything(
                        q=config.get("query", "finance"),
                        language=config.get("language", "en"),
                        from_param=from_date.strftime("%Y-%m-%d"),
                        to=to_date.strftime("%Y-%m-%d"),
                        page_size=config.get("page_size", 15)
                    )
                elif api_name == "polygon":
                    config = SEARCH_CONFIG.get("polygon", {})
                    data = self.clients["polygon"].get_market_news(
                        limit=config.get("limit", 8)
                    )
                elif api_name == "finnhub":
                    config = SEARCH_CONFIG.get("finnhub", {})
                    data = self.clients["finnhub"].general_news(
                        config.get("category", "general")
                    )
                elif api_name == "marketaux":
                    config = SEARCH_CONFIG.get("marketaux", {})
                    data = self.clients["marketaux"].get_latest_news(
                        limit=config.get("limit", 50)
                    )
                elif api_name == "newsdata":
                    config = SEARCH_CONFIG.get("newsdata", {})
                    data = self.clients["newsdata"].latest_news(
                        category="business",
                        size=config.get("size", 8)
                    )

                # СОХРАНЯЕМ ВСЁ: исходные данные И отфильтрованные

                # 1. Извлекаем статьи для фильтрации
                articles = []
                if api_name == "marketaux":
                    articles = data if isinstance(data, list) else []
                elif isinstance(data, dict):
                    if api_name == "newsapi":
                        articles = data.get("articles", [])
                    elif api_name in ["polygon", "newsdata"]:
                        articles = data.get("results", [])
                elif isinstance(data, list):
                    articles = data

                # 2. Применяем фильтры
                filtered_articles = self.apply_content_filters(articles, api_name)
                priority_count = len([a for a in filtered_articles if a.get("_priority", False)])

                # 3. СОЗДАЁМ ПОЛНЫЙ РЕЗУЛЬТАТ СО ВСЕЙ ИНФОРМАЦИЕЙ
                result = {
                    "source": api_name,
                    "timestamp": datetime.now().isoformat(),
                    "total_articles_from_api": len(articles),  # <- НОВОЕ: сколько дал API
                    "filtered_articles_count": len(filtered_articles),  # <- НОВОЕ: сколько прошло фильтры
                    "filtered_out_count": len(articles) - len(filtered_articles),  # <- НОВОЕ: сколько убрано
                    "priority_articles_count": priority_count if priority_count > 0 else 0,  # <- НОВОЕ

                    # ПОЛНЫЕ ИСХОДНЫЕ ДАННЫЕ ОТ API (БЕЗ ИЗМЕНЕНИЙ)
                    "raw_api_response": data,  # <- НОВОЕ: всё что вернул API

                    # ОТФИЛЬТРОВАННЫЕ ДАННЫЕ
                    "filtered_articles": filtered_articles,  # <- НОВОЕ: только прошедшие фильтры

                    # МЕТАДАННЫЕ ФИЛЬТРАЦИИ
                    "filter_settings_used": {  # <- НОВОЕ: какие фильтры применялись
                        "filters_enabled": FILTER_SETTINGS.get("apply_filters", True),
                        "priority_marking": FILTER_SETTINGS.get("mark_priority", True),
                        "priority_sorting": FILTER_SETTINGS.get("sort_by_priority", True),
                        "min_title_length": CONTENT_FILTERS.get("min_title_length", 15),
                        "max_title_length": CONTENT_FILTERS.get("max_title_length", 200),
                        "exclude_keywords_count": len(CONTENT_FILTERS.get("exclude_keywords", [])),
                        "priority_keywords_count": len(CONTENT_FILTERS.get("priority_keywords", []))
                    }
                }

                print(f"OK {len(filtered_articles)}/{len(articles)} ({len(articles) - len(filtered_articles)} removed)",
                      flush=True)

            except Exception as e:
                print(f"ERROR {str(e)[:30]}...", flush=True)
                result = {"source": api_name, "error": str(e)[:100], "timestamp": datetime.now().isoformat()}

        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()
        thread.join(timeout=10.0)

        if thread.is_alive():
            print(f"TIMEOUT!", flush=True)
            result = {"source": api_name, "error": "Timeout 10 seconds", "timestamp": datetime.now().isoformat()}

        return result

    def save_fast(self, result: Dict[str, Any]):
        try:
            api_name = result.get("source", "unknown")
            filename = self.fixed_filenames.get(api_name, f"news_{api_name}_latest.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"Saved {filename}")
        except Exception as e:
            print(f"Save error: {e}")

    def run_cycle(self):
        total_requests = sum(self.request_counts.values()) + 1
        print(f"\nCycle #{total_requests} - {datetime.now().strftime('%H:%M:%S')}")

        apis = ['newsapi', 'polygon', 'finnhub', 'marketaux', 'newsdata']  # ЗАМЕНИЛ twelve_data
        completed = 0

        for api_name in apis:
            if api_name in self.clients and self.can_make_request(api_name):
                result = self.fetch_with_timeout(api_name)
                if "error" not in result:
                    self.save_fast(result)
                    self.request_counts[api_name] += 1
                    self.last_requests[api_name] = datetime.now()
                    completed += 1
                time.sleep(0.1)

        if completed > 0:
            print(f"Completed: {completed} requests with filtering")
        else:
            print("All on cooldown")

        return completed > 0

    def run_forever(self):
        print("\nMONITORING MODE")
        print("MarketAux financial news integration")
        print("Ctrl+C to stop\n")

        cycle_count = 0
        try:
            while True:
                cycle_count += 1
                print(f"\n>>> CYCLE #{cycle_count} <<<")
                try:
                    self.run_cycle()
                    print("Pause 5 sec...")
                    for i in range(5):
                        time.sleep(1)
                        if i == 2:
                            print(".", end="", flush=True)
                    print()
                except Exception as e:
                    print(f"Cycle error: {e}")
                    time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\nSTOPPED")
            print(f"Cycles completed: {cycle_count}")


def main():
    print("NEWS FETCHER + MARKETAUX INTEGRATION")
    print("=" * 50)
    try:
        fetcher = SurgicalTwelveDataFetcher()
        if not fetcher.clients:
            print("\nNo API keys!")
            return

        print("\nModes:")
        print("1 - Test cycle")
        print("2 - Monitoring with MarketAux")

        choice = input("\nChoice (1-2): ").strip()
        if choice == "1":
            fetcher.run_cycle()
        else:
            fetcher.run_forever()
    except Exception as e:
        print(f"\nCritical error: {e}")


if __name__ == "__main__":
    main()

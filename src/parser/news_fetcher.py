#!/usr/bin/env python3
import time
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

from clients.newsapi_client import NewsApiClient
from clients.polygon_client import PolygonClient
from clients.finnhub_client import FinnHubClient
from clients.marketaux_client import MarketAuxClient
from clients.newsdata_client import NewsDataClient

from config import API_KEYS, RATE_LIMITS, CONTENT_FILTERS, FILTER_SETTINGS, SEARCH_CONFIG


class SurgicalNewsFetcher:
    def __init__(self):
        print("🚀 News Fetcher starting...")
        self.clients = {}
        self.request_counts = {api: 0 for api in ["newsapi", "polygon", "finnhub", "marketaux", "newsdata"]}
        self.last_requests = {api: datetime.min for api in self.request_counts}
        self.fixed_filenames = {api: f"news_{api}_latest.json" for api in self.request_counts}

        self.parser_dir = os.path.dirname(__file__)
        self._init_clients()
        print(f"✅ Clients ready: {len(self.clients)}")

    def _init_clients(self):
        apis = [
            ("newsapi", NewsApiClient),
            ("polygon", PolygonClient),
            ("finnhub", FinnHubClient),
            ("marketaux", MarketAuxClient),
            ("newsdata", NewsDataClient),
        ]

        for api_name, ClientClass in apis:
            try:
                key = API_KEYS.get(api_name, "")
                if key and not key.startswith("YOUR_"):
                    self.clients[api_name] = ClientClass(key)
                    print(f"  - {api_name.upper()} client initialized")
            except Exception as e:
                print(f"⚠️ {api_name.upper()} init failed: {e}")

    def can_make_request(self, api_name: str) -> bool:
        now = datetime.now()
        last = self.last_requests[api_name]
        return (now - last).total_seconds() >= RATE_LIMITS.get(api_name, 60)

    def apply_content_filters(self, articles: List[Dict], api_name: str) -> List[Dict]:
        """Базовые фильтры контента"""
        if not articles:
            return []

        exclude_keywords = [kw.lower() for kw in CONTENT_FILTERS.get("exclude_keywords", [])]
        min_title_len = CONTENT_FILTERS.get("min_title_length", 15)
        min_desc_len = CONTENT_FILTERS.get("min_description_length", 20)

        filtered = []
        for art in articles:
            title = art.get("title") or art.get("headline") or ""
            desc = art.get("description") or art.get("summary") or ""

            if len(title) < min_title_len or any(kw in title.lower() for kw in exclude_keywords):
                continue
            if desc and len(desc) < min_desc_len:
                continue
            filtered.append(art)
        return filtered

    def fetch_api(self, api_name: str) -> Dict[str, Any]:
        """Основная логика получения данных"""
        result = {"source": api_name, "timestamp": datetime.utcnow().isoformat(), "raw_data": {}}

        try:
            print(f"🔹 Fetching {api_name.upper()}...", end=" ")

            if api_name == "newsapi":
                config = SEARCH_CONFIG["newsapi"]
                data = self.clients[api_name].get_everything(
                    q=config["query"], language=config["language"], page_size=config["page_size"]
                )
                articles = data.get("articles", [])
            elif api_name == "polygon":
                data = self.clients[api_name].get_market_news(limit=SEARCH_CONFIG["polygon"]["limit"])
                articles = data.get("results", [])
            elif api_name == "finnhub":
                data = self.clients[api_name].general_news(SEARCH_CONFIG["finnhub"]["category"])
                articles = data
            elif api_name == "marketaux":
                data = self.clients[api_name].get_latest_news(limit=SEARCH_CONFIG["marketaux"]["limit"])
                articles = data if isinstance(data, list) else []
            elif api_name == "newsdata":
                data = self.clients[api_name].latest_news(size=SEARCH_CONFIG["newsdata"]["size"])
                articles = data.get("results", [])

            filtered = self.apply_content_filters(articles, api_name)
            result["raw_data"] = {"articles": filtered}
            print(f"OK ({len(filtered)} articles)")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            result["error"] = str(e)

        return result

    def save_result(self, api_name: str, result: Dict[str, Any]):
        """Сохраняет результат в parser/"""
        try:
            path = os.path.join(self.parser_dir, self.fixed_filenames[api_name])
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved {path}")
        except Exception as e:
            print(f"⚠️ Save error {api_name}: {e}")

    def run_cycle(self):
        for api in self.clients:
            if self.can_make_request(api):
                data = self.fetch_api(api)
                self.save_result(api, data)
                self.last_requests[api] = datetime.now()
                time.sleep(0.5)


def main():
    fetcher = SurgicalNewsFetcher()
    print("\n🔁 Fetch cycle started. Ctrl+C to stop.\n")
    try:
        while True:
            fetcher.run_cycle()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")


if __name__ == "__main__":
    main()

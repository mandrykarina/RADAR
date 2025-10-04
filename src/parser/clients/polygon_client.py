"""
Polygon.io Client - упрощенная версия основанная на официальном клиенте
https://github.com/polygon-io/client-python
"""
import requests
from typing import Dict, Any, List

class PolygonClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"

    def get_ticker_news(self, ticker: str = None, published_utc_gte: str = None,
                       published_utc_lte: str = None, order: str = "desc",
                       limit: int = 10) -> Dict[str, Any]:
        """Get news for ticker"""
        url = f"{self.base_url}/v2/reference/news"

        params = {
            'apikey': self.api_key,
            'ticker': ticker,
            'published_utc.gte': published_utc_gte,
            'published_utc.lte': published_utc_lte,
            'order': order,
            'limit': limit
        }
        # Удаляем None значения
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        return response.json()

    def get_market_news(self, limit: int = 10) -> Dict[str, Any]:
        """Get general market news"""
        return self.get_ticker_news(limit=limit)

"""
NewsData.io Client - упрощенная версия
"""
import requests
from typing import Dict, Any, List

class NewsDataClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsdata.io/api/1"

    def latest_news(self, q: str = None, country: str = None,
                   category: str = None, language: str = None,
                   size: int = 10) -> Dict[str, Any]:
        """Get latest news"""
        url = f"{self.base_url}/latest"
        params = {
            'apikey': self.api_key,
            'q': q,
            'country': country,
            'category': category,
            'language': language,
            'size': size
        }
        # Удаляем None значения
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        return response.json()

    def archive_news(self, q: str = None, from_date: str = None,
                    to_date: str = None, country: str = None,
                    language: str = None, size: int = 10) -> Dict[str, Any]:
        """Get archived news"""
        url = f"{self.base_url}/archive"
        params = {
            'apikey': self.api_key,
            'q': q,
            'from_date': from_date,
            'to_date': to_date,
            'country': country,
            'language': language,
            'size': size
        }
        # Удаляем None значения
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        return response.json()

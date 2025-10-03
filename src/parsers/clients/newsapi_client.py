"""
NewsAPI Client - скопировано с https://github.com/mattlisiv/newsapi-python
"""
import requests
from typing import Dict, Any, Optional

class NewsApiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"

    def get_top_headlines(self, q: str = None, sources: str = None, 
                         category: str = None, country: str = None,
                         page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Get top headlines"""
        url = f"{self.base_url}/top-headlines"
        params = {
            'apiKey': self.api_key,
            'q': q,
            'sources': sources,
            'category': category,
            'country': country,
            'pageSize': page_size,
            'page': page
        }
        # Удаляем None значения
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        return response.json()

    def get_everything(self, q: str = None, sources: str = None,
                      domains: str = None, exclude_domains: str = None,
                      from_param: str = None, to: str = None,
                      language: str = None, sort_by: str = None,
                      page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Search everything"""
        url = f"{self.base_url}/everything"
        params = {
            'apiKey': self.api_key,
            'q': q,
            'sources': sources,
            'domains': domains,
            'excludeDomains': exclude_domains,
            'from': from_param,
            'to': to,
            'language': language,
            'sortBy': sort_by,
            'pageSize': page_size,
            'page': page
        }
        # Удаляем None значения
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        return response.json()

    def get_sources(self, category: str = None, language: str = None, 
                   country: str = None) -> Dict[str, Any]:
        """Get available sources"""
        url = f"{self.base_url}/sources"
        params = {
            'apiKey': self.api_key,
            'category': category,
            'language': language,
            'country': country
        }
        # Удаляем None значения
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        return response.json()

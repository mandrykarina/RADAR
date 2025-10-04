"""
FinnHub Client - упрощенная версия
https://github.com/Finnhub-Stock-API/finnhub-python
"""
import requests
from typing import Dict, Any, List

class FinnHubClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"

    def company_news(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """Get company news"""
        url = f"{self.base_url}/company-news"
        params = {
            'symbol': symbol,
            'from': from_date,
            'to': to_date,
            'token': self.api_key
        }

        response = requests.get(url, params=params)
        return response.json()

    def general_news(self, category: str = "general", min_id: int = 0) -> List[Dict[str, Any]]:
        """Get general news"""
        url = f"{self.base_url}/news"
        params = {
            'category': category,
            'minId': min_id,
            'token': self.api_key
        }

        response = requests.get(url, params=params)
        return response.json()

    def market_news(self, category: str = "general") -> List[Dict[str, Any]]:
        """Get market news"""
        return self.general_news(category=category)

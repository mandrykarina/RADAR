"""
Financial Modeling Prep Client - упрощенная версия
"""
import requests
from typing import Dict, Any, List

class FMPClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api"

    def get_general_news(self, page: int = 0, size: int = 20) -> List[Dict[str, Any]]:
        """Get general news"""
        url = f"{self.base_url}/v4/general_news"
        params = {
            'page': page,
            'size': size,
            'apikey': self.api_key
        }

        response = requests.get(url, params=params)
        return response.json()

    def get_stock_news(self, tickers: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get stock news"""
        url = f"{self.base_url}/v3/stock_news"
        params = {
            'limit': limit,
            'apikey': self.api_key
        }

        if tickers:
            params['tickers'] = tickers

        response = requests.get(url, params=params)
        return response.json()

    def get_press_releases(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get press releases for symbol"""
        url = f"{self.base_url}/v3/press-releases/{symbol}"
        params = {
            'limit': limit,
            'apikey': self.api_key
        }

        response = requests.get(url, params=params)
        return response.json()

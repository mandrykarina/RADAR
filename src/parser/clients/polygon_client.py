"""Polygon Client - без изменений"""
import requests

class PolygonClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"

    def get_market_news(self, limit: int = 8):
        url = f"{self.base_url}/v2/reference/news"
        params = {'apikey': self.api_key, 'limit': limit}

        response = requests.get(url, params=params, timeout=7)
        response.raise_for_status()
        return response.json()

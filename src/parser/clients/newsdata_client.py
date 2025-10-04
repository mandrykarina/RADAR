"""NewsData Client - без изменений"""
import requests

class NewsDataClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsdata.io/api/1"

    def latest_news(self, category: str = "business", size: int = 8):
        url = f"{self.base_url}/latest"
        params = {'apikey': self.api_key, 'category': category, 'size': size}

        response = requests.get(url, params=params, timeout=7)
        response.raise_for_status()
        return response.json()

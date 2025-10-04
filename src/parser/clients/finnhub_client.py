"""FinnHub Client - без изменений"""
import requests

class FinnHubClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"

    def general_news(self, category: str = "general"):
        url = f"{self.base_url}/news"
        params = {'category': category, 'token': self.api_key}

        response = requests.get(url, params=params, timeout=7)
        response.raise_for_status()
        result = response.json()
        return result if isinstance(result, list) else []

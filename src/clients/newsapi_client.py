"""NewsAPI Client - без изменений"""
import requests

class NewsApiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"

    def get_everything(self, q: str = "finance", language: str = "en",
                      from_param: str = None, to: str = None, page_size: int = 15):
        url = f"{self.base_url}/everything"
        params = {
            'apiKey': self.api_key, 'q': q, 'language': language, 
            'pageSize': page_size, 'from': from_param, 'to': to
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params, timeout=7)
        response.raise_for_status()
        return response.json()

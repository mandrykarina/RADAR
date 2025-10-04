import requests


class MarketAuxClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.marketaux.com/v1"

    def get_latest_news(self, limit: int = 50):
        """
        Получение последних финансовых новостей с MarketAux
        """
        url = f"{self.base_url}/news/all"

        params = {
            'api_token': self.api_key,
            'language': 'en',
            'limit': min(limit, 100),  # лимит API
            'must_have_entities': 'true',  # только новости с идентифицированными сущностями
            'filter_entities': 'true',  # только релевантные сущности
            'group_similar': 'true',  # группировать похожие статьи
            'sort': 'published_at',
            'sort_order': 'desc'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('data', [])

                # Преобразуем в формат, совместимый с остальными клиентами
                formatted_articles = []
                for article in articles:
                    formatted_article = {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'publishedAt': article.get('published_at', ''),
                        'source': {'name': article.get('source', '')},
                        'content': article.get('snippet', '')
                    }
                    formatted_articles.append(formatted_article)

                return formatted_articles
            else:
                print(f"MarketAux API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"MarketAux Client Error: {e}")
            return []

    def get_market_news(self, market: str = "stocks", size: int = 50):
        """
        Альтернативный метод - просто вызывает get_latest_news
        """
        return self.get_latest_news(limit=size)

"""Twelve Data Client - ИСПРАВЛЕНА СИНТАКСИЧЕСКАЯ ОШИБКА
Использует только БЕСПЛАТНЫЕ endpoints
"""
import requests

class TwelveDataClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"

    def get_latest_news(self, symbol: str = "AAPL", size: int = 10):
        """
        ОКОНЧАТЕЛЬНО ИСПРАВЛЕНО: Используем БЕСПЛАТНЫЕ endpoints
        Получаем данные по популярным акциям как "новости о движениях"
        """
        print(f"🔍 TWELVE DATA: Запрос цен топ акций как 'новости'")

        # Список популярных символов для получения данных
        symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM",][:size]

        news_items = []

        for symbol in symbols:
            try:
                url = f"{self.base_url}/price"
                params = {
                    'symbol': symbol,
                    'apikey': self.api_key
                }

                print(f"🔗 TWELVE DATA: Запрос цены для {symbol}")

                response = requests.get(url, params=params, timeout=5)


                print(f"📡 {symbol}: status_code={response.status_code}")
                if response.status_code != 200:
                    print(f"❌ {symbol}: {response.text[:100]}")

                if response.status_code == 200:
                    result = response.json()

                    # ← И ЭТИ СТРОКИ:
                    print(f"📊 {symbol}: response={result}")

                    if 'price' in result:
                        # ... остальной код

                        # Создаем "новость" из данных о цене
                        news_item = {
                            'title': f"{symbol} Current Price Update",
                            'description': f"Current price: ${result['price']}. Last updated price data for {symbol}.",
                            'symbol': symbol,
                            'price': result['price'],
                            'datetime': result.get('datetime', 'N/A'),
                            'source': 'twelve_data_price'
                        }
                        news_items.append(news_item)

            except Exception as e:
                print(f"💥 TWELVE DATA {symbol} ошибка: {e}")
                continue

        if news_items:
            print(f"✅ TWELVE DATA Успех: {len(news_items)} ценовых 'новостей'")
        else:
            print(f"❌ TWELVE DATA: Не удалось получить данные")

        return news_items

    def get_market_news(self, market: str = "stocks", size: int = 10):

        return self.get_latest_news(size=size)

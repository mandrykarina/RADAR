from typing import List
import yfinance as yf
from datetime import datetime, timedelta


class FinancialDataProvider:
    """Провайдер финансовых данных"""

    def __init__(self):
        self.market_caps_cache = {}

    def get_market_cap(self, company_name: str) -> float:
        """Получение рыночной капитализации"""

        ticker_map = {
            'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL',
            'amazon': 'AMZN', 'tesla': 'TSLA', 'meta': 'META',
            'сбербанк': 'SBER.ME', 'газпром': 'GAZP.ME',
            'лукойл': 'LKOH.ME', 'яндекс': 'YNDX.ME'
        }

        company_key = company_name.lower()
        ticker = ticker_map.get(company_key)

        if not ticker:
            return 0.0

        # Кеш на 24 часа
        if company_key in self.market_caps_cache:
            cached = self.market_caps_cache[company_key]
            if datetime.now() - cached['timestamp'] < timedelta(hours=24):
                return cached['market_cap']

        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            market_cap = info.get('marketCap', 0)

            # Кешируем
            self.market_caps_cache[company_key] = {
                'market_cap': market_cap,
                'timestamp': datetime.now()
            }

            return market_cap
        except Exception:
            return 0.0

    def estimate_market_impact(self, entities: List[str]) -> float:
        """Оценка влияния на рынок"""

        total_cap = sum(self.get_market_cap(entity) for entity in entities)
        return min(1.0, total_cap / 1e12)  # нормализация к $1T
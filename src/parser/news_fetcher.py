#!/usr/bin/env python3
"""
ULTRA STABLE - ИСПРАВЛЕНИЕ ЗАВИСАНИЯ НА 11 ЦИКЛЕ
Проблема: зависание после Polygon/NewsAPI
Решение: минимальные timeout, неблокирующие операции
"""
import time
import json
import os
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, Any

from clients.newsapi_client import NewsApiClient
from clients.polygon_client import PolygonClient  
from clients.finnhub_client import FinnHubClient
from clients.fmp_client import FMPClient
from clients.newsdata_client import NewsDataClient

from config import API_KEYS, RATE_LIMITS


class UltraStableFetcher:
    """УЛЬТРА СТАБИЛЬНАЯ ВЕРСИЯ - НЕ ЗАВИСАЕТ!"""

    def __init__(self):
        print("🚨 ULTRA STABLE NEWS FETCHER")
        print("⚡ Максимальная защита от зависаний")

        self.clients = {}
        self.request_counts = {
            'newsapi': 0, 'polygon': 0, 'finnhub': 0, 'fmp': 0, 'newsdata': 0
        }

        self.last_requests = {
            'newsapi': datetime.min, 'polygon': datetime.min, 'finnhub': datetime.min, 
            'fmp': datetime.min, 'newsdata': datetime.min
        }

        # Фиксированные файлы
        self.fixed_filenames = {
            'newsapi': 'news_newsapi_latest.json',
            'polygon': 'news_polygon_latest.json', 
            'finnhub': 'news_finnhub_latest.json',
            'fmp': 'news_fmp_latest.json',
            'newsdata': 'news_newsdata_latest.json'
        }

        self._init_clients()
        print(f"✅ Клиентов готово: {len(self.clients)}")

    def _init_clients(self):
        """Быстрая инициализация без блокировок"""

        apis = [('newsapi', NewsApiClient), ('polygon', PolygonClient), 
                ('finnhub', FinnHubClient), ('fmp', FMPClient), ('newsdata', NewsDataClient)]

        for api_name, ClientClass in apis:
            try:
                key = API_KEYS.get(api_name, "")
                if key and key != f"YOUR_{api_name.upper()}_KEY_HERE":
                    self.clients[api_name] = ClientClass(key)
                    print(f"✅ {api_name.upper()}")
            except Exception as e:
                print(f"❌ {api_name.upper()}: {e}")

    def can_make_request(self, api_name: str) -> bool:
        """Упрощенная проверка лимитов"""
        try:
            now = datetime.now()
            last = self.last_requests[api_name]
            passed = (now - last).total_seconds()

            return passed >= RATE_LIMITS.get(api_name, 60)
        except:
            return True

    def fetch_with_timeout(self, api_name: str) -> Dict[str, Any]:
        """НОВОЕ: Запрос с жестким timeout через threading"""

        result = {"source": api_name, "error": "timeout", "articles_count": 0}

        def _fetch():
            nonlocal result
            try:
                print(f"📡 {api_name.upper()}...", end=" ", flush=True)

                if api_name == "newsapi":
                    to_date = datetime.now()
                    from_date = to_date - timedelta(hours=24)

                    data = self.clients["newsapi"].get_everything(
                        q="finance",
                        language="en",
                        from_param=from_date.strftime("%Y-%m-%d"),
                        to=to_date.strftime("%Y-%m-%d"),
                        page_size=10
                    )

                elif api_name == "polygon":
                    data = self.clients["polygon"].get_market_news(limit=5)

                elif api_name == "finnhub":
                    data = self.clients["finnhub"].general_news("general")

                elif api_name == "fmp":
                    data = self.clients["fmp"].get_general_news(page=0, size=5)

                elif api_name == "newsdata":
                    data = self.clients["newsdata"].latest_news(category="business", size=5)

                # Подсчет быстро
                count = 0
                if isinstance(data, dict):
                    if api_name == "newsapi":
                        count = len(data.get("articles", []))
                    elif api_name in ["polygon", "newsdata"]:
                        count = len(data.get("results", []))
                elif isinstance(data, list):
                    count = len(data)

                result = {
                    "source": api_name,
                    "timestamp": datetime.now().isoformat(),
                    "request_number": self.request_counts[api_name] + 1,
                    "articles_count": count,
                    "raw_data": data
                }

                print(f"✅ {count}", flush=True)

            except Exception as e:
                print(f"❌ {str(e)[:30]}...", flush=True)
                result = {
                    "source": api_name,
                    "error": str(e)[:100]
                }

        # Запускаем в отдельном потоке с timeout
        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()
        thread.join(timeout=8.0)  # ЖЕСТКИЙ timeout 8 секунд

        if thread.is_alive():
            print(f"⏰ TIMEOUT!", flush=True)
            result = {
                "source": api_name,
                "error": "Timeout 8 секунд",
                "articles_count": 0
            }

        return result

    def save_fast(self, result: Dict[str, Any]):
        """БЫСТРОЕ сохранение без блокировок"""
        try:
            api_name = result.get("source", "unknown")
            filename = self.fixed_filenames.get(api_name, f"news_{api_name}_latest.json")

            # Быстрая запись
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=None)  # Без форматирования

            print(f"💾 {filename}", flush=True)

        except Exception as e:
            print(f"❌ Сохранение: {e}", flush=True)

    def run_cycle(self):
        """УЛЬТРА-БЫСТРЫЙ цикл без зависаний"""
        total_requests = sum(self.request_counts.values()) + 1
        print(f"\n🔄 Цикл #{total_requests} - {datetime.now().strftime('%H:%M:%S')}")

        apis = ['newsapi', 'polygon', 'finnhub', 'fmp', 'newsdata']
        completed = 0

        for api_name in apis:
            if api_name in self.clients and self.can_make_request(api_name):

                result = self.fetch_with_timeout(api_name)

                if "error" not in result:
                    self.save_fast(result)
                    self.request_counts[api_name] += 1
                    self.last_requests[api_name] = datetime.now()
                    completed += 1

                # Микро-пауза
                time.sleep(0.1)

        if completed > 0:
            print(f"✅ Завершено: {completed} запросов")
        else:
            print("⏰ Все на cooldown")

        return completed > 0

    def run_forever(self):
        """Главный цикл с защитой от зависаний"""
        print("\n🔄 УЛЬТРА-СТАБИЛЬНЫЙ МОНИТОРИНГ")
        print("⚡ Timeout 8 сек на каждый запрос")
        print("🚀 Неблокирующие операции")
        print("Ctrl+C для остановки\n")

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                print(f"\n>>> ЦИКЛ #{cycle_count} <<<")

                try:
                    self.run_cycle()

                    # БЫСТРАЯ пауза
                    print("⏰ Пауза 3 сек...")
                    for i in range(3):
                        time.sleep(1)
                        print(".", end="", flush=True)
                    print()

                except Exception as e:
                    print(f"❌ Ошибка цикла: {e}")
                    time.sleep(1)  # Короткая пауза

        except KeyboardInterrupt:
            print("\n\n🛑 ОСТАНОВЛЕНО")
            print(f"Циклов выполнено: {cycle_count}")


def main():
    print("🚨 ULTRA STABLE NEWS FETCHER")
    print("⚡ ИСПРАВЛЕНИЕ ЗАВИСАНИЯ НА 11 ЦИКЛЕ")
    print("=" * 50)

    try:
        fetcher = UltraStableFetcher()

        if not fetcher.clients:
            print("\n❌ Нет API ключей!")
            return

        print("\n⚡ ЗАЩИТА ОТ ЗАВИСАНИЙ:")
        print("• Timeout 8 сек на каждый запрос")
        print("• Threading для неблокирующих операций") 
        print("• Быстрая запись файлов")

        print("\nРежимы:")
        print("1 - Тестовый цикл")
        print("2 - Ультра-стабильный мониторинг")

        choice = input("\nВыбор (1-2): ").strip()

        if choice == "1":
            fetcher.run_cycle()
        else:
            fetcher.run_forever()

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()

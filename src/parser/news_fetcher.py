#!/usr/bin/env python3
"""
ULTRA STABLE + NORMALIZER
Теперь fetcher сохраняет уже нормализованные новости
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, Any

from clients.newsapi_client import NewsApiClient
from clients.polygon_client import PolygonClient  
from clients.finnhub_client import FinnHubClient
from clients.fmp_client import FMPClient
from clients.newsdata_client import NewsDataClient

from config import API_KEYS, RATE_LIMITS
from src.normalizer import normalize_batch   # ✅ импорт нормализатора



class UltraStableFetcher:
    """УЛЬТРА СТАБИЛЬНЫЙ ПАРСЕР + НОРМАЛИЗАТОР"""

    def __init__(self):
        print("🚨 ULTRA STABLE NEWS FETCHER + NORMALIZER")

        # Создаём папку data для файлов
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.data_dir = os.path.abspath(self.data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

        self.clients = {}
        self.request_counts = {
            'newsapi': 0, 'polygon': 0, 'finnhub': 0, 'fmp': 0, 'newsdata': 0
        }

        self.last_requests = {
            'newsapi': datetime.min, 'polygon': datetime.min, 'finnhub': datetime.min, 
            'fmp': datetime.min, 'newsdata': datetime.min
        }

        # Файлы теперь лежат в папке data/
        self.fixed_filenames = {
            'newsapi': os.path.join(self.data_dir, 'news_newsapi_latest.json'),
            'polygon': os.path.join(self.data_dir, 'news_polygon_latest.json'),
            'finnhub': os.path.join(self.data_dir, 'news_finnhub_latest.json'),
            'fmp': os.path.join(self.data_dir, 'news_fmp_latest.json'),
            'newsdata': os.path.join(self.data_dir, 'news_newsdata_latest.json')
        }

        self._init_clients()
        print(f"✅ Клиентов готово: {len(self.clients)}")

    def _init_clients(self):
        """Инициализация клиентов"""
        apis = [
            ('newsapi', NewsApiClient), 
            ('polygon', PolygonClient), 
            ('finnhub', FinnHubClient), 
            ('fmp', FMPClient), 
            ('newsdata', NewsDataClient)
        ]

        for api_name, ClientClass in apis:
            try:
                key = API_KEYS.get(api_name, "")
                if key and key != f"YOUR_{api_name.upper()}_KEY_HERE":
                    self.clients[api_name] = ClientClass(key)
                    print(f"✅ {api_name.upper()}")
            except Exception as e:
                print(f"❌ {api_name.upper()}: {e}")

    def can_make_request(self, api_name: str) -> bool:
        """Проверка лимитов"""
        try:
            now = datetime.now()
            last = self.last_requests[api_name]
            passed = (now - last).total_seconds()
            return passed >= RATE_LIMITS.get(api_name, 60)
        except:
            return True

    def fetch_with_timeout(self, api_name: str) -> Dict[str, Any]:
        """Запрос с жестким timeout"""
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

                else:
                    data = {}

                # Подсчёт статей
                count = 0
                if isinstance(data, dict):
                    if api_name == "newsapi":
                        count = len(data.get("articles", []))
                    elif api_name in ["polygon", "newsdata"]:
                        count = len(data.get("results", []))
                elif isinstance(data, list):
                    count = len(data)

                # ✅ нормализация
                normalized = normalize_batch(api_name, data)

                result = {
                    "source": api_name,
                    "timestamp": datetime.now().isoformat(),
                    "request_number": self.request_counts[api_name] + 1,
                    "articles_count": count,
                    "normalized": normalized
                }

                print(f"✅ {count}", flush=True)

            except Exception as e:
                print(f"❌ {str(e)[:30]}...", flush=True)
                result = {
                    "source": api_name,
                    "error": str(e)[:100]
                }

        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()
        thread.join(timeout=8.0)

        if thread.is_alive():
            print(f"⏰ TIMEOUT!", flush=True)
            result = {
                "source": api_name,
                "error": "Timeout 8 секунд",
                "articles_count": 0
            }

        return result

    def save_fast(self, result: Dict[str, Any]):
        """Сохранение нормализованных новостей"""
        try:
            api_name = result.get("source", "unknown")
            filename = self.fixed_filenames.get(api_name, os.path.join(self.data_dir, f"news_{api_name}_latest.json"))

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result["normalized"], f, ensure_ascii=False, indent=2)

            print(f"💾 Сохранено: {filename}", flush=True)

        except Exception as e:
            print(f"❌ Сохранение: {e}", flush=True)

    def run_cycle(self):
        """Один цикл запросов"""
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

                time.sleep(0.1)

        if completed > 0:
            print(f"✅ Завершено: {completed} запросов")
        else:
            print("⏰ Все на cooldown")

        return completed > 0

    def run_forever(self):
        """Основной цикл"""
        print("\n🔄 УЛЬТРА-СТАБИЛЬНЫЙ МОНИТОРИНГ (с нормализацией)")
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
                    print("⏰ Пауза 3 сек...")
                    for i in range(3):
                        time.sleep(1)
                        print(".", end="", flush=True)
                    print()
                except Exception as e:
                    print(f"❌ Ошибка цикла: {e}")
                    time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n🛑 ОСТАНОВЛЕНО")
            print(f"Циклов выполнено: {cycle_count}")


def main():
    print("🚨 ULTRA STABLE FETCHER + NORMALIZER + DATA FOLDER")
    print("=" * 50)

    try:
        fetcher = UltraStableFetcher()

        if not fetcher.clients:
            print("\n❌ Нет API ключей!")
            return

        print("\nРежимы:")
        print("1 - Один тестовый цикл")
        print("2 - Постоянный мониторинг")

        choice = input("\nВыбор (1-2): ").strip()

        if choice == "1":
            fetcher.run_cycle()
        else:
            fetcher.run_forever()

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()

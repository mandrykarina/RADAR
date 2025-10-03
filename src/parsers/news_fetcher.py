#!/usr/bin/env python3
"""
Rate-Limited News Fetcher с поисковыми словами из конфига
Использует настройки из config.py для поиска новостей
"""
import time
import json
from datetime import datetime
from typing import Dict, Any

# Импортируем наши клиенты
from clients.newsapi_client import NewsApiClient
from clients.polygon_client import PolygonClient  
from clients.finnhub_client import FinnHubClient
from clients.fmp_client import FMPClient
from clients.newsdata_client import NewsDataClient

# Импортируем конфигурацию
from config import API_KEYS, RATE_LIMITS, SEARCH_QUERIES, GENERAL_SETTINGS


class ConfigurableNewsFetcher:
    """Сборщик новостей с настройками из конфига"""

    def __init__(self):
        print("🚀 Инициализация Configurable News Fetcher...")

        # Инициализируем клиенты
        self.clients = {}
        self._init_clients()

        # Счетчики запросов
        self.request_counts = {
            'newsapi': 0,
            'polygon': 0, 
            'finnhub': 0,
            'fmp': 0,
            'newsdata': 0
        }

        # Последние запросы (для отслеживания интервалов)
        self.last_requests = {
            'newsapi': datetime.min,
            'polygon': datetime.min,
            'finnhub': datetime.min, 
            'fmp': datetime.min,
            'newsdata': datetime.min
        }

        print(f"✅ Готов! Активных клиентов: {len(self.clients)}")
        self._show_search_config()

    def _init_clients(self):
        """Инициализация клиентов API"""

        if API_KEYS["newsapi"] != "YOUR_NEWSAPI_KEY_HERE":
            try:
                self.clients["newsapi"] = NewsApiClient(API_KEYS["newsapi"])
                print("✅ NewsAPI клиент готов (каждые 60 сек)")
            except Exception as e:
                print(f"❌ Ошибка NewsAPI: {e}")

        if API_KEYS["polygon"] != "YOUR_POLYGON_KEY_HERE":
            try:
                self.clients["polygon"] = PolygonClient(API_KEYS["polygon"])
                print("✅ Polygon клиент готов (каждые 12 сек)")
            except Exception as e:
                print(f"❌ Ошибка Polygon: {e}")

        if API_KEYS["finnhub"] != "YOUR_FINNHUB_KEY_HERE":
            try:
                self.clients["finnhub"] = FinnHubClient(API_KEYS["finnhub"])
                print("✅ FinnHub клиент готов (каждую 1 сек)")
            except Exception as e:
                print(f"❌ Ошибка FinnHub: {e}")

        if API_KEYS["fmp"] != "YOUR_FMP_KEY_HERE":
            try:
                self.clients["fmp"] = FMPClient(API_KEYS["fmp"])
                print("✅ FMP клиент готов (каждые 6 мин)")
            except Exception as e:
                print(f"❌ Ошибка FMP: {e}")

        if API_KEYS["newsdata"] != "YOUR_NEWSDATA_KEY_HERE":
            try:
                self.clients["newsdata"] = NewsDataClient(API_KEYS["newsdata"])
                print("✅ NewsData клиент готов (каждые 8 мин)")
            except Exception as e:
                print(f"❌ Ошибка NewsData: {e}")

    def _show_search_config(self):
        """Показать текущие настройки поиска"""
        print("\n🔍 НАСТРОЙКИ ПОИСКА ИЗ КОНФИГА:")
        print("-" * 50)

        for api_name, settings in SEARCH_QUERIES.items():
            if api_name in self.clients:
                print(f"📊 {api_name.upper()}:")

                if api_name == "newsapi":
                    print(f"   Запрос: {settings['main_query']}")
                    print(f"   Язык: {settings['language']}")
                    print(f"   Сортировка: {settings['sort_by']}")

                elif api_name == "polygon":
                    print(f"   Термины: {', '.join(settings['search_terms'])}")
                    print(f"   Лимит: {settings['limit']}")

                elif api_name == "finnhub":
                    print(f"   Категории: {', '.join(settings['categories'])}")
                    print(f"   По умолчанию: {settings['default_category']}")

                elif api_name == "fmp":
                    print(f"   Термины: {', '.join(settings['search_terms'])}")
                    print(f"   Размер страницы: {settings['page_size']}")

                elif api_name == "newsdata":
                    print(f"   Запрос: {settings['query']}")
                    print(f"   Категории: {', '.join(settings['categories'])}")
                    print(f"   Размер: {settings['size']}")

                print()

    def can_make_request(self, api_name: str) -> bool:
        """Проверка можно ли делать запрос к API"""
        now = datetime.now()
        last_request = self.last_requests[api_name]
        seconds_passed = (now - last_request).total_seconds()

        return seconds_passed >= RATE_LIMITS.get(api_name, 60)

    def fetch_from_api(self, api_name: str) -> Dict[str, Any]:
        """Запрос к конкретному API с использованием настроек из конфига"""

        if api_name not in self.clients:
            return {"source": api_name, "error": "Клиент недоступен"}

        if not self.can_make_request(api_name):
            return {"source": api_name, "error": "Rate limit - ждем интервал"}

        try:
            print(f"📡 Запрос к {api_name.upper()}...")

            if api_name == "newsapi":
                config = SEARCH_QUERIES["newsapi"]
                result = self.clients["newsapi"].get_everything(
                    q=config["main_query"],
                    language=config["language"],
                    sort_by=config["sort_by"], 
                    page_size=GENERAL_SETTINGS["default_page_size"]
                )

            elif api_name == "polygon":
                config = SEARCH_QUERIES["polygon"]
                result = self.clients["polygon"].get_market_news(
                    limit=config["limit"]
                )

            elif api_name == "finnhub":
                config = SEARCH_QUERIES["finnhub"]
                result = self.clients["finnhub"].general_news(
                    category=config["default_category"]
                )

            elif api_name == "fmp":
                config = SEARCH_QUERIES["fmp"]
                result = self.clients["fmp"].get_general_news(
                    page=0, 
                    size=config["page_size"]
                )

            elif api_name == "newsdata":
                config = SEARCH_QUERIES["newsdata"]
                result = self.clients["newsdata"].latest_news(
                    q=config["query"],
                    category=config["categories"][0] if config["categories"] else None,
                    language=config["languages"][0] if config["languages"] else "en",
                    size=config["size"]
                )

            # Обновляем счетчики
            self.request_counts[api_name] += 1
            self.last_requests[api_name] = datetime.now()

            # Подсчитываем количество статей
            if api_name == "newsapi":
                count = result.get("totalResults", 0) if isinstance(result, dict) else 0
            elif api_name == "polygon":
                count = result.get("count", 0) if isinstance(result, dict) else 0
            elif api_name in ["finnhub", "fmp"]:
                count = len(result) if isinstance(result, list) else 0
            elif api_name == "newsdata":
                count = result.get("totalResults", 0) if isinstance(result, dict) else 0
            else:
                count = 0

            response = {
                "source": api_name,
                "timestamp": datetime.now().isoformat(),
                "request_number": self.request_counts[api_name],
                "articles_count": count,
                "search_config": SEARCH_QUERIES.get(api_name, {}),
                "raw_data": result
            }

            print(f"    ✅ {api_name.upper()}: получено {count} новостей (запрос #{self.request_counts[api_name]})")
            return response

        except Exception as e:
            print(f"    ❌ {api_name.upper()}: {str(e)}")
            return {
                "source": api_name,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    def save_result(self, result: Dict[str, Any]):
        """Сохранение результата"""
        if not GENERAL_SETTINGS.get("save_results", True):
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source = result.get("source", "unknown")
            filename = f"news_{source}_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            if GENERAL_SETTINGS.get("show_progress", True):
                print(f"💾 Сохранено: {filename}")

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")

    def print_stats(self):
        """Статистика запросов"""
        print("\n📊 СТАТИСТИКА:")
        print("-" * 50)

        for api_name, count in self.request_counts.items():
            if api_name in self.clients:
                last_req = self.last_requests[api_name]
                if last_req != datetime.min:
                    mins_ago = (datetime.now() - last_req).total_seconds() / 60
                    print(f"📈 {api_name.upper()}: {count} запросов (последний {mins_ago:.1f} мин назад)")
                else:
                    print(f"📈 {api_name.upper()}: {count} запросов (еще не запрашивался)")

        total = sum(self.request_counts.values())
        print(f"\n🔢 ВСЕГО ЗАПРОСОВ: {total}")
        print("-" * 50)

    def run_cycle(self):
        """Один цикл проверки всех API"""
        if GENERAL_SETTINGS.get("show_progress", True):
            print(f"\n🔄 Проверка API - {datetime.now().strftime('%H:%M:%S')}")

        apis = ['newsapi', 'polygon', 'finnhub', 'fmp', 'newsdata']
        requests_made = 0

        for api_name in apis:
            if api_name in self.clients:
                if self.can_make_request(api_name):
                    result = self.fetch_from_api(api_name)

                    if "error" not in result:
                        self.save_result(result)
                        requests_made += 1

                    # Маленькая пауза между запросами
                    time.sleep(0.5)
                else:
                    # Показываем когда будет следующий запрос
                    if GENERAL_SETTINGS.get("show_progress", True):
                        last_req = self.last_requests[api_name]
                        if last_req != datetime.min:
                            seconds_left = RATE_LIMITS[api_name] - (datetime.now() - last_req).total_seconds()
                            if seconds_left > 0:
                                if seconds_left > 60:
                                    print(f"⏰ {api_name.upper()}: следующий запрос через {seconds_left/60:.1f} мин")
                                else:
                                    print(f"⏰ {api_name.upper()}: следующий запрос через {seconds_left:.0f} сек")

        if requests_made == 0 and GENERAL_SETTINGS.get("show_progress", True):
            print("⏰ Все API на cooldown")
        elif requests_made > 0:
            print(f"✅ Выполнено {requests_made} запросов в этом цикле")

    def run_forever(self):
        """Бесконечный цикл"""
        print("\n🔄 ЗАПУСК НЕПРЕРЫВНОГО МОНИТОРИНГА")
        print("Проверка каждые 5 секунд...")
        print("Ctrl+C для остановки\n")

        try:
            cycle_count = 0
            while True:
                cycle_count += 1

                if GENERAL_SETTINGS.get("show_progress", True):
                    print(f"\n>>> ЦИКЛ #{cycle_count}")

                self.run_cycle()

                # Статистика каждые 10 циклов
                if cycle_count % 10 == 0:
                    self.print_stats()

                # Ждем 5 секунд
                if GENERAL_SETTINGS.get("show_progress", True):
                    print("\n⏰ Пауза 5 секунд...")
                time.sleep(5)

        except KeyboardInterrupt:
            print("\n\n🛑 ОСТАНОВКА")
            self.print_stats()

    def show_schedule(self):
        """Показать расписание"""
        print("\n📅 РАСПИСАНИЕ ЗАПРОСОВ:")
        print("=" * 50)
        for api_name, interval in RATE_LIMITS.items():
            if api_name in self.clients:
                if interval >= 60:
                    print(f"📰 {api_name.upper():<12} каждые {interval//60} минут")
                else:
                    print(f"📰 {api_name.upper():<12} каждые {interval} секунд")
        print("=" * 50)
        print("⚡ Проверка каждые 5 секунд\n")


def main():
    print("=" * 60)
    print("📰 CONFIGURABLE NEWS FETCHER")
    print("=" * 60)

    fetcher = ConfigurableNewsFetcher()

    if not fetcher.clients:
        print("\n❌ Нет API ключей! Настройте config.py")
        return

    fetcher.show_schedule()

    print("Режимы:")
    print("1 - Один цикл проверки")
    print("2 - Непрерывная работа (РЕКОМЕНДУЕТСЯ)")
    print("3 - Показать настройки поиска")

    choice = input("\nВыбор (1-3): ").strip()

    if choice == "1":
        fetcher.run_cycle()
        fetcher.print_stats()
    elif choice == "3":
        fetcher._show_search_config()
    else:
        fetcher.run_forever()


if __name__ == "__main__":
    main()

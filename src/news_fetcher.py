#!/usr/bin/env python3
"""
🔬 SURGICAL FIX + TWELVE DATA INTEGRATION
============================================
✂️ FMP ПОЛНОСТЬЮ УДАЛЕН
🆕 TWELVE DATA ДОБАВЛЕН
✅ Фильтры сохранены и работают
"""
import time
import json
import os
import threading
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List

from clients.newsapi_client import NewsApiClient
from clients.polygon_client import PolygonClient  
from clients.finnhub_client import FinnHubClient
from clients.twelve_data_client import TwelveDataClient  # 🆕 НОВЫЙ ИМПОРТ
from clients.newsdata_client import NewsDataClient

from config import API_KEYS, RATE_LIMITS, CONTENT_FILTERS, FILTER_SETTINGS, SEARCH_CONFIG


class SurgicalTwelveDataFetcher:
    """🔬 ХИРУРГИЧЕСКИ ИСПРАВЛЕННАЯ ВЕРСИЯ С TWELVE DATA"""

    def __init__(self):
        print("🔬 SURGICAL FIX + TWELVE DATA INTEGRATION")
        print("✂️ FMP удален, 🆕 Twelve Data добавлен")

        self.clients = {}
        self.request_counts = {
            'newsapi': 0, 'polygon': 0, 'finnhub': 0, 
            'twelve_data': 0,  # 🆕 НОВЫЙ СЧЕТЧИК
            'newsdata': 0
        }

        self.last_requests = {
            'newsapi': datetime.min, 'polygon': datetime.min, 'finnhub': datetime.min, 
            'twelve_data': datetime.min,  # 🆕 НОВОЕ ОТСЛЕЖИВАНИЕ
            'newsdata': datetime.min
        }

        self.fixed_filenames = {
            'newsapi': 'news_newsapi_latest.json',
            'polygon': 'news_polygon_latest.json', 
            'finnhub': 'news_finnhub_latest.json',
            'twelve_data': 'news_twelve_data_latest.json',  # 🆕 НОВЫЙ ФАЙЛ
            'newsdata': 'news_newsdata_latest.json'
        }

        self._init_clients()
        print(f"✅ Клиентов готово: {len(self.clients)}")

        # Показываем настройки фильтров
        if FILTER_SETTINGS.get("apply_filters", True):
            print("🔍 Фильтры ВКЛЮЧЕНЫ:")
            print(f"   • Исключаем: {len(CONTENT_FILTERS.get('exclude_keywords', []))} спам-слов")
            print(f"   • Приоритет: {len(CONTENT_FILTERS.get('priority_keywords', []))} важных слов")

    def _init_clients(self):
        """Инициализация клиентов - FMP УДАЛЕН, Twelve Data ДОБАВЛЕН"""
        apis = [
            ('newsapi', NewsApiClient), 
            ('polygon', PolygonClient), 
            ('finnhub', FinnHubClient), 
            ('twelve_data', TwelveDataClient),  # 🆕 НОВЫЙ КЛИЕНТ
            ('newsdata', NewsDataClient)
        ]

        for api_name, ClientClass in apis:
            try:
                key = API_KEYS.get(api_name, "")
                if key and not key.startswith("YOUR_"):
                    self.clients[api_name] = ClientClass(key)
                    print(f"✅ {api_name.upper()}")
                else:
                    print(f"⚠️ {api_name.upper()}: Нет API ключа")
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

    def apply_content_filters(self, articles: List[Dict], api_name: str) -> List[Dict]:
        """Применение фильтров контента - TWELVE DATA ПОДДЕРЖАН"""

        if not FILTER_SETTINGS.get("apply_filters", True):
            return articles

        if not articles:
            return articles

        filtered_articles = []
        exclude_keywords = [kw.lower() for kw in CONTENT_FILTERS.get("exclude_keywords", [])]
        priority_keywords = [kw.lower() for kw in CONTENT_FILTERS.get("priority_keywords", [])]
        min_title_len = CONTENT_FILTERS.get("min_title_length", 15)
        max_title_len = CONTENT_FILTERS.get("max_title_length", 200)
        min_desc_len = CONTENT_FILTERS.get("min_description_length", 20)

        for article in articles:
            try:
                # Извлекаем заголовок в зависимости от API
                title = ""
                description = ""

                if api_name == "newsapi":
                    title = article.get("title", "") or ""
                    description = article.get("description", "") or ""
                elif api_name == "polygon":
                    title = article.get("title", "") or ""
                    description = article.get("description", "") or ""
                elif api_name == "finnhub":
                    title = article.get("headline", "") or ""
                    description = article.get("summary", "") or ""
                elif api_name == "twelve_data":  # 🆕 НОВЫЙ СЛУЧАЙ
                    title = article.get("title", "") or ""
                    description = article.get("description", "") or ""
                elif api_name == "newsdata":
                    title = article.get("title", "") or ""
                    description = article.get("description", "") or ""

                if not title:
                    continue

                title_lower = title.lower()
                desc_lower = description.lower() if description else ""

                # Фильтр 1: Длина заголовка
                if len(title) < min_title_len or len(title) > max_title_len:
                    continue

                # Фильтр 2: Минимальная длина описания  
                if description and len(description) < min_desc_len:
                    continue

                # Фильтр 3: Исключаемые слова
                if any(exclude_word in title_lower for exclude_word in exclude_keywords):
                    continue

                if description and any(exclude_word in desc_lower for exclude_word in exclude_keywords):
                    continue

                # Фильтр 4: Приоритетные новости (помечаем)
                if FILTER_SETTINGS.get("mark_priority", True):
                    if any(priority_word in title_lower for priority_word in priority_keywords):
                        article["_priority"] = True
                        article["_priority_reason"] = "Important keywords in title"

                # Статья прошла все фильтры
                filtered_articles.append(article)

            except Exception as e:
                continue

        # Сортировка по приоритету
        if FILTER_SETTINGS.get("sort_by_priority", True):
            filtered_articles.sort(key=lambda x: x.get("_priority", False), reverse=True)

        return filtered_articles

    def fetch_with_timeout(self, api_name: str) -> Dict[str, Any]:
        """Запрос с timeout и фильтрацией - TWELVE DATA ИНТЕГРИРОВАН"""

        result = {"source": api_name, "error": "timeout", "articles_count": 0}

        def _fetch():
            nonlocal result
            try:
                print(f"📡 {api_name.upper()}...", end=" ", flush=True)

                if api_name == "newsapi":
                    config = SEARCH_CONFIG.get("newsapi", {})
                    to_date = datetime.now()
                    from_date = to_date - timedelta(hours=24)

                    data = self.clients["newsapi"].get_everything(
                        q=config.get("query", "finance"),
                        language=config.get("language", "en"),
                        from_param=from_date.strftime("%Y-%m-%d"),
                        to=to_date.strftime("%Y-%m-%d"),
                        page_size=config.get("page_size", 15)
                    )

                elif api_name == "polygon":
                    config = SEARCH_CONFIG.get("polygon", {})
                    data = self.clients["polygon"].get_market_news(
                        limit=config.get("limit", 8)
                    )

                elif api_name == "finnhub":
                    config = SEARCH_CONFIG.get("finnhub", {})
                    data = self.clients["finnhub"].general_news(
                        config.get("category", "general")
                    )

                elif api_name == "twelve_data":  # 🆕 НОВАЯ ИНТЕГРАЦИЯ
                    config = SEARCH_CONFIG.get("twelve_data", {})
                    data = self.clients["twelve_data"].get_latest_news(
                        size=config.get("outputsize", 10)
                    )
                    # Twelve Data возвращает уже готовый список

                elif api_name == "newsdata":
                    config = SEARCH_CONFIG.get("newsdata", {})
                    data = self.clients["newsdata"].latest_news(
                        category="business",
                        size=config.get("size", 8)
                    )

                # Извлекаем статьи для фильтрации
                articles = []
                if api_name == "twelve_data":
                    # Twelve Data уже возвращает список статей
                    articles = data if isinstance(data, list) else []
                elif isinstance(data, dict):
                    if api_name == "newsapi":
                        articles = data.get("articles", [])
                    elif api_name in ["polygon", "newsdata"]:
                        articles = data.get("results", [])
                elif isinstance(data, list):
                    articles = data

                # ПРИМЕНЯЕМ ФИЛЬТРЫ
                filtered_articles = self.apply_content_filters(articles, api_name)

                # Обновляем данные отфильтрованными статьями
                if api_name == "twelve_data":
                    # Для Twelve Data просто заменяем
                    data = filtered_articles
                elif isinstance(data, dict):
                    if api_name == "newsapi":
                        data["articles"] = filtered_articles
                        data["totalResults"] = len(filtered_articles)
                    elif api_name in ["polygon", "newsdata"]:
                        data["results"] = filtered_articles
                        if api_name == "polygon":
                            data["count"] = len(filtered_articles)
                        else:
                            data["totalResults"] = len(filtered_articles)
                elif isinstance(data, list):
                    data = filtered_articles

                count = len(filtered_articles)

                result = {
                    "source": api_name,
                    "timestamp": datetime.now().isoformat(),
                    "request_number": self.request_counts[api_name] + 1,
                    "articles_count": count,
                    "filtered": True,
                    "filter_stats": {
                        "original_count": len(articles),
                        "filtered_count": count,
                        "removed_count": len(articles) - count
                    },
                    "raw_data": data
                }

                priority_count = len([a for a in filtered_articles if a.get("_priority", False)])
                if priority_count > 0:
                    result["priority_articles"] = priority_count

                print(f"✅ {count} ({len(articles)-count} убрано)", flush=True)

            except Exception as e:
                print(f"❌ {str(e)[:30]}...", flush=True)
                result = {"source": api_name, "error": str(e)[:100]}

        # Запуск с timeout
        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()
        thread.join(timeout=10.0)

        if thread.is_alive():
            print(f"⏰ TIMEOUT!", flush=True)
            result = {"source": api_name, "error": "Timeout 10 секунд"}

        return result

    def save_fast(self, result: Dict[str, Any]):
        """Быстрое сохранение"""
        try:
            api_name = result.get("source", "unknown")
            filename = self.fixed_filenames.get(api_name, f"news_{api_name}_latest.json")

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # Показываем статистику фильтрации
            if "filter_stats" in result:
                stats = result["filter_stats"]
                priority = result.get("priority_articles", 0)
                priority_text = f", {priority} важных" if priority > 0 else ""
                print(f"💾 {filename} ({stats['filtered_count']}/{stats['original_count']}{priority_text})")
            else:
                print(f"💾 {filename}")

        except Exception as e:
            print(f"❌ Сохранение: {e}")

    def run_cycle(self):
        """Цикл с фильтрацией - FMP УДАЛЕН, Twelve Data ДОБАВЛЕН"""
        total_requests = sum(self.request_counts.values()) + 1
        print(f"\n🔄 Цикл #{total_requests} - {datetime.now().strftime('%H:%M:%S')}")

        # ✂️ FMP УДАЛЕН из списка
        apis = ['newsapi', 'polygon', 'finnhub', 'twelve_data', 'newsdata']  # 🆕 twelve_data добавлен
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
            print(f"✅ Завершено: {completed} запросов с фильтрацией")
        else:
            print("⏰ Все на cooldown")

        return completed > 0

    def run_forever(self):
        """Мониторинг с Twelve Data"""
        print("\n🔄 МОНИТОРИНГ + TWELVE DATA INTEGRATION")
        print("✂️ FMP удален навсегда")
        print("🆕 Twelve Data добавлен с market movers")
        print("🔍 Фильтрация спама включена")
        print("Ctrl+C для остановки\n")

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                print(f"\n>>> ЦИКЛ #{cycle_count} <<<")

                try:
                    self.run_cycle()

                    print("⏰ Пауза 5 сек...")
                    for i in range(5):
                        time.sleep(1)
                        if i == 2:
                            print(".", end="", flush=True)
                    print()

                except Exception as e:
                    print(f"❌ Ошибка цикла: {e}")
                    time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n🛑 ОСТАНОВЛЕНО")
            print(f"Циклов выполнено: {cycle_count}")


def main():
    print("🔬 SURGICAL FIX + TWELVE DATA INTEGRATION")
    print("=" * 50)

    try:
        fetcher = SurgicalTwelveDataFetcher()

        if not fetcher.clients:
            print("\n❌ Нет API ключей!")
            return

        print("\n🔬 ХИРУРГИЧЕСКИЕ ИЗМЕНЕНИЯ:")
        print("✂️ FMP полностью удален (проблемный)")
        print("🆕 Twelve Data добавлен (market movers)")
        print("✅ Фильтры работают для всех источников")
        print("⚡ Архитектура сохранена")

        print("\nРежимы:")
        print("1 - Тестовый цикл")
        print("2 - Мониторинг с Twelve Data")

        choice = input("\nВыбор (1-2): ").strip()

        if choice == "1":
            fetcher.run_cycle()
        else:
            fetcher.run_forever()

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()

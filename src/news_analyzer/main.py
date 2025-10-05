import os
import sys
import locale
import warnings
import pandas as pd
import json
import re
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List

# Критическая настройка UTF-8 перед всеми импортами
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8:strict'
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['LANG'] = 'C.UTF-8'

if os.name == 'nt':
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except:
        pass

try:
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            warnings.warn("Не удалось установить UTF-8 локаль")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
else:
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print(f"Системное кодирование: {sys.getdefaultencoding()}")
print(f"Локальное кодирование: {locale.getpreferredencoding()}")
print(f"Локаль: {locale.getlocale()}")
print(f"UTF-8 режим: {getattr(sys.flags, 'utf8_mode', False)}")

from news_analyzer.core.news_loader import NewsLoader
from news_analyzer.core.hotness_calculator import HotnessCalculator
from news_analyzer.core.entity_extractor import EntityExtractor
from news_analyzer.core.timeline_builder import TimelineBuilder
from news_analyzer.models.output_models import RadarOutput, BatchRadarOutput
from news_analyzer.config.settings import TOP_NEWS_COUNT
from news_analyzer.utils.cache import CacheManager
from news_analyzer.core.llm_client import AsyncLLMClient as LLMClient

# Параметры для адаптивного расчета
HOT_NEWS_THRESHOLD = 0.15
ADAPTIVE_TARGET_COUNT = 15
ADAPTIVE_MIN_THRESHOLD = 0.1
ADAPTIVE_MAX_THRESHOLD = 0.4
TOP_NEWS_COUNT_OPTIMIZED = 15


def calculate_adaptive_threshold(news_scores, target_count=15, min_threshold=0.1, max_threshold=0.4):
    """Вычисляет адаптивный порог для получения желаемого количества новостей"""
    if len(news_scores) < target_count:
        return min_threshold

    sorted_scores = sorted([score for score in news_scores if score > 0], reverse=True)

    if len(sorted_scores) >= target_count:
        adaptive_threshold = sorted_scores[target_count - 1]
        adaptive_threshold = max(min_threshold, min(max_threshold, adaptive_threshold))
    else:
        adaptive_threshold = min_threshold

    return adaptive_threshold


def ensure_minimum_news(hot_news, all_news_with_scores, min_count=10):
    """Гарантирует минимальное количество новостей в выводе"""
    if len(hot_news) >= min_count:
        return hot_news

    remaining_news = [item for item in all_news_with_scores if item not in hot_news]
    remaining_news.sort(key=lambda x: x[1].total, reverse=True)

    additional_needed = min_count - len(hot_news)
    hot_news.extend(remaining_news[:additional_needed])

    return hot_news


def log_hotness_analysis(news_item, score, threshold):
    """Подробное логирование для понимания оценок"""
    if score.total >= threshold * 0.8:
        print(f"\nАНАЛИЗ: {news_item.title[:50]}...")
        print(f" Unexpectedness: {score.unexpectedness:.3f}")
        print(f" Materiality: {score.materiality:.3f}")
        print(f" Velocity: {score.velocity:.3f}")
        print(f" Breadth: {score.breadth:.3f}")
        print(f" Source Trust: {score.source_trust:.3f}")
        print(f" ИТОГО: {score.total:.3f} ({'ПРОХОДИТ' if score.total >= threshold else 'НЕ ПРОХОДИТ'})")


class RadarNewsAnalyzer:
    """Асинхронный анализатор новостей RADAR"""

    def __init__(self):
        self.news_loader = NewsLoader()
        self.hotness_calculator = HotnessCalculator()
        self.llm_client = LLMClient()
        self.entity_extractor = EntityExtractor(self.llm_client)
        self.timeline_builder = TimelineBuilder(self.llm_client)
        self.cache = CacheManager()

        print("RADAR асинхронная версия загружена")
        print("Цель: высокопроизводительный анализ новостей")
        print("Улучшенная система горячности")
        print()

    async def analyze_news_file_async(self, file_path: str) -> BatchRadarOutput:
        """АСИНХРОННЫЙ анализ новостей из JSON файла"""
        print("=" * 60)
        print(f"RADAR: Асинхронный анализ файла {file_path}")
        print("=" * 60)

        # Загружаем новости
        news_data = self.news_loader.load_json(file_path)
        print(f"Загружено новостей: {len(news_data.news)}")

        # Статистика исходных данных
        stats = self.news_loader.get_statistics(news_data)
        print(f"Уникальных новостей: {stats['unique_news']}")
        print(f"Групп дубликатов: {stats['duplicate_groups']}")
        print(f"Средняя надежность: {stats['avg_credibility']:.1f}")
        print(f"Языки: {list(stats['languages'].keys())}")
        print(f"Категории: {list(stats['categories'].keys())}")

        print("-" * 40)
        print("Фильтрация по надежности источников")
        print("-" * 40)

        # Фильтруем по надежности
        filtered_data = self.news_loader.filter_by_credibility(news_data, min_credibility=6)
        print(f"После фильтрации: {len(filtered_data.news)} новостей")

        print("-" * 40)
        print("Расчет горячности")
        print("-" * 40)

        # Рассчитываем горячность для всех новостей
        all_news_with_scores = []
        all_scores = []

        for item in filtered_data.news:
            score = self.hotness_calculator.calculate_hotness(item)
            all_news_with_scores.append((item, score))
            all_scores.append(score.total)
            print(f"{item.title[:50]}... - {score.total:.3f}")

        # АДАПТИВНЫЙ РАСЧЕТ ПОРОГА
        adaptive_threshold = calculate_adaptive_threshold(
            all_scores,
            target_count=ADAPTIVE_TARGET_COUNT,
            min_threshold=ADAPTIVE_MIN_THRESHOLD,
            max_threshold=ADAPTIVE_MAX_THRESHOLD
        )

        # Используем адаптивный порог
        HOT_NEWS_THRESHOLD_ACTUAL = adaptive_threshold
        print(f"Адаптивный порог горячности: {HOT_NEWS_THRESHOLD_ACTUAL:.3f}")
        print(
            f" (Целевое количество: {ADAPTIVE_TARGET_COUNT}, мин: {ADAPTIVE_MIN_THRESHOLD}, макс: {ADAPTIVE_MAX_THRESHOLD})")

        # Фильтруем горячие новости
        hot_news = []
        for item, score in all_news_with_scores:
            if score.total >= HOT_NEWS_THRESHOLD_ACTUAL:
                hot_news.append((item, score))

            # Подробное логирование для отладки
            if score.total >= 0.4:
                print(f"ВЫСОКАЯ ({score.total:.3f}): {item.title[:60]}...")
                explanations = self.hotness_calculator.get_hotness_explanation(item, score)
                for component, explanation in explanations.items():
                    if component != 'total':
                        print(f" {explanation}")

        # FALLBACK механизм - гарантируем минимальное количество
        hot_news = ensure_minimum_news(hot_news, all_news_with_scores, min_count=10)

        # Сортируем по убыванию горячности
        hot_news.sort(key=lambda x: x[1].total, reverse=True)

        # Берем топ новостей
        top_news = hot_news[:TOP_NEWS_COUNT_OPTIMIZED]

        print(f"Найдено горячих новостей: {len(hot_news)}")
        print(f"Анализируем топ-{len(top_news)} новостей")

        # Группируем по дубликатам
        news_groups = self._group_news_by_duplicates(top_news)
        print(f"Сформировано групп: {len(news_groups)}")

        print("-" * 40)
        print("АСИНХРОННЫЙ LLM анализ")
        print("-" * 40)

        # АСИНХРОННО анализируем каждую группу через LLM
        radar_outputs = await self._analyze_all_groups_async(news_groups)

        # Формируем финальный результат
        result = BatchRadarOutput(
            timestamp=datetime.now(),
            top_events=radar_outputs,
            total_processed=len(news_data.news),
            hot_news_count=len(hot_news),
            processing_stats={
                "avg_hotness": sum(s.total for _, s in hot_news) / len(hot_news) if hot_news else 0,
                "groups_analyzed": len(news_groups),
                "api_calls_made": self.llm_client.api_calls_count,
                "duplicate_groups": stats['duplicate_groups'],
                "filtered_by_credibility": len(news_data.news) - len(filtered_data.news),
                "hotness_threshold_used": HOT_NEWS_THRESHOLD_ACTUAL,
                "language_count": len(stats['languages'])
            }
        )

        return result

    async def _analyze_all_groups_async(self, news_groups: dict) -> List[RadarOutput]:
        """АСИНХРОННЫЙ анализ всех групп новостей параллельно"""
        tasks = []
        for gid, group in news_groups.items():
            task = self._analyze_news_group_async(gid, group)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        radar_outputs = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Ошибка анализа группы: {result}")
                continue
            if result is not None:
                radar_outputs.append(result)

        return radar_outputs

    async def _analyze_news_group_async(self, gid: str, group_news: List) -> RadarOutput:
        """АСИНХРОННЫЙ анализ группы новостей через LLM"""
        try:
            print(f" Группа {gid}: {len(group_news)} новостей")

            # Выбираем новость с максимальной горячностью как главную
            main_news, main_hotness = max(group_news, key=lambda x: x[1].total)
            all_news = [news_item for news_item, _ in group_news]

            print(f" Главная новость: {main_news.title[:40]}...")
            print(f" Язык: {main_news.language or 'авто'}")
            print(f" Источник: {main_news.source}")

            # Параллельное выполнение задач
            entities_task = self.entity_extractor.extract_entities_async(main_news.content or main_news.title)
            timeline_task = self.timeline_builder.build_timeline_async(all_news)

            # Ждем завершения параллельных задач
            entities, timeline = await asyncio.gather(entities_task, timeline_task)

            print(
                f" Найдено: {len(entities.companies)} компаний, {len(entities.countries)} стран, {len(entities.people)} людей")

            # Формируем контекст для LLM
            context = f"Hotness: {main_hotness.total:.2f}, Sources: {len(all_news)}, Duplicates: {main_news.is_duplicate}"

            # Параллельная генерация контента
            why_now_task = self.llm_client.generate_why_now_async(main_news.content or main_news.title, context)
            headline_task = self.llm_client.generate_headline_async(main_news.content or main_news.title, entities)

            why_now, headline = await asyncio.gather(why_now_task, headline_task)

            # Генерируем черновик (зависит от why_now)
            draft = await self.llm_client.generate_draft_async(
                main_news.content or main_news.title,
                entities,
                why_now
            )

            # Собираем уникальные источники
            sources = list(set(news.url for news in all_news))

            # Формируем итоговый список сущностей
            entity_list = []
            if entities.companies:
                entity_list.extend([comp.get('name', str(comp)) for comp in entities.companies])
            if entities.countries:
                entity_list.extend(entities.countries)
            if entities.people:
                entity_list.extend(entities.people)
            if entities.instruments:
                entity_list.extend(entities.instruments)
            if entities.sectors:
                entity_list.extend(entities.sectors)

            result = RadarOutput(
                headline=headline,
                hotness=main_hotness.total,
                why_now=why_now,
                entities=entity_list[:20],  # Ограничиваем до 20 сущностей
                sources=sources[:5],  # Ограничиваем до 5 источников
                timeline=timeline,
                draft=draft,
                dedup_group=main_news.duplicate_group
            )

            print(f"Готово: {result.headline[:50]}... (горячность: {result.hotness:.3f})")
            return result

        except Exception as e:
            print(f"Ошибка анализа группы {gid}: {e}")
            import traceback
            print(f" Детали: {traceback.format_exc()}")
            return None

    def _group_news_by_duplicates(self, hot_news: List) -> dict:
        """Группировка новостей по дубликатам"""
        groups = {}
        for item, score in hot_news:
            # Уникальный ID для каждой новости или группы дубликатов
            gid = f"unique_{item.id}" if item.is_duplicate == -1 else f"duplicate_group_{item.is_duplicate}"
            groups.setdefault(gid, []).append((item, score))
        return groups

    def save_radar_csv(self, results: BatchRadarOutput, output_path: str):
        """Сохранение результатов в CSV формат"""
        print("-" * 40)
        print("Сохранение результатов в CSV")
        print("-" * 40)
        print(f"Создаем CSV файл: {output_path}")

        # Создаем директорию если не существует
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        csv_data = []
        for i, event in enumerate(results.top_events, 1):
            # Форматируем временную шкалу
            timeline_str = self._format_timeline(event.timeline)

            # Определяем категорию горячности
            hotness_category = self._categorize_hotness(event.hotness)

            # Анализируем типы сущностей
            entity_types = self._analyze_entity_types(event.entities)

            csv_row = {
                "rank": i,
                "headline": event.headline,
                "hotness_score": f"{event.hotness:.4f}",
                "hotness_category": hotness_category,
                "why_now": event.why_now,
                "dedup_group": event.dedup_group,
                "entities_all": "; ".join(event.entities[:15]),
                "entities_count": len(event.entities),
                "companies_detected": entity_types['companies'],
                "countries_detected": entity_types['countries'],
                "people_detected": entity_types['people'],
                "sources_count": len(event.sources),
                "sources_list": "; ".join([url[:50] + "..." if len(url) > 50 else url for url in event.sources[:3]]),
                "timeline_events": timeline_str,
                "timeline_count": len(event.timeline),
                "draft_headline": event.draft.headline,
                "draft_lead": event.draft.lead[:200] + "..." if len(event.draft.lead) > 200 else event.draft.lead,
                "draft_bullets": "; ".join(event.draft.bullets),
                "draft_quote": event.draft.quote
            }

            csv_data.append(csv_row)

        # Создаем DataFrame и сохраняем
        df = pd.DataFrame(csv_data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        print(f"Сохранено {len(csv_data)} записей в CSV")
        print(f"CSV содержит {len(df.columns)} колонок")
        print("Структура CSV:")
        for col in df.columns:
            print(f" - {col}")

    def _format_timeline(self, timeline: List) -> str:
        """Форматирование временной шкалы для CSV"""
        if not timeline:
            return ""

        formatted_events = []
        for event in timeline[:5]:  # Берем только первые 5 событий
            try:
                time_str = event.time.strftime("%H:%M")
                event_desc = event.event[:40] + "..." if len(event.event) > 40 else event.event
                formatted_events.append(f"{time_str}: {event_desc}")
            except:
                formatted_events.append(f"{event.event[:40]}")

        return " | ".join(formatted_events)

    def _categorize_hotness(self, hotness: float) -> str:
        """Категоризация уровня горячности"""
        if hotness >= 0.8:
            return "Экстремально горячая"
        elif hotness >= 0.6:
            return "Очень горячая"
        elif hotness >= 0.4:
            return "Горячая"
        elif hotness >= 0.2:
            return "Теплая"
        else:
            return "Обычная"

    def _analyze_entity_types(self, entities: List[str]) -> dict:
        """Анализ типов сущностей для CSV статистики"""
        # Паттерны для распознавания типов
        company_patterns = [
            r'\b\w+\s*(Inc|Corp|Ltd|Bank|Group|Company)\b',
            r'\b(Apple|Microsoft|Tesla)\b',
            r'\b[A-Z]{2,5}\b'  # Тикеры
        ]

        country_patterns = [
            r'\b(США|Россия|Китай|Германия|Япония|США|Франция)\b',
            r'\b(USA|Russia|China|Germany|Japan|UK|France)\b'
        ]

        people_patterns = [
            r'\b[А-ЯA-Z][а-яa-z]+ [А-ЯA-Z][а-яa-z]+\b',
            r'\b(Putin|Trump|Biden)\b'
        ]

        companies = []
        countries = []
        people = []

        for entity in entities:
            if any(re.search(pattern, entity, re.IGNORECASE) for pattern in company_patterns):
                companies.append(entity)
            elif any(re.search(pattern, entity, re.IGNORECASE) for pattern in country_patterns):
                countries.append(entity)
            elif any(re.search(pattern, entity, re.IGNORECASE) for pattern in people_patterns):
                people.append(entity)

        return {
            'companies': len(companies),
            'countries': len(countries),
            'people': len(people)
        }

    def save_results_json(self, results: BatchRadarOutput, output_path: str):
        """Сохранение результатов в JSON формат"""
        # Создаем директорию если не существует
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Конвертируем в словарь
        output_data = results.model_dump()

        # Обрабатываем временные метки
        output_data['timestamp'] = results.timestamp.isoformat()

        for event in output_data['top_events']:
            for timeline_item in event['timeline']:
                timeline_item['time'] = timeline_item['time'].isoformat()

        # Сохраняем в файл
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"JSON результаты сохранены: {output_path}")

    def print_final_statistics(self, results: BatchRadarOutput):
        """Вывод финальной статистики"""
        print("=" * 60)
        print("ФИНАЛЬНАЯ СТАТИСТИКА RADAR ASYNC")
        print("=" * 60)

        stats = results.processing_stats
        print(f"Всего обработано новостей: {results.total_processed}")
        print(f"Горячих новостей найдено: {results.hot_news_count}")
        print(f"Итоговых событий: {len(results.top_events)}")
        print(f"LLM вызовов: {stats['api_calls_made']}")
        print(f"Средняя горячность: {stats['avg_hotness']:.3f}")
        print(f"Языков: {stats.get('language_count', 0)}")
        print(f"Дубликатов: {stats.get('duplicate_groups', 0)}")
        print(f"Групп проанализировано: {stats['groups_analyzed']}")
        print(f"Порог горячности: {stats.get('hotness_threshold_used', HOT_NEWS_THRESHOLD)}")

        print("-" * 40)
        print("ТОП-3 САМЫХ ГОРЯЧИХ СОБЫТИЯ:")
        print("-" * 40)

        for i, event in enumerate(results.top_events[:3], 1):
            print(f"{i}. {event.headline}")
            print(f" Горячность: {event.hotness:.3f}")
            print(f" Почему сейчас: {event.why_now[:100]}...")
            print(f" Сущности ({len(event.entities)}): {', '.join(event.entities[:5])}")
            print(f" Источников: {len(event.sources)}")


async def main():
    """АСИНХРОННАЯ главная функция запуска RADAR"""
    print("=" * 60)
    print("RADAR News Analysis System - АСИНХРОННАЯ ВЕРСИЯ")
    print("=" * 60)

    analyzer = RadarNewsAnalyzer()

    # Параметры файлов
    input_file = "test_news.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"data/processed/radar_analysis_{timestamp}.csv"
    output_json = f"data/processed/radar_full_{timestamp}.json"

    # Создаем необходимые директории
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("data/cache").mkdir(parents=True, exist_ok=True)

    try:
        # Проверяем наличие входного файла
        if not Path(input_file).exists():
            print(f"Файл {input_file} не найден!")
            return

        # АСИНХРОННО запускаем анализ
        results = await analyzer.analyze_news_file_async(input_file)

        # Сохраняем результаты
        analyzer.save_radar_csv(results, output_csv)
        analyzer.save_results_json(results, output_json)

        # Выводим финальную статистику
        analyzer.print_final_statistics(results)

        print("=" * 60)
        print("АСИНХРОННЫЙ АНАЛИЗ ЗАВЕРШЕН УСПЕШНО!")
        print("=" * 60)
        print(f"Результаты CSV: {output_csv}")
        print(f"Полный JSON: {output_json}")
        print("=" * 60)

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        print(f"Детали:\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    # Запускаем асинхронную версию
    asyncio.run(main())

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List

from news_analyzer.core.news_loader import NewsLoader
from news_analyzer.core.hotness_calculator import HotnessCalculator
from news_analyzer.core.llm_client import LLMClient
from news_analyzer.core.entity_extractor import EntityExtractor
from news_analyzer.core.timeline_builder import TimelineBuilder
from news_analyzer.models.output_models import RadarOutput, BatchRadarOutput
from news_analyzer.config.settings import TOP_NEWS_COUNT, HOT_NEWS_THRESHOLD
from news_analyzer.utils.cache import CacheManager


class RadarNewsAnalyzer:
    """Главный класс системы анализа новостей RADAR"""

    def __init__(self):
        self.news_loader = NewsLoader()
        self.hotness_calculator = HotnessCalculator()
        self.llm_client = LLMClient()
        self.entity_extractor = EntityExtractor(self.llm_client)
        self.timeline_builder = TimelineBuilder(self.llm_client)
        self.cache = CacheManager()

    async def analyze_news_file(self, file_path: str) -> BatchRadarOutput:
        """Основная функция анализа JSON файла"""

        print(f"📂 Загружаем новости из {file_path}")

        # 1. Загрузка и валидация
        news_data = self.news_loader.load_json(file_path)
        print(f"✅ Загружено {len(news_data.news)} новостей")

        # 2. Расчет горячести
        print("🔥 Рассчитываем горячность...")
        hot_news = []

        for news_item in news_data.news:
            hotness_score = await self.hotness_calculator.calculate_hotness(news_item)

            if hotness_score.total >= HOT_NEWS_THRESHOLD:
                hot_news.append((news_item, hotness_score))
                print(f"🌟 Горячая новость ({hotness_score.total:.3f}): {news_item.title[:50]}...")

        # 3. Топ-N самых горячих
        hot_news.sort(key=lambda x: x.total, reverse=True)
        top_news = hot_news[:TOP_NEWS_COUNT]

        print(f"🔥 Найдено {len(hot_news)} горячих, анализируем топ-{len(top_news)}")

        # 4. Группировка по duplicate_group
        news_groups = self._group_news_by_dedup(top_news)

        # 5. LLM анализ каждой группы
        radar_outputs = []

        for group_id, group_news in news_groups.items():
            print(f"🤖 Анализируем группу: {group_id}")

            try:
                radar_output = await self._analyze_news_group(group_news)
                radar_outputs.append(radar_output)
            except Exception as e:
                print(f"❌ Ошибка группы {group_id}: {e}")
                continue

        # 6. Финальный результат
        result = BatchRadarOutput(
            timestamp=datetime.now(),
            top_events=radar_outputs,
            total_processed=len(news_data.news),
            hot_news_count=len(hot_news),
            processing_stats={
                "avg_hotness": sum(s.total for _, s in hot_news) / len(hot_news) if hot_news else 0,
                "groups_analyzed": len(news_groups),
                "api_calls_made": self.llm_client.api_calls_count
            }
        )

        return result

    def _group_news_by_dedup(self, hot_news: List) -> dict:
        """Группировка по duplicate_group"""
        groups = {}

        for news_item, hotness_score in hot_news:
            group_id = news_item.duplicate_group

            if group_id not in groups:
                groups[group_id] = []

            groups[group_id].append((news_item, hotness_score))

        return groups

    async def _analyze_news_group(self, group_news: List) -> RadarOutput:
        """Анализ группы связанных новостей"""

        # Основная новость - с максимальной горячностью
        main_news, main_hotness = max(group_news, key=lambda x: x.total)
        all_news = [item for item in group_news]

        # Извлечение сущностей
        entities = await self.entity_extractor.extract_entities(main_news.content)

        # Timeline
        timeline = await self.timeline_builder.build_timeline(all_news)

        # Why now объяснение
        why_now = await self.llm_client.generate_why_now(
            main_news.content,
            f"Hotness: {main_hotness.total:.2f}, Sources: {len(all_news)}"
        )

        # Черновик статьи
        draft = await self.llm_client.generate_draft(
            main_news.content, entities, why_now
        )

        # Заголовок события
        headline = await self.llm_client.generate_headline(main_news.content, entities)

        # Список источников
        sources = list(set([news.url for news in all_news]))

        # Список сущностей
        entity_list = []
        if entities.companies:
            entity_list.extend([comp.get('name', '') for comp in entities.companies])
        if entities.countries:
            entity_list.extend(entities.countries)
        if entities.people:
            entity_list.extend(entities.people)

        return RadarOutput(
            headline=headline,
            hotness=main_hotness.total,
            why_now=why_now,
            entities=entity_list[:20],
            sources=sources[:5],
            timeline=timeline,
            draft=draft,
            dedup_group=main_news.duplicate_group
        )

    async def save_results(self, results: BatchRadarOutput, output_path: str):
        """Сохранение результатов"""

        output_data = results.model_dump()

        # Конвертация datetime для JSON
        output_data['timestamp'] = results.timestamp.isoformat()

        for event in output_data['top_events']:
            for timeline_item in event['timeline']:
                timeline_item['time'] = timeline_item['time'].isoformat()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"💾 Результаты сохранены: {output_path}")


async def main():
    """Основная функция запуска"""

    analyzer = RadarNewsAnalyzer()

    # Пути файлов
    input_file = "data/sample_news.json"
    output_file = f"data/processed/radar_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Создаем папки если их нет
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("data/cache").mkdir(parents=True, exist_ok=True)

    try:
        # Создаем тестовые данные если файла нет
        if not Path(input_file).exists():
            print("📝 Создаем тестовые данные...")
            analyzer.news_loader.create_sample_data(input_file)

        # Анализ
        results = await analyzer.analyze_news_file(input_file)

        # Сохранение
        await analyzer.save_results(results, output_file)

        # Статистика
        print("\n📊 СТАТИСТИКА:")
        print(f"Всего новостей: {results.total_processed}")
        print(f"Горячих новостей: {results.hot_news_count}")
        print(f"Топ событий: {len(results.top_events)}")
        print(f"API вызовов: {results.processing_stats['api_calls_made']}")
        print(f"Средняя горячность: {results.processing_stats['avg_hotness']:.3f}")

        # Топ события
        print("\n🔥 ТОП СОБЫТИЯ:")
        for i, event in enumerate(results.top_events[:3], 1):
            print(f"{i}. {event.headline} (hotness: {event.hotness:.3f})")
            print(f"   Why now: {event.why_now}")
            print()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
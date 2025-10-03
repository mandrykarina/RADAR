import pytest
from pathlib import Path

from news_analyzer.core import NewsLoader
from news_analyzer.core.hotness_calculator import HotnessCalculator
from main import RadarNewsAnalyzer


class TestIntegration:
    """Интеграционные тесты"""

    def test_news_loader(self):
        """Тест загрузки новостей"""
        loader = NewsLoader()

        # Создаем тестовые данные
        test_file = "data/test_news.json"
        loader.create_sample_data(test_file)

        # Загружаем
        news_data = loader.load_json(test_file)

        assert len(news_data.news) >= 2
        assert news_data.news.title
        assert news_data.news.content

        # Очистка
        Path(test_file).unlink()

    @pytest.mark.asyncio
    async def test_hotness_calculation(self):
        """Тест расчета горячности"""
        loader = NewsLoader()
        calculator = HotnessCalculator()

        # Создаем тестовые данные
        test_file = "data/test_hotness.json"
        loader.create_sample_data(test_file)

        news_data = loader.load_json(test_file)
        news_item = news_data.news

        # Рассчитываем горячность
        hotness = await calculator.calculate_hotness(news_item)

        assert 0 <= hotness.total <= 1
        assert 0 <= hotness.suddenness <= 1
        assert 0 <= hotness.materiality <= 1
        assert hotness.reasoning

        # Очистка
        Path(test_file).unlink()

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Тест полного пайплайна (без LLM вызовов)"""

        # Настройка без API ключа для теста
        import os
        os.environ['OPENAI_API_KEY'] = 'test_key'

        analyzer = RadarNewsAnalyzer()

        # Создаем тестовые данные
        test_file = "data/test_pipeline.json"
        analyzer.news_loader.create_sample_data(test_file)

        try:
            # Тест только расчета горячности (без LLM)
            news_data = analyzer.news_loader.load_json(test_file)

            hot_news = []
            for news_item in news_data.news:
                hotness = await analyzer.hotness_calculator.calculate_hotness(news_item)
                if hotness.total > 0.5:  # более низкий порог для теста
                    hot_news.append((news_item, hotness))

            assert len(hot_news) > 0

        finally:
            # Очистка
            Path(test_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
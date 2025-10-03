from datetime import datetime

from news_analyzer.models.data_models import NewsItem, HotnessScores
from news_analyzer.config.settings import HOTNESS_WEIGHTS, SOURCE_RATINGS, VOLATILITY_KEYWORDS
from news_analyzer.utils.text_processing import TextProcessor

class HotnessCalculator:
    """Калькулятор горячности новостей по алгоритму RADAR"""

    def __init__(self):
        self.weights = HOTNESS_WEIGHTS
        self.source_ratings = SOURCE_RATINGS
        self.volatility_keywords = VOLATILITY_KEYWORDS
        self.text_processor = TextProcessor()

    async def calculate_hotness(self, news_item: NewsItem) -> HotnessScores:
        """Основная функция расчета горячности"""

        # Расчет всех компонентов
        suddenness = self._calculate_suddenness(news_item)
        materiality = self._calculate_materiality(news_item)
        spread_speed = self._calculate_spread_speed(news_item)
        scope = self._calculate_scope(news_item)
        source_trust = self._calculate_source_trust(news_item)

        # Взвешенная сумма
        total = (
                suddenness * self.weights['suddenness'] +
                materiality * self.weights['materiality'] +
                spread_speed * self.weights['spread_speed'] +
                scope * self.weights['scope'] +
                source_trust * self.weights['source_trust']
        )

        return HotnessScores(
            suddenness=suddenness,
            materiality=materiality,
            spread_speed=spread_speed,
            scope=scope,
            source_trust=source_trust,
            total=min(1.0, total),
            reasoning=f"Материальность: {materiality:.2f}, Неожиданность: {suddenness:.2f}"
        )

    def _calculate_suddenness(self, news_item: NewsItem) -> float:
        """Неожиданность относительно консенсуса (0-0.3)"""

        text = f"{news_item.title} {news_item.content}".lower()

        # 1. Ключевые слова неожиданности
        surprise_keywords = [
            'неожиданно', 'внезапно', 'шокирует', 'сенсация',
            'впервые', 'экстренно', 'срочно', 'нарушение', 'удивил'
        ]

        surprise_count = sum(1 for kw in surprise_keywords if kw in text)
        keyword_surprise = min(1.0, surprise_count / 3.0)

        # 2. Время публикации (внерабочее время = больше неожиданности)
        hour = news_item.published_at.hour
        time_surprise = 0.8 if hour < 8 or hour > 20 else 0.3

        # 3. Штраф за плановые события
        planned_keywords = ['плановый', 'ожидаемый', 'анонсированный']
        is_planned = any(kw in text for kw in planned_keywords)
        planned_penalty = 0.3 if is_planned else 1.0

        return min(1.0, (keyword_surprise + time_surprise) / 2.0 * planned_penalty)

    def _calculate_materiality(self, news_item: NewsItem) -> float:
        """Материальность для цены/волатильности (0-0.25)"""

        text = f"{news_item.title} {news_item.content}".lower()

        # 1. Ключевые слова волатильности
        keyword_score = 0
        for keyword, weight in self.volatility_keywords.items():
            if keyword in text:
                keyword_score += weight

        keyword_materiality = min(1.0, keyword_score / 2.0)

        # 2. Крупные компании/организации
        major_entities = [
            'apple', 'microsoft', 'google', 'amazon', 'tesla',
            'цб рф', 'фрс', 'сбербанк', 'газпром', 'лукойл'
        ]
        entity_count = sum(1 for entity in major_entities if entity in text)
        entity_materiality = min(1.0, entity_count / 2.0)

        # 3. Большие числа (суммы/проценты)
        numbers = self.text_processor.extract_numbers(text)
        large_numbers = [n for n in numbers if n > 1e9 or (n > 5 and '%' in text)]
        number_materiality = min(1.0, len(large_numbers) / 2.0)

        return (keyword_materiality + entity_materiality + number_materiality) / 3.0

    def _calculate_spread_speed(self, news_item: NewsItem) -> float:
        """Скорость распространения (0-0.2)"""

        # 1. Скорость подтверждений
        confirmation_speed = min(1.0, news_item.confirmation_count / 5.0)

        # 2. Авторитет источника влияет на скорость
        source_speed_multipliers = {
            'reuters': 0.9, 'bloomberg': 0.8, 'newsapi': 0.7, 'finnhub': 0.6
        }

        source_name = news_item.source.lower()
        source_multiplier = 0.5
        for src, mult in source_speed_multipliers.items():
            if src in source_name:
                source_multiplier = mult
                break

        # 3. Фактор времени (свежие новости быстрее)
        time_diff_hours = (datetime.now() - news_item.published_at).total_seconds() / 3600
        time_factor = max(0.1, 1.0 - (time_diff_hours / 24.0))

        return (confirmation_speed + source_multiplier + time_factor) / 3.0

    def _calculate_scope(self, news_item: NewsItem) -> float:
        """Широта затрагиваемых активов (0-0.15)"""

        # 1. Разнообразие сущностей
        entity_diversity = min(1.0, len(set(news_item.entities)) / 5.0)

        # 2. Разнообразие ключевых слов
        keyword_diversity = min(1.0, len(set(news_item.keywords)) / 8.0)

        # 3. Секторный охват
        text = f"{news_item.title} {news_item.content}".lower()
        sectors = [
            'банк', 'технолог', 'энергетика', 'металлургия',
            'телеком', 'ритейл', 'транспорт', 'недвижимость'
        ]
        sector_count = sum(1 for sector in sectors if sector in text)
        sector_scope = min(1.0, sector_count / 3.0)

        # 4. Географический охват
        regions = ['россия', 'сша', 'европа', 'китай', 'азия', 'глобальн']
        region_count = sum(1 for region in regions if region in text)
        geo_scope = min(1.0, region_count / 2.0)

        return (entity_diversity + keyword_diversity + sector_scope + geo_scope) / 4.0

    def _calculate_source_trust(self, news_item: NewsItem) -> float:
        """Достоверность источника (0-0.1)"""

        # 1. Базовый рейтинг источника
        source_name = news_item.source.lower()
        base_rating = 0.5

        for src, rating in self.source_ratings.items():
            if src in source_name:
                base_rating = rating
                break

        # 2. Бонус от подтверждений
        confirmation_boost = min(1.0, news_item.confirmation_count / 3.0)

        # 3. Используем готовый credibility_score
        final_trust = (base_rating + news_item.credibility_score + confirmation_boost) / 3.0

        return min(1.0, final_trust)
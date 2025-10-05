"""Оптимизированный расширенный калькулятор горячности с поддержкой нового формата данных"""

import re
import math
from typing import Dict, List, Set
from datetime import datetime, timedelta

from news_analyzer.models.data_models import NewsItem, HotnessScore
from news_analyzer.utils.financial_data import FinancialDataProvider
from news_analyzer.utils.text_processing import TextProcessor


class HotnessCalculator:
    """Оптимизированный калькулятор горячности новостей с более мягкими критериями"""

    def __init__(self):
        self.financial_data = FinancialDataProvider()
        self.text_processor = TextProcessor()

        # Расширенные ключевые слова на русском и английском
        self.impact_keywords = {
            'crisis': {
                'ru': ['кризис', 'обвал', 'крах', 'банкротство', 'дефолт', 'коллапс', 'паника',
                      'катастрофа', 'срочно', 'экстренно', 'чрезвычайный'],
                'en': ['crisis', 'crash', 'collapse', 'bankruptcy', 'default', 'panic',
                      'emergency', 'urgent', 'breaking', 'catastrophe', 'meltdown']
            },
            'growth': {
                'ru': ['рост', 'подъем', 'взлет', 'скачок', 'рекорд', 'максимум', 'прорыв',
                      'достижение', 'успех', 'триумф', 'бум'],
                'en': ['growth', 'surge', 'boom', 'record', 'high', 'peak', 'breakthrough',
                      'achievement', 'success', 'triumph', 'rally', 'spike']
            },
            'monetary': {
                'ru': ['ставка', 'процентная', 'монетарная', 'денежная', 'инфляция', 'дефляция',
                      'эмиссия', 'ликвидность', 'резерв', 'центробанк', 'цб'],
                'en': ['rate', 'interest', 'monetary', 'inflation', 'deflation', 'liquidity',
                      'federal reserve', 'central bank', 'fed', 'ecb', 'boe']
            },
            'market_movers': {
                'ru': ['санкции', 'война', 'конфликт', 'договор', 'соглашение', 'слияние',
                      'поглощение', 'ipo', 'размещение', 'листинг', 'делистинг'],
                'en': ['sanctions', 'war', 'conflict', 'deal', 'agreement', 'merger',
                      'acquisition', 'ipo', 'listing', 'delisting', 'spinoff']
            }
        }

        # РАСШИРЕННЫЕ финансовые сущности с добавлением средних компаний
        self.financial_entities = {
            'major_companies': {
                'ru': ['сбербанк', 'газпром', 'роснефт', 'лукойл', 'втб', 'норникель',
                      'яндекс', 'магнит', 'x5', 'мтс', 'мегафон', 'татнефт',
                      # ДОБАВЛЕННЫЕ средние компании для повышения materiality
                      'новатэк', 'полиметалл', 'металлоинвест', 'евраз', 'нлмк', 'северсталь'],
                'en': ['apple', 'microsoft', 'google', 'amazon', 'tesla', 'nvidia',
                      'meta', 'netflix', 'jpmorgan', 'goldman sachs', 'berkshire',
                      # ДОБАВЛЕННЫЕ средние компании для повышения materiality
                      'paypal', 'salesforce', 'adobe', 'shopify', 'zoom', 'docusign']
            },
            'currencies': {
                'ru': ['рубль', 'доллар', 'евро', 'юань', 'иена', 'фунт', 'франк',
                      'usdrub', 'eurrub', 'usdeur', 'gbpusd'],
                'en': ['dollar', 'euro', 'pound', 'yen', 'yuan', 'ruble', 'franc',
                      'usd', 'eur', 'gbp', 'jpy', 'cny', 'chf']
            },
            'commodities': {
                'ru': ['нефть', 'газ', 'золото', 'серебро', 'медь', 'алюминий', 'никель',
                      'пшеница', 'кукуруза', 'соя', 'brent', 'wti'],
                'en': ['oil', 'gas', 'gold', 'silver', 'copper', 'aluminum', 'nickel',
                      'wheat', 'corn', 'soybean', 'brent', 'wti', 'crude']
            },
            'indices': {
                'ru': ['ртс', 'мосбиржа', 'imoex', 'rgbi', 'micex'],
                'en': ['sp500', 's&p 500', 'nasdaq', 'dow', 'ftse', 'dax', 'nikkei',
                      'hang seng', 'shanghai composite', 'csi300']
            }
        }

        # Весовые коэффициенты для расчета горячности (оставляем как есть)
        self.weights = {
            'unexpectedness': 0.30,
            'materiality': 0.25,
            'velocity': 0.20,
            'breadth': 0.15,
            'source_trust': 0.10
        }

    def calculate_hotness(self, news_item: NewsItem) -> HotnessScore:
        """Основной метод расчета горячности новости"""
        score = HotnessScore()

        # Определяем язык для анализа ключевых слов
        language = self._detect_language(news_item)

        # 1. Неожиданность (Unexpectedness) - ОПТИМИЗИРОВАННЫЙ
        score.unexpectedness = self._calculate_unexpectedness(news_item, language)

        # 2. Материальность (Materiality) - ОПТИМИЗИРОВАННЫЙ
        score.materiality = self._calculate_materiality(news_item, language)

        # 3. Скорость распространения (Velocity) - ОПТИМИЗИРОВАННЫЙ
        score.velocity = self._calculate_velocity(news_item)

        # 4. Широта охвата (Breadth) - ОПТИМИЗИРОВАННЫЙ
        score.breadth = self._calculate_breadth(news_item, language)

        # 5. Доверие к источнику (Source Trust) - УЛУЧШЕННЫЙ
        score.source_trust = self._calculate_source_trust(news_item)

        # Итоговая оценка
        score.total = score.calculate_total(self.weights)

        return score

    def _detect_language(self, news_item: NewsItem) -> str:
        """Определение языка новости"""
        if news_item.language:
            return 'ru' if news_item.language in ['ru', 'russian'] else 'en'

        # Определяем по содержимому
        text = f"{news_item.title} {news_item.content or ''}"
        russian_chars = len(re.findall(r'[а-яёА-ЯЁ]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        return 'ru' if russian_chars > english_chars else 'en'

    def _calculate_unexpectedness(self, news_item: NewsItem, language: str) -> float:
        """ОПТИМИЗИРОВАННЫЙ расчет неожиданности события"""
        score = 0.0
        text = f"{news_item.title} {news_item.content or ''}".lower()

        # БАЗОВАЯ ОЦЕНКА для финансово-значимых категорий
        financial_categories = [
            'monetary policy', 'banking', 'technology', 'automotive',
            'energy', 'commodities', 'cryptocurrency', 'economic policy'
        ]
        if news_item.category in financial_categories:
            score += 0.2  # Базовый бонус для финансовых новостей

        # 1. Ключевые слова кризиса (более мягко)
        crisis_words = self.impact_keywords['crisis'][language]
        crisis_count = sum(1 for word in crisis_words if word in text)
        if crisis_count > 0:
            score += min(0.4, crisis_count * 0.12)  # Было 0.15

        # 2. Экстренные маркеры (более мягко)
        urgent_markers = ['срочно', 'breaking', 'urgent', 'экстренно', 'немедленно']
        urgent_count = sum(1 for marker in urgent_markers if marker in text)
        if urgent_count > 0:
            score += min(0.3, urgent_count * 0.15)  # Было 0.2

        # 3. Численные индикаторы неожиданности (снижаем порог)
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
        if percentages:
            max_change = max(float(p) for p in percentages)
            if max_change > 5:  # Было 10
                score += min(0.3, (max_change - 5) / 80)  # Было (max_change - 10) / 100

        # 4. Временные индикаторы
        time_urgency = ['впервые', 'first time', 'никогда', 'never', 'с начала',
                       'рекорд', 'record', 'исторический', 'historic']
        for marker in time_urgency:
            if marker in text:
                score += 0.12  # Было 0.15
                break

        # 5. НОВЫЙ: Корпоративные события
        corporate_events = ['слияние', 'поглощение', 'ipo', 'делистинг', 'банкротство',
                           'merger', 'acquisition', 'bankruptcy', 'spinoff', 'layoffs']
        for event in corporate_events:
            if event in text:
                score += 0.15
                break

        # 6. НОВЫЙ: Регулятивные изменения
        regulatory_words = ['запрет', 'ban', 'регулир', 'regulat', 'license', 'лицензия']
        for word in regulatory_words:
            if word in text:
                score += 0.1
                break

        return min(1.0, score)

    def _calculate_materiality(self, news_item: NewsItem, language: str) -> float:
        """ОПТИМИЗИРОВАННЫЙ расчет материальности влияния на рынки"""
        score = 0.0
        text = f"{news_item.title} {news_item.content or ''}".lower()

        # БАЗОВАЯ ОЦЕНКА для финансово-значимых категорий
        high_impact_categories = ['monetary policy', 'banking', 'economic policy']
        medium_impact_categories = ['technology', 'energy', 'commodities', 'automotive']

        if news_item.category in high_impact_categories:
            score += 0.3  # Высокий базовый бонус
        elif news_item.category in medium_impact_categories:
            score += 0.2  # Средний базовый бонус
        else:
            score += 0.1  # Минимальный бонус для остальных

        # 1. Крупные финансовые суммы (снижаем пороги)
        amounts = re.findall(r'(\d+(?:\.\d+)?)\s*(?:трлн|млрд|billion|trillion)', text)
        if amounts:
            max_amount = max(float(a) for a in amounts)
            if 'трлн' in text or 'trillion' in text:
                score += min(0.4, max_amount / 8)  # Было max_amount / 10
            elif 'млрд' in text or 'billion' in text:
                score += min(0.3, max_amount / 80)  # Было max_amount / 100

        # 2. РАСШИРЕННЫЙ список значимых компаний
        major_companies = self.financial_entities['major_companies'][language]
        company_mentions = sum(1 for company in major_companies if company in text)
        if company_mentions > 0:
            score += min(0.3, company_mentions * 0.08)  # Было 0.1

        # 3. Влияние на валюты и сырье (повышаем веса)
        currencies = self.financial_entities['currencies'][language]
        commodities = self.financial_entities['commodities'][language]

        currency_impact = sum(1 for curr in currencies if curr in text)
        commodity_impact = sum(1 for comm in commodities if comm in text)

        if currency_impact > 0:
            score += min(0.25, currency_impact * 0.1)  # Было 0.08
        if commodity_impact > 0:
            score += min(0.25, commodity_impact * 0.1)  # Было 0.08

        # 4. Индексы и широкие рынки
        indices = self.financial_entities['indices'][language]
        index_mentions = sum(1 for idx in indices if idx in text)
        if index_mentions > 0:
            score += min(0.25, index_mentions * 0.1)  # Было 0.12

        # 5. НОВЫЙ: Отраслевые маркеры
        sector_markers = {
            'ru': ['банковский сектор', 'нефтегазовый', 'металлургия', 'ритейл', 'телеком'],
            'en': ['banking sector', 'oil gas', 'mining', 'retail', 'telecom', 'fintech']
        }

        for marker in sector_markers.get(language, []):
            if marker in text:
                score += 0.15
                break

        # 6. НОВЫЙ: Капитализация и объемы
        market_size_words = ['капитализация', 'market cap', 'оборот', 'volume', 'торги']
        for word in market_size_words:
            if word in text:
                score += 0.1
                break

        return min(1.0, score)

    def _calculate_velocity(self, news_item: NewsItem) -> float:
        """ОПТИМИЗИРОВАННЫЙ расчет скорости распространения новости"""
        score = 0.0

        # БАЗОВАЯ ОЦЕНКА для финансовых категорий
        financial_categories = [
            'monetary policy', 'banking', 'technology', 'automotive',
            'energy', 'commodities', 'cryptocurrency', 'economic policy'
        ]
        if news_item.category in financial_categories:
            score += 0.25  # Базовый бонус для быстрого распространения финансовых новостей

        # 1. Надежность источника (более мягкие пороги)
        if news_item.source_credibility >= 8:
            score += 0.25  # Было 0.3
        elif news_item.source_credibility >= 7:  # НОВЫЙ порог
            score += 0.2   # Новый бонус
        elif news_item.source_credibility >= 6:
            score += 0.15  # Было 0.2

        # 2. Количество подтверждений (дубликатов)
        if news_item.is_duplicate != -1:
            confirmation_bonus = min(0.3, news_item.confirmation_count * 0.04)  # Было 0.05
            score += confirmation_bonus

        # 3. Временная близость к торговым сессиям
        if news_item.published_at:
            pub_hour = news_item.published_at.hour
            # Расширяем торговые часы
            if (8 <= pub_hour <= 17) or (13 <= pub_hour <= 22): # Было (9 <= pub_hour <= 16)
                score += 0.15  # Было 0.2

        # 4. НОВЫЙ: Приоритетные источники (больше источников)
        priority_sources = [
            'reuters', 'bloomberg', 'financial_times', 'wall_street_journal',
            'cnbc', 'marketwatch', 'yahoo_finance', 'investing_com',
            'interfax', 'ria', 'tass', 'vedomosti', 'rbc'
        ]
        if any(source in news_item.source.lower() for source in priority_sources):
            score += 0.1

        # 5. НОВЫЙ: Социальные сигналы и вирусность
        viral_indicators = ['trending', 'viral', 'breaking', 'alert', 'срочно']
        text = f"{news_item.title} {news_item.content or ''}".lower()
        for indicator in viral_indicators:
            if indicator in text:
                score += 0.1
                break

        # 6. Тикеры в новости (снижаем влияние)
        if news_item.tickers:
            score += min(0.2, len(news_item.tickers) * 0.04)  # Было 0.05

        return min(1.0, score)

    def _calculate_breadth(self, news_item: NewsItem, language: str) -> float:
        """ОПТИМИЗИРОВАННЫЙ расчет широты влияния на различные активы и рынки"""
        score = 0.0
        text = f"{news_item.title} {news_item.content or ''}".lower()

        # БАЗОВАЯ ОЦЕНКА по важности категории
        category_impact = {
            'monetary policy': 0.4,    # Максимальное влияние
            'economic policy': 0.4,    # Максимальное влияние
            'banking': 0.3,            # Высокое влияние
            'energy': 0.3,             # Высокое влияние
            'commodities': 0.3,        # Высокое влияние
            'technology': 0.25,        # Среднее влияние (крупный сектор)
            'automotive': 0.2,         # Среднее влияние
            'cryptocurrency': 0.25,    # Среднее влияние (волатильность)
            'media': 0.15,             # Низкое влияние
            'aerospace': 0.15,         # Низкое влияние
            'corporate': 0.1           # Базовое влияние
        }

        base_score = category_impact.get(news_item.category, 0.1)
        score += base_score

        affected_categories = set()

        # 1. Акции и корпоративные события
        if any(word in text for word in ['акции', 'shares', 'stock', 'equity']):
            affected_categories.add('equities')

        # 2. Валютные рынки
        currencies = self.financial_entities['currencies'][language]
        if any(curr in text for curr in currencies):
            affected_categories.add('currencies')

        # 3. Сырьевые товары
        commodities = self.financial_entities['commodities'][language]
        if any(comm in text for comm in commodities):
            affected_categories.add('commodities')

        # 4. Облигации и долговые рынки
        bond_words = {
            'ru': ['облигации', 'долг', 'займ', 'доходность', 'кредит'],
            'en': ['bonds', 'debt', 'yield', 'credit', 'treasury']
        }
        if any(word in text for word in bond_words[language]):
            affected_categories.add('fixed_income')

        # 5. Криптовалюты
        crypto_words = {
            'ru': ['биткоин', 'эфириум', 'криптовалюта', 'блокчейн'],
            'en': ['bitcoin', 'ethereum', 'cryptocurrency', 'blockchain', 'crypto']
        }
        if any(word in text for word in crypto_words[language]):
            affected_categories.add('crypto')

        # УЛУЧШЕННАЯ оценка по количеству затронутых категорий
        category_bonus = len(affected_categories) * 0.1  # Было 0.15
        score += min(0.3, category_bonus)

        # 6. НОВЫЙ: Отраслевое влияние
        sector_multipliers = {
            'финансы': 0.2, 'finance': 0.2,
            'энергетика': 0.15, 'energy': 0.15,
            'технологии': 0.15, 'tech': 0.15,
            'промышленность': 0.1, 'industrial': 0.1
        }

        for sector, bonus in sector_multipliers.items():
            if sector in text:
                score += bonus
                break

        # 7. Географическое влияние (оптимизированное)
        regions = []
        if language == 'ru':
            if any(word in text for word in ['россия', 'россии', 'российский', 'рф']):
                regions.append('russia')
            if any(word in text for word in ['сша', 'америка', 'американский']):
                regions.append('usa')
            if any(word in text for word in ['китай', 'китайский']):
                regions.append('china')
            if any(word in text for word in ['европа', 'европейский', 'ес', 'еврозона']):
                regions.append('europe')
        else:
            if any(word in text for word in ['usa', 'america', 'us', 'united states']):
                regions.append('usa')
            if any(word in text for word in ['china', 'chinese']):
                regions.append('china')
            if any(word in text for word in ['europe', 'eu', 'european', 'eurozone']):
                regions.append('europe')
            if any(word in text for word in ['russia', 'russian']):
                regions.append('russia')

        # Бонус за географическое влияние (увеличенный)
        if len(regions) >= 3:
            score += 0.3   # Глобальное влияние
        elif len(regions) == 2:
            score += 0.2   # Региональное влияние
        elif len(regions) == 1:
            score += 0.1   # Локальное влияние

        return min(1.0, score)

    def _calculate_source_trust(self, news_item: NewsItem) -> float:
        """УЛУЧШЕННЫЙ расчет доверия к источнику информации"""
        # Базовая оценка из source_credibility (1-10 -> 0-1)
        base_score = news_item.source_credibility / 10.0

        # РАСШИРЕННЫЕ бонусы за особо надежные источники
        premium_sources = [
            'reuters', 'bloomberg', 'financial_times', 'wall_street_journal',
            'central_bank', 'federal_reserve', 'ecb', 'boe', 'sec',
            'interfax', 'ria', 'tass', 'cbr.ru', 'government',
            # ДОБАВЛЕННЫЕ источники
            'cnbc', 'marketwatch', 'yahoo_finance', 'investing_com',
            'vedomosti', 'rbc', 'kommersant'
        ]

        if any(source in news_item.source.lower() for source in premium_sources):
            base_score = min(1.0, base_score + 0.1)

        # Штраф за непроверенные источники
        unreliable_indicators = ['blog', 'forum', 'social', 'rumor', 'speculation']
        if any(indicator in news_item.source.lower() for indicator in unreliable_indicators):
            base_score = max(0.0, base_score - 0.2)

        return base_score

    def get_hotness_explanation(self, news_item: NewsItem, score: HotnessScore) -> Dict[str, str]:
        """Получение объяснения компонентов оценки горячности"""
        language = self._detect_language(news_item)

        explanations = {
            'unexpectedness': f"Неожиданность: {score.unexpectedness:.3f} - " +
                            self._explain_unexpectedness(news_item, language),
            'materiality': f"Материальность: {score.materiality:.3f} - " +
                         self._explain_materiality(news_item, language),
            'velocity': f"Скорость: {score.velocity:.3f} - " +
                       self._explain_velocity(news_item),
            'breadth': f"Широта: {score.breadth:.3f} - " +
                      self._explain_breadth(news_item, language),
            'source_trust': f"Доверие: {score.source_trust:.3f} - " +
                          self._explain_source_trust(news_item),
            'total': f"Итого: {score.total:.3f} - " +
                    self._get_hotness_category(score.total)
        }

        return explanations

    def _explain_unexpectedness(self, news_item: NewsItem, language: str) -> str:
        """Объяснение оценки неожиданности"""
        text = f"{news_item.title} {news_item.content or ''}".lower()
        factors = []

        if any(word in text for word in self.impact_keywords['crisis'][language]):
            factors.append("кризисные маркеры")

        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
        if percentages:
            max_change = max(float(p) for p in percentages)
            if max_change > 5:  # Обновленный порог
                factors.append(f"значительное изменение ({max_change}%)")

        if not factors:
            factors.append("рутинное событие")

        return ", ".join(factors)

    def _explain_materiality(self, news_item: NewsItem, language: str) -> str:
        """Объяснение оценки материальности"""
        text = f"{news_item.title} {news_item.content or ''}".lower()
        factors = []

        if re.search(r'\d+\s*(?:трлн|млрд|billion|trillion)', text):
            factors.append("крупные суммы")

        major_companies = self.financial_entities['major_companies'][language]
        if any(company in text for company in major_companies):
            factors.append("значимые компании")

        if any(curr in text for curr in self.financial_entities['currencies'][language]):
            factors.append("валютные рынки")

        if not factors:
            factors.append("ограниченное влияние")

        return ", ".join(factors)

    def _explain_velocity(self, news_item: NewsItem) -> str:
        """Объяснение оценки скорости"""
        factors = []

        if news_item.source_credibility >= 7:  # Обновленный порог
            factors.append("надежный источник")

        if news_item.is_duplicate != -1:
            factors.append(f"подтверждения ({news_item.confirmation_count})")

        if not factors:
            factors.append("медленное распространение")

        return ", ".join(factors)

    def _explain_breadth(self, news_item: NewsItem, language: str) -> str:
        """Объяснение оценки широты влияния"""
        text = f"{news_item.title} {news_item.content or ''}".lower()
        affected = []

        if any(word in text for word in ['акции', 'shares', 'stock']):
            affected.append("акции")

        if any(curr in text for curr in self.financial_entities['currencies'][language]):
            affected.append("валюты")

        if any(comm in text for comm in self.financial_entities['commodities'][language]):
            affected.append("сырье")

        return ", ".join(affected) if affected else "узкое влияние"

    def _explain_source_trust(self, news_item: NewsItem) -> str:
        """Объяснение оценки доверия к источнику"""
        credibility_desc = {
            9: "максимальное доверие",
            8: "высокое доверие",
            7: "хорошее доверие",  # Обновлено для нового порога
            6: "среднее доверие",
            5: "умеренное доверие"
        }

        return credibility_desc.get(news_item.source_credibility, "низкое доверие")

    def _get_hotness_category(self, total_score: float) -> str:
        """Категоризация общей оценки горячности"""
        if total_score >= 0.8:
            return "экстремально горячая новость"
        elif total_score >= 0.6:
            return "очень горячая новость"
        elif total_score >= 0.4:
            return "горячая новость"
        elif total_score >= 0.2:
            return "теплая новость"
        else:
            return "обычная новость"

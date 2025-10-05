import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '1500'))

# Hotness calculation weights (по ТЗ RADAR)
HOTNESS_WEIGHTS = {
    'suddenness': 0.3,  # неожиданность относительно консенсуса
    'materiality': 0.25,  # материальность для цены/волатильности
    'spread_speed': 0.2,  # скорость распространения
    'scope': 0.15,  # широта затрагиваемых активов
    'source_trust': 0.1  # достоверность источника
}

# Analysis thresholds - КРИТИЧЕСКИ ПОНИЖЕНЫ ДЛЯ ДЕМОНСТРАЦИИ
HOT_NEWS_THRESHOLD = float(os.getenv('HOT_NEWS_THRESHOLD', '0.2'))  # Было 0.5, стало 0.2
WARM_NEWS_THRESHOLD = float(os.getenv('WARM_NEWS_THRESHOLD', '0.1'))  # Было 0.5, стало 0.1
TOP_NEWS_COUNT = int(os.getenv('TOP_NEWS_COUNT', '15'))  # Увеличиваем с 10 до 15

# Source credibility ratings
SOURCE_RATINGS = {
    'reuters': 0.95,
    'bloomberg': 0.9,
    'wsj': 0.9,
    'financial_times': 0.85,
    'finnhub': 0.8,
    'polygon': 0.8,
    'newsdata': 0.7,
    'newsapi': 0.75,
    'unknown': 0.5
}

# РАСШИРЕННЫЕ VOLATILITY_KEYWORDS для лучшего детекта горячности
VOLATILITY_KEYWORDS = {
    # Основные финансовые термины
    'финансы': 0.6,
    'finance': 0.6,
    'financial': 0.6,
    'экономика': 0.7,
    'economy': 0.7,
    'economic': 0.7,
    'рынки': 0.7,
    'markets': 0.7,
    'market': 0.7,
    'трейдинг': 0.6,
    'trading': 0.6,
    'инвестиции': 0.8,
    'investment': 0.8,

    # Криптовалюты
    'криптовалюта': 0.8,
    'cryptocurrency': 0.8,
    'crypto': 0.8,
    'биткоин': 0.9,
    'bitcoin': 0.9,
    'блокчейн': 0.8,
    'blockchain': 0.8,
    'эфириум': 0.9,
    'ethereum': 0.9,
    'defi': 0.7,
    'нфт': 0.6,
    'nft': 0.6,

    # Фондовый рынок
    'акции': 0.85,
    'stock': 0.85,
    'stocks': 0.85,
    'акционерный капитал': 0.8,
    'equity': 0.8,
    'дивиденды': 0.8,
    'dividend': 0.8,
    'ipo': 0.9,
    'spac': 0.7,
    'прибыли': 0.85,
    'earnings': 0.85,

    # Банкинг и бизнес
    'банк': 0.75,
    'bank': 0.75,
    'банковский': 0.75,
    'banking': 0.75,
    'финтех': 0.7,
    'fintech': 0.7,
    'бизнес': 0.7,
    'business': 0.7,
    'компания': 0.7,
    'company': 0.7,
    'корпоративный': 0.7,
    'corporate': 0.7,
    'генеральный директор': 0.8,
    'ceo': 0.8,
    'финансовый директор': 0.8,
    'cfo': 0.8,

    # НОВЫЕ КЛЮЧЕВЫЕ СЛОВА ДЛЯ ЛУЧШЕГО ПОКРЫТИЯ
    'price': 0.8,
    'цена': 0.8,
    'рост': 0.7,
    'growth': 0.7,
    'падение': 0.8,
    'decline': 0.8,
    'прорыв': 0.9,
    'breakthrough': 0.9,
    'новость': 0.5,
    'news': 0.5,
    'объявление': 0.7,
    'announcement': 0.7,
    'соглашение': 0.8,
    'agreement': 0.8,
    'партнерство': 0.7,
    'partnership': 0.7,
    'контракт': 0.8,
    'contract': 0.8,

    # Автомобильная индустрия (для Tesla и других)
    'автомобиль': 0.6,
    'car': 0.6,
    'automotive': 0.6,
    'tesla': 0.8,
    'electric': 0.7,
    'электрический': 0.7,
    'vehicle': 0.6,
    'транспорт': 0.6,

    # Технологические компании
    'технология': 0.7,
    'technology': 0.7,
    'tech': 0.7,
    'software': 0.7,
    'программное': 0.7,
    'ai': 0.8,
    'искусственный интеллект': 0.8,
    'data': 0.6,
    'данные': 0.6,

    # Медиа и коммуникации
    'медиа': 0.6,
    'media': 0.6,
    'коммуникации': 0.6,
    'communications': 0.6,
    'телеком': 0.6,
    'telecom': 0.6,

    # Экономические события
    'выручка': 0.85,
    'revenue': 0.85,
    'прибыль': 0.9,
    'profit': 0.9,
    'убытки': 0.85,
    'loss': 0.85,
    'слияние': 0.9,
    'merger': 0.9,
    'поглощение': 0.9,
    'acquisition': 0.9,
    'банкротство': 1.0,
    'bankruptcy': 1.0,
    'дефолт': 0.95,
    'default': 0.95,

    # Макроэкономика
    'инфляция': 0.9,
    'inflation': 0.9,
    'рецессия': 0.9,
    'recession': 0.9,
    'ввп': 0.8,
    'gdp': 0.8,
    'безработица': 0.7,
    'unemployment': 0.7,
    'процентная ставка': 0.9,
    'interest rates': 0.9,
    'федеральная резервная система': 0.85,
    'federal reserve': 0.85,
    'центральный банк': 0.85,
    'central bank': 0.85,

    # Облигации и кредиты
    'облигации': 0.7,
    'bonds': 0.7,
    'казначейские облигации': 0.7,
    'treasury': 0.7,
    'доходность': 0.7,
    'yield': 0.7,
    'спред': 0.7,
    'spread': 0.7,
    'кредит': 0.8,
    'credit': 0.8,
    'долг': 0.8,
    'debt': 0.8,
    'рейтинг': 0.8,
    'rating': 0.8,

    # Товары
    'нефть': 0.75,
    'oil': 0.75,
    'золото': 0.75,
    'gold': 0.75,
    'серебро': 0.7,
    'silver': 0.7,
    'медь': 0.7,
    'copper': 0.7,
    'энергия': 0.75,
    'energy': 0.75,
    'газ': 0.75,
    'gas': 0.75,

    # Форекс
    'форекс': 0.7,
    'forex': 0.7,
    'валюта': 0.85,
    'currency': 0.85,
    'usd': 0.85,
    'eur': 0.85,
    'jpy': 0.85,
    'gbp': 0.85,
    'обменный курс': 0.8,
    'exchange rate': 0.8,

    # Регуляторные новости
    'регулирование': 0.7,
    'regulation': 0.7,
    'sec': 0.8,
    'cftc': 0.8,
    'исковое заявление': 0.7,
    'lawsuit': 0.7,
    'расследование': 0.7,
    'investigation': 0.7,
    'санкции': 0.9,
    'sanctions': 0.9,
    'соблюдение': 0.7,
    'compliance': 0.7,

    # Фонды и инвестиции
    'etf': 0.8,
    'паи': 0.7,
    'mutual fund': 0.7,
    'хедж-фонд': 0.7,
    'hedge fund': 0.7,
    'управление активами': 0.8,
    'asset management': 0.8,
    'портфель': 0.7,
    'portfolio': 0.7,
    'vanguard': 0.7,
    'blackrock': 0.7
}

# Cache settings
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
CACHE_TTL_HOURS = int(os.getenv('CACHE_TTL_HOURS', '24'))
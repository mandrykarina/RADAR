# config.py - SURGICAL FIX + Twelve Data Integration
# ✅ FMP УДАЛЕН, добавлен Twelve Data

API_KEYS = {
    "newsapi": "bfab95463f0a470b89e8dd50ff0aebf7",
    "polygon": "fs0KdxS96Q8Pjt96G0T5KXT0rpKR_sip", 
    "finnhub": "d3ghv7hr01qpep66viq0d3ghv7hr01qpep66viqg",
    "marketaux": "O0PAhUdU3mm8MUwi8Tc1JXRDAb0pBU89fMnOivS9",
    "newsdata": "pub_3e37db7de78347b3af0f2cc25311109b"
}

RATE_LIMITS = {
    "newsapi": 60,
    "polygon": 12,
    "finnhub": 60,
    "marketaux": 864,
    "newsdata": 60
}

# ============= ПОИСКОВЫЕ КЛЮЧЕВЫЕ СЛОВА =============
FINANCIAL_KEYWORDS = {
    # Критические рыночные события
    "market_movers": [
        "crash", "surge", "rally", "plunge", "collapse", "meltdown", "rebound",
        "volatility", "flash crash", "circuit breaker", "trading halt", "trading suspended",
        "market crash", "stock crash", "crypto crash", "bull market", "bear market"
    ],

    # Центральные банки и монетарная политика
    "central_banks": [
        "federal reserve", "fed", "ecb", "european central bank", "bank of england",
        "bank of japan", "pboc", "people's bank of china", "central bank",
        "interest rate", "rate hike", "rate cut", "quantitative easing", "qe",
        "tapering", "monetary policy", "fomc", "jackson hole"
    ],

    # Макроэкономические показатели
    "macro_indicators": [
        "inflation", "cpi", "ppi", "deflation", "stagflation", "recession",
        "gdp", "gross domestic product", "unemployment", "employment",
        "retail sales", "consumer confidence", "manufacturing pmi", "services pmi"
    ],

    # Корпоративные события высокой важности
    "corporate_events": [
        "earnings report", "quarterly results", "profit warning", "guidance cut",
        "bankruptcy", "chapter 11", "insolvency", "default", "delisting",
        "merger", "acquisition", "m&a", "takeover", "hostile bid", "buyout",
        "ipo", "initial public offering", "spac", "stock split", "dividend cut"
    ],

    # Криптовалюты и блокчейн
    "crypto": [
        "bitcoin", "btc", "ethereum", "eth", "cryptocurrency", "crypto",
        "blockchain", "defi", "nft", "stablecoin", "binance", "coinbase"
    ]
}

# ============= ФИЛЬТРЫ КОНТЕНТА =============
CONTENT_FILTERS = {
    # Ключевые слова которые нужно ИСКЛЮЧИТЬ из результатов
    "exclude_keywords": [
        "advertisement", "sponsored", "promotion", "promo", "casino", 
        "gambling", "bet", "lottery", "porn", "adult", "spam"
    ],

    # Ключевые слова которые делают новость ВАЖНОЙ (приоритет)
    "priority_keywords": [
        "breaking", "urgent", "alert", "crisis", "crash", "surge", 
        "record", "massive", "unprecedented", "emergency", "federal reserve",
        "interest rate", "inflation", "recession", "bull market", "bear market"
    ],

    # Технические фильтры
    "min_title_length": 15,
    "max_title_length": 200,
    "min_description_length": 20,
    "allowed_languages": ["en", "ru"],

    # Источники которые нужно исключить
    "exclude_sources": [
        "promo.com", "ads.com", "casino", "gambling"
    ]
}

# ============= НАСТРОЙКИ ПРИМЕНЕНИЯ ФИЛЬТРОВ =============
FILTER_SETTINGS = {
    "apply_filters": True,
    "mark_priority": True, 
    "remove_duplicates": True,
    "sort_by_priority": True,
    "min_priority_score": 0.7,
    "max_results": 50,
    "time_window_hours": 24
}

# ============= НАСТРОЙКИ ПОИСКА ДЛЯ API =============
SEARCH_CONFIG = {
    "newsapi": {
        "query": "finance OR economy OR market OR stock OR banking OR investment OR bitcoin OR crypto OR inflation OR recession",
        "categories": ["business", "finance"],
        "language": "en",
        "page_size": 50
    },
    "polygon": {
        "limit": 50
    },
    "finnhub": {
        "category": "general"
    },
    "marketaux": {
        "limit": 50,
        "must_have_entities": True,
        "language": "en"
    },
    "newsdata": {
        "query": "finance OR economy OR market OR stock OR banking OR bitcoin OR crypto OR inflation OR recession",
        "categories": ["business", "finance"],
        "languages": ["en"],
        "size": 10
    }
}

# config.py
# Конфигурация для Rate-Limited News Fetcher

# ============= API КЛЮЧИ =============
API_KEYS = {
    "newsapi": "bfab95463f0a470b89e8dd50ff0aebf7",  # https://newsapi.org (безлимитный)
    "polygon": "fs0KdxS96Q8Pjt96G0T5KXT0rpKR_sip",  # https://polygon.io (5 запросов/минуту)
    "finnhub": "d3fqfopr01qolknedg00d3fqfopr01qolknedg0g",  # https://finnhub.io (1 запрос/секунду)
    "fmp": "5vfTeDjautq2siMpKix8QmiQ27mHrGnn",  # https://financialmodelingprep.com (250/день)
    "newsdata": "pub_3e37db7de78347b3af0f2cc25311109b"  # https://newsdata.io (200/день)
}

# ============= ПОИСКОВЫЕ ЗАПРОСЫ =============
# Ключевые слова для поиска финансовых новостей
SEARCH_KEYWORDS = {
    # Основные финансовые термины
    "finance": ["finance", "financial", "economy", "economic", "markets", "trading", "investment"],

    # Криптовалюты
    "crypto": ["bitcoin", "cryptocurrency", "crypto", "blockchain", "ethereum", "BTC", "ETH", "DeFi", "NFT"],

    # Фондовый рынок
    "stocks": ["stock", "stocks", "equity", "shares", "IPO", "SPAC", "earnings", "dividend"],

    # Банкинг и бизнес
    "banking": ["bank", "banking", "fintech", "business", "company", "corporate", "CEO", "CFO"],

    # Экономические события
    "events": ["revenue", "profit", "loss", "merger", "acquisition", "M&A", "bankruptcy", "default"],

    # Макроэкономика
    "macro": ["inflation", "recession", "GDP", "unemployment", "interest rates", "Federal Reserve", "central bank"],

    # Облигации и кредиты
    "bonds": ["bonds", "treasury", "yield", "spread", "credit", "debt", "rating"],

    # Товары
    "commodities": ["oil", "gold", "silver", "copper", "commodities", "crude", "energy"],

    # Форекс
    "forex": ["forex", "currency", "USD", "EUR", "JPY", "GBP", "exchange rate"],

    # Регуляторные новости
    "regulation": ["regulation", "SEC", "CFTC", "lawsuit", "investigation", "sanctions", "compliance"],

    # Фонды и инвестиции
    "funds": ["ETF", "mutual fund", "hedge fund", "asset management", "portfolio", "Vanguard", "BlackRock"]
}

# Формирование поискового запроса для каждого API
SEARCH_QUERIES = {
    "newsapi": {
        # Для NewsAPI используем OR между группами ключевых слов
        "main_query": "finance OR financial OR economy OR market OR trading OR investment OR "
                      "bitcoin OR crypto OR cryptocurrency OR blockchain OR "
                      "stock OR stocks OR equity OR shares OR IPO OR earnings OR "
                      "bank OR banking OR fintech OR business OR corporate OR "
                      "inflation OR recession OR GDP OR interest OR rates OR "
                      "bonds OR yield OR credit OR debt OR "
                      "oil OR gold OR commodities OR "
                      "forex OR currency OR USD OR "
                      "regulation OR SEC OR lawsuit OR "
                      "ETF OR fund OR asset",
        "categories": ["business", "finance"],
        "language": "en",
        "sort_by": "publishedAt"
    },

    "polygon": {
        "search_terms": ["finance", "market", "stock", "trading", "investment", "earnings", "economic"],
        "limit": 20
    },

    "finnhub": {
        "categories": ["general", "forex", "crypto", "merger"],
        "default_category": "general"
    },

    "fmp": {
        "search_terms": ["finance", "stock", "market", "earnings", "economic", "crypto", "banking"],
        "page_size": 20
    },

    "newsdata": {
        "query": "finance OR financial OR economy OR market OR trading OR "
                 "bitcoin OR crypto OR stock OR banking OR "
                 "inflation OR recession OR interest OR bonds OR oil OR gold",
        "categories": ["business", "finance"],
        "languages": ["en"],
        "size": 20
    }
}

# ============= РАСПИСАНИЕ ЗАПРОСОВ =============
# Интервалы между запросами (НЕ ИЗМЕНЯТЬ!)
RATE_LIMITS = {
    "newsapi": 60,  # секунд между запросами (безлимитный, но делаем раз в минуту)
    "polygon": 12,  # 5 запросов/минуту = каждые 12 сек
    "finnhub": 1,  # 1 запрос/секунду
    "fmp": 360,  # 250/день = каждые 6 минут
    "newsdata": 480  # 200/день = каждые 8 минут
}

# ============= ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ =============
# Общие настройки поиска
GENERAL_SETTINGS = {
    "default_page_size": 30,  # Количество статей по умолчанию
    "max_retries": 3,  # Количество повторов при ошибке
    "timeout": 30,  # Timeout запроса в секундах
    "save_results": True,  # Сохранять ли результаты в файлы
    "show_progress": True  # Показывать ли прогресс запросов
}

# Фильтрация новостей (опционально)
CONTENT_FILTERS = {
    # Ключевые слова высокого приоритета (делают новость "горячей")
    "hot_keywords": [
        # Внезапность и срочность
        "breaking", "urgent", "alert", "flash", "immediate", "sudden", "unexpected",

        # Рыночные движения
        "surge", "plunge", "crash", "collapse", "rally", "soar", "tumble", "plummet",
        "volatility", "flash crash", "circuit breaker", "trading halt",

        # Экстремальные события
        "crisis", "emergency", "default", "bankruptcy", "insolvency", "bailout",
        "takeover", "merger", "acquisition", "hostile bid",

        # Рекордные значения
        "record", "all-time high", "all-time low", "historic", "unprecedented",
        "massive", "huge", "major", "significant",

        # Регуляторные действия
        "investigation", "subpoena", "lawsuit", "sanctions", "ban", "restrictions",
        "raid", "probe", "settlement", "fine",

        # Макро-события
        "recession", "inflation", "deflation", "rate hike", "rate cut", "QE",
        "stimulus", "austerity", "default", "downgrade",

        # Корпоративные события
        "CEO resigns", "CFO leaves", "executive shakeup", "board change",
        "earnings miss", "profit warning", "guidance cut",

        # Геополитические риски
        "trade war", "embargo", "sanctions", "political crisis", "election upset"
    ],

    # Слова которые нужно исключить из результатов
    "exclude_keywords": [
        # Коммерческий контент
        "advertisement", "sponsored", "promotion", "advertorial", "paid post",

        # Нежелательные темы
        "casino", "gambling", "lottery", "betting", "poker",

        # Личные финансы (не институциональные)
        "personal finance", "retirement planning", "savings account", "mortgage tips",
        "how to invest", "investment tips", "trading for beginners",

        # Образовательный контент
        "tutorial", "guide", "explained", "for beginners", "what is",

        # Устаревшие форматы
        "newsletter", "recap", "summary", "weekly review", "monthly outlook",
        "year in review", "predictions for",

        # Нерелевантные сектора
        "celebrity", "entertainment", "sports", "lifestyle", "travel deals",
        "fashion", "beauty", "health tips"
    ],

    # Минимальная длина заголовка новости
    "min_title_length": 15,

    # Исключаемые источники (если есть спам)
    "exclude_sources": [
        "Motley Fool", "Seeking Alpha", "Investopedia",  # Образовательные/советующие
        "Benzinga", "The Street", "MarketWatch",  # Часто содержат спонсорский контент
        "Yahoo Finance Personal", "Forbes Advisor"  # Личные финансы
    ]
}
# config.py - FINAL STABLE

API_KEYS = {
    "newsapi": "bfab95463f0a470b89e8dd50ff0aebf7",
    "polygon": "fs0KdxS96Q8Pjt96G0T5KXT0rpKR_sip",
    "finnhub": "d3fqfopr01qolknedg00d3fqfopr01qolknedg0g",
    "fmp": "5vfTeDjautq2siMpKix8QmiQ27mHrGnn",
    "newsdata": "pub_3e37db7de78347b3af0f2cc25311109b"
}

# Упрощенные настройки для стабильности
SEARCH_QUERIES = {
    "newsapi": {"query": "finance OR bitcoin"},
    "polygon": {"limit": 8},
    "finnhub": {"category": "general"},
    "fmp": {"size": 8},
    "newsdata": {"size": 8}
}

RATE_LIMITS = {
    "newsapi": 60,
    "polygon": 12,
    "finnhub": 1,
    "fmp": 360,
    "newsdata": 480
}

GENERAL_SETTINGS = {
    "save_results": True,
    "show_progress": True
}

CONTENT_FILTERS = {
    "exclude_keywords": ["advertisement"],
    "min_title_length": 5
}

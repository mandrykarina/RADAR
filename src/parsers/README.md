# 📰 Configurable News Fetcher

Сборщик новостей с **поисковыми словами в конфиге** и строгим соблюдением лимитов.

## 🎯 Главные изменения

✅ **Все поисковые слова в config.py** - легко менять и настраивать  
✅ **Настройки для каждого API** - индивидуальные запросы  
✅ **Фильтры контента** - исключение спама и приоритет "горячих" слов  

## 🔍 Поисковые настройки

В `config.py` есть секция `SEARCH_QUERIES` с настройками для каждого API:

```python
SEARCH_QUERIES = {
    "newsapi": {
        "main_query": "finance OR bitcoin OR crypto OR stock OR market OR banking OR fintech",
        "categories": ["business"],
        "language": "en"
    },
    "newsdata": {
        "query": "finance OR bitcoin OR stock OR market",
        "categories": ["business"],
        "size": 10
    }
    # ... настройки для всех API
}
```

## 🚀 Запуск

1. `pip install requests`
2. Получить API ключи и вставить в `config.py`  
3. **Настроить поисковые слова** в `config.py` (опционально)
4. `python news_fetcher.py`

## ⚙️ Настройки поиска

Можно легко изменить что искать:

- **Финансовые термины:** finance, financial, economy
- **Криптовалюты:** bitcoin, cryptocurrency, blockchain  
- **Фондовый рынок:** stock, trading, investment
- **Банкинг:** bank, fintech, business
- **События:** earnings, IPO, merger

## 📊 Результат

Получаете JSON файлы с указанием настроек поиска:

```json
{
  "source": "newsapi",
  "search_config": {
    "main_query": "finance OR bitcoin OR crypto",
    "language": "en"
  },
  "articles_count": 15,
  "raw_data": {...}
}
```

**Готово к использованию!** 🎉

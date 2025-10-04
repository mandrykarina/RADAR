from loads2 import insert_article, close, prepare_database

example_json = {
  "id": "3e21bffe08be16f58896586be9d8073f",
  "title": "Polygon, Standard Chartered Enlisted for AlloyX Tokenized Money Market Fund",
  "content": "AlloyX, a Hong Kong-based stablecoin infrastructure firm...",
  "url": "https://www.coindesk.com/business/2025/10/02/polygon-standard-chartered-enlisted-for-alloyx-tokenized-money-market-fund",
  "source": "newsapi",


  "author": "Ian Allison, AI Boost",
  "language": "en",
  "country": None,
  "category": None,
  "tags": [],
  "tickers": [],
  "keywords": ["слово1", "слово2"],
  "entities": ["Компания", "Страна"],
  "sentiment": 0.0,
  "relevance": 0.0,
  "hotness": 0.0,

  "source_credibility": 0.8,
  "credibility_score": 0.85,
  "is_duplicate": -1,
  "collected_at": "2025-10-03T16:37:06.775903",
  "created_at": None,
  "updated_at": None,
  "published_at": "2025-10-02T12:00:50+00:00"
}

prepare_database() #Создать в базе нужные типы данных и таблицу (активировать единожды)
insert_article(example_json) #Добавить новость, автоматически сравнив
close() #Закрыть соединение
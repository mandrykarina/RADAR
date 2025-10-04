import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline

# --- Конфиг базы ---
DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5434
}

# --- Константы ---
DUPLICATE_LOOKBACK_DAYS = 1
SIMILARITY_THRESHOLD = 0.85

# --- Глобальные переменные для ленивой инициализации ---
conn = None
cursor = None
model = None
classifier = None
sentiment_analyzer = None

# ----------------- Существующий функционал -----------------
def init():
    global conn, cursor, model, classifier, sentiment_analyzer
    if conn is None:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    if model is None:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    if classifier is None:
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    if sentiment_analyzer is None:
        sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

def get_local_embedding(text: str):
    init()
    return model.encode(text, convert_to_numpy=True, show_progress_bar=False).tolist()

def fetch_recent_articles():
    init()
    cursor.execute("""
        SELECT id, is_duplicate, embedding, source_name
        FROM news_articles
        WHERE embedding IS NOT NULL
          AND published_at >= NOW() - INTERVAL '%s DAY'
    """, (DUPLICATE_LOOKBACK_DAYS,))
    return cursor.fetchall()

def classify_category(text: str) -> str:
    init()
    labels = ["finance", "crypto", "stocks", "macro"]
    result = classifier(text, labels)
    return result["labels"][0]

def analyze_sentiment(text: str):
    init()
    result = sentiment_analyzer(text[:512])[0]
    label = result["label"].lower()
    score = result["score"]
    if "positive" in label:
        return 1, "positive", score
    elif "negative" in label:
        return -1, "negative", score
    else:
        return 0, "neutral", score

def calculate_relevance(text: str, query: str = "finance") -> float:
    init()
    emb_text = model.encode(text, convert_to_numpy=True)
    emb_query = model.encode(query, convert_to_numpy=True)
    score = cosine_similarity([emb_text], [emb_query])[0][0]
    return float(score)

def insert_article(article_json: dict):
    init()

    cursor.execute("SELECT 1 FROM news_articles WHERE id = %s", (article_json['id'],))
    if cursor.fetchone():
        print(f"Новость {article_json['id']} уже есть в базе — пропускаем")
        return False

    text_for_embedding = ' '.join(filter(None, [
        article_json.get('title'),
        article_json.get('description'),
        article_json.get('content'),
        article_json.get('author'),
        article_json.get('source_name'),
        ' '.join(article_json.get('tags') or []),
        ' '.join(article_json.get('tickers') or [])
    ]))
    embedding = get_local_embedding(text_for_embedding)

    category = article_json.get('category') or classify_category(text_for_embedding)
    sentiment_value, sentiment_enum, sentiment_score = analyze_sentiment(text_for_embedding)
    relevance_score = calculate_relevance(text_for_embedding, query="finance news")
    hotness_score = article_json.get('hotness', 0.0)
    credibility_score = article_json.get('credibility', 0)

    recent_articles = fetch_recent_articles()
    duplicate_group_id = -1

    for existing in recent_articles:
        score = cosine_similarity([embedding], [existing['embedding']])[0][0]
        if score >= SIMILARITY_THRESHOLD:
            if existing['is_duplicate'] >= 0:
                duplicate_group_id = existing['is_duplicate']
            else:
                cursor.execute("SELECT COALESCE(MAX(is_duplicate), -1) + 1 AS new_group FROM news_articles")
                duplicate_group_id = cursor.fetchone()['new_group']
                cursor.execute("UPDATE news_articles SET is_duplicate = %s WHERE id = %s", (duplicate_group_id, existing['id']))
            break

    cursor.execute("""
        INSERT INTO news_articles
        (id, title, url, source, published_at, content, description, author, source_name,
         language, country, category, tags, tickers, sentiment, sentiment_score,
         relevance_score, hotness_score, is_duplicate, embedding, credibility_score)
        VALUES (%(id)s, %(title)s, %(url)s, %(source)s, %(published_at)s, %(content)s, %(description)s,
                %(author)s, %(source_name)s, %(language)s, %(country)s, %(category)s,
                %(tags)s, %(tickers)s, %(sentiment)s, %(sentiment_score)s,
                %(relevance_score)s, %(hotness_score)s, %(is_duplicate)s, %(embedding)s, %(credibility_score)s)
    """, {
        'id': article_json['id'],
        'title': article_json.get('title'),
        'url': article_json.get('url'),
        'source': article_json.get('source'),
        'published_at': article_json.get('published_at'),
        'content': article_json.get('content'),
        'description': article_json.get('description'),
        'author': article_json.get('author'),
        'source_name': article_json.get('source_name'),
        'language': article_json.get('language'),
        'country': article_json.get('country'),
        'category': category,
        'tags': article_json.get('tags') or [],
        'tickers': article_json.get('tickers') or [],
        'sentiment': sentiment_enum,
        'sentiment_score': sentiment_value,
        'relevance_score': relevance_score,
        'hotness_score': hotness_score,
        'is_duplicate': duplicate_group_id,
        'embedding': embedding,
        'credibility_score': credibility_score
    })
    conn.commit()
    print(f"Новость {article_json['id']} добавлена с категорией={category}, sentiment={sentiment_enum}, relevance={relevance_score:.2f}, hotness={hotness_score}, credibility={credibility_score}, is_duplicate={duplicate_group_id}")
    return True

def close():
    global conn, cursor
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    conn = None
    cursor = None

def prepare_database():
    conn_local = psycopg2.connect(**DB_PARAMS)
    conn_local.autocommit = True
    cursor_local = conn_local.cursor()

    cursor_local.execute("SELECT 1 FROM pg_type WHERE typname = 'news_source_enum'")
    if not cursor_local.fetchone():
        cursor_local.execute("""
            CREATE TYPE news_source_enum AS ENUM (
                'newsapi', 'polygon', 'finnhub', 'fmp', 'newsdata'
            )
        """)

    cursor_local.execute("SELECT 1 FROM pg_type WHERE typname = 'sentiment_enum'")
    if not cursor_local.fetchone():
        cursor_local.execute("""
            CREATE TYPE sentiment_enum AS ENUM (
                'positive', 'negative', 'neutral'
            )
        """)

    cursor_local.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            source news_source_enum NOT NULL,
            published_at TIMESTAMP WITH TIME ZONE NOT NULL,
            content TEXT,
            description TEXT,
            author TEXT,
            source_name TEXT,
            language VARCHAR(10),
            country VARCHAR(2),
            category VARCHAR(50),
            tags TEXT[] DEFAULT '{}',
            tickers TEXT[] DEFAULT '{}',
            sentiment sentiment_enum,
            sentiment_score DOUBLE PRECISION,
            relevance_score DOUBLE PRECISION,
            hotness_score DOUBLE PRECISION,
            is_duplicate INT DEFAULT -1,
            embedding DOUBLE PRECISION[],
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            credibility_score INTEGER
        )
    """)

    cursor_local.execute("ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS credibility_score INTEGER")

    cursor_local.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    cursor_local.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_set_updated_at'
            ) THEN
                CREATE TRIGGER trigger_set_updated_at
                BEFORE UPDATE ON news_articles
                FOR EACH ROW
                EXECUTE FUNCTION set_updated_at();
            END IF;
        END;
        $$;
    """)

    cursor_local.close()
    conn_local.close()
    print("База успешно подготовлена (enum, таблица, trigger set_updated_at).")

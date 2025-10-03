from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class NewsItem(BaseModel):
    """Модель новости из JSON файла друга"""
    id: str
    source: str
    source_credibility: float
    title: str
    content: str
    url: str
    published_at: datetime
    keywords: List[str]
    entities: List[str]
    collected_at: datetime
    dedup_hash: str
    credibility_score: float
    confirmation_count: int
    duplicate_group: str

class NewsData(BaseModel):
    """Модель всего JSON файла с новостями"""
    timestamp: datetime
    news: List[NewsItem]

class HotnessScores(BaseModel):
    """Результат расчета горячности по всем критериям"""
    suddenness: float = Field(ge=0, le=1, description="Неожиданность")
    materiality: float = Field(ge=0, le=1, description="Материальность")
    spread_speed: float = Field(ge=0, le=1, description="Скорость распространения")
    scope: float = Field(ge=0, le=1, description="Широта охвата")
    source_trust: float = Field(ge=0, le=1, description="Доверие к источнику")
    total: float = Field(ge=0, le=1, description="Итоговая горячность")
    reasoning: Optional[str] = None

class ExtractedEntities(BaseModel):
    """Извлеченные сущности из новости"""
    companies: List[Dict[str, str]] = []
    countries: List[str] = []
    instruments: List[str] = []
    people: List[str] = []
    sectors: List[str] = []

class TimelineEvent(BaseModel):
    """Событие во временной шкале"""
    time: datetime
    event: str

class ArticleDraft(BaseModel):
    """Черновик статьи"""
    headline: str
    lead: str
    bullets: List[str]
    quote: str
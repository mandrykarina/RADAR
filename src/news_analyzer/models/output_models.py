from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
from .data_models import TimelineEvent, ArticleDraft

class RadarOutput(BaseModel):
    """Выходной формат по ТЗ RADAR"""
    headline: str
    hotness: float = Field(ge=0, le=1)
    why_now: str
    entities: List[str]
    sources: List[str]
    timeline: List[TimelineEvent]
    draft: ArticleDraft
    dedup_group: str

class BatchRadarOutput(BaseModel):
    """Результат обработки всего файла новостей"""
    timestamp: datetime
    top_events: List[RadarOutput]
    total_processed: int
    hot_news_count: int
    processing_stats: Dict[str, float]
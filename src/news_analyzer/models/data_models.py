"""Обновленные модели данных для нового формата входных JSON новостей"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class NewsItem(BaseModel):
    """Модель новости в новом формате"""

    # Основные поля
    id: int
    title: str
    content: Optional[str] = None # может быть null
    url: str
    source: str

    # Метаданные автора и языка
    author: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None

    # Категоризация
    category: str
    tags: List[str] = Field(default_factory=list)

    # Финансовые данные
    tickers: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)

    # Аналитические метрики
    sentiment: Optional[float] = None # -1 до 1
    relevance: Optional[float] = None # 0 до 1
    source_credibility: int = Field(ge=1, le=10) # 1-10 шкала

    # Дедупликация
    is_duplicate: int = Field(default=-1) # -1 если уникальная, иначе ID группы дубликатов

    # Временные метки
    collected_at: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    @property
    def duplicate_group(self) -> str:
        """Совместимость со старым полем duplicate_group"""
        if self.is_duplicate == -1:
            return f"unique_{self.id}"
        return f"group_{self.is_duplicate}"

    @property
    def credibility_score(self) -> float:
        """Совместимость - преобразование 1-10 в 0-1"""
        return self.source_credibility / 10.0

    @property
    def confirmation_count(self) -> int:
        """Примерная оценка количества подтверждений"""
        if self.is_duplicate == -1:
            return 1
        # Для дубликатов считаем больше подтверждений
        return min(self.source_credibility, 8)

class NewsData(BaseModel):
    """Контейнер для массива новостей"""
    news: List[NewsItem]
    # Добавляем совместимость с timestamp если есть
    timestamp: Optional[datetime] = None

    @classmethod
    def from_list(cls, news_list: List[Dict[str, Any]]) -> "NewsData":
        """Создание из списка словарей"""
        news_items = [NewsItem(**item) for item in news_list]
        return cls(news=news_items, timestamp=datetime.now())

class ExtractedEntities(BaseModel):
    """Извлеченные финансовые сущности"""
    companies: List[Union[Dict[str, str], str]] = Field(default_factory=list)  # ИСПРАВЛЕНИЕ: Может быть словарь или строка
    countries: List[str] = Field(default_factory=list)
    instruments: List[str] = Field(default_factory=list)
    people: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)

class ArticleDraft(BaseModel):
    """Черновик статьи для RADAR системы"""
    headline: str = Field(default="Статья без заголовка")  # Добавляем значение по умолчанию
    lead: str = Field(default="Краткое описание недоступно")
    bullets: List[str] = Field(default_factory=list)
    quote: str = Field(default="")

class TimelineEvent(BaseModel):
    """События для временной шкалы"""
    time: datetime
    event: str

class HotnessScore(BaseModel):
    """Компоненты оценки горячести новости"""
    unexpectedness: float = 0.0 # Неожиданность [0,1]
    materiality: float = 0.0 # Материальность [0,1]
    velocity: float = 0.0 # Скорость распространения [0,1]
    breadth: float = 0.0 # Широта охвата [0,1]
    source_trust: float = 0.0 # Доверие к источнику [0,1]
    total: float = 0.0 # Итоговая оценка [0,1]

    def calculate_total(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Расчет итоговой оценки с весами"""
        if weights is None:
            weights = {
                'unexpectedness': 0.3,
                'materiality': 0.25,
                'velocity': 0.2,
                'breadth': 0.15,
                'source_trust': 0.1
            }

        self.total = (
            self.unexpectedness * weights['unexpectedness'] +
            self.materiality * weights['materiality'] +
            self.velocity * weights['velocity'] +
            self.breadth * weights['breadth'] +
            self.source_trust * weights['source_trust']
        )

        return self.total

class RadarOutput(BaseModel):
    """Выходные данные RADAR анализа для одного события"""
    headline: str = Field(default="Событие без заголовка")  # Заголовок события
    hotness: float = Field(default=0.0)  # Оценка горячности [0,1]
    why_now: str = Field(default="Важность не определена")  # Почему важно сейчас
    entities: List[str] = Field(default_factory=list)  # Список сущностей
    sources: List[str] = Field(default_factory=list)  # Список источников
    timeline: List[TimelineEvent] = Field(default_factory=list)  # Временная шкала
    draft: ArticleDraft = Field(default_factory=ArticleDraft)  # Черновик статьи
    dedup_group: str = Field(default="unknown")  # ID группы дедупликации

class BatchRadarOutput(BaseModel):
    """Результат анализа пакета новостей"""
    timestamp: datetime
    top_events: List[RadarOutput] = Field(default_factory=list)
    total_processed: int = Field(default=0)
    hot_news_count: int = Field(default=0)
    processing_stats: Dict[str, Any] = Field(default_factory=dict)
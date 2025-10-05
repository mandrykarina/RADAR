import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

class CacheManager:
    """Менеджер кеширования для экономии API вызовов"""

    def __init__(self, cache_dir: str = "data/cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = ttl_hours

    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[str]:
        """Получить данные из кеша"""
        cache_file = self._get_cache_path(key)
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ts = datetime.fromisoformat(data['timestamp'])
            if datetime.now() > ts + timedelta(hours=self.ttl_hours):
                cache_file.unlink()
                return None
            return data['value']
        except Exception as e:
            print(f"⚠️ Ошибка чтения кеша: {e}")
            return None

    def set(self, key: str, value: str):
        """Сохранить данные в кеш"""
        cache_file = self._get_cache_path(key)
        data = {
            'timestamp': datetime.now().isoformat(),
            'value': value
        }
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка записи кеша: {e}")
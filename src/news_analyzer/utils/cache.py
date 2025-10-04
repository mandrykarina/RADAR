import json
import hashlib
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

    async def get(self, key: str) -> Optional[str]:
        """Получение из кеша"""

        cache_file = self._get_cache_path(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Проверка TTL
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            expiry_time = cached_time + timedelta(hours=self.ttl_hours)

            if datetime.now() > expiry_time:
                cache_file.unlink()
                return None

            return cache_data['value']

        except (json.JSONDecodeError, KeyError, Exception):
            return None

    async def set(self, key: str, value: str):
        """Сохранение в кеш"""

        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'value': value
        }

        cache_file = self._get_cache_path(key)

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка кеша: {e}")
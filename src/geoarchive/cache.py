import hashlib
import json
import os
from pathlib import Path

import pydantic

from geoarchive.services.base import Layer


class CacheService:
    def __init__(self, data: dict | None):
        self._cached = data if data is not None else {}

    def exists(self, layer: Layer) -> bool:
        return layer.name in self._cached

    def set(self, layer: Layer):
        self._cached[layer.name] = layer.model_dump()

    @classmethod
    def load(cls, url: str, project_path: Path):
        cache_dir = project_path / '.cache/remotes/'
        cache_path = cache_dir / f'{hashlib.md5(url.encode()).hexdigest()}.json'

        if not cache_path.exists():
            return cls(data=None)

        with cache_path.open() as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = None
            return cls(data=data)

    def save(self, url: str, project_path: Path):
        cache_dir = project_path / '.cache/remotes/'
        cache_path = cache_dir / f'{hashlib.md5(url.encode()).hexdigest()}.json'
        os.makedirs(cache_dir, exist_ok=True)

        with open(cache_path, 'w') as f:
            f.write(json.dumps(self._cached))

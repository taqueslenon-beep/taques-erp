"""
Cache simples em memória para dados do módulo de processos.
TTL: 5 minutos (300 segundos)
"""
import time
from typing import Any, Optional, Callable

_cache = {}
_cache_timestamps = {}
CACHE_TTL = 300  # 5 minutos

def get_cached(key: str) -> Optional[Any]:
    """Retorna valor do cache se não expirado."""
    if key in _cache:
        if time.time() - _cache_timestamps.get(key, 0) < CACHE_TTL:
            print(f"[CACHE] Hit: {key}")
            return _cache[key]
        else:
            print(f"[CACHE] Expired: {key}")
            del _cache[key]
            del _cache_timestamps[key]
    return None

def set_cached(key: str, value: Any) -> None:
    """Armazena valor no cache."""
    _cache[key] = value
    _cache_timestamps[key] = time.time()
    print(f"[CACHE] Set: {key}")

def invalidate_cache(key: str = None) -> None:
    """Invalida cache específico ou todo o cache."""
    global _cache, _cache_timestamps
    if key:
        _cache.pop(key, None)
        _cache_timestamps.pop(key, None)
        print(f"[CACHE] Invalidated: {key}")
    else:
        _cache = {}
        _cache_timestamps = {}
        print(f"[CACHE] Invalidated ALL")

def cached_call(key: str, func: Callable) -> Any:
    """Executa função com cache."""
    cached = get_cached(key)
    if cached is not None:
        return cached
    
    result = func()
    set_cached(key, result)
    return result





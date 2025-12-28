import redis
import json
from typing import Optional, Any
from app.core.config import settings


class CacheService:
    """Redis cache service for storing temporary data"""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        expiry: int = 3600
    ) -> bool:
        """Set value in cache with expiry (seconds)"""
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, expiry, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    def cache_document_check(self, content_hash: str, result: dict, hours: int = 24):
        """Cache plagiarism check result"""
        key = f"plagiarism_check:{content_hash}"
        self.set(key, result, expiry=hours * 3600)
    
    def get_cached_check(self, content_hash: str) -> Optional[dict]:
        """Get cached plagiarism check result"""
        key = f"plagiarism_check:{content_hash}"
        return self.get(key)


# Global instance
cache_service = CacheService()
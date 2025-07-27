# src/backend/tests/unit/core/parser/complex_project/services/data/database.py

from typing import Dict, List, Any, Optional
from ...models.user import User
from ...models.base import BaseModel
from .cache import CacheManager


class DatabaseManager:
    """Database management service"""
    
    def __init__(self, connection_string: str = "sqlite:///:memory:"):
        self.connection_string = connection_string
        self.cache = CacheManager()
        self.tables: Dict[str, List[Dict]] = {}
        self._setup_tables()
    
    def _setup_tables(self):
        """Initialize database tables"""
        self.tables["users"] = []
        self.tables["sessions"] = []
        self.tables["logs"] = []
    
    def save(self, model: BaseModel, table: str) -> bool:
        """Save model to database"""
        try:
            data = model.to_dict()
            data["id"] = self._generate_id()
            self.tables[table].append(data)
            
            # Cache the record
            cache_key = f"{table}:{data['id']}"
            self.cache.set(cache_key, data)
            return True
        except Exception as e:
            self._log_error(f"Failed to save to {table}: {e}")
            return False
    
    def find(self, table: str, conditions: Dict[str, Any]) -> List[Dict]:
        """Find records matching conditions"""
        if table not in self.tables:
            return []
        
        results = []
        for record in self.tables[table]:
            match = True
            for key, value in conditions.items():
                if record.get(key) != value:
                    match = False
                    break
            if match:
                results.append(record)
        return results
    
    def find_one(self, table: str, conditions: Dict[str, Any]) -> Optional[Dict]:
        """Find single record matching conditions"""
        results = self.find(table, conditions)
        return results[0] if results else None
    
    def update(self, table: str, record_id: str, updates: Dict[str, Any]) -> bool:
        """Update record by ID"""
        if table not in self.tables:
            return False
        
        for record in self.tables[table]:
            if record.get("id") == record_id:
                record.update(updates)
                # Update cache
                cache_key = f"{table}:{record_id}"
                self.cache.set(cache_key, record)
                return True
        return False
    
    def delete(self, table: str, record_id: str) -> bool:
        """Delete record by ID"""
        if table not in self.tables:
            return False
        
        for i, record in enumerate(self.tables[table]):
            if record.get("id") == record_id:
                del self.tables[table][i]
                # Remove from cache
                cache_key = f"{table}:{record_id}"
                self.cache.delete(cache_key)
                return True
        return False
    
    def count(self, table: str) -> int:
        """Count records in table"""
        return len(self.tables.get(table, []))
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _log_error(self, message: str):
        """Log error message"""
        import logging
        logging.error(message) 
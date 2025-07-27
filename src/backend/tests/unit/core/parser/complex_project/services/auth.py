# src/backend/tests/unit/core/parser/complex_project/services/auth.py

from typing import Optional, Dict, Any
from ..models.user import User, UserType
from ..utils.string_utils import StringProcessor


class AuthService:
    """Authentication service"""
    
    def __init__(self):
        self.active_sessions: Dict[str, User] = {}
        self.string_processor = StringProcessor()
    
    def login(self, username: str, password: str) -> Optional[str]:
        """Login user and return session token"""
        # Mock authentication
        if self._validate_credentials(username, password):
            token = self._generate_token(username)
            user = User(name=username, user_type=UserType.USER)
            self.active_sessions[token] = user
            return token
        return None
    
    def logout(self, token: str) -> bool:
        """Logout user by token"""
        if token in self.active_sessions:
            del self.active_sessions[token]
            return True
        return False
    
    def get_user(self, token: str) -> Optional[User]:
        """Get user by session token"""
        return self.active_sessions.get(token)
    
    def is_authenticated(self, token: str) -> bool:
        """Check if token is valid"""
        return token in self.active_sessions
    
    def _validate_credentials(self, username: str, password: str) -> bool:
        """Validate user credentials (mock)"""
        return len(username) > 0 and len(password) >= 6
    
    def _generate_token(self, username: str) -> str:
        """Generate session token (mock)"""
        import hashlib
        import time
        data = f"{username}:{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()


class PermissionService:
    """Permission management service"""
    
    def __init__(self):
        self.permissions: Dict[str, list] = {}
    
    def grant_permission(self, user_id: str, permission: str):
        """Grant permission to user"""
        if user_id not in self.permissions:
            self.permissions[user_id] = []
        if permission not in self.permissions[user_id]:
            self.permissions[user_id].append(permission)
    
    def revoke_permission(self, user_id: str, permission: str):
        """Revoke permission from user"""
        if user_id in self.permissions:
            if permission in self.permissions[user_id]:
                self.permissions[user_id].remove(permission)
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has permission"""
        return (user_id in self.permissions and 
                permission in self.permissions[user_id]) 
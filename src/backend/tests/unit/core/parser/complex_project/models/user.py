# src/backend/tests/unit/core/parser/complex_project/models/user.py

from enum import Enum
from typing import Optional, List
from .base import BaseModel, ValidationMixin


class UserType(Enum):
    """User type enumeration"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class User(BaseModel, ValidationMixin):
    """User model class"""
    
    def __init__(self, name: str, email: str = "", 
                 user_type: UserType = UserType.USER):
        super().__init__()
        self.name = name
        self.email = email
        self.user_type = user_type
        self.permissions: List[str] = []
    
    def get_name(self) -> str:
        return self.name
    
    def set_email(self, email: str):
        self.email = email
        self.update()
    
    def add_permission(self, permission: str):
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions
    
    def is_admin(self) -> bool:
        return self.user_type == UserType.ADMIN
    
    def validate(self) -> bool:
        """Validate user data"""
        if not self.name or len(self.name.strip()) == 0:
            return False
        if self.email and "@" not in self.email:
            return False
        return True
    
    def to_dict(self):
        """Convert user to dictionary"""
        data = super().to_dict()
        data.update({
            "name": self.name,
            "email": self.email,
            "user_type": self.user_type.value,
            "permissions": self.permissions.copy()
        })
        return data


class UserManager:
    """User management class"""
    
    def __init__(self):
        self.users: List[User] = []
    
    def add_user(self, user: User) -> bool:
        if user.validate():
            self.users.append(user)
            return True
        return False
    
    def find_user(self, name: str) -> Optional[User]:
        for user in self.users:
            if user.name == name:
                return user
        return None
    
    def get_admin_users(self) -> List[User]:
        return [user for user in self.users if user.is_admin()] 
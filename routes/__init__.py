# routes 包
from .auth import auth_bp
from .works import works_bp
from .users import users_bp
from .comments import comments_bp
from .collections import collections_bp
from .calligraphy import calligraphy_bp

__all__ = ['auth_bp', 'works_bp', 'users_bp', 'comments_bp', 'collections_bp', 'calligraphy_bp']

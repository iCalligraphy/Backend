from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255), default='default_avatar.png')
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    works = db.relationship('Work', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    collections = db.relationship('Collection', backref='collector', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'bio': self.bio,
            'created_at': self.created_at.isoformat(),
            'works_count': self.works.count(),
            'collections_count': self.collections.count()
        }

    def __repr__(self):
        return f'<User {self.username}>'


class Work(db.Model):
    """作品模型"""
    __tablename__ = 'works'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255), nullable=False)
    style = db.Column(db.String(50))  # 书法风格：楷书、行书、草书等
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    views = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    comments = db.relationship('Comment', backref='work', lazy='dynamic', cascade='all, delete-orphan')
    collections = db.relationship('Collection', backref='work', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='work', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_author=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'style': self.style,
            'views': self.views,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'likes_count': self.likes.count(),
            'comments_count': self.comments.count(),
            'collections_count': self.collections.count()
        }
        if include_author:
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username,
                'avatar': self.author.avatar
            }
        return data

    def __repr__(self):
        return f'<Work {self.title}>'


class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))  # 父评论ID，用于回复
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 自引用关系
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                            lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_replies=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'content': self.content,
            'work_id': self.work_id,
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'avatar': self.author.avatar
            },
            'created_at': self.created_at.isoformat(),
            'parent_id': self.parent_id
        }
        if include_replies:
            data['replies'] = [reply.to_dict() for reply in self.replies]
        return data

    def __repr__(self):
        return f'<Comment {self.id}>'


class Collection(db.Model):
    """收藏模型"""
    __tablename__ = 'collections'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 唯一约束：一个用户不能重复收藏同一作品
    __table_args__ = (db.UniqueConstraint('user_id', 'work_id', name='unique_user_work_collection'),)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'work_id': self.work_id,
            'work': self.work.to_dict() if self.work else None,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Collection user:{self.user_id} work:{self.work_id}>'


class Like(db.Model):
    """点赞模型"""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 唯一约束：一个用户不能重复点赞同一作品
    __table_args__ = (db.UniqueConstraint('user_id', 'work_id', name='unique_user_work_like'),)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'work_id': self.work_id,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Like user:{self.user_id} work:{self.work_id}>'

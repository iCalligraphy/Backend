from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

db = SQLAlchemy()

class User(db.Model):
    """用户信息表"""
    __tablename__ = 'user'

    u_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, default='')  # 默认手机号
    password = db.Column(db.String(100), nullable=False)  # MD5加密存储
    nickname = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    avatar = db.Column(db.String(200), default='default_avatar.png')  # 存储服务器图片URL
    common_font = db.Column(db.String(20), default='')  # 常用字体
    fan_count = db.Column(db.Integer, default=0)  # 粉丝数
    follow_count = db.Column(db.Integer, default=0)  # 关注数
    create_time = db.Column(db.DateTime, default=datetime.utcnow)  # 注册时间

    # 关系
    works = db.relationship('Work', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='commenter', lazy='dynamic', cascade='all, delete-orphan')
    calligraphy_sets = db.relationship('CalligraphySet', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    calligraphy_reads = db.relationship('CalligraphyRead', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码MD5加密"""
        # 使用MD5加密密码
        md5 = hashlib.md5()
        md5.update(password.encode('utf-8'))
        self.password = md5.hexdigest()

    def check_password(self, password):
        """验证密码"""
        md5 = hashlib.md5()
        md5.update(password.encode('utf-8'))
        return self.password == md5.hexdigest()

    def to_dict(self):
        """转换为字典"""
        return {
            'u_id': self.u_id,
            'username': self.username,
            'nickname': self.nickname,
            'phone': self.phone,
            'avatar': self.avatar,
            'common_font': self.common_font,
            'fan_count': self.fan_count,
            'follow_count': self.follow_count,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }

    def __repr__(self):
        return f'<User {self.nickname} (u_id={self.u_id})>'


class Work(db.Model):
    """作品表"""
    __tablename__ = 'work'

    w_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), nullable=False)
    title = db.Column(db.String(50), nullable=False)  # 作品名称
    content = db.Column(db.String(500), default='')  # 创作思路
    image_url = db.Column(db.String(200), nullable=False)  # 作品图片URL
    font_type = db.Column(db.String(20), default='')  # 字体类型
    topic_id = db.Column(db.Integer, nullable=True)  # 关联话题ID
    like_count = db.Column(db.Integer, default=0)  # 点赞数
    comment_count = db.Column(db.Integer, default=0)  # 评论数
    create_time = db.Column(db.DateTime, default=datetime.utcnow)  # 发布时间

    # 关系
    comments = db.relationship('Comment', backref='work', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_author=True):
        """转换为字典"""
        data = {
            'w_id': self.w_id,
            'u_id': self.u_id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'font_type': self.font_type,
            'topic_id': self.topic_id,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }
        if include_author and self.author:
            data['author'] = {
                'u_id': self.author.u_id,
                'username': self.author.username,
                'nickname': self.author.nickname,
                'avatar': self.author.avatar
            }
        return data

    def __repr__(self):
        return f'<Work {self.title} (w_id={self.w_id})>'


class Comment(db.Model):
    """评论表"""
    __tablename__ = 'comment'

    c_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), nullable=False)
    w_id = db.Column(db.Integer, db.ForeignKey('work.w_id'), nullable=False)
    comment_type = db.Column(db.String(10), nullable=False)  # 评论类型：笔法、结构、章法、综合
    content = db.Column(db.String(500), nullable=False)  # 评论内容
    create_time = db.Column(db.DateTime, default=datetime.utcnow)  # 评论时间

    def to_dict(self, include_commenter=True):
        """转换为字典"""
        data = {
            'c_id': self.c_id,
            'u_id': self.u_id,
            'w_id': self.w_id,
            'comment_type': self.comment_type,
            'content': self.content,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }
        if include_commenter and self.commenter:
            data['commenter'] = {
                'u_id': self.commenter.u_id,
                'username': self.commenter.username,
                'nickname': self.commenter.nickname,
                'avatar': self.commenter.avatar
            }
        return data

    def __repr__(self):
        return f'<Comment c_id={self.c_id} type={self.comment_type}>'


class CalligraphySet(db.Model):
    """集字记录表"""
    __tablename__ = 'calligraphy_set'

    cs_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), nullable=False)
    target_text = db.Column(db.String(50), nullable=False)  # 目标文字
    font_type = db.Column(db.String(20), nullable=False)  # 字体类型
    copybook_author = db.Column(db.String(20), nullable=False)  # 字帖作者
    layout_type = db.Column(db.String(10), nullable=False)  # 排版方式：横排或竖排
    image_url = db.Column(db.String(200), nullable=False)  # 集字效果图URL
    create_time = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间

    def to_dict(self, include_user=True):
        """转换为字典"""
        data = {
            'cs_id': self.cs_id,
            'u_id': self.u_id,
            'target_text': self.target_text,
            'font_type': self.font_type,
            'copybook_author': self.copybook_author,
            'layout_type': self.layout_type,
            'image_url': self.image_url,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }
        if include_user and self.user:
            data['user'] = {
                'u_id': self.user.u_id,
                'username': self.user.username,
                'nickname': self.user.nickname
            }
        return data

    def __repr__(self):
        return f'<CalligraphySet cs_id={self.cs_id} text="{self.target_text}">'


class CalligraphyRead(db.Model):
    """读帖记录表"""
    __tablename__ = 'calligraphy_read'

    cr_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), nullable=False)
    char_id = db.Column(db.Integer, nullable=True)  # 单字ID，可空
    copybook_id = db.Column(db.Integer, nullable=True)  # 字帖ID，可空
    upload_image_url = db.Column(db.String(200), nullable=True)  # 上传单字URL，可空
    analysis_data = db.Column(db.Text, nullable=False)  # 分析数据，JSON格式
    create_time = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间

    def to_dict(self, include_user=True):
        """转换为字典"""
        data = {
            'cr_id': self.cr_id,
            'u_id': self.u_id,
            'char_id': self.char_id,
            'copybook_id': self.copybook_id,
            'upload_image_url': self.upload_image_url,
            'analysis_data': self.analysis_data,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }
        if include_user and self.user:
            data['user'] = {
                'u_id': self.user.u_id,
                'username': self.user.username,
                'nickname': self.user.nickname
            }
        return data

    def __repr__(self):
        return f'<CalligraphyRead cr_id={self.cr_id}>'


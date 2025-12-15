from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

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
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    collections = db.relationship('Collection', backref='collector', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    post_likes = db.relationship('PostLike', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    post_comments = db.relationship('PostComment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    checkins = db.relationship('Checkin', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码哈希，使用更通用的pbkdf2:sha256算法"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

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
            'bio': self.bio,
            'created_at': self.created_at.isoformat(),
            'works_count': self.works.count(),
            'collections_count': self.collections.count(),
            'posts_count': self.posts.count(),
            'followers_count': self.followers.count(),
            'following_count': self.following.count()
        }

    def __repr__(self):
        return f'<User {self.nickname} (u_id={self.u_id})>'


class Work(db.Model):
    """作品表"""
    __tablename__ = 'work'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255), nullable=False)
    style = db.Column(db.String(50))  # 书法风格：楷书、行书、草书等
    author_name = db.Column(db.String(100))  # 作品作者（朝代+作者）
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source_type = db.Column(db.String(50))  # 来源类型
    tags = db.Column(db.JSON, default=list)  # 作品标签
    views = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='approved')  # 默认approved，跳过审核
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    comments = db.relationship('Comment', backref='work', lazy='dynamic', cascade='all, delete-orphan')
    collections = db.relationship('Collection', backref='work', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='work', lazy='dynamic', cascade='all, delete-orphan')
    characters = db.relationship('Character', backref='work', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_author=True):
        """转换为字典"""
        data = {
            'w_id': self.w_id,
            'u_id': self.u_id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'style': self.style,
            'author_name': self.author_name,
            'source_type': self.source_type,
            'tags': self.tags,
            'views': self.views,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'likes_count': self.likes.count(),
            'comments_count': self.comments.count(),
            'collections_count': self.collections.count()
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
    """评论模型（针对作品）"""
    __tablename__ = 'comments'

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


class Like(db.Model):
    """点赞模型（针对作品）"""
    __tablename__ = 'likes'

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
        return f'<Like user:{self.user_id} work:{self.work_id}>'


class Post(db.Model):
    """社区帖子模型"""
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))  # 标题可选
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.String(50), db.ForeignKey('topics.id'), nullable=True)  # 话题ID可选
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    likes = db.relationship('PostLike', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('PostComment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    topic = db.relationship('Topic', backref=db.backref('posts', lazy='dynamic'))

    def to_dict(self, include_author=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'topic_id': self.topic_id,
            'topic': self.topic.to_dict() if self.topic else None,
            'created_at': (self.created_at + timedelta(hours=8)).isoformat(),
            'updated_at': (self.updated_at + timedelta(hours=8)).isoformat(),
            'likes_count': self.likes.count(),
            'comments_count': self.comments.count()
        }
        if include_author:
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username,
                'avatar': self.author.avatar
            }
        return data

    def __repr__(self):
        return f'<Post {self.id}>'


class PostLike(db.Model):
    """帖子点赞模型"""
    __tablename__ = 'post_likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 唯一约束：一个用户不能重复点赞同一帖子
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<PostLike user:{self.user_id} post:{self.post_id}>'


class PostComment(db.Model):
    """帖子评论模型"""
    __tablename__ = 'post_comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('post_comments.id'))  # 父评论ID，用于回复
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 自引用关系
    replies = db.relationship('PostComment', backref=db.backref('parent', remote_side=[id]),
                            lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_replies=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'content': self.content,
            'post_id': self.post_id,
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
        return f'<PostComment {self.id}>'


class Checkin(db.Model):
    """每日打卡模型"""
    __tablename__ = 'checkins'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    checkin_date = db.Column(db.Date, default=datetime.utcnow().date(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 唯一约束：一个用户每天只能打卡一次
    __table_args__ = (db.UniqueConstraint('user_id', 'checkin_date', name='unique_user_daily_checkin'),)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'checkin_date': self.checkin_date.isoformat(),
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Checkin user:{self.user_id} date:{self.checkin_date}>'


class Follow(db.Model):
    """关注关系模型"""
    __tablename__ = 'follows'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 唯一约束：一个用户不能重复关注另一个用户
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow_relationship'),)

    # 关系
    follower = db.relationship('User', foreign_keys=[follower_id], backref=db.backref('following', lazy='dynamic', cascade='all, delete-orphan'))
    followed = db.relationship('User', foreign_keys=[followed_id], backref=db.backref('followers', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'follower_id': self.follower_id,
            'followed_id': self.followed_id,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Follow {self.follower_id} -> {self.followed_id}>'


class Topic(db.Model):
    """话题模型"""
    __tablename__ = 'topics'

    id = db.Column(db.String(50), primary_key=True)  # 使用字符串ID，如'technique'
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    post_count = db.Column(db.Integer, default=0)
    today_posts = db.Column(db.Integer, default=0)
    color = db.Column(db.String(20), default='#8b4513')  # 话题颜色
    icon = db.Column(db.String(10), default='🖌️')  # 话题图标
    is_popular = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    followers = db.relationship('FollowTopic', backref='topic', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'post_count': self.post_count,
            'today_posts': self.today_posts,
            'color': self.color,
            'icon': self.icon,
            'is_popular': self.is_popular,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Topic {self.name}>'


class FollowTopic(db.Model):
    """用户关注话题关系模型"""
    __tablename__ = 'follow_topics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.String(50), db.ForeignKey('topics.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 唯一约束：一个用户不能重复关注同一个话题
    __table_args__ = (db.UniqueConstraint('user_id', 'topic_id', name='unique_user_topic_follow'),)

    # 关系
    user = db.relationship('User', backref=db.backref('topic_follows', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'topic_id': self.topic_id,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<FollowTopic user:{self.user_id} topic:{self.topic_id}>'


class Character(db.Model):
    """书法字符模型"""
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False)
    style = db.Column(db.String(50), nullable=False)  # 书体：楷书、行书、草书等
    strokes = db.Column(db.Integer, nullable=False)  # 笔画数量
    stroke_order = db.Column(db.String(100), nullable=False)  # 笔顺
    recognition = db.Column(db.String(50), nullable=False)  # 识别结果
    source = db.Column(db.String(200), nullable=False)  # 出自
    collected_at = db.Column(db.DateTime, default=datetime.utcnow)  # 采集时间
    keypoints = db.Column(db.JSON, nullable=False, default=list)  # 关键点列表
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间

    # 关系
    # 通过work_id外键自动建立与Work模型的关系

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'work_id': self.work_id,
            'style': self.style,
            'strokes': self.strokes,
            'stroke_order': self.stroke_order,
            'recognition': self.recognition,
            'source': self.source,
            'collected_at': self.collected_at.isoformat(),
            'keypoints': self.keypoints,
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Character id:{self.id} work:{self.work_id} style:{self.style}>'
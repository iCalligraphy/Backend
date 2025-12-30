from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
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
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    post_likes = db.relationship('PostLike', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    post_comments = db.relationship('PostComment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    checkins = db.relationship('Checkin', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码哈希，使用更通用的pbkdf2:sha256算法"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

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
            'collections_count': self.collections.count(),
            'posts_count': self.posts.count(),
            'followers_count': self.followers.count(),
            'following_count': self.following.count()
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
    dynasty = db.Column(db.String(50))  # 朝代信息
    author_name = db.Column(db.String(100))  # 作品作者
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source_type = db.Column(db.String(50))  # 来源类型
    tags = db.Column(db.JSON, default=list)  # 作品标签
    views = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='approved')  # 默认approved，跳过审核
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    original_width = db.Column(db.Integer, default=0)  # 原始图片宽度
    original_height = db.Column(db.Integer, default=0)  # 原始图片高度

    # 关系
    comments = db.relationship('Comment', backref='work', lazy='dynamic', cascade='all, delete-orphan')
    collections = db.relationship('Collection', backref='work', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='work', lazy='dynamic', cascade='all, delete-orphan')
    characters = db.relationship('Character', backref='work', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_author=True):
        """转换为字典"""
        # 生成完整的图片URL
        from utils import get_file_url
        image_url = get_file_url(self.image_url, 'works')
        
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': image_url,
            'style': self.style,
            'dynasty': self.dynasty,
            'author_name': self.author_name,
            'source_type': self.source_type,
            'tags': self.tags,
            'views': self.views,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'likes_count': self.likes.count(),
            'comments_count': self.comments.count(),
            'collections_count': self.collections.count(),
            'characters_count': self.characters.count()
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
    """评论模型（针对作品）"""
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
    """点赞模型（针对作品）"""
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


class Post(db.Model):
    """社区帖子模型"""
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))  # 标题可选
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.String(50), db.ForeignKey('topics.id'), nullable=False)  # 话题ID必填
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
    description = db.Column(db.Text, nullable=False)
    post_count = db.Column(db.Integer, default=0)
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
    x = db.Column(db.Integer, nullable=False, default=0)  # 单字在作品中的X坐标
    y = db.Column(db.Integer, nullable=False, default=0)  # 单字在作品中的Y坐标
    width = db.Column(db.Integer, nullable=False, default=100)  # 单字宽度
    height = db.Column(db.Integer, nullable=False, default=100)  # 单字高度

    # 关系
    # 通过work_id外键自动建立与Work模型的关系

    def to_dict(self, include_work=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'work_id': self.work_id,
            'style': self.style,
            'strokes': self.strokes,
            'stroke_order': self.stroke_order,
            'recognition': self.recognition,
            'source': self.source,
            'collected_at': self.collected_at.isoformat(),
            'keypoints': self.keypoints,
            'updated_at': self.updated_at.isoformat(),
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }
        
        if include_work:
            # 生成完整的作品图片URL
            from utils import get_file_url
            work_image_url = get_file_url(self.work.image_url, 'works')
            data['work_image_url'] = work_image_url
            # 添加作品图片的尺寸信息，用于前端裁剪显示
            data['work_image_width'] = self.work.original_width if hasattr(self.work, 'original_width') else 0
            data['work_image_height'] = self.work.original_height if hasattr(self.work, 'original_height') else 0
        
        return data

    def __repr__(self):
        return f'<Character id:{self.id} work:{self.work_id} style:{self.style}>'


class CharacterSet(db.Model):
    """字集模型"""
    __tablename__ = 'character_sets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 字集名称
    description = db.Column(db.Text)  # 字集描述
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 创建者
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    characters = db.relationship('CharacterInSet', backref='character_set', lazy='dynamic', cascade='all, delete-orphan')
    user = db.relationship('User', backref=db.backref('character_sets', lazy='dynamic'))
    
    # 唯一约束：一个用户的字集名称不能重复
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='unique_user_character_set_name'),)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'characters_count': self.characters.count()
        }
    
    def __repr__(self):
        return f'<CharacterSet {self.name} user:{self.user_id}>'


class CharacterInSet(db.Model):
    """字集-单字关联模型"""
    __tablename__ = 'characters_in_sets'
    
    id = db.Column(db.Integer, primary_key=True)
    character_set_id = db.Column(db.Integer, db.ForeignKey('character_sets.id'), nullable=False)  # 所属字集
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'), nullable=False)  # 关联单字
    added_at = db.Column(db.DateTime, default=datetime.utcnow)  # 添加时间
    
    # 关系
    character = db.relationship('Character', backref=db.backref('in_sets', lazy='dynamic'))
    
    # 唯一约束：一个字集内不能重复添加同一个单字
    __table_args__ = (db.UniqueConstraint('character_set_id', 'character_id', name='unique_set_character'),)
    
    def to_dict(self, include_character=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'character_set_id': self.character_set_id,
            'character_id': self.character_id,
            'added_at': self.added_at.isoformat()
        }
        if include_character:
            data['character'] = self.character.to_dict()
        return data
    
    def __repr__(self):
        return f'<CharacterInSet set:{self.character_set_id} char:{self.character_id}>'


class SearchLog(db.Model):
    """搜索记录模型 - 用于统计热门搜索词"""
    __tablename__ = 'search_logs'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 可选，记录搜索用户
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = db.relationship('User', backref=db.backref('search_logs', lazy='dynamic'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'keyword': self.keyword,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<SearchLog keyword:{self.keyword}>'


class Notification(db.Model):
    """通知模型"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # 接收通知的用户
    type = db.Column(db.String(20), nullable=False, index=True)  # 通知类型：like, comment, follow, mention, system
    content = db.Column(db.Text, nullable=False)  # 通知内容
    related_id = db.Column(db.Integer, nullable=False)  # 关联对象ID（如帖子ID、评论ID等）
    related_type = db.Column(db.String(20), nullable=False)  # 关联对象类型：post, comment, user等
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)  # 是否已读
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)  # 创建时间
    
    # 关系
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))
    
    def to_dict(self):
        """转换为字典"""
        from datetime import timedelta
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'content': self.content,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'is_read': self.is_read,
            'created_at': (self.created_at + timedelta(hours=8)).isoformat()
        }
    
    def __repr__(self):
        return f'<Notification user:{self.user_id} type:{self.type} id:{self.id}>'
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from models import db, Post, PostLike, PostComment, Checkin, User, Topic
from utils import create_notification
from datetime import datetime, date
import json
import traceback
import traceback

posts_bp = Blueprint('posts', __name__)

# 为posts蓝图添加JWT调试中间件
@posts_bp.before_request
def posts_jwt_debug_middleware():
    """为所有posts蓝图请求添加JWT调试日志"""
    # 仅在开发环境启用详细调试
    if current_app.config.get('DEBUG'):
        auth_header = request.headers.get('Authorization')
        print(f"[JWT DEBUG] 请求路径: {request.path}")
        print(f"[JWT DEBUG] Authorization头存在: {bool(auth_header)}")
        if auth_header:
            # 只打印前20个字符，避免敏感信息
            header_start = auth_header[:20] + '...' if len(auth_header) > 20 else auth_header
            print(f"[JWT DEBUG] Authorization头前20字符: {header_start}")
            # 检查Bearer格式
            is_bearer = auth_header.lower().startswith('bearer ')
            print(f"[JWT DEBUG] Authorization头是否为Bearer格式: {is_bearer}")
            if is_bearer:
                # 提取token部分
                token_part = auth_header[7:].strip()
                print(f"[JWT DEBUG] 提取的token长度: {len(token_part)}")
                print(f"[JWT DEBUG] 提取的token前20字符: {token_part[:20] + '...' if len(token_part) > 20 else token_part}")
                # 检查token段数（JWT标准应该有3段）
                segments = token_part.split('.')
                print(f"[JWT DEBUG] Token段数: {len(segments)}")
                for i, segment in enumerate(segments):
                    print(f"[JWT DEBUG] 第{i+1}段长度: {len(segment)}, 前5字符: {segment[:5] if segment else '空'}")

# 错误处理装饰器
def handle_errors(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except IntegrityError as e:
            db.session.rollback()
            return jsonify({'error': '数据库操作错误', 'details': str(e)}), 409
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    wrapper.__name__ = f.__name__
    return wrapper

@posts_bp.route('/api/posts', methods=['POST'])
@jwt_required()  # 必须登录才能发布帖子
@handle_errors
def create_post():
    """创建新帖子"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    # 验证必填字段
    if 'content' not in data or not data['content'].strip():
        return jsonify({'error': '内容不能为空'}), 400
    
    # 获取话题ID（支持topic和topic_id两种字段名）
    topic_id = data.get('topic') or data.get('topic_id')
    if not topic_id:
        return jsonify({'error': '必须选择话题'}), 400
    
    # 验证话题是否存在
    topic = Topic.query.get(topic_id)
    if not topic:
        return jsonify({'error': '话题不存在'}), 400
    
    # 获取当前用户ID
    from flask_jwt_extended import get_jwt_identity
    current_user_id = get_jwt_identity()
    
    # 确保用户ID是整数类型
    try:
        current_user_id = int(current_user_id)
    except ValueError:
        return jsonify({'error': '无效的用户身份'}), 401
    
    # 创建帖子
    post = Post(
        title=data.get('title', '').strip(),  # 标题可选
        content=data['content'].strip(),
        author_id=current_user_id,
        topic_id=topic_id  # 添加话题ID
    )
    db.session.add(post)
    
    # 更新话题帖子计数
    topic = Topic.query.get(topic_id)
    topic.post_count += 1
    
    db.session.commit()

    return jsonify({
        'message': '帖子发布成功',
        'post': post.to_dict()
    }), 201

@posts_bp.route('/api/posts', methods=['GET'])
@handle_errors
def get_posts():
    # 为测试环境临时移除JWT验证，允许未授权访问
    # 在生产环境中应恢复@jwt_required()装饰器
    """获取帖子列表，支持分页和排序"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort_by = request.args.get('sort_by', 'created_at')  # 支持 created_at, likes_count, comments_count
    order = request.args.get('order', 'desc')  # asc 或 desc

    # 构建查询，预加载话题关系
    query = Post.query.options(joinedload(Post.topic))

    # 排序逻辑
    if sort_by == 'likes_count':
        # 使用子查询计算点赞数
        from sqlalchemy import func
        if order == 'desc':
            query = query.outerjoin(PostLike).group_by(Post.id).order_by(func.count(PostLike.id).desc())
        else:
            query = query.outerjoin(PostLike).group_by(Post.id).order_by(func.count(PostLike.id).asc())
    elif sort_by == 'comments_count':
        # 使用子查询计算评论数
        from sqlalchemy import func
        if order == 'desc':
            query = query.outerjoin(PostComment).group_by(Post.id).order_by(func.count(PostComment.id).desc())
        else:
            query = query.outerjoin(PostComment).group_by(Post.id).order_by(func.count(PostComment.id).asc())
    else:  # 默认按创建时间排序
        if order == 'desc':
            query = query.order_by(Post.created_at.desc())
        else:
            query = query.order_by(Post.created_at.asc())

    # 分页查询
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items

    # 获取当前用户ID（如果有）
    # 由于临时移除了JWT验证，设置默认值为None
    current_user_id = None
    
    try:
        # 尝试获取JWT身份，但不强制要求
        try:
            from flask_jwt_extended import verify_jwt_in_request_optional, get_jwt_identity
            # 首先调用verify_jwt_in_request_optional()来安全地验证JWT
            verify_jwt_in_request_optional()
            # 然后再尝试获取用户ID
            current_user_id = get_jwt_identity()
        except ImportError:
            # 如果无法导入相关模块，保持默认值
            pass
    except:
        # 如果JWT验证失败或不存在，保持current_user_id为None
        pass

    # 构建响应数据
    posts_data = []
    for post in posts:
        post_dict = post.to_dict()
        # 添加是否点赞信息（仅当用户已登录时）
        if current_user_id:
            post_dict['is_liked'] = PostLike.query.filter_by(
                user_id=current_user_id, post_id=post.id
            ).first() is not None
        else:
            post_dict['is_liked'] = False
        posts_data.append(post_dict)

    return jsonify({
        'posts': posts_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@posts_bp.route('/api/posts/<int:post_id>', methods=['GET'])
@handle_errors
def get_post(post_id):
    """获取单个帖子详情"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    post_dict = post.to_dict()
    
    # 获取当前用户ID（如果已登录）
    current_user_id = None
    try:
        current_user_id = get_jwt_identity()
    except:
        pass

    # 如果用户已登录，添加是否点赞信息
    if current_user_id:
        post_dict['is_liked'] = PostLike.query.filter_by(
            user_id=current_user_id, post_id=post.id
        ).first() is not None

    # 获取帖子评论
    comments = PostComment.query.filter_by(
        post_id=post_id, parent_id=None
    ).order_by(PostComment.created_at.desc()).all()
    post_dict['comments'] = [comment.to_dict(include_replies=True) for comment in comments]

    return jsonify(post_dict)

@posts_bp.route('/api/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
@handle_errors
def like_post(post_id):
    """点赞帖子"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    user_id = get_jwt_identity()
    
    # 检查是否已经点赞
    existing_like = PostLike.query.filter_by(
        user_id=user_id, post_id=post_id
    ).first()

    if existing_like:
        # 如果已经点赞，则取消点赞
        db.session.delete(existing_like)
        db.session.commit()
        # 重新获取帖子，确保数据最新
        post = Post.query.get(post_id)
        return jsonify({
            'message': '已取消点赞',
            'is_liked': False,
            'likes_count': post.likes.count()
        })
    else:
        # 创建新点赞
        like = PostLike(user_id=user_id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
        
        # 发送点赞通知（如果点赞者不是作者自己）
        if user_id != post.author_id:
            # 获取点赞者信息
            liker = User.query.get(user_id)
            if liker:
                content = f'{liker.username} 点赞了你的帖子'
                create_notification(post.author_id, 'like', content, post_id, 'post')
        
        return jsonify({
            'message': '点赞成功',
            'is_liked': True,
            'likes_count': post.likes.count()
        })

@posts_bp.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
@handle_errors
def create_comment(post_id):
    """评论帖子"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    data = request.get_json()
    if not data or 'content' not in data or not data['content'].strip():
        return jsonify({'error': '评论内容不能为空'}), 400

    # 创建评论
    user_id = get_jwt_identity()
    comment = PostComment(
        content=data['content'].strip(),
        post_id=post_id,
        author_id=user_id,
        parent_id=data.get('parent_id')  # 可选，用于回复
    )
    db.session.add(comment)
    db.session.commit()
    
    # 发送评论通知（如果评论者不是作者自己）
    if user_id != post.author_id:
        # 获取评论者信息
        commenter = User.query.get(user_id)
        if commenter:
            content = f'{commenter.username} 评论了你的帖子'
            create_notification(post.author_id, 'comment', content, post_id, 'post')
    
    return jsonify({
        'message': '评论成功',
        'comment': comment.to_dict()
    }), 201

@posts_bp.route('/api/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_post(post_id):
    """删除帖子（仅作者可删除）"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    user_id = get_jwt_identity()
    if post.author_id != user_id:
        return jsonify({'error': '无权删除该帖子'}), 403

    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': '帖子已删除'})

@posts_bp.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_comment(comment_id):
    """删除评论（仅作者可删除）"""
    comment = PostComment.query.get(comment_id)
    if not comment:
        return jsonify({'error': '评论不存在'}), 404

    user_id = get_jwt_identity()
    if comment.author_id != user_id:
        return jsonify({'error': '无权删除该评论'}), 403

    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': '评论已删除'})

@posts_bp.route('/api/checkin', methods=['POST'])
@jwt_required()
@handle_errors
def create_checkin():
    """每日打卡"""
    # 获取当前用户ID
    user_id = get_jwt_identity()
    print(f"[DEBUG] 打卡请求获取到用户ID: {user_id}")
    
    today = date.today()

    # 检查今天是否已经打卡
    existing_checkin = Checkin.query.filter_by(
        user_id=user_id, checkin_date=today
    ).first()

    if existing_checkin:
        return jsonify({'error': '今天已经打卡过了'}), 400

    # 创建新打卡记录
    checkin = Checkin(user_id=user_id, checkin_date=today)
    db.session.add(checkin)
    db.session.commit()

    # 计算连续打卡天数
    consecutive_days = 1
    current_date = today
    while True:
        try:
            previous_date = current_date.replace(day=current_date.day - 1)
            prev_checkin = Checkin.query.filter_by(
                user_id=user_id, checkin_date=previous_date
            ).first()
            if prev_checkin:
                consecutive_days += 1
                current_date = previous_date
            else:
                break
        except ValueError:  # 处理日期边界情况
            break

    return jsonify({
        'message': '打卡成功',
        'consecutive_days': consecutive_days,
        'checkin_date': checkin.checkin_date.isoformat()
    })

@posts_bp.route('/api/checkin/status', methods=['GET'])
@jwt_required()
@handle_errors
def get_checkin_status():
    """获取当前用户的打卡状态"""
    # 添加详细调试日志
    print("[DEBUG] 打卡状态检查请求到达")
    
    # 获取当前用户ID
    user_id = get_jwt_identity()
    print(f"[DEBUG] 获取到用户ID: {user_id}")
    
    today = date.today()
    
    # 检查今天是否已打卡
    today_checkin = Checkin.query.filter_by(
        user_id=user_id, checkin_date=today
    ).first()
    checked_today = today_checkin is not None

    # 计算连续打卡天数
    consecutive_days = 0
    if checked_today:
        consecutive_days = 1
        current_date = today
        while True:
            try:
                previous_date = current_date.replace(day=current_date.day - 1)
                prev_checkin = Checkin.query.filter_by(
                    user_id=user_id, checkin_date=previous_date
                ).first()
                if prev_checkin:
                    consecutive_days += 1
                    current_date = previous_date
                else:
                    break
            except ValueError:  # 处理日期边界情况
                break

    # 获取总打卡次数
    total_checkins = Checkin.query.filter_by(user_id=user_id).count()
    
    # 获取本月打卡记录（前端必需的字段）
    month_start = today.replace(day=1)
    month_checkins = Checkin.query.filter_by(
        user_id=user_id
    ).filter(Checkin.checkin_date >= month_start).all()
    month_checkin_dates = [checkin.checkin_date.day for checkin in month_checkins]

    return jsonify({
        'checked_today': checked_today,
        'consecutive_days': consecutive_days,
        'total_checkins': total_checkins,
        'today': today.isoformat(),
        'month_checkins': month_checkin_dates  # 前端必需的字段
    })
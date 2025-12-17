# 话题相关路由
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Topic, User, FollowTopic
from datetime import datetime

# 创建话题蓝图
topics_bp = Blueprint('topics_bp', __name__)

# 初始化话题数据 - 仅在首次运行时调用
def init_topics():
    # 检查是否已有话题数据
    if Topic.query.count() == 0:
        # 创建初始话题
        initial_topics = [
            {
                'id': 'technique',
                'name': '技法交流',
                'description': '分享书写技巧，讨论笔法、结构、章法等',
                'post_count': 1250,
                'today_posts': 23,
                'color': '#8b4513',
                'icon': '🖌️',
                'is_popular': True,
                'created_at': datetime(2022, 3, 15)
            },
            {
                'id': 'appreciation',
                'name': '作品欣赏',
                'description': '欣赏经典与原创书法作品，交流鉴赏心得',
                'post_count': 890,
                'today_posts': 15,
                'color': '#4a7c59',
                'icon': '👁️',
                'is_popular': True,
                'created_at': datetime(2022, 4, 10)
            },
            {
                'id': 'qna',
                'name': '问答求助',
                'description': '提出书法学习中的疑问，互相解答帮助',
                'post_count': 670,
                'today_posts': 18,
                'color': '#2c5aa0',
                'icon': '❓',
                'is_popular': True,
                'created_at': datetime(2022, 5, 20)
            },
            {
                'id': 'materials',
                'name': '文房四宝',
                'description': '讨论笔墨纸砚等书法工具的选择与使用',
                'post_count': 450,
                'today_posts': 8,
                'color': '#a0522d',
                'icon': '📦',
                'is_popular': False,
                'created_at': datetime(2022, 6, 5)
            },
            {
                'id': 'events',
                'name': '活动赛事',
                'description': '书法比赛、展览、线下活动等信息分享',
                'post_count': 320,
                'today_posts': 5,
                'color': '#c84b31',
                'icon': '🎯',
                'is_popular': False,
                'created_at': datetime(2022, 7, 12)
            }
        ]

        # 添加到数据库
        for topic_data in initial_topics:
            topic = Topic(**topic_data)
            db.session.add(topic)
        db.session.commit()
        print('初始话题数据已创建')


@topics_bp.route('/api/topics', methods=['GET'])
def get_topics():
    """获取所有话题列表"""
    try:
        topics = Topic.query.all()
        topics_data = [{
            'id': topic.id,
            'name': topic.name,
            'description': topic.description,
            'postCount': topic.post_count,
            'color': topic.color,
            'icon': topic.icon,
            'isPopular': topic.is_popular,
            'createdAt': topic.created_at.strftime('%Y-%m-%d')
        } for topic in topics]
        return jsonify({'topics': topics_data}), 200
    except Exception as e:
        return jsonify({'error': f'获取话题列表失败: {str(e)}'}), 500


@topics_bp.route('/api/topics/<topic_id>', methods=['GET'])
def get_topic(topic_id):
    """获取单个话题详情"""
    try:
        topic = Topic.query.filter_by(id=topic_id).first()
        if not topic:
            return jsonify({'error': '话题不存在'}), 404
        
        topic_data = {
            'id': topic.id,
            'name': topic.name,
            'description': topic.description,
            'postCount': topic.post_count,
            'color': topic.color,
            'icon': topic.icon,
            'isPopular': topic.is_popular,
            'createdAt': topic.created_at.strftime('%Y-%m-%d')
        }
        return jsonify(topic_data), 200
    except Exception as e:
        return jsonify({'error': f'获取话题详情失败: {str(e)}'}), 500


@topics_bp.route('/api/topics/<topic_id>/follow', methods=['POST'])
@jwt_required()
def follow_topic(topic_id):
    """关注话题"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        topic = Topic.query.filter_by(id=topic_id).first()
        if not topic:
            return jsonify({'error': '话题不存在'}), 404
        
        # 检查是否已关注
        existing_follow = FollowTopic.query.filter_by(
            user_id=current_user_id, 
            topic_id=topic_id
        ).first()
        
        if existing_follow:
            return jsonify({'message': '已关注该话题'}), 200
        
        # 创建关注记录
        follow_topic = FollowTopic(
            user_id=current_user_id,
            topic_id=topic_id
        )
        db.session.add(follow_topic)
        db.session.commit()
        
        return jsonify({'message': '关注话题成功'}), 201
    except Exception as e:
        return jsonify({'error': f'关注话题失败: {str(e)}'}), 500


@topics_bp.route('/api/topics/<topic_id>/follow', methods=['DELETE'])
@jwt_required()
def unfollow_topic(topic_id):
    """取消关注话题"""
    try:
        current_user_id = get_jwt_identity()
        
        # 查找关注记录
        follow_topic = FollowTopic.query.filter_by(
            user_id=current_user_id, 
            topic_id=topic_id
        ).first()
        
        if not follow_topic:
            return jsonify({'error': '未关注该话题'}), 404
        
        # 删除关注记录
        db.session.delete(follow_topic)
        db.session.commit()
        
        return jsonify({'message': '取消关注话题成功'}), 200
    except Exception as e:
        return jsonify({'error': f'取消关注话题失败: {str(e)}'}), 500


@topics_bp.route('/api/users/<user_id>/following/topics', methods=['GET'])
def get_following_topics(user_id):
    """获取指定用户已关注的话题"""
    try:
        # 查找用户已关注的话题
        follow_records = FollowTopic.query.filter_by(user_id=user_id).all()
        
        # 获取话题ID列表
        topic_ids = [record.topic_id for record in follow_records]
        
        # 获取话题详情
        followed_topics = Topic.query.filter(Topic.id.in_(topic_ids)).all()
        
        # 转换为JSON格式
        topics_data = [{
            'id': topic.id,
            'name': topic.name,
            'description': topic.description,
            'postCount': topic.post_count,
            'color': topic.color,
            'icon': topic.icon,
            'isPopular': topic.is_popular,
            'createdAt': topic.created_at.strftime('%Y-%m-%d')
        } for topic in followed_topics]
        
        return jsonify({'topics': topics_data}), 200
    except Exception as e:
        return jsonify({'error': f'获取已关注话题失败: {str(e)}'}), 500

@topics_bp.route('/api/users/me/following/topics', methods=['GET'])
@jwt_required()
def get_current_user_following_topics():
    """获取当前登录用户已关注的话题"""
    try:
        # 获取当前用户ID
        current_user_id = get_jwt_identity()
        
        # 查找用户已关注的话题
        follow_records = FollowTopic.query.filter_by(user_id=current_user_id).all()
        
        # 获取话题ID列表
        topic_ids = [record.topic_id for record in follow_records]
        
        # 获取话题详情
        followed_topics = Topic.query.filter(Topic.id.in_(topic_ids)).all()
        
        # 转换为JSON格式
        topics_data = [{
            'id': topic.id,
            'name': topic.name,
            'description': topic.description,
            'postCount': topic.post_count,
            'color': topic.color,
            'icon': topic.icon,
            'isPopular': topic.is_popular,
            'createdAt': topic.created_at.strftime('%Y-%m-%d')
        } for topic in followed_topics]
        
        return jsonify({'topics': topics_data}), 200
    except Exception as e:
        return jsonify({'error': f'获取已关注话题失败: {str(e)}'}), 500

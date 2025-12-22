from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Notification
from datetime import datetime, timedelta

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """获取通知列表"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': '未授权'}), 401
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    notification_type = request.args.get('type', 'all')
    
    # 构建查询
    query = Notification.query.filter_by(user_id=user_id)
    
    # 按类型筛选
    if notification_type != 'all':
        query = query.filter_by(type=notification_type)
    
    # 按创建时间降序排序
    query = query.order_by(Notification.created_at.desc())
    
    # 分页查询
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    notifications = pagination.items
    
    return jsonify({
        'notifications': [notification.to_dict() for notification in notifications],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'has_next': pagination.has_next
    })


@notifications_bp.route('/count', methods=['GET'])
@jwt_required()
def get_notifications_count():
    """获取未读通知数量"""
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': '未授权'}), 401
        
        # 获取未读通知数量
        unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        
        return jsonify({
            'unread_count': unread_count
        })
    except Exception as e:
        print(f"[ERROR] 获取通知数量失败: {str(e)}")
        # 返回默认值，避免前端500错误
        return jsonify({
            'unread_count': 0
        }), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    """标记单条通知为已读"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': '未授权'}), 401
    
    # 查询通知
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        return jsonify({'error': '通知不存在'}), 404
    
    # 标记为已读
    notification.is_read = True
    db.session.commit()
    
    return jsonify({
        'message': '通知已标记为已读',
        'notification': notification.to_dict()
    })


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_notifications_read():
    """标记所有通知为已读"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': '未授权'}), 401
    
    # 更新所有未读通知
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({
        'message': '所有通知已标记为已读'
    })


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """删除单条通知"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': '未授权'}), 401
    
    # 查询通知
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        return jsonify({'error': '通知不存在'}), 404
    
    # 删除通知
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({
        'message': '通知已删除'
    })


@notifications_bp.route('', methods=['DELETE'])
@jwt_required()
def clear_all_notifications():
    """清空所有通知"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': '未授权'}), 401
    
    # 删除所有通知
    Notification.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return jsonify({
        'message': '所有通知已清空'
    })


@notifications_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_notifications_stats():
    """获取通知统计信息"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': '未授权'}), 401
    
    # 计算统计数据
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 未读通知数量
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    # 今日通知数量
    today_count = Notification.query.filter_by(user_id=user_id)
    today_count = today_count.filter(Notification.created_at >= today_start).count()
    
    # 本周通知数量
    week_count = Notification.query.filter_by(user_id=user_id)
    week_count = week_count.filter(Notification.created_at >= week_start).count()
    
    return jsonify({
        'unread_count': unread_count,
        'today_count': today_count,
        'week_count': week_count
    })

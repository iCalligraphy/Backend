from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Work, Follow
from utils import allowed_file, save_upload_file, create_notification
import os

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取用户信息"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    return jsonify({'user': user.to_dict()}), 200


@users_bp.route('/<int:user_id>/works', methods=['GET'])
def get_user_works(user_id):
    """获取用户的作品列表"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    pagination = Work.query.filter_by(author_id=user_id, status='approved').order_by(
        Work.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    works = [work.to_dict(include_author=False) for work in pagination.items]

    return jsonify({
        'works': works,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户资料"""
    current_user_id = get_jwt_identity()
    print(f"[UPDATE_PROFILE] 开始更新用户资料，用户ID: {current_user_id}")
    
    user = User.query.get(current_user_id)

    if not user:
        print(f"[UPDATE_PROFILE] 用户不存在，用户ID: {current_user_id}")
        return jsonify({'error': '用户不存在'}), 404

    data = request.get_json()
    print(f"[UPDATE_PROFILE] 收到的更新数据: {data}")

    if 'email' in data:
        # 检查邮箱是否已被其他用户使用
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != current_user_id:
            print(f"[UPDATE_PROFILE] 邮箱已被使用，邮箱: {data['email']}")
            return jsonify({'error': '邮箱已被使用'}), 409
        user.email = data['email']
        print(f"[UPDATE_PROFILE] 更新邮箱: {data['email']}")

    if 'bio' in data:
        user.bio = data['bio']
        print(f"[UPDATE_PROFILE] 更新简介: {data['bio']}")

    try:
        db.session.commit()
        print(f"[UPDATE_PROFILE] 资料更新成功，用户ID: {current_user_id}")
        return jsonify({
            'message': '资料更新成功',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"[UPDATE_PROFILE] 更新失败，用户ID: {current_user_id}，错误: {str(e)}")
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@users_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """上传头像"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    if 'avatar' not in request.files:
        return jsonify({'error': '缺少图片文件'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式'}), 400

    # 保存文件
    filename = save_upload_file(file, 'avatars')
    if not filename:
        return jsonify({'error': '文件上传失败'}), 500

    # 删除旧头像（如果不是默认头像）
    if user.avatar and user.avatar != 'default_avatar.png':
        from flask import current_app
        old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', user.avatar)
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    user.avatar = filename

    try:
        db.session.commit()
        return jsonify({
            'message': '头像上传成功',
            'avatar': filename
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


@users_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    """修改密码"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    data = request.get_json()

    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': '缺少必要字段'}), 400

    # 验证旧密码
    if not user.check_password(data['old_password']):
        return jsonify({'error': '旧密码错误'}), 401

    # 设置新密码
    user.set_password(data['new_password'])

    try:
        db.session.commit()
        return jsonify({'message': '密码修改成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'修改失败: {str(e)}'}), 500


@users_bp.route('/<int:user_id>/following', methods=['GET'])
@jwt_required(optional=True)
def get_user_following(user_id):
    """获取用户关注列表"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 获取当前用户的ID（如果已登录）
    current_user_id = get_jwt_identity()

    # 查询用户关注的人
    pagination = Follow.query.filter_by(follower_id=user_id).order_by(
        Follow.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    following_list = []
    for follow in pagination.items:
        followed_user = follow.followed
        is_following = False
        if current_user_id:
            # 如果当前用户正在查看自己的关注列表，那么所有用户都应该是已关注状态
            if int(current_user_id) == user_id:
                is_following = True
            else:
                is_following = Follow.query.filter_by(follower_id=int(current_user_id), followed_id=followed_user.id).first() is not None
        
        following_list.append({
            'id': followed_user.id,
            'username': followed_user.username,
            'avatar': followed_user.avatar,
            'bio': followed_user.bio,
            'followers_count': followed_user.followers.count(),
            'following_count': followed_user.following.count(),
            'is_following': is_following,
            'followed_at': follow.created_at.isoformat()
        })

    return jsonify({
        'following': following_list,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@users_bp.route('/<int:user_id>/followers', methods=['GET'])
@jwt_required(optional=True)
def get_user_followers(user_id):
    """获取用户粉丝列表"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 获取当前用户的ID（如果已登录）
    current_user_id = get_jwt_identity()

    # 查询关注该用户的人
    pagination = Follow.query.filter_by(followed_id=user_id).order_by(
        Follow.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    followers_list = []
    for follow in pagination.items:
        follower_user = follow.follower
        is_following = False
        if current_user_id:
            is_following = Follow.query.filter_by(follower_id=int(current_user_id), followed_id=follower_user.id).first() is not None
        
        followers_list.append({
            'id': follower_user.id,
            'username': follower_user.username,
            'avatar': follower_user.avatar,
            'bio': follower_user.bio,
            'followers_count': follower_user.followers.count(),
            'following_count': follower_user.following.count(),
            'is_following': is_following,
            'followed_at': follow.created_at.isoformat()
        })

    return jsonify({
        'followers': followers_list,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@users_bp.route('/<int:user_id>/follow/status', methods=['GET'])
@jwt_required()
def get_follow_status(user_id):
    """获取关注状态"""
    current_user_id = get_jwt_identity()
    
    # 检查当前用户是否关注了目标用户
    follow = Follow.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
    
    return jsonify({
        'is_following': follow is not None
    }), 200


@users_bp.route('/<int:user_id>/follow', methods=['POST'])
@jwt_required()
def follow_user(user_id):
    """关注用户"""
    current_user_id = get_jwt_identity()
    
    # 不能关注自己
    if current_user_id == user_id:
        return jsonify({'error': '不能关注自己'}), 400
    
    # 检查目标用户是否存在
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 检查是否已经关注
    existing_follow = Follow.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
    if existing_follow:
        return jsonify({'error': '已经关注该用户'}), 409
    
    # 创建关注关系
    new_follow = Follow(follower_id=current_user_id, followed_id=user_id)
    
    try:
        db.session.add(new_follow)
        db.session.commit()
        
        # 发送关注通知
        # 获取关注者信息
        follower_user = User.query.get(current_user_id)
        if follower_user:
            content = f'{follower_user.username} 关注了你'
            create_notification(user_id, 'follow', content, current_user_id, 'user')
        
        return jsonify({
            'message': '关注成功',
            'is_following': True
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'关注失败: {str(e)}'}), 500


@users_bp.route('/<int:user_id>/follow', methods=['DELETE'])
@jwt_required()
def unfollow_user(user_id):
    """取消关注用户"""
    current_user_id = get_jwt_identity()
    
    # 检查关注关系是否存在
    follow = Follow.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
    if not follow:
        return jsonify({'error': '未关注该用户'}), 404
    
    try:
        db.session.delete(follow)
        db.session.commit()
        return jsonify({
            'message': '取消关注成功',
            'is_following': False
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'取消关注失败: {str(e)}'}), 500

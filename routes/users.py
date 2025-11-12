from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Work
from utils import allowed_file, save_upload_file
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
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    data = request.get_json()

    if 'email' in data:
        # 检查邮箱是否已被其他用户使用
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != current_user_id:
            return jsonify({'error': '邮箱已被使用'}), 409
        user.email = data['email']

    if 'bio' in data:
        user.bio = data['bio']

    try:
        db.session.commit()
        return jsonify({
            'message': '资料更新成功',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
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

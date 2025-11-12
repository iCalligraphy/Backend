from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Work, Like, Collection
from utils import allowed_file, save_upload_file
import os

works_bp = Blueprint('works', __name__, url_prefix='/api/works')

@works_bp.route('/', methods=['GET'])
def get_works():
    """获取作品列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    style = request.args.get('style')
    status = request.args.get('status', 'approved')
    search = request.args.get('search')

    query = Work.query

    # 过滤状态
    if status:
        query = query.filter_by(status=status)

    # 过滤风格
    if style:
        query = query.filter_by(style=style)

    # 搜索
    if search:
        query = query.filter(Work.title.contains(search) | Work.description.contains(search))

    # 分页
    pagination = query.order_by(Work.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    works = [work.to_dict() for work in pagination.items]

    return jsonify({
        'works': works,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@works_bp.route('/<int:work_id>', methods=['GET'])
def get_work(work_id):
    """获取单个作品详情"""
    work = Work.query.get(work_id)

    if not work:
        return jsonify({'error': '作品不存在'}), 404

    # 增加浏览次数
    work.views += 1
    db.session.commit()

    return jsonify({'work': work.to_dict()}), 200


@works_bp.route('/', methods=['POST'])
@jwt_required()
def create_work():
    """创建新作品"""
    current_user_id = get_jwt_identity()

    # 检查是否有文件上传
    if 'image' not in request.files:
        return jsonify({'error': '缺少图片文件'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式'}), 400

    # 保存文件
    filename = save_upload_file(file, 'works')
    if not filename:
        return jsonify({'error': '文件上传失败'}), 500

    # 获取其他字段
    title = request.form.get('title')
    description = request.form.get('description', '')
    style = request.form.get('style', '')

    if not title:
        return jsonify({'error': '缺少作品标题'}), 400

    # 创建作品
    work = Work(
        title=title,
        description=description,
        image_url=filename,
        style=style,
        author_id=current_user_id
    )

    try:
        db.session.add(work)
        db.session.commit()
        return jsonify({
            'message': '作品创建成功',
            'work': work.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建失败: {str(e)}'}), 500


@works_bp.route('/<int:work_id>', methods=['PUT'])
@jwt_required()
def update_work(work_id):
    """更新作品"""
    current_user_id = get_jwt_identity()
    work = Work.query.get(work_id)

    if not work:
        return jsonify({'error': '作品不存在'}), 404

    if work.author_id != current_user_id:
        return jsonify({'error': '无权修改此作品'}), 403

    data = request.get_json()

    if 'title' in data:
        work.title = data['title']
    if 'description' in data:
        work.description = data['description']
    if 'style' in data:
        work.style = data['style']

    try:
        db.session.commit()
        return jsonify({
            'message': '作品更新成功',
            'work': work.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@works_bp.route('/<int:work_id>', methods=['DELETE'])
@jwt_required()
def delete_work(work_id):
    """删除作品"""
    current_user_id = get_jwt_identity()
    work = Work.query.get(work_id)

    if not work:
        return jsonify({'error': '作品不存在'}), 404

    if work.author_id != current_user_id:
        return jsonify({'error': '无权删除此作品'}), 403

    try:
        # 删除关联的图片文件
        if work.image_url:
            from flask import current_app
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'works', work.image_url)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(work)
        db.session.commit()
        return jsonify({'message': '作品删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@works_bp.route('/<int:work_id>/like', methods=['POST'])
@jwt_required()
def like_work(work_id):
    """点赞作品"""
    current_user_id = get_jwt_identity()
    work = Work.query.get(work_id)

    if not work:
        return jsonify({'error': '作品不存在'}), 404

    # 检查是否已点赞
    existing_like = Like.query.filter_by(user_id=current_user_id, work_id=work_id).first()
    if existing_like:
        return jsonify({'error': '已经点赞过了'}), 409

    like = Like(user_id=current_user_id, work_id=work_id)

    try:
        db.session.add(like)
        db.session.commit()
        return jsonify({'message': '点赞成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'点赞失败: {str(e)}'}), 500


@works_bp.route('/<int:work_id>/like', methods=['DELETE'])
@jwt_required()
def unlike_work(work_id):
    """取消点赞"""
    current_user_id = get_jwt_identity()
    like = Like.query.filter_by(user_id=current_user_id, work_id=work_id).first()

    if not like:
        return jsonify({'error': '尚未点赞'}), 404

    try:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': '取消点赞成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'取消点赞失败: {str(e)}'}), 500

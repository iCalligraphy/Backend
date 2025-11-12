from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Collection, Work

collections_bp = Blueprint('collections', __name__, url_prefix='/api/collections')

@collections_bp.route('/', methods=['GET'])
@jwt_required()
def get_collections():
    """获取当前用户的收藏列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    pagination = Collection.query.filter_by(user_id=current_user_id).order_by(
        Collection.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    collections = [collection.to_dict() for collection in pagination.items]

    return jsonify({
        'collections': collections,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@collections_bp.route('/', methods=['POST'])
@jwt_required()
def add_collection():
    """添加收藏"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('work_id'):
        return jsonify({'error': '缺少作品ID'}), 400

    # 检查作品是否存在
    work = Work.query.get(data['work_id'])
    if not work:
        return jsonify({'error': '作品不存在'}), 404

    # 检查是否已收藏
    existing_collection = Collection.query.filter_by(
        user_id=current_user_id,
        work_id=data['work_id']
    ).first()

    if existing_collection:
        return jsonify({'error': '已经收藏过了'}), 409

    collection = Collection(
        user_id=current_user_id,
        work_id=data['work_id']
    )

    try:
        db.session.add(collection)
        db.session.commit()
        return jsonify({
            'message': '收藏成功',
            'collection': collection.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'收藏失败: {str(e)}'}), 500


@collections_bp.route('/<int:work_id>', methods=['DELETE'])
@jwt_required()
def remove_collection(work_id):
    """取消收藏"""
    current_user_id = get_jwt_identity()
    collection = Collection.query.filter_by(
        user_id=current_user_id,
        work_id=work_id
    ).first()

    if not collection:
        return jsonify({'error': '未收藏此作品'}), 404

    try:
        db.session.delete(collection)
        db.session.commit()
        return jsonify({'message': '取消收藏成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'取消收藏失败: {str(e)}'}), 500


@collections_bp.route('/check/<int:work_id>', methods=['GET'])
@jwt_required()
def check_collection(work_id):
    """检查是否已收藏某作品"""
    current_user_id = get_jwt_identity()
    collection = Collection.query.filter_by(
        user_id=current_user_id,
        work_id=work_id
    ).first()

    return jsonify({
        'is_collected': collection is not None
    }), 200

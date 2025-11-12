from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Comment, Work

comments_bp = Blueprint('comments', __name__, url_prefix='/api/comments')

@comments_bp.route('/', methods=['POST'])
@jwt_required()
def create_comment():
    """创建评论"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('work_id') or not data.get('content'):
        return jsonify({'error': '缺少必要字段'}), 400

    # 检查作品是否存在
    work = Work.query.get(data['work_id'])
    if not work:
        return jsonify({'error': '作品不存在'}), 404

    # 如果是回复评论，检查父评论是否存在
    parent_id = data.get('parent_id')
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if not parent_comment:
            return jsonify({'error': '父评论不存在'}), 404

    comment = Comment(
        content=data['content'],
        work_id=data['work_id'],
        author_id=current_user_id,
        parent_id=parent_id
    )

    try:
        db.session.add(comment)
        db.session.commit()
        return jsonify({
            'message': '评论成功',
            'comment': comment.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'评论失败: {str(e)}'}), 500


@comments_bp.route('/work/<int:work_id>', methods=['GET'])
def get_work_comments(work_id):
    """获取作品的评论列表"""
    work = Work.query.get(work_id)
    if not work:
        return jsonify({'error': '作品不存在'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 只获取顶级评论（没有父评论的）
    pagination = Comment.query.filter_by(work_id=work_id, parent_id=None).order_by(
        Comment.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    comments = [comment.to_dict(include_replies=True) for comment in pagination.items]

    return jsonify({
        'comments': comments,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@comments_bp.route('/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """更新评论"""
    current_user_id = get_jwt_identity()
    comment = Comment.query.get(comment_id)

    if not comment:
        return jsonify({'error': '评论不存在'}), 404

    if comment.author_id != current_user_id:
        return jsonify({'error': '无权修改此评论'}), 403

    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'error': '缺少评论内容'}), 400

    comment.content = data['content']

    try:
        db.session.commit()
        return jsonify({
            'message': '评论更新成功',
            'comment': comment.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """删除评论"""
    current_user_id = get_jwt_identity()
    comment = Comment.query.get(comment_id)

    if not comment:
        return jsonify({'error': '评论不存在'}), 404

    if comment.author_id != current_user_id:
        return jsonify({'error': '无权删除此评论'}), 403

    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': '评论删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

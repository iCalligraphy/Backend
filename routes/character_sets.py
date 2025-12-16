from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, CharacterSet, CharacterInSet, Character

character_sets_bp = Blueprint('character_sets', __name__, url_prefix='/api/character-sets')


@character_sets_bp.route('/', methods=['GET'])
@jwt_required()
def get_character_sets():
    """获取用户字集列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    pagination = CharacterSet.query.filter_by(user_id=current_user_id).order_by(
        CharacterSet.updated_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    character_sets = [cs.to_dict() for cs in pagination.items]

    return jsonify({
        'character_sets': character_sets,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@character_sets_bp.route('/', methods=['POST'])
@jwt_required()
def create_character_set():
    """创建新字集"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': '缺少字集名称'}), 400

    # 检查字集名称是否已存在
    existing_set = CharacterSet.query.filter_by(
        user_id=current_user_id,
        name=data['name']
    ).first()

    if existing_set:
        return jsonify({'error': '字集名称已存在'}), 409

    character_set = CharacterSet(
        name=data['name'],
        description=data.get('description', ''),
        user_id=current_user_id
    )

    try:
        db.session.add(character_set)
        db.session.commit()
        return jsonify({
            'message': '字集创建成功',
            'character_set': character_set.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'字集创建失败: {str(e)}'}), 500


@character_sets_bp.route('/<int:set_id>', methods=['GET'])
@jwt_required()
def get_character_set(set_id):
    """获取字集详情"""
    current_user_id = get_jwt_identity()
    
    # 检查字集是否存在且属于当前用户
    character_set = CharacterSet.query.filter_by(
        id=set_id,
        user_id=current_user_id
    ).first()

    if not character_set:
        return jsonify({'error': '字集不存在或无权限访问'}), 404

    return jsonify({
        'character_set': character_set.to_dict()
    }), 200


@character_sets_bp.route('/<int:set_id>', methods=['PUT'])
@jwt_required()
def update_character_set(set_id):
    """更新字集信息"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    # 检查字集是否存在且属于当前用户
    character_set = CharacterSet.query.filter_by(
        id=set_id,
        user_id=current_user_id
    ).first()

    if not character_set:
        return jsonify({'error': '字集不存在或无权限访问'}), 404

    # 检查新名称是否已被其他字集使用
    if data.get('name') and data['name'] != character_set.name:
        existing_set = CharacterSet.query.filter_by(
            user_id=current_user_id,
            name=data['name']
        ).first()
        if existing_set:
            return jsonify({'error': '字集名称已存在'}), 409
        character_set.name = data['name']

    # 更新描述
    if 'description' in data:
        character_set.description = data['description']

    try:
        db.session.commit()
        return jsonify({
            'message': '字集更新成功',
            'character_set': character_set.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'字集更新失败: {str(e)}'}), 500


@character_sets_bp.route('/<int:set_id>', methods=['DELETE'])
@jwt_required()
def delete_character_set(set_id):
    """删除字集"""
    current_user_id = get_jwt_identity()

    # 检查字集是否存在且属于当前用户
    character_set = CharacterSet.query.filter_by(
        id=set_id,
        user_id=current_user_id
    ).first()

    if not character_set:
        return jsonify({'error': '字集不存在或无权限访问'}), 404

    try:
        db.session.delete(character_set)
        db.session.commit()
        return jsonify({'message': '字集删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'字集删除失败: {str(e)}'}), 500


@character_sets_bp.route('/<int:set_id>/characters', methods=['GET'])
@jwt_required()
def get_characters_in_set(set_id):
    """获取字集内单字列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 24, type=int)

    # 检查字集是否存在且属于当前用户
    character_set = CharacterSet.query.filter_by(
        id=set_id,
        user_id=current_user_id
    ).first()

    if not character_set:
        return jsonify({'error': '字集不存在或无权限访问'}), 404

    # 获取字集内的单字
    pagination = CharacterInSet.query.filter_by(
        character_set_id=set_id
    ).order_by(
        CharacterInSet.added_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    characters = [char_in_set.to_dict() for char_in_set in pagination.items]

    return jsonify({
        'characters': characters,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@character_sets_bp.route('/<int:set_id>/characters', methods=['POST'])
@jwt_required()
def add_character_to_set(set_id):
    """添加单字到字集"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('character_id'):
        return jsonify({'error': '缺少单字ID'}), 400

    # 检查字集是否存在且属于当前用户
    character_set = CharacterSet.query.filter_by(
        id=set_id,
        user_id=current_user_id
    ).first()

    if not character_set:
        return jsonify({'error': '字集不存在或无权限访问'}), 404

    # 检查单字是否存在
    character = Character.query.get(data['character_id'])
    if not character:
        return jsonify({'error': '单字不存在'}), 404

    # 检查单字是否已在字集中
    existing_char = CharacterInSet.query.filter_by(
        character_set_id=set_id,
        character_id=data['character_id']
    ).first()

    if existing_char:
        return jsonify({'error': '单字已在字集中'}), 409

    # 添加单字到字集
    char_in_set = CharacterInSet(
        character_set_id=set_id,
        character_id=data['character_id']
    )

    try:
        db.session.add(char_in_set)
        db.session.commit()
        return jsonify({
            'message': '单字添加成功',
            'character_in_set': char_in_set.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'单字添加失败: {str(e)}'}), 500


@character_sets_bp.route('/<int:set_id>/characters/<int:char_id>', methods=['DELETE'])
@jwt_required()
def remove_character_from_set(set_id, char_id):
    """从字集移除单字"""
    current_user_id = get_jwt_identity()

    # 检查字集是否存在且属于当前用户
    character_set = CharacterSet.query.filter_by(
        id=set_id,
        user_id=current_user_id
    ).first()

    if not character_set:
        return jsonify({'error': '字集不存在或无权限访问'}), 404

    # 检查单字是否在字集中
    char_in_set = CharacterInSet.query.filter_by(
        character_set_id=set_id,
        character_id=char_id
    ).first()

    if not char_in_set:
        return jsonify({'error': '单字不在字集中'}), 404

    try:
        db.session.delete(char_in_set)
        db.session.commit()
        return jsonify({'message': '单字移除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'单字移除失败: {str(e)}'}), 500


@character_sets_bp.route('/<int:set_id>/characters/move', methods=['POST'])
@jwt_required()
def move_character_between_sets(set_id):
    """移动单字到其他字集"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('character_id') or not data.get('target_set_id'):
        return jsonify({'error': '缺少单字ID或目标字集ID'}), 400

    # 检查源字集是否存在且属于当前用户
    source_set = CharacterSet.query.filter_by(
        id=set_id,
        user_id=current_user_id
    ).first()

    if not source_set:
        return jsonify({'error': '源字集不存在或无权限访问'}), 404

    # 检查目标字集是否存在且属于当前用户
    target_set = CharacterSet.query.filter_by(
        id=data['target_set_id'],
        user_id=current_user_id
    ).first()

    if not target_set:
        return jsonify({'error': '目标字集不存在或无权限访问'}), 404

    # 检查单字是否在源字集中
    char_in_set = CharacterInSet.query.filter_by(
        character_set_id=set_id,
        character_id=data['character_id']
    ).first()

    if not char_in_set:
        return jsonify({'error': '单字不在源字集中'}), 404

    # 检查单字是否已在目标字集中
    existing_in_target = CharacterInSet.query.filter_by(
        character_set_id=data['target_set_id'],
        character_id=data['character_id']
    ).first()

    if existing_in_target:
        return jsonify({'error': '单字已在目标字集中'}), 409

    try:
        # 更新单字所属字集
        char_in_set.character_set_id = data['target_set_id']
        db.session.commit()
        return jsonify({'message': '单字移动成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'单字移动失败: {str(e)}'}), 500
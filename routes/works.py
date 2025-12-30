from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Work, Like, Collection, Character
from utils import allowed_file, save_upload_file
import os
import base64
import json
import uuid
import requests
from datetime import datetime
from io import BytesIO

try:
	from PIL import Image  # Optional, used to get original image size
	_PIL_AVAILABLE = True
except Exception:
	_PIL_AVAILABLE = False

works_bp = Blueprint('works', __name__, url_prefix='/api/works')

@works_bp.route('/', methods=['GET'])
def get_works():
    """获取作品列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    style = request.args.get('style')
    status = request.args.get('status', 'approved')
    search = request.args.get('search')
    author = request.args.get('author')
    dynasty = request.args.get('dynasty')
    source_type = request.args.get('source_type')

    query = Work.query

    # 过滤状态
    if status:
        query = query.filter_by(status=status)

    # 过滤风格
    if style:
        query = query.filter_by(style=style)

    # 过滤作者
    if author:
        query = query.filter(Work.author_name.contains(author))

    # 过滤朝代
    if dynasty:
        query = query.filter(Work.dynasty.contains(dynasty))

    # 过滤来源类型
    if source_type:
        query = query.filter_by(source_type=source_type)

    # 搜索
    if search:
        query = query.filter(
            Work.title.contains(search) | 
            Work.description.contains(search) |
            Work.author_name.contains(search) |
            Work.dynasty.contains(search)
        )

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

    # 先压缩图片至宽度800像素
    from io import BytesIO
    compressed_file = BytesIO()
    new_width = 0
    new_height = 0
    
    with Image.open(file) as img:
        # 计算新尺寸，保持原始比例
        original_width, original_height = img.size
        if original_width > 800:
            new_width = 800
            new_height = int((new_width / original_width) * original_height)
        else:
            new_width, new_height = original_width, original_height
        
        # 调整图片尺寸
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 保存压缩后的图片到BytesIO对象
        resized_img.save(compressed_file, format=img.format)
        compressed_file.seek(0)
    
    # 将BytesIO对象转换为werkzeug.FileStorage对象，以便使用save_upload_file函数保存
    from werkzeug.datastructures import FileStorage
    compressed_file_storage = FileStorage(
        stream=compressed_file,
        filename=file.filename,
        content_type=file.content_type
    )
    
    # 保存压缩后的文件
    filename = save_upload_file(compressed_file_storage, 'works')
    if not filename:
        return jsonify({'error': '文件上传失败'}), 500

    # 获取作品基本信息
    title = request.form.get('title')
    description = request.form.get('description', '')
    style = request.form.get('style', '')
    dynasty = request.form.get('dynasty', '')
    author_name = request.form.get('author_name', '')
    source_type = request.form.get('source_type', '')
    
    # 获取标签，处理为列表格式
    tags_str = request.form.get('tags', '')
    tags = [tag.strip() for tag in tags_str.split(',')] if tags_str else []
    
    # 获取单字分割结果
    characters_json = request.form.get('characters', '')
    characters = []
    if characters_json:
        try:
            import json
            characters = json.loads(characters_json)
        except Exception as e:
            return jsonify({'error': f'单字分割数据格式错误: {str(e)}'}), 400

    if not title:
        return jsonify({'error': '缺少作品标题'}), 400

    # 创建作品，直接设为approved状态
    work = Work(
        title=title,
        description=description,
        image_url=filename,
        style=style,
        dynasty=dynasty,
        author_name=author_name,
        author_id=current_user_id,
        source_type=source_type,
        tags=tags,
        status='approved',  # 直接设为已通过，跳过审核
        original_width=new_width,  # 保存压缩后的宽度
        original_height=new_height  # 保存压缩后的高度
    )

    try:
        db.session.add(work)
        db.session.flush()  # 获取work.id，用于创建Character记录
        
        # 处理单字分割结果，创建Character记录
        if characters:
            for char_data in characters:
                # 确保单字数据包含必要字段
                if all(k in char_data for k in ['text', 'position', 'style']):
                    # 解析position字段 [x1, y1, x2, y2]
                    position = char_data['position']
                    if len(position) >= 4:
                        x1, y1, x2, y2 = position
                        # 创建Character记录，保存真实位置信息
                        character = Character(
                            work_id=work.id,
                            style=char_data['style'],
                            strokes=0,  # 默认值，后续可通过AI识别获取
                            stroke_order='',  # 默认值，后续可通过AI识别获取
                            recognition=char_data['text'],
                            source=work.title,
                            keypoints=char_data.get('keypoints', []),
                            collected_at=datetime.utcnow(),
                            x=x1,  # 保存真实X坐标
                            y=y1,  # 保存真实Y坐标
                            width=x2 - x1,  # 计算宽度
                            height=y2 - y1  # 计算高度
                        )
                        db.session.add(character)
        
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
    if 'dynasty' in data:
        work.dynasty = data['dynasty']
    if 'author_name' in data:
        work.author_name = data['author_name']

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


@works_bp.route('/<int:work_id>/characters', methods=['GET'])
def get_work_characters(work_id):
    """获取作品的单字列表"""
    work = Work.query.get(work_id)

    if not work:
        return jsonify({'error': '作品不存在'}), 404

    characters = work.characters.all()
    characters_data = [char.to_dict() for char in characters]

    return jsonify({'characters': characters_data}), 200


@works_bp.route('/<int:work_id>/characters', methods=['POST'])
@jwt_required()
def add_work_character(work_id):
    """添加作品单字"""
    current_user_id = get_jwt_identity()
    work = Work.query.get(work_id)

    if not work:
        return jsonify({'error': '作品不存在'}), 404

    # 检查权限：只有作品作者才能添加单字
    if work.author_id != int(current_user_id):
        return jsonify({'error': '无权添加单字'}), 403

    data = request.get_json()

    if not data:
        return jsonify({'error': '未接收到数据'}), 400

    # 验证必要字段
    if not data.get('recognition'):
        return jsonify({'error': '缺少单字内容'}), 400
    if not data.get('style'):
        return jsonify({'error': '缺少单字风格'}), 400
    if not data.get('x') or not data.get('y') or not data.get('width') or not data.get('height'):
        return jsonify({'error': '缺少单字位置信息'}), 400

    # 创建单字
    character = Character(
        work_id=work_id,
        style=data['style'],
        strokes=data.get('strokes', 0),
        stroke_order=data.get('stroke_order', ''),
        recognition=data['recognition'],
        source=work.title,
        keypoints=data.get('keypoints', []),
        collected_at=datetime.utcnow(),
        x=data['x'],
        y=data['y'],
        width=data['width'],
        height=data['height']
    )

    try:
        db.session.add(character)
        db.session.commit()
        return jsonify({
            'message': '单字添加成功',
            'character': character.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加单字失败: {str(e)}'}), 500


@works_bp.route('/characters/<int:character_id>', methods=['DELETE'])
@jwt_required()
def delete_character(character_id):
    """删除单字"""
    current_user_id = get_jwt_identity()
    character = Character.query.get(character_id)

    if not character:
        return jsonify({'error': '单字不存在'}), 404

    # 检查权限：只有作品作者才能删除单字
    if character.work.author_id != int(current_user_id):
        return jsonify({'error': '无权删除单字'}), 403

    try:
        db.session.delete(character)
        db.session.commit()
        return jsonify({'message': '单字删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除单字失败: {str(e)}'}), 500


@works_bp.route('/characters/<int:character_id>', methods=['PUT'])
@jwt_required()
def update_character(character_id):
    """修改作品单字"""
    current_user_id = get_jwt_identity()
    character = Character.query.get(character_id)

    if not character:
        return jsonify({'error': '单字不存在'}), 404

    # 检查权限：只有作品作者才能修改单字
    if character.work.author_id != int(current_user_id):
        return jsonify({'error': '无权修改单字'}), 403

    data = request.get_json()

    if not data:
        return jsonify({'error': '未接收到数据'}), 400

    # 更新单字字段
    if 'recognition' in data:
        character.recognition = data['recognition']
    if 'style' in data:
        character.style = data['style']
    if 'x' in data:
        character.x = data['x']
    if 'y' in data:
        character.y = data['y']
    if 'width' in data:
        character.width = data['width']
    if 'height' in data:
        character.height = data['height']
    if 'strokes' in data:
        character.strokes = data['strokes']
    if 'stroke_order' in data:
        character.stroke_order = data['stroke_order']
    if 'keypoints' in data:
        character.keypoints = data['keypoints']

    try:
        db.session.commit()
        return jsonify({
            'message': '单字更新成功',
            'character': character.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新单字失败: {str(e)}'}), 500


@works_bp.route('/characters/<int:character_id>', methods=['GET'])
def get_character(character_id):
    """
    获取单个单字的详情
    
    Response JSON:
    - character: 单字详情，包括keypoints
    """
    try:
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'error': '单字不存在'}), 404
        
        return jsonify({
            'character': character.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'获取单字详情失败: {str(e)}'}), 500


@works_bp.route('/characters', methods=['GET'])
def get_all_characters():
    """
    获取所有可用单字列表
    
    Response JSON:
    - characters: 单字列表
    - total: 单字总数
    """
    try:
        # 获取所有单字，按采集时间倒序排列
        characters = Character.query.order_by(Character.collected_at.desc()).all()
        characters_data = [char.to_dict() for char in characters]
        
        return jsonify({
            'characters': characters_data,
            'total': len(characters_data)
        }), 200
    except Exception as e:
        return jsonify({'error': f'获取单字列表失败: {str(e)}'}), 500


@works_bp.route('/config', methods=['GET'])
def get_work_config():
    """获取作品上传的预配置信息
    
    Response JSON:
    - styles: 书法风格列表 [{value, label}]
    - source_types: 来源类型列表 [{value, label}]
    - dynasties: 朝代列表 [{value, label}]
    """
    try:
        # 预配置的选项数据，返回前端需要的格式
        config = {
            'styles': [
                {'value': 'kai', 'label': '楷书'},
                {'value': 'xing', 'label': '行书'},
                {'value': 'cao', 'label': '草书'},
                {'value': 'li', 'label': '隶书'},
                {'value': 'zhuan', 'label': '篆书'},
                {'value': 'wei', 'label': '魏碑'},
                {'value': 'shoujin', 'label': '瘦金体'},
                {'value': 'other', 'label': '其他'}
            ],
            'source_types': [
                {'value': 'classic', 'label': '经典碑帖'},
                {'value': 'original', 'label': '原创作品'},
                {'value': 'copy', 'label': '临摹作品'}
            ],
            'dynasties': [
                {'value': '', 'label': '请选择'},
                {'value': '夏', 'label': '夏朝'},
                {'value': '商', 'label': '商朝'},
                {'value': '周', 'label': '周朝'},
                {'value': '春秋', 'label': '春秋时期'},
                {'value': '战国', 'label': '战国时期'},
                {'value': '秦', 'label': '秦朝'},
                {'value': '汉', 'label': '汉朝'},
                {'value': '西汉', 'label': '西汉'},
                {'value': '东汉', 'label': '东汉'},
                {'value': '三国', 'label': '三国时期'},
                {'value': '魏', 'label': '曹魏'},
                {'value': '蜀', 'label': '蜀汉'},
                {'value': '吴', 'label': '东吴'},
                {'value': '晋', 'label': '晋朝'},
                {'value': '西晋', 'label': '西晋'},
                {'value': '东晋', 'label': '东晋'},
                {'value': '南北朝', 'label': '南北朝'},
                {'value': '南朝', 'label': '南朝'},
                {'value': '北朝', 'label': '北朝'},
                {'value': '隋', 'label': '隋朝'},
                {'value': '唐', 'label': '唐朝'},
                {'value': '五代十国', 'label': '五代十国'},
                {'value': '五代', 'label': '五代'},
                {'value': '十国', 'label': '十国'},
                {'value': '宋', 'label': '宋朝'},
                {'value': '北宋', 'label': '北宋'},
                {'value': '南宋', 'label': '南宋'},
                {'value': '辽', 'label': '辽朝'},
                {'value': '金', 'label': '金朝'},
                {'value': '元', 'label': '元朝'},
                {'value': '明', 'label': '明朝'},
                {'value': '清', 'label': '清朝'},
                {'value': '中华民国', 'label': '中华民国'},
                {'value': '现代', 'label': '现代'},
                {'value': '当代', 'label': '当代'}
            ]
        }
        return jsonify(config), 200
    except Exception as e:
        return jsonify({'error': f'获取配置失败: {str(e)}'}), 500


@works_bp.route('/ocr', methods=['POST'])
def ocr_recognize():
    """调用古籍OCR API，对上传的图片进行识别，并将结果JSON暂存到 json_temp 目录。
    
    Request JSON:
    - image: base64 数据（可包含 dataURL 前缀）
    - det_mode/version/return_position: 可选透传参数
    
    Response JSON:
    - message: success | error
    - temp_json_path: 暂存JSON文件的相对路径
    - boxes: 提取的字符框 [{text, position:[x1,y1,x2,y2], confidence, det_confidence}]
    - image_size: {width, height} 原图尺寸（如可获取）
    """
    try:
        # 解析请求数据
        try:
            req_data = request.get_json(silent=True) or {}
        except Exception as e:
            return jsonify({'message': 'error', 'info': f'请求数据格式错误: {str(e)}'}), 400
        
        # 检查必要参数
        image_b64 = req_data.get('image', '')
        if not image_b64:
            return jsonify({'message': 'error', 'info': '缺少 image(base64) 参数'}), 400

        # 处理 base64 数据
        try:
            # 去掉 dataURL 前缀
            if ',' in image_b64:
                image_b64 = image_b64.split(',', 1)[1]
            
            # 验证 base64 格式
            base64.b64decode(image_b64, validate=True)
        except Exception as e:
            return jsonify({'message': 'error', 'info': f'base64 格式错误: {str(e)}'}), 400

        # 读取原图尺寸（如果 Pillow 可用）
        orig_width = None
        orig_height = None
        if _PIL_AVAILABLE:
            try:
                img_bytes = base64.b64decode(image_b64)
                with Image.open(BytesIO(img_bytes)) as im:
                    orig_width, orig_height = im.size
            except Exception:
                pass  # 忽略尺寸获取失败，继续执行

        # 获取 OCR API 配置
        token = os.getenv('Token', '').strip('"').strip("'")
        email = os.getenv('Email', '').strip('"').strip("'")
        if not token or not email:
            return jsonify({'message': 'error', 'info': '服务器未配置 OCR Token/Email 环境变量'}), 500

        # 组装 OCR API 请求参数
        params = {
            'token': token,
            'email': email,
            'image': image_b64
        }
        for key in ('det_mode', 'version', 'return_position'):
            if key in req_data:
                params[key] = req_data[key]
        # 默认参数确保返回位置信息
        params.setdefault('return_position', True)
        params.setdefault('version', 'v2')
        params.setdefault('det_mode', 'auto')

        # 调用远端 OCR API
        try:
            api_url = 'https://ocr.kandianguji.com/ocr_api'
            resp = requests.post(api_url, json=params, timeout=30)
            resp.raise_for_status()  # 检查 HTTP 响应状态码
            api_json = resp.json()
        except requests.exceptions.Timeout:
            return jsonify({'message': 'error', 'info': 'OCR API 请求超时'}), 504
        except requests.exceptions.ConnectionError:
            return jsonify({'message': 'error', 'info': 'OCR API 连接失败'}), 503
        except requests.exceptions.HTTPError as e:
            return jsonify({'message': 'error', 'info': f'OCR API 请求失败: HTTP {e.response.status_code}'}), 502
        except requests.exceptions.RequestException as e:
            return jsonify({'message': 'error', 'info': f'OCR API 请求失败: {str(e)}'}), 502
        except ValueError:
            return jsonify({'message': 'error', 'info': 'OCR API 返回格式错误'}), 502

        # 验证 OCR API 返回结果
        if not isinstance(api_json, dict):
            return jsonify({'message': 'error', 'info': 'OCR API 返回格式错误'}), 502
        
        if api_json.get('message') != 'success':
            return jsonify({'message': 'error', 'info': f'OCR 识别失败: {api_json.get("info", "未知错误")}'}), 502

        # 确保 json_temp 目录存在
        try:
            from flask import current_app
            json_temp_dir = os.path.join(os.path.dirname(current_app.instance_path), 'json_temp')
            os.makedirs(json_temp_dir, exist_ok=True)
        except Exception as e:
            return jsonify({'message': 'error', 'info': f'创建临时目录失败: {str(e)}'}), 500

        # 保存 OCR 结果到临时文件
        try:
            filename = f"ocr_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.json"
            temp_path = os.path.join(json_temp_dir, filename)
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(api_json, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return jsonify({'message': 'error', 'info': f'保存 OCR 结果失败: {str(e)}'}), 500

        # 提取字符框数据
        boxes = []
        try:
            data = api_json.get('data', {})
            text_lines = data.get('text_lines', [])
            for line_idx, text_line in enumerate(text_lines):
                words = text_line.get('words', [])
                for word_idx, word in enumerate(words):
                    text = word.get('text', '')
                    position = word.get('position', [])
                    confidence = word.get('confidence', 0.0)
                    det_confidence = word.get('det_confidence', 0.0)
                    if text and isinstance(position, list) and len(position) >= 4:
                        boxes.append({
                            'text': text,
                            'position': position[:4],  # [x1,y1,x2,y2]
                            'confidence': confidence,
                            'det_confidence': det_confidence,
                            'line_index': line_idx,
                            'word_index': word_idx
                        })
        except Exception as e:
            return jsonify({'message': 'error', 'info': f'处理 OCR 结果失败: {str(e)}'}), 500

        # 返回成功结果
        return jsonify({
            'message': 'success',
            'temp_json_path': f"json_temp/{filename}",
            'boxes': boxes,
            'image_size': {'width': orig_width, 'height': orig_height} if orig_width and orig_height else None
        }), 200

    except Exception as e:
        # 捕获所有未处理的异常
        return jsonify({'message': 'error', 'info': f'服务器内部错误: {str(e)}'}), 500

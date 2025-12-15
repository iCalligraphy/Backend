#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
书法分析API路由
提供字帖单字的智能解读功能
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import io
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User

# 尝试导入OpenAI客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

calligraphy_bp = Blueprint('calligraphy', __name__, url_prefix='/api/calligraphy')

# 配置
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image_if_needed(image):
    """
    确保图片边长大于300px
    
    Args:
        image: PIL Image对象
        
    Returns:
        调整后的PIL Image对象
    """
    width, height = image.size
    min_side = min(width, height)
    
    if min_side < 300:
        scale = 300 / min_side
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = image.resize((new_width, new_height), Image.LANCZOS)
    
    return image

def image_to_base64(image):
    """
    将PIL图像转换为base64编码
    
    Args:
        image: PIL Image对象
        
    Returns:
        base64编码的字符串
    """
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return img_base64

def analyze_with_doubao(image):
    """
    使用豆包视觉模型分析书法单字
    
    Args:
        image: PIL Image对象
        
    Returns:
        分析结果字典
    """
    if not OPENAI_AVAILABLE:
        raise Exception("OpenAI客户端未安装")
    
    # 获取环境变量配置
    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    vision_model = os.getenv("ARK_VISION_MODEL", "doubao-1.5-vision-pro-32k-250115")
    
    if not api_key:
        raise ValueError("未配置 ARK_API_KEY 环境变量")
    
    # 初始化客户端
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )
    
    # 调整图片大小
    image = resize_image_if_needed(image)
    
    # 转换为base64
    img_base64 = image_to_base64(image)
    
    # 构建提示词
    prompt = """请仔细分析这个书法单字，并提供以下信息：

1. 根据这个字的复杂程度，标注1-5个关键位置的坐标点（简单的字1-2个点，复杂的字3-5个点）
2. 对每个坐标点，说明在临摹时需要注意的事项

要求：
- 坐标以图片左上角为原点(0,0)，单位为像素
- 坐标格式为相对坐标，x和y的值都在0-1之间（例如图片中心点为(0.5, 0.5)）
- 标注的位置应该是临摹时需要特别注意的关键点，如：笔画交叉点、重要转折点、结构关键点等
- 每个点的注意事项要具体且实用，帮助初学者临摹

请严格按照以下JSON格式返回（不要有任何其他文字说明）：
{
    "character": "字的名称",
    "complexity": "简单/中等/复杂",
    "keypoints": [
        {
            "id": 1,
            "x": 0.5,
            "y": 0.3,
            "description": "这是什么位置",
            "tips": "临摹时需要注意什么"
        }
    ],
    "overall_tips": "整体临摹建议"
}"""
    
    # 调用视觉理解模型
    response = client.chat.completions.create(
        model=vision_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        temperature=0.7,
    )
    
    # 解析响应
    content = response.choices[0].message.content
    
    # 移除可能的markdown代码块标记
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    result = json.loads(content)
    
    # 添加元数据
    result["metadata"] = {
        "image_size": f"{image.size[0]}x{image.size[1]}",
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": vision_model
    }
    
    return result

@calligraphy_bp.route('/analyze', methods=['POST'])
def analyze_character():
    """
    分析书法单字
    
    接收图片文件，调用AI模型分析，返回关键点和注释
    """
    try:
        # 检查是否有文件
        if 'image' not in request.files:
            return jsonify({'error': '未找到图片文件'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式，请上传 JPG、PNG 或 WEBP 格式'}), 400
        
        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': '文件过大，请上传小于10MB的图片'}), 400
        
        # 读取图片
        image = Image.open(file.stream)
        
        # 转换为RGB模式（如果是RGBA或其他模式）
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 调用AI分析
        result = analyze_with_doubao(image)
        
        return jsonify({'analysis': result}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 500
    except json.JSONDecodeError as e:
        return jsonify({'error': f'AI返回结果解析失败: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

@calligraphy_bp.route('/save', methods=['POST'])
def save_annotations():
    """
    保存注释数据（兼容旧版API）
    
    接收JSON格式的注释数据，保存到本地文件
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '未接收到数据'}), 400
        
        # 创建保存目录（位于 Backend/calligraphy_annotations 下）
        save_dir = Path(__file__).resolve().parent.parent / 'calligraphy_annotations'
        save_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        character = data.get('character', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{character}_annotation_{timestamp}.json"
        filepath = save_dir / filename
        
        # 保存JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'message': '保存成功',
            'filepath': str(filepath)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@calligraphy_bp.route('/annotations', methods=['POST'])
@jwt_required()
def create_annotation():
    """
    创建新注释
    
    接收JSON格式的注释数据，添加用户身份信息后保存到本地文件
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '未接收到数据'}), 400
        
        # 验证必要字段
        if not data.get('character'):
            return jsonify({'error': '缺少必要字段: character'}), 400
        if not isinstance(data.get('keypoints'), list):
            return jsonify({'error': 'keypoints必须是数组'}), 400
        
        # 获取当前用户信息
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 添加用户身份信息
        data['user_id'] = current_user_id
        data['username'] = user.username
        
        # 确保timestamp字段存在
        if not data.get('timestamp'):
            data['timestamp'] = datetime.utcnow().isoformat()
        
        # 创建保存目录
        save_dir = Path(__file__).resolve().parent.parent / 'calligraphy_annotations'
        save_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        character = data.get('character', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{character}_annotation_{timestamp}.json"
        filepath = save_dir / filename
        
        # 保存JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'id': filename,
            'message': '注释创建成功',
            'annotation': {
                'id': filename,
                'character': data['character'],
                'user_id': data['user_id'],
                'username': data['username'],
                'keypoints': data['keypoints'],
                'timestamp': data['timestamp']
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'创建注释失败: {str(e)}'}), 500

@calligraphy_bp.route('/annotations', methods=['GET'])
def get_annotations():
    """
    获取所有注释列表
    
    查询参数:
        page: 页码，默认1
        per_page: 每页数量，默认10
        sort_by: 排序字段，默认timestamp
        order: 排序顺序，asc或desc，默认desc
    
    返回注释列表，带分页信息
    """
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        sort_by = request.args.get('sort_by', 'timestamp')
        order = request.args.get('order', 'desc')
        
        # 验证参数
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        save_dir = Path(__file__).resolve().parent.parent / 'calligraphy_annotations'
        
        if not save_dir.exists():
            return jsonify({
                'annotations': [],
                'pagination': {
                    'total': 0,
                    'pages': 0,
                    'page': page,
                    'per_page': per_page
                }
            }), 200
        
        # 获取所有注释文件
        all_annotations = []
        for filepath in save_dir.glob('*.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_annotations.append({
                        'id': filepath.name,
                        'filename': filepath.name,
                        'character': data.get('character', 'unknown'),
                        'user_id': data.get('user_id'),
                        'username': data.get('username'),
                        'timestamp': data.get('timestamp', ''),
                        'keypoints_count': len(data.get('keypoints', []))
                    })
            except Exception:
                continue
        
        # 排序
        reverse = order.lower() == 'desc'
        all_annotations.sort(key=lambda x: x[sort_by] if sort_by in x else '', reverse=reverse)
        
        # 分页
        total = len(all_annotations)
        pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        paginated_annotations = all_annotations[start:end]
        
        return jsonify({
            'annotations': paginated_annotations,
            'pagination': {
                'total': total,
                'pages': pages,
                'page': page,
                'per_page': per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取列表失败: {str(e)}'}), 500

@calligraphy_bp.route('/list', methods=['GET'])
def list_annotations():
    """
    列出所有已保存的注释（兼容旧版API）
    
    返回注释列表
    """
    try:
        save_dir = Path(__file__).resolve().parent.parent / 'calligraphy_annotations'
        
        if not save_dir.exists():
            return jsonify({'annotations': []}), 200
        
        annotations = []
        for filepath in save_dir.glob('*.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    annotations.append({
                        'filename': filepath.name,
                        'character': data.get('character', 'unknown'),
                        'timestamp': data.get('timestamp', ''),
                        'keypoints_count': len(data.get('keypoints', []))
                    })
            except Exception:
                continue
        
        # 按时间倒序排序
        annotations.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'annotations': annotations}), 200
        
    except Exception as e:
        return jsonify({'error': f'获取列表失败: {str(e)}'}), 500

@calligraphy_bp.route('/annotations/<id>', methods=['GET'])
def get_annotation(id):
    """
    获取单个注释详情
    
    Args:
        id: 注释ID（文件名）
        
    Returns:
        注释数据
    """
    try:
        # 注意：不使用secure_filename，因为它会过滤掉中文字符
        # 直接使用id作为文件名，因为我们在创建时已经使用了安全的文件名生成方式
        save_dir = Path(__file__).resolve().parent.parent / 'calligraphy_annotations'
        
        # 遍历所有文件，找到匹配的文件
        target_file = None
        for filepath in save_dir.glob('*.json'):
            if filepath.name == id:
                target_file = filepath
                break
        
        if not target_file:
            return jsonify({'error': '注释不存在'}), 404
        
        with open(target_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 添加id字段
        data['id'] = id
        
        return jsonify({
            'annotation': data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取注释失败: {str(e)}'}), 500

@calligraphy_bp.route('/annotations/<id>', methods=['PUT'])
@jwt_required()
def update_annotation(id):
    """
    更新注释
    
    Args:
        id: 注释ID（文件名）
        
    Returns:
        更新后的注释数据
    """
    try:
        save_dir = Path(__file__).resolve().parent.parent / 'calligraphy_annotations'
        
        # 遍历所有文件，找到匹配的文件
        target_file = None
        for filepath in save_dir.glob('*.json'):
            if filepath.name == id:
                target_file = filepath
                break
        
        if not target_file:
            return jsonify({'error': '注释不存在'}), 404
        
        # 读取现有注释
        with open(target_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        # 获取当前用户信息
        current_user_id = get_jwt_identity()
        
        # 检查权限：只有创建者才能更新
        if str(existing_data.get('user_id')) != current_user_id:
            return jsonify({'error': '没有权限更新此注释'}), 403
        
        # 获取更新数据
        update_data = request.get_json()
        
        if not update_data:
            return jsonify({'error': '未接收到更新数据'}), 400
        
        # 验证必要字段
        if 'character' in update_data and not update_data['character']:
            return jsonify({'error': 'character字段不能为空'}), 400
        if 'keypoints' in update_data and not isinstance(update_data['keypoints'], list):
            return jsonify({'error': 'keypoints必须是数组'}), 400
        
        # 更新注释数据
        updated_data = {**existing_data, **update_data}
        
        # 确保用户身份信息不被修改
        updated_data['user_id'] = existing_data['user_id']
        updated_data['username'] = existing_data['username']
        
        # 更新timestamp
        updated_data['timestamp'] = datetime.utcnow().isoformat()
        
        # 保存更新后的注释
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        
        # 添加id字段
        updated_data['id'] = id
        
        return jsonify({
            'message': '注释更新成功',
            'annotation': updated_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'更新注释失败: {str(e)}'}), 500

@calligraphy_bp.route('/annotations/<id>', methods=['DELETE'])
@jwt_required()
def delete_annotation(id):
    """
    删除注释
    
    Args:
        id: 注释ID（文件名）
        
    Returns:
        成功消息
    """
    try:
        save_dir = Path(__file__).resolve().parent.parent / 'calligraphy_annotations'
        
        # 遍历所有文件，找到匹配的文件
        target_file = None
        for filepath in save_dir.glob('*.json'):
            if filepath.name == id:
                target_file = filepath
                break
        
        if not target_file:
            return jsonify({'error': '注释不存在'}), 404
        
        # 读取现有注释，检查权限
        with open(target_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        # 获取当前用户信息
        current_user_id = get_jwt_identity()
        
        # 检查权限：只有创建者才能删除
        if str(existing_data.get('user_id')) != current_user_id:
            return jsonify({'error': '没有权限删除此注释'}), 403
        
        # 删除文件
        target_file.unlink()
        
        return jsonify({
            'message': '注释删除成功',
            'id': id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'删除注释失败: {str(e)}'}), 500

@calligraphy_bp.route('/load/<filename>', methods=['GET'])
def load_annotation(filename):
    """
    加载指定的注释文件（兼容旧版API）
    
    Args:
        filename: 文件名
        
    Returns:
        注释数据
    """
    try:
        # 安全检查文件名
        filename = secure_filename(filename)
        
        save_dir = Path(__file__).resolve().parent.parent / 'calligraphy_annotations'
        filepath = save_dir / filename
        
        if not filepath.exists():
            return jsonify({'error': '文件不存在'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({'error': f'加载失败: {str(e)}'}), 500

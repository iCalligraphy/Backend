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
import numpy as np
from werkzeug.utils import secure_filename
from PIL import Image
import io
import cv2

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
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 500
    except json.JSONDecodeError as e:
        return jsonify({'error': f'AI返回结果解析失败: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

@calligraphy_bp.route('/save', methods=['POST'])
def save_annotations():
    """
    保存注释数据
    
    接收JSON格式的注释数据，保存到本地文件
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '未接收到数据'}), 400
        
        # 新增
        
        # json_String=json.dumps(data)
        # encoded_Data=base64.b64encode(json_String.encode()).decode()
        # token="44782d01-8259-485f-ac9f-7cc0a3ef1b27"
        # email="15168632863"
        # # received_Data=request.post("https://ocr.kandianguji.com/ocr_api",token,email,encoded_data)
        # received_Message,received_Id,received_Info,received_Data=request.post("https://ocr.kandianguji.com/ocr_api",token,email,encoded_Data,return_position=True)
        # image_Data=base64.b64decode(encoded_Data)
        # image_Array=np.frombuffer(image_Data,np.uint8)
        # image=cv2.imdecode(image_Array,cv2.IMREAD_COLOR)
        # text_Lines=received_Data["text_lines"]
        # position=text_Lines["position"]
        # for i in position:
        #     image=cv2.polylines(image,i,True)
        # data=json.dumps(image,cls=NumpyArrayEncoder)
        
        # 新增结尾
 
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

@calligraphy_bp.route('/list', methods=['GET'])
def list_annotations():
    """
    列出所有已保存的注释
    
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

@calligraphy_bp.route('/load/<filename>', methods=['GET'])
def load_annotation(filename):
    """
    加载指定的注释文件
    
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

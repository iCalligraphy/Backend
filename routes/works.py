from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Work, Like, Collection
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

works_bp = Blueprint("works", __name__, url_prefix="/api/works")


@works_bp.route("/", methods=["GET"])
def get_works():
    """获取作品列表"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 12, type=int)
    style = request.args.get("style")
    status = request.args.get("status", "approved")
    search = request.args.get("search")

    query = Work.query

    # 过滤状态
    if status:
        query = query.filter_by(status=status)

    # 过滤风格
    if style:
        query = query.filter_by(style=style)

    # 搜索
    if search:
        query = query.filter(
            Work.title.contains(search) | Work.description.contains(search)
        )

    # 分页
    pagination = query.order_by(Work.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    works = [work.to_dict() for work in pagination.items]

    return (
        jsonify(
            {
                "works": works,
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages,
            }
        ),
        200,
    )


@works_bp.route("/<int:work_id>", methods=["GET"])
def get_work(work_id):
    """获取单个作品详情"""
    work = Work.query.get(work_id)

    if not work:
        return jsonify({"error": "作品不存在"}), 404

    # 增加浏览次数
    work.views += 1
    db.session.commit()

    return jsonify({"work": work.to_dict()}), 200


@works_bp.route("/", methods=["POST"])
@jwt_required()
def create_work():
    """创建新作品"""
    current_user_id = get_jwt_identity()

    # 检查是否有文件上传
    if "image" not in request.files:
        return jsonify({"error": "缺少图片文件"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "未选择文件"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "不支持的文件格式"}), 400

    # 保存文件
    filename = save_upload_file(file, "works")
    if not filename:
        return jsonify({"error": "文件上传失败"}), 500

    # 获取其他字段
    title = request.form.get("title")
    description = request.form.get("description", "")
    style = request.form.get("style", "")

    if not title:
        return jsonify({"error": "缺少作品标题"}), 400

    # 创建作品
    work = Work(
        title=title,
        description=description,
        image_url=filename,
        style=style,
        author_id=current_user_id,
    )

    try:
        db.session.add(work)
        db.session.commit()
        return jsonify({"message": "作品创建成功", "work": work.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"创建失败: {str(e)}"}), 500


@works_bp.route("/<int:work_id>", methods=["PUT"])
@jwt_required()
def update_work(work_id):
    """更新作品"""
    current_user_id = get_jwt_identity()
    work = Work.query.get(work_id)

    if not work:
        return jsonify({"error": "作品不存在"}), 404

    if work.author_id != current_user_id:
        return jsonify({"error": "无权修改此作品"}), 403

    data = request.get_json()

    if "title" in data:
        work.title = data["title"]
    if "description" in data:
        work.description = data["description"]
    if "style" in data:
        work.style = data["style"]

    try:
        db.session.commit()
        return jsonify({"message": "作品更新成功", "work": work.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"更新失败: {str(e)}"}), 500


@works_bp.route("/<int:work_id>", methods=["DELETE"])
@jwt_required()
def delete_work(work_id):
    """删除作品"""
    current_user_id = get_jwt_identity()
    work = Work.query.get(work_id)

    if not work:
        return jsonify({"error": "作品不存在"}), 404

    if work.author_id != current_user_id:
        return jsonify({"error": "无权删除此作品"}), 403

    try:
        # 删除关联的图片文件
        if work.image_url:
            from flask import current_app

            file_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], "works", work.image_url
            )
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(work)
        db.session.commit()
        return jsonify({"message": "作品删除成功"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"删除失败: {str(e)}"}), 500


@works_bp.route("/<int:work_id>/like", methods=["POST"])
@jwt_required()
def like_work(work_id):
    """点赞作品"""
    current_user_id = get_jwt_identity()
    work = Work.query.get(work_id)

    if not work:
        return jsonify({"error": "作品不存在"}), 404

    # 检查是否已点赞
    existing_like = Like.query.filter_by(
        user_id=current_user_id, work_id=work_id
    ).first()
    if existing_like:
        return jsonify({"error": "已经点赞过了"}), 409

    like = Like(user_id=current_user_id, work_id=work_id)

    try:
        db.session.add(like)
        db.session.commit()
        return jsonify({"message": "点赞成功"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"点赞失败: {str(e)}"}), 500


@works_bp.route("/<int:work_id>/like", methods=["DELETE"])
@jwt_required()
def unlike_work(work_id):
    """取消点赞"""
    current_user_id = get_jwt_identity()
    like = Like.query.filter_by(user_id=current_user_id, work_id=work_id).first()

    if not like:
        return jsonify({"error": "尚未点赞"}), 404

    try:
        db.session.delete(like)
        db.session.commit()
        return jsonify({"message": "取消点赞成功"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"取消点赞失败: {str(e)}"}), 500


@works_bp.route("/ocr", methods=["POST"])
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
        req_data = request.get_json(silent=True) or {}
        image_b64 = req_data.get("image", "")
        if not image_b64:
            return jsonify({"message": "error", "info": "缺少 image(base64)"}), 400

        # 去掉 dataURL 前缀
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        # 读取原图尺寸（如果 Pillow 可用）
        orig_width = None
        orig_height = None
        if _PIL_AVAILABLE:
            try:
                img_bytes = base64.b64decode(image_b64)
                with Image.open(BytesIO(img_bytes)) as im:
                    orig_width, orig_height = im.size
            except Exception:
                pass

        # 环境变量中读取鉴权
        token = os.getenv("Token", "").strip('"').strip("'")
        email = os.getenv("Email", "").strip('"').strip("'")
        if not token or not email:
            return (
                jsonify({"message": "error", "info": "服务器未配置 OCR Token/Email 环境变量"}),
                500,
            )

        # 组装请求体（透传可选参数）
        params = {"token": token, "email": email, "image": image_b64}
        for key in ("det_mode", "version", "return_position"):
            if key in req_data:
                params[key] = req_data[key]

        # 默认确保返回位置信息
        params.setdefault("return_position", True)
        params.setdefault("version", "v2")
        params.setdefault("det_mode", "auto")

        # 调用远端 OCR
        api_url = "https://ocr.kandianguji.com/ocr_api"
        resp = requests.post(api_url, json=params, timeout=30)
        resp.raise_for_status()
        api_json = resp.json()

        # 保存到 json_temp
        from flask import current_app

        json_temp_dir = os.path.join(
            os.path.dirname(current_app.instance_path), "json_temp"
        )
        if not os.path.exists(json_temp_dir):
            os.makedirs(json_temp_dir, exist_ok=True)

        filename = (
            f"ocr_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.json"
        )
        temp_path = os.path.join(json_temp_dir, filename)
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(api_json, f, ensure_ascii=False, indent=2)

        # 保存到数据库 新增
        import logging

        logging.basicConfig()
        logging.getLogger("sqlqlchemy.orm").setLevel(logging.DEBUG)
        # print(1)
        # print(Work.query.column_descriptions)
        # print(Work.query.all())
        # cnt =Work.query.all()
        # print(1)
        image_data = req_data.get("image_data", "")
        print(image_data["title"])
        work = Work(
            id=2,
            title=image_data["title"],
            author_name=image_data["author"],
            dynasty=image_data["dynasty"],
            style=image_data["style"],
            description=image_data["description"],
            image_url=f"json_temp/{filename}",
            author_id=1
            # image_data
        )
        print(1)
        db.session.add(work)
        db.session.commit()
        print(1)
        # 新增

        # 提取 boxes（与 API_Test/extract_characters.py 的结构保持一致字段）
        boxes = []
        if isinstance(api_json, dict) and api_json.get("message") == "success":
            data = api_json.get("data", {})
            text_lines = data.get("text_lines", [])
            for line_idx, text_line in enumerate(text_lines):
                words = text_line.get("words", [])
                for word_idx, word in enumerate(words):
                    text = word.get("text", "")
                    position = word.get("position", [])
                    confidence = word.get("confidence", 0.0)
                    det_confidence = word.get("det_confidence", 0.0)
                    if text and isinstance(position, list) and len(position) >= 4:
                        boxes.append(
                            {
                                "text": text,
                                "position": position[:4],  # [x1,y1,x2,y2]
                                "confidence": confidence,
                                "det_confidence": det_confidence,
                                "line_index": line_idx,
                                "word_index": word_idx,
                            }
                        )

        return (
            jsonify(
                {
                    "message": "success",
                    "temp_json_path": f"json_temp/{filename}",
                    "boxes": boxes,
                    "image_size": {"width": orig_width, "height": orig_height}
                    if orig_width and orig_height
                    else None,
                }
            ),
            200,
        )

    except requests.exceptions.RequestException as e:
        return jsonify({"message": "error", "info": f"OCR API 请求失败: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"message": "error", "info": f"服务器错误: {str(e)}"}), 500

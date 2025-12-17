import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload_file(file, subfolder=''):
    """
    保存上传的文件

    Args:
        file: 上传的文件对象
        subfolder: 子文件夹名称（如 'works', 'avatars'）

    Returns:
        str: 保存的文件名，失败返回 None
    """
    if not file or file.filename == '':
        return None

    if not allowed_file(file.filename):
        return None

    # 生成唯一文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    filename = secure_filename(filename)

    # 确保上传目录存在
    from flask import current_app
    upload_path = current_app.config['UPLOAD_FOLDER']

    if subfolder:
        upload_path = os.path.join(upload_path, subfolder)

    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    # 保存文件
    file_path = os.path.join(upload_path, filename)
    try:
        file.save(file_path)
        return filename
    except Exception as e:
        print(f"文件保存失败: {str(e)}")
        return None


def delete_file(filename, subfolder=''):
    """
    删除文件

    Args:
        filename: 文件名
        subfolder: 子文件夹名称

    Returns:
        bool: 删除是否成功
    """
    from flask import current_app
    upload_path = current_app.config['UPLOAD_FOLDER']

    if subfolder:
        upload_path = os.path.join(upload_path, subfolder)

    file_path = os.path.join(upload_path, filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"文件删除失败: {str(e)}")
        return False


def get_file_url(filename, subfolder=''):
    """
    获取文件的 URL

    Args:
        filename: 文件名
        subfolder: 子文件夹名称

    Returns:
        str: 文件的 URL 路径
    """
    if subfolder:
        return f"/uploads/{subfolder}/{filename}"
    return f"/uploads/{filename}"


def create_notification(user_id, notification_type, content, related_id, related_type):
    """
    创建通知记录

    Args:
        user_id: 接收通知的用户ID
        notification_type: 通知类型（like, comment, follow, mention, system）
        content: 通知内容
        related_id: 关联对象ID
        related_type: 关联对象类型（post, comment, user等）

    Returns:
        Notification: 创建的通知对象
    """
    from models import db, Notification
    
    # 创建通知记录
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        content=content,
        related_id=related_id,
        related_type=related_type,
        is_read=False
    )
    
    try:
        db.session.add(notification)
        db.session.commit()
        print(f'已创建通知给用户 {user_id}')
        return notification
    except Exception as e:
        db.session.rollback()
        print(f'创建通知失败: {str(e)}')
        return None

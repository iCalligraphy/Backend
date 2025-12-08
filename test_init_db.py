"""
简单的数据库初始化测试脚本
"""
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.abspath('.'))

from app import create_app
from models import db, User, Work

def simple_init():
    """简单初始化数据库"""
    print("开始简单数据库初始化...")
    
    # 创建应用实例
    app = create_app()
    
    with app.app_context():
        try:
            # 创建所有表
            print("正在创建所有表...")
            db.create_all()
            print("表创建成功")
            
            # 检查users表是否存在
            from sqlalchemy import text
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")).fetchone()
            if result:
                print("users表存在")
            else:
                print("users表不存在")
                return False
            
            print("数据库初始化成功！")
            return True
            
        except Exception as e:
            print(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    simple_init()
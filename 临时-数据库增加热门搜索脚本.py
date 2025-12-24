"""
数据库迁移脚本 - 添加 search_logs 表
此脚本用于在现有数据库中安全添加搜索记录表，不会影响现有数据
"""
from app import create_app
from models import db, SearchLog
from sqlalchemy import inspect

def migrate():
    """添加 search_logs 表"""
    app, _ = create_app()

    with app.app_context():
        # 检查表是否已存在
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'search_logs' in existing_tables:
            print("search_logs 表已存在，无需迁移")
            return
        
        # 只创建 SearchLog 表
        print("正在创建 search_logs 表...")
        SearchLog.__table__.create(db.engine)
        
        print("search_logs 表创建成功！")
        print("\n热门搜索功能已启用：")
        print("  - 每次用户搜索时会自动记录搜索词")
        print("  - 通过 /api/calligraphy/hot-keywords 获取热门搜索词")


if __name__ == '__main__':
    migrate()

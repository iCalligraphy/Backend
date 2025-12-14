"""
数据库初始化脚本
用于创建数据库表和初始数据
"""
from app import create_app
from models import db, User, Work
from datetime import datetime


def init_db():
    """初始化数据库"""
    app = create_app()

    with app.app_context():
        # 删除所有表
        print("正在删除旧表...")
        db.drop_all()

        # 创建所有表
        print("正在创建新表...")
        db.create_all()

        # 创建测试用户
        print("正在创建测试数据...")
        admin = User(
            username="admin", email="admin@icalligraphy.com", bio="系统管理员",
            phone="admin"
        )
        admin.set_password("admin123")

        test_user = User(
            username="testuser",
            email="test@example.com",
            bio="测试用户，喜欢书法艺术",
            phone="test",
        )
        test_user.set_password("test123")

        test_work = Work(
            id=1,
            title="test",
            image_url="test",
            author_name="test",
            dynasty="test",
            style="test",
            description="test",
            author_id=1,
        )

        db.session.add(admin)
        db.session.add(test_user)
        db.session.add(test_work)
        db.session.commit()
        # print(db.session.query(User).all())
        print(db.session.query(Work).all())

        print(f"创建用户成功:")
        print(f"  - 管理员: username=admin, password=admin123")
        print(f"  - 测试用户: username=testuser, password=test123")

        print("\n数据库初始化完成！")


if __name__ == "__main__":
    init_db()

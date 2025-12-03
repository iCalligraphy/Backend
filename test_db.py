from app import create_app
from models import db, User

def test_user_exists():
    app = create_app()
    with app.app_context():
        # 查询所有用户
        users = User.query.all()
        print(f"数据库中共有 {len(users)} 个用户")
        
        # 检查admin用户
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("admin用户存在:")
            print(f"- 用户名: {admin.username}")
            print(f"- 邮箱: {admin.email}")
            print(f"- 密码哈希: {admin.password_hash}")
        else:
            print("错误: admin用户不存在!")

if __name__ == '__main__':
    test_user_exists()
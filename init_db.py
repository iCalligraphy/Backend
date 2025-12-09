"""
数据库初始化脚本
用于创建数据库表和初始数据
"""
from app import create_app
from models import db, User, Work, Follow, Topic
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
            username='admin',
            email='admin@icalligraphy.com',
            bio='系统管理员'
        )
        admin.set_password('admin123')

        test_user = User(
            username='testuser',
            email='test@example.com',
            bio='测试用户，喜欢书法艺术'
        )
        test_user.set_password('test123')

        db.session.add(admin)
        db.session.add(test_user)
        db.session.commit()

        print(f"创建用户成功:")
        print(f"  - 管理员: username=admin, password=admin123")
        print(f"  - 测试用户: username=testuser, password=test123")

        # 创建初始话题分类
        print("\n正在创建话题分类...")
        initial_topics = [
            {
                'id': 'technique',
                'name': '技法交流',
                'description': '分享书写技巧，讨论笔法、结构、章法等',
                'post_count': 1250,
                'today_posts': 23,
                'color': '#8b4513',
                'icon': '🖌️',
                'is_popular': True,
                'created_at': datetime(2022, 3, 15)
            },
            {
                'id': 'appreciation',
                'name': '作品欣赏',
                'description': '欣赏经典与原创书法作品，交流鉴赏心得',
                'post_count': 890,
                'today_posts': 15,
                'color': '#4682b4',
                'icon': '🖼️',
                'is_popular': True,
                'created_at': datetime(2022, 3, 16)
            },
            {
                'id': 'qna',
                'name': '问答求助',
                'description': '提出书法学习中的疑问，互相解答帮助',
                'post_count': 678,
                'today_posts': 19,
                'color': '#32cd32',
                'icon': '❓',
                'is_popular': False,
                'created_at': datetime(2022, 3, 17)
            },
            {
                'id': 'materials',
                'name': '文房四宝',
                'description': '讨论笔墨纸砚等书法工具的选择与使用',
                'post_count': 543,
                'today_posts': 12,
                'color': '#daa520',
                'icon': '✒️',
                'is_popular': False,
                'created_at': datetime(2022, 3, 18)
            },
            {
                'id': 'events',
                'name': '活动赛事',
                'description': '书法比赛、展览、线下活动等信息分享',
                'post_count': 321,
                'today_posts': 8,
                'color': '#ff6347',
                'icon': '🏆',
                'is_popular': False,
                'created_at': datetime(2022, 3, 19)
            }
        ]

        for topic_data in initial_topics:
            topic = Topic(**topic_data)
            db.session.add(topic)
        db.session.commit()

        print(f"创建话题分类成功，共 {len(initial_topics)} 个话题:")
        for topic_data in initial_topics:
            print(f"  - {topic_data['name']} (ID: {topic_data['id']})")

        print("\n数据库初始化完成！")


if __name__ == '__main__':
    init_db()

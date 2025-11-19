"""
数据库初始化脚本
用于创建数据库表和初始数据
"""
from models import db, User, Work, Comment, CalligraphySet, CalligraphyRead
from datetime import datetime
from flask import Flask
import os
import json

def init_db(app):
    """初始化数据库"""
    with app.app_context():
        # 删除旧表
        db.drop_all()
        # 创建新表
        db.create_all()
        
        print("开始创建测试数据...")
        
        # 创建测试用户
        test_user1 = User(
            username='13800138001',  # 默认手机号
            nickname='书法爱好者',
            phone='13800138001',
            common_font='楷书',
            avatar='default_avatar1.png'
        )
        test_user1.set_password('password123')  # 使用MD5加密
        db.session.add(test_user1)
        
        test_user2 = User(
            username='13900139002',
            nickname='专业书法家',
            phone='13900139002',
            common_font='行书',
            avatar='default_avatar2.png'
        )
        test_user2.set_password('password123')
        db.session.add(test_user2)
        
        test_user3 = User(
            username='13700137003',
            nickname='书法初学者',
            phone='13700137003',
            common_font='隶书',
            avatar='default_avatar3.png'
        )
        test_user3.set_password('password123')
        db.session.add(test_user3)
        
        # 提交用户到数据库以获取ID
        db.session.commit()
        print(f"创建了 {User.query.count()} 个用户")
        
        # 创建话题
        # 创建测试作品
        work1 = Work(
            u_id=test_user1.u_id,
            title='家和万事兴挂联',
            content='借鉴颜真卿《多宝塔碑》笔法，横排布局',
            image_url='/static/images/work1.jpg',
            font_type='楷书',
            like_count=2,
            comment_count=1
        )
        db.session.add(work1)
        
        work2 = Work(
            u_id=test_user2.u_id,
            title='宁静致远',
            content='行书作品，表达平和心态',
            image_url='/static/images/work2.jpg',
            font_type='行书',
            like_count=1,
            comment_count=0
        )
        db.session.add(work2)
        
        work3 = Work(
            u_id=test_user1.u_id,
            title='中国梦',
            content='展现时代精神',
            image_url='/static/images/work3.jpg',
            font_type='楷书',
            like_count=1,
            comment_count=0
        )
        db.session.add(work3)
        
        # 提交作品到数据库以获取ID
        db.session.commit()
        print(f"创建了 {Work.query.count()} 个作品")
        
        # 创建测试评论
        comment1 = Comment(
            u_id=test_user2.u_id,
            w_id=work1.w_id,
            comment_type='笔法',
            content='笔法精湛，气势恢宏！'
        )
        db.session.add(comment1)
        
        comment2 = Comment(
            u_id=test_user3.u_id,
            w_id=work2.w_id,
            comment_type='结构',
            content='结构严谨，非常精美！'
        )
        db.session.add(comment2)
        
        comment3 = Comment(
            u_id=test_user1.u_id,
            w_id=work1.w_id,
            comment_type='章法',
            content='章法布局合理，值得学习'
        )
        db.session.add(comment3)
        
        db.session.commit()
        print(f"创建了 {Comment.query.count()} 个评论")
        
        # 创建集字记录
        calligraphy_set1 = CalligraphySet(
            u_id=test_user1.u_id,
            target_text='家和万事兴',
            font_type='楷书',
            copybook_author='颜真卿',
            layout_type='横排',
            image_url='/static/images/calligraphy_set1.jpg'
        )
        db.session.add(calligraphy_set1)
        
        calligraphy_set2 = CalligraphySet(
            u_id=test_user2.u_id,
            target_text='宁静致远',
            font_type='行书',
            copybook_author='王羲之',
            layout_type='竖排',
            image_url='/static/images/calligraphy_set2.jpg'
        )
        db.session.add(calligraphy_set2)
        
        db.session.commit()
        print(f"创建了 {CalligraphySet.query.count()} 个集字记录")
        
        # 创建读帖记录
        analysis_data1 = json.dumps({
            "stroke": {"start": "露锋入笔", "end": "回锋收笔"},
            "structure": {"type": "方形", "balance": "左侧紧凑"},
            "comment": "该字结构严谨，笔力遒劲"
        })
        
        calligraphy_read1 = CalligraphyRead(
            u_id=test_user1.u_id,
            char_id=None,
            copybook_id=None,
            upload_image_url='/static/images/char1.jpg',
            analysis_data=analysis_data1
        )
        db.session.add(calligraphy_read1)
        
        analysis_data2 = json.dumps({
            "stroke": {"start": "藏锋入笔", "end": "出锋收笔"},
            "structure": {"type": "长方形", "balance": "左右均衡"},
            "comment": "该字笔法流畅，结构优美"
        })
        
        calligraphy_read2 = CalligraphyRead(
            u_id=test_user3.u_id,
            char_id=None,
            copybook_id=None,
            upload_image_url='/static/images/char2.jpg',
            analysis_data=analysis_data2
        )
        db.session.add(calligraphy_read2)
        
        db.session.commit()
        print(f"创建了 {CalligraphyRead.query.count()} 个读帖记录")
        
        # 提交所有更改
        db.session.commit()
        
        print("数据库初始化完成！")
        print("\n数据库内容概览：")
        print(f"用户总数: {User.query.count()}")
        print(f"作品总数: {Work.query.count()}")
        
        print(f"评论总数: {Comment.query.count()}")
        print(f"集字记录: {CalligraphySet.query.count()}")
        print(f"读帖记录: {CalligraphyRead.query.count()}")

if __name__ == '__main__':
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 配置数据库
    basedir = os.path.abspath(os.path.dirname(__file__)) + "/instance"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'icalligraphy.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    # 调用初始化函数
    init_db(app)

from flask import Flask, jsonify, send_from_directory, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

from config import config
from models import db, User
from routes import auth_bp, works_bp, users_bp, comments_bp, collections_bp, calligraphy_bp, posts_bp

# 加载环境变量
load_dotenv()

def create_app(config_name='default'):
    """创建 Flask 应用工厂"""
    # 获取前端目录的绝对路径
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Frontend-HTML')
    template_dir = os.path.join(frontend_dir, 'templates')
    static_dir = os.path.join(frontend_dir, 'static')

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir,
                static_url_path='/static')

    # 加载配置
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
    jwt = JWTManager(app)

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(works_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(calligraphy_bp)
    app.register_blueprint(posts_bp)

    # 创建上传目录
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'works'))
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'))

    # 创建 json_temp 目录（用于暂存OCR结果）
    json_temp_dir = os.path.join(os.path.dirname(app.instance_path), 'json_temp')
    if not os.path.exists(json_temp_dir):
        os.makedirs(json_temp_dir, exist_ok=True)
        
    # 静态文件路由（用于访问上传的图片）
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """访问上传的文件"""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # ========== 前端页面路由 ==========
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html', active_page='index')

    @app.route('/auth')
    @app.route('/auth.html')
    def auth():
        """登录/注册页面"""
        return render_template('auth.html', active_page='auth')
        
    @app.route('/login')
    def login_page():
        """登录页面（重定向到auth页面）"""
        return render_template('auth.html', active_page='auth')

    @app.route('/profile')
    def profile():
        """个人主页"""
        return render_template('profile.html', active_page='profile')

    @app.route('/search')
    def search():
        """搜索页面"""
        return render_template('search.html', active_page='search')

    @app.route('/community')
    def community():
        """社区页面"""
        return render_template('community.html', active_page='community')

    @app.route('/my-collections')
    def my_collections():
        """我的收藏"""
        return render_template('my_collections.html', active_page='my_collections')

    @app.route('/work-upload')
    def work_upload():
        """作品上传"""
        return render_template('work_upload.html', active_page='work_upload')

    @app.route('/work/<int:work_id>')
    def work_detail(work_id):
        """作品详情"""
        return render_template('work_detail.html', active_page='work_detail')

    @app.route('/review-center')
    def review_center():
        """审核中心"""
        return render_template('review_center.html', active_page='review_center')

    @app.route('/read-post')
    def read_post():
        """读帖页面"""
        return render_template('read_post.html', active_page='read_post')

    # ========== API 信息路由 ==========
    @app.route('/api')
    def api_info():
        """API 信息"""
        return jsonify({
            'message': 'iCalligraphy API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'works': '/api/works',
                'users': '/api/users',
                'comments': '/api/comments',
                'collections': '/api/collections'
            }
        })

    # 健康检查路由
    @app.route('/health')
    def health_check():
        """健康检查"""
        return jsonify({'status': 'healthy'}), 200

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '资源不存在'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500

    # JWT 错误处理 - 添加详细调试信息
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"[JWT ERROR] Token 已过期: {jwt_header}, {jwt_payload}")
        return jsonify({'error': 'Token 已过期'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"[JWT ERROR] 无效的 Token: {str(error)}")
        return jsonify({'error': f'无效的 Token: {str(error)}'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"[JWT ERROR] 缺少 Token: {str(error)}")
        return jsonify({'error': f'缺少 Token: {str(error)}'}), 401
    
    # 额外的JWT验证钩子用于调试
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        print(f"[JWT DEBUG] 检查token是否在黑名单: {jwt_payload['jti']}")
        return False
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        print(f"[JWT DEBUG] 设置用户身份: {user}")
        return user
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        print(f"[JWT DEBUG] 查找用户身份: {identity}")
        return User.query.get(identity) if identity else None

    # 创建数据库表
    with app.app_context():
        db.create_all()
        # admin = User(
        #     id=1,
        #     username='admin',
        #     email='admin@icalligraphy.com',
        #     bio='系统管理员',
        #     # phone='admin'
        # )
        # admin.set_password('admin123')

        # test_user = User(
        #     id=2,
        #     username='testuser',
        #     email='test@example.com',
        #     bio='测试用户，喜欢书法艺术',
        #     # phone='test'
        # )
        # test_user.set_password('test123')

        # if( not User.query.filter_by(username='admin').first()):
        #     db.session.add(admin)
        # if( not User.query.filter_by(username='testuser').first()):
        #     db.session.add(test_user)
        # db.session.commit()
        # print(db.session.query(User).all())
    return app


if __name__ == '__main__':
    # 获取环境变量
    env = os.getenv('FLASK_ENV', 'development')
    app = create_app(env)

    # 运行应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        # debug=(env == 'development')
        
    )

# iCalligraphy Backend API

智能书法学习平台后端 API，基于 Flask + SQLAlchemy + SQLite。

## 技术栈 
 
 - **Web 框架**: Flask 3.0.0 
 - **ORM**: SQLAlchemy 2.0.23+ 
 - **数据库**: SQLite 
 - **认证**: Flask-JWT-Extended 
 - **跨域**: Flask-CORS 
 - **密码加密**: Werkzeug 
 - **图像处理**: Pillow 
 - **AI 集成**: 豆包 API

## 项目结构

```
Backend/
├── app.py              # 主应用入口
├── config.py           # 配置文件
├── models.py           # 数据库模型
├── utils.py            # 工具函数
├── init_db.py          # 数据库初始化脚本
├── requirements.txt    # Python 依赖
├── .env.example        # 环境变量示例
├── .gitignore         # Git 忽略文件
├── routes/            # API 路由 
 │   ├── __init__.py 
 │   ├── auth.py        # 认证相关 
 │   ├── works.py       # 作品相关 
 │   ├── users.py       # 用户相关 
 │   ├── comments.py    # 评论相关 
 │   ├── collections.py # 收藏相关 
 │   ├── calligraphy.py # 书法相关 
 │   ├── posts.py       # 帖子相关 
 │   └── topics.py      # 话题相关
├── calligraphy_annotations/  # 书法注释数据
│   └── .gitkeep
├── json_temp/                # 临时JSON文件
├── Docs/                     # 项目文档

```

## 快速开始

### 1. 安装依赖

```bash
cd Backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URI=sqlite:///icalligraphy.db
```

### 3. 初始化数据库

```bash
python init_db.py
```

这将创建数据库表并插入测试数据：
- 管理员账号: `admin` / `admin123`
- 测试账号: `testuser` / `test123`

### 4. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## API 端点 
 
 ### 帖子相关 (`/api/posts`) 
 
 - `GET /api/posts` - 获取帖子列表 
 - `GET /api/posts/<post_id>` - 获取帖子详情 
 - `POST /api/posts` - 创建帖子（需认证） 
 - `PUT /api/posts/<post_id>` - 更新帖子（需认证） 
 - `DELETE /api/posts/<post_id>` - 删除帖子（需认证） 
 - `POST /api/posts/<post_id>/like` - 点赞帖子（需认证） 
 - `GET /api/posts/<post_id>/comments` - 获取帖子评论 
 
 ### 话题相关 (`/api/topics`) 
 
 - `GET /api/topics` - 获取所有话题列表 
 - `GET /api/topics/<topic_id>` - 获取单个话题详情 
 - `POST /api/topics/<topic_id>/follow` - 关注话题（需认证） 
 - `DELETE /api/topics/<topic_id>/follow` - 取消关注话题（需认证） 
 - `GET /api/users/<user_id>/following/topics` - 获取用户已关注的话题

### 书法相关 (`/api/calligraphy`)

- `GET /api/calligraphy/annotations` - 获取书法注释
- `POST /api/calligraphy/annotations` - 创建书法注释（需认证）
- `GET /api/calligraphy/styles` - 获取书法风格列表
- `POST /api/calligraphy/analyze` - 分析书法作品（需认证）

### 认证相关 (`/api/auth`)

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新 Token
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/logout` - 用户登出

### 用户相关 (`/api/users`)

- `GET /api/users/<user_id>` - 获取用户信息
- `GET /api/users/<user_id>/works` - 获取用户作品列表
- `PUT /api/users/profile` - 更新用户资料（需认证）
- `POST /api/users/avatar` - 上传头像（需认证）
- `PUT /api/users/password` - 修改密码（需认证）

### 作品相关 (`/api/works`)

- `GET /api/works` - 获取作品列表（支持分页、筛选、搜索）
- `GET /api/works/<work_id>` - 获取作品详情
- `POST /api/works` - 创建作品（需认证）
- `PUT /api/works/<work_id>` - 更新作品（需认证）
- `DELETE /api/works/<work_id>` - 删除作品（需认证）
- `POST /api/works/<work_id>/like` - 点赞作品（需认证）
- `DELETE /api/works/<work_id>/like` - 取消点赞（需认证）

### 评论相关 (`/api/comments`)

- `POST /api/comments` - 创建评论（需认证）
- `GET /api/comments/work/<work_id>` - 获取作品评论列表
- `PUT /api/comments/<comment_id>` - 更新评论（需认证）
- `DELETE /api/comments/<comment_id>` - 删除评论（需认证）

### 收藏相关 (`/api/collections`)

- `GET /api/collections` - 获取当前用户收藏列表（需认证）
- `POST /api/collections` - 添加收藏（需认证）
- `DELETE /api/collections/<work_id>` - 取消收藏（需认证）
- `GET /api/collections/check/<work_id>` - 检查是否已收藏（需认证）

## 数据模型 
 
 ### User（用户） 
 - id, username, email, password_hash 
 - avatar, bio 
 - created_at, updated_at 
 
 ### Work（作品） 
 - id, title, description, image_url 
 - style（书法风格）, author_id, views 
 - status（审核状态） 
 - created_at, updated_at 
 
 ### Comment（评论） 
 - id, content, work_id, author_id 
 - parent_id（父评论，用于回复） 
 - created_at 
 
 ### Collection（收藏） 
 - id, user_id, work_id 
 - created_at 
 
 ### Like（点赞） 
 - id, user_id, work_id 
 - created_at 
 
 ### Post（社区帖子） 
 - id, title, content, author_id 
 - created_at, updated_at 
 
 ### PostLike（帖子点赞） 
 - id, user_id, post_id 
 - created_at 
 
 ### PostComment（帖子评论） 
 - id, content, post_id, author_id 
 - parent_id（父评论，用于回复） 
 - created_at 
 
 ### Checkin（每日打卡） 
 - id, user_id, checkin_date 
 - created_at 
 
 ### Follow（关注关系） 
 - id, follower_id, followed_id 
 - created_at 
 
 ### Topic（话题） 
 - id, name, description 
 - post_count, today_posts, color, icon 
 - is_popular, created_at 
 
 ### FollowTopic（关注话题） 
 - id, user_id, topic_id 
 - created_at

## 认证机制

使用 JWT (JSON Web Token) 进行认证：

1. 登录后获取 `access_token` 和 `refresh_token`
2. 在请求头中添加：`Authorization: Bearer <access_token>`
3. Token 过期后使用 `refresh_token` 刷新

## 开发注意事项 
 
 1. **文件处理**: 
    - 书法注释数据存储在 `calligraphy_annotations/` 目录 
    - 临时 JSON 文件（如 OCR 结果）存储在 `json_temp/` 目录 
    - 上传的作品图片和头像存储在动态创建的 `uploads/` 目录 
 2. **前端集成**: 后端直接集成了前端路由，前端文件位于项目根目录的 `Frontend-HTML/` 目录 
 3. **分页**: 默认每页 12 条数据，可通过 `page` 和 `per_page` 参数调整 
 4. **CORS**: 支持跨域请求，具体配置可在 `config.py` 中修改 
 5. **数据库**: 
    - 使用 SQLite，数据文件为 `icalligraphy.db` 
    - 启动时会自动检查数据库连接和表结构，若缺失则自动执行初始化 
 6. **AI 功能**: 集成了 OpenAI API 用于书法作品分析

## 测试

可以使用 Postman 或 curl 测试 API：

```bash
# 注册用户
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","email":"new@example.com","password":"password123"}'

# 登录
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取作品列表
curl http://localhost:5000/api/works
```

## License

MIT

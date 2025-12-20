# iCalligraphy Backend API

智能书法学习平台后端 API，基于 Flask + SQLAlchemy + SQLite。

## 技术栈

- **Web 框架**: Flask 3.0.0 
- **ORM**: SQLAlchemy 2.0.25+ 
- **数据库**: SQLite 
- **认证**: Flask-JWT-Extended 4.6.0 
- **跨域**: Flask-CORS 4.0.0 
- **密码加密**: Werkzeug 3.0.1 
- **图像处理**: Pillow 10.4.0 
- **AI 集成**: 豆包 API 
- **环境变量**: python-dotenv 1.0.0 
- **HTTP 请求**: requests 2.32.3
- **实时通信**: Flask-SocketIO 5.3.6, python-socketio 5.10.0, python-engineio>=4.8.0
  - 异步模式: threading

## 项目结构

```
Backend/
├── app.py                  # 主应用入口
├── config.py               # 配置文件
├── models.py               # 数据库模型
├── utils.py                # 工具函数
├── init_db.py              # 数据库初始化脚本
├── requirements.txt        # Python 依赖
├── LICENSE                 # 许可证文件
├── test_topic_features.py  # 话题功能测试脚本
├── .env.example            # 环境变量示例
├── .env                    # 环境变量（运行时创建）
├── .gitignore              # Git 忽略文件
├── README.md               # 项目说明文档
├── instance/               # 数据库文件目录
│   └── icalligraphy.db     # SQLite 数据库文件
├── routes/                 # API 路由 
│   ├── __init__.py 
│   ├── auth.py             # 认证相关 
│   ├── works.py            # 作品相关 
│   ├── users.py            # 用户相关 
│   ├── comments.py         # 评论相关 
│   ├── collections.py      # 收藏相关 
│   ├── calligraphy.py      # 书法相关 
│   ├── posts.py            # 帖子相关 
│   ├── topics.py           # 话题相关
│   ├── character_sets.py   # 字集相关
│   ├── notifications.py    # 通知相关
├── calligraphy_annotations/  # 书法注释数据
│   ├── .gitkeep
│   └── *annotation_*.json    # 注释数据文件
├── json_temp/                # 临时 JSON 文件
│   └── ocr_*.json            # OCR结果文件
├── Docs/                     # 项目文档
│   └── 读帖功能使用说明.md   # 功能说明文档
├── uploads/                  # 上传文件目录（应用运行时动态创建）
│   ├── works/               # 作品图片目录
│   └── avatars/             # 用户头像目录

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
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# 古籍OCR API配置
Token="your-ocr-token-here"
Email="your-email-here"

# 豆包大模型 API 配置
ARK_API_KEY="your-ark-api-key-here"
ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
ARK_VISION_MODEL="doubao-1.5-vision-pro-32k-250115"
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

应用将在 `http://0.0.0.0:5000` 启动，支持外部访问。

## API 端点 
 
### 帖子相关 (`/api/posts`) 

 - `GET /api/posts` - 获取帖子列表 
 - `POST /api/posts` - 创建帖子 
 - `GET /api/posts/<post_id>` - 获取帖子详情 
 - `DELETE /api/posts/<post_id>` - 删除帖子（需认证） 
 - `POST /api/posts/<post_id>/like` - 点赞帖子（需认证） 
 - `POST /api/posts/<post_id>/comments` - 创建帖子评论（需认证） 
 - `DELETE /api/comments/<comment_id>` - 删除帖子评论（需认证）

### 每日打卡相关 (`/api/checkin`)

 - `POST /api/checkin` - 每日打卡（需认证） 
 - `GET /api/checkin/status` - 检查今日打卡状态（需认证） 
 
### 话题相关 (`/api/topics`) 
 
 - `GET /api/topics` - 获取所有话题列表 
 - `GET /api/topics/<topic_id>` - 获取单个话题详情 
 - `POST /api/topics/<topic_id>/follow` - 关注话题（需认证） 
 - `DELETE /api/topics/<topic_id>/follow` - 取消关注话题（需认证） 
 - `GET /api/users/<user_id>/following/topics` - 获取用户已关注的话题
 - `GET /api/users/me/following/topics` - 获取当前用户已关注的话题

### 书法相关 (`/api/calligraphy`)

- `GET /api/calligraphy/annotations` - 获取书法注释列表（支持分页、排序）
- `POST /api/calligraphy/annotations` - 创建书法注释（需认证）
- `GET /api/calligraphy/annotations/<id>` - 获取单个书法注释详情
- `PUT /api/calligraphy/annotations/<id>` - 更新书法注释（需认证且为创建者）
- `DELETE /api/calligraphy/annotations/<id>` - 删除书法注释（需认证且为创建者）
- `POST /api/calligraphy/analyze` - 分析书法作品
- `POST /api/calligraphy/save` - 保存注释数据到数据库
- `GET /api/calligraphy/list` - 获取注释列表（兼容旧版API）
- `GET /api/calligraphy/load/<filename>` - 加载指定的注释文件（兼容旧版API）
- `GET /api/calligraphy/search` - 搜索书法作品和单字

### 认证相关 (`/api/auth`)

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新 Token
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/logout` - 用户登出

### 用户相关 (`/api/users`)

- `GET /api/users/<user_id>` - 获取用户信息
- `GET /api/users/<user_id>/works` - 获取用户作品列表
- `GET /api/users/<user_id>/following` - 获取用户关注列表
- `GET /api/users/<user_id>/followers` - 获取用户粉丝列表
- `GET /api/users/<user_id>/follow/status` - 检查是否关注用户（需认证）
- `POST /api/users/<user_id>/follow` - 关注用户（需认证）
- `DELETE /api/users/<user_id>/follow` - 取消关注用户（需认证）
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
- `GET /api/works/<work_id>/characters` - 获取作品字符列表
- `POST /api/works/<work_id>/characters` - 添加作品字符（需认证）
- `GET /api/works/characters/<character_id>` - 获取单个字符详情
- `PUT /api/works/characters/<character_id>` - 更新作品字符（需认证）
- `DELETE /api/works/characters/<character_id>` - 删除作品字符（需认证）
- `GET /api/works/config` - 获取作品上传的预配置信息
- `POST /api/works/ocr` - 调用OCR API进行识别，返回结果JSON并暂存

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

### 字集相关 (`/api/character-sets`)

- `GET /api/character-sets` - 获取用户字集列表（需认证）
- `POST /api/character-sets` - 创建新字集（需认证）
- `GET /api/character-sets/<set_id>` - 获取字集详情（需认证）
- `PUT /api/character-sets/<set_id>` - 更新字集信息（需认证）
- `DELETE /api/character-sets/<set_id>` - 删除字集（需认证）
- `GET /api/character-sets/<set_id>/characters` - 获取字集内单字列表（需认证）
- `POST /api/character-sets/<set_id>/characters` - 添加单字到字集（需认证）
- `DELETE /api/character-sets/<set_id>/characters/<char_id>` - 从字集移除单字（需认证）
- `POST /api/character-sets/<set_id>/characters/move` - 移动单字到其他字集（需认证）

### 通知相关 (`/api/notifications`)

- `GET /api/notifications` - 获取通知列表（需认证，支持分页和类型筛选）
- `GET /api/notifications/count` - 获取未读通知数量（需认证）
- `PUT /api/notifications/<notification_id>/read` - 标记单条通知为已读（需认证）
- `PUT /api/notifications/read-all` - 标记所有通知为已读（需认证）
- `DELETE /api/notifications/<notification_id>` - 删除单条通知（需认证）
- `DELETE /api/notifications` - 清空所有通知（需认证）
- `GET /api/notifications/stats` - 获取通知统计信息（需认证）

### 系统路由

- `GET /health` - 健康检查
- `GET /api` - API 信息

## 数据模型 
 
### User（用户）
- id, username, email, password_hash
- avatar, bio
- created_at, updated_at 
- followers（粉丝关系）
- following（关注关系） 

### Work（作品）
- id, title, description, image_url
- style（书法风格）, author_name（作品作者）, author_id, views
- source_type（来源类型）, tags（作品标签，JSON格式）
- status（审核状态）
- created_at, updated_at 

### Comment（评论，针对作品）
- id, content, work_id, author_id
- parent_id（父评论，用于回复）
- created_at 

### Collection（收藏）
- id, user_id, work_id
- created_at 

### Like（作品点赞）
- id, user_id, work_id 
- created_at 

### Post（社区帖子） 
- id, title, content, author_id 
- topic_id（关联话题，可选）
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

### Character（书法字符）
- id, work_id, style（书体）, strokes（笔画数量）
- stroke_order（笔顺）, recognition（识别结果）
- source（出自）, collected_at（采集时间）
- keypoints（关键点列表，JSON格式）
- x, y（单字在作品中的坐标）, width, height（单字尺寸）
- updated_at（更新时间）

### CharacterSet（字集）
- id, name（字集名称）, description（字集描述）
- user_id（创建者）, created_at, updated_at

### CharacterInSet（字集-单字关联）
- id, character_set_id（所属字集）, character_id（关联单字）
- added_at（添加时间）

### Notification（通知）
- id, user_id（接收通知的用户）, type（通知类型：like, comment, follow, mention, system）
- content（通知内容）, related_id（关联对象ID）, related_type（关联对象类型：post, comment, user等）
- is_read（是否已读）, created_at（创建时间）

## 认证机制

使用 JWT (JSON Web Token) 进行认证：

1. 登录后获取 `access_token` 和 `refresh_token`
2. 在请求头中添加：`Authorization: Bearer <access_token>`
3. Token 过期后使用 `refresh_token` 刷新

## 开发注意事项 
 
 1. **文件处理**: 
    - 书法注释数据存储在 `calligraphy_annotations/` 目录 
    - 临时 JSON 文件（如 OCR 结果）存储在 `json_temp/` 目录 
    - 上传的作品图片和头像存储在动态创建的 `uploads/` 目录（按作品和头像分类） 
 2. **前端集成**: 后端直接集成了前端路由，前端文件位于项目根目录的 `Frontend-HTML/` 目录 
 3. **实时通信**: 使用 Flask-SocketIO 实现实时通信功能，支持通知推送等实时交互 
 4. **分页**: 默认每页 12 条数据，可通过 `page` 和 `per_page` 参数调整 
 5. **CORS 配置**: 支持跨域请求，使用具体地址而非通配符，以支持 credentials，具体配置在 `config.py` 中修改，当前支持的域名包括：
    - http://localhost:5000 
    - http://127.0.0.1:5000 
    - http://10.234.242.47:5000 
 6. **Flask 应用工厂模式**: 采用应用工厂模式创建 Flask 应用，便于不同环境配置和测试 
 7. **数据库**: 
    - 使用 SQLite，数据文件为 `icalligraphy.db` 
    - 启动时会自动检查数据库连接和表结构，若缺失则自动执行初始化 
 8. **AI 功能**: 集成了豆包 API 用于书法作品分析，以及古籍 OCR API 用于文字识别 
 9. **健康检查**: 提供 `/health` 路由用于健康检查 
 10. **API 信息**: 提供 `/api` 路由用于查看 API 基本信息 
 11. **JWT 配置**: 
    - 访问令牌有效期 24 小时 
    - 刷新令牌有效期 30 天 
    - 使用 `flask_jwt_extended` 库实现 
    - 支持 Token 刷新机制 
 12. **自动数据库检查**: 应用启动时会自动检查数据库连接和表结构，若缺失则自动执行 `init_db.py` 初始化脚本

## AI 集成配置

### 1. 豆包 API 配置

智能书法学习平台集成了豆包 API 用于书法作品分析，需要在 `.env` 文件中配置以下参数：

- **ARK_API_KEY**: 豆包 API Key，从火山方舟平台获取
- **ARK_BASE_URL**: API Base URL，根据业务所在地域配置，默认值为 `https://ark.cn-beijing.volces.com/api/v3`
- **ARK_VISION_MODEL**: 视觉模型 ID，用于图像理解任务（书法笔迹分析等），默认值为 `doubao-1.5-vision-pro-32k-250115`

### 2. 古籍 OCR API 配置

平台集成了古籍 OCR API 用于文字识别，需要在 `.env` 文件中配置以下参数：

- **Token**: OCR API 的令牌
- **Email**: 注册 OCR API 时使用的邮箱

### 3. AI 功能使用

- **书法作品分析**: 通过 `/api/calligraphy/analyze` 端点调用豆包 API 进行书法作品分析
- **文字识别**: 通过 `/api/works/ocr` 端点调用古籍 OCR API 进行文字识别
- **AI 辅助学习**: 结合书法注释数据和 AI 分析结果，为用户提供个性化的学习建议

## 测试

可以使用 Postman 或 curl 测试 API：

```bash
# 注册用户
curl -X POST http://0.0.0.0:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","email":"new@example.com","password":"password123"}'

# 登录
curl -X POST http://0.0.0.0:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取作品列表
curl http://0.0.0.0:5000/api/works

# 创建书法注释（需要认证）
curl -X POST http://0.0.0.0:5000/api/calligraphy/annotations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"character": "测试", "keypoints": [{"id": 1, "description": "测试要点", "tips": "这是一个测试提示", "x": 0.5, "y": 0.5}]}'

# 获取书法注释列表
curl http://0.0.0.0:5000/api/calligraphy/annotations

# 获取单个书法注释
curl http://0.0.0.0:5000/api/calligraphy/annotations/<id>

# 更新书法注释（需要认证）
curl -X PUT http://0.0.0.0:5000/api/calligraphy/annotations/<id> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"character": "更新测试", "keypoints": [{"id": 1, "description": "更新后的要点", "tips": "这是更新后的测试提示", "x": 0.6, "y": 0.6}]}'

# 删除书法注释（需要认证）
curl -X DELETE http://0.0.0.0:5000/api/calligraphy/annotations/<id> \
  -H "Authorization: Bearer <access_token>"```

## License

查看 [LICENSE](LICENSE) 文件了解详细信息。

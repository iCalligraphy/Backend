# iCalligraphy Backend API

智能书法学习平台后端 API，基于 Flask + SQLAlchemy + SQLite。

## 技术栈

- **Web 框架**: Flask 3.0.0
- **ORM**: Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.25+ 
- **数据库**: SQLite 
- **认证**: Flask-JWT-Extended 4.6.0 
- **跨域**: Flask-CORS 4.0.0 
- **密码加密**: Werkzeug 3.0.1 
- **图像处理**: Pillow 10.4.0 
- **AI 集成**: 豆包 API, OpenAI API (openai>=1.0.0) 
- **环境变量**: python-dotenv 1.0.0 
- **HTTP 请求**: requests 2.32.3
- **实时通信**: Flask-SocketIO 5.3.6, python-socketio 5.10.0, python-engineio>=4.8.0, eventlet 0.33.3
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
├── .env                    # 环境变量（运行时创建，git忽略）
├── .gitignore              # Git 忽略文件
├── README.md               # 项目说明文档
├── icalligraphy.db         # SQLite 数据库文件（根目录，非instance目录）
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

- `POST /api/comments` - 创建作品评论（需认证）
- `GET /api/comments/work/<work_id>` - 获取作品评论列表
- `PUT /api/comments/<comment_id>` - 更新评论（需认证）
- `DELETE /api/comments/<comment_id>` - 删除评论（需认证）

### 收藏相关 (`/api/collections`)

- `GET /api/collections` - 获取当前用户收藏列表（需认证）
- `POST /api/collections` - 添加收藏（需认证）
- `DELETE /api/collections/<work_id>` - 取消收藏（需认证）
- `GET /api/collections/check/<work_id>` - 检查是否已收藏（需认证）

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
- `GET /api/calligraphy/hot-keywords` - 获取热门搜索词（支持limit和days参数）

### 帖子相关 (`/api/posts`) 

- `GET /api/posts` - 获取帖子列表（支持分页、话题筛选）
- `POST /api/posts` - 创建帖子（需认证）
- `GET /api/posts/<post_id>` - 获取帖子详情
- `DELETE /api/posts/<post_id>` - 删除帖子（需认证）
- `POST /api/posts/<post_id>/like` - 点赞帖子（需认证）
- `DELETE /api/posts/<post_id>/like` - 取消点赞帖子（需认证）
- `POST /api/posts/<post_id>/comments` - 创建帖子评论（需认证）

### 帖子评论相关

- `POST /api/posts/<post_id>/comments` - 创建帖子评论（需认证）
- `DELETE /api/post-comments/<comment_id>` - 删除帖子评论（需认证，仅作者可删除）

### 话题相关 (`/api/topics`) 

- `GET /api/topics` - 获取所有话题列表 
- `GET /api/topics/<topic_id>` - 获取单个话题详情 
- `POST /api/topics/<topic_id>/follow` - 关注话题（需认证） 
- `DELETE /api/topics/<topic_id>/follow` - 取消关注话题（需认证） 
- `GET /api/users/<user_id>/following/topics` - 获取用户已关注的话题
- `GET /api/users/me/following/topics` - 获取当前用户已关注的话题

### 每日打卡相关 (`/api/checkin`)

- `POST /api/checkin` - 每日打卡（需认证） 
- `GET /api/checkin/status` - 检查今日打卡状态（需认证） 

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
- `GET /uploads/<path:filename>` - 访问上传的文件（图片、头像等）

## 数据模型 
 
### User（用户）
- **基本字段**: id, username, email, password_hash
- **个人信息**: avatar, bio
- **时间戳**: created_at, updated_at 
- **关系**: 
  - followers（粉丝关系）
  - following（关注关系）
  - works（用户创建的作品）
  - comments（用户发表的评论）
  - collections（用户收藏的作品）
  - likes（用户点赞的作品）
  - posts（用户发表的帖子）
  - post_likes（用户点赞的帖子）
  - post_comments（用户发表的帖子评论）
  - character_sets（用户创建的字集）
  - notifications（用户的通知）

### Work（作品）
- **基本字段**: id, title, description, image_url
- **作品信息**: 
  - style（书法风格）, author_name（作品作者）, author_id
  - source_type（来源类型）, tags（作品标签，JSON格式）
  - views（浏览量）, status（审核状态，默认approved）
  - original_width, original_height（原始图片尺寸）
- **时间戳**: created_at, updated_at 
- **关系**: 
  - comments（作品评论）
  - collections（作品收藏）
  - likes（作品点赞）
  - characters（作品中的单字）

### Comment（评论，针对作品）
- **基本字段**: id, content, work_id, author_id
- **回复关系**: parent_id（父评论，用于回复）
- **时间戳**: created_at 
- **关系**: replies（子评论）

### Collection（收藏）
- **基本字段**: id, user_id, work_id
- **时间戳**: created_at 
- **唯一约束**: 一个用户不能重复收藏同一作品

### Like（作品点赞）
- **基本字段**: id, user_id, work_id 
- **时间戳**: created_at 
- **唯一约束**: 一个用户不能重复点赞同一作品

### Post（社区帖子） 
- **基本字段**: id, title, content, author_id 
- **话题关联**: topic_id（关联话题，必填）
- **时间戳**: created_at, updated_at 
- **关系**: 
  - likes（帖子点赞）
  - comments（帖子评论）
  - topic（所属话题）

### PostLike（帖子点赞）
- **基本字段**: id, user_id, post_id
- **时间戳**: created_at 
- **唯一约束**: 一个用户不能重复点赞同一帖子

### PostComment（帖子评论）
- **基本字段**: id, content, post_id, author_id 
- **回复关系**: parent_id（父评论，用于回复） 
- **时间戳**: created_at 
- **关系**: replies（子评论）

### Checkin（每日打卡）
- **基本字段**: id, user_id, checkin_date
- **时间戳**: created_at 
- **唯一约束**: 一个用户每天只能打卡一次

### Follow（关注关系）
- **基本字段**: id, follower_id, followed_id
- **时间戳**: created_at 
- **唯一约束**: 一个用户不能重复关注另一个用户
- **关系**: 
  - follower（关注者）
  - followed（被关注者）

### Topic（话题）
- **基本字段**: id（字符串ID，如'technique'）, name, description
- **话题信息**: 
  - post_count（帖子数量）, color（话题颜色）, icon（话题图标）
  - is_popular（是否热门）
- **时间戳**: created_at
- **关系**: 
  - posts（话题下的帖子）
  - followers（关注话题的用户）

### FollowTopic（关注话题）
- **基本字段**: id, user_id, topic_id
- **时间戳**: created_at
- **唯一约束**: 一个用户不能重复关注同一个话题

### Character（书法字符）
- **基本字段**: id, work_id
- **字符信息**: 
  - style（书体）, strokes（笔画数量）, stroke_order（笔顺）
  - recognition（识别结果）, source（出自）
  - keypoints（关键点列表，JSON格式）
- **坐标信息**: x, y（单字在作品中的坐标）, width, height（单字尺寸）
- **时间戳**: collected_at（采集时间）, updated_at（更新时间）
- **关系**: 
  - work（所属作品）
  - in_sets（所属字集，通过CharacterInSet关联）

### CharacterSet（字集）
- **基本字段**: id, name（字集名称）, description（字集描述）
- **创建者**: user_id
- **时间戳**: created_at, updated_at
- **唯一约束**: 一个用户的字集名称不能重复
- **关系**: characters（字集内的单字，通过CharacterInSet关联）

### CharacterInSet（字集-单字关联）
- **基本字段**: id, character_set_id（所属字集）, character_id（关联单字）
- **时间戳**: added_at（添加时间）
- **唯一约束**: 一个字集内不能重复添加同一个单字
- **关系**: 
  - character_set（所属字集）
  - character（关联单字）

### Notification（通知）
- **基本字段**: id, user_id（接收通知的用户）
- **通知信息**: 
  - type（通知类型：like, comment, follow, mention, system）
  - content（通知内容）
  - related_id（关联对象ID）, related_type（关联对象类型：post, comment, user等）
  - is_read（是否已读，默认false）
- **时间戳**: created_at（创建时间）
- **关系**: user（接收通知的用户）

### SearchLog（搜索记录）
- **基本字段**: id, keyword（搜索关键词）
- **用户关联**: user_id（可选，记录搜索用户）
- **时间戳**: created_at（搜索时间）
- **用途**: 统计热门搜索词，支持搜索推荐功能
- **关系**: user（搜索用户，可选）

## 认证机制

使用 JWT (JSON Web Token) 进行认证：

1. 登录后获取 `access_token` 和 `refresh_token`
2. 在请求头中添加：`Authorization: Bearer <access_token>`
3. Token 过期后使用 `refresh_token` 刷新

## 开发注意事项 
 
### 1. 文件处理 
- **书法注释数据**: 存储在 `calligraphy_annotations/` 目录，用于保存书法作品的注释信息
- **临时 JSON 文件**: 如 OCR 识别结果，存储在 `json_temp/` 目录，便于前端临时使用
- **上传文件**: 
  - 作品图片：`uploads/works/` 目录
  - 用户头像：`uploads/avatars/` 目录
  - 上传目录会在应用启动时自动创建
  - 通过 `/uploads/<path:filename>` 路由访问上传的文件

### 2. 前端集成 
- 后端直接集成了前端路由，前端文件位于项目根目录的 `Frontend-HTML/` 目录
- 支持直接访问前端页面，如：
  - 首页：`http://localhost:5000/`
  - 登录/注册：`http://localhost:5000/auth`
  - 个人主页：`http://localhost:5000/profile`
  - 社区页面：`http://localhost:5000/community`
  - 作品上传：`http://localhost:5000/work-upload`

### 3. 实时通信 
- 使用 Flask-SocketIO 实现实时通信功能，支持通知推送、实时消息等交互
- 异步模式：threading
- 主要事件：
  - `connect`/`disconnect`：客户端连接/断开
  - `join_room`/`leave_room`：加入/离开用户房间
  - `send_notification`：发送通知
  - `mark_notification_read`：标记通知已读
  - `delete_notification`：删除通知

### 4. 分页与排序 
- 默认每页 12 条数据，可通过 `page` 和 `per_page` 参数调整
- 支持通过 `sort_by` 和 `order` 参数进行排序
- 分页结果包含 `total`, `pages`, `current_page`, `per_page` 等元数据

### 5. CORS 配置 
- 支持跨域请求，使用具体地址而非通配符，以支持 credentials
- 具体配置在 `config.py` 中的 `CORS_ORIGINS` 列表中修改
- 当前支持的域名：
  - http://localhost:5000 
  - http://127.0.0.1:5000 
  - http://10.234.242.47:5000 

### 6. Flask 应用工厂模式 
- 采用应用工厂模式创建 Flask 应用，便于不同环境配置和测试
- 支持多种环境配置：development, production, testing
- 配置文件：`config.py`

### 7. 数据库配置 
- **数据库类型**: SQLite（默认）
- **数据库文件**: `icalligraphy.db`（位于项目根目录）
- **自动初始化**: 应用启动时会自动检查数据库连接和表结构，若缺失则自动执行 `init_db.py` 初始化脚本
- **表关系**: 采用 SQLAlchemy ORM 管理，支持复杂的表关系和查询
- **事务管理**: 使用 SQLAlchemy 的事务机制，确保数据一致性

### 8. AI 功能集成 
- **豆包 API**: 用于书法作品分析和智能学习建议
- **古籍 OCR API**: 用于书法作品中的文字识别
- **OpenAI API**: 用于增强 AI 功能（可选）
- **配置**: 所有 AI 相关配置均在 `.env` 文件中设置

### 9. 系统监控与健康检查 
- **健康检查**: 提供 `/health` 路由用于健康检查，返回系统状态
- **API 信息**: 提供 `/api` 路由用于查看 API 基本信息和可用端点
- **日志**: 支持详细的日志记录，便于调试和监控

### 10. JWT 认证配置 
- **访问令牌有效期**: 24 小时
- **刷新令牌有效期**: 30 天
- **实现库**: `flask_jwt_extended`
- **支持功能**: 
  - Token 刷新机制
  - Token 黑名单（预留）
  - 详细的错误处理和日志记录
  - 用户身份验证和授权

### 11. 测试与调试 
- **测试脚本**: 提供 `test_topic_features.py` 用于话题功能测试
- **调试模式**: 开发环境下自动启用调试模式，便于开发和调试
- **API 测试**: 可使用 Postman 或 curl 测试 API 端点

### 12. 环境变量配置 
- 所有敏感配置均通过环境变量设置
- 环境变量示例文件: `.env.example`
- 运行时创建 `.env` 文件，根据实际情况修改配置
- 主要环境变量：
  - `FLASK_APP`: Flask 应用入口
  - `FLASK_ENV`: 运行环境（development/production/testing）
  - `SECRET_KEY`: 应用密钥
  - `JWT_SECRET_KEY`: JWT 密钥
  - `DATABASE_URI`: 数据库连接 URI
  - `UPLOAD_FOLDER`: 上传文件目录
  - `ARK_API_KEY`: 豆包 API 密钥
  - `ARK_BASE_URL`: 豆包 API 基础 URL
  - `ARK_VISION_MODEL`: 豆包视觉模型 ID
  - `Token`: 古籍 OCR API 令牌
  - `Email`: 古籍 OCR API 邮箱

### 13. 安全考虑 
- **密码加密**: 使用 Werkzeug 的 `generate_password_hash` 进行密码加密，算法为 `pbkdf2:sha256`
- **文件上传安全**: 限制文件类型和大小，使用 `secure_filename` 处理文件名
- **CORS 安全**: 使用具体域名而非通配符，支持 credentials
- **JWT 安全**: 合理设置 Token 有效期，支持刷新机制
- **输入验证**: 所有 API 输入均经过严格验证，防止注入攻击

### 14. 部署注意事项 
- **生产环境**: 切换 `FLASK_ENV` 为 `production`
- **密钥管理**: 使用强密钥，定期更换
- **数据库备份**: 定期备份数据库文件
- **日志管理**: 配置适当的日志级别，定期清理日志
- **性能优化**: 考虑使用 Gunicorn 或 uWSGI 作为生产服务器
- **静态文件**: 考虑使用 CDN 或 Nginx 处理静态文件

### 15. 开发规范 
- 代码风格遵循 PEP 8 规范
- 使用 Flask 蓝图（Blueprint）组织 API 路由
- 数据库模型与业务逻辑分离
- 工具函数封装在 `utils.py` 中
- 配置与代码分离，支持多种环境配置

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

### 3. OpenAI API 配置（可选）

平台支持集成 OpenAI API 用于增强 AI 功能，需要在 `.env` 文件中配置以下参数：

- **OPENAI_API_KEY**: OpenAI API Key
- **OPENAI_API_BASE**: OpenAI API Base URL（可选，用于自定义端点）

### 4. AI 功能使用

- **书法作品分析**: 通过 `/api/calligraphy/analyze` 端点调用豆包 API 进行书法作品分析
- **文字识别**: 通过 `/api/works/ocr` 端点调用古籍 OCR API 进行文字识别
- **AI 辅助学习**: 结合书法注释数据和 AI 分析结果，为用户提供个性化的学习建议
- **智能搜索**: 利用 AI 技术实现更智能的书法作品和单字搜索
- **自动标注**: 利用 AI 技术辅助标注书法作品中的单字和关键点

### 5. AI 功能流程

#### 书法作品分析流程
1. 用户上传书法作品图片
2. 系统调用 `/api/works/ocr` 端点进行文字识别
3. 识别结果暂存到 `json_temp/` 目录
4. 用户进行单字标注和关键点标注
5. 系统调用 `/api/calligraphy/analyze` 端点进行 AI 分析
6. AI 返回分析结果，包括笔画点评、结构分析等
7. 结果保存到数据库，供用户查看和学习

#### 文字识别流程
1. 用户上传书法作品图片
2. 系统调用古籍 OCR API 进行文字识别
3. 识别结果以 JSON 格式返回并暂存
4. 前端根据识别结果生成单字标注界面
5. 用户可以手动调整和完善标注

### 6. AI 模型选择

根据不同的任务需求，可以选择不同的 AI 模型：

- **视觉分析**: 使用豆包视觉模型 `doubao-1.5-vision-pro-32k-250115`
- **文字识别**: 使用古籍 OCR API
- **自然语言处理**: 可选择豆包或 OpenAI 模型（根据具体需求）

### 7. AI 性能优化

- **请求缓存**: 对频繁调用的 AI 请求进行缓存，减少 API 调用次数
- **异步处理**: 对耗时的 AI 分析任务进行异步处理，提高系统响应速度
- **批量处理**: 支持批量上传和分析，提高处理效率
- **资源监控**: 监控 AI API 调用频率和资源使用情况，优化系统性能

### 8. AI 结果存储

- **临时结果**: 存储在 `json_temp/` 目录，格式为 JSON
- **永久结果**: 存储在数据库中，包括：
  - 书法注释数据（`calligraphy_annotations/` 目录）
  - 单字标注数据（`characters` 表）
  - AI 分析结果（关联到对应的作品和单字）

## 测试

可以使用 Postman 或 curl 测试 API。以下是一些常用 API 端点的测试示例：

### 1. 认证相关测试

```bash
# 注册用户
curl -X POST http://0.0.0.0:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","email":"new@example.com","password":"password123"}'

# 登录
curl -X POST http://0.0.0.0:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取当前用户信息（需要认证）
curl -X GET http://0.0.0.0:5000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### 2. 用户相关测试

```bash
# 获取用户信息
curl -X GET http://0.0.0.0:5000/api/users/1

# 更新用户资料（需要认证）
curl -X PUT http://0.0.0.0:5000/api/users/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"bio": "我是一名书法爱好者"}'

# 关注用户（需要认证）
curl -X POST http://0.0.0.0:5000/api/users/2/follow \
  -H "Authorization: Bearer <access_token>"

# 取消关注用户（需要认证）
curl -X DELETE http://0.0.0.0:5000/api/users/2/follow \
  -H "Authorization: Bearer <access_token>"
```

### 3. 作品相关测试

```bash
# 获取作品列表
curl -X GET http://0.0.0.0:5000/api/works

# 获取作品详情
curl -X GET http://0.0.0.0:5000/api/works/1

# 创建作品（需要认证，需要先获取访问令牌）
# 注意：实际创建作品需要上传图片，这里仅作示例
echo "创建作品需要上传图片，建议使用 Postman 测试"

# 点赞作品（需要认证）
curl -X POST http://0.0.0.0:5000/api/works/1/like \
  -H "Authorization: Bearer <access_token>"

# 取消点赞作品（需要认证）
curl -X DELETE http://0.0.0.0:5000/api/works/1/like \
  -H "Authorization: Bearer <access_token>"
```

### 4. 评论相关测试

```bash
# 获取作品评论列表
curl -X GET http://0.0.0.0:5000/api/comments/work/1

# 创建作品评论（需要认证）
curl -X POST http://0.0.0.0:5000/api/comments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"work_id": 1, "content": "这幅作品写得真好！"}'

# 更新评论（需要认证）
curl -X PUT http://0.0.0.0:5000/api/comments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"content": "更新后的评论内容"}'
```

### 5. 收藏相关测试

```bash
# 获取当前用户收藏列表（需要认证）
curl -X GET http://0.0.0.0:5000/api/collections \
  -H "Authorization: Bearer <access_token>"

# 添加收藏（需要认证）
curl -X POST http://0.0.0.0:5000/api/collections \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"work_id": 1}'

# 取消收藏（需要认证）
curl -X DELETE http://0.0.0.0:5000/api/collections/1 \
  -H "Authorization: Bearer <access_token>"

# 检查是否已收藏（需要认证）
curl -X GET http://0.0.0.0:5000/api/collections/check/1 \
  -H "Authorization: Bearer <access_token>"
```

### 6. 帖子相关测试

```bash
# 获取帖子列表
curl -X GET http://0.0.0.0:5000/api/posts

# 创建帖子（需要认证）
curl -X POST http://0.0.0.0:5000/api/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"title": "书法学习心得", "content": "学习书法需要持之以恒", "topic_id": "technique"}'

# 点赞帖子（需要认证）
curl -X POST http://0.0.0.0:5000/api/posts/1/like \
  -H "Authorization: Bearer <access_token>"
```

### 7. 书法相关测试

```bash
# 获取书法注释列表
curl -X GET http://0.0.0.0:5000/api/calligraphy/annotations

# 创建书法注释（需要认证）
curl -X POST http://0.0.0.0:5000/api/calligraphy/annotations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"character": "测试", "keypoints": [{"id": 1, "description": "测试要点", "tips": "这是一个测试提示", "x": 0.5, "y": 0.5}]}'

# 获取单个书法注释
curl -X GET http://0.0.0.0:5000/api/calligraphy/annotations/1
```

### 8. 字集相关测试

```bash
# 获取用户字集列表（需要认证）
curl -X GET http://0.0.0.0:5000/api/character-sets \
  -H "Authorization: Bearer <access_token>"

# 创建新字集（需要认证）
curl -X POST http://0.0.0.0:5000/api/character-sets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"name": "我的常用字集", "description": "我常用的书法单字"}'

# 获取字集详情（需要认证）
curl -X GET http://0.0.0.0:5000/api/character-sets/1 \
  -H "Authorization: Bearer <access_token>"
```

### 9. 通知相关测试

```bash
# 获取通知列表（需要认证）
curl -X GET http://0.0.0.0:5000/api/notifications \
  -H "Authorization: Bearer <access_token>"

# 获取未读通知数量（需要认证）
curl -X GET http://0.0.0.0:5000/api/notifications/count \
  -H "Authorization: Bearer <access_token>"

# 标记通知为已读（需要认证）
curl -X PUT http://0.0.0.0:5000/api/notifications/1/read \
  -H "Authorization: Bearer <access_token>"
```

### 10. 系统测试

```bash
# 健康检查
curl -X GET http://0.0.0.0:5000/health

# API 信息
curl -X GET http://0.0.0.0:5000/api
```

## License

查看 [LICENSE](LICENSE) 文件了解详细信息。

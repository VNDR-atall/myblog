# VNDR Blog

欢迎您来到VD的个人博客网站。`VNDR Blog` 是一个基于 Flask 的个人博客系统，支持游客浏览、用户注册登录、评论互动，以及管理员内容管理，正文使用 Markdown 存储并渲染。

## 功能概览

### 游客功能

- 文章列表：`/`
- 文章详情：`/post/<slug>`
- 文件夹分类浏览：`/folder/<folder_id>`

### 用户功能

- 注册：`/register`
- 登录：`/login`
- 个人管理：`/user/profile`
  - 修改用户名（7天内仅可修改一次）
  - 修改密码（7天内仅可修改一次）
  - 修改头像
  - 查看和删除自己的评论
  - 注销账号
- 评论功能：在文章详情页发表评论

### 管理员功能

- 登录/退出：`/admin/login`、`/logout`
- 新建文章：`/new`
- 编辑文章：`/edit/<slug>`
- 删除文章：`/delete/<slug>`
- 图片上传：在新建/编辑文章时上传图片

### Markdown 能力

- 代码高亮、表格、TOC、fenced code
- 支持 Obsidian 风格的任务列表：`- [ ] 待办事项`、`- [x] 已完成事项`
- 支持 Obsidian 风格的文本高亮：`==高亮文本==`
- 智能引号转换
- 自动换行转换

## 技术栈

- 后端框架：`Flask`
- 数据库：`SQLite` + `Flask-SQLAlchemy`
- 迁移扩展：`Flask-Migrate`（已接入扩展，当前未使用迁移目录）
- 表单支持：`Flask-WTF`（依赖已安装）
- Markdown：`markdown` + `Pygments`
- 生产 WSGI：`gunicorn`
- 容器化：`Docker` + `docker compose`

## 项目结构

```text
myblog/
├── app/
│   ├── __init__.py              # 应用工厂、扩展初始化、404/500 错误页处理
│   ├── routes.py                # 主要路由（浏览、登录、CRUD、上传）
│   ├── models.py                # Post、Folder、Comment 模型
│   ├── decorators.py            # admin_required 权限装饰器
│   ├── utils.py                 # Markdown 渲染、上传、slug 生成工具
│   ├── templates/               # 页面模板
│   └── static/images/           # 上传图片目录
│       └── avatars/             # 用户头像目录
├── content/posts/               # 文章正文（Markdown 文件）
├── config.py                    # 配置（数据库、管理员账号、上传目录等）
├── init_db.py                   # 初始化数据库表
├── init_test_db.py              # 初始化测试数据库（本地测试专用）
├── run.py                       # 本地开发入口
├── wsgi.py                      # Gunicorn 入口
├── Dockerfile
├── docker-compose.yml
├── start.sh                     # 启动脚本
└── requirements.txt
```

## 数据设计与内容存储

- 数据库表 `Post` 保存文章元数据：`title`、`slug`、`created_date`、`modified_date`、`summary`、`filename`、`folder_id`
- 数据库表 `Folder` 保存文件夹信息：`name`
- 数据库表 `Comment` 保存评论信息：`content`、`username`、`post_id`、`created_date`
- 文章正文不直接入库，而是存放在 `content/posts/<filename>.md`
- 创建文章时，后端会根据标题自动生成唯一 `slug` 与 `filename`
- 编辑文章时不会修改 `created_date`

## 一键启动脚本

项目根目录提供 `start.sh`，支持本地与 Docker 两种启动方式。

```bash
bash start.sh [local|docker|docker-detached|docker-down]
```

### `local`（默认）

```bash
bash start.sh
```

脚本会自动执行：

1. 创建虚拟环境（默认 `.venv`）
2. 安装依赖（`pip install -r requirements.txt`）
3. 创建必要目录（`content/posts`、`app/static/images`、`app/static/images/avatars`）
4. 初始化数据库（`python init_db.py`）
5. 启动开发服务（`python run.py`）

可选环境变量：

- `VENV_DIR`：虚拟环境目录（默认 `.venv`）
- `PYTHON_BIN`：Python 命令（默认 `python3`）

### `docker`

```bash
bash start.sh docker
```

前台启动（可实时看日志）。

### `docker-detached`

```bash
bash start.sh docker-detached
```

后台启动。

### `docker-down`

```bash
bash start.sh docker-down
```

停止容器服务。

## 手动启动（不使用脚本）

### 本地

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p content/posts app/static/images app/static/images/avatars
python init_db.py
python run.py
```

### 本地测试数据库

```bash
python init_test_db.py
```

测试数据库包含：

- 3个默认文件夹：欢迎、日常、项目
- 3篇测试文章
- 3条测试评论
- 2个测试用户：testuser1、testuser2

### Docker

```bash
docker compose up --build
```

访问：`http://localhost:5000`

## 管理员账号

默认管理员账号来自 `config.py`：

- `ADMIN_USERNAME=adminVD`
- `ADMIN_PASSWORD=@Wtdlxwsmlm329`

建议生产环境通过环境变量覆盖：

```bash
export ADMIN_USERNAME="your_admin"
export ADMIN_PASSWORD="strong_password"
```

## 用户注册与登录

- 注册时需要输入用户名、密码、确认密码
- 用户名长度限制：2-8个字符
- 密码长度限制：6-20个字符
- 注册时检测用户名是否与管理员账号冲突
- 注册成功后自动登录
- 登录时若账户不存在，会提示并提供注册链接

## 头像上传说明

- 用户注册和个人管理页面均可上传头像
- 支持格式：`jpg`、`png`
- 大小限制：2MB
- 未上传头像时显示默认头像（用户名首字母）

## 图片上传说明

- 上传接口：`POST /upload`（管理员权限）
- 前端页面（`/new`、`/edit/<slug>`）已集成上传按钮
- 成功后返回 `{ "location": "/static/images/<filename>" }`
- 编辑器会自动插入 `![image](...)`

允许上传扩展名：`png`、`jpg`、`jpeg`、`gif`、`svg`

## 评论功能

- 只有登录用户才能发表评论
- 评论字数限制：2-100字
- 评论显示用户头像、用户名、评论内容和时间
- 用户可以在个人管理页面查看和删除自己的评论

## 线上部署建议（公网）

在云服务器与域名可用后，推荐：

1. 使用 `gunicorn + nginx`（或仅 gunicorn + 反向代理）
2. 配置 HTTPS（Let's Encrypt）
3. 将 `SECRET_KEY`、管理员密码改为强随机值
4. 为 `content/posts`、`app/static/images` 做定期备份
5. 观察应用日志，重点关注 4xx/5xx 与上传失败场景

## 已知注意事项

- Markdown 渲染结果使用 `|safe` 输出，若面向公网建议引入 HTML 清洗策略
- 当前数据库为 SQLite，单机场景可用；并发写入较高时建议迁移至 MySQL/PostgreSQL
- 测试数据库 `test.db` 已添加到 `.gitignore`，不会被 git 推送


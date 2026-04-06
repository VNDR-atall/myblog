# VNDR Blog

Hello everyone! Welcome to VD's personal blog website.

`VNDR Blog` 是一个基于 Flask 的个人博客系统，支持游客浏览与管理员内容管理，正文使用 Markdown 存储并渲染。

## 功能概览

- 游客只读访问：
  - 文章列表：`/`
  - 文章详情：`/post/<slug>`
- 管理员写操作：
  - 登录/退出：`/login`、`/logout`
  - 新建文章：`/new`
  - 编辑文章：`/edit/<slug>`
  - 删除文章：`/delete/<slug>`
- Markdown 能力：
  - 代码高亮、表格、TOC、fenced code
  - 在新建/编辑页可上传图片并自动插入 Markdown 图片语法

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
│   ├── models.py                # Post 模型
│   ├── decorators.py            # admin_required 权限装饰器
│   ├── utils.py                 # Markdown 渲染、上传、slug 生成工具
│   ├── templates/               # 页面模板
│   └── static/images/           # 上传图片目录
├── content/posts/               # 文章正文（Markdown 文件）
├── config.py                    # 配置（数据库、管理员账号、上传目录等）
├── init_db.py                   # 初始化数据库表
├── run.py                       # 本地开发入口
├── wsgi.py                      # Gunicorn 入口
├── Dockerfile
├── docker-compose.yml
├── start.sh                     # 启动脚本（本次新增）
└── requirements.txt
```

## 数据设计与内容存储

- 数据库表 `Post` 保存元数据：`title`、`slug`、`created_date`、`modified_date`、`tags`、`summary`、`filename`
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
3. 创建必要目录（`content/posts`、`app/static/images`）
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
mkdir -p content/posts app/static/images
python init_db.py
python run.py
```

### Docker

```bash
docker compose up --build
```

访问：`http://localhost:5000`

## 管理员账号

默认管理员账号来自 `config.py`：

- `ADMIN_USERNAME=admin`
- `ADMIN_PASSWORD=admin`

建议生产环境通过环境变量覆盖：

```bash
export ADMIN_USERNAME="your_admin"
export ADMIN_PASSWORD="strong_password"
```

## 图片上传说明

- 上传接口：`POST /upload`（管理员权限）
- 前端页面（`/new`、`/edit/<slug>`）已集成上传按钮
- 成功后返回 `{ "location": "/static/images/<filename>" }`
- 编辑器会自动插入 `![image](...)`

允许上传扩展名：`png`、`jpg`、`jpeg`、`gif`、`svg`

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


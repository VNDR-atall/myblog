# MyBlog

一个轻量级的个人博客 Web 项目（Flask），支持：

- **文章列表** / **文章详情**
- **新建文章**：把 Markdown 内容保存到文件系统，同时把文章元数据写入 SQLite
- **图片上传**：将图片保存到 `app/static/images/`，并返回可直接插入到编辑器/Markdown 的 URL
- **Markdown 渲染**：支持代码高亮、TOC、表格等扩展

---

### 技术栈

- **后端**：`Flask`
- **ORM/数据库**：`Flask-SQLAlchemy` + **SQLite**
- **迁移（已依赖但当前未配置迁移目录）**：`Flask-Migrate`
- **表单（已依赖但当前未实现登录/编辑权限）**：`Flask-WTF`
- **Markdown 渲染**：`markdown` + `Pygments`（代码高亮）
- **容器化（可选）**：`Dockerfile` + `docker-compose.yml`

---

### 整体结构 & 数据流（核心设计）

本项目采用一种“**文件存正文、数据库存元数据**”的方式：

- `app/models.py` 定义了 `Post` 模型，字段包含：
  - `title`、`slug`（作为 URL 标识，唯一）
  - `tags`、`summary`
  - `filename`：对应正文文件名（默认保存为 `f"{slug}.md"`）
- 文章正文保存到文件系统目录：
  - `content/posts/`
  - 文件名来自 `Post.filename`
- 访问文章时（`/post/<slug>`）：
  1. 先用 `slug` 从 SQLite 找到 `Post`
  2. 再读取 `content/posts/<filename>`
  3. 用 `app/utils.py` 的 `render_markdown()` 渲染为 HTML，并在 `post.html` 中展示

---

### 目录结构（以实际代码为准）

```text
myblog/
├── app/
│   ├── __init__.py            # 应用工厂 create_app + 扩展初始化
│   ├── routes.py              # Blueprint 路由：/、/post/<slug>、/new、/upload
│   ├── models.py              # Post 数据模型（SQLite）
│   ├── utils.py               # Markdown 渲染与图片上传保存
│   ├── forms.py               # （当前为空）预留
│   ├── decorators.py         # （当前为空）预留
│   ├── templates/            # Jinja2 模板（base/index/post/edit/login）
│   └── static/
│       └── images/           # 上传图片目录（gitkeep 用于保留目录）
├── config.py                  # 环境变量配置项（SECRET_KEY、DATABASE_URL 等）
├── run.py                     # 开发环境启动入口
├── init_db.py                 # 初始化数据库：db.create_all()
├── requirements.txt
├── app.db                     # SQLite 数据库（可能被忽略/按需生成）
├── content/
│   └── posts/                # **正文目录：当前仓库中可能尚未创建**
├── Dockerfile
└── docker-compose.yml
```

---

### 配置项（环境变量）

`config.py` 提供以下默认值（都可用环境变量覆盖）：

- `SECRET_KEY`：Flask 密钥（默认是一个硬编码的字符串；生产环境建议设置）
- `DATABASE_URL`：数据库连接串
  - 默认：`sqlite:////<项目根目录>/app.db`
- 文章目录与上传目录（来自代码，不单独暴露为环境变量）：
  - `POSTS_FOLDER = <项目根目录>/content/posts`
  - `UPLOAD_FOLDER = <项目根目录>/app/static/images`

---

### 本地开发/运行

#### 1) 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2) 准备目录

当前代码会把 Markdown 写入并读取 `content/posts`。如果该目录不存在，需要先创建：

```bash
mkdir -p content/posts
```

`app/static/images` 目录已在仓库中保留（通过 `app/static/images/.gitkeep`）。

#### 3) 初始化数据库

```bash
python init_db.py
```

该命令会创建 SQLite 表（`app.db`）。

#### 4) 启动服务（开发模式）

```bash
python run.py
```

打开浏览器访问：

- `http://localhost:5000/`：文章列表
- `http://localhost:5000/new`：新建文章（保存 Markdown 到 `content/posts`，并写入数据库）
- `http://localhost:5000/post/<slug>`：文章详情

---

### 图片上传接口

- 路由：`POST /upload`
- 请求：`multipart/form-data`
  - 字段名：`file`
- 返回：
  - 成功：`{"location": "/static/images/<filename>"}`（供 Markdown/编辑器使用）

图片允许扩展名来自 `Config.ALLOWED_EXTENSIONS`：`png/jpg/jpeg/gif/svg`

---

### 管理员登录与权限

目前采用**单固定管理员账号**（无多用户注册）。

- 管理员可进行写操作：`/new`（新建文章）、`/upload`（上传图片）
- 访客默认只读：`/`、`/post/<slug>`

管理员账号由 `config.py` 的环境变量控制：

- `ADMIN_USERNAME`（默认：`admin`）
- `ADMIN_PASSWORD`（默认：`admin`）

---

### Docker / docker-compose（可选）

```bash
docker compose up --build
```

- 端口：`5000:5000`
- 代码挂载：`.:/app`（容器内会实时看到本地变更）

**注意（当前仓库状态）**：`Dockerfile` 使用 `gunicorn wsgi:app`，但本项目的 `wsgi.py` 当前为空。
如果你要在 Docker 中启动生产模式，请先补全 `wsgi.py` 的 WSGI 入口（示例可以参考 `run.py` 中的 `create_app()` 用法）。

---

### 当前已知限制 / 后续可增强

- `login.html`、`forms.py`、`decorators.py` 目前是“预留/空实现”，**没有登录与权限控制**。
- `/new` 只负责“新建文章”，目前没有“编辑/删除文章”的专门路由。
- Markdown 渲染结果使用了 `{{ content|safe }}`，对内容的安全净化策略未在代码中体现；如果要上线到公网，建议加入 XSS 防护（例如对 HTML 进行清洗/限制）。

---

如果你希望我继续增强 README 的“编辑/更新文章、登录权限、生产部署（gunicorn/wsgi）”的说明，我也可以基于现有代码给出一步到位的实现建议。


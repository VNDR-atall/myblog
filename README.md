# MyBlog Project

by VNDR

2026.03.10 start

## Project Structure

```
myblog/
├── app/                        # 应用核心模块
│   ├── static/                 # 静态文件 (CSS, JS, 上传图片等)
│   │   ├── css/
│   │   ├── js/
│   │   ├── images/             # 用户上传的图片存放处
│   │   └── uploads/            # 其他上传文件（可选）
│   ├── templates/              # Jinja2 HTML 模板
│   │   ├── base.html
│   │   ├── index.html          # 文章列表页
│   │   ├── post.html           # 单篇文章详情页
│   │   ├── edit.html           # 新建/编辑文章页
│   │   └── login.html          # 登录页（后续添加）
│   ├── __init__.py             # 初始化 Flask 应用
│   ├── routes.py               # 路由定义（首页、文章、编辑、上传等）
│   ├── models.py               # 数据库模型（文章元数据）
│   ├── forms.py                # WTForms 表单类（登录、文章编辑）
│   ├── utils.py                # 工具函数（Markdown 渲染、文件处理等）
│   └── decorators.py           # 装饰器（如登录验证）
├── content/                    # 存放 Markdown 文章文件
│   └── posts/                  # 按日期或分类组织（可选）
├── migrations/                  # 数据库迁移脚本（Flask-Migrate）
├── logs/                        # 日志文件（可选）
├── config.py                    # 配置文件（环境变量、数据库 URI 等）
├── run.py                       # 应用启动入口（开发环境）
├── requirements.txt             # Python 依赖列表
├── .gitignore                   # Git 忽略文件
├── README.md                    # 项目说明
└── wsgi.py                      # 生产环境 WSGI 入口（Gunicorn 使用）
```

---


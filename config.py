import os

# 获取当前文件所在目录的绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    # SQLite 数据库文件路径
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文章 Markdown 文件存放目录
    POSTS_FOLDER = os.path.join(basedir, 'content/posts')
    # 上传图片存放目录
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/images')
    # 允许上传的文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

    # 固定管理员账号（仅单用户）
    # 生产/对外部署建议通过环境变量覆盖，避免明文默认值
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'adminVD'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or '@Wtdlxwsmlm329'

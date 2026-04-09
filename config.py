import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """基础配置（所有环境共用）"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
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


class DevelopmentConfig(Config):
    """开发环境配置（本地测试）"""
    DEBUG = True
    # 使用独立的测试数据库，放在 instance/test.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'test.db')


class ProductionConfig(Config):
    """生产环境配置（云服务器）"""
    DEBUG = False
    # 使用正式数据库，放在 instance/app.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')


# 配置字典，方便通过 FLASK_ENV 选择
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
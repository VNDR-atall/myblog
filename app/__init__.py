import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    """应用工厂函数，支持通过环境变量 FLASK_ENV 选择配置"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    app = Flask(__name__)
    # 根据配置名称加载对应类
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图
    from app import routes
    app.register_blueprint(routes.bp)

    # 错误处理
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", message="页面未找到（可能是文章已删除或 slug 不存在）"), 404

    @app.errorhandler(500)
    def internal_error(_e):
        app.logger.exception("Unhandled internal server error")
        return render_template("error.html", message="服务器内部错误，请稍后再试。"), 500

    return app

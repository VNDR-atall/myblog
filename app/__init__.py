from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展与 app
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图（此处使用临时路由，后续可拆分）
    from app import routes
    app.register_blueprint(routes.bp)

    return app

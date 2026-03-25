from flask import Flask, render_template
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

    @app.errorhandler(404)
    def not_found(_e):
        # 避免“偶发找不到正文文件”时展示 500
        return render_template("error.html", message="页面未找到（可能是文章已删除或 slug 不存在）"), 404

    @app.errorhandler(500)
    def internal_error(_e):
        # production 下把堆栈写入日志，前端给友好提示
        app.logger.exception("Unhandled internal server error")
        return render_template("error.html", message="服务器内部错误，请稍后再试。"), 500

    return app

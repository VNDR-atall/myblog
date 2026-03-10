from app import db
from datetime import datetime

class Post(db.Model):
    """文章元数据模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)          # 标题
    slug = db.Column(db.String(100), unique=True, nullable=False)  # URL 标识
    created_date = db.Column(db.DateTime, default=datetime.utcnow) # 创建日期
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = db.Column(db.String(200))                            # 标签（逗号分隔）
    summary = db.Column(db.Text)                                # 摘要
    filename = db.Column(db.String(200))                        # 对应的 Markdown 文件名

    def __repr__(self):
        return f'<Post {self.title}>'

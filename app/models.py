from app import db
from datetime import datetime

class Folder(db.Model):
    """文件夹模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # 文件夹名称
    posts = db.relationship('Post', backref='folder', lazy=True)  # 关联的文章

    def __repr__(self):
        return f'<Folder {self.name}>'

class Post(db.Model):
    """文章元数据模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)          # 标题
    slug = db.Column(db.String(100), unique=True, nullable=False)  # URL 标识
    created_date = db.Column(db.DateTime, default=datetime.utcnow) # 创建日期
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    summary = db.Column(db.Text)                                # 摘要
    filename = db.Column(db.String(200))                        # 对应的 Markdown 文件名
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)  # 关联的文件夹
    comments = db.relationship('Comment', backref='post', lazy=True)  # 关联的评论

    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    """评论模型"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)              # 评论内容
    created_date = db.Column(db.DateTime, default=datetime.utcnow) # 评论日期
    username = db.Column(db.String(50), nullable=False)       # 评论用户名
    avatar = db.Column(db.String(200), nullable=True)          # 评论用户头像
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)  # 关联的文章

    def __repr__(self):
        return f'<Comment {self.id} by {self.username}>'

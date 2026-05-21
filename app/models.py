from app import db
from datetime import datetime

class Folder(db.Model):
    """文件夹模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 文件夹名称
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)  # 父文件夹ID
    created_date = db.Column(db.DateTime, default=datetime.utcnow)  # 创建日期
    is_all_folder = db.Column(db.Boolean, default=False)  # 是否是"全部"文件夹
    
    # 自引用关系
    parent = db.relationship('Folder', remote_side=[id], backref=db.backref('children', lazy=True))
    posts = db.relationship('Post', backref='folder', lazy=True)  # 关联的文章

    def __repr__(self):
        return f'<Folder {self.name}>'
    
    def get_path(self):
        """获取文件夹路径"""
        path = []
        current = self
        while current and not current.is_all_folder:
            path.insert(0, current.name)
            current = current.parent
        return '/'.join(path) if path else '无'

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
    
    def get_location(self):
        """获取文章归属路径"""
        if self.folder:
            return self.folder.get_path()
        return '无'

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

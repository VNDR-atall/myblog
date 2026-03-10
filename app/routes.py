from flask import Blueprint, render_template, request, redirect, url_for, current_app, send_from_directory
from app import db
from app.models import Post
from app.utils import render_markdown, save_uploaded_file
import os

# 创建蓝图
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """首页：显示文章列表（从数据库获取）"""
    posts = Post.query.order_by(Post.created_date.desc()).all()
    return render_template('index.html', posts=posts)

@bp.route('/post/<slug>')
def post(slug):
    """单篇文章详情页"""
    post_meta = Post.query.filter_by(slug=slug).first_or_404()
    # 读取对应的 Markdown 文件
    filepath = os.path.join(current_app.config['POSTS_FOLDER'], post_meta.filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    html_content = render_markdown(content)
    return render_template('post.html', post=post_meta, content=html_content)

@bp.route('/new', methods=['GET', 'POST'])
def new_post():
    """新建文章（暂时未加登录验证）"""
    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        tags = request.form['tags']
        summary = request.form['summary']
        content = request.form['content']

        # 保存 Markdown 文件
        filename = f"{slug}.md"
        filepath = os.path.join(current_app.config['POSTS_FOLDER'], filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # 保存元数据到数据库
        post = Post(title=title, slug=slug, tags=tags, summary=summary, filename=filename)
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('main.post', slug=slug))

    return render_template('edit.html')

@bp.route('/upload', methods=['POST'])
def upload_image():
    """处理图片上传，返回图片 URL（供编辑器使用）"""
    if 'file' not in request.files:
        return 'No file', 400
    file = request.files['file']
    url = save_uploaded_file(file)
    if url:
        return {'location': url}   # 一些编辑器期望 JSON 格式
    return 'Upload failed', 400

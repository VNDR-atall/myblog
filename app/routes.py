from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, send_from_directory, abort
from app import db
from app.models import Post
from app.utils import render_markdown, save_uploaded_file, slugify
from app.decorators import admin_required
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
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        # 数据库存在但正文文件缺失：避免 500，直接 404
        abort(404)
    html_content = render_markdown(content)
    return render_template('post.html', post=post_meta, content=html_content)

@bp.route('/new', methods=['GET', 'POST'])
@admin_required
def new_post():
    """新建文章（管理员可用；自动生成 URL slug）"""
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        tags = (request.form.get('tags') or '').strip()
        summary = (request.form.get('summary') or '').strip()
        content = request.form.get('content') or ''

        if not title:
            return render_template('edit.html', error="标题不能为空。", post=None, content=content), 400
        if not content.strip():
            return render_template('edit.html', error="内容不能为空。", post=None, content=content), 400

        # 由标题生成 slug，并保证“数据库记录 + 正文文件”都不会冲突，
        # 从而避免由于竞态导致的 internal server error。
        base_slug = slugify(title)
        slug = base_slug
        idx = 1
        while True:
            filename = f"{slug}.md"
            filepath = os.path.join(current_app.config['POSTS_FOLDER'], filename)
            exists_in_db = Post.query.filter_by(slug=slug).first() is not None
            exists_on_disk = os.path.exists(filepath)
            if not exists_in_db and not exists_on_disk:
                break
            idx += 1
            slug = f"{base_slug}-{idx}"

        post = Post(title=title, slug=slug, tags=tags, summary=summary, filename=filename)

        tmp_filepath = f"{filepath}.tmp"
        try:
            # 先写文件（原子替换），再落库；这样避免“库有记录但文件缺失”造成的 500。
            os.makedirs(current_app.config['POSTS_FOLDER'], exist_ok=True)
            with open(tmp_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            os.replace(tmp_filepath, filepath)

            db.session.add(post)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # 最佳努力清理临时文件/可能写入的正文文件
            try:
                if os.path.exists(tmp_filepath):
                    os.remove(tmp_filepath)
            except Exception:
                pass
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass

            return (
                render_template(
                    'edit.html',
                    error=f"保存失败：{type(e).__name__}",
                    post=None,
                    content=content,
                ),
                400,
            )

        return redirect(url_for('main.post', slug=slug))

    return render_template('edit.html')

@bp.route('/upload', methods=['POST'])
@admin_required
def upload_image():
    """处理图片上传，返回图片 URL（供编辑器使用）"""
    if 'file' not in request.files:
        return 'No file', 400
    file = request.files['file']
    url = save_uploaded_file(file)
    if url:
        return {'location': url}   # 一些编辑器期望 JSON 格式
    return 'Upload failed', 400


@bp.route('/edit/<slug>', methods=['GET', 'POST'])
@admin_required
def edit_post(slug):
    """编辑已有文章（不改变 created_date，仅更新内容与元数据）"""
    post_meta = Post.query.filter_by(slug=slug).first_or_404()

    if request.method == 'POST':
        # slug 不可变：永远以 URL 中的 slug 为准
        title = request.form.get('title', '').strip()
        tags = request.form.get('tags', '').strip()
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '')

        # 1) 更新数据库元数据（不触碰 created_date）
        post_meta.title = title
        post_meta.tags = tags
        post_meta.summary = summary

        filename = post_meta.filename or f"{post_meta.slug}.md"
        filepath = os.path.join(current_app.config['POSTS_FOLDER'], filename)

        try:
            # 先写文件（原子替换），再提交，避免正文被中途截断导致偶发 500。
            os.makedirs(current_app.config['POSTS_FOLDER'], exist_ok=True)
            tmp_filepath = f"{filepath}.tmp"
            with open(tmp_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            os.replace(tmp_filepath, filepath)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return (
                render_template(
                    'edit.html',
                    post=post_meta,
                    content=content,
                    error=f"保存失败：{type(e).__name__}",
                ),
                400,
            )

        return redirect(url_for('main.post', slug=post_meta.slug))

    # GET：读取并回填 Markdown 内容
    filename = post_meta.filename or f"{post_meta.slug}.md"
    filepath = os.path.join(current_app.config['POSTS_FOLDER'], filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        abort(404)

    return render_template('edit.html', post=post_meta, content=content)


@bp.route('/delete/<slug>', methods=['POST'])
@admin_required
def delete_post(slug):
    """删除文章（删除数据库记录 + Markdown 文件）"""
    post_meta = Post.query.filter_by(slug=slug).first_or_404()

    filename = post_meta.filename or f"{post_meta.slug}.md"
    filepath = os.path.join(current_app.config['POSTS_FOLDER'], filename)

    # 先删文件（不存在也不影响）
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass

    try:
        db.session.delete(post_meta)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return redirect(url_for('main.index'))

    return redirect(url_for('main.index'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录（单用户固定账号）"""
    error = None
    if request.method == 'POST':
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            username == current_app.config["ADMIN_USERNAME"]
            and password == current_app.config["ADMIN_PASSWORD"]
        ):
            session["admin_authenticated"] = True
            next_url = request.args.get("next") or url_for("main.index")
            # 防止开放式跳转：只允许跳站内路径
            if not (isinstance(next_url, str) and next_url.startswith("/")):
                next_url = url_for("main.index")
            return redirect(next_url)

        error = "用户名或密码错误"

    return render_template("login.html", error=error)


@bp.route('/logout')
def logout():
    """退出管理员登录"""
    session.pop("admin_authenticated", None)
    return redirect(url_for("main.index"))

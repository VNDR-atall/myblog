from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, send_from_directory, abort
from app import db
from app.models import Post, Folder, Comment
from app.utils import render_markdown, save_uploaded_file, slugify
from app.decorators import admin_required
import os
import time

# 创建蓝图
bp = Blueprint('main', __name__)

# 初始化默认文件夹
def init_default_folders():
    default_folders = ['欢迎', '日常', '项目']
    for folder_name in default_folders:
        folder = Folder.query.filter_by(name=folder_name).first()
        if not folder:
            folder = Folder(name=folder_name)
            db.session.add(folder)
    db.session.commit()

@bp.route('/')
def index():
    """首页：显示文章列表（从数据库获取）"""
    # 初始化默认文件夹
    init_default_folders()
    
    # 获取文件夹参数
    folder_id = request.args.get('folder')
    
    # 根据文件夹筛选文章
    if folder_id:
        posts = Post.query.filter_by(folder_id=folder_id).order_by(Post.created_date.desc()).all()
    else:
        posts = Post.query.order_by(Post.created_date.desc()).all()
    
    # 获取所有文件夹
    folders = Folder.query.all()
    
    return render_template('index.html', posts=posts, folders=folders, current_folder_id=folder_id)

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
    # 获取所有文件夹
    folders = Folder.query.all()
    
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        folder_id = request.form.get('folder_id')
        summary = (request.form.get('summary') or '').strip()
        content = request.form.get('content') or ''

        if not title:
            return render_template('edit.html', error="标题不能为空。", post=None, content=content, folders=folders), 400
        if not content.strip():
            return render_template('edit.html', error="内容不能为空。", post=None, content=content, folders=folders), 400

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

        post = Post(title=title, slug=slug, summary=summary, filename=filename, folder_id=folder_id)

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

    return render_template('edit.html', folders=folders)

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
    # 获取所有文件夹
    folders = Folder.query.all()

    if request.method == 'POST':
        # slug 不可变：永远以 URL 中的 slug 为准
        title = request.form.get('title', '').strip()
        folder_id = request.form.get('folder_id')
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '')

        # 1) 更新数据库元数据（不触碰 created_date）
        post_meta.title = title
        post_meta.folder_id = folder_id
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
                    folders=folders,
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

    return render_template('edit.html', post=post_meta, content=content, folders=folders)


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

@bp.route('/post/<slug>/comment', methods=['POST'])
def add_comment(slug):
    """添加评论"""
    if not session.get('user_authenticated'):
        return redirect(url_for('main.login'))
    
    post = Post.query.filter_by(slug=slug).first_or_404()
    content = request.form.get('content', '').strip()
    
    # 验证评论长度
    if len(content) < 2 or len(content) > 100:
        return redirect(url_for('main.post', slug=slug))
    
    # 创建评论
    comment = Comment(
        content=content,
        username=session.get('username'),
        avatar=session.get('avatar'),
        post_id=post.id
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    return redirect(url_for('main.post', slug=slug))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    # 确保用户登录时，管理员会话已清除
    session.pop("admin_authenticated", None)
    
    error = None
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # 检查是否为管理员账号（防止用户使用管理员账号登录）
        if username == current_app.config["ADMIN_USERNAME"]:
            error = "请使用管理员登录入口"
        elif username and password:
            # 模拟用户数据库，实际应从数据库查询
            # 这里使用一个简单的字典来模拟用户数据库
            # 实际项目中应从数据库验证
            # 假设只有注册过的用户才能登录
            # 从session中获取已注册用户列表
            registered_users = session.get('registered_users', [])
            if username in registered_users:
                session["user_authenticated"] = True
                session["username"] = username
                next_url = request.args.get("next") or url_for("main.index")
                if not (isinstance(next_url, str) and next_url.startswith("/")):
                    next_url = url_for("main.index")
                return redirect(next_url)
            else:
                error = "账户不存在，是否注册？"
        else:
            error = "账户不存在，是否注册？"

    return render_template("login.html", error=error)

@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录"""
    # 确保管理员登录时，用户会话已清除
    session.pop("user_authenticated", None)
    session.pop("username", None)
    
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
            if not (isinstance(next_url, str) and next_url.startswith("/")):
                next_url = url_for("main.index")
            return redirect(next_url)

        error = "管理员用户名或密码错误"

    return render_template("admin_login.html", error=error)


@bp.route('/logout')
def logout():
    """退出登录"""
    session.pop("admin_authenticated", None)
    session.pop("user_authenticated", None)
    session.pop("username", None)
    session.pop("avatar", None)
    return redirect(url_for("main.index"))

@bp.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    """用户个人管理页面"""
    if not session.get('user_authenticated'):
        return redirect(url_for('main.login'))
    
    error = None
    success = None
    
    if request.method == 'POST':
        # 处理头像上传
        avatar = request.files.get('avatar')
        if avatar:
            # 检查文件类型
            if not avatar.filename.lower().endswith(('.jpg', '.png')):
                error = "头像文件格式必须为.jpg或.png"
            else:
                # 检查文件大小（限制为2MB）
                if len(avatar.read()) > 2 * 1024 * 1024:
                    error = "头像文件大小不能超过2MB"
                else:
                    # 重置文件指针
                    avatar.seek(0)
                    # 生成唯一文件名
                    avatar_filename = f"avatar_{session.get('username')}_{int(time.time())}.{avatar.filename.split('.')[-1]}"
                    # 保存头像
                    avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
                    os.makedirs(avatar_path, exist_ok=True)
                    avatar.save(os.path.join(avatar_path, avatar_filename))
                    # 更新会话中的头像信息
                    session["avatar"] = avatar_filename
                    success = "头像修改成功"
    
    return render_template('user_profile.html', error=error, success=success)

@bp.route('/user/comments')
def user_comments():
    """用户评论管理页面"""
    if not session.get('user_authenticated'):
        return redirect(url_for('main.login'))
    
    # 模拟评论数据
    comments = [
        {
            'id': 1,
            'post_title': '测试文章1',
            'content': '这是一条测试评论',
            'created_at': '2026-04-01 12:00:00'
        },
        {
            'id': 2,
            'post_title': '测试文章2',
            'content': '这是另一条测试评论',
            'created_at': '2026-04-02 14:30:00'
        }
    ]
    
    return render_template('user_comments.html', comments=comments)

@bp.route('/user/delete-account')
def delete_account():
    """注销账号"""
    if not session.get('user_authenticated'):
        return redirect(url_for('main.login'))
    
    # 清除用户会话
    session.pop("user_authenticated", None)
    session.pop("username", None)
    session.pop("avatar", None)
    
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册功能"""
    error = None
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        avatar = request.files.get('avatar')

        # 验证用户名长度
        if len(username) < 2 or len(username) > 8:
            error = "用户名长度应在2-8个字符之间"
        # 验证密码长度
        elif len(password) < 6 or len(password) > 20:
            error = "密码长度应在6-20个字符之间"
        # 验证密码是否一致
        elif password != confirm_password:
            error = "两次输入的密码不一致"
        # 验证用户名是否与管理员账号冲突
        elif username == current_app.config["ADMIN_USERNAME"]:
            error = "该用户名已被使用，请更换"
        else:
            # 检查用户名是否已存在（模拟数据库检查）
            # 实际项目中应从数据库查询
            # 这里简化处理，假设所有非管理员用户名都不存在
            # 处理头像上传
            avatar_filename = None
            if avatar:
                # 检查文件类型
                if not avatar.filename.lower().endswith(('.jpg', '.png')):
                    error = "头像文件格式必须为.jpg或.png"
                else:
                    # 检查文件大小（限制为2MB）
                    if len(avatar.read()) > 2 * 1024 * 1024:
                        error = "头像文件大小不能超过2MB"
                    else:
                        # 重置文件指针
                        avatar.seek(0)
                        # 生成唯一文件名
                        avatar_filename = f"avatar_{username}_{int(time.time())}.{avatar.filename.split('.')[-1]}"
                        # 保存头像
                        avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
                        os.makedirs(avatar_path, exist_ok=True)
                        avatar.save(os.path.join(avatar_path, avatar_filename))
            
            if not error:
                # 注册成功，将用户添加到已注册用户列表
                registered_users = session.get('registered_users', [])
                if username not in registered_users:
                    registered_users.append(username)
                    session['registered_users'] = registered_users
                # 自动登录
                session["user_authenticated"] = True
                session["username"] = username
                session["avatar"] = avatar_filename
                return redirect(url_for("main.index"))

    return render_template("register.html", error=error)

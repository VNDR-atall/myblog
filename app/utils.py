import os
import re
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from werkzeug.utils import secure_filename
from flask import current_app

def render_markdown(content):
    """将 Markdown 文本转换为 HTML，支持代码高亮和表格"""
    extensions = [
        CodeHiliteExtension(linenums=False),
        FencedCodeExtension(),
        TableExtension(),
        TocExtension(),
        'markdown.extensions.extra'   # 包含脚注、缩写等
    ]
    return markdown.markdown(content, extensions=extensions)

def allowed_file(filename):
    """检查文件扩展名是否允许上传"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file):
    """保存上传的图片，返回相对 URL 路径"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 避免重名，可添加时间戳或 uuid
        from datetime import datetime
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f'/static/images/{filename}'
    return None


def slugify(text: str) -> str:
    """把标题转换为 URL slug（用于文章路由/文件名）。"""
    text = (text or "").strip().lower()
    # 把非字母数字替换为连字符，再折叠重复连字符
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "post"

from functools import wraps

from flask import current_app, jsonify, redirect, request, session, url_for


def admin_required(view_func):
    """限制写操作，仅允许管理员访问。

    - 未登录：重定向到登录页（`next` 回跳）
    - 针对图片上传等非浏览器请求：返回 401 JSON
    """

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if session.get("admin_authenticated") is True:
            return view_func(*args, **kwargs)

        next_url = request.args.get("next") or request.path
        # 防止开放式重定向：只允许回到站内相对路径
        if not (isinstance(next_url, str) and next_url.startswith("/")):
            next_url = url_for("main.index")

        if request.path == "/upload":
            return jsonify({"error": "unauthorized"}), 401

        return redirect(url_for("main.login", next=next_url))

    return wrapped

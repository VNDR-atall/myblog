#!/usr/bin/env python
"""初始化数据库脚本"""
from app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ 数据库表创建成功！文件：app.db")

#!/usr/bin/env python3
"""
测试数据库初始化脚本
创建本地测试专用的SQLite数据库，包含测试数据
"""

import os
import sys
from app import create_app, db
from app.models import Post, Folder, Comment
from datetime import datetime

# 创建测试应用实例
app = create_app()

# 激活应用上下文
with app.app_context():
    # 删除旧的测试数据库
    test_db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test.db')
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("删除旧的测试数据库")
    
    # 创建所有表
    db.create_all()
    print("创建数据库表结构")
    
    # 创建默认文件夹
    folder_names = ["欢迎", "日常", "项目"]
    for folder_name in folder_names:
        # 检查文件夹是否已存在
        existing_folder = Folder.query.filter_by(name=folder_name).first()
        if not existing_folder:
            folder = Folder(name=folder_name)
            db.session.add(folder)
    
    # 创建测试文章
    posts = [
        Post(
            title="欢迎来到我的博客",
            slug="welcome-to-my-blog",
            summary="这是我的第一篇博客文章，欢迎大家访问！",
            filename="welcome-to-my-blog.md",
            folder_id=1
        ),
        Post(
            title="日常记录",
            slug="daily-record",
            summary="记录日常生活中的点点滴滴",
            filename="daily-record.md",
            folder_id=2
        ),
        Post(
            title="项目开发笔记",
            slug="project-notes",
            summary="项目开发过程中的技术笔记",
            filename="project-notes.md",
            folder_id=3
        )
    ]
    for post in posts:
        db.session.add(post)
    
    # 创建测试评论
    comments = [
        Comment(
            content="这篇文章写得真好！",
            username="testuser1",
            post_id=1
        ),
        Comment(
            content="感谢分享！",
            username="testuser2",
            post_id=1
        ),
        Comment(
            content="期待更多内容！",
            username="testuser1",
            post_id=2
        )
    ]
    for comment in comments:
        db.session.add(comment)
    
    # 提交所有更改
    db.session.commit()
    print("测试数据创建完成")
    print(f"测试数据库已创建：{test_db_path}")
    print("测试用户：testuser1, testuser2")
    print("测试文章：3篇")
    print("测试评论：3条")

print("测试数据库初始化完成！")
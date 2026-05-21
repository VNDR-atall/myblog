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
    
    # 创建"全部"文件夹
    all_folder = Folder(name="全部", is_all_folder=True)
    db.session.add(all_folder)
    
    # 创建默认文件夹
    folder1 = Folder(name="技术笔记")
    folder2 = Folder(name="日常记录")
    folder3 = Folder(name="项目文档")
    
    # 创建嵌套文件夹
    folder3_1 = Folder(name="设计文档", parent=folder3)
    folder3_2 = Folder(name="开发文档", parent=folder3)
    
    db.session.add(folder1)
    db.session.add(folder2)
    db.session.add(folder3)
    db.session.add(folder3_1)
    db.session.add(folder3_2)
    
    # 创建测试文章
    post1 = Post(
        title="Flask入门教程",
        slug="flask-introduction",
        summary="介绍Flask框架的基本使用",
        filename="flask-introduction.md",
        folder=folder1
    )
    
    post2 = Post(
        title="今天天气真好",
        slug="nice-weather",
        summary="记录今天的天气和心情",
        filename="nice-weather.md",
        folder=folder2
    )
    
    post3 = Post(
        title="项目架构设计",
        slug="project-architecture",
        summary="项目的整体架构设计文档",
        filename="project-architecture.md",
        folder=folder3_1
    )
    
    post4 = Post(
        title="开发规范",
        slug="development-standards",
        summary="团队开发规范文档",
        filename="development-standards.md",
        folder=folder3_2
    )
    
    post5 = Post(
        title="无分类文章",
        slug="uncategorized-post",
        summary="没有分类的文章",
        filename="uncategorized-post.md"
    )
    
    db.session.add(post1)
    db.session.add(post2)
    db.session.add(post3)
    db.session.add(post4)
    db.session.add(post5)
    
    # 创建测试评论
    comment1 = Comment(
        content="写得太好了！学到了很多",
        username="testuser1",
        post=post1
    )
    
    comment2 = Comment(
        content="期待更多内容",
        username="testuser2",
        post=post1
    )
    
    comment3 = Comment(
        content="记录得很详细",
        username="testuser1",
        post=post2
    )
    
    db.session.add(comment1)
    db.session.add(comment2)
    db.session.add(comment3)
    
    # 提交所有更改
    db.session.commit()
    print("测试数据创建完成")
    print("测试数据库已创建：test.db")
    print("\n测试文件夹结构：")
    print("  - 全部")
    print("    - 技术笔记")
    print("    - 日常记录")
    print("    - 项目文档")
    print("      - 设计文档")
    print("      - 开发文档")
    print("\n测试文章：5篇")
    print("测试评论：3条")

print("\n测试数据库初始化完成！")
print("\n使用测试数据库的方法：")
print("1. 修改 config.py 中的 DATABASE = 'test.db'")
print("2. 或者设置环境变量 export DATABASE=test.db")

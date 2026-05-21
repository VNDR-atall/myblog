#!/usr/bin/env python3
"""
数据库初始化脚本
"""

from app import create_app, db
from app.models import Folder
import os
import shutil

def init_database():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 检查是否已经存在"全部"文件夹
        all_folder = Folder.query.filter_by(is_all_folder=True).first()
        
        if not all_folder:
            # 创建"全部"文件夹
            all_folder = Folder(
                name="全部",
                is_all_folder=True
            )
            db.session.add(all_folder)
            db.session.commit()
            print("创建'全部'文件夹成功！")
        else:
            print("'全部'文件夹已存在。")
        
        print("数据库初始化完成！")

if __name__ == '__main__':
    init_database()

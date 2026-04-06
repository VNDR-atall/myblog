## 一、更新博客内容（文章）

- **存储位置**：  
  - 正文 Markdown 文件：服务器上的 `/root/myblog/content/posts/`  
  - 元数据（标题、slug、标签等）：服务器上的 SQLite 数据库 `/root/myblog/instance/app.db`（或 `/root/myblog/app.db`，取决于配置）
- **更新方式**：  
  直接登录网站后台（`/login`），使用内置的“新建/编辑”功能。修改后立即生效，**无需任何额外操作**。  
  > 这是最方便的方式，适合日常写博客。

---

## 二、更新网站前端、美术、框架、功能（代码改动）

这些改动需要修改项目文件（`.py`, `.html`, `.css` 等）。标准流程如下：

### 1. 在本地（Ubuntu 或 Mac）修改代码
- 推荐使用 **Git 作为同步桥梁**：在 Ubuntu 上修改 → 提交 → 推送到 GitHub。  
- 另一台电脑（Mac）通过 `git pull` 同步，保持本地一致。  
- 本地测试：运行 `python run.py` 查看效果。

### 2. 推送到 GitHub
```bash
git add .
git commit -m "描述改动"
git push origin main   # 或 master
```

### 3. 在云服务器上拉取并生效
SSH 登录服务器，执行：
```bash
cd /root/myblog
git pull origin main
source venv/bin/activate
pip install -r requirements.txt   # 仅当依赖变化时
python init_db.py                 # 仅当数据库模型变化时（会补全表，不删数据）
systemctl restart myblog          # 重启 Gunicorn 使代码生效
systemctl reload nginx            # 如果改了 Nginx 配置
```

**注意**：  
- 如果只改了前端模板（HTML/CSS），重启 Gunicorn 即可。  
- 如果改了 `models.py`，需要运行 `python init_db.py` 来更新表结构（它会安全地添加新列，不会删除数据）。  
- 如果改了 Nginx 配置文件（`/etc/nginx/sites-available/myblog`），需单独 `systemctl reload nginx`。

---

## 三、关于 Ubuntu 和 Mac 之间的同步

您目前使用 GitHub 作为中央仓库，这是**最标准、最可靠**的方式。两台电脑分别 `git pull` 和 `git push` 即可。  
如果觉得手动操作麻烦，可以写一个简单的脚本，但通常没必要。**不需要**使用其他同步工具（如 syncthing），因为容易产生冲突。

---

## 四、关于 Docker 的引入

- **当前生产环境**：没有使用 Docker，而是直接运行 Gunicorn + Nginx。这完全没问题，稳定可靠。  
- **学习目的**：可以在本地用 Docker 运行项目，理解容器化。项目中的 `Dockerfile` 和 `docker-compose.yml` 已经配置好，进入项目目录执行 `docker-compose up` 即可。  
- **未来是否迁移到 Docker**：如果您希望简化部署（比如迁移到另一台服务器时），可以考虑用 Docker，但需要处理好数据持久化（将数据库和图片目录挂载到宿主机）。**不是必须的**，个人博客保持现状也很好。

---

## 五、总结：您需要记住的操作

| 场景 | 操作 |
|------|------|
| 写新文章 / 编辑文章 | 网站后台直接操作，无需其他步骤 |
| 修改代码（任何 .py/.html 等） | 本地改 → `git push` → 服务器 `git pull` → `systemctl restart myblog` |
| 修改 Nginx 配置 | 服务器上直接编辑 `/etc/nginx/sites-available/myblog` → `systemctl reload nginx` |
| 修改依赖（requirements.txt） | 本地改 → `git push` → 服务器 `git pull` → 重新 `pip install -r requirements.txt` → 重启 Gunicorn |
| 修改数据库模型（models.py） | 本地改 → `git push` → 服务器 `git pull` → 运行 `python init_db.py` → 重启 Gunicorn |

**建议**：在服务器上创建一个简单的更新脚本 `update.sh`，内容如下：
```bash
#!/bin/bash
cd /root/myblog
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
systemctl restart myblog
echo "Update completed."
```
之后每次只需运行 `bash update.sh` 即可。

这样，您就可以清晰、高效地维护您的博客了。如果还有任何疑问，欢迎继续交流。

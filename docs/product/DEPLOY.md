# Ubuntu 部署准备（尚未部署）

面向个人使用的轻量准备：Ubuntu 22.04、2 核 / 4GB、Python 3.10+、Flask、SQLite 与系统 FFmpeg。当前网页不含可自动运行的 ASR 或模型 worker；提交视频链接不代表课程已经完成转录或教材生成。字幕、听音与写作仍需要原版工具链和宿主 Agent 配合。本文件和 systemd 模板尚未在服务器执行验证。

## 安装与启动

以下步骤在未来选定的服务器执行，需要管理员权限；本阶段不连接服务器、不购买服务。将审核后的项目版本放到 `/opt/video2book`，使用虚拟环境安装仓库已有依赖，避免重复安装其他框架。

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv ffmpeg
sudo useradd --system --home /var/lib/video2book --shell /usr/sbin/nologin video2book
sudo install -d -o video2book -g video2book -m 0700 /var/lib/video2book
cd /opt/video2book
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip install -r deploy/requirements.txt
sudo install -o root -g root -m 0600 deploy/video2book.env.example /etc/video2book.env
sudoedit /etc/video2book.env
sudo install -o root -g root -m 0644 deploy/video2book.service /etc/systemd/system/video2book.service
sudo install -o root -g root -m 0644 deploy/video2book-worker.service /etc/systemd/system/video2book-worker.service
sudo systemctl daemon-reload
sudo systemctl enable --now video2book video2book-worker
sudo systemctl status video2book
sudo journalctl -u video2book -n 50 --no-pager
curl -I http://127.0.0.1:8000/
```

`/opt/video2book` 和虚拟环境必须可被服务用户读取，应用运行时只写 `/var/lib/video2book`。在启动前将 `BOOKSITE_PASSWORD` 换成独立密码；不要提交真实环境文件。应用首次启动会在数据目录生成私有会话密钥，应与数据库一起备份。密码变更后需要重启服务。

默认仅监听 `127.0.0.1:8000`，不开放公网端口。Windows 使用 SSH 隧道访问：

```powershell
ssh -N -L 8000:127.0.0.1:8000 用户名@服务器地址
```

打开 `http://127.0.0.1:8000`。关闭 Windows 或 SSH 隧道会中断访问，服务器上的 systemd 服务和已持久化教材不受影响。公网访问需另行配置 HTTPS 反向代理，属于后续部署工作。systemd 模板使用一个 Gunicorn worker、两个线程提供网页；CLI 内置 Flask 服务仅用于开发。任务 worker 是独立串行进程，网页重启不会自动删除任务。当前只有元数据/字幕 worker，没有自动写作 worker，不能承诺无人值守生成教材。

## 持久化、备份与磁盘

将数据库、上传媒体、任务工作区与生成教材统一保存到 `--data-dir /var/lib/video2book`，不要依赖容器临时目录或应用代码目录。备份应同时包含 SQLite、教材、逐字稿和状态文件；只备份数据库不能恢复教材正文。

最简单的一致性备份是在没有任务执行时暂停服务，备份整个数据目录后再启动。备份文件包含私人课程与账户状态，放在受限目录，定期复制到独立存储。

```bash
sudo install -d -m 0700 /var/backups/video2book
sudo systemctl stop video2book video2book-worker
sudo tar -C /var/lib -czf /var/backups/video2book/data-$(date +%Y%m%d-%H%M%S).tar.gz video2book
sudo systemctl start video2book video2book-worker
sudo du -sh /var/lib/video2book
df -h /var/lib/video2book
```

恢复前暂停服务，将归档恢复到 `/var/lib`，确认目录归属为 `video2book:video2book` 后启动，并检查教材及任务状态。升级前先备份，保留上一版本代码和依赖以便回退。

音视频通常占用最多空间。优先复用原版完成后音频回收功能；仅对确认完成且已有备份的任务清理源媒体与可重建临时文件。保留教材、逐字稿、计划和状态，不设置自动删除教材的定时任务。空间不足时暂停新增上传并检查失败任务的媒体，不用清空整个数据目录来解决。

## 发布前验收

核验服务账户权限、登录密码、回环监听、重启后的任务/教材持久化和一次备份恢复；再按原版 workflow 验证真实课程。服务启动成功、网页可访问与真正完成视频教材转换是不同的验收项。当前所有服务器启动、备份恢复和 Windows 关机后的持续运行均为“尚未验证”。

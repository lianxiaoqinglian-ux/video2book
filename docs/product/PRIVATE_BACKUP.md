# 私有教材备份与恢复

`tools/private_backup.py` 仅使用 Python 标准库，在本机创建私有 ZIP，并验证每份教材、图像、来源记录及 SQLite 快照的 SHA256。SQLite 使用在线 `Connection.backup()` API，不直接复制正在使用的数据库；快照使用 DELETE journal，恢复后无需原 WAL 文件。备份与恢复文件权限为 `0600`，新建目录为 `0700`。ZIP 本身未加密，请按课程正文的私密程度保存。

```bash
python tools/private_backup.py create output/first-textbook/readable output/private-backups/first-textbook-readable-20261013.zip
python tools/private_backup.py create output/website-data output/private-backups/website-data-20261013.zip
python tools/private_backup.py verify output/private-backups/first-textbook-readable-20261013.zip
python tools/private_backup.py restore output/private-backups/website-data-20261013.zip /tmp/restored-website-data
python tools/private_backup.py verify output/private-backups/website-data-20261013.zip /tmp/restored-website-data
```

目标 ZIP 不可已存在，也不能位于来源目录内。恢复目标必须不存在。工具拒绝来源、目标及包内的符号链接、重复成员、绝对路径、`..`、反斜线和驱动器路径。`verify` 校验包内每个文件，并拒绝清单以外或缺失的文件；提供恢复目录时也逐项验证恢复文件及额外文件。

工具只接收 Markdown、HTML、TXT、JSON、图像及 SQLite 文件；媒体、未知类型、SQLite WAL/SHM、`.env`、secret/token/cookie/credential/password 命名文件与常见凭据目录均排除。文本或数据库字节中出现已识别的私钥、凭据 JSON 字段、签名 URL 参数时整文件排除。排除情况写入包内 `backup-manifest.json`；请检查排除清单，确认必要教材未因过滤被跳过。过滤器识别常见秘密格式，不能识别任意编码或任意命名的秘密；仅对已检查的教材目录与网站数据目录运行，不要把任意个人目录作为来源。图片帧是教材资产，音视频不进入备份。

网站的 `secret.key` 不进入备份；恢复服务器需重新生成会话密钥并通过服务环境配置登录密码，旧会话失效。停止网站工作进程后备份，可进一步避免数据库快照与另行读取的教材文件之间发生业务更新；在线 SQLite 快照自身保持一致性，但整个目录不构成跨文件原子事务。

已验证的本机包：

- `output/private-backups/first-textbook-readable-20261013.zip`：4 个教材/图像/来源文件。
- `output/private-backups/website-data-20261013.zip`：4 个网站数据文件，排除 `secret.key`。
- 安全证据：`research/product/evidence/private-backup.json`，仅路径、数量、大小、哈希及验证结果，不含教材正文或秘密值。

这些包位于 Git 忽略的 `output/`，仅存在于当前云工作区。未上传、未部署到服务器，也不构成持久化保证。用户应下载到自己的安全存储，或保存在自己的私有服务器，并保留代码/部署说明与独立密码配置，才能可靠地在新云环境中重建。请勿将 ZIP、正文、媒体或凭据提交到公共 GitHub。

验证测试：`/workspace/.venvs/video2book/bin/python -m pytest website/test_backup.py -q`。

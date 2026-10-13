# 本地私人教材库

复用现有虚拟环境，不部署、不自动调用模型。需要 Flask、Markdown、bleach：`python -m pip install -r website/requirements.txt`。生产WSGI另用 `deploy/requirements.txt`。任务worker目前只针对Ubuntu/Linux（fcntl文件锁）。

密码通过环境变量 `BOOKSITE_PASSWORD` 注入，不写进 Git。启动：

```bash
/workspace/.venvs/video2book/bin/python -m website --data-dir /workspace/booksite-data --port 8765
```

默认监听 `127.0.0.1`。打开 `http://127.0.0.1:8765`，密码登录后提交规范 Bilibili 视频链接、查看任务历史、阅读和下载已导入的真实教材。新任务为 `queued`；重复同一规范链接复用原任务，保留 `?p=N` 分集参数。worker 获取元数据并尝试匿名中文字幕；有字幕为 `waiting_writer`，无字幕为 `waiting_input`，网络失败为 `failed`，不伪造教材。

导入已核验的真实教材：

```bash
/workspace/.venvs/video2book/bin/python -m website --data-dir /workspace/booksite-data import-book --title '课程名称' --source-url 'https://www.bilibili.com/video/BV14VqVBrEhc' --markdown /absolute/path/book.md --provenance '真实来源、处理方式及尚未验证项'
```

SQLite、私有 secret key、Markdown 存在 data-dir，保留该目录才能保留历史。重试保留产物并回到 `queued`；已缓存元数据与字幕不重复请求。本版不下载视频、不提供 ASR、不提供图像上传或公式 MathJax；原始 Markdown 下载保留公式。网页禁止外部图片请求。导入可选 `--assets-dir`，仅接收单张不超过5MB的 jpg/png，教材引用图片用相对 basename（如 `![图](chart.png)`），阅读页自动改为鉴权图片地址。所有导入及读取文件路径禁止符号链接。

所有任务页和下载需要登录，POST 检查 CSRF，Markdown 消毒。Flask 内置服务仅供本地验证，尚未提供公网生产部署。

验证：`/workspace/.venvs/video2book/bin/python -m pytest website/test_site.py -q`

单线程处理一项任务（默认单集上限30分钟）：

```bash
/workspace/.venvs/video2book/bin/python -m website --data-dir /workspace/booksite-data worker
```

持续处理可加 `--loop`。只复用原版 `BilibiliParser` / `fetch_episode_subtitle`，匿名字幕尝试1次，不读取私人Cookie。导入已提交任务可加 `--task-id <ID>`，来源必须与该任务完全一致。

任务中断后串行worker会恢复遗留processing；任务处理时重试/导入被拒绝以防重复或覆盖。缓存原子提交；损坏JSON会重取。不可信字幕留在waiting_input。网站写作worker尚未实现，`waiting_writer`需合法外部Worker/宿主沿原版learning写作后使用import-book交接。

每次worker结果追加到data-dir中的 `{task_id}_events.jsonl`，详细进程日志由systemd journal保存。当前不下载长视频媒体，也不自动删除教材；先按部署说明备份，日后媒体缓存只清理可重建文件。

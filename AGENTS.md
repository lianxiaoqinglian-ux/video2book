# video2book — Agent 入口

本仓库是一个跨 agent 的 **Agent Skill**（把 B 站、YouTube、抖音网课/本地音视频重构为教材长文、模块全书与思维导图笔记）。

**完整说明以 [`CLAUDE.md`](CLAUDE.md) 为准**（本文件只是同一份内容的通用入口，便于各平台自动加载）。

快速事实：

- 技能定义：`skills/video2book/SKILL.md`（唯一真源）
- 工具链（技能的依赖，必须一起安装）：`skills/video2book/src/` 与 `skills/video2book/scripts/`
- **安装单元 = `skills/video2book/` 整个目录**（其余 README/平台声明/LICENSE 无需安装）
- 各平台安装对照：`skills/video2book/references/install.md`
- CLI 场景手册（八个场景）：`skills/video2book/references/cli-cookbook.md`
- 运行前置：Python 3.10+、系统 `ffmpeg`、以及缺字幕块实际需要的 `read_audio` 或 `read_media` 听音通道之一
- 自检：`cd skills/video2book && python scripts/selfcheck.py`
- 容器根 `.git` 是 Codex 工作区标记，只允许保持为空；技能自检会拒绝含提交或 tracked 文件的根仓库。

## Codex Cloud 执行补充

- 优先复用 `/workspace/.venvs/video2book`：先检查 Python、依赖与 FFmpeg；依赖齐备时不重复安装。激活后使用原版 CLI、selfcheck、queue_tracker 和 v2b_dispatch；后者只打印载荷，真正派发由宿主完成。
- 每个云任务已隔离，使用现有 checkout；只有用户明确要求时才创建 Git worktree。研究报告和验证证据在独立工作分支保存。
- 简单任务直接执行；局部修改先跑相关 pytest，再运行原作者要求的 selfcheck；重大改动才做完整方案研究。只有具体缺失功能需要解决时才检索现成开源方案，不重复阅读无关资料或安装依赖。
- 记录命令、退出码和证据；同一检查通过后不无故重复。真实课程、作者既有产物与模拟测试分别标注；未读取原视频时不得宣称完整性、画面或时间戳已验收。
- 缺少指定听音通道时报告阻塞；不绕用另一套 ASR、不配置私人凭据。核心源码修改须遵守当前用户授权范围。

## 后续成果记录

- 用户要求每轮工作后将简短中文总结保存到 GitHub：更新 `research/product/README.md` 的当前状态，向 `research/product/WORKLOG.md` 追加本轮完成内容、实际验证、产物路径、阻塞和下一步；沿用工作分支，不直接修改 main。
- 总结区分实际完成、人工交接与尚未验证；只提交代码和安全证据，课程正文、完整逐字稿、媒体及凭据保持私有。聊天交付提供 GitHub 查看链接，明确是否已推送。

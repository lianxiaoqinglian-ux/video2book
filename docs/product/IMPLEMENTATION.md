# 本轮实现范围与当前交接

已实现：原版 learning 任务书＋原生子Agent生成真实归档逐字稿教材；私有 HTML/Markdown样本含一张真实截图及标注AI补充练习；Flask、SQLite、简单页面的登录、任务、历史、阅读、下载、重试；串行原版元数据/字幕worker。代码独立于原版核心和Skill。

已验证：真实P2链接提交、原版元数据读取、无字幕等待、人工导入本轮新教材、阅读/截图/下载；Gunicorn普通网页进程启动及持久化重启。原729＋初始14测试通过，审查修复后19项网站测试通过，selfcheck通过。证据在 research/product/evidence/。

未实现：网站自动模型写作、无字幕自动可靠听音；现有Codex CLI登录不能绕过云代理对chatgpt.com的403。独立74MB/14M ASR试验质量不合格，未接入原版。完整自动端到端、长课、完整视觉信息及逐句时间戳未完成，服务器未部署。

交接接口：worker写入 `{task_id}_metadata.json` 与可信字幕 `{task_id}_transcript.json`，设 waiting_writer；合法外部Worker/宿主按原版learning工作流写作和验收，再通过 `import-book --task-id ... --provenance ...` 原子提交教材及可选图片。当前不接受任意网页shell命令。未来worker可以复用此文件边界，而无需新增编排框架。CLI人工导入不是自动生成的替代成功声明。

保护措施：仅规范B站域名与分集参数、密码/CSRF、Markdown消毒、鉴权图片与下载、拒绝符号链接、一次串行处理、失败/重启保留缓存、可信性不足等待人工核查。默认≤30分钟单集、localhost；部署模板普通用户systemd/Gunicorn，无大模型本机推理。

下一项实际实验：发布已保存chatgpt.com网络规则后，验证既有Codex CLI能否自动写出当前真实教材并过原版门禁，再做网站写作worker。不要继续扩展前端或搭新Agent框架。

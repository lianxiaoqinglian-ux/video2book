# 实际交付（2026-10-13）

已产出首份新教材：16分03秒MySQL《为什么使用数据库及数据库常用概念》。事实输入是作者公开归档完整逐字稿；按原版learning任务书由真正原生子Agent新写，未复制旧教材。保留公交GPS/Excel、QQ持久化、Word/WPS和购物查询案例。原版实体覆盖14/15，渲染检查通过；词覆盖不代表完整性保证。原声逐句准确性、所有画面信息和段落时间戳仍未核验。

私人样本在 `output/first-textbook/第一份真实教材.zip`，解压打开 `textbook.html`；另有Markdown。包括真实原视频02:30截图，以及单独标注的AI补充练习/答案。仅在本轮临时工作区，未向公共Git提交正文、逐字稿或媒体。

网站实际可运行：B站分集提交、任务状态、密码登录、教材库/历史、阅读/图片、Markdown下载、阶段保留重试。真实HTTP验收是“提交P2→真实元数据→无字幕等待→人工交接本轮新教材→阅读/下载”，没有自动写作或自动听音。截图/阅读/下载200；未登录下载302，CSRF缺失403。Gunicorn重启后教材仍在；网页主进程+一worker约49MB、当前数据约100KB，未包含大型模型或长课媒体。

可复用命令：

```bash
source /workspace/.venvs/video2book/bin/activate
python -m website --data-dir /workspace/video2book/output/website-data --port 8765
python -m website --data-dir /workspace/video2book/output/website-data worker --loop
python -m pytest website/test_site.py -q
python skills/video2book/scripts/selfcheck.py
```

先在私有环境中设置 `BOOKSITE_PASSWORD`；不提供默认密码。Cloud localhost不等于公开预览，用户尚不能从手机直接访问本轮临时服务。离线HTML可以先验收阅读内容。

成功命令证据：原版pipeline复用真实逐字稿退出0；原版queue派发/本块门禁成功；selfcheck退出0；原版729+初始14网页测试共743项通过；审查修复后19项网页测试通过。独立测试验证中断恢复、并发领取锁、可信字幕限制、原子缓存、鉴权/CSRF/路径与脚本注入。完整整课stage1退出1（其余355块未处理），不声称整课门禁通过。

失败：原课及新课匿名接口未取得中文字幕；官方read_audio/read_media仍不可用。独立免费14M ASR的60秒探针关键术语错误严重，已拒绝，不接入原版。独立Codex CLI原运行目录只读；临时可写目录保留原登录后，chatgpt.com代理CONNECT403、HTTPS回退超时，未得到自动写作产物。浏览器截图未成功，不声称手机/桌面浏览器视觉验收通过。

下一步只做一项：网页环境设置审核、保存并发布已存草稿（新增实测chatgpt.com及安装/启动说明），再验证既有Codex CLI写作。发布不保证模型调用必然可用。写作验证成功才接入网站worker；无字幕视频仍要可靠合法转录来源。

国内Ubuntu部署模板在 `deploy/` 与 `docs/product/DEPLOY.md`，普通用户systemd、Gunicorn和串行字幕worker、回环绑定及备份说明。未连接/修改用户服务器。公共手机访问需要私有网络或HTTPS访问方案；2–10小时、断点全书整合与生产服务器资源均尚未验证。

证据：[教材门禁](evidence/textbook-quality.json)、[真实HTTP](evidence/web-smoke.json)、[WSGI/重启](evidence/wsgi-smoke.json)、[独立ASR](evidence/independent-asr.json)、[来源](evidence/source-provenance.json)、[测试/失败/云草稿](evidence/checks.json)。

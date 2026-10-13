# 最新继续点：国内测试版可选写作适配与私有备份

从d43e6f5继续。用户明确要求长期国内2核4GB部署，Cloud只研发；不依赖Cloud订阅CLI作网站API。只补website/generation.py与现有worker调用，复用原版learning提示词、BlockPlan、本块门禁，原版核心/Skill未改。默认BOOKSITE_AUTO_WRITE=0；提供真实SILICONFLOW_API_KEY并设1后可消费可信字幕/等待写作任务。原有网页/SQLite/单进程锁、人工导入继续复用。

真实SF调用尚未验收：用户给的“你的 SiliconFlow 密钥”为占位文字，环境无key；当前代理拒绝官方域名，已存密钥要求和api.siliconflow.cn网络草稿，保存不等于发布。请求模型Qwen/Qwen3.5-122B-A10B现时ID/价格/上限均未证实。14项新接口测试为自有输入/模拟API，不称真实教材。7项受影响worker回归、11项备份测试通过，原版selfcheck通过，未重复旧全套。

教材包仍存在且已私有备份实际恢复校验：output/private-backups/first-textbook-readable-20261013.zip和website-data-20261013.zip。SHA256/SQLite完整性通过，排除secret.key。只在云本地ignored，必须下载到自有安全存储才能跨环境保留，未公开课程正文。

下一步只做：用户安全配置key并发布草稿后，provider-check --live读取model清单、核实价格/现有额度，再用真实短课字幕验收Qwen写作。无字幕优先复用omni-media ext的transcriptions接云ASR，协议有代码但兼容/准确性未测；视觉另验。不要扩新架构或下载大本地模型。详见research/product/README.md与docs/product/MODEL_SERVICES.md。

---

# 最新继续点：已生成真实教材，并实现私人教材库

本轮从 `2d4ce20` 继续，用户已授权轻量网站开发及一次独立免费ASR实验；此前“只研究/不开发”的阶段限制已被后续产品任务替代。原版Skill和核心源码未改。

- 首份新教材：BV1iq4y1u7vj P2《为什么使用数据库及数据库常用概念》，真实时长963秒。复用作者公开归档完整逐字稿，原版pipeline→任务书→真正原生子Agent生成learning长文11588字节；不是实时字幕抓取、不是本次听音，也不是复制旧教材。
- 原版本块实体14/15（93.33%），中文词块21/29（72.41%，含噪声）；渲染检查通过。完整课程严格stage1退出1，因为其余355块未处理；不声称整课完成。原声逐句准确性、完整视觉信息、段落时间戳仍未验收。
- 私有阅读样本：`output/first-textbook/readable/textbook.html` 与 `textbook.md`，含实际原视频02:30截图、明确标注AI补充的3道练习和解析；ZIP在 `output/first-textbook/第一份真实教材.zip`。上述都未公开提交，临时工作区重建后可能消失，请先检查。
- 网站代码 `website/`：密码/CSRF、B站分集链接、SQLite任务与历史、真实教材阅读/图片/Markdown下载、重试保留阶段。串行worker复用原版元数据/字幕；没有自动模型/ASR。真实HTTP流程提交P2→元数据成功→无字幕waiting_input→导入本轮新教材到同一任务→阅读/截图/下载200；这是有人交接的真实流程，自动端到端尚未完成。
- Gunicorn实际启动/持久化重启通过，主进程+一worker约49MB RSS，单本数据目录约100KB；不是2核4GB目标服务器实测或长课模型资源评估。`deploy/` 为普通用户systemd准备，用户服务器未连接/部署。
- 原729+首批网站14测试全通过；审查后的针对性修复结果见 `research/product/evidence/`。原版selfcheck通过。不需要无故反复全量测试。
- 独立ASR：官方sherpa-onnx中文14M int8，74MB下载，2线程，60秒真实音频试验占112–119MB，3.78/9.12秒；关系代数关键词严重错识，已拒绝，未处理全片、未写入原版逐字稿。
- 独立Codex CLI保留已有ChatGPT登录；只读CODEX_HOME无法启动，临时私有可写目录测试不改原登录。实际代理CONNECT到 `chatgpt.com` 返回403，HTTPS回退仍不能完成，90秒超时。没有CLI自动写作成功产物，不能假定登录就等于可用模型。
- 已保存更新后的云环境安装/启动草稿及仅新增实测 `chatgpt.com` 的网络规则；工具返回saved/requires_publish=true。需要用户在网页环境设置审核、保存、发布，未发布前不重试同样失败请求。未宣称规则已在本轮生效。

下一项小实验：发布该明确域名配置后，用当前真实逐字稿验证已有Codex CLI能否自动生成并通过同一原版门禁，再接入网站写作worker；不先搭新框架。无字幕任意新课程仍需要可靠合法听音/逐字稿通道。

---

# 第一阶段继续验证：最新结果

## 本轮：从3cb2441继续，真实音频已完整取得

- 已复用虚拟环境和原分块计划，没有再次运行729项测试。CDN `upos-sz-mirrorcosov.bilivideo.com` 单次探测返回206，之后原版真实P02音频准备流程退出0。
- 完整音频保存在本地忽略目录 `output/phase1-real-db-relationship/audio/P02_2、关系数据库.m4a`，未上传课程内容。FFprobe时长2001.611秒（元数据2002秒，差0.389秒），AAC/16kHz/单声道；全文件FFmpeg解码退出0、无错误。原版转录任务书已就位，queue返回BLK02一项。
- 原版匿名字幕探测一次未返回中文字幕轨；没有登录存档，SubtitleService返回`missing_sessdata`。这只说明当前匿名访问未取得字幕，不能断言课程没有字幕。未要求公开Cookie、未伪造登录态或逐字稿。
- **唯一最关键的阻塞：当前会话没有官方要求的read_audio/read_media，无法把已下载的真实音频转成完整逐字稿。** 当前可调用工具也没有该通道的挂载接口。最小下一步是接入官方原生听音通道，或私下提供本集已有合法完整逐字稿；不另装ASR或购买API。
- 尚未生成教材，因而未运行长文质量门禁；首次学习的详细度、原案例、画面信息、时间戳、练习答案都尚未验收。
- 本轮确认一个最小缺陷：下载中断残留的`.tmp.m4a`被`BlockPlan.audio_path`的`Pxx_*.m4a`回退匹配识别为缓存，CLI可退出0而音频缺尾。曾测得1681.593秒，已隔离并重新下载，未用于转录。建议以后仅做“排除临时文件＋缓存时长校验”的最小修复，等待用户确认；本轮核心源码未改。
- 发布状态未获确认：配置读取仍显示草稿、基线版本未变，平台未提供运行态/发布版本查询。不能据此认定已发布；但当前CDN运行态实测已通。如果网页显示待发布，请在环境设置审核、保存并发布以持久化。

证据：[本轮探测](evidence/first-textbook/results.json) · [完整音频与队列检查](evidence/first-textbook/local-ready-state.json) · [干净下载命令](evidence/first-textbook/audio-command-clean.json) · [中断缓存缺陷](evidence/first-textbook/rejected-cache-check.json)。以上不包含签名URL、凭据、课程音频或逐字稿正文。

## 上一轮记录（保留历史，以下403不代表当前CDN状态）

本轮继续使用原仓库与已有虚拟环境，没有连接/修改RackNerd，没有安装依赖、配置私人凭据或改业务代码。此前报告保留为历史记录，本页是当前结论。

| 原版操作 | 实测结果 |
|---|---|
| `python scripts/selfcheck.py` | 退出0，全部结构检查通过 |
| `python -m pytest -q` | 退出0，**729 passed in 7.35s**；此前WBI导航访问失败本轮已消失，没有修改或跳过测试 |
| B站README课程 `--page 1 --dry-run` | 退出0，真实元数据可读取；P01为18分40秒 |
| YouTube教学链接 `--dry-run` | 退出1，元数据请求仍被代理403拒绝 |
| B站P01 `--audio-only --block-minutes 25` | 退出2：默认40–60分钟的完整计划中BLK01含P01+P02，单选P01跨出块范围；这是计划保护，不是下载失败 |
| B站P02，官方环境变量把块区间设为20–40分钟、目标30分钟，新任务 `--audio-only` | 已生成真实parts/block_plan；所选P02为**33分22秒**。退出3，音频CDN下载被代理403拒绝 |
| 原版AudioFetcher只读取得P02媒体地址，64字节Range探测 | 返回有效媒体地址；实际媒体主机 `upos-sz-mirrorcosov.bilivideo.com` 的连接仍被代理403拒绝。不保存或输出带签名的完整URL |
| 真实工作区 `queue_tracker --next-transcribe 1 --json` | 退出0，无物理音频时不派发转录任务；不把空队列当作课程完成 |

精确参数、环境覆盖、耗时与底层退出码见 [commands.json](evidence/continuation/commands.json)，原始日志在同目录。真实生成的 [parts.json](evidence/continuation/real-parts.json)、[block_plan.json](evidence/continuation/real-block_plan.json) 可直接检查；不是根据假输入构造的计划。

## 当前到底跑到哪一步

**B站元数据 → 真实分块计划 → 获取音频地址已跑通；实际下载 → 听音转录 → 新教材生成尚未跑通。** YouTube元数据仍未跑通。

当前过程变量没有SESSDATA，原版因此跳过B站字幕分支。工具列表仍没有read_audio/read_media；即便媒体访问恢复，也不能据此宣称已有转录能力。未下载/安装其他ASR替代，未用旧教材冒充本次产物。

已保存追加媒体域名的云配置草稿，保留已有api.bilibili.com、www.youtube.com与包管理器预设。需要在环境设置中审核并应用网络变更；保存草稿不是实时网络已解除的证据。仅补充实测出现的域名，没有开放所有媒体站点。

## 尚未验证与最小解决方案

- **P0：实际媒体下载**——先应用该CDN域名配置，再仅重试这个33分钟分集；如果媒体主机变化，依据新报错精确补充，不循环盲试。
- **P0：指定听音**——需要平台支持的read_audio/read_media工具挂载，或提供原版已有真实逐字稿工作区。当前已登录Codex CLI并不自动等于具备这两个工具。VPS路线仅研究，未使用。
- **P1：画面信息**——原版仅逐字稿事实源，关键截图/未念出的代码、公式与界面动作没有采集链。先做10个关键点的“原视频—逐字稿—教材”对照，证实缺口后才比较成熟截图/OCR功能；不提前整合新框架。
- **P1：时间与来源**——听音稿禁止时间戳、静默纠错不留来源。先核验字幕时间映射/纠错案例，再提出最小侧车索引或标签方案，源码修改等确认。
- **P1：学习质量**——详细度、重要知识覆盖、原案例、练习答案与跨块连贯性都还未对新真实教材验收；729个测试通过不替代这些检查。
- **P2：长课**——2–10小时资源消耗、并发、真实中断恢复与全书质量仍留到第3阶段。当前只验证计划/缓存机制，不扩大成平台开发。

**结论不变：值得继续复用原版。** 本轮已有真实进展，环境阻塞从“B站元数据不可读”收窄为“媒体CDN不可读＋缺听音工具”。下一步只需继续这个已选33分钟分集，不需要购买API、提供VPS连接或重新调研架构。

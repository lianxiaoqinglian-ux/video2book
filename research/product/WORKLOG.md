# 简短工作记录

后续按轮次追加；同一天有多轮时分开记录。旧记录不改写为新的成功结论。

## 2026-10-13：真实教材与私人教材库（ad55a8d）

- 完成：用作者公开归档真实逐字稿，经原版learning任务书和原生子Agent生成MySQL新教材；增加一张真实截图和明确标注AI补充的练习。实现轻量私人网站及元数据/字幕串行worker。
- 验证：真实HTTP阅读、图片和下载成功；登录/CSRF保护有效；Gunicorn重启保留教材。原729＋首批网页14测试通过；中断恢复、并发锁、原子写入和字幕可信性修复后19项网页测试通过。
- 产物：[交付详情](RESULTS.md)、[证据](evidence/)、[网站](../../website/)、[部署说明](../../docs/product/DEPLOY.md)。私人教材正文仅在本地忽略目录。
- 阻塞：网站未接入自动写作；Codex CLI代理403；无字幕可靠转录缺失。无自动端到端、长课或实际服务器部署成功声明。
- 下一步：发布所存网络草稿后，仅复测真实CLI写作，成功再接入网站。

## 2026-10-13：建立固定GitHub查看入口

- 完成：新增 [进展入口](README.md) 与本工作记录；把后续总结路径写入AGENTS补充规则，保留原作者指令。
- 验证：核对当前分支与ad55a8d代码/已有证据、教材包仍在；文档本地链接检查和原版selfcheck通过。不改业务代码、不重装依赖、不重复全套测试。
- 后续：每轮更新入口、追加简短记录，并在聊天中给出GitHub链接及实际提交状态。


## 2026-10-13：国内测试版最小写作接口与私有验收备份

- 完成：定位worker的waiting_writer缺口；新增远程SiliconFlow宿主适配，复用原版learning提示词、BlockPlan与本块实体/渲染门禁，不改网页/数据库结构/原版核心。默认关闭，保留人工导入。增加安全provider-check，拒绝未知地址/重定向，保存用量/回执，超时不自动重复计费。
- 验证：14项新接口测试使用自有测试语料与模拟响应；7项受影响worker回归通过。缺密钥的真实provider-check退出1，没有发推理请求。原版selfcheck通过；没重复旧整套19项或729全量。API费用本轮0元，指定模型现时价格、真实准确性、国内机器可用性均未验证。
- 研究：官方SF旧schema证实SenseVoiceSmall转录设计；原版配套omni-media已有transcriptions模式，需私有配置与真实兼容验收。没有安装新ASR或把文字模型当听音工具。ChatGPT登录不充当网站API或免费不限量额度。来源见provider-research.json。
- 保全：新增标准库私有备份工具，11项测试通过；实际备份/恢复首本教材与SQLite网站数据，校验SHA256及SQLite integrity_check=ok，凭据不入包。ZIP仅本地ignored，尚未跨云保存；需用户下载到安全存储。
- 产物：[模型与费用边界](../../docs/product/MODEL_SERVICES.md)、[备份说明](../../docs/product/PRIVATE_BACKUP.md)、[接口证据](evidence/generation-adapter.json)、[私有备份证据](evidence/private-backup.json)。部署env模板已补默认关闭的API参数，不部署服务器。
- 下一步：在安全环境填真实SiliconFlow密钥、发布该域名规则，确认model ID/价格及已有额度，用一份真实短课字幕做模型验收；暂无需提供SSH。无字幕和视觉必须分别试跑，不承诺完全自动链。


### 本轮补充：Windows接续意向

用户要求先将当前进度推送GitHub，之后可能在已部署BiliNote的Windows电脑操作。新增WINDOWS_HANDOFF.md：保留原BiliNote配置/登录、Linux worker平台限制、私有教材备份位置与最小真实试验。未访问Windows、未实施集成或改写任务锁。

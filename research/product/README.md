# 视频教材网站：进展入口

后续每轮工作完成后，更新本页的当前状态，并在 [工作记录](WORKLOG.md) 追加简短记录：做了什么、实际验证、产物位置、阻塞和下一步。代码与证据保存到 `research/phase1-video-textbook`，不直接修改 main。

## 当前状态（2026-10-13）

| 项目 | 已完成 | 仍缺什么 |
| --- | --- | --- |
| 第一份教材 | 16分03秒MySQL课程，真实公开归档逐字稿→原版learning新长文，含真实截图及标注AI补充练习 | 原声逐句核验、完整视觉信息和逐句时间戳 |
| 私人网站 | 登录、B站分集提交、任务状态、历史、教材阅读、图片、Markdown下载、重试保留阶段 | 真实API写作验收、无字幕课程可靠转录、手机实际访问 |
| 实际验收 | 链接→真实元数据→等待输入→人工交接教材→阅读/下载；Gunicorn重启后教材保留 | 完全自动的真实端到端流程 |
| 测试 | 原版729项＋初批网页14项通过；修复后网页19项通过；原版自检通过 | 长课和目标服务器验收 |
| 部署准备 | 普通用户systemd、Gunicorn、持久化与备份说明 | 尚未连接或部署用户服务器 |

已有网站/教材实现提交：`ad55a8d`；进展入口提交：`d43e6f5`。本轮仅补最小写作适配和私有备份：14项新接口测试（测试数据/模拟API响应）、7项受影响worker回归、11项备份测试通过；未重复729全量或整套19网页测试，没有真实SiliconFlow推理。

当前已新增可选SiliconFlow写作适配，保留原网页/SQLite/单worker，默认关闭。当前阻塞是缺真实密钥、api.siliconflow.cn尚未放行，指定模型的现时可用性、价格和质量未验收。国内服务不依赖Cloud的ChatGPT订阅登录。无字幕可靠听音和视觉仍未接通。

下一项实验：私密配置SiliconFlow密钥并发布已存域名草稿，先只读检查model ID/当前报价，再用短课真实字幕验收一次远程写作；不用购买新服务或继续扩网页。

## 查看具体成果

- [Windows与现有BiliNote接续](../../docs/product/WINDOWS_HANDOFF.md)
- [每轮工作记录](WORKLOG.md)
- [实际交付与测试结果](RESULTS.md)
- [测试证据](evidence/)
- [网站启动和使用说明](../../website/README.md)
- [模型接口、费用边界与长期路线](../../docs/product/MODEL_SERVICES.md)
- [私有备份与恢复](../../docs/product/PRIVATE_BACKUP.md)
- [国内Ubuntu部署准备](../../docs/product/DEPLOY.md)
- [后续任务继续点](../phase1/CONTINUATION.md)

真实教材包保存在忽略目录 `output/first-textbook/第一份真实教材.zip`，本次检查仍存在。GitHub只保存代码、来源说明和测试证据，不上传未经授权的课程全文、逐字稿、媒体、Cookie、凭据或签名下载URL。Cloud临时文件可能随环境重建消失，该路径不是GitHub下载链接。

已创建并实际恢复校验私有样本/网站备份：`output/private-backups/first-textbook-readable-20261013.zip`、`website-data-20261013.zip`。SHA256清单和SQLite完整性校验通过；仍仅云端本地副本，必须下载到自有安全存储才跨环境持久。

用户后续可能在Windows接续，已有BiliNote。先复用原部署并核查真实转录，不重装或提前集成；当前worker/Gunicorn/systemd为Linux路径，建议已有WSL2 Ubuntu接续，原生Windows全流程未验收。

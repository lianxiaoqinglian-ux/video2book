# 国内测试版本的模型接口

网站继续使用现有Flask、SQLite、一个串行worker和人工导入，无新框架或本地大模型。默认 `BOOKSITE_AUTO_WRITE=0`，可先部署阅读库。设置为1且提供真实 `SILICONFLOW_API_KEY` 后，worker可消费可信字幕/`waiting_writer`任务，调用指定Qwen模型，复用原版learning提示词、BlockPlan和本块实体/渲染门禁，原子保存后发布。这是新增的最小宿主适配，不是原版原生子Agent SOP已自动化的声明；原版核心与Skill未改。

## 已接通和未验收

- 写作边界：`website/generation.py` 输入可信字幕、分集元数据，输出候选长文、请求回执、token用量与门禁报告。只调用官方HTTPS地址，拒绝重定向；默认输出8192 token、单集≤30分钟。实际模型上限尚未核验，不等于该模型官方额度。
- 失败恢复：复用元数据、字幕及已返回的候选稿；截断/低覆盖/渲染失败不发布。401/402/403/429等已拒绝请求可由用户修复后重试；超时或中断的计费状态未知，不自动再次请求。核对账单后备份/移走该任务`*_generation.json`回执再重试，可能重复计费。
- 14项新增API/发布/恢复测试使用自有教学测试语料与模拟响应，不是云模型试跑。此前真实MySQL教材和网站验收仍有效；本轮没有新生成的SiliconFlow真实教材。
- 真实provider-check退出1：缺密钥。官方域名本轮被云代理拒绝；已声明私密密钥及新增api.siliconflow.cn网络草稿，保存不等于发布。没有推理调用和费用。

## 推荐路线与费用边界

| 环节 | 最小复用方案 | 真正验证程度 |
| --- | --- | --- |
| 有字幕教材 | 原版可信字幕→新增SiliconFlow文字适配→原版门禁 | 本地接口已测；指定模型现时可用性、质量、价格待真调用 |
| 无字幕 | 原版omni-media `read_media` ext已有OpenAI-compatible `transcriptions`模式；评估接SF SenseVoiceSmall | 官方旧SF schema与上游源码已核查；实际兼容、中文专业术语、时长限制与价格未测 |
| 必要视觉 | 保留真实截图；后续少量关键帧提交已确认支持图像的远程模型，单独标注视觉核验 | 已有一张真实课件截图；指定Qwen图像能力/视觉API尚未验收 |
| 免费本地ASR | 仅作独立对照候选，当前不部署 | 先前14M sherpa试跑术语错误已拒绝；FunASR等本轮未试跑，也不绕过原版听音规则 |

SF旧公开schema只有转录text响应，不保证句级时间戳；不能伪造。omni-media目前读取私有config.json，单设API环境变量不足，后续需安全配置并实际验收；不需要重写ASR框架。2核4GB服务器只做轻量调度、缓存与FFmpeg预处理，模型推理在远程。

指定模型 `Qwen/Qwen3.5-122B-A10B` 的当前价格尚未取得官方证据，不报虚构金额。按每百万token输入价P、输出价Q：一次10000输入＋6000输出约 **0.01P＋0.006Q元**；这是计算公式，不是本模型报价。ASR按供应商实际音频计费规则另计，缓存/推理token、复审和人工重试以账单为准。本轮实花0元。也没有承诺免费ASR服务或不限量套餐。

ChatGPT套餐允许官方Codex CLI登录执行套餐内工作，受当前套餐限制；没有把该登录变成网站通用API的依据。国内长期网站使用独立供应商API认证与计费，不依赖Cloud订阅会话或Windows开机。

## 最小操作

在自己控制的安全配置中填真实密钥；不要发到聊天或Git。先只读核查model ID：

```bash
python -m website --data-dir /var/lib/video2book provider-check --live
```

列出model不等于推理通过或价格确认。确认当前价格、现有额度和小样本预算后启用 `BOOKSITE_AUTO_WRITE=1`，先测有真实字幕的短课。无字幕音频与视觉另验，未经验证前保持人工兜底。此阶段无需服务器SSH；部署时需要普通服务账户、Python/FFmpeg/systemd及私有访问方式的安装授权。Ubuntu服务器、国内网络、全自动视频链和长课仍未实测。

可核查来源与失败记录：[官方资料证据](../../research/product/evidence/provider-research.json)。

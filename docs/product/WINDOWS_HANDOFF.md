# Windows接续：先复用现有部署

用户已在Windows部署BiliNote，后续可能转到该电脑操作。不要重装BiliNote、覆盖其配置/登录、移动原目录或修改全局代理。当前阶段仅保存交接信息，没有访问用户电脑或集成BiliNote。

## 代码与当前状态

拉取 `research/phase1-video-textbook`；进展入口在 `research/product/README.md`，每轮记录在 `WORKLOG.md`。首本MySQL教材已生成；网页阅读/下载已真实验收。新增SiliconFlow写作适配只有本地接口测试，真实模型调用未验收。原版video2book仍是Agent Skill，不是完整自动网站。

若已有本地checkout，先 `git status` 检查并保留个人改动，再fetch/切分支；不运行强制reset。不在BiliNote目录直接安装本项目。

## 运行边界

- 推荐已有WSL2 Ubuntu22.04接续，这与最终国内服务器相近。按website/README.md安装项目与网页依赖，保留独立虚拟环境；网站和worker需要同一持久化data-dir。
- 原生Windows可研究启动Flask阅读界面，但当前worker使用Linux `fcntl`互斥锁，Gunicorn/systemd也针对Linux。未完成原生Windows兼容验收，不能承诺直接运行全部命令。此轮不为了迁移重写锁或任务系统。
- Windows可帮助核查浏览器、网络和模型API，性能较强时也更便于独立转录实验；原版禁止本地ASR替代听音的约束仍保留，不能将第三方结果冒充原版产物。Windows关闭后，最终国内服务器上的网站应独立运行，不把电脑作为长期必需worker。

## 保住真实验收教材

先下载当前私有包到自己的安全磁盘：

- `output/private-backups/first-textbook-readable-20261013.zip`：教材HTML、Markdown、真实截图与来源。
- `output/private-backups/website-data-20261013.zip`：SQLite教材库及所需教材/图片，排除登录密钥。

按 [PRIVATE_BACKUP.md](PRIVATE_BACKUP.md)验证、恢复；在新机器私密设置网站密码/API key。不要把包、逐字稿、Cookie或key推到公共GitHub。当前Cloud副本并不保证跨环境保留，GitHub没有课程正文。

## 接续只做一项小实验

先检查BiliNote当前版本、原转录能力与配置是否已可用，保留其现有环境。若有真实转录结果，先核验一小段专业术语、原声和时间戳，明确标为BiliNote独立产物；本网站尚未自动接入它。不能据“已部署”直接断言准确性或无需模型费用。

字幕写作优先检查现有SiliconFlow密钥、当前model ID与价格，按 [MODEL_SERVICES.md](MODEL_SERVICES.md)做一次真实短课验收。当前提供的key是占位文字，不能用于调用；无需公开账号Cookie或先提供服务器SSH。

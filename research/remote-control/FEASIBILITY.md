# 网页/飞书控制已有VPS Codex：仅可行性研究

未访问RackNerd，未安装、部署、生成密钥、启动远程控制或改变已有CLI/代理/登录。用户暂不提供SSH信息，本研究不作为video2book继续工作的前置条件。

| 路线 | 结论 | 登录/费用/限制 |
|---|---|---|
| 官方Codex remote-control | 官方仓库及本云CLI 0.159.2已有实验命令；Linux daemon、注册、配对、出站连接有实现 | 使用ChatGPT认证；API-key认证被明确拒绝。VPS版本、用户账号资格、chatgpt.com/codex网页接入是否开放均未验证；不能承诺即插即用或特定套餐权益 |
| Codex Cloud → SSH → VPS `codex exec` | 间接批处理可行，不是原生接管CLI；当前Cloud未接入用户Tailscale且无认证通道 | 可使用VPS原登录，但需解决连接、长任务存活、审批与回传；不优先搭这种桥 |
| HAPI Web/PWA＋Tailscale | 已有Codex app-server集成、Hub/Runner、远程新建/审批/恢复能力；是独立网页，不是ChatGPT网页 | 文档要求Codex≥0.154.0。继承启动用户的认证/CODEX_HOME；可自托管免费使用，无需模型API或自购域名，使用Plus时受订阅额度约束；未在VPS部署验证 |
| cc-connect＋飞书长连接 | 已有Codex与Feishu代码实现，最贴合“不用自有域名、Windows关机仍从飞书发任务”的备选 | 在VPS常驻桥接进程并调用现有CLI；飞书应用凭据另行安全配置，不是模型API。软件MIT免费；飞书权限/额度与VPS兼容性未实测 |
| Agents SDK/API | 能在VPS构建应用，但不自动接入Codex网页，也不把Plus变成免费API | 常规API调用单独计费；本需求不采用、不购买、不自研 |

## 飞书候选的源码核查

`chenhg5/cc-connect` 固定提交 `dfad19415a38b00b2c5c288610784d1a7eef337f`：

- `agent/codex/codex.go` 注册Codex，支持exec与app_server；`agent/codex/executable.go`支持显式CLI路径或PATH发现，避免误选第二份安装。
- exec后端没有交互审批IPC；源码说明需app_server后端才能交互审批。不能把默认自动执行当作符合安全要求。
- `platform/feishu/feishu.go`及`docs/feishu.md`实现/说明WebSocket长连接，不要求公网回调、域名或公开SSH端口。
- 配置样例的`allow_from`默认允许所有用户，所以将来实施必须限定自己的用户ID、项目目录及权限；普通用户运行，禁止yolo/root无人值守。
- 不配置第三方provider、不改原代理/认证，在同一普通用户环境调用已有CLI是候选路径；保留全部现有状态是否兼容还需真正部署前检查。

## 推荐顺序（暂不实施）

如果必须用chatgpt.com/codex，先只读核验VPS的`codex remote-control --help`及账户网页入口；确认开放后才能考虑官方方案。HAPI、飞书桥不会自动变成该网页的执行环境。

如果接受飞书作为入口，下一阶段优先验证**cc-connect＋飞书长连接＋已有VPS Codex**。如果接受独立网页，则HAPI＋Tailscale是备选。两者都将执行进程放在VPS，并作为普通用户持久服务，Windows关机不影响服务器执行；会话恢复不等于崩溃后自动重放任务。

最小未来步骤：只读确认VPS CLI版本/普通用户/原认证方式 → 固定一个成熟桥接版本 → 单项目、单用户、只读模式试发任务 → 核验结果回传及关机后持续工作 → 才批准持久服务配置。所有安装、登录/密钥、配对、服务修改和服务器访问仍待另行授权。Tailscale保持备用，不要求暴露公网SSH/API。

## 可检查来源

- [官方daemon文档](https://github.com/openai/codex/blob/a9b0815167c27ab13719dd12d13b63e02b70d221/codex-rs/app-server-daemon/README.md)、[ChatGPT认证约束](https://github.com/openai/codex/blob/a9b0815167c27ab13719dd12d13b63e02b70d221/codex-rs/app-server-transport/src/transport/remote_control/auth.rs)
- [HAPI共享Codex会话及生命周期](https://github.com/tiann/hapi/blob/99cd3d4172fb49f893b62dff39239fa85c5f6275/docs/guide/codex-shared-sessions.md)
- [cc-connect飞书接入](https://github.com/chenhg5/cc-connect/blob/dfad19415a38b00b2c5c288610784d1a7eef337f/docs/feishu.md)、[Codex后端与审批区别](https://github.com/chenhg5/cc-connect/blob/dfad19415a38b00b2c5c288610784d1a7eef337f/agent/codex/codex.go)、[配置样例](https://github.com/chenhg5/cc-connect/blob/dfad19415a38b00b2c5c288610784d1a7eef337f/config.example.toml)
- [官方Agents SDK](https://github.com/openai/openai-agents-python)：常规模型调用需要API认证，与CLI订阅登录不同。

官方网页文档此前受Cloud代理403限制，以上主要依据官方/项目GitHub文档及源码；第三方功能声明不等于VPS端验收。此次未配置任何飞书应用或连接器、未发送消息。

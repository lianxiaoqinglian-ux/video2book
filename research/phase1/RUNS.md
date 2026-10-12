# 实际执行及失败记录

所有下表输出均由当前命令直接捕获。`commands.json` 保存完整参数、工作目录、退出码和耗时；日志保留stdout/stderr，未用管道覆盖底层退出码。原版CLI命令不改源码。完整pytest只运行一次；AGENTS补充后仅重跑作者要求的结构自检。

| 检查 | 退出码 | 日志 |
|---|---:|---|
| environment | 0 | [environment.log](evidence/environment.log) |
| pip-check | 0 | [pip-check.log](evidence/pip-check.log) |
| selfcheck | 0 | [selfcheck.log](evidence/selfcheck.log) |
| pytest | 1 | [pytest.log](evidence/pytest.log) |
| cli-info | 0 | [cli-info.log](evidence/cli-info.log) |
| queue-help | 0 | [queue-help.log](evidence/queue-help.log) |
| bilibili-real-dry-run | 1 | [bilibili-real-dry-run.log](evidence/bilibili-real-dry-run.log) |
| youtube-real-dry-run | 1 | [youtube-real-dry-run.log](evidence/youtube-real-dry-run.log) |
| synthetic-audio-create | 0 | [synthetic-audio-create.log](evidence/synthetic-audio-create.log) |
| synthetic-local-pipeline | 0 | [synthetic-local-pipeline.log](evidence/synthetic-local-pipeline.log) |
| synthetic-local-resume | 0 | [synthetic-local-resume.log](evidence/synthetic-local-resume.log) |
| synthetic-ffprobe | 0 | [synthetic-ffprobe.log](evidence/synthetic-ffprobe.log) |
| synthetic-queue-summary | 0 | [synthetic-queue-summary.log](evidence/synthetic-queue-summary.log) |
| synthetic-queue-claim | 0 | [synthetic-queue-claim.log](evidence/synthetic-queue-claim.log) |
| synthetic-queue-after-claim | 0 | [synthetic-queue-after-claim.log](evidence/synthetic-queue-after-claim.log) |
| synthetic-queue-release | 0 | [synthetic-queue-release.log](evidence/synthetic-queue-release.log) |
| synthetic-dispatch-print | 0 | [synthetic-dispatch-print.log](evidence/synthetic-dispatch-print.log) |
| ffmpeg-version | 0 | [ffmpeg-version.log](evidence/ffmpeg-version.log) |
| ffprobe-version | 0 | [ffprobe-version.log](evidence/ffprobe-version.log) |
| final-selfcheck | 0 | [final-selfcheck.log](evidence/final-selfcheck.log) |
| archived-source-commit | 0 | [archived-source-commit.log](evidence/archived-source-commit.log) |

## 可复制命令（工作目录见JSON）

```bash
/workspace/.venvs/video2book/bin/python -c 'import sys,importlib.metadata as m,shutil; print(sys.version); print({p:m.version(p) for p in ["video2book","pytest","requests","yt-dlp"]}); print({p:shutil.which(p) for p in ["ffmpeg","ffprobe"]})'
/workspace/.venvs/video2book/bin/python -m pip check
/workspace/.venvs/video2book/bin/python scripts/selfcheck.py
/workspace/.venvs/video2book/bin/python -m pytest -q
/workspace/.venvs/video2book/bin/python skills/video2book/src/cli.py info
/workspace/.venvs/video2book/bin/python skills/video2book/scripts/queue_tracker.py --help
/workspace/.venvs/video2book/bin/python skills/video2book/src/cli.py pipeline https://www.bilibili.com/video/BV14VqVBrEhc --page 1 --dry-run --article-type learning --base-dir /tmp/video2book-phase1-real
/workspace/.venvs/video2book/bin/python skills/video2book/src/cli.py pipeline 'https://www.youtube.com/watch?v=rfscVS0vtbw' --page 1 --dry-run --article-type learning --base-dir /tmp/video2book-phase1-real
ffmpeg -hide_banner -loglevel error -f lavfi -i sine=frequency=440:duration=3 -c:a pcm_s16le /tmp/video2book-phase1-synthetic/sample.wav
/workspace/.venvs/video2book/bin/python skills/video2book/src/cli.py pipeline /tmp/video2book-phase1-synthetic/sample.wav --all --audio-only --article-type learning --base-dir /tmp/video2book-phase1-synthetic/output
/workspace/.venvs/video2book/bin/python skills/video2book/src/cli.py pipeline /tmp/video2book-phase1-synthetic/sample.wav --all --audio-only --article-type learning --base-dir /tmp/video2book-phase1-synthetic/output
ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -of json /tmp/video2book-phase1-synthetic/output/sample_local_sample/audio/P01_sample.m4a
/workspace/.venvs/video2book/bin/python skills/video2book/scripts/queue_tracker.py --dir /tmp/video2book-phase1-synthetic/output/sample_local_sample --summary
/workspace/.venvs/video2book/bin/python skills/video2book/scripts/queue_tracker.py --dir /tmp/video2book-phase1-synthetic/output/sample_local_sample --next-transcribe 1 --claim --json
/workspace/.venvs/video2book/bin/python skills/video2book/scripts/queue_tracker.py --dir /tmp/video2book-phase1-synthetic/output/sample_local_sample --next-transcribe 1 --json
/workspace/.venvs/video2book/bin/python skills/video2book/scripts/queue_tracker.py --dir /tmp/video2book-phase1-synthetic/output/sample_local_sample --release all --json
timeout 30 /workspace/.venvs/video2book/bin/python skills/video2book/tools/v2b_dispatch.py transcribe 1 --base-dir /tmp/video2book-phase1-synthetic/output
ffmpeg -version
ffprobe -version
/workspace/.venvs/video2book/bin/python scripts/selfcheck.py
git rev-parse HEAD
```

## 结果判读

- 全套pytest：729个用例执行完成，728 passed / 1 failed，退出1。失败为 `test_wbi_auto_sticky_downgrade_on_first_failure`；mock播放器请求之前，实际WBI key取得调用导航接口被代理403拒绝，故只记录到旧端点一次调用。未禁用断言、未跳过测试、未伪造密钥。建议单独授权修复该测试网络隔离，不以改安装掩盖它。
- B站真实dry-run：仓库README的 `BV14VqVBrEhc`，元数据前置导航请求被拒；YouTube：freeCodeCamp Python入门公开教学链接 `rfscVS0vtbw`，yt-dlp元数据被代理拒绝。YouTube例本身超过20–40分钟，只用于非下载访问探测，不冒充短课样本或已合法取得素材；没有下载/读取内容。
- 网络草稿已声明api.bilibili.com、www.youtube.com，但当前实测仍403。没有证据认定是缺Cookie或模型密钥，也未要求私人Cookie。网络配置生效后才重试；即便生效仍可能有平台限流/访问限制。
- `info` 中平台“就绪”是本地依赖诊断，不代表平台网络、字幕或听音功能真的可用。工具元数据中没有read_audio/read_media；没有新模型/ASR安装。
- synthetic开头各命令只用3秒正弦波，不能验证课程内容、转录、长文写作或长课语义。重跑前后哈希在 `synthetic-resume-hashes.json`，queue-after-claim中next_transcribe为空；释放后wrapper重新取得载荷。
- dispatch-print退出0只表明打印预制prompt；没有把提示词当作教材，也没有启动转录子Agent。
- 两个真实独立审查Agent分别检查源码能力、运行兼容，并互相交换发现。主Agent复核：learning只能还原原题，legacy才可生成2–3题；以源码而非审查口述为准。

## 公开归档审计复核

只读Git克隆成功：`git clone --depth 1 --filter=blob:none --no-checkout https://github.com/LINJIANG12/video2book-courses.git /tmp/video2book-course-reference`，退出0。固定提交及文件哈希见归档审计JSON。可以按源路径读取：

```bash
git -C /tmp/video2book-course-reference show 675f5d59107498a7e2091d8c46f4f90d97e926cd:计算机/数据库/SQL两小时半入门/subtitles/BLK01_P01上_逐字稿.md
git -C /tmp/video2book-course-reference show 675f5d59107498a7e2091d8c46f4f90d97e926cd:计算机/数据库/SQL两小时半入门/textbooks/模块01_SQL关系型数据库从入门到全流程实战精通_精读全书.md
```

审计直接调用原版 `lint_render(text)`、`summarize_render(...)`、`fatal_render_total(...)`，不是另写一套门禁；计数及小量摘录保存在 `archived-course-audit.json`。归档没有parts/block_plan/manifest，因此没有伪造这些文件让它冒充可续跑工作区，也未把整本书送入stage1后宣称通过。

## 云配置与文件范围

云配置工具返回 `status=saved`、`requires_publish=true`；已保存安装脚本、启动说明和精确网络域名。安装脚本实际走“已有依赖可用、跳过安装”分支。未执行发布/新任务恢复。详见本目录WORKFLOW和环境设置。

新增研究报告和证据、AGENTS仅追加8行；核心源码、现有测试及依赖声明不变。报告是本地工作分支交付，未推送GitHub、未部署服务。

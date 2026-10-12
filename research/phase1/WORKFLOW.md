# 轻量复用工作方式

```bash
cd /workspace/video2book
source /workspace/.venvs/video2book/bin/activate
python -m pip check
video2book info
```

依赖已满足时直接工作。简单任务不做大方案研究；只阅读当前功能需要的文档。局部改动运行相关 `python -m pytest -q skills/video2book/tests/test_<相关模块>.py`，随后遵守原作者结构自检要求；新环境/重大改动/未解释的广泛故障才做完整基线 `python -m pytest -q`。通过后不无故重复。

```bash
cd /workspace/video2book/skills/video2book
python scripts/selfcheck.py
python scripts/queue_tracker.py --dir <真实课程工作区> --summary
python scripts/queue_tracker.py --dir <真实课程工作区> --next-module 1 --json
timeout 30 python tools/v2b_dispatch.py module 1 --base-dir <产物根> --pattern <课程标识>
```

`queue_tracker` 负责文件进度/载荷/认领；`v2b_dispatch` 是载荷打印包装器，**不会自行启动模型或子Agent**。需要并发时复用宿主真正的独立Agent，不安装编排框架。小于等于60分钟课程按原版由主Agent串行。

真实转换前按 SKILL 核查输入、风格及指定通道；输出用 `--base-dir /workspace/video2book/output`。任务未完成、缺逐字稿或缺原视频时停止相应验收，不用伪造文件或模拟素材填补成功标准。遇到具体缺陷才检索成熟开源功能。研究和证据保存在工作分支，核心源码改动先征得用户确认。

没有常驻Web服务需要启动。云配置保存/发布与当前进程、外部MCP工具挂载是不同操作；配置草稿保存不会解除403或自动添加听音工具。

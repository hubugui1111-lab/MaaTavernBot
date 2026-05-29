# CLAUDE.md - 炉石传说酒馆战旗 Bot 项目指引

## 项目概述

本项目是基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 开发的炉石传说酒馆战旗自动化脚本。通过 ADB 连接 MuMu 模拟器，使用图像识别技术实现游戏自动化，并提供简洁的褐色主题图形界面。

## 关键文件路径

### 项目入口
- [main.py](main.py) — 程序入口，包含 tkinter UI 和 MAA 框架初始化

### 核心代码（bot/）
- [bot/game_bot.py](bot/game_bot.py) — 核心游戏逻辑，BotAction 自定义动作
- [bot/phase_detector.py](bot/phase_detector.py) — 页面检测，PhaseDetector 自定义识别
- [bot/screen_regions.py](bot/screen_regions.py) — 坐标常量定义
- [bot/ui_log_handler.py](bot/ui_log_handler.py) — 日志桥接到 UI

### 资源文件（resource/）
- [resource/default_pipeline.json](resource/default_pipeline.json) — 流水线默认参数
- [resource/pipeline/bg_pipeline.json](resource/pipeline/bg_pipeline.json) — 游戏任务流水线
- [resource/image/](resource/image/) — 模板图片目录

### 项目文档（docs/）
- [docs/requirements.md](docs/requirements.md) — **需求文档**：功能需求、用户确认的策略选项
- [docs/architecture.md](docs/architecture.md) — **技术架构**：技术栈、架构图、状态机、对象关系
- [docs/design-spec.md](docs/design-spec.md) — **设计规范**：UI色彩/字体/布局、代码规范、操作时序、日志级别
- [docs/implementation-plan.md](docs/implementation-plan.md) — **执行计划**：9 个阶段的详细任务、产出、验证方法

### 开发日志（devlog/）
- [devlog/](devlog/) — 每日开发日志，按日期命名（如 `2026-05-28.md`）

## 工作指引

### 每次开发前
1. 阅读 `docs/implementation-plan.md`，确认当前处于哪个阶段
2. 阅读 `devlog/` 中最新日期的日志，了解最近进展和待办事项
3. 确认当前阶段的依赖阶段已完成并验证通过

### 开发过程中
1. **小步推进**：每个任务完成后验证，再进入下一个任务
2. **不跳阶段**：严格按执行计划的阶段顺序进行
3. **不预写代码**：只写当前阶段需要的代码，不做"以后可能用到"的功能
4. **先读后写**：修改已有文件前先用 Read 工具查看当前内容
5. **遵守设计规范**：色彩、字体、时序、命名均按 `docs/design-spec.md` 执行
6. **更新日志**：每个阶段完成后更新 `devlog/` 中的当日日志

### 开发完成后
1. 更新 `devlog/` 日志，标记完成的任务和新产生的待办
2. 如有文档变更，同步更新 `docs/` 中的对应文件

### 给 AI 助手的特别说明
- 用户是不懂代码的小白，所有交互用通俗语言，避免技术术语
- 需要用户操作时（如截图），给出清晰的步骤说明
- 代码注释用中文，但变量/函数命名用英文
- 不要一次性写太多代码，每步确认能跑通再继续
- 模板图片需要用户从游戏中截取，AI 无法自动生成

## MaaFramework 参考

MaaFramework 源码位于上级目录 `../`（即 `d:/MaaFramework-main/`），需要查看框架源码时使用该路径。

### MaaFramework 关键文件
- `../AGENTS.md` — MaaFramework 本身的开发指引
- `../sample/python/demo1.py` — 官方 Python 示例（ADB 连接、自定义识别/动作）
- `../docs/zh_cn/3.1-任务流水线协议.md` — Pipeline JSON 协议文档
- `../docs/zh_cn/2.4-控制方式说明.md` — 控制器（ADB/Win32）使用说明
- `../source/binding/Python/maa/` — Python 绑定源码（参考 API）

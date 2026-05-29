# 技术架构文档

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 框架 | MaaFramework | 图像识别 + 自动化执行框架 |
| 语言 | Python 3.10+ | MaaFramework 提供 Python 绑定（`maafw` 包） |
| UI | tkinter (ttk) | Python 标准库，无需额外安装 |
| 连接 | ADB | Android Debug Bridge，连接 MuMu 模拟器 |
| 识别 | TemplateMatch + OCR | 模板匹配找图 + 文字识别读金币 |
| 设备 | MuMu 模拟器 12 | 默认 ADB 端口 127.0.0.1:7555 |

## 架构概览

```
┌─────────────────────────────────┐
│         main.py (UI层)           │
│   tkinter 窗口 + 状态/日志显示    │
└──────────────┬──────────────────┘
               │ 调用
┌──────────────▼──────────────────┐
│     bot/game_bot.py (逻辑层)     │
│   BotAction 自定义动作           │
│   游戏状态机 + 回合循环          │
└──────┬──────────────┬───────────┘
       │              │
       │ 调用         │ 调用
┌──────▼──────┐ ┌────▼───────────┐
│  检测层      │ │  策略层         │
│  phase_     │ │  screen_regions│
│  detector   │ │  .py (坐标常量) │
│  (页面识别)  │ │                │
└──────┬──────┘ └────────────────┘
       │
┌──────▼──────────────────────────┐
│  resource/ (资源层)              │
│  pipeline/*.json (任务流水线)    │
│  image/*.png    (模板图片)       │
└─────────────────────────────────┘
       │
┌──────▼──────────────────────────┐
│  MaaFramework (框架层)           │
│  Resource → Controller → Tasker  │
└─────────────────────────────────┘
       │
┌──────▼──────────────────────────┐
│  MuMu 模拟器 (设备层)            │
│  炉石传说游戏                    │
└─────────────────────────────────┘
```

## 核心对象关系

```
Resource ──加载──> pipeline JSON + 模板图片
Resource ──注册──> PhaseDetector (自定义识别)
Resource ──注册──> BotAction (自定义动作)

AdbController ──连接──> MuMu 模拟器 (ADB)

Tasker ──绑定──> Resource + AdbController
Tasker ──执行──> tasker.post_task("MainLoop")
```

## 流水线结构

```json
{
    "MainLoop": {
        "next": ["BotLoop"]
    },
    "BotLoop": {
        "recognition": "Custom",         // PhaseDetector 检测当前页面
        "custom_recognition": "PhaseDetector",
        "action": "Custom",              // BotAction 执行对应操作
        "custom_action": "BotAction",
        "next": ["BotLoop"],             // 自循环
        "timeout": -1,                   // 永不超时
        "rate_limit": 500               // 每秒最多 2 次迭代
    }
}
```

## 游戏状态机

```
  [主菜单] ──点击战旗入口──> [战旗大厅] ──寻找对局──> [英雄选择]
       ^                                                  │
       │                                          选最左英雄
       │                                                  │
       │                                                  v
       │                                            [招募阶段]
       │                                           /    |    \
       │                                  升级 / 购买 / 打牌 \ 结束回合
       │                                         /      |      \
       │                                        v       v       v
       │                                    [招募阶段 循环操作]
       │                                                  │
       │                                         点击结束回合
       │                                                  │
       │                                                  v
       │                                            [战斗阶段]
       │                                             等待...
       │                                           /        \
       │                                    对局结束?      还在打?
       │                                       │              │
       │                                       v              │
       └─── 结算退出 ◄── [结算画面]              └──────────────┘
```

## 坐标系统

- 基准分辨率：1080 × 1920（竖屏，宽 × 高）
- 坐标缩放：实际截图尺寸 / 基准尺寸 按比例缩放
- 精度要求：点击误差在 ±10 像素内均可接受

## 关键目录

```
hearthstone-bot/
├── main.py                  # 程序入口
├── CLAUDE.md                # AI 助手指引
├── bot/                     # 核心代码
│   ├── game_bot.py          # 游戏主循环
│   ├── phase_detector.py    # 页面检测
│   ├── screen_regions.py    # 坐标常量
│   └── ui_log_handler.py    # UI 日志
├── resource/                # 资源文件
│   ├── default_pipeline.json
│   ├── pipeline/            # 流水线 JSON
│   └── image/               # 模板图片
├── docs/                    # 项目文档
│   ├── requirements.md      # 需求文档
│   ├── architecture.md      # 本文件
│   ├── design-spec.md       # 设计规范
│   └── implementation-plan.md # 执行计划
└── devlog/                  # 开发日志
    └── YYYY-MM-DD.md
```

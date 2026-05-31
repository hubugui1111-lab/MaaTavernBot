# MaaTavernBot (MTB)

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的炉石传说酒馆战旗全自动脚本。开源免费，仅供学习交流使用。

![Version](https://img.shields.io/badge/version-v1.7.1-green)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## 功能

| 功能 | 说明 |
|------|------|
| 自动导航 | 11 种界面模板匹配，不依赖外部 API |
| 英雄选择 | 自动选第2个英雄并确认 |
| 升级酒馆 | 每回合自动检测升级 |
| 购买随从 | 自动从酒馆拖拽到手牌 |
| 打出手牌 | 手牌拖到场上，循环最多5轮 |
| 英雄技能 | 每回合自动使用 |
| 任务刷新 | 对局结束 OCR 识别零进度任务自动更换 |
| 智能出售 | 手牌≥8且满场时自动出售 |
| 自动重开 | 对局结束自动重开 |
| 卡住自救 | 5分钟同画面自动重启 |
| 微信通知 | PushPlus 掉线/卡住推送微信 |
| 定时运行 | 设置时间段自动启停 |
| 系统托盘 | 最小化到托盘后台运行 |
| 炉石酒馆UI | QSS 定制暗棕底金色边框主题 |

## 下载

[📥 最新版本 v1.7.1](https://github.com/hubugui1111-lab/MaaTavernBot/releases/latest)

解压即用，无需安装。

## 使用

### 环境要求
- MuMu 模拟器（或其他支持 ADB 的模拟器）
- 分辨率：**1600×900 横屏**，DPI：**240**
- 开启 ADB 调试

### 运行
1. 双击 `MaaTavernBot.exe`
2. 输入 ADB 端口号（MuMu 默认 16384 或 16416）
3. 点击「连接」→「开始」

### PushPlus 微信通知
在设置页输入 PushPlus Token，Bot 掉线或卡住时自动推送微信通知。

## 常见问题

| 问题 | 解决 |
|------|------|
| 连接没反应 | 检查 ADB 端口、模拟器是否开启 ADB 调试 |
| 不买随从/不升级 | 确认分辨率 1600×900 横屏、DPI 240 |
| 任务刷新失败 | 每个账号每天只能刷新一次 |
| 卡住不动 | Bot 5分钟自动重启，也可手动停止重开 |
| 会掉分吗 | 会，本软件未接入打牌AI或策略 |

## 贡献

[CONTRIBUTING.md](CONTRIBUTING.md)

## 反馈

[🐛 提交问题](https://github.com/hubugui1111-lab/MaaTavernBot/issues)

## 免责声明

本软件开源免费，仅供学习交流使用。通过图像识别模拟操作，可能违反游戏服务条款。使用产生的账号风险由用户自行承担。**禁止用于商业用途。**

## 协议

代码基于 AGPL-3.0 协议开源。图标及视觉设计保留所有权利。

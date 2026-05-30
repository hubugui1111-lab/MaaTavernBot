# MaaTavernBot (MTB)

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的炉石传说酒馆战旗全自动脚本。开源免费，仅供学习交流使用。

![Version](https://img.shields.io/badge/version-v1.2-green)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## 功能

| 功能 | 说明 |
|------|------|
| 自动导航 | 主菜单 → 模式选择 → 酒馆战旗 → 对局 |
| 英雄选择 | 自动选第2个英雄并确认 |
| 升级酒馆 | 每回合自动检测升级 |
| 购买随从 | 自动从酒馆拖拽到手牌 |
| 打出手牌 | 手牌拖到场上，循环最多5轮 |
| 英雄技能 | 每回合自动使用 |
| 饰品选择 | 自动随机选择 |
| 智能出售 | 手牌≥8且满场时自动出售 |
| 自动重开 | 对局结束自动重开 |
| 卡住自救 | 5分钟同画面自动重启 |
| 定时运行 | 设置时间段自动启停 |
| 系统托盘 | 最小化到托盘后台运行 |

## 下载

[📥 最新版本 v1.2](https://github.com/hubugui1111-lab/MaaTavernBot/releases/latest)

解压即用，无需安装。

## 使用

### 环境要求
- MuMu 模拟器（或其他支持 ADB 的模拟器）
- 分辨率：**1600×900 横屏**，DPI：**240**
- 开启 ADB 调试

### 运行
1. 双击 `MaaTavernBot.exe`
2. 输入 ADB 端口号（MuMu 默认 7555）
3. 点击「连接」→「开始」

详细说明见 [使用文档](docs/USAGE.md)

## 常见问题

| 问题 | 解决 |
|------|------|
| 连接没反应 | 检查 ADB 端口、模拟器是否开启 ADB 调试 |
| 不买随从/不升级 | 确认分辨率 1600×900 横屏、DPI 240 |
| 卡住不动 | Bot 5分钟自动重启，也可手动停止重开 |
| 会掉分吗 | 会，本软件未接入打牌AI或策略 |

## 反馈

[🐛 提交问题](https://github.com/hubugui1111-lab/MaaTavernBot/issues/new/choose)

## 免责声明

本软件开源免费，仅供学习交流使用。通过图像识别模拟操作，可能违反游戏服务条款。使用产生的账号风险由用户自行承担。**禁止用于商业用途。**

## 协议

代码基于 AGPL-3.0 协议开源。图标及视觉设计保留所有权利。

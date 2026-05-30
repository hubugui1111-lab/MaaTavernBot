# PushPlus 异常告警通知 — 设计文档

## 概述

为 MaaTavernBot 添加远程异常告警功能，Bot 卡住或断连时通过 PushPlus 推送微信通知。

## 架构

```
game_bot.py (现有)                notify.py (新增 ~50行)
┌──────────────────┐              ┌─────────────────────────┐
│ 卡住检测 (已有)    │──卡住重启──→│ send_alert(title, msg)   │
│ 截图前 ADB 检查   │──断连检测──→│                         │
│ (新增)           │              │ POST pushplus.hxtrip.com│
└──────────────────┘              └─────────┬───────────────┘
                                          │
                                          ↓
                                    微信消息通知
```

## 组件

### notify.py

- `send_alert(title, msg)` — 单次通知
- 内部维护 `_last_sent: dict[str, float]`，同类型告警 30min 内不重复发
- 需要全局 `token` 变量，从 `maa_option.json` 读取
- HTTP POST: `https://pushplus.hxtrip.com/send?token={token}&title={title}&content={content}&template=html`
- 超时 8 秒，失败静默（不阻塞主流程）

### game_bot.py 改动

**卡住重启通知** — 在现有 `_handle_stuck()` 尾部添加：
```
_notify("卡住重启", "Bot 已自动重启\n时间: {datetime}\n版本: v{VERSION}")
```

**断连检测** — 在每次 `post_screencap()` 前后包装：
```
连续 3 次截图失败（结果为空/超时）:
  _notify("掉线", "Bot 与模拟器断开\n最后活跃: {last_ok_time}")
  标记 offline = True
恢复: offline = False（不发通知）
```

### GUI 变更

- 控制面板新增 `Token: [________]` 输入框
- 保存/加载复用现有 `maa_option.json`，key: `pushplus_token`
- Token 为空时不发通知

## 通知模板

| 事件 | 标题 | 内容 |
|------|------|------|
| 卡住重启 | ⚠️ 卡住重启 | Bot 已自动重启\n时间: HH:MM:SS\n版本: v1.5 |
| 断连 | ❌ Bot 掉线 | Bot 与模拟器断开\n最后活跃: HH:MM:SS |

## 防骚扰

- `_last_sent` dict 记录每种事件最后发送时间
- `debounce_minutes = 30`，同类型 30 分钟内不重复
- 首次发完直接 return，不发"已恢复"

## 不做的

- 不统计掉分/胜率
- 不主动定时汇报
- 不检测游戏闪退（闪退后会截图失败 → 触发断连通知）
- 不接入其他推送平台

## 测试

1. 填 Token → 运行 → 断连模拟器 → 等 3 次截图失败 → 微信收到"掉线"
2. 运行中让画面冻结 → 5 分钟 → Bot 重启 → 微信收到"卡住重启"
3. 同类型告警 30 分钟内只收一次
4. 不填 Token → 正常运行，无副作用

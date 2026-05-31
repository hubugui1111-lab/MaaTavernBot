# 贡献指南

欢迎贡献！本项目是 AGPL-3.0 开源协议。

## 如何贡献

- **报告 Bug**: 在 [Issues](https://github.com/hubugui1111-lab/MaaTavernBot/issues) 提交，附上截图和操作步骤
- **功能建议**: 在 Issues 用 Feature Request 模板
- **提交代码**: Fork → 新分支 → PR

## 开发环境

- Python 3.11
- `pip install maafw opencv-python numpy PySide6`
- MuMu 模拟器 (ADB 调试)

## 代码规范

- 变量/函数命名用英文，注释用中文
- TDD: 先写测试 → 确认失败 → 最小实现 → 确认通过
- 每步做完用 `/requesting-code-review`

## 禁止

- 不要在代码/注释中提及 aalc
- 不要把开发日志 (devlog/) 推送到 GitHub
- 不要硬编码 API token/key

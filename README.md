# Ollama Fluent UI

<div align="center">

🎨 基于 PySide6 + PySide6-Fluent-Widgets 实现的 Fluent Design 风格 Ollama 客户端

[![Python](https://img.shields.io/badge/Python-3.14.3-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.x-green.svg)](https://doc.qt.io/qtforpython-6/)
[![License](https://img.shields.io/badge/License-AGPL3.0-yellow.svg)](LICENSE)

</div>

---

## 📖 简介

Ollama Fluent UI 是一款采用 Fluent Design 设计风格的 Ollama 客户端应用程序，提供美观、流畅的用户体验。支持多语言界面、模型管理、对话历史、分屏对话等丰富功能。

## ✨ 特性

### 🌍 多语言支持
支持 **8 种语言** 界面，切换后立即生效：
- 🇨🇳 简体中文 (zh_CN)
- 🇺🇸 English (en_US)
- 🇯🇵 日本語 (ja_JP)
- 🇫🇷 Français (fr_FR)
- 🇩🇪 Deutsch (de_DE)
- 🇪🇸 Español (es_ES)
- 🇷🇺 Русский (ru_RU)
- 🇰🇷 한국어 (ko_KR)

### 💬 聊天功能
- 实时流式对话，打字机效果
- 对话历史记录自动保存
- 支持图像上传与识别
- 分屏对话 - 同时进行两个独立对话
- 上下文限制调节
- 对话内容总结

### 📦 模型管理
- 本地模型列表查看
- 模型详情展示（大小、修改时间）
- 一键删除模型
- 导入本地 GGUF 模型文件

### 📥 模型下载
- 从 Ollama 官方库下载模型
- 支持下载镜像配置
- 实时下载进度显示
- 常用模型快速选择

### 💻 控制台
- Ollama 服务日志实时显示
- 服务启动/停止控制
- 日志清空功能

### ⚙️ 设置
- **主题切换**: 浅色 / 深色 / 跟随系统
- **历史记录管理**: 打开文件夹 / 清空所有历史
- **MCP 服务器配置**: 允许 AI 读写文件
- **下载镜像设置**: 加速模型下载

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Ollama 已安装并运行

### 安装依赖

```bash
pip install PySide6 PySide6-Fluent-Widgets requests
```

或使用 `requirements.txt`（如有）:

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

### 首次使用

1. 确保 Ollama 服务已启动
   - Windows: `ollama serve`
   - macOS/Linux: 通常自动启动

2. 程序会自动检测并连接 Ollama 服务

3. 在聊天界面选择模型，开始对话

### 数据存储位置

程序数据存储在系统应用数据目录：

- **Windows**: `%APPDATA%\OFU\`
  - `TalkHistory/` - 对话历史
  - `Config/` - 配置文件
  - `Templates/` - 提示词模板
  - `Knowledge/` - 知识库

## 📋 功能说明

### 聊天界面

- **模型选择**: 从下拉列表选择要使用的模型
- **刷新模型**: 手动刷新模型列表
- **历史记录**: 查看当前模型的对话历史
- **发送消息**: 点击发送或按 `Ctrl+Enter` 快速发送
- **清空对话**: 清除当前对话内容

### 分屏对话

- 左右两个独立的对话区域
- 可分别发送消息到左侧或右侧
- 支持图像上传
- 独立的历史记录

### 模型管理

- 查看所有已下载的模型
- 显示模型大小和修改日期
- 删除不需要的模型
- 导入本地 GGUF 格式模型

### 模型下载

- 输入模型名称或从预设列表选择
- 支持配置下载镜像加速
- 实时显示下载进度
- 下载完成自动刷新模型列表

### 设置

#### 外观
- 浅色主题
- 深色主题
- 跟随系统

#### 语言
- 8 种语言可选
- 切换后立即生效

#### MCP 服务器
- 启用/禁用 MCP
- 配置服务器地址
- 设置 API 密钥
- 指定允许访问的路径
- 限制最大文件大小

## 🔧 配置说明

### MCP 服务器配置

MCP (Model Context Protocol) 允许 AI 访问本地文件：

```json
{
  "enabled": true,
  "server_url": "http://localhost:8080",
  "api_key": "your-api-key",
  "allowed_paths": ["C:\\Users\\YourName\\Documents"],
  "max_file_size": 10485760
}
```

配置文件位置：`%APPDATA%\OFU\Config\mcp_config.json`

### 语言配置

```json
{
  "language": "zh_CN"
}
```

配置文件位置：`%APPDATA%\OFU\Config\language.json`

## 🛠️ 开发

### 添加新语言

1. 在 `locales/` 目录创建新的翻译文件，如 `it_IT.json`
2. 复制现有翻译文件结构
3. 翻译所有键值
4. 在 `i18n.py` 的 `AVAILABLE_LANGUAGES` 中添加新语言

```python
AVAILABLE_LANGUAGES = {
    'zh_CN': '简体中文',
    'en_US': 'English',
    'it_IT': 'Italiano',  # 新增
    # ...
}
```

### 自定义提示词模板

提示词模板存储在 `%APPDATA%\OFU\Config\prompt_templates.json`

默认模板包括：
- 翻译成英文
- 翻译成中文
- 写周报
- 代码审查
- 解释概念
- 生成摘要
- 头脑风暴
- 润色文章

## 📸 截图

> 添加应用截图展示界面效果

## 🤝 贡献

欢迎贡献代码、翻译或报告问题！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

AGPL-3.0 License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Ollama](https://ollama.ai/) - 本地大模型运行工具
- [PySide6](https://doc.qt.io/qtforpython-6/) - Python Qt 绑定
- [PySide6-Fluent-Widgets](https://github.com/zhiyiYo/PySide6-Fluent-Widgets) - Fluent Design 组件库

## 📬 联系方式

如有问题或建议，请提交 Issue 或联系维护者。

---

<div align="center">

**Ollama Fluent UI** - 让本地 AI 交互更优雅

Made with ❤️ by Contributors

</div>

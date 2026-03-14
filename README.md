# Ollama Fluent UI

<div align="center">

一个使用 PySide6 + PySide6-Fluent-Widgets 实现的 Fluent Design 风格 Ollama 客户端

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.x-green.svg)
![License](https://img.shields.io/badge/License-AGPL--3.0-orange.svg)

</div>

## 📖 简介

**Ollama Fluent UI** 是一款现代化的本地 Ollama 客户端应用，采用 Fluent Design 设计语言，提供优雅的用户界面和流畅的交互体验。支持模型管理、对话历史、多语言切换等功能。

## ✨ 特性

- 🎨 **Fluent Design 风格** - 现代化的界面设计，支持浅色/深色主题
- 💬 **智能对话** - 流式响应，支持图像上传和多轮对话
- 📦 **模型管理** - 查看、删除、导入本地模型
- 📥 **模型下载** - 支持配置下载镜像，加速模型下载
- 📜 **历史记录** - 自动保存对话历史，支持按模型分类管理
- 🌍 **多语言支持** - 支持中文、英文、日文、法文、德文、西班牙文、俄文、韩文
- 💻 **控制台** - 实时查看 Ollama 服务运行日志
- ⚙️ **MCP 服务器** - 支持配置 MCP 服务器，允许 AI 读写文件

## 🖼️ 界面预览

| 聊天界面 | 模型管理 |
|---------|---------|
| ![Chat](https://via.placeholder.com/400x250/0078D4/FFFFFF?text=Chat+Interface) | ![Models](https://via.placeholder.com/400x250/0078D4/FFFFFF?text=Model+Management) |

## 🚀 快速开始

### 下载安装包

| 平台 | 下载链接 |
|------|---------|
| Windows | [📥 下载](https://github.com/Midio1013/OllamaFluentUI/releases/) |

### 使用步骤

1. 下载安装包并安装
2. 确保 Ollama 服务已启动（访问 https://ollama.com 下载安装）
3. 打开应用，在「模型管理」页面刷新模型列表
4. 选择一个模型即可开始对话

## 🚀 自行编译

### 环境要求

- Python 3.8+
- [Ollama](https://ollama.com/) (需预先安装并运行)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

### 打包为可执行文件

项目支持打包为独立的可执行文件，方便分发给用户：

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包程序
pyinstaller --name "Ollama Fluent UI" --windowed --icon icon.ico main.py

# 生成的可执行文件位于 dist/Ollama Fluent UI/ 目录
```

打包后生成独立的可执行文件，用户无需安装 Python 环境即可运行。

> 💡 **提示**：如需创建 NSIS 安装包，可进一步使用 NSIS 工具将生成的可执行文件打包为安装程序。

### 首次使用

1. 确保 Ollama 服务已启动（程序会自动检测并启动）
2. 在「模型管理」页面刷新模型列表
3. 选择一个模型即可开始对话

## 📁 项目结构

```
ollama-fluent/
├── main.py              # 主程序入口
├── i18n.py              # 多语言支持模块
├── create_icon.py       # 图标生成脚本
├── icon.ico             # Windows 图标文件
├── icon.png             # PNG 图标
├── icon.svg             # SVG 矢量图标
├── config/
│   └── language.json    # 语言配置文件
├── locales/             # 翻译文件目录
│   ├── zh_CN.json       # 简体中文
│   ├── en_US.json       # English
│   ├── ja_JP.json       # 日本語
│   ├── fr_FR.json       # Français
│   ├── de_DE.json       # Deutsch
│   ├── es_ES.json       # Español
│   ├── ru_RU.json       # Русский
│   └── ko_KR.json       # 한국어
├── README.md            # 项目说明文档
└── requirements.txt     # Python 依赖列表
```

## 🎯 功能说明

### 聊天界面
- 支持选择不同模型进行对话
- 流式输出，实时显示 AI 回复
- 支持上传图像进行多模态对话
- 自动保存对话历史
- 支持清空对话和总结上下文

### 模型管理
- 查看已安装的模型列表
- 删除不需要的模型
- 导入本地 GGUF 格式模型

### 模型下载
- 直接从 Ollama 官方库下载模型
- 支持配置镜像源加速下载
- 实时显示下载进度

### 控制台
- 启动/停止 Ollama 服务
- 查看服务运行日志
- 实时监控服务状态

### 设置
- 切换应用主题（浅色/深色/跟随系统）
- 配置下载镜像
- 管理对话历史
- 配置 MCP 服务器

## ⌨️ 快捷键

| 快捷键 | 功能 |
|-------|------|
| `Ctrl + Enter` | 发送消息 |

## 🛠️ 开发

### 添加新语言

1. 在 `locales/` 目录下创建新的语言文件，如 `pt_BR.json`
2. 参考现有语言文件的格式
3. 在 `i18n.py` 的 `AVAILABLE_LANGUAGES` 中添加新语言

### 自定义主题

程序使用 PySide6-Fluent-Widgets 的主题系统，可通过设置界面切换主题。

## 📝 许可证

AGPL-3.0 License

## 🙏 致谢

- [Ollama](https://ollama.com/) - 本地大模型运行平台
- [PySide6](https://doc.qt.io/qtforpython/) - Python Qt 绑定
- [PySide6-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - Fluent Design 风格组件库

## 📮 反馈与支持

如有问题或建议，欢迎提交 Issue 或 Pull Request。

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ollama Fluent UI 客户端
使用 PySide6 + PySide6-Fluent-Widgets 实现的 Fluent Design 风格 Ollama 客户端
"""

import os
import sys
import json
import subprocess
import threading
from PySide6.QtCore import Qt, QThread, Signal, QObject, QEvent, QTimer, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QVariantAnimation
from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QWidget, QStackedWidget, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QIcon, QPen, QBrush
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, setTheme, Theme,
    TitleLabel, SubtitleLabel, BodyLabel, StrongBodyLabel,
    CardWidget, PrimaryPushButton, PushButton, ComboBox,
    TextEdit, InfoBar, MessageBox, LineEdit,
    SettingCardGroup, ComboBoxSettingCard, FluentIcon as FIF,
    ProgressBar
)
import requests


class LoadingSpinner(QWidget):
    """旋转加载动画"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(50)  # 降低刷新率，减少 CPU 使用
    
    def rotate(self):
        self.angle = (self.angle + 15) % 360
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.translate(30, 30)
        painter.rotate(self.angle)
        
        # 绘制圆环
        pen = QPen(QColor("#0078D4"), 4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # 绘制 270 度的圆弧（留 90 度缺口）
        painter.drawArc(-25, -25, 50, 50, 0, -270 * 16)


class LoadingDialog(QWidget):
    """启动加载对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 250)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        
        # 卡片
        card = CardWidget(self)
        card.setBorderRadius(20)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(16)
        
        # 旋转动画
        self.spinner = LoadingSpinner(self)
        card_layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        
        # 标题
        title = StrongBodyLabel("Ollama Fluent UI", self)
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)
        
        # 状态标签
        self.status_label = BodyLabel("正在启动 Ollama 服务...", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888888;")
        card_layout.addWidget(self.status_label)
        
        layout.addWidget(card)
    
    def set_status(self, text):
        """设置状态文本"""
        self.status_label.setText(text)


class OllamaServiceThread(QThread):
    """Ollama 服务启动线程"""
    started = Signal()
    error = Signal(str)
    output = Signal(str)
    status_update = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self._stop_flag = False
        self.already_running = False
    
    def __del__(self):
        """析构函数，确保线程停止"""
        self.stop()
        self.wait()

    def run(self):
        try:
            # 检查是否已在运行
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    self.status_update.emit("✅ Ollama 服务已在运行")
                    self.output.emit("✅ Ollama 服务已在运行")
                    self.already_running = True
                    self.started.emit()
                    # 继续监控服务
                    self.monitor_existing_service()
                    return
            except:
                pass

            # 启动 Ollama 服务
            self.process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                universal_newlines=True,
                bufsize=1
            )

            self.status_update.emit("🚀 正在启动 Ollama 服务...")
            self.output.emit("🚀 正在启动 Ollama 服务...")

            # 读取输出
            import time
            start_time = time.time()
            log_count = 0
            while not self._stop_flag:
                if self.process.poll() is not None:
                    # 进程已退出
                    self.error.emit("服务启动失败")
                    return

                # 非阻塞读取输出（限制日志数量，避免 UI 卡顿）
                try:
                    line = self.process.stdout.readline()
                    if line and log_count < 30:  # 只输出前 30 条日志
                        self.output.emit(line.strip())
                        log_count += 1
                except:
                    pass

                # 检查服务是否就绪
                if time.time() - start_time > 30:
                    self.error.emit("Ollama 服务启动超时")
                    return

                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=2)
                    if response.status_code == 200:
                        self.output.emit("✅ Ollama 服务已就绪")
                        self.started.emit()
                        # 继续读取输出（限制日志数量）
                        log_count = 0
                        while not self._stop_flag:
                            if self.process.poll() is not None:
                                return
                            try:
                                line = self.process.stdout.readline()
                                if line and log_count < 10:  # 只输出 10 条运行日志
                                    self.output.emit(line.strip())
                                    log_count += 1
                            except:
                                pass
                            time.sleep(1)  # 降低检查频率到 1 秒
                        return
                except:
                    pass

                time.sleep(1)  # 降低检查频率到 1 秒
            
        except FileNotFoundError:
            self.error.emit("未找到 Ollama，请先安装 Ollama")
            self.output.emit("❌ 未找到 Ollama，请先安装 Ollama")
        except Exception as e:
            self.error.emit(f"启动失败：{e}")
            self.output.emit(f"❌ 启动失败：{e}")
    
    def monitor_existing_service(self):
        """监控已存在的服务"""
        import time
        while not self._stop_flag:
            time.sleep(1)
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code != 200:
                    self.output.emit("⚠️ Ollama 服务已停止")
                    return
            except:
                self.output.emit("⚠️ Ollama 服务已停止")
                return
    
    def stop(self):
        """停止线程"""
        self._stop_flag = True


class ChatBubble(CardWidget):
    """聊天气泡"""
    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role
        self.content = content
        
        # 设置边框半径
        self.setBorderRadius(12)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # 角色标签
        role_text = "👤 你" if role == 'user' else "🤖 AI"
        role_label = BodyLabel(role_text, self)
        role_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(role_label)
        
        # 消息内容
        self.content_label = BodyLabel(content, self)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.content_label)
        
        # 设置背景色
        if role == 'user':
            self.setStyleSheet("""
                CardWidget {
                    background-color: #0078D4;
                }
                CardWidget BodyLabel {
                    color: #FFFFFF;
                }
            """)
            role_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px;")
            self.content_label.setStyleSheet("color: #FFFFFF;")
        else:
            self.setStyleSheet("""
                CardWidget {
                    background-color: #F3F3F3;
                }
            """)


class ChatThread(QThread):
    """聊天线程 - 处理流式响应"""
    message_chunk = Signal(str)
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, api_url: str, model: str, messages: list):
        super().__init__()
        self.api_url = api_url
        self.model = model
        self.messages = messages
    
    def run(self):
        try:
            payload = {
                "model": self.model,
                "messages": self.messages,
                "stream": True
            }
            
            response = requests.post(
                f"{self.api_url}/api/chat",
                json=payload,
                stream=True,
                timeout=120
            )
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'message' in data:
                        content = data['message'].get('content', '')
                        if content:
                            self.message_chunk.emit(content)
                    if data.get('done', False):
                        break
            
            self.finished.emit()
            
        except requests.exceptions.ConnectionError:
            self.error.emit("无法连接到 Ollama")
        except Exception as e:
            self.error.emit(f"发生错误：{e}")


class ModelRefreshThread(QThread):
    """后台刷新模型线程"""
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, api_url, parent=None):
        super().__init__(parent)
        self.api_url = api_url
        self._abort = False
    
    def __del__(self):
        """析构函数，确保线程停止"""
        self._abort = True
        self.wait()

    def run(self):
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                if not self._abort:
                    self.finished.emit(models)
            else:
                if not self._abort:
                    self.error.emit(f"HTTP {response.status_code}")
        except Exception as e:
            if not self._abort:
                self.error.emit(str(e))
    
    def abort(self):
        """中止线程"""
        self._abort = True


class ChatInterface(QWidget):
    """聊天界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatInterface")

        self.api_url = "http://localhost:11434"
        self.current_model = ""
        self.messages = []
        self.current_assistant_bubble = None
        self.is_ollama_connected = False
        self.monitor_timer = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 顶部工具栏
        toolbar = CardWidget(self)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        toolbar_layout.addWidget(BodyLabel("📦 模型:", self))
        self.model_combo = ComboBox(self)
        self.model_combo.setFixedWidth(200)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        toolbar_layout.addWidget(self.model_combo)
        
        toolbar_layout.addStretch()
        
        self.refresh_btn = PushButton("🔄 刷新", self)
        self.refresh_btn.clicked.connect(self.refresh_models)
        toolbar_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(toolbar)
        
        # 聊天区域
        self.chat_scroll = QScrollArea(self)
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll)
        
        # 输入区域
        input_card = CardWidget(self)
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(12)
        
        self.input_edit = TextEdit(self)
        self.input_edit.setPlaceholderText("输入消息... (Ctrl+Enter 发送)")
        self.input_edit.setFixedHeight(80)
        self.input_edit.installEventFilter(self)
        input_layout.addWidget(self.input_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.send_btn = PrimaryPushButton("📤 发送", self)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setDisabled(True)
        btn_layout.addWidget(self.send_btn)
        
        self.clear_btn = PushButton("🗑️ 清空", self)
        self.clear_btn.clicked.connect(self.clear_chat)
        btn_layout.addWidget(self.clear_btn)
        
        input_layout.addLayout(btn_layout)
        layout.addWidget(input_card)
        
        # 状态标签
        self.status_label = BodyLabel("", self)
        self.status_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.status_label)

        # 延迟刷新模型，确保 UI 已完全初始化（减少延迟）
        # QTimer.singleShot(300, self.refresh_models)

    def closeEvent(self, event):
        """关闭窗口时停止监控"""
        if self.monitor_timer:
            self.monitor_timer.stop()
            self.monitor_timer.deleteLater()
        # 停止刷新线程
        if hasattr(self, 'refresh_thread') and self.refresh_thread:
            self.refresh_thread.abort()
        event.accept()
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理 Ctrl+Enter 发送"""
        if obj == self.input_edit and event.type() == QEvent.KeyPress:
            key_event = event
            if key_event.key() == Qt.Key_Return and key_event.modifiers() == Qt.ControlModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def on_model_changed(self, model):
        """模型改变"""
        self.current_model = model
        self.send_btn.setEnabled(bool(model))
    
    def refresh_models(self, show_info=True):
        """刷新模型列表（异步）"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳ 加载中...")
        
        # 停止之前的刷新线程
        if hasattr(self, 'refresh_thread') and self.refresh_thread:
            self.refresh_thread.abort()
            self.refresh_thread.wait(1000)
            self.refresh_thread.deleteLater()
        
        # 使用后台线程刷新，避免阻塞 UI
        self.refresh_thread = ModelRefreshThread(self.api_url, self)
        self.refresh_thread.finished.connect(
            lambda models: self._on_models_loaded(models, show_info)
        )
        self.refresh_thread.error.connect(self._on_refresh_error)
        self.refresh_thread.start()
    
    def _on_models_loaded(self, models, show_info):
        """模型加载完成"""
        self.model_combo.clear()
        if models:
            self.model_combo.addItems(models)
            self.current_model = models[0]
            self.send_btn.setEnabled(True)
            self.is_ollama_connected = True
            self.status_label.setText("✅ Ollama 已连接")
            self.status_label.setStyleSheet("color: #107C10;")
            if show_info:
                InfoBar.success("成功", f"找到 {len(models)} 个模型", parent=self)
            
            # 启动连接监控（每 15 秒检查一次）
            if not self.monitor_timer:
                self.monitor_timer = QTimer()
                self.monitor_timer.setSingleShot(True)
                self.monitor_timer.timeout.connect(self.check_connection)
                self.monitor_timer.start(15000)
        else:
            if show_info:
                InfoBar.warning("警告", "没有找到任何模型", parent=self)
        
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")
    
    def _on_refresh_error(self, error):
        """刷新错误"""
        if "Connection" in error or "connect" in error.lower():
            self._show_ollama_not_found()
        else:
            InfoBar.error("错误", f"发生错误：{error}", parent=self)
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")

    def _show_ollama_not_found(self):
        """显示 Ollama 未找到的提示"""
        self.status_label.setText("❌ Ollama 未运行")
        self.status_label.setStyleSheet("color: #D13438;")
        self.is_ollama_connected = False
        InfoBar.error(
            "⚠️ 未检测到 Ollama",
            "请确保 Ollama 已安装并正在运行\n访问 https://ollama.com/download 下载",
            parent=self,
            duration=10000
        )

    def on_ollama_connected(self):
        """Ollama 已连接"""
        self.is_ollama_connected = True
        self.status_label.setText("✅ Ollama 已连接")
        self.status_label.setStyleSheet("color: #107C10;")
        self.refresh_models(show_info=False)

    def on_ollama_disconnected(self):
        """Ollama 已断开连接"""
        self.is_ollama_connected = False
        self.status_label.setText("❌ Ollama 已断开连接")
        self.status_label.setStyleSheet("color: #D13438;")
        self.model_combo.clear()
        self.send_btn.setEnabled(False)
        InfoBar.warning("警告", "Ollama 服务已断开连接", parent=self, duration=5000)

    def check_connection(self):
        """检查 Ollama 连接状态"""
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=2)
            if response.status_code == 200:
                if not self.is_ollama_connected:
                    self.on_ollama_connected()
            else:
                if self.is_ollama_connected:
                    self.on_ollama_disconnected()
        except:
            if self.is_ollama_connected:
                self.on_ollama_disconnected()
        finally:
            # 继续监控
            if self.monitor_timer and self.monitor_timer.isActive():
                self.monitor_timer.start(15000)

    def add_message(self, role: str, content: str):
        """添加消息"""
        bubble = ChatBubble(role, content, self)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )
    
    def send_message(self):
        """发送消息"""
        content = self.input_edit.toPlainText().strip()
        if not content:
            return
        
        if not self.current_model:
            InfoBar.warning("警告", "请先选择一个模型", parent=self)
            return
        
        # 添加用户消息
        self.add_message("user", content)
        self.messages.append({"role": "user", "content": content})
        self.input_edit.clear()
        
        # 禁用输入
        self.input_edit.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.status_label.setText("⏳ AI 正在思考...")
        
        # 创建助手消息气泡（初始为空）
        assistant_bubble = ChatBubble("assistant", "", self)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, assistant_bubble)
        self.current_assistant_bubble = assistant_bubble
        
        # 启动流式请求线程
        self.chat_thread = ChatThread(
            self.api_url, 
            self.current_model, 
            self.messages.copy()
        )
        self.chat_thread.message_chunk.connect(
            lambda chunk: self.update_assistant_message(chunk)
        )
        self.chat_thread.finished.connect(self.on_chat_finished)
        self.chat_thread.error.connect(self.on_chat_error)
        self.chat_thread.start()
    
    def update_assistant_message(self, chunk: str):
        """更新助手消息"""
        if self.current_assistant_bubble:
            self.current_assistant_bubble.content += chunk
            self.current_assistant_bubble.content_label.setText(
                self.current_assistant_bubble.content
            )
            self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            )
    
    def on_chat_finished(self):
        """聊天完成"""
        self.input_edit.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.status_label.setText("")
        
        # 保存最后一条助手消息
        if self.current_assistant_bubble:
            self.messages.append({
                "role": "assistant", 
                "content": self.current_assistant_bubble.content
            })
            self.current_assistant_bubble = None
        
        self.input_edit.setFocus()
    
    def on_chat_error(self, error: str):
        """聊天错误"""
        self.input_edit.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.status_label.setText("")
        InfoBar.error("错误", error, parent=self)
    
    def clear_chat(self):
        """清空聊天"""
        self.messages.clear()
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class ModelCard(CardWidget):
    """模型卡片"""
    def __init__(self, model_info: dict, parent=None):
        super().__init__(parent)
        self.model_info = model_info
        self.api_url = "http://localhost:11434"
        self.parent_interface = parent
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 模型名称
        name = model_info.get('name', 'Unknown')
        name_label = StrongBodyLabel(name, self)
        layout.addWidget(name_label)
        
        # 模型信息
        info_layout = QHBoxLayout()
        
        # 大小
        size = model_info.get('size', 0)
        size_gb = size / (1024 ** 3)
        size_label = BodyLabel(f"📦 {size_gb:.2f} GB", self)
        size_label.setStyleSheet("color: #888888;")
        info_layout.addWidget(size_label)
        
        # 修改时间
        modified = model_info.get('modified_at', '')
        if modified:
            date = modified.split('T')[0]
            date_label = BodyLabel(f"📅 {date}", self)
            date_label.setStyleSheet("color: #888888;")
            info_layout.addWidget(date_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.delete_btn = PushButton("🗑️ 删除", self)
        self.delete_btn.setStyleSheet("color: #D13438;")
        self.delete_btn.clicked.connect(self.delete_model)
        btn_layout.addWidget(self.delete_btn)
        
        layout.addLayout(btn_layout)
    
    def delete_model(self):
        """删除模型"""
        name = self.model_info.get('name', '')
        
        box = MessageBox("确认删除", f"确定要删除模型 {name} 吗？", self.window())
        if box.exec():
            try:
                response = requests.delete(
                    f"{self.api_url}/api/delete",
                    json={"name": name},
                    timeout=30
                )
                if response.status_code == 200:
                    InfoBar.success("成功", f"已删除 {name}", parent=self.window())
                    if self.parent_interface:
                        self.parent_interface.refresh_models()
                else:
                    InfoBar.error("错误", f"删除失败：{response.status_code}", parent=self.window())
            except Exception as e:
                InfoBar.error("错误", f"删除失败：{e}", parent=self.window())


class ModelsInterface(QWidget):
    """模型管理界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModelsInterface")
        
        self.api_url = "http://localhost:11434"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题
        title_card = CardWidget(self)
        title_layout = QVBoxLayout(title_card)
        title_layout.setContentsMargins(20, 20, 20, 20)
        
        title = TitleLabel("📦 模型管理", self)
        title_layout.addWidget(title)
        
        subtitle = SubtitleLabel("管理本地 Ollama 模型", self)
        subtitle.setStyleSheet("color: #888888;")
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_card)
        
        # 刷新按钮
        self.refresh_btn = PrimaryPushButton("🔄 刷新模型列表", self)
        self.refresh_btn.clicked.connect(self.refresh_models)
        layout.addWidget(self.refresh_btn)
        
        # 模型列表
        self.models_scroll = QScrollArea(self)
        self.models_scroll.setWidgetResizable(True)
        self.models_scroll.setFrameShape(QFrame.NoFrame)
        
        self.models_container = QWidget()
        self.models_layout = QVBoxLayout(self.models_container)
        self.models_layout.setContentsMargins(0, 0, 0, 0)
        self.models_layout.setSpacing(12)
        
        self.models_scroll.setWidget(self.models_container)
        layout.addWidget(self.models_scroll)
        
        # 状态
        self.status_label = BodyLabel("", self)
        self.status_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.status_label)
    
    def closeEvent(self, event):
        """关闭窗口时停止刷新"""
        if hasattr(self, 'refresh_thread') and self.refresh_thread:
            self.refresh_thread.abort()
        event.accept()
    
    def refresh_models(self):
        """刷新模型列表（异步）"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳ 加载中...")

        # 清空现有模型卡片
        while self.models_layout.count():
            item = self.models_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 停止之前的刷新线程
        if hasattr(self, 'refresh_thread') and self.refresh_thread:
            self.refresh_thread.abort()
            self.refresh_thread.wait(1000)
            self.refresh_thread.deleteLater()

        # 使用后台线程刷新，避免阻塞 UI
        self.refresh_thread = ModelRefreshThread(self.api_url, self)
        self.refresh_thread.finished.connect(self._on_models_loaded)
        self.refresh_thread.error.connect(self._on_refresh_error)
        self.refresh_thread.start()
    
    def _on_models_loaded(self, models_data):
        """模型加载完成"""
        # 重新获取完整模型信息（包含 size 等）
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                
                if models:
                    for model in models:
                        card = ModelCard(model, self)
                        self.models_layout.addWidget(card)

                    self.models_layout.addStretch()
                    self.status_label.setText(f"✅ 共 {len(models)} 个模型")
                    InfoBar.success("成功", f"找到 {len(models)} 个模型", parent=self)
                else:
                    self.status_label.setText("⚠️ 没有找到任何模型")
        except Exception as e:
            self.status_label.setText(f"❌ 错误：{e}")
        
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新模型列表")
    
    def _on_refresh_error(self, error):
        """刷新错误"""
        self.status_label.setText(f"❌ {error}")
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新模型列表")

    def _show_ollama_not_found(self):
        """显示 Ollama 未找到的提示"""
        self.status_label.setText("❌ Ollama 未运行")
        InfoBar.error(
            "⚠️ 未检测到 Ollama",
            "请确保 Ollama 已安装并正在运行\n访问 https://ollama.com/download 下载",
            parent=self,
            duration=10000
        )


class ConsoleInterface(QWidget):
    """控制台界面 - 显示 Ollama 服务输出"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConsoleInterface")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题
        title_card = CardWidget(self)
        title_layout = QVBoxLayout(title_card)
        title_layout.setContentsMargins(20, 20, 20, 20)
        
        title = TitleLabel("💻 控制台", self)
        title_layout.addWidget(title)
        
        subtitle = SubtitleLabel("Ollama 服务运行日志", self)
        subtitle.setStyleSheet("color: #888888;")
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_card)
        
        # 控制按钮
        btn_card = CardWidget(self)
        btn_layout = QHBoxLayout(btn_card)
        btn_layout.setContentsMargins(16, 12, 16, 12)
        
        self.start_btn = PrimaryPushButton("▶️ 启动服务", self)
        self.start_btn.clicked.connect(self.start_service)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = PushButton("⏹️ 停止服务", self)
        self.stop_btn.clicked.connect(self.stop_service)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addStretch()
        
        self.clear_btn = PushButton("🗑️ 清空日志", self)
        self.clear_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addWidget(btn_card)
        
        # 日志显示区
        self.log_edit = TextEdit(self)
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("等待服务启动...")
        self.log_edit.setStyleSheet("""
            TextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
        """)
        layout.addWidget(self.log_edit)
        
        # 状态
        self.status_label = BodyLabel("● 未连接", self)
        self.status_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.status_label)
        
        # 服务线程引用
        self.service_thread = None
    
    def set_service_thread(self, thread):
        """设置服务线程"""
        self.service_thread = thread
        if thread:
            thread.output.connect(self.append_log)
    
    def append_log(self, text):
        """添加日志"""
        from PySide6.QtCore import QTime
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        
        # 限制日志行数，防止内存泄漏
        doc = self.log_edit.document()
        if doc.blockCount() > 500:
            # 删除前 100 行
            cursor = self.log_edit.textCursor()
            cursor.movePosition(cursor.Start)
            for _ in range(100):
                cursor.select(cursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # 删除换行符
        
        # 批量更新时禁用重绘，提高性能
        self.log_edit.setUpdatesEnabled(False)
        self.log_edit.append(f"[{timestamp}] {text}")
        # 自动滚动到底部
        scrollbar = self.log_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.log_edit.setUpdatesEnabled(True)
        self.log_edit.repaint()  # 强制重绘
    
    def clear_log(self):
        """清空日志"""
        self.log_edit.clear()
    
    def start_service(self):
        """启动服务"""
        if self.service_thread and not self.service_thread.isRunning():
            self.append_log("正在启动 Ollama 服务...")
            self.service_thread.start()
        elif self.service_thread and self.service_thread.isRunning():
            self.append_log("ℹ️ 服务已在运行中")

    def stop_service(self):
        """停止服务"""
        self.append_log("正在停止 Ollama 服务...")
        
        # 使用 taskkill 结束 ollama 进程
        import subprocess
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "ollama.exe"],
                capture_output=True,
                timeout=5
            )
            self.append_log("⏹️ Ollama 服务已停止")
            self.status_label.setText("● 已停止")
            self.status_label.setStyleSheet("color: #888888;")
        except Exception as e:
            self.append_log(f"停止失败：{e}")
        
        # 停止监控线程
        if self.service_thread:
            self.service_thread.stop()

    def set_connected(self):
        """设置已连接状态"""
        self.status_label.setText("● 运行中")
        self.status_label.setStyleSheet("color: #107C10;")

    def set_disconnected(self):
        """设置未连接状态"""
        self.status_label.setText("● 未连接")
        self.status_label.setStyleSheet("color: #888888;")


class DownloadInterface(QWidget):
    """模型下载界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DownloadInterface")
        self.parent_window = parent
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题
        title_card = CardWidget(self)
        title_layout = QVBoxLayout(title_card)
        title_layout.setContentsMargins(20, 20, 20, 20)
        
        title = TitleLabel("📥 模型下载", self)
        title_layout.addWidget(title)
        
        subtitle = SubtitleLabel("从 Ollama 官方库下载模型", self)
        subtitle.setStyleSheet("color: #888888;")
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_card)
        
        # 搜索区域
        search_card = CardWidget(self)
        search_layout = QVBoxLayout(search_card)
        search_layout.setContentsMargins(16, 16, 16, 16)
        search_layout.setSpacing(12)
        
        # 模型名称输入
        input_layout = QHBoxLayout()
        input_layout.addWidget(BodyLabel("模型名称:", self))
        self.model_name_edit = ComboBox(self)
        self.model_name_edit.setPlaceholderText("输入模型名称，如 llama3.1:8b")
        self.model_name_edit.addItems([
            "llama3.1:8b", "llama3.1:70b", "qwen2.5:7b", "qwen2.5:72b",
            "deepseek-r1:8b", "deepseek-r1:70b", "gemma2:9b", "mistral:7b",
            "nomic-embed-text", "mxbai-embed-large"
        ])
        self.model_name_edit.setFixedWidth(300)
        input_layout.addWidget(self.model_name_edit)
        input_layout.addStretch()
        layout.addLayout(input_layout)
        
        # 下载按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.download_btn = PrimaryPushButton("📥 下载", self)
        self.download_btn.clicked.connect(self.download_model)
        btn_layout.addWidget(self.download_btn)
        
        self.cancel_btn = PushButton("❌ 取消", self)
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.cancel_btn)
        
        search_layout.addLayout(btn_layout)
        layout.addWidget(search_card)
        
        # 进度显示
        progress_card = CardWidget(self)
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(16, 16, 16, 16)
        progress_layout.setSpacing(12)
        
        self.status_label = BodyLabel("等待下载...", self)
        self.status_label.setStyleSheet("color: #888888;")
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.speed_label = BodyLabel("", self)
        self.speed_label.setStyleSheet("color: #888888; font-size: 12px;")
        progress_layout.addWidget(self.speed_label)
        
        layout.addWidget(progress_card)
        
        # 已下载模型列表
        list_card = CardWidget(self)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(16, 16, 16, 16)
        
        list_title = StrongBodyLabel("已下载的模型", self)
        list_layout.addWidget(list_title)
        
        self.model_list = ComboBox(self)
        self.model_list.setPlaceholderText("选择已下载的模型")
        self.model_list.currentTextChanged.connect(self.on_model_selected)
        list_layout.addWidget(self.model_list)
        
        layout.addWidget(list_card)
        
        # 下载进程
        self.download_process = None
        self.is_downloading = False
        self.downloading_model = None  # 保存正在下载的模型名称
        self._was_cancelled = False  # 标记是否被取消
        
        # 刷新模型列表
        QTimer.singleShot(500, self.refresh_model_list)
    
    def refresh_model_list(self):
        """刷新已下载模型列表"""
        # 下载中时不刷新，避免干扰
        if self.is_downloading:
            return
        
        # 暂时断开信号，避免 clear() 和 addItems() 触发 on_model_selected
        self.model_list.currentTextChanged.disconnect(self.on_model_selected)
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m.get('name', '') for m in response.json().get('models', [])]
                current_text = self.model_name_edit.currentText()  # 保存当前选择的模型
                self.model_list.clear()
                self.model_list.addItems(models)
                # 恢复信号连接
                self.model_list.currentTextChanged.connect(self.on_model_selected)
                # 恢复之前的选择
                if current_text in models:
                    self.model_list.setCurrentText(current_text)
        except:
            pass
        finally:
            # 确保信号连接恢复
            try:
                self.model_list.currentTextChanged.connect(self.on_model_selected)
            except:
                pass
    
    def on_model_selected(self, name):
        """选择模型"""
        # 下载中时不允许修改
        if self.is_downloading:
            return
        if name:
            self.model_name_edit.setCurrentText(name)
    
    def download_model(self):
        """下载模型"""
        model_name = self.model_name_edit.currentText().strip()
        if not model_name:
            InfoBar.warning("警告", "请输入模型名称", parent=self)
            return
        
        # 保存当前模型名称，防止被修改
        self.downloading_model = model_name
        
        # 获取镜像设置
        mirror_url = ""
        if self.parent_window and hasattr(self.parent_window, 'settings_interface'):
            mirror_url = self.parent_window.settings_interface.mirror_edit.text().strip()
        
        self.is_downloading = True
        self._was_cancelled = False
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText(f"正在下载 {model_name}...")
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        
        # 设置环境变量
        env = os.environ.copy()
        if mirror_url:
            env["OLLAMA_MIRROR"] = mirror_url
            self.status_label.setText(f"正在下载 {model_name}... (镜像：{mirror_url})")
        
        # 启动下载进程
        self.download_process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
            universal_newlines=True,
            encoding='utf-8',
            env=env
        )
        
        # 启动监控线程
        self.monitor_thread = DownloadMonitorThread(self.download_process, model_name)
        self.monitor_thread.progress.connect(self.update_progress)
        self.monitor_thread.finished.connect(self.download_finished)
        self.monitor_thread.error.connect(self.download_error)
        self.monitor_thread.start()
    
    def cancel_download(self):
        """取消下载"""
        if self.download_process and self.is_downloading:
            self._was_cancelled = True  # 标记为取消
            self.is_downloading = False  # 先设置标志，防止重复触发
            self.download_process.terminate()
            self.download_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.status_label.setText("下载已取消")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            # 清空进度显示
            if hasattr(self, 'speed_label'):
                self.speed_label.setText("")
            InfoBar.warning("警告", "下载已取消", parent=self, duration=3000)
    
    def update_progress(self, progress_data):
        """更新进度"""
        # 下载已取消或完成，忽略后续进度更新
        if not self.is_downloading:
            return
        
        status = progress_data.get('status', '')
        total = progress_data.get('total', 0)
        completed = progress_data.get('completed', 0)
        percent = progress_data.get('percent', 0)

        # 有百分比时直接显示
        if percent > 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percent)
            self.status_label.setText(status)
        elif total > 0 and completed > 0:
            # 有 total 和 completed 时计算百分比
            p = int((completed / total) * 100)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(p)
            self.status_label.setText(f"{status} - {p}%")
        else:
            # 没有具体进度时，使用无限循环进度条
            self.progress_bar.setRange(0, 0)
            if status:
                self.status_label.setText(status)
    
    def download_finished(self):
        """下载完成"""
        # 如果是取消下载，不显示完成提示
        if self._was_cancelled:
            self._was_cancelled = False
            self.is_downloading = False
            self.download_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            # 重置进度条
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            return

        # 检查是否有错误（防止错误后还显示成功）
        if hasattr(self.monitor_thread, '_has_error') and self.monitor_thread._has_error:
            return

        self.is_downloading = False
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_bar.setRange(0, 100)
        self.status_label.setText("✅ 下载完成")
        self.speed_label.setText("")

        # 恢复之前下载的模型名称
        if hasattr(self, 'downloading_model') and self.downloading_model:
            self.model_name_edit.setCurrentText(self.downloading_model)
            self.downloading_model = None

        InfoBar.success("成功", "模型下载完成", parent=self, duration=3000)
        # 延迟刷新模型列表
        QTimer.singleShot(1000, self.refresh_model_list)

    def download_error(self, error):
        """下载错误"""
        # 如果是取消下载，不显示错误提示
        if self._was_cancelled:
            self._was_cancelled = False
            self.is_downloading = False
            self.download_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            # 重置进度条
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            return
        
        # 标记为有错误，防止 download_finished 再次触发
        if hasattr(self.monitor_thread, '_has_error'):
            self.monitor_thread._has_error = True
        
        self.is_downloading = False
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"❌ {error}")
        
        # 恢复之前下载的模型名称
        if hasattr(self, 'downloading_model') and self.downloading_model:
            self.model_name_edit.setCurrentText(self.downloading_model)
            self.downloading_model = None
        
        InfoBar.error("错误", error, parent=self, duration=3000)


class DownloadMonitorThread(QThread):
    """下载监控线程"""
    progress = Signal(dict)
    finished = Signal()
    error = Signal(str)

    def __init__(self, process, model_name):
        super().__init__()
        self.process = process
        self.model_name = model_name
        self._has_error = False

    def run(self):
        import re
        try:
            for line in self.process.stdout:
                line = line.strip()
                if not line:
                    continue

                # 解析 Ollama 输出格式：
                # pulling manifest
                # pulling 2bada8a74506: 100% ▕████ 4.7 GB
                # pulling 66b9ea09bd5b: 100% ▕████ 68 B
                # verifying sha256 digest
                # writing manifest
                # success

                # 尝试解析进度行（有百分比和大小）
                # 格式：pulling xxx: 87% ▕████ 4.1 GB/4.7 GB 或 pulling xxx: 100% ▕████ 4.7 GB
                progress_match = re.match(
                    r'pulling\s+\S+:\s+(\d+)%.*?([\d.]+\s*[KMG]?B)(?:/([\d.]+\s*[KMG]?B))?',
                    line
                )

                if progress_match:
                    percent = int(progress_match.group(1))
                    completed_str = progress_match.group(2)
                    total_str = progress_match.group(3)  # 可能为 None
                    
                    # 解析字节数
                    completed = self.parse_size(completed_str)
                    total = self.parse_size(total_str) if total_str else completed
                    
                    self.progress.emit({
                        'status': f'pulling - {percent}%',
                        'total': total,
                        'completed': completed,
                        'percent': percent
                    })
                elif line.startswith('pulling'):
                    self.progress.emit({'status': line})
                elif line.startswith('verifying'):
                    self.progress.emit({'status': line})
                elif line.startswith('writing'):
                    self.progress.emit({'status': line})
                elif line.startswith('success'):
                    self.progress.emit({'status': '✅ ' + line})
                else:
                    self.progress.emit({'status': line})

            # 检查退出码
            if self.process.returncode == 0:
                self.finished.emit()
            else:
                self._has_error = True
                self.error.emit(f"下载失败 (退出码：{self.process.returncode})")
        except Exception as e:
            self._has_error = True
            self.error.emit(str(e))
    
    def parse_size(self, size_str):
        """解析字节数，如 '4.1 GB' -> 4402341478, '687 B' -> 687"""
        size_str = size_str.strip().upper()
        
        # 处理 'B' 结尾（字节）
        if size_str.endswith(' B'):
            try:
                return int(float(size_str[:-2].strip()))
            except:
                return 0
        
        multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
        
        for suffix, mult in multipliers.items():
            if suffix in size_str:
                try:
                    num = float(size_str.replace(suffix, '').strip())
                    return int(num * mult)
                except:
                    return 0
        
        # 没有单位，直接返回数字
        try:
            return float(size_str)
        except:
            return 0


class SettingsInterface(QWidget):
    """设置界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsInterface")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题
        title_card = CardWidget(self)
        title_layout = QVBoxLayout(title_card)
        title_layout.setContentsMargins(20, 20, 20, 20)
        
        title = TitleLabel("⚙️ 设置", self)
        title_layout.addWidget(title)
        
        subtitle = SubtitleLabel("自定义 Ollama 客户端", self)
        subtitle.setStyleSheet("color: #888888;")
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_card)

        # 下载设置组
        download_group = SettingCardGroup("下载设置", self)

        # 下载镜像
        mirror_card = CardWidget(self)
        mirror_card.setMinimumHeight(140)
        mirror_card_layout = QVBoxLayout(mirror_card)
        mirror_card_layout.setContentsMargins(16, 16, 16, 16)
        mirror_card_layout.setSpacing(12)
        
        mirror_title_layout = QHBoxLayout()
        mirror_icon = BodyLabel("🌐", self)
        mirror_icon.setStyleSheet("font-size: 18px;")
        mirror_title_layout.addWidget(mirror_icon)
        mirror_title_layout.addWidget(BodyLabel("下载镜像", self))
        mirror_title_layout.addStretch()
        mirror_card_layout.addLayout(mirror_title_layout)
        
        mirror_card_layout.addWidget(BodyLabel("模型下载镜像地址（可选）", self))
        
        self.mirror_edit = LineEdit(self)
        self.mirror_edit.setText("")
        self.mirror_edit.setPlaceholderText("如：https://ollama.1panel.live/")
        self.mirror_edit.setFixedHeight(36)
        mirror_card_layout.addWidget(self.mirror_edit)
        
        mirror_card_layout.addStretch()
        
        download_group.addSettingCard(mirror_card)

        layout.addWidget(download_group)

        # 主题设置组
        theme_group = SettingCardGroup("外观", self)

        # 主题切换
        from qfluentwidgets import ComboBox
        self.theme_label = BodyLabel("🎨 主题:", self)

        self.theme_combo = ComboBox(self)
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()

        theme_card = CardWidget(self)
        theme_card.setMinimumHeight(140)
        theme_card_layout = QVBoxLayout(theme_card)
        theme_card_layout.setContentsMargins(16, 16, 16, 16)
        theme_card_layout.setSpacing(12)
        theme_card_layout.addWidget(BodyLabel("🎨 应用主题"))
        theme_card_layout.addWidget(BodyLabel("更改应用程序的外观"))
        theme_card_layout.addLayout(theme_layout)
        theme_card_layout.addStretch()

        theme_group.addSettingCard(theme_card)
        layout.addWidget(theme_group)
        layout.addStretch()
    
    def on_theme_changed(self, index):
        """主题改变"""
        if index == 0:
            setTheme(Theme.LIGHT)
        elif index == 1:
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.AUTO)


class OllamaWindow(FluentWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ollama Fluent UI")
        self.setMinimumSize(920, 650)
        self.resize(920, 650)

        setTheme(Theme.AUTO)

        # 创建界面（延迟初始化，先显示加载动画）
        self.chat_interface = None
        self.models_interface = None
        self.console_interface = None
        self.download_interface = None
        self.settings_interface = None

        # 显示启动画面（置顶）
        self.loading_dialog = LoadingDialog()
        self.loading_dialog.show()
        self.loading_dialog.activateWindow()
        self.loading_dialog.raise_()
        self.loading_dialog.set_status("🚀 正在初始化...")

        # 立即初始化界面（不延迟）
        self._init_interfaces()
    
    def _init_interfaces(self):
        """延迟初始化界面"""
        try:
            self.loading_dialog.set_status("📦 加载界面...")

            # 分阶段创建界面，减少卡顿
            # 第一阶段：创建核心界面（聊天、模型管理）
            self.chat_interface = ChatInterface(self)
            self.models_interface = ModelsInterface(self)
            
            # 添加到导航
            self.addSubInterface(
                self.chat_interface,
                FIF.CHAT,
                "聊天",
                NavigationItemPosition.SCROLL
            )
            self.addSubInterface(
                self.models_interface,
                FIF.FOLDER,
                "模型管理",
                NavigationItemPosition.SCROLL
            )
            
            # 确保页面显示
            self.stackedWidget.setCurrentIndex(0)
            for i in range(self.stackedWidget.count()):
                widget = self.stackedWidget.widget(i)
                if widget:
                    widget.show()

            # 第二阶段：延迟创建其他界面（控制台、下载、设置）
            QTimer.singleShot(100, self._init_remaining_interfaces)
            
        except Exception as e:
            print(f"Error initializing interfaces: {e}")
            import traceback
            traceback.print_exc()
            self.loading_dialog.close()
            InfoBar.error("错误", f"初始化失败：{e}", parent=None, duration=10000)
            self.show()
    
    def _init_remaining_interfaces(self):
        """初始化剩余界面"""
        try:
            self.console_interface = ConsoleInterface(self)
            self.download_interface = DownloadInterface(self)
            self.settings_interface = SettingsInterface(self)
            
            self.addSubInterface(
                self.console_interface,
                FIF.COMMAND_PROMPT,
                "控制台",
                NavigationItemPosition.SCROLL
            )
            self.addSubInterface(
                self.download_interface,
                FIF.FOLDER_ADD,
                "模型下载",
                NavigationItemPosition.SCROLL
            )
            self.addSubInterface(
                self.settings_interface,
                FIF.SETTING,
                "设置",
                NavigationItemPosition.BOTTOM
            )
            
            # 启动 Ollama 服务（启动画面会一直显示到服务启动完成）
            if hasattr(self, 'loading_dialog') and self.loading_dialog:
                self.loading_dialog.set_status("🚀 启动 Ollama 服务...")
            self.start_ollama_service()
        except Exception as e:
            print(f"Error initializing remaining interfaces: {e}")
            import traceback
            traceback.print_exc()
    
    def _set_navigation_enabled(self, enabled):
        """设置导航是否可用"""
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget:
                widget.setEnabled(enabled)
                widget.show()  # 确保页面显示
        
        # 显示第一个页面
        if self.stackedWidget.count() > 0:
            self.stackedWidget.setCurrentIndex(0)
    
    def start_ollama_service(self):
        """启动 Ollama 服务"""
        self.service_thread = OllamaServiceThread(self)
        self.service_thread.started.connect(self.on_service_started)
        self.service_thread.error.connect(self.on_service_error)
        self.service_thread.output.connect(self.console_interface.append_log)
        
        # 连接状态更新到加载对话框（确保对话框存在）
        if hasattr(self, 'loading_dialog') and self.loading_dialog:
            self.service_thread.status_update.connect(self.loading_dialog.set_status)

        # 设置控制台的服务线程
        self.console_interface.set_service_thread(self.service_thread)

        # 在后台线程启动服务，避免阻塞 UI
        self.service_thread.start()
    
    def __del__(self):
        """析构函数，确保服务线程停止"""
        if hasattr(self, 'service_thread') and self.service_thread:
            self.service_thread.stop()
            self.service_thread.wait(1000)
    
    def on_service_started(self):
        """服务启动成功"""
        # 确保加载对话框存在
        if not hasattr(self, 'loading_dialog') or not self.loading_dialog:
            return
        
        # 确保动画至少显示 500ms，让用户能看到
        QTimer.singleShot(500, self._finish_startup)
    
    def _finish_startup(self):
        """完成启动流程"""
        # 确保加载对话框存在
        if not hasattr(self, 'loading_dialog') or not self.loading_dialog:
            return
        
        # 关闭启动画面
        self.loading_dialog.close()
        self.loading_dialog.deleteLater()

        # 确保窗口大小正确
        self.resize(920, 650)
        self.adjustSize()  # 调整大小以适应内容

        # 显示主窗口并提升到最前
        self.show()
        self.activateWindow()
        self.raise_()
        self.setFocus()

        if self.service_thread.already_running:
            InfoBar.info(
                "提示",
                "Ollama 服务已在运行",
                parent=self,
                duration=3000
            )
        else:
            InfoBar.success(
                "成功",
                "Ollama 服务已启动",
                parent=self,
                duration=3000
            )
        if self.console_interface:
            self.console_interface.set_connected()
        # 刷新模型列表（在后台线程执行）
        QTimer.singleShot(100, self._refresh_all_models)
    
    def _refresh_all_models(self):
        """刷新所有模型列表"""
        # 确保界面已创建
        if not hasattr(self, 'chat_interface') or not self.chat_interface:
            # 界面未准备好，延迟 500ms 重试
            QTimer.singleShot(500, self._refresh_all_models)
            return
        
        # 同时刷新所有页面
        self.chat_interface.refresh_models(show_info=False)
        if self.models_interface:
            self.models_interface.refresh_models()
        if self.download_interface:
            self.download_interface.refresh_model_list()
    
    def on_service_error(self, error: str):
        """服务启动失败"""
        # 关闭启动画面
        self.loading_dialog.close()

        # 显示主窗口并提升到最前
        self.show()
        self.activateWindow()
        self.raise_()

        InfoBar.error(
            "错误",
            error,
            parent=self,
            duration=10000
        )
        if self.console_interface:
            self.console_interface.set_disconnected()
        # 更新聊天页面状态
        if self.chat_interface:
            self.chat_interface.is_ollama_connected = False
            self.chat_interface.status_label.setText("❌ Ollama 未运行")
            self.chat_interface.status_label.setStyleSheet("color: #D13438;")
            self.chat_interface.send_btn.setEnabled(False)
    
    def closeEvent(self, event):
        """关闭窗口时停止服务"""
        # 停止服务线程
        if hasattr(self, 'service_thread') and self.service_thread:
            self.console_interface.append_log("正在关闭 Ollama 服务...")
            self.service_thread.stop()
        
        # 使用 taskkill 结束 ollama 进程
        import subprocess
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "ollama.exe"],
                capture_output=True,
                timeout=5
            )
        except:
            pass
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Ollama Fluent UI")
    app.setApplicationVersion("1.0.0")

    window = OllamaWindow()
    # 不在这里 show()，由 on_service_started() 控制显示

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

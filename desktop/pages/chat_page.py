"""智能问答页面 - AI 对话。"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QCheckBox, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from desktop.api_client import chat as api_chat


class ChatWorker(QThread):
    """后台线程调用 API，避免阻塞 UI。"""
    finished = pyqtSignal(object)

    def __init__(self, message, agent_mode):
        super().__init__()
        self._msg = message
        self._agent = agent_mode

    def run(self):
        result = api_chat(self._msg, self._agent)
        self.finished.emit(result)


class ChatPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("chat")
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        # 标题
        title = QLabel("\U0001f4ac  \u667a\u80fd\u95ee\u7b54")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        desc = QLabel("\u57fa\u4e8e RAG \u589e\u5f3a\u68c0\u7d22\u548c ReAct \u667a\u80fd\u4f53\uff0c\u7cbe\u51c6\u56de\u7b54\u5316\u5de5\u9886\u57df\u4e13\u4e1a\u95ee\u9898")
        desc.setStyleSheet("color: #8395a7; font-size: 12px;")
        layout.addWidget(desc)

        # 对话区域
        self._chat_area = QTextEdit()
        self._chat_area.setReadOnly(True)
        self._chat_area.setStyleSheet("""
            QTextEdit {
                background: white; border: 1px solid #e0e0e0;
                border-radius: 8px; padding: 14px;
                font-size: 13px; line-height: 1.6;
            }
        """)
        layout.addWidget(self._chat_area, stretch=1)

        # 输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet("QFrame { background: white; border-radius: 8px; border: 1px solid #e0e0e0; }")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 8, 8, 8)

        self._input = QTextEdit()
        self._input.setPlaceholderText("\u8f93\u5165\u4f60\u7684\u95ee\u9898\uff0c\u4f8b\u5982\uff1a\u201c\u5e2e\u6211\u627e\u4e00\u4e2a\u8010\u5019\u6027\u597d\u7684\u6c34\u6027\u6d82\u6599\u914d\u65b9\u5e76\u5206\u6790\u4f18\u7f3a\u70b9\u201d")
        self._input.setMaximumHeight(80)
        self._input.setStyleSheet("border: none; font-size: 13px; padding: 4px;")
        input_layout.addWidget(self._input)

        self._agent_check = QCheckBox("\U0001f9e0 \u667a\u80fd\u4f53\u6a21\u5f0f")
        self._agent_check.setStyleSheet("font-size: 12px; color: #8395a7;")
        input_layout.addWidget(self._agent_check)

        self._send_btn = QPushButton("\u53d1\u9001")
        self._send_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8; color: white; border: none;
                border-radius: 6px; padding: 8px 20px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #1557b0; }
            QPushButton:disabled { background: #b0c4de; }
        """)
        self._send_btn.clicked.connect(self._send)
        input_layout.addWidget(self._send_btn)

        layout.addWidget(input_frame)

    def _send(self):
        msg = self._input.toPlainText().strip()
        if not msg:
            return

        self._chat_area.append(f'\n<b style="color:#1a73e8;">\U0001f468\u200d\U0001f52c \u4f60:</b> {msg}')
        self._chat_area.append('')
        self._input.clear()
        self._send_btn.setEnabled(False)
        self._send_btn.setText("\u7b49\u5f85\u4e2d...")

        self._worker = ChatWorker(msg, self._agent_check.isChecked())
        self._worker.finished.connect(self._on_response)
        self._worker.start()

    def _on_response(self, result):
        self._send_btn.setEnabled(True)
        self._send_btn.setText("\u53d1\u9001")
        if result:
            reply = result.get("reply", str(result))
            self._chat_area.append(f'<b style="color:#27ae60;">\U0001f916 \u52a9\u624b:</b> {reply}')
        else:
            self._chat_area.append('<b style="color:#e74c3c;">\u26a0\ufe0f API \u672a\u54cd\u5e94\uff0c\u8bf7\u68c0\u67e5\u670d\u52a1\u72b6\u6001</b>')
        self._chat_area.append('<hr style="border:0;border-top:1px solid #eee;">')

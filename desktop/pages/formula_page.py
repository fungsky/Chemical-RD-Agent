"""配方管理页面 - 搜索、查看、对比配方。"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QTextEdit, QSplitter, QMessageBox, QComboBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from desktop.api_client import search_formulas, get_formula


class SearchWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self, keyword, category):
        super().__init__()
        self._kw = keyword
        self._cat = category

    def run(self):
        result = search_formulas(self._kw, self._cat)
        self.finished.emit(result if result else [])


class DetailWorker(QThread):
    finished = pyqtSignal(object)

    def __init__(self, code):
        super().__init__()
        self._code = code

    def run(self):
        result = get_formula(self._code)
        self.finished.emit(result)


class FormulaPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("formulas")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("\U0001f9ea  \u914d\u65b9\u7ba1\u7406")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # 搜索栏
        search_frame = QHBoxLayout()
        search_frame.setSpacing(10)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("\u641c\u7d22\u914d\u65b9\u540d\u79f0\u3001\u7f16\u53f7\u6216\u539f\u6599...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px; border: 1px solid #d0d0d0;
                border-radius: 6px; font-size: 14px; background: white;
            }
            QLineEdit:focus { border-color: #1a73e8; }
        """)
        search_frame.addWidget(self._search_input)

        self._cat_combo = QComboBox()
        self._cat_combo.addItems([
            "\u5168\u90e8\u7c7b\u522b", "\u6d82\u6599", "\u80f6\u7c98\u5242", "\u5bc6\u5c01\u5242",
            "\u6811\u8102", "\u50ac\u5316\u5242", "\u52a9\u5242", "\u5176\u4ed6",
        ])
        self._cat_combo.setStyleSheet("padding: 8px; border: 1px solid #d0d0d0; border-radius: 6px; font-size: 13px;")
        search_frame.addWidget(self._cat_combo)

        search_btn = QPushButton("\U0001f50d \u641c\u7d22")
        search_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8; color: white; border: none;
                border-radius: 6px; padding: 10px 20px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #1557b0; }
        """)
        search_btn.clicked.connect(self._search)
        search_frame.addWidget(search_btn)

        layout.addLayout(search_frame)

        # 分割器：上表下详情
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 结果表格
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "\u914d\u65b9\u7f16\u53f7", "\u540d\u79f0", "\u7c7b\u522b", "\u4e3b\u8981\u6210\u5206", "\u64cd\u4f5c"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setStyleSheet("""
            QTableWidget {
                background: white; border: 1px solid #e0e0e0;
                border-radius: 8px; gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background: #f8f9fa; padding: 8px; border: none;
                font-weight: bold; font-size: 12px; color: #2c3e50;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected { background: #e8f0fe; color: #1a73e8; }
        """)
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)
        splitter.addWidget(self._table)

        # 详情面板
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setPlaceholderText("\u53cc\u51fb\u914d\u65b9\u67e5\u770b\u8be6\u60c5...")
        self._detail.setStyleSheet("""
            QTextEdit {
                background: white; border: 1px solid #e0e0e0;
                border-radius: 8px; padding: 14px; font-size: 13px;
            }
        """)
        splitter.addWidget(self._detail)

        splitter.setSizes([300, 200])
        layout.addWidget(splitter, stretch=1)

    def _search(self):
        kw = self._search_input.text().strip()
        cat_text = self._cat_combo.currentText()
        cat = "" if cat_text == "\u5168\u90e8\u7c7b\u522b" else cat_text

        self._worker = SearchWorker(kw, cat)
        self._worker.finished.connect(self._populate_table)
        self._worker.start()

    def _populate_table(self, results):
        self._table.setRowCount(0)
        if not results:
            QMessageBox.information(self, "\u641c\u7d22\u7ed3\u679c", "\u672a\u627e\u5230\u5339\u914d\u7684\u914d\u65b9\u3002")
            return

        self._table.setRowCount(len(results))
        for i, item in enumerate(results):
            code = item.get("code", "-")
            name = item.get("name", item.get("formula_name", "-"))
            cat = item.get("category", "-")
            comps = item.get("components", item.get("items_summary", "-"))
            self._table.setItem(i, 0, QTableWidgetItem(code))
            self._table.setItem(i, 1, QTableWidgetItem(name))
            self._table.setItem(i, 2, QTableWidgetItem(str(cat)))
            self._table.setItem(i, 3, QTableWidgetItem(str(comps)[:40]))

            view_btn = QPushButton("\U0001f441 \u67e5\u770b")
            view_btn.setStyleSheet("QPushButton { color: #1a73e8; border: none; font-size: 12px; }")
            view_btn.clicked.connect(lambda checked, c=code: self._view_detail(c))
            self._table.setCellWidget(i, 4, view_btn)

    def _on_row_double_clicked(self, row, col):
        code_item = self._table.item(row, 0)
        if code_item:
            self._view_detail(code_item.text())

    def _view_detail(self, code):
        self._detail.setText(f"\u6b63\u5728\u52a0\u8f7d {code} \u8be6\u60c5...")
        self._detail_worker = DetailWorker(code)
        self._detail_worker.finished.connect(self._show_detail)
        self._detail_worker.start()

    def _show_detail(self, result):
        if not result:
            self._detail.setText("\u26a0\ufe0f \u65e0\u6cd5\u52a0\u8f7d\u914d\u65b9\u8be6\u60c5")
            return
        import json
        self._detail.setText(json.dumps(result, ensure_ascii=False, indent=2))

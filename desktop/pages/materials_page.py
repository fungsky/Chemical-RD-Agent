"""原材料管理页面."""

import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QTabWidget, QLineEdit, QFormLayout)
from PyQt6.QtGui import QFont
from desktop.api_client import mat_add, mat_get, mat_query, mat_list, mat_categories

def _mt(t): t.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold)); t.setStyleSheet("color:#2c3e50;"); return t
def _btn(t,c="#1a73e8"): b=QPushButton(t); b.setStyleSheet(f"QPushButton{{background:{c};color:white;border:none;border-radius:6px;padding:8px 18px;font-weight:bold}}"); return b
def _rb(): te=QTextEdit(); te.setReadOnly(True); te.setStyleSheet("background:white;border:1px solid #e0e0e0;border-radius:6px;padding:10px;font-size:12px;font-family:Consolas;"); return te

class MaterialsPage(QWidget):
    def __init__(self):
        super().__init__(); self.setObjectName("materials")
        tabs = QTabWidget()
        tabs.addTab(self._add_tab(), "添加/查询")
        tabs.addTab(self._list_tab(), "全部列表")
        tabs.addTab(self._cat_tab(), "分类统计")
        l = QVBoxLayout(self); l.addWidget(tabs)

    def _add_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("原材料管理")))
        self._mat_name = QLineEdit(); self._mat_name.setPlaceholderText("环氧树脂E-51")
        l.addWidget(QLabel("名称:")); l.addWidget(self._mat_name)
        self._mat_data = QTextEdit()
        self._mat_data.setPlaceholderText('{"name":"环氧树脂E-51","cas_number":"25068-38-6","category":"树脂","density_g_ml":1.16}')
        self._mat_data.setMaximumHeight(100)
        l.addWidget(QLabel("完整数据(JSON):")); l.addWidget(self._mat_data)
        h=QHBoxLayout()
        h.addWidget(_btn("添加/更新","#27ae60"))
        h.addWidget(_btn("查询"))
        l.addLayout(h)
        self._mat_res = _rb(); l.addWidget(self._mat_res)
        h.itemAt(0).widget().clicked.connect(lambda: self._do(lambda: mat_add(json.loads(self._mat_data.toPlainText()))))
        h.itemAt(1).widget().clicked.connect(lambda: self._do(lambda: mat_get(self._mat_name.text())))
        return w

    def _list_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("全部原材料")))
        b=_btn("刷新"); l.addWidget(b)
        self._mat_lr = _rb(); l.addWidget(self._mat_lr)
        b.clicked.connect(lambda: self._do2(mat_list))
        return w

    def _cat_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("分类统计")))
        b=_btn("刷新"); l.addWidget(b)
        self._mat_cr = _rb(); l.addWidget(self._mat_cr)
        b.clicked.connect(lambda: self._do2(mat_categories))
        return w

    def _do(self, fn):
        try: r=fn(); self._mat_res.setText(json.dumps(r.model_dump() if hasattr(r,'model_dump') else r, ensure_ascii=False, indent=2, default=str))
        except Exception as e: self._mat_res.setText(str(e))

    def _do2(self, fn):
        try: r=fn(); self._mat_lr.setText(json.dumps(r, ensure_ascii=False, indent=2, default=str)[:5000])
        except Exception as e: self._mat_lr.setText(str(e))

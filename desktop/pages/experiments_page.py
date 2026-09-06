"""实验数据管理页面."""

import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QTabWidget)
from PyQt6.QtGui import QFont
from desktop.api_client import exp_add, exp_batch, exp_query, exp_stats, exp_export_training

def _mt(t): t.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold)); t.setStyleSheet("color:#2c3e50;"); return t
def _btn(t,c="#1a73e8"): b=QPushButton(t); b.setStyleSheet(f"QPushButton{{background:{c};color:white;border:none;border-radius:6px;padding:8px 18px;font-weight:bold}}"); return b
def _rb(): te=QTextEdit(); te.setReadOnly(True); te.setStyleSheet("background:white;border:1px solid #e0e0e0;border-radius:6px;padding:10px;font-size:12px;font-family:Consolas;"); te.setMaximumHeight(300); return te

class ExperimentsPage(QWidget):
    def __init__(self):
        super().__init__(); self.setObjectName("experiments")
        tabs = QTabWidget()
        tabs.addTab(self._add_tab(), "录入")
        tabs.addTab(self._query_tab(), "查询")
        tabs.addTab(self._stats_tab(), "统计+导出")
        l = QVBoxLayout(self); l.addWidget(tabs)

    def _add_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("录入实验结果")))
        self._exp_input = QTextEdit()
        self._exp_input.setPlaceholderText('批量JSON: [{"experiment_id":"E-001","formula_name":"环氧",...}]')
        l.addWidget(self._exp_input)
        b=_btn("提交"); l.addWidget(b)
        self._exp_res=_rb(); l.addWidget(self._exp_res)
        b.clicked.connect(lambda: self._do(exp_batch, {"batch_name":"import","results":json.loads(self._exp_input.toPlainText())}))
        return w

    def _query_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("查询实验")))
        self._exp_q = QTextEdit(); self._exp_q.setPlaceholderText('{"project":"防腐","limit":50}'); self._exp_q.setMaximumHeight(60)
        l.addWidget(self._exp_q)
        b=_btn("查询"); l.addWidget(b)
        self._exp_qr = _rb(); l.addWidget(self._exp_qr)
        b.clicked.connect(lambda: self._do2(exp_query, json.loads(self._exp_q.toPlainText())))
        return w

    def _stats_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("实验统计")))
        b1=_btn("刷新统计","#27ae60"); l.addWidget(b1)
        self._exp_st = _rb(); l.addWidget(self._exp_st)
        b1.clicked.connect(lambda: self._do2(lambda: exp_stats(), {}))
        b2=_btn("导出训练数据","#e67e22"); l.addWidget(b2)
        self._exp_tr = _rb(); l.addWidget(self._exp_tr)
        b2.clicked.connect(lambda: self._do2(exp_export_training, True))
        return w

    def _do(self, fn, data):
        try: r=fn(data); self._exp_res.setText(json.dumps(r,ensure_ascii=False,indent=2) if r else "Error")
        except Exception as e: self._exp_res.setText(str(e))

    def _do2(self, fn, arg):
        try: r=fn(arg) if callable(fn) else fn(); self._exp_qr.setText(json.dumps(r,ensure_ascii=False,indent=2) if r else "Error")
        except Exception as e: self._exp_qr.setText(str(e))

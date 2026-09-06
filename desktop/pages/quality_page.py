"""质量管理: COA + SPC."""

import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QTabWidget, QLineEdit, QFormLayout)
from PyQt6.QtGui import QFont
from desktop.api_client import (quality_add_template, quality_list_templates, quality_generate_coa, quality_list_coas, spc_analyze)

def _mt(t): t.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold)); t.setStyleSheet("color:#2c3e50;"); return t
def _btn(t,c="#1a73e8"): b=QPushButton(t); b.setStyleSheet(f"QPushButton{{background:{c};color:white;border:none;border-radius:6px;padding:8px 18px;font-weight:bold}}"); return b
def _rb(): te=QTextEdit(); te.setReadOnly(True); te.setStyleSheet("background:white;border:1px solid #e0e0e0;border-radius:6px;padding:10px;font-size:12px;font-family:Consolas;"); return te

class QualityPage(QWidget):
    def __init__(self):
        super().__init__(); self.setObjectName("quality")
        tabs = QTabWidget()
        tabs.addTab(self._coa_tab(), "COA报告")
        tabs.addTab(self._spc_tab(), "SPC过程控制")
        l = QVBoxLayout(self); l.addWidget(tabs)

    def _coa_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("COA出厂检验报告")))

        self._coa_tpl = QTextEdit()
        self._coa_tpl.setPlaceholderText('模板JSON:\n{"name":"涂料COA","product_name":"环氧防腐涂料","specs":[{"name":"粘度","direction":"range","min_value":80,"max_value":120,"unit":"KU"},...]}')
        self._coa_tpl.setMaximumHeight(100)
        l.addWidget(QLabel("COA模板:")); l.addWidget(self._coa_tpl)
        h=QHBoxLayout(); h.addWidget(_btn("添加模板","#27ae60")); h.addWidget(_btn("查看模板")); l.addLayout(h)
        h.itemAt(0).widget().clicked.connect(lambda: self._do(quality_add_template, json.loads(self._coa_tpl.toPlainText())))
        h.itemAt(1).widget().clicked.connect(lambda: self._do2(quality_list_templates))

        self._coa_meas = QTextEdit()
        self._coa_meas.setPlaceholderText('{"粘度":100,"细度":25,"附着力":5.5}')
        self._coa_meas.setMaximumHeight(60)
        l.addWidget(QLabel("实测值:")); l.addWidget(self._coa_meas)

        f=QFormLayout()
        self._coa_rid = QLineEdit("COA-001"); f.addRow("报告编号:",self._coa_rid)
        self._coa_batch = QLineEdit("B2024-001"); f.addRow("批号:",self._coa_batch)
        self._coa_tname = QLineEdit("涂料COA"); f.addRow("模板名:",self._coa_tname)
        l.addLayout(f)

        b=_btn("生成COA","#e67e22"); l.addWidget(b)
        self._coa_res=_rb(); l.addWidget(self._coa_res)
        b.clicked.connect(lambda: self._do(quality_generate_coa, self._coa_tname.text(), self._coa_rid.text(), self._coa_batch.text(), json.loads(self._coa_meas.toPlainText())))
        return w

    def _spc_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("SPC统计过程控制")))
        self._spc_input = QTextEdit()
        self._spc_input.setPlaceholderText('{"process_name":"固化温度","measurements":[100,102,98,101,99,105,...],"usl":115,"lsl":85,"subgroup_size":3}')
        self._spc_input.setMaximumHeight(80)
        l.addWidget(self._spc_input)
        b=_btn("SPC分析","#9b59b6"); l.addWidget(b)
        self._spc_res=_rb(); l.addWidget(self._spc_res)
        b.clicked.connect(lambda: self._do(spc_analyze, json.loads(self._spc_input.toPlainText())))
        return w

    def _do(self, fn, *args):
        try: r=fn(*args); self._coa_res.setText(json.dumps(r,ensure_ascii=False,indent=2,default=str) if r else "Error")
        except Exception as e: self._coa_res.setText(str(e))

    def _do2(self, fn):
        try: r=fn(); self._coa_res.setText(json.dumps(r,ensure_ascii=False,indent=2,default=str)[:3000])
        except Exception as e: self._coa_res.setText(str(e))

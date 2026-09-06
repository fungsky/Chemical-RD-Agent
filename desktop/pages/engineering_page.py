"""工程放大: ScaleUp + Stability + Sustainability."""

import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QTabWidget, QFormLayout, QDoubleSpinBox)
from PyQt6.QtGui import QFont
from desktop.api_client import scaleup_calculate, stability_predict, sustainability_assess

def _mt(t): t.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold)); t.setStyleSheet("color:#2c3e50;"); return t
def _btn(t,c="#1a73e8"): b=QPushButton(t); b.setStyleSheet(f"QPushButton{{background:{c};color:white;border:none;border-radius:6px;padding:8px 18px;font-weight:bold}}"); return b
def _rb(): te=QTextEdit(); te.setReadOnly(True); te.setStyleSheet("background:white;border:1px solid #e0e0e0;border-radius:6px;padding:10px;font-size:12px;font-family:Consolas;"); return te

class EngineeringPage(QWidget):
    def __init__(self):
        super().__init__(); self.setObjectName("engineering")
        tabs = QTabWidget()
        tabs.addTab(self._scaleup_tab(), "放大计算")
        tabs.addTab(self._stability_tab(), "稳定性预测")
        tabs.addTab(self._sustain_tab(), "可持续性")
        l = QVBoxLayout(self); l.addWidget(tabs)

    def _scaleup_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("工艺放大计算")))
        self._su_input = QTextEdit()
        self._su_input.setPlaceholderText('{"lab_volume_l":1,"target_volume_l":1000,"lab_speed_rpm":800,"impeller_diameter_m":0.05}')
        self._su_input.setMaximumHeight(60)
        l.addWidget(self._su_input)
        b=_btn("计算放大参数"); l.addWidget(b)
        self._su_res=_rb(); l.addWidget(self._su_res)
        b.clicked.connect(lambda: self._do(scaleup_calculate, json.loads(self._su_input.toPlainText())))
        return w

    def _stability_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("稳定性/货架寿命预测")))
        self._st_input = QTextEdit()
        self._st_input.setPlaceholderText('{"aging_data":[{"temperature_c":60,"time_hours":0,"property_value":100},...],"failure_threshold":50,"model":"arrhenius"}')
        self._st_input.setMaximumHeight(80)
        l.addWidget(self._st_input)
        b=_btn("预测货架寿命","#e67e22"); l.addWidget(b)
        self._st_res=_rb(); l.addWidget(self._st_res)
        b.clicked.connect(lambda: self._do(stability_predict, json.loads(self._st_input.toPlainText())))
        return w

    def _sustain_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(_mt(QLabel("可持续性评估")))
        self._sa_input = QTextEdit()
        self._sa_input.setPlaceholderText('{"components":[{"name":"树脂","weight_percent":50,"voc_content_percent":5,"bio_based_percent":20,"carbon_footprint_kgCO2_per_kg":3},...],"energy_kwh_per_kg":0.5}')
        self._sa_input.setMaximumHeight(80)
        l.addWidget(self._sa_input)
        b=_btn("评估","#27ae60"); l.addWidget(b)
        self._sa_res=_rb(); l.addWidget(self._sa_res)
        b.clicked.connect(lambda: self._do(sustainability_assess, json.loads(self._sa_input.toPlainText())))
        return w

    def _do(self, fn, data):
        try: r=fn(data); self._su_res.setText(json.dumps(r,ensure_ascii=False,indent=2) if r else "Error")
        except Exception as e: self._su_res.setText(str(e))

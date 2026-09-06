"""仪表盘页面 - 实时数据概览."""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from desktop.api_client import health, kg_stats, exp_stats, mat_categories

class StatCard(QFrame):
    def __init__(self, title, value, color="#1a73e8"):
        super().__init__()
        self.setStyleSheet(f"QFrame{{background:white;border-radius:10px;border:1px solid #e0e0e0;padding:18px;}}QFrame:hover{{border-color:{color};}}")
        self.setMinimumHeight(100)
        l=QVBoxLayout(self)
        tl=QLabel(title); tl.setStyleSheet("color:#8395a7;font-size:12px;border:none;")
        self._val=QLabel(str(value)); self._val.setStyleSheet(f"color:{color};font-size:28px;font-weight:bold;border:none;")
        l.addWidget(tl); l.addWidget(self._val)
    def set_val(self, v): self._val.setText(str(v))

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__(); self.setObjectName("dashboard"); self._init_ui()
        QTimer.singleShot(1000, self._refresh)

    def _init_ui(self):
        sc=QScrollArea(); sc.setWidgetResizable(True); sc.setStyleSheet("QScrollArea{border:none;background:#f5f6fa;}")
        c=QWidget(); l=QVBoxLayout(c); l.setContentsMargins(30,24,30,24); l.setSpacing(18)

        t=QLabel("\U0001f3e0  ChemAgent 仪表盘")
        t.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold)); t.setStyleSheet("color:#2c3e50;"); l.addWidget(t)

        g=QGridLayout(); g.setSpacing(14)
        self._cards={
            "formulas":StatCard("\U0001f9ea 配方总数","--"),
            "materials":StatCard("\U0001f4e6 原材料","--","#27ae60"),
            "experiments":StatCard("\U0001f52c 实验记录","--","#e67e22"),
            "models":StatCard("\U0001f916 预测模型","--","#9b59b6"),
        }
        for i,(k,card) in enumerate(self._cards.items()): g.addWidget(card,0,i)
        l.addLayout(g)

        self._api_st = QLabel("Connecting..."); self._api_st.setStyleSheet("padding:12px;font-size:13px;color:#8395a7;"); l.addWidget(self._api_st)

        sl=QLabel("快捷模块"); sl.setFont(QFont("Microsoft YaHei",14,QFont.Weight.Bold)); sl.setStyleSheet("color:#2c3e50;margin-top:10px;"); l.addWidget(sl)
        bl=QHBoxLayout(); bl.setSpacing(12)
        for txt,clr in [("DOE设计","#1a73e8"),("风险评估","#e74c3c"),("成本核算","#27ae60"),("合规检查","#e67e22"),("多目标优化","#9b59b6"),("工程放大","#2c3e50")]:
            b=QPushButton(txt); b.setStyleSheet(f"QPushButton{{background:{clr};color:white;border:none;border-radius:8px;padding:12px 18px;font-size:13px;font-weight:bold;}}")
            b.setMinimumHeight(44); bl.addWidget(b)
        l.addLayout(bl)
        l.addStretch()
        sc.setWidget(c)
        o=QVBoxLayout(self); o.setContentsMargins(0,0,0,0); o.addWidget(sc)

    def _refresh(self):
        h=health()
        if h:
            self._api_st.setText(f"API Online  v{h.get('version','?')}")
            self._api_st.setStyleSheet("padding:12px;font-size:13px;color:#27ae60;")

            # Pull KG stats
            kg=kg_stats()
            if kg:
                self._cards["formulas"].set_val(kg.get("formulas","?"))
                self._cards["materials"].set_val(kg.get("materials","?"))

            # Pull experiment stats
            es=exp_stats()
            if es:
                self._cards["experiments"].set_val(es.get("total","?"))

            self._cards["models"].set_val("就绪" if h else "未加载")
        else:
            self._api_st.setText("API Offline - please start backend")
            self._api_st.setStyleSheet("padding:12px;font-size:13px;color:#e74c3c;")
        QTimer.singleShot(30000, self._refresh)

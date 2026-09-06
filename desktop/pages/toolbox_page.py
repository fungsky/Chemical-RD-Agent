"""研发工具箱: DOE / Risk / Cost / Compliance / Optimization."""

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QTextEdit, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QFormLayout, QScrollArea, QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from desktop.api_client import (
    doe_generate, doe_methods, risk_analyze, cost_calculate,
    compliance_check, compliance_domains, opt_run, opt_methods,
)

def _make_title(text): 
    t = QLabel(text)
    t.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
    t.setStyleSheet("color: #2c3e50; margin-bottom: 8px;")
    return t

def _make_btn(text, color="#1a73e8"):
    b = QPushButton(text)
    b.setStyleSheet(f"QPushButton{{background:{color};color:white;border:none;border-radius:6px;padding:8px 18px;font-weight:bold}}QPushButton:hover{{opacity:0.9}}")
    return b

def _result_box():
    te = QTextEdit()
    te.setReadOnly(True)
    te.setStyleSheet("background:white;border:1px solid #e0e0e0;border-radius:6px;padding:10px;font-size:12px;font-family:Consolas;")
    te.setMaximumHeight(250)
    return te


class ToolboxPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("toolbox")
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane{border:1px solid #e0e0e0;border-radius:8px;background:white;}QTabBar::tab{padding:10px 20px;font-size:13px;}")
        tabs.addTab(self._doe_tab(), "DOE设计")
        tabs.addTab(self._risk_tab(), "风险评估")
        tabs.addTab(self._cost_tab(), "成本核算")
        tabs.addTab(self._compliance_tab(), "合规检查")
        tabs.addTab(self._opt_tab(), "多目标优化")
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)

    def _doe_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(_make_title("实验设计 (DOE)"))

        f = QFormLayout()
        self._doe_method = QComboBox()
        self._doe_method.addItems(["full_factorial","2k_factorial","plackett_burman","latin_hypercube","central_composite"])
        f.addRow("方法:", self._doe_method)

        self._doe_factors = QTextEdit()
        self._doe_factors.setPlaceholderText('{"name":"温度","low":100,"high":200}\n{"name":"时间","low":10,"high":60}')
        self._doe_factors.setMaximumHeight(80)
        f.addRow("因子(每行JSON):", self._doe_factors)

        self._doe_reps = QSpinBox(); self._doe_reps.setValue(1); self._doe_reps.setRange(1,5)
        f.addRow("重复:", self._doe_reps)

        l.addLayout(f)
        btn = _make_btn("生成实验方案"); l.addWidget(btn)
        self._doe_result = _result_box(); l.addWidget(self._doe_result)
        btn.clicked.connect(self._run_doe)
        return w

    def _run_doe(self):
        try:
            factors = []
            for line in self._doe_factors.toPlainText().strip().split("\n"):
                if line.strip(): factors.append(json.loads(line))
            r = doe_generate({"method":self._doe_method.currentText(),"factors":factors,"replicates":self._doe_reps.value()})
            self._doe_result.setText(json.dumps(r, ensure_ascii=False, indent=2) if r else "Error")
        except Exception as e: self._doe_result.setText(str(e))

    def _risk_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(_make_title("配方风险评估"))

        self._risk_input = QTextEdit()
        self._risk_input.setPlaceholderText('配方JSON (含safety字段):\n{"name":"测试","items":[{"material":{"name":"甲苯","safety":{"hazard_class":["有毒","易燃液体/固体"],"flash_point_c":4}},"weight_percent":40},...]}')
        self._risk_input.setMaximumHeight(100)
        l.addWidget(QLabel("配方数据:")); l.addWidget(self._risk_input)

        f = QFormLayout()
        self._risk_batch = QDoubleSpinBox(); self._risk_batch.setValue(100); self._risk_batch.setRange(0.1,10000)
        f.addRow("批次(kg):", self._risk_batch)
        self._risk_temp = QDoubleSpinBox(); self._risk_temp.setValue(25); self._risk_temp.setRange(-20,500)
        f.addRow("工艺温度(℃):", self._risk_temp)
        l.addLayout(f)

        btn = _make_btn("分析风险", "#e74c3c"); l.addWidget(btn)
        self._risk_result = _result_box(); l.addWidget(self._risk_result)
        btn.clicked.connect(self._run_risk)
        return w

    def _run_risk(self):
        try:
            data = json.loads(self._risk_input.toPlainText())
            r = risk_analyze({"formula":data,"batch_size_kg":self._risk_batch.value(),"process_temperature_c":self._risk_temp.value()})
            self._risk_result.setText(json.dumps(r, ensure_ascii=False, indent=2) if r else "Error")
        except Exception as e: self._risk_result.setText(str(e))

    def _cost_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(_make_title("BOM成本核算"))

        self._cost_formula = QTextEdit()
        self._cost_formula.setPlaceholderText('{"name":"配方","items":[{"material":{"name":"树脂"},"weight_percent":60},...]}')
        self._cost_formula.setMaximumHeight(80)
        l.addWidget(QLabel("配方:")); l.addWidget(self._cost_formula)

        f = QFormLayout()
        self._cost_batch = QDoubleSpinBox(); self._cost_batch.setValue(100); self._cost_batch.setRange(0.1,100000)
        f.addRow("批次(kg):", self._cost_batch)
        self._cost_prices = QLineEdit(); self._cost_prices.setPlaceholderText('{"树脂":25,"溶剂":8}')
        f.addRow("单价(元/kg):", self._cost_prices)
        self._cost_pack = QDoubleSpinBox(); self._cost_pack.setValue(2)
        f.addRow("包装(元/kg):", self._cost_pack)
        self._cost_labor = QDoubleSpinBox(); self._cost_labor.setValue(5)
        f.addRow("人工(元/kg):", self._cost_labor)
        l.addLayout(f)

        btn = _make_btn("核算成本", "#27ae60"); l.addWidget(btn)
        self._cost_result = _result_box(); l.addWidget(self._cost_result)
        btn.clicked.connect(self._run_cost)
        return w

    def _run_cost(self):
        try:
            formula = json.loads(self._cost_formula.toPlainText())
            prices = json.loads(self._cost_prices.text())
            r = cost_calculate({"formula":formula,"batch_size_kg":self._cost_batch.value(),"price_map":prices,"packaging_cost_per_kg":self._cost_pack.value(),"labor_cost_per_kg":self._cost_labor.value()})
            self._cost_result.setText(json.dumps(r, ensure_ascii=False, indent=2) if r else "Error")
        except Exception as e: self._cost_result.setText(str(e))

    def _compliance_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(_make_title("合规检查"))

        self._comp_formula = QTextEdit()
        self._comp_formula.setPlaceholderText('{"name":"配方","items":[{"material":{"name":"铅铬黄","cas_number":"7758-97-6"},"weight_percent":0.5},...]}')
        self._comp_formula.setMaximumHeight(80)
        l.addWidget(QLabel("配方:")); l.addWidget(self._comp_formula)

        self._comp_domains = QTextEdit()
        self._comp_domains.setText("food_contact\ntoys\nelectronics")
        self._comp_domains.setMaximumHeight(60)
        l.addWidget(QLabel("法规领域(每行一个):")); l.addWidget(self._comp_domains)

        btn = _make_btn("合规检查", "#e67e22"); l.addWidget(btn)
        self._comp_result = _result_box(); l.addWidget(self._comp_result)
        btn.clicked.connect(self._run_compliance)
        return w

    def _run_compliance(self):
        try:
            formula = json.loads(self._comp_formula.toPlainText())
            domains = [d.strip() for d in self._comp_domains.toPlainText().strip().split("\n") if d.strip()]
            r = compliance_check({"formula":formula,"domains":domains})
            self._comp_result.setText(json.dumps(r, ensure_ascii=False, indent=2) if r else "Error")
        except Exception as e: self._comp_result.setText(str(e))

    def _opt_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(_make_title("多目标优化"))

        self._opt_input = QTextEdit()
        self._opt_input.setPlaceholderText('JSON请求体:\n{"method":"pareto_frontier","factor_ranges":[...],"objectives":[...],"population_size":500,"top_n":10}')
        self._opt_input.setMaximumHeight(100)
        l.addWidget(self._opt_input)

        btn = _make_btn("执行优化", "#9b59b6"); l.addWidget(btn)
        self._opt_result = _result_box(); l.addWidget(self._opt_result)
        btn.clicked.connect(self._run_opt)
        return w

    def _run_opt(self):
        try:
            r = opt_run(json.loads(self._opt_input.toPlainText()))
            self._opt_result.setText(json.dumps(r, ensure_ascii=False, indent=2) if r else "Error")
        except Exception as e: self._opt_result.setText(str(e))

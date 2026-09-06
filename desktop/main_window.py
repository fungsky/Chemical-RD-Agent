"""ChemAgent Desktop - Main Window."""

import json, logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QStatusBar, QLabel, QFrame, QPushButton, QSystemTrayIcon, QMenu, QApplication,
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QAction, QFont

from desktop.api_client import health as api_health
from desktop.pages.dashboard_page import DashboardPage
from desktop.pages.formula_page import FormulaPage
from desktop.pages.chat_page import ChatPage
from desktop.pages.toolbox_page import ToolboxPage
from desktop.pages.experiments_page import ExperimentsPage
from desktop.pages.materials_page import MaterialsPage
from desktop.pages.engineering_page import EngineeringPage
from desktop.pages.quality_page import QualityPage

logger = logging.getLogger(__name__)
SETTINGS_FILE = Path.home() / ".chemagent" / "desktop_settings.json"

NAV_GROUPS = [
    ("\U0001f3e0 仪表盘", "dashboard", "home"),
    ("\U0001f9ea 配方管理", "formulas", "rd"),
    ("\U0001f4ac 智能问答", "chat", "rd"),
    ("\U0001f527 研发工具箱", "toolbox", "rd"),
    ("\U0001f52c 实验管理", "experiments", "rd"),
    ("\U0001f4e6 原材料库", "materials", "supply"),
    ("\U0001f3ed 工程放大", "engineering", "mfg"),
    ("\u2705 质量管控", "quality", "mfg"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._theme = "light"
        self._settings = self._load_settings()
        self._init_ui()
        self._init_tray()
        self._check_api()
        self._restore_geometry()
        self._apply_theme()

    def _init_ui(self):
        self.setWindowTitle("ChemAgent - 化工研发智能体")
        self.setMinimumSize(1100, 700)
        self.resize(self._settings.get("width", 1280), self._settings.get("height", 820))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left nav
        nav = QFrame()
        nav.setFixedWidth(220)
        nav.setObjectName("navFrame")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        logo = QLabel("  \U0001f9ea ChemAgent")
        logo.setObjectName("logoLabel")
        nav_layout.addWidget(logo)

        self._nav_list = QListWidget()
        self._nav_list.setObjectName("navList")
        for text, key, group in NAV_GROUPS:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._nav_list.addItem(item)
        self._nav_list.currentRowChanged.connect(self._on_nav)
        nav_layout.addWidget(self._nav_list)

        # Theme toggle
        self._theme_btn = QPushButton("\u263E 暗色模式")
        self._theme_btn.setObjectName("themeBtn")
        self._theme_btn.clicked.connect(self._toggle_theme)
        nav_layout.addWidget(self._theme_btn)

        ver = QLabel("  v0.2.0")
        ver.setObjectName("versionLabel")
        nav_layout.addWidget(ver)

        layout.addWidget(nav)

        # Right content
        self._stack = QStackedWidget()
        self._pages = {
            "dashboard": DashboardPage(),
            "formulas": FormulaPage(),
            "chat": ChatPage(),
            "toolbox": ToolboxPage(),
            "experiments": ExperimentsPage(),
            "materials": MaterialsPage(),
            "engineering": EngineeringPage(),
            "quality": QualityPage(),
        }
        for _, key, _ in NAV_GROUPS:
            if key in self._pages:
                self._stack.addWidget(self._pages[key])
        layout.addWidget(self._stack)

        # Status bar
        self._status_label = QLabel("  Connecting...")
        self._status = QStatusBar()
        self._status.addWidget(self._status_label)
        self.setStatusBar(self._status)

        self._nav_list.setCurrentRow(0)

    def _init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable(): return
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("ChemAgent")
        menu = QMenu()
        menu.addAction("Show", self._show_window)
        menu.addSeparator()
        menu.addAction("Quit", self._quit_app)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(lambda r: self._show_window() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self._tray.show()

    def closeEvent(self, e):
        if hasattr(self, "_tray") and self._tray.isVisible():
            self.hide(); e.ignore()
        else:
            self._save_settings(); e.accept()

    def _show_window(self): self.show(); self.raise_(); self.activateWindow()
    def _quit_app(self): self._save_settings(); QApplication.quit()

    def _on_nav(self, idx):
        key = self._nav_list.item(idx).data(Qt.ItemDataRole.UserRole)
        for i in range(self._stack.count()):
            if self._stack.widget(i) in self._pages.values() and list(self._pages.keys())[list(self._pages.values()).index(self._stack.widget(i))] == key:
                self._stack.setCurrentIndex(i)
                break

    def _check_api(self):
        r = api_health()
        if r:
            self._status_label.setText(f"  API Online  v{r.get('version','?')}")
            self._status_label.setStyleSheet("color: #27ae60;")
        else:
            self._status_label.setText("  API Offline")
            self._status_label.setStyleSheet("color: #e74c3c;")
        QTimer.singleShot(30000, self._check_api)

    def _toggle_theme(self):
        self._theme = "dark" if self._theme == "light" else "light"
        self._apply_theme()
        self._theme_btn.setText("\u2600 亮色模式" if self._theme == "dark" else "\u263E 暗色模式")

    def _apply_theme(self):
        dark = self._theme == "dark"
        bg = "#1a1a2e" if dark else "#f5f6fa"
        nav_bg = "#0f0f23" if dark else "#1e2a3a"
        card_bg = "#16213e" if dark else "white"
        text = "#e0e0e0" if dark else "#2c3e50"
        sub_text = "#a0a0b0" if dark else "#8395a7"
        border = "#2a2a4a" if dark else "#e0e0e0"

        self.setStyleSheet(f"""
            QMainWindow {{ background: {bg}; }}
            #navFrame {{ background: {nav_bg}; }}
            #logoLabel {{ color: white; font-size: 16px; font-weight: bold; padding: 16px; }}
            #navList {{
                background: {nav_bg}; color: {"#c8d6e5" if not dark else "#a0b0c0"}; border: none;
                font-size: 14px; padding: 8px 0;
            }}
            #navList::item {{ padding: 10px 16px; border-left: 3px solid transparent; }}
            #navList::item:selected {{ background: {"#2d3e50" if not dark else "#1a3a5c"}; color: white; border-left: 3px solid #1a73e8; }}
            #themeBtn {{
                background: transparent; color: {"#8395a7" if not dark else "#a0b0c0"}; border: 1px solid {"#3d4f5f" if not dark else "#2a3a4a"};
                border-radius: 4px; padding: 6px; margin: 8px 12px; font-size: 12px;
            }}
            #versionLabel {{ color: {"#576574" if not dark else "#6a7a8a"}; padding: 12px; font-size: 11px; }}
            QStatusBar {{ background: {nav_bg}; color: {sub_text}; font-size: 12px; }}
        """)

    def _load_settings(self):
        if SETTINGS_FILE.exists(): return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return {}

    def _save_settings(self):
        self._settings.update({"width": self.width(), "height": self.height(), "theme": self._theme})
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(self._settings, indent=2), encoding="utf-8")

    def _restore_geometry(self):
        self.resize(self._settings.get("width", 1280), self._settings.get("height", 820))
        self._theme = self._settings.get("theme", "light")

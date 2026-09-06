"""ChemAgent 桌面应用启动入口。

用法:
    python desktop_app.py              # 启动桌面
    python desktop_app.py --minimized   # 最小化到托盘启动

打包（PyInstaller）后同样适用：后端以进程内线程方式启动，
数据写入 %LOCALAPPDATA%\ChemAgent，避免只读目录/临时目录问题。
"""

import logging
import os
import shutil
import sys
import threading
import time
import urllib.request
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    """打包后的资源目录（onefile 为 _MEIPASS 解压目录）。"""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def writable_data_dir() -> Path:
    """可写的数据目录（用户级），避免 Program Files / 临时目录只读问题。"""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    d = Path(base) / "ChemAgent"
    d.mkdir(parents=True, exist_ok=True)
    return d


def setup_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
    )


def seed_data(src: Path, dst: Path) -> None:
    """首次运行把内置示例数据复制到用户数据目录。"""
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            if not target.exists():
                shutil.copytree(item, target)
        elif not target.exists():
            shutil.copy2(item, target)


def _health_ok(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
        return True
    except Exception:
        return False


def start_backend(port: int = 8000):
    """进程内启动 FastAPI 后端（uvicorn 线程），打包后同样可用。"""
    if _health_ok(port):
        return None

    # 静态导入以便 PyInstaller 收集全部依赖
    from chem_agent.api.main import app  # noqa: F401
    from uvicorn import Config
    from uvicorn.server import Server

    config = Config(app, host="127.0.0.1", port=port, log_level="warning", workers=1)
    server = Server(config)
    thread = threading.Thread(target=server.run, daemon=True, name="chemagent-api")
    thread.start()

    for _ in range(60):
        if _health_ok(port):
            logging.getLogger("desktop_app").info("API ready on 127.0.0.1:%s", port)
            return server
        time.sleep(0.5)
    logging.getLogger("desktop_app").error("API failed to start on port %s", port)
    return server


def main():
    minimized = "--minimized" in sys.argv
    data_dir = writable_data_dir()
    setup_logging(data_dir / "chemagent.log")
    logger = logging.getLogger("desktop_app")
    logger.info("ChemAgent desktop starting (frozen=%s)", is_frozen())

    if is_frozen():
        # 保证 ./data 等相对路径指向可写目录
        os.chdir(data_dir)
        seed_data(resource_dir() / "data", data_dir / "data")

    logger.info("Starting ChemAgent API...")
    server = start_backend()
    logger.info("API ready on http://127.0.0.1:8000")

    from PyQt6.QtWidgets import QApplication

    from desktop.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("ChemAgent")
    app.setOrganizationName("ChemAgent")

    window = MainWindow()
    if not minimized:
        window.show()

    def cleanup():
        logger.info("Shutting down...")
        if server is not None:
            server.should_exit = True

    app.aboutToQuit.connect(cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

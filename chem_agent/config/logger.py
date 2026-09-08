"""全局日志配置模块。"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from chem_agent.config import settings

def setup_logging(log_level=None, log_file=None, log_dir="./logs", max_bytes=10*1024*1024, backup_count=5):
    if log_level is None:
        log_level = "DEBUG" if settings.debug else "INFO"
    if log_file is None:
        log_file = "chemagent.log"
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.handlers.clear()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-7s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    file_handler = RotatingFileHandler(
        filename=log_path / log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    for lib in ("neo4j", "urllib3", "httpx", "chromadb"):
        logging.getLogger(lib).setLevel(logging.WARNING)
    logging.getLogger("chem_agent").info("Logging initialized level=%s", log_level)

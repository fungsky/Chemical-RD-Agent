"""启动脚本"""

import subprocess
import sys
import os


def start_api():
    """启动 FastAPI 后端"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "chem_agent.api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
    ])


def start_ui():
    """启动 Streamlit 前端"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "chem_agent/ui/app.py",
        "--server.port", "8501",
    ])


def init_data():
    """初始化示例数据"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "data/init_data.py"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python run.py api    - 启动后端 API 服务")
        print("  python run.py ui     - 启动前端 UI")
        print("  python run.py init   - 初始化示例数据")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "api":
        start_api()
    elif cmd == "ui":
        start_ui()
    elif cmd == "init":
        init_data()
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)

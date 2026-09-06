"""ChemAgent Desktop Launcher - 一键启动."""

import subprocess, sys, os, time, webbrowser, threading, json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
API_PORT = 8000
UI_PORT = 8501

class ChemAgentLauncher:
    def __init__(self):
        self.api_proc = None
        self.ui_proc = None
        self.running = True

    def check_deps(self):
        """Check if required packages are installed."""
        try:
            import fastapi, uvicorn, streamlit
            return True
        except ImportError:
            return False

    def install_deps(self):
        """Install dependencies."""
        print("Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                       cwd=str(PROJECT_DIR), check=True)

    def start_api(self):
        """Start FastAPI backend."""
        print("Starting API server...")
        self.api_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "chem_agent.api.main:app",
             "--host", "0.0.0.0", "--port", str(API_PORT), "--log-level", "warning"],
            cwd=str(PROJECT_DIR),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        # Wait for ready
        import urllib.request
        for i in range(30):
            try:
                urllib.request.urlopen(f"http://localhost:{API_PORT}/health", timeout=2)
                print("API server ready!")
                return True
            except:
                time.sleep(1)
        print("WARNING: API may not be ready")
        return False

    def start_ui(self):
        """Start Streamlit UI."""
        print("Starting UI...")
        self.ui_proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "chem_agent/ui/app.py",
             "--server.port", str(UI_PORT), "--server.headless", "true"],
            cwd=str(PROJECT_DIR),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    def open_browser(self):
        time.sleep(3)
        webbrowser.open(f"http://localhost:{UI_PORT}")

    def stop(self):
        print("Stopping services...")
        for proc in [self.ui_proc, self.api_proc]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except:
                    proc.kill()
        self.running = False

    def run(self):
        print("=" * 50)
        print("  ChemAgent - Chemical R&D Platform")
        print("  v0.2.0")
        print("=" * 50)

        if not self.check_deps():
            print("\nDependencies not installed.")
            resp = input("Install now? (y/n): ").strip().lower()
            if resp == 'y':
                self.install_deps()
            else:
                print("Run: pip install -r requirements.txt")
                return

        self.start_api()
        self.start_ui()
        threading.Thread(target=self.open_browser, daemon=True).start()

        print(f"\n  API:  http://localhost:{API_PORT}/docs")
        print(f"  UI:   http://localhost:{UI_PORT}")
        print(f"\n  Press Ctrl+C to stop\n")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


def main():
    """GUI launcher using tkinter."""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        # Fallback to console
        ChemAgentLauncher().run()
        return

    launcher = ChemAgentLauncher()

    root = tk.Tk()
    root.title("ChemAgent Launcher")
    root.geometry("420x320")
    root.resizable(False, False)

    # Style
    bg = "#1e2a3a"
    fg = "#c8d6e5"
    accent = "#1a73e8"
    root.configure(bg=bg)

    # Title
    title = tk.Label(root, text="ChemAgent", font=("Segoe UI", 20, "bold"),
                     fg="white", bg=bg)
    title.pack(pady=(20, 5))

    subtitle = tk.Label(root, text="Chemical R&D Platform v0.2.0",
                        font=("Segoe UI", 10), fg="#8395a7", bg=bg)
    subtitle.pack()

    # Status frame
    status_frame = tk.Frame(root, bg=bg)
    status_frame.pack(pady=15)

    api_label = tk.Label(status_frame, text="API:  --", font=("Consolas", 10),
                         fg="#e74c3c", bg=bg)
    api_label.grid(row=0, column=0, padx=10, pady=2)

    ui_label = tk.Label(status_frame, text="UI:   --", font=("Consolas", 10),
                        fg="#e74c3c", bg=bg)
    ui_label.grid(row=1, column=0, padx=10, pady=2)

    # Progress
    progress = ttk.Progressbar(root, mode='indeterminate', length=300)
    progress.pack(pady=5)

    # Log
    log_text = tk.Text(root, height=6, width=48, bg="#0f1923", fg="#27ae60",
                       font=("Consolas", 9), relief="flat", borderwidth=0)
    log_text.pack(pady=5, padx=20)

    def log(msg):
        log_text.insert("end", msg + "\n")
        log_text.see("end")

    def update_status():
        import urllib.request
        try:
            urllib.request.urlopen(f"http://localhost:8000/health", timeout=1)
            api_label.config(text="API:  Running", fg="#27ae60")
            try:
                urllib.request.urlopen(f"http://localhost:8501", timeout=1)
                ui_label.config(text="UI:   Running", fg="#27ae60")
            except:
                ui_label.config(text="UI:   Starting...", fg="#e67e22")
        except:
            pass
        root.after(3000, update_status)

    def start_all():
        start_btn.config(state="disabled", text="Starting...")
        progress.start()

        def run():
            if not launcher.check_deps():
                log("Installing dependencies...")
                try:
                    launcher.install_deps()
                    log("Dependencies installed!")
                except Exception as e:
                    log(f"Install failed: {e}")
                    root.after(0, lambda: messagebox.showerror("Error", f"Failed to install: {e}"))
                    root.after(0, lambda: start_btn.config(state="normal", text="Start ChemAgent"))
                    root.after(0, progress.stop)
                    return

            log("Starting API server...")
            if launcher.start_api():
                api_label.config(text="API:  Running", fg="#27ae60")
                log("API server ready on :8000")
            else:
                log("WARNING: API start failed")

            log("Starting UI...")
            launcher.start_ui()
            log("Opening browser...")
            launcher.open_browser()

            start_btn.config(text="Running...", state="disabled")
            stop_btn.config(state="normal")
            progress.stop()
            update_status()

        threading.Thread(target=run, daemon=True).start()

    def stop_all():
        launcher.stop()
        api_label.config(text="API:  Stopped", fg="#e74c3c")
        ui_label.config(text="UI:   Stopped", fg="#e74c3c")
        start_btn.config(text="Start ChemAgent", state="normal")
        stop_btn.config(state="disabled")
        log("All services stopped")

    # Buttons
    btn_frame = tk.Frame(root, bg=bg)
    btn_frame.pack(pady=15)

    start_btn = tk.Button(btn_frame, text="Start ChemAgent", command=start_all,
                          bg=accent, fg="white", font=("Segoe UI", 11, "bold"),
                          relief="flat", padx=20, pady=8, cursor="hand2",
                          activebackground="#1557b0", activeforeground="white")
    start_btn.grid(row=0, column=0, padx=5)

    stop_btn = tk.Button(btn_frame, text="Stop", command=stop_all,
                         bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"),
                         relief="flat", padx=20, pady=8, cursor="hand2",
                         state="disabled",
                         activebackground="#c0392b", activeforeground="white")
    stop_btn.grid(row=0, column=1, padx=5)

    root.protocol("WM_DELETE_WINDOW", lambda: (stop_all(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()

import traceback
import sys
from core.agent import AIAgent
from core.github_client import GitHubClient

class AutomationMonitor:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.agent = None
        self.git_client = None

    def lazy_init(self):
        """Inisialisasi AI hanya saat terjadi error agar hemat memori."""
        if not self.agent:
            self.agent = AIAgent()
            self.git_client = GitHubClient()

    def run_and_monitor(self, target_script_path: str):
        """
        Menjalankan skrip Python lain di workspace, mengawasi kinerjanya,
        dan otomatis memperbaiki jika skrip tersebut crash/error.
        """
        import subprocess
        import os
        from config import Config
        
        full_script_path = os.path.join(Config.WORKSPACE_DIR, target_script_path)
        print(f"[Monitor] Menjalankan dan mengawasi skrip: {target_script_path}")
        
        # Jalankan skrip sebagai subprocess dan tangkap error-nya
        result = subprocess.run(
            [sys.executable, full_script_path],
            capture_output=True,
            text=True
        )
        
        # Cek apakah ada error (return code bukan 0)
        if result.returncode != 0:
            error_log = result.stderr
            print(f"[Monitor] 🚨 Error Terdeteksi di {target_script_path}!\nLog Error:\n{error_log}")
            
            # Panggil AI untuk self-healing
            self.lazy_init()
            print("[Monitor] Meminta AI Lokal memperbaiki error tersebut...")
            ai_status = self.agent.analyze_and_fix(target_script_path, error_log)
            print(ai_status)
            
            # Push perbaikan ke GitHub
            commit_msg = f"Self-Healing Bot: Memperbaiki crash otomatis pada {target_script_path}"
            git_status = self.git_client.commit_and_push(commit_msg)
            print(git_status)
            
            return f"Crash terdeteksi dan berhasil diperbaiki otomatis: {git_status}"
        else:
            print(f"[Monitor] ✅ Skrip {target_script_path} berjalan sukses tanpa error.")
            return "Skrip berjalan sukses."
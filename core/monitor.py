import subprocess
import os
import sys
from config import Config
from core.agent import AIAgent
from core.github_client import GitHubClient

class AutomationMonitor:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.agent = None
        self.git_client = None

    def lazy_init(self):
        """Inisialisasi AI hanya saat terjadi error agar hemat memori GPU T4."""
        if not self.agent:
            self.agent = AIAgent()
            self.git_client = GitHubClient()

    def get_execution_command(self, script_path: str) -> list:
        """Mendapatkan perintah eksekusi berdasarkan ekstensi file secara dinamis."""
        ext = os.path.splitext(script_path)[1].lower()
        
        if ext == '.py':
            return [sys.executable]
        elif ext == '.php':
            return ['php']          
        elif ext == '.js':
            return ['node']         
        elif ext == '.sh':
            return ['bash']
        else:
            return []

    def run_and_monitor(self, target_script_path: str):
        """
        Menjalankan skrip (Python/PHP/JS) di workspace, mengawasi kinerjanya,
        dan otomatis memperbaiki via Pull Request jika skrip tersebut crash.
        """
        full_script_path = os.path.join(Config.WORKSPACE_DIR, target_script_path)
        print(f"[Monitor] Menjalankan dan mengawasi skrip: {target_script_path}")
        
        exec_cmd = self.get_execution_command(target_script_path)
        if exec_cmd:
            full_cmd = exec_cmd + [full_script_path]
        else:
            full_cmd = [full_script_path]

        # Jalankan skrip dengan context directory yang benar (cwd)
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            cwd=Config.WORKSPACE_DIR
        )
        
        # Cek status return code (jika bukan 0 artinya crash/error)
        if result.returncode != 0:
            error_log = result.stderr if result.stderr else result.stdout
            print(f"[Monitor] 🚨 Error Terdeteksi di {target_script_path}!\nLog Error:\n{error_log}")
            
            # Panggil AI untuk self-healing
            self.lazy_init()
            print("[Monitor] Meminta AI Lokal memperbaiki error tersebut...")
            ai_status = self.agent.analyze_and_fix(target_script_path, error_log)
            print(ai_status)
            
            # Buat branch baru dan otomatis Push + Pull Request ke GitHub
            commit_msg = f"Memperbaiki crash otomatis pada {target_script_path}"
            git_status = self.git_client.commit_push_and_pr(commit_msg, error_log)
            print(git_status)
            
            return f"Crash terdeteksi dan berhasil ditangani: {git_status}"
        else:
            print(f"[Monitor] ✅ Skrip {target_script_path} berjalan sukses tanpa error.")
            return "Skrip berjalan sukses."
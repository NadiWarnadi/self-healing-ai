import os
import shutil
from git import Repo
from config import Config

class GitHubClient:
    def __init__(self):
        Config.validate()
        self.token = Config.GITHUB_TOKEN
        self.workspace = Config.WORKSPACE_DIR

    def clone_repository(self, repo_url: str):
        """Mengeklon repositori target ke workspace lokal Colab menggunakan Token."""
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace) # Bersihkan workspace lama
            
        # Format URL agar menggunakan token untuk autentikasi otomatis
        # Contoh: https://<token>@github.com/username/repo.git
        auth_url = repo_url.replace("https://", f"https://{self.token}@")
        
        print(f"[Git] Cloning repository dari {repo_url}...")
        Repo.clone_from(auth_url, self.workspace)
        print("[Git] Clone berhasil.")

    def commit_and_push(self, commit_message: str):
        """Melakukan commit dan push otomatis setelah kode diperbaiki oleh AI."""
        if not os.path.exists(self.workspace):
            return "[Git Error] Workspace kosong, tidak ada repo yang di-clone."
            
        repo = Repo(self.workspace)
        
        # Konfigurasi identitas Git robot Anda
        repo.git.config("user.name", "Self-Healing AI Bot")
        repo.git.config("user.email", "ai-bot@selfhealing.internal")
        
        # Jalankan git add . dan commit
        repo.git.add(A=True)
        if not repo.is_dirty():
            return "[Git] Tidak ada perubahan kode yang terdeteksi."
            
        repo.index.commit(commit_message)
        print(f"[Git] Committing: {commit_message}")
        
        # Push ke branch utama (main/master)
        origin = repo.remote(name='origin')
        origin.push()
        return "[Git] Kode berhasil diperbaiki dan di-push ke GitHub!"
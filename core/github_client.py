import os
import shutil
from git import Repo
from github import Github  # Membutuhkan pip install PyGithub
from config import Config

class GitHubClient:
    def __init__(self):
        Config.validate()
        self.token = Config.GITHUB_TOKEN
        self.workspace = Config.WORKSPACE_DIR
        self.repo_owner = None
        self.repo_name = None

    def _parse_repo_info(self, repo_url: str):
        """Mengekstrak owner dan nama repo dari URL. 
        Contoh: https://github.com/NadiWarnadi/self-healing-ai -> NadiWarnadi, self-healing-ai
        """
        parts = repo_url.rstrip("/").split("/")
        self.repo_name = parts[-1].replace(".git", "")
        self.repo_owner = parts[-2]

    def clone_repository(self, repo_url: str):
        """Mengeklon repositori target ke workspace lokal."""
        self._parse_repo_info(repo_url)
        
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)
            
        auth_url = repo_url.replace("https://", f"https://{self.token}@")
        
        print(f"[Git] Cloning repository dari {repo_url}...")
        Repo.clone_from(auth_url, self.workspace)
        print("[Git] Clone berhasil.")

    def commit_push_and_pr(self, commit_message: str, error_context: str):
        """
        Membuat branch baru, push kode, dan otomatis membuat Pull Request di GitHub.
        """
        if not os.path.exists(self.workspace):
            return "[Git Error] Workspace kosong, tidak ada repo yang di-clone."
            
        repo = Repo(self.workspace)
        
        # 1. Konfigurasi Bot
        repo.git.config("user.name", "Self-Healing AI Bot")
        repo.git.config("user.email", "ai-bot@selfhealing.internal")
        
        # 2. Cek apakah ada perubahan kode
        repo.git.add(A=True)
        if not repo.is_dirty():
            return "[Git] Tidak ada perubahan kode yang terdeteksi dari AI."

        # 3. Buat Branch Baru yang Unik
        import time
        branch_name = f"fix/ai-healing-{int(time.time())}"
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        
        # 4. Commit di Branch Baru
        repo.index.commit(commit_message)
        print(f"[Git] Committing ke branch {branch_name}...")
        
        # 5. Push Branch Baru ke Remote Git
        repo.git.push("--set-upstream", "origin", branch_name)
        print(f"[Git] Push ke branch {branch_name} sukses.")

        # 6. Membuat Pull Request Melalui API GitHub (PyGithub)
        try:
            print("[GitHub API] Sedang membuat Pull Request otomatis...")
            gh = Github(self.token)
            # Ambil objek repositori target
            remote_repo = gh.get_repo(f"{self.repo_owner}/{self.repo_name}")
            
            pr_title = f"🤖 [AI Patch] {commit_message}"
            pr_body = f"""
### 🛠️ Perbaikan Otomatis oleh Self-Healing AI

Sistem mendeteksi adanya kegagalan/crash pada aplikasi Anda dan telah menghasilkan kode perbaikan.

**Detail Log Error yang Diterima AI:**
```text
{error_context}
```
Mohon periksa kembali perubahan kode di bawah ini sebelum melakukan merge ke branch main.
"""
            # Parameter: title, body, base_branch (target merge), head_branch (asal kode)
            pull_request = remote_repo.create_pull(
                title=pr_title,
                body=pr_body,
                base="main",  # Sesuaikan jika default branch Anda 'master'
                head=branch_name
            )

            return f"[Git & PR] Sukses! PR telah dibuat: {pull_request.html_url}"
            
        except Exception as e:
            print(f"[GitHub API Error Details]: {e}")
            return f"[GitHub API Error] Gagal membuat PR, namun branch {branch_name} berhasil di-push."

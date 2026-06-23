import os

class Config:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    WORKSPACE_DIR = "/content/workspace_repo"

    @classmethod
    def validate(cls):
        if not cls.GITHUB_TOKEN:
            raise ValueError("[ERROR] GITHUB_TOKEN tidak ditemukan di Environment/Secrets Colab!")
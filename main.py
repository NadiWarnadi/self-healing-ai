import uvicorn
import os
from config import Config

def main():
    print("==================================================")
    print("🤖 MEMULAI SISTEM SELF-HEALING AI (QWEN-CODER T4) 🤖")
    print("==================================================")
    
    # Validasi awal apakah Environment Token GitHub sudah siap
    try:
        Config.validate()
        print("[System] Validasi token berhasil. Siap berjalan aman tanpa hardcode.")
    except ValueError as e:
        print(str(e))
        print("[Warning] Pastikan Anda mengisi GITHUB_TOKEN di Google Colab Secrets sebelum lanjut!")

    # Jalankan FastAPI Web Server di port 8000
    # Host '0.0.0.0' agar bisa dihubungkan ke Cloudflare Tunnel
    print("[System] Menghidupkan Controller Dashboard pada port 8000...")
    uvicorn.run("controller.app:app", host="0.0.0.0", port=8000, reload=False, loop='asyncio')

if __name__ == "__main__":
    main()
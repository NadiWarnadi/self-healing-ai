from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from core.github_client import GitHubClient
from core.agent import AIAgent
from core.monitor import AutomationMonitor # Impor monitor baru kita
import os

app = FastAPI()

state = {
    "status": "Idle (Menunggu Perintah)",
    "target_repo": "Belum diatur",
    "logs": ["[System] Controller aktif."]
}

def log_message(msg: str):
    print(msg)
    state["logs"].append(msg)

def self_healing_worker(repo_url: str, file_to_fix: str, error_msg: str):
    """Worker untuk perbaikan manual via dashboard log."""
    try:
        git_client = GitHubClient()
        ai_agent = AIAgent()
        
        state["status"] = "Processing: Cloning Repo..."
        log_message(f"[Manual Fix] Memulai perbaikan pada repo: {repo_url}")
        
        git_client.clone_repository(repo_url)
        
        state["status"] = "Processing: AI sedang memperbaiki kode..."
        ai_result = ai_agent.analyze_and_fix(file_to_fix, error_msg)
        log_message(ai_result)
        
        state["status"] = "Processing: Pushing ke GitHub..."
        commit_msg = f"Memperbaiki error pada {file_to_fix}"
        git_result = git_client.commit_push_and_pr(commit_msg, error_msg)
        log_message(git_result)
        
        state["status"] = "Selesai ✨"
    except Exception as e:
        state["status"] = "Error ❌"
        log_message(f"[System Error] Kegagalan: {str(e)}")

def auto_monitor_worker(repo_url: str, target_script: str):
    """Worker untuk clone, eksekusi, dan awasi skrip secara otomatis."""
    try:
        git_client = GitHubClient()
        state["status"] = f"Monitoring: Cloning {repo_url}..."
        log_message(f"[Auto Monitor] Mempersiapkan lingkungan untuk {target_script}")
        
        # 1. Pastikan repo terbaru sudah di-clone
        git_client.clone_repository(repo_url)
        
        # 2. Serahkan kendali ke AutomationMonitor
        state["status"] = f"Monitoring: Menjalankan {target_script}..."
        monitor = AutomationMonitor(repo_url)
        
        # Jalankan dan tangkap hasilnya (jika sukses/crash)
        res_message = monitor.run_and_monitor(target_script)
        log_message(f"[Monitor Output] {res_message}")
        
        if "Crash terdeteksi" in res_message:
            state["status"] = "Selesai Memperbaiki ✨"
        else:
            state["status"] = "Sukses Tanpa Error ✅"
            
    except Exception as e:
        state["status"] = "Error ❌"
        log_message(f"[Monitor Error] Kegagalan pengawasan: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    logs_html = "".join([f"<li>{log}</li>" for log in state["logs"][::-1]])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Self-Healing AI Controller</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f6f9; color: #333; }}
            .container {{ max-width: 900px; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 0 auto; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #eef2f7; padding-bottom: 10px; }}
            .status-box {{ padding: 15px; background: #eef2f7; border-left: 5px solid #3498db; margin-bottom: 20px; font-weight: bold; font-size: 1.1em; }}
            .grid {{ display: flex; gap: 20px; }}
            .card {{ flex: 1; background: #fafbfc; padding: 20px; border: 1px solid #e1e4e8; border-radius: 6px; }}
            input[type="text"], textarea {{ width: 100%; padding: 10px; margin: 8px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }}
            button {{ width: 100%; color: white; padding: 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 15px; font-weight: bold; margin-top: 10px; }}
            .btn-monitor {{ background-color: #3498db; }} .btn-monitor:hover {{ background-color: #2980b9; }}
            .btn-manual {{ background-color: #2ecc71; }} .btn-manual:hover {{ background-color: #27ae60; }}
            .log-container {{ background: #2c3e50; color: #2ecc71; padding: 15px; border-radius: 4px; height: 250px; overflow-y: scroll; font-family: monospace; list-style-type: none; margin-top: 20px; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Self-Healing AI Dashboard</h1>
            <div class="status-box">Status Sekarang: {state["status"]} (Repo: {state["target_repo"]})</div>
            
            <div class="grid">
                <div class="card">
                    <h3>🛡️ Mode 1: Run & Auto-Monitor</h3>
                    <p style="font-size: 12px; color: #666;">AI akan mengklon repo, mengeksekusi script Anda, dan langsung memperbaikinya jika di tengah jalan mendadak crash.</p>
                    <form action="/trigger-monitor" method="post">
                        <label><b>URL Repositori GitHub:</b></label>
                        <input type="text" name="repo_url" placeholder="https://github.com/user/repo" required>
                        <label><b>Script Target (misal: main.py / test.py):</b></label>
                        <input type="text" name="target_script" placeholder="main.py" required>
                        <button type="submit" class="btn-monitor">Jalankan & Awasi Script</button>
                    </form>
                </div>

                <div class="card">
                    <h3>🔧 Mode 2: Manual Error Healing</h3>
                    <p style="font-size: 12px; color: #666;">Gunakan ini jika Anda sudah punya log error mandiri dan ingin AI langsung menyasar file spesifik tanpa mengeksekusi sistem.</p>
                    <form action="/trigger-healing" method="post">
                        <label><b>URL Repositori GitHub:</b></label>
                        <input type="text" name="repo_url" placeholder="https://github.com/user/repo" required>
                        <label><b>File Bermasalah:</b></label>
                        <input type="text" name="file_to_fix" placeholder="core/monitor.py" required>
                        <label><b>Log Error / Stack Trace:</b></label>
                        <textarea name="error_msg" rows="3" placeholder="Paste log error..." required></textarea>
                        <button type="submit" class="btn-manual">Perbaiki File Langsung</button>
                    </form>
                </div>
            </div>
            
            <h3>Sistem Log Terkini:</h3>
            <ul class="log-container">
                {logs_html}
            </ul>
        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/trigger-healing")
async def trigger_healing(background_tasks: BackgroundTasks, repo_url: str = Form(...), file_to_fix: str = Form(...), error_msg: str = Form(...)):
    state["target_repo"] = repo_url
    background_tasks.add_task(self_healing_worker, repo_url, file_to_fix, error_msg)
    return HTMLResponse(content="<script>alert('Proses manual healing dimulai di background!'); window.location.href='/';</script>")

@app.post("/trigger-monitor")
async def trigger_monitor(background_tasks: BackgroundTasks, repo_url: str = Form(...), target_script: str = Form(...)):
    state["target_repo"] = repo_url
    background_tasks.add_task(auto_monitor_worker, repo_url, target_script)
    return HTMLResponse(content="<script>alert('Monitor diaktifkan! AI sedang menguji skrip Anda di background.'); window.location.href='/';</script>")
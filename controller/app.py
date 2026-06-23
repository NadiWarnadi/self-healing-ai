from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from core.github_client import GitHubClient
from core.agent import AIAgent
import os

app = FastAPI()

# Variabel status di memori (State)
state = {
    "status": "Idle (Menunggu Perintah)",
    "target_repo": "Belum diatur",
    "logs": ["[System] Controller aktif."]
}

def log_message(msg: str):
    print(msg)
    state["logs"].append(msg)

def self_healing_worker(repo_url: str, file_to_fix: str, error_msg: str):
    """Worker background agar proses Git & AI tidak membuat web nge-lag (freeze)."""
    try:
        git_client = GitHubClient()
        ai_agent = AIAgent()
        
        state["status"] = "Processing: Cloning Repo..."
        log_message(f"[Process] Memulai perbaikan pada repo: {repo_url}")
        
        # 1. Clone
        git_client.clone_repository(repo_url)
        
        # 2. AI Analisis & Perbaikan
        state["status"] = "Processing: AI sedang memperbaiki kode..."
        ai_result = ai_agent.analyze_and_fix(file_to_fix, error_msg)
        log_message(ai_result)
        
        # 3. Push ke GitHub
        state["status"] = "Processing: Pushing ke GitHub..."
        commit_msg = f"Self-Healing Bot: Memperbaiki error pada {file_to_fix}"
        git_result = git_client.commit_and_push(commit_msg)
        log_message(git_result)
        
        state["status"] = "Selesai ✨"
    except Exception as e:
        state["status"] = "Error ❌"
        log_message(f"[System Error] Terjadi kegagalan sistem: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    # Tampilan UI Dashboard Controller (HTML murni tanpa aset eksternal)
    logs_html = "".join([f"<li>{log}</li>" for log in state["logs"][::-1]]) # Log terbaru di atas
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Self-Healing AI Controller</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f6f9; color: #333; }}
            .container {{ max-width: 800px; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; }}
            .status-box {{ padding: 15px; background: #eef2f7; border-left: 5px solid #3498db; margin-bottom: 20px; font-weight: bold; }}
            input[type="text"], textarea {{ width: 100%; padding: 10px; margin: 8px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }}
            button {{ background-color: #2ecc71; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
            button:hover {{ background-color: #27ae60; }}
            .log-container {{ background: #2c3e50; color: #2ecc71; padding: 15px; border-radius: 4px; height: 250px; overflow-y: scroll; font-family: monospace; list-style-type: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Self-Healing AI Dashboard</h1>
            <div class="status-box">Status Sekarang: {state["status"]}</div>
            
            <form action="/trigger-healing" method="post">
                <label><b>URL Repositori GitHub Target:</b></label>
                <input type="text" name="repo_url" placeholder="https://github.com/username/nama-repo" required>
                
                <label><b>File yang Bermasalah (misal: core/monitor.py):</b></label>
                <input type="text" name="file_to_fix" placeholder="core/monitor.py" required>
                
                <label><b>Pesan / Log Error:</b></label>
                <textarea name="error_msg" rows="4" placeholder="Paste log error atau stack trace di sini..." required></textarea>
                
                <button type="submit">Kirim ke AI & Perbaiki Repo</button>
            </form>
            
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
async def trigger_healing(
    background_tasks: BackgroundTasks, 
    repo_url: str = Form(...), 
    file_to_fix: str = Form(...), 
    error_msg: str = Form(...)
):
    state["target_repo"] = repo_url
    # Jalankan proses di background agar tidak memblokir respon HTTP
    background_tasks.add_task(self_healing_worker, repo_url, file_to_fix, error_msg)
    return HTMLResponse(content="<script>alert('AI mulai bekerja mendeteksi dan memperbaiki kode di background!'); window.location.href='/';</script>")
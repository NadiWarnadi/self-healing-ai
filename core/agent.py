import os
import re
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from duckduckgo_search import DDGS
from config import Config

class AIAgent:
    def __init__(self):
        self.workspace = Config.WORKSPACE_DIR
        self.model_name = "Qwen/Qwen2.5-Coder-7B-Instruct"
        
        print(f"[AI Lokal] Memuat model {self.model_name} ke GPU T4...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name, 
            torch_dtype=torch.float16, 
            device_map="auto"
        )
        self.pipe = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)
        print("[AI Lokal] Model siap digunakan!")

    def search_internet(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=3)]
                summary = ""
                for i, r in enumerate(results):
                    summary += f"[{i+1}] {r['title']}\nSnippet: {r['body']}\n\n"
                return summary
        except Exception as e:
            return f"Gagal mencari di internet: {str(e)}"

    def extract_clean_code(self, raw_text: str, ext: str) -> str:
        """Mengambil kode dari markdown block sesuai ekstensi bahasa."""
        lang_tag = ext.replace('.', '')
        patterns = [
            rf"```{lang_tag}\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```"
        ]
        for pattern in patterns:
            match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return raw_text.strip()

    def validate_syntax(self, file_path: str) -> bool:
        """Memeriksa validitas sintaks secara universal menggunakan CLI Tool bawaan bahasa."""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.py':
                import py_compile
                py_compile.compile(file_path, doraise=True)
                return True
            elif ext == '.php':
                res = subprocess.run(['php', '-l', file_path], capture_output=True, text=True)
                return res.returncode == 0
            elif ext == '.js':
                res = subprocess.run(['node', '--check', file_path], capture_output=True, text=True)
                return res.returncode == 0
            
            # Jika bahasa lain belum didukung linter-nya, loloskan dahulu
            return True
        except Exception as e:
            print(f"[Validation Error] Gagal memvalidasi sintaks: {str(e)}")
            return False

    def analyze_and_fix(self, file_path: str, error_message: str) -> str:
        full_path = os.path.join(self.workspace, file_path)
        ext = os.path.splitext(file_path)[1].lower()
        
        if not os.path.exists(full_path):
            return f"[AI Error] File {file_path} tidak ditemukan di workspace."

        with open(full_path, "r", encoding="utf-8") as f:
            broken_code = f.read()

        print(f"[AI] Meneliti solusi di internet untuk error...")
        internet_context = self.search_internet(f"fix error {error_message}")

        messages = [
            {"role": "system", "content": "Kamu adalah AI Senior Multi-Language Programmer. Perbaiki kode yang error. Kamu WAJIB mengembalikan kode perbaikan yang UTUH dan LENGKAP di dalam block markdown ```. Jangan berikan penjelasan teks apa pun di luar block tersebut."},
            {"role": "user", "content": f"""
            Tolong perbaiki file: {file_path}
            Pesan Error: {error_message}
            Referensi Solusi: {internet_context}
            Kode Saat Ini:
            ```
            {broken_code}
            ```
            """}
        ]

        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        outputs = self.pipe(prompt, max_new_tokens=2048, do_sample=False, temperature=0.1)
        response_content = outputs[0]["generated_text"][len(prompt):].strip()
        
        fixed_code = self.extract_clean_code(response_content, ext)

        temp_path = full_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)

        if self.validate_syntax(temp_path):
            os.replace(temp_path, full_path)
            return f"[AI Lokal] Sukses! Kode pada {file_path} telah diperbaiki & lolos uji sintaks."
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise ValueError(f"[AI Error] Kode {ext} hasil regenerasi AI mengandung kesalahan sintaks (SyntaxError). Proses dihentikan.")
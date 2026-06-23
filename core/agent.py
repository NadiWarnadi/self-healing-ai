import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from duckduckgo_search import DDGS
from config import Config

class AIAgent:
    def __init__(self):
        self.workspace = Config.WORKSPACE_DIR
        self.model_name = "Qwen/Qwen2.5-Coder-7B-Instruct" # Model paling top untuk coding saat ini yang muat di T4
        
        print(f"[AI Lokal] Memuat model {self.model_name} ke GPU T4... (Mohon tunggu, ini butuh beberapa menit saat awal)")
        
        # Inisialisasi Tokenizer dan Model langsung ke GPU (cuda)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16, # Menghemat VRAM T4 agar tidak crash
            device_map="auto"
        )
        
        # Buat pipeline generator teks
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer
        )
        print("[AI Lokal] Model berhasil dimuat ke GPU T4 dan siap digunakan!")

    def search_internet(self, query: str) -> str:
        """Tool bagi AI untuk mencari solusi error di internet."""
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=3)]
                summary = ""
                for i, r in enumerate(results):
                    summary += f"[{i+1}] {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}\n\n"
                return summary
        except Exception as e:
            return f"Gagal mencari di internet: {str(e)}"

    def analyze_and_fix(self, file_path: str, error_message: str) -> str:
        """Fungsi utama AI lokal menganalisis dan memperbaiki kode."""
        full_path = os.path.join(self.workspace, file_path)
        
        if not os.path.exists(full_path):
            return f"[AI Error] File {file_path} tidak ditemukan di workspace."

        # Baca kode yang rusak
        with open(full_path, "r", encoding="utf-8") as f:
            broken_code = f.read()

        # Langkah 1: Browsing internet untuk referensi
        print(f"[AI] Sedang mencari referensi internet untuk error: {error_message}")
        internet_context = self.search_internet(f"python fix error {error_message}")

        # Langkah 2: Buat prompt untuk Model Lokal
        messages = [
            {"role": "system", "content": "Kamu adalah AI ahli pemrograman. Perbaiki kode Python yang error. Berikan HANYA kode perbaikan yang utuh di dalam block markdown ```python tanpa teks penjelasan lainnya."},
            {"role": "user", "content": f"""
            Tolong perbaiki file: {file_path}
            
            Pesan Error:
            {error_message}

            Referensi Solusi Internet:
            {internet_context}

            Kode Saat Ini:
            ```python
            {broken_code}
            ```
            """}
        ]

        # Format prompt sesuai standar model Qwen/Llama
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        print("[AI Lokal] Menjalankan inferensi di GPU T4 untuk memperbaiki kode...")
        outputs = self.pipe(
            prompt,
            max_new_tokens=2048,
            do_sample=False, # False agar jawabannya pasti dan fokus pada perbaikan kode
            temperature=0.1
        )

        generated_text = outputs[0]["generated_text"]
        
        # Ambil hanya respon setelah prompt selesai (jawaban AI-nya saja)
        response_content = generated_text[len(prompt):].strip()
        
        # Bersihkan tag markdown ```python dan ``` jika ada
        fixed_code = response_content.replace("```python", "").replace("```", "").strip()

        # Langkah 3: Tulis balik kode yang sudah diperbaiki ke file asli
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)

        return f"[AI Lokal] Sukses! Kode pada file {file_path} telah direkondisi menggunakan GPU T4."
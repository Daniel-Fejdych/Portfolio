import tkinter as tk
import threading
import queue
import requests
import json
import time

# ========== CONFIG ==========
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "hf.co/DavidAU/Qwen3-4B-Gemini-TripleX-High-Reasoning-Thinking-Heretic-Uncensored-GGUF:Q8_0"  # Change if needed
MAX_BUFFER = 16
# ============================

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Prompt Sender")

        self.prompt_queue = queue.Queue(maxsize=MAX_BUFFER)
        self.generating = False

        # GUI Elements
        self.input_box = tk.Entry(root, width=60)
        self.input_box.pack(padx=10, pady=10)

        self.send_button = tk.Button(root, text="Send", command=self.send_prompt)
        self.send_button.pack(pady=5)

        self.status_label = tk.Label(root, text="Idle")
        self.status_label.pack(pady=5)

        # Worker thread
        self.worker_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.worker_thread.start()

    def send_prompt(self):
        prompt = self.input_box.get().strip()
        if not prompt:
            return

        if self.prompt_queue.full():
            self.status_label.config(text="Buffer full (16 prompts max)")
            return

        self.prompt_queue.put(prompt)
        self.input_box.delete(0, tk.END)

        if self.generating:
            self.status_label.config(
                text=f"Prompt buffered ({self.prompt_queue.qsize()} in queue)"
            )
        else:
            self.status_label.config(text="Prompt queued")

    def process_queue(self):
        while True:
            prompt = self.prompt_queue.get()
            self.generating = True
            self.update_status("Generating...")

            self.generate_from_ollama(prompt)

            self.generating = False

            if self.prompt_queue.empty():
                self.update_status("Idle — No prompts buffered.")
            else:
                self.update_status(
                    f"{self.prompt_queue.qsize()} prompt(s) remaining..."
                )

            self.prompt_queue.task_done()

    def generate_from_ollama(self, prompt):
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": True
        }

        try:
            with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            print(data["response"], end="", flush=True)
                        if data.get("done"):
                            print("\n--- Generation Complete ---\n")
        except Exception as e:
            print("Error communicating with Ollama:", e)

    def update_status(self, message):
        self.root.after(0, lambda: self.status_label.config(text=message))


if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()

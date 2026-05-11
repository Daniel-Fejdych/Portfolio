import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import ollama

class PairFrame(ttk.Frame):
    """A frame containing a prompt text, response text, and a remove button."""
    def __init__(self, parent, prompt_text="", response_text="", remove_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.remove_callback = remove_callback

        # Configure grid weights so text boxes expand
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)

        # Prompt text box
        self.prompt = tk.Text(self, height=3, wrap=tk.WORD)
        self.prompt.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        self.prompt.insert("1.0", prompt_text)

        # Response text box
        self.response = tk.Text(self, height=3, wrap=tk.WORD)
        self.response.grid(row=0, column=1, sticky="nsew", padx=(2, 2))
        self.response.insert("1.0", response_text)

        # Remove button
        self.remove_btn = ttk.Button(self, text="✖", width=3, command=self.remove)
        self.remove_btn.grid(row=0, column=2, sticky="ns", padx=(2, 0))

    def remove(self):
        """Destroy this frame and notify the parent."""
        if self.remove_callback:
            self.remove_callback(self)
        self.destroy()

    def get_pair(self):
        """Return (prompt, response) as strings."""
        return (self.prompt.get("1.0", "end-1c"), self.response.get("1.0", "end-1c"))


class OllamaChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Chat")
        self.root.geometry("800x600")

        # Default Ollama model (change as needed)
        self.model = "llama3.2:3b"  # or "llama3.2:3b", "mistral", etc.

        # System prompt area
        sys_frame = ttk.Frame(root)
        sys_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(sys_frame, text="System Prompt:").pack(anchor=tk.W)
        self.system_text = tk.Text(sys_frame, height=3, wrap=tk.WORD)
        self.system_text.pack(fill=tk.X, expand=True)

        # Scrollable area for conversation pairs
        self.canvas = tk.Canvas(root, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.pairs_frame = ttk.Frame(self.canvas)
        self.pairs_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.pairs_frame, anchor="nw")

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Current prompt area
        current_frame = ttk.Frame(root)
        current_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(current_frame, text="Current Prompt:").pack(anchor=tk.W)
        self.current_text = tk.Text(current_frame, height=3, wrap=tk.WORD)
        self.current_text.pack(fill=tk.X, expand=True)

        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        self.send_btn = ttk.Button(btn_frame, text="Send", command=self.send)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        self.add_btn = ttk.Button(btn_frame, text="Add", command=self.add)
        self.add_btn.pack(side=tk.LEFT, padx=5)

        # Keep track of pair frames
        self.pairs = []

    def add_pair(self, prompt="", response=""):
        """Add a new pair frame to the scrollable area."""
        pair = PairFrame(self.pairs_frame, prompt, response, remove_callback=self.remove_pair)
        pair.pack(fill=tk.X, pady=2, padx=5)
        self.pairs.append(pair)

    def remove_pair(self, pair):
        """Remove a pair from the list."""
        if pair in self.pairs:
            self.pairs.remove(pair)

    def get_history_messages(self):
        """Return a list of messages from the system prompt and all pairs."""
        messages = []
        system = self.system_text.get("1.0", "end-1c").strip()
        if system:
            messages.append({"role": "system", "content": system})
        for pair in self.pairs:
            prompt, response = pair.get_pair()
            if prompt.strip():
                messages.append({"role": "user", "content": prompt.strip()})
            if response.strip():
                messages.append({"role": "assistant", "content": response.strip()})
        return messages

    def send(self):
        """Send the current prompt along with history to Ollama."""
        current = self.current_text.get("1.0", "end-1c").strip()
        if not current:
            messagebox.showwarning("No prompt", "Please enter a current prompt.")
            return

        # Disable buttons during request
        self.send_btn.config(state=tk.DISABLED)
        self.add_btn.config(state=tk.DISABLED)

        # Prepare messages
        messages = self.get_history_messages()
        messages.append({"role": "user", "content": current})

        # Run Ollama in a separate thread to avoid freezing GUI
        threading.Thread(target=self._ollama_request, args=(messages, current), daemon=True).start()

    def _ollama_request(self, messages, current_prompt):
        """Perform the actual Ollama request (runs in background thread)."""
        try:
            response = ollama.chat(model=self.model, messages=messages)
            reply = response['message']['content'].strip()
        except Exception as e:
            reply = f"[Error: {e}]"

        # Schedule UI update in main thread
        self.root.after(0, self._handle_response, reply, current_prompt)

    def _handle_response(self, reply, current_prompt):
        """Add the new pair and clear current prompt."""
        # Add the new pair (current prompt + response)
        self.add_pair(prompt=current_prompt, response=reply)

        # Clear current prompt
        self.current_text.delete("1.0", tk.END)

        # Re-enable buttons
        self.send_btn.config(state=tk.NORMAL)
        self.add_btn.config(state=tk.NORMAL)

    def add(self):
        """Manually add the current prompt as a user message with empty response."""
        current = self.current_text.get("1.0", "end-1c").strip()
        if not current:
            messagebox.showwarning("No prompt", "Please enter a prompt to add.")
            return

        self.add_pair(prompt=current, response="")
        self.current_text.delete("1.0", tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaChatGUI(root)
    root.mainloop()

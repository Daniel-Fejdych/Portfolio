import json
import requests
import re



from ch import *
# Has ch1, ch2, ch3, and plan Strings defined.

from docx import Document

def app(text_to_append):
    """
    Appends a string to the end of a Microsoft Word (.docx) file.
    
    :param text_to_append: Text to add at the end of the document
    """
    doc = Document("story.docx")
    doc.add_paragraph(text_to_append)
    doc.save("story.docx")

chapters = []

class Last3Chapters:
    def __init__(self):
        self._strings = []
        self._max_size = 3

    def add(self, new_string: str):
        if len(self._strings) >= self._max_size:
            # Remove the oldest added string (first in the list)
            self._strings.pop(0)
        self._strings.append(new_string)

    def get(self):
        return "".join(list(self._strings))  # Return a copy to prevent external modification
last_3_chapters = Last3Chapters()

ch1 = re.sub(r'\n\s*\n', '\n', ch1)
ch2 = re.sub(r'\n\s*\n', '\n', ch2)
ch3 = re.sub(r'\n\s*\n', '\n', ch3)

last_3_chapters.add(ch1)
last_3_chapters.add(ch2)
last_3_chapters.add(ch3)


OLLAMA_URL = "http://localhost:11434/api/generate"

def ollama_generate(prompt, model="llama3.2:3b"):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=720
        )
        response.raise_for_status()
        return response.json()["response"]
    except:
        print("WOOWWOWOWOOWOWOWOWOWOWOWOWOWOW")
        pass

p_start = "Using these plot points defined per each arc: "
p_mid = " And these last three chapters: "
p_end = " Generate the next chapter."

for i in range(0, 20):
    prompt = p_start + plan + p_mid + last_3_chapters.get() + p_end
    ch = ollama_generate(prompt)
    print(ch)
    last_3_chapters.add(ch)
    app(ch)


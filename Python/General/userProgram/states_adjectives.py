import requests
import json

def get_states_and_adjectives(item: str):
    url = "http://localhost:11434/api/generate"

    prompt = f"""
        You are a helpful assistant.

        Given the thing: "{item}"

        Return:
        1. A list of common states that the thing can take (e.g. raw, cooked, melted, spun, oxidized)
        2. A list of typical adjectives used to describe it (e.g. wet, metallic, fresh, warm, cold)
        "Requirements:\n"
        "1) Output ONLY a single valid JSON object (no explanatory text).\n"
        "2) All items lowercase, no punctuation, no duplicates, short (1–3 words each).\n"
        "3) Prefer concrete physical states and common adjectives relevant to the item.\n\n"

        Respond ONLY as valid JSON in this format:
        {{
          "states": ["state1", "state2"],
          "adjectives": ["adj1", "adj2"]
        }}
        """

    payload = {
        "model": "hf.co/DavidAU/Qwen3-4B-Gemini-TripleX-High-Reasoning-Thinking-Heretic-Uncensored-GGUF:Q8_0",
        "prompt": prompt,
        "stream": False
    }
        
    response = requests.post(url, json=payload)
    response.raise_for_status()

    data = response.json()
    text = data["response"].strip()

    parsed = json.loads(text)

    states = parsed.get("states", [])
    adjectives = parsed.get("adjectives", [])

    return states, adjectives


for i in ["gold", "silver", "meat", "bone", "skin", "water", "iron", "chocolate", "brick"]:
    states, adjectives = get_states_and_adjectives(i)
    print(i)
    print("States:", states)
    print("Adjectives:", adjectives)



    #You are a precise assistant. Given the noun gold,
##return a JSON object with exactly two keys: "states" and "adjectives".
##- "states": an array (4–12) of short words (nouns/adjectival-phrases) describing
##common states or conditions that the thing can take (e.g. raw, cooked, melted,
##spun, oxidized).
##- "adjectives": an array (4–12) of adjectives commonly used to describe the thing.
##Requirements:
##1) Output ONLY a single valid JSON object (no explanatory text).
##2) All items lowercase, no punctuation, no duplicates, short (1–3 words each).
##3) Prefer concrete physical states and common adjectives relevant to the item.
##Example output:
##{"states":["raw","cooked","frozen"],"adjectives":["tender","fresh","smoked"]}
##Now produce the JSON for: gold

import requests
import json
import typing
import re

def _extract_first_json_block(text: str) -> typing.Optional[str]:
    """Find first well-formed JSON object in a string by matching braces."""
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

def get_states_and_adjectives(
    item: str,
    model: str = "hf.co/DavidAU/Qwen3-4B-Gemini-TripleX-High-Reasoning-Thinking-Heretic-Uncensored-GGUF:Q8_0",
    base_url: str = "http://localhost:11434/api/generate",
    timeout: int = 300
) -> typing.Tuple[typing.List[str], typing.List[str]]:
    """
    Send `item` to a local Ollama instance and request two lists:
      - states: short nouns describing common states the item can take
      - adjectives: typical adjectives used for the item

    Returns: (states_list, adjectives_list) — both are lists of strings.
    On failure returns two empty lists.
    """
    # Build a constrained prompt that asks for JSON only
    prompt = (
        f"You are a precise assistant. Given the single-word or short noun '{item}', "
        "return a JSON object with exactly two keys: \"states\" and \"adjectives\".\n\n"
        "- \"states\": an array (4–12) of short words (nouns/adjectival-phrases) describing "
        "common states or conditions that the thing can take (e.g. raw, cooked, melted, "
        "spun, oxidized).\n"
        "- \"adjectives\": an array (4–12) of adjectives commonly used to describe the thing.\n\n"
        "Requirements:\n"
        "1) Output ONLY a single valid JSON object (no explanatory text).\n"
        "2) All items lowercase, no punctuation, no duplicates, short (1–3 words each).\n"
        "3) Prefer concrete physical states and common adjectives relevant to the item.\n\n"
        "Example output:\n"
        '{"states":["raw","cooked","frozen"],"adjectives":["tender","fresh","smoked"]}\n\n'
        "Now produce the JSON for: " + item
    )

    payload = {
        "model": model,
        "prompt": prompt,
        # keep the generation deterministic-ish
        "temperature": 0.2,
        "max_tokens": 200
    }

    try:
        resp = requests.post(base_url, json=payload, timeout=timeout)
    except requests.RequestException as e:
        # Could not contact Ollama
        print(f"[error] could not contact ollama at {base_url}: {e}")
        return [], []

    if resp.status_code != 200:
        print(f"[error] ollama returned status {resp.status_code}: {resp.text[:400]}")
        return [], []

    text = resp.text.strip()
    # Try direct JSON parse first
    try:
        parsed = json.loads(text)
    except Exception as e:
        print(e)
        # Extract first JSON block and try again
        json_block = _extract_first_json_block(text)
        print(json_block)
        if json_block:
            try:
                parsed = json.loads(json_block)
            except Exception:
                parsed = None
        else:
            parsed = None

    states = []
    adjectives = []

    if isinstance(parsed, dict):
        # Safely pull lists if present, coerce to list[str]
        raw_states = parsed.get("states") or parsed.get("state") or parsed.get("States")
        raw_adj = parsed.get("adjectives") or parsed.get("adjective") or parsed.get("Adjectives")

        def _to_list_of_str(x):
            if x is None:
                return []
            if isinstance(x, str):
                # maybe comma separated
                return [s.strip().lower() for s in re.split(r'[,\n;]+', x) if s.strip()]
            if isinstance(x, (list, tuple)):
                out = []
                for v in x:
                    if v is None:
                        continue
                    vs = str(v).strip().lower()
                    # strip surrounding punctuation
                    vs = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', vs)
                    if vs:
                        out.append(vs)
                return out
            # fallback
            return [str(x).strip().lower()]

        states = _to_list_of_str(raw_states)
        adjectives = _to_list_of_str(raw_adj)

    else:
        # last resort: try to parse simple labeled lists inside text
        # look for "states:" and "adjectives:" lines
        lower = text.lower()
        s_match = re.search(r"states[:\s]*\[([^\]]+)\]", lower)
        a_match = re.search(r"adjectives[:\s]*\[([^\]]+)\]", lower)
        if s_match:
            items = [s.strip() for s in s_match.group(1).split(",") if s.strip()]
            states = [re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', it.lower()) for it in items]
        if a_match:
            items = [s.strip() for s in a_match.group(1).split(",") if s.strip()]
            adjectives = [re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', it.lower()) for it in items]

    # Deduplicate while preserving order
    def _dedup_keep_order(lst):
        seen = set()
        out = []
        for v in lst:
            if v not in seen:
                seen.add(v)
                out.append(v)
        return out

    states = _dedup_keep_order(states)
    adjectives = _dedup_keep_order(adjectives)

    # Final sanitization: enforce simple tokens and reasonable length
    def _sanitize(lst):
        cleaned = []
        for item in lst:
            item = item.strip().lower()
            # drop extremely long items
            if not item or len(item) > 40:
                continue
            cleaned.append(item)
        return cleaned[:12]  # cap at 12
    states = _sanitize(states)
    adjectives = _sanitize(adjectives)

    return states, adjectives


# Example usage:
if __name__ == "__main__":
    for test in ("gold", "meat", "cotton"):
        s, a = get_states_and_adjectives(test)
        print(f"\n== {test} ==")
        print("states:", s)
        print("adjectives:", a)

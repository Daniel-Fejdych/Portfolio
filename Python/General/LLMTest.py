# =========================
# Imports
# =========================

import sys
import requests
import string
import random

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QScrollArea,
)

# =========================
# UI Styling & Constants
# =========================

APP_STYLE = """
    QWidget {
        background-color: #f0f8f7;
        color: #0f1927;
        font-family: "Segoe UI", "Inter", sans-serif;
        font-size: 10.5pt;
    }
"""

# Defines the height of each row (buttons + labels)
ROW_MIN_HEIGHT = 120

SELECT_BUTTON_STYLE = """
    QPushButton {
        background-color: #ef4444;
        color: white;
        border: 1px solid #dc2626;
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 500;
    }
    QPushButton:hover { background-color: #dc2626; }
    QPushButton:pressed { background-color: #b91c1c; }
"""

SELECTED_BUTTON_STYLE = """
    QPushButton {
        background-color: #2563eb;
        color: white;
        border: 2px solid #1d4ed8;
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 600;
    }
"""

LABEL_STYLE = """
    QLabel {
        background-color: #e8f2ff;
        color: #1c4ed8;
        border: 1px solid #93c5fd;
        border-radius: 6px;
        padding: 6px 8px;
    }
"""

TEXT_BOX_STYLE = """
    QTextEdit {
        background-color: #ffffff;
        color: #1f2937;
        border: 1px solid #c7d2fe;
        border-radius: 6px;
        padding: 6px 8px;
    }
"""

UI_TEXT = {
    "choose_player": "Choose\nthis Player",
    "submit": "Submit",
    "loading": "⏳ Generating prompt…",
}

# =========================
# Game Constants
# =========================

VISIBILITY_PUBLIC = "public"
VISIBILITY_WHISPER = "whisper"

# Werewolf roles are intentionally minimal for now
WEREWOLF_ROLES = {
    "villager": {
        "team": "village",
        "description": (
            "You are a Villager. You do not have special powers. "
            "Your goal is to identify and eliminate the Werewolves."
        ),
    },
    "werewolf": {
        "team": "werewolves",
        "description": (
            "You are a Werewolf. You appear innocent during the day. "
            "Your goal is to mislead the village."
        ),
    },
}

# Each LLM has:
# - a personality style
# - a hidden role
PLAYER_PROFILES = [
    ("suspicious", "villager"),
    ("expert", "villager"),
    ("newbie", "villager"),
    ("innocent", "werewolf"),
]

NUM_LLM_PLAYERS = len(PLAYER_PROFILES)
NUM_TOTAL_PLAYERS = NUM_LLM_PLAYERS + 1  # +1 human

# Debug-friendly defaults
HUMAN_QUESTIONS_PER_ROUND = 3
LLM_QUESTIONS_PER_ROUND = 1

INCLUDE_OTHER_PLAYERS_CONTEXT = True

# =========================
# Helper Functions
# =========================

def player_label(player_id: int) -> str:
    """
    Converts a player seat index into a display label.
    Example: 0 -> Player A, 1 -> Player B, etc.
    """
    if not isinstance(player_id, int):
        return "Unknown"
    if player_id < 0 or player_id >= NUM_TOTAL_PLAYERS:
        return "Unknown"
    return f"Player {string.ascii_uppercase[player_id]}"


def parse_llm_question(text):
    """
    Attempts to parse a structured LLM question.

    Expected format:
        TARGET: Player X
        VISIBILITY: public|whisper
        TEXT: <question>

    Returns:
        (target_player_id, visibility, question_text)
        or None if parsing fails.
    """
    try:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        data = {}

        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.upper()] = v.strip()

        if "TARGET" not in data or "TEXT" not in data:
            raise ValueError("Missing TARGET or TEXT")

        letter = data["TARGET"].replace("Player", "").strip()
        player_id = string.ascii_uppercase.index(letter)

        visibility = data.get("VISIBILITY", VISIBILITY_PUBLIC)
        if visibility not in (VISIBILITY_PUBLIC, VISIBILITY_WHISPER):
            visibility = VISIBILITY_PUBLIC

        return player_id, visibility, data["TEXT"]

    except Exception as e:
        print("[LLM PARSE ERROR]", e)
        print(text)
        return None

# =========================
# Main Game Window
# =========================

class WerewolfGameWindow(QWidget):
    """
    Main application window.

    Responsibilities:
    - Render UI
    - Track turn/phase state
    - Route messages between human and LLMs
    - Enforce game flow rules
    """

    def __init__(self, button_configs):
        super().__init__()
        self.setWindowTitle("Imposter Interface")
        self.resize(1000, 500)

        # ---- Turn / phase state ----
        self.phase = "human"  # human -> llm -> vote
        self.human_questions_left = HUMAN_QUESTIONS_PER_ROUND
        self.current_llm_turn = 0
        self.llm_questions_left = {
            i: LLM_QUESTIONS_PER_ROUND for i in range(NUM_LLM_PLAYERS)
        }

        # Used when an LLM asks the human a question
        self.waiting_for_human_answer = False
        self.pending_llm_question = None

        # ---- Seating model ----
        self.player_seats = list(range(NUM_TOTAL_PLAYERS))
        random.shuffle(self.player_seats)

        self.human_player_id = self.player_seats[-1]
        self.llm_player_ids = {
            i: self.player_seats[i] for i in range(NUM_LLM_PLAYERS)
        }

        # Dialogue history is indexed by LLM index
        self.dialogue_history = [[] for _ in range(NUM_TOTAL_PLAYERS)]

        self.whisper_mode = False
        self.selected_player = None

        self.setStyleSheet(APP_STYLE)
        self._build_ui(button_configs)

        # ---- Background startup worker ----
        self.worker = LLMWorker()
        self.worker.prompt_ready.connect(self.update_player_text)
        self.worker.start()

        self.chat_worker = None

    # -------------------------
    # UI Construction
    # -------------------------

    def _build_ui(self, button_configs):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.player_buttons = []
        self.player_labels = []

        for index, text in enumerate(button_configs):
            layout.addLayout(self._create_player_row(text, index))

        self.text_input = QTextEdit()
        self.text_input.setStyleSheet(TEXT_BOX_STYLE)
        self.text_input.setMinimumHeight(100)
        layout.addWidget(self.text_input)

        self.whisper_button = QPushButton("Whisper: OFF")
        self.whisper_button.setCheckable(True)
        self.whisper_button.clicked.connect(self.toggle_whisper)
        layout.addWidget(self.whisper_button)

        submit = QPushButton(UI_TEXT["submit"])
        submit.clicked.connect(self.submit_text)
        layout.addWidget(submit)

        self.setLayout(layout)

    def _create_player_row(self, text, index):
        row = QHBoxLayout()

        button = QPushButton(UI_TEXT["choose_player"])
        button.setFixedSize(ROW_MIN_HEIGHT, ROW_MIN_HEIGHT)
        button.setStyleSheet(SELECT_BUTTON_STYLE)
        button.clicked.connect(lambda _, i=index: self.select_player(i))

        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(LABEL_STYLE)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(label)

        self.player_buttons.append(button)
        self.player_labels.append(label)

        row.addWidget(button)
        row.addWidget(scroll)
        return row

    # -------------------------
    # Input Handling
    # -------------------------

    def submit_text(self):
        """
        Handles ALL human input:
        - Answering LLM questions
        - Asking LLMs questions
        """
        text = self.text_input.toPlainText().strip()
        if not text:
            return

        self.text_input.clear()

        # Human answering an LLM question
        if self.waiting_for_human_answer:
            llm_index, _ = self.pending_llm_question
            self.waiting_for_human_answer = False
            self.pending_llm_question = None

            self.dialogue_history[llm_index].append({
                "speaker": self.human_player_id,
                "text": text,
                "visibility": VISIBILITY_PUBLIC,
                "targets": [self.llm_player_ids[llm_index]],
            })

            self.llm_questions_left[llm_index] -= 1
            self.current_llm_turn += 1
            self.advance_llm_turn()
            return

        # Human asking a question
        if self.phase != "human":
            print("It is not your turn.")
            return

        if self.selected_player is None:
            print("Select a player first.")
            return

        self.human_questions_left -= 1

        self.dialogue_history[self.selected_player].append({
            "speaker": self.human_player_id,
            "text": text,
            "visibility": VISIBILITY_WHISPER if self.whisper_mode else VISIBILITY_PUBLIC,
            "targets": [self.llm_player_ids[self.selected_player]],
        })

        prompt = build_prompt(
            self.selected_player,
            self.dialogue_history,
            self.llm_player_ids,
            INCLUDE_OTHER_PLAYERS_CONTEXT,
        )

        self.player_labels[self.selected_player].setText(
            self.render_dialogue(self.selected_player, thinking=True)
        )

        self.chat_worker = ChatWorker(self.selected_player, prompt)
        self.chat_worker.response_ready.connect(self.on_chat_response)
        self.chat_worker.start()

        if self.human_questions_left <= 0:
            self.start_llm_phase()

    # -------------------------
    # Turn / Phase Control
    # -------------------------

    def start_llm_phase(self):
        print("Human phase over. LLMs are now asking questions.")
        self.phase = "llm"
        self.current_llm_turn = 0
        self.advance_llm_turn()

    def advance_llm_turn(self):
        if self.current_llm_turn >= NUM_LLM_PLAYERS:
            self.start_vote_phase()
            return

        if self.llm_questions_left[self.current_llm_turn] <= 0:
            self.current_llm_turn += 1
            self.advance_llm_turn()
            return

        self.ask_llm_to_question(self.current_llm_turn)

    def start_vote_phase(self):
        self.phase = "vote"
        print("Voting phase started")

    # -------------------------
    # LLM Interaction
    # -------------------------

    def ask_llm_to_question(self, llm_index):
        prompt = build_prompt(
            llm_index,
            self.dialogue_history,
            self.llm_player_ids,
            INCLUDE_OTHER_PLAYERS_CONTEXT,
        )

        prompt += (
            "\nIt is now your turn to ASK A QUESTION.\n"
            "Respond in the specified structured format."
        )

        self.chat_worker = ChatWorker(llm_index, prompt)
        self.chat_worker.response_ready.connect(self.on_llm_question)
        self.chat_worker.start()

    def on_llm_question(self, llm_index, response):
        parsed = parse_llm_question(response)

        if not parsed:
            print(f"[ERROR] Invalid question from LLM {llm_index}")
            self.ask_llm_to_question(llm_index)
            return

        target_id, visibility, question = parsed
        speaker_id = self.llm_player_ids[llm_index]

        if target_id == self.human_player_id:
            self.waiting_for_human_answer = True
            self.pending_llm_question = (llm_index, question)
            return

        self.dialogue_history[llm_index].append({
            "speaker": speaker_id,
            "text": question,
            "visibility": visibility,
            "targets": [target_id] if visibility == VISIBILITY_WHISPER else [],
        })

        self.llm_questions_left[llm_index] -= 1
        self.current_llm_turn += 1
        self.advance_llm_turn()

    def on_chat_response(self, player_index, response):
        self.dialogue_history[player_index].append({
            "speaker": self.llm_player_ids[player_index],
            "text": response,
            "visibility": VISIBILITY_PUBLIC,
            "targets": [self.human_player_id],
        })

        self.player_labels[player_index].setText(
            self.render_dialogue(player_index)
        )

    # -------------------------
    # Rendering & UI Helpers
    # -------------------------

    def render_dialogue(self, player_index, thinking=False):
        lines = []
        for entry in self.dialogue_history[player_index]:
            if entry["visibility"] == VISIBILITY_PUBLIC:
                lines.append(
                    f"{player_label(entry['speaker'])}: {entry['text']}"
                )
        if thinking:
            lines.append("⏳ thinking…")
        return "\n\n".join(lines)

    def select_player(self, index):
        self.selected_player = index
        self.whisper_button.setChecked(False)
        self.toggle_whisper(False)

        for b in self.player_buttons:
            b.setStyleSheet(SELECT_BUTTON_STYLE)
        self.player_buttons[index].setStyleSheet(SELECTED_BUTTON_STYLE)

    def toggle_whisper(self, checked):
        self.whisper_mode = checked
        self.whisper_button.setText(
            "Whisper: ON" if checked else "Whisper: OFF"
        )

# =========================
# Background Workers
# =========================

class LLMWorker(QThread):
    prompt_ready = pyqtSignal(int, str)

    def run(self):
        for index, (style, role) in enumerate(PLAYER_PROFILES):
            self.prompt_ready.emit(
                index,
                generate_initial_player_prompt(style, role)
            )

class ChatWorker(QThread):
    response_ready = pyqtSignal(int, str)

    def __init__(self, player_index, prompt):
        super().__init__()
        self.player_index = player_index
        self.prompt = prompt

    def run(self):
        self.response_ready.emit(
            self.player_index,
            ollama_generate(self.prompt)
        )

# =========================
# LLM Utilities
# =========================

OLLAMA_URL = "http://localhost:11434/api/generate"

def ollama_generate(prompt, model="llama3.2:3b"):
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["response"]
    except Exception as e:
        return f"[LLM error: {e}]"

def generate_initial_player_prompt(style, role_name):
    role = WEREWOLF_ROLES[role_name]
    return ollama_generate(f"""
    You are playing Werewolf.
    Your role: {role_name}
    Personality: {style}
    Do not reveal your role.
    Introduce yourself in-character.
    """)

def build_prompt(player_index, histories, llm_player_ids, include_others):
    style, role_name = PLAYER_PROFILES[player_index]
    role = WEREWOLF_ROLES[role_name]

    prompt = [
        "SYSTEM:",
        "You are playing Werewolf.",
        f"Role: {role_name}",
        f"Personality: {style}",
        "",
    ]

    if include_others:
        prompt.append("Public dialogue:")
        for history in histories:
            for entry in history:
                if entry["visibility"] == VISIBILITY_PUBLIC:
                    prompt.append(
                        f"{player_label(entry['speaker'])}: {entry['text']}"
                    )

    prompt.append("")
    prompt.append(f"{player_label(llm_player_ids[player_index])}:")
    return "\n".join(prompt)

# =========================
# App Entry Point
# =========================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WerewolfGameWindow(
        [UI_TEXT["loading"]] * NUM_LLM_PLAYERS
    )
    window.show()
    sys.exit(app.exec())

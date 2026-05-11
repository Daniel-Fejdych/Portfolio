"""
ARCHITECTURE OVERVIEW

This file combines three major responsibilities:

1. UI Layer (PyQt):
   - Displays players, dialogue, and input controls
   - Handles user interaction and rendering

2. Game State / Turn Logic:
   - Tracks phases (human → LLM → vote)
   - Manages question counts and turn order
   - Coordinates pauses when LLMs ask the human questions

3. LLM Orchestration:
   - Builds prompts from filtered dialogue history
   - Sends requests asynchronously via QThreads
   - Parses structured LLM responses (questions, targets, visibility)

These are intentionally kept together for rapid iteration,
but may later be separated into modules.
"""

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

SELECT_BUTTON_STYLE =  """
    QPushButton {
        background-color: #ef4444;
        color: white;
        border: 1px solid #dc2626;
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #dc2626;
    }

    QPushButton:pressed {
        background-color: #b91c1c;
    }

    QPushButton:disabled {
        background-color: #fecaca;
        border-color: #fca5a5;
        color: #f5f5f5;
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

# Styling for the main text input area
TEXT_BOX_STYLE = """
    QTextEdit {
        background-color: #ffffff;
        color: #1f2937;
        border: 1px solid #c7d2fe;
        border-radius: 6px;
        padding: 6px 8px;
        selection-background-color: #bfdbfe;
    }

    QTextEdit:focus {
        border: 1px solid #3b82f6;
        background-color: #fefeff;
    }

    QTextEdit:disabled {
        background-color: #f1f5f9;
        color: #94a3b8;
        border-color: #e5e7eb;
    }
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

UI_TEXT = {
    "choose_player": "Choose\nthis Player",
    "submit": "Submit",
    "loading": "⏳ Generating prompt…",
}


# Visibility Modifiers and roles
VISIBILITY_PUBLIC = "public"
VISIBILITY_WHISPER = "whisper"


# ---- Werewolf Roles ----

WEREWOLF_ROLES = {
    "villager": {
        "team": "village",
        "description": (
            "You are a Villager. You do not have special powers. "
            "Your goal is to identify and eliminate the Werewolves "
            "through discussion and deduction."
        ),
    },
    "werewolf": {
        "team": "werewolves",
        "description": (
            "You are a Werewolf. You appear innocent during the day. "
            "Your goal is to survive and secretly mislead the villagers."
        ),
    },
}

# Player personality + assigned role
PLAYER_PROFILES = [
    ("suspicious", "villager"),
    ("expert", "villager"),
    ("newbie", "villager"),
    ("innocent", "werewolf"),
]

# Total players include all LLM-controlled players plus exactly one human player.
# Player IDs are abstract "seats" (Player A, B, C, ...) and do NOT imply control type.
NUM_LLM_PLAYERS = len(PLAYER_PROFILES)
NUM_TOTAL_PLAYERS = NUM_LLM_PLAYERS + 1  # +1 for human

# Number of questions human and each llm get(For debugging keep 3 for human and 1 for llm) 
HUMAN_QUESTIONS_PER_ROUND = 3
LLM_QUESTIONS_PER_ROUND = 1

def player_label(player_id: int) -> str:
    """
    Converts a numeric player ID (seat index) into a display label (Player A, Player B, ...).

    Player IDs are seating positions, not LLM indices.
    """
    if not isinstance(player_id, int):
        return "Unknown"
    if player_id < 0 or player_id >= NUM_TOTAL_PLAYERS:
        return "Unknown"
    return f"Player {string.ascii_uppercase[player_id]}"


class WerewolfGameWindow(QWidget):
    """
    Main application window.
    Displays one row per player with a selectable button and LLM-generated prompt,
    plus a shared text input and submit button.
    """
    def __init__(self, button_configs):
        super().__init__()
        self.resize(1000, 500)
        self.setWindowTitle("Imposter Interface")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)



        # ---- Turn / round state ----
        # The game progresses in strict phases:
        #   1. "human" → human may ask a limited number of questions
        #   2. "llm"   → each LLM gets a turn to ask exactly N questions
        #   3. "vote"  → voting phase (stub for now)
        #
        # Phase transitions are one-way per round and centrally controlled.
        self.phase = "human"  # "human" | "llm" | "vote"
        self.human_questions_left = HUMAN_QUESTIONS_PER_ROUND
        self.current_llm_turn = 0
        self.llm_questions_left = {
            i: LLM_QUESTIONS_PER_ROUND for i in range(NUM_LLM_PLAYERS)
        }

        # If an LLM asks the human a question, we pause here
        self.waiting_for_human_answer = False
        self.pending_llm_question = None  # (llm_index, question_text)

        # If an LLM asks another LLM a question, pause here
        self.waiting_for_llm_answer = False
        self.pending_llm_to_llm = None
        # (asking_llm_index, target_llm_index, question_text)

        # Track malformed question retries per LLM per turn
        self.llm_question_retries = {
            i: 0 for i in range(NUM_LLM_PLAYERS)
        }

        # Maximum retries before defaulting
        self.MAX_LLM_QUESTION_RETRIES = 2

        
        # --- Player seating model ---
        # We separate "LLM index" (which model/personality to talk to)
        # from "player seat" (Player A, B, C... as seen in the game).
        # Seats are randomized at startup to avoid the human always being Player A.
        self.player_seats = list(range(NUM_TOTAL_PLAYERS))
        random.shuffle(self.player_seats)

        # Human gets exactly one seat (not tied to any LLM index)
        self.human_player_id = self.player_seats[-1]

        # Maps each LLM index (0..NUM_LLM_PLAYERS-1) to a unique player seat
        # Example: LLM 0 -> Player C, LLM 1 -> Player A, etc.
        self.llm_player_ids = {
            llm_index: self.player_seats[llm_index]
            for llm_index in range(NUM_LLM_PLAYERS)
        }
        
        # Per-player dialogue history.
        # Each entry is a dict containing:
        # - speaker (int Player id)
        # - text (str)
        # - visibility (VISIBILITY_PUBLIC | VISIBILITY_WHISPER)
        # - targets (list[int]): which players may see this message
        #
        # Dialogue history is player-centric, not user/assistant-centric.
        # Every message is spoken by a player index (human or LLM),
        # which allows all participants to be treated uniformly.
        # IMPORTANT:
        # dialogue_history is indexed by *LLM index*, not by player seat.
        # Each LLM maintains its own subjective view of the conversation,
        # filtered by visibility rules (public vs whisper).
        #
        # The same real-world "message" may appear differently (or not at all)
        # in different LLM histories.
        self.dialogue_history = [[] for _ in range(NUM_LLM_PLAYERS)]

        # Used to store if whisper mode is enabled
        self.whisper_mode = False

        # Main Page styling
        self.setStyleSheet(APP_STYLE)

        # ----- Button + Label Rows -----
        # Keep references to player labels so their text can be updated asynchronously
        self.player_labels = []
        self.player_buttons = []
        # Keep track of selected player
        self.selected_player = None

        for index, text in enumerate(button_configs):
            main_layout.addLayout(
                self._create_player_row(text, index)
            )

        
        # ----- Text Input -----
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter your text here...")
        self.text_input.setMinimumHeight(100)
        main_layout.addWidget(self.text_input)

        self.text_input.setStyleSheet(TEXT_BOX_STYLE)

        self.whisper_button = QPushButton("Whisper: OFF")
        self.whisper_button.setCheckable(True)
        self.whisper_button.clicked.connect(self.toggle_whisper)
        main_layout.addWidget(self.whisper_button)

        # ----- Submit Button -----
        submit_button = QPushButton(UI_TEXT["submit"])
        submit_button.clicked.connect(self.submit_text)
        main_layout.addWidget(submit_button)

        self.setLayout(main_layout)

        # Start background LLM generation after UI elements are fully constructed
        self.worker = LLMWorker()
        self.worker.prompt_ready.connect(self.update_player_text)
        self.worker.start()
        self.chat_worker = None
        
        
    # Creates the UI row for a single LLM-controlled player:
    # a selection button + a scrollable dialogue label.
    def _create_player_row(self, text, index):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)

        button = QPushButton(UI_TEXT["choose_player"])
        button.setFixedSize(ROW_MIN_HEIGHT, ROW_MIN_HEIGHT)
        button.setStyleSheet(SELECT_BUTTON_STYLE)
        button.clicked.connect(lambda _, n=index: self.select_player(n))

        self.player_buttons.append(button)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        label.setStyleSheet(LABEL_STYLE)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(ROW_MIN_HEIGHT)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(label)

        self.player_labels.append(label)

        row_layout.addWidget(button)
        row_layout.addWidget(scroll)
        return row_layout

    def start_vote_phase(self):
        self.phase = "vote"
        print("Voting phase started")

    def submit_text(self):
        """
        Handles ALL user text submission cases:

        1. Human answering an LLM's question (waiting_for_human_answer)
        2. Human asking questions during the human phase
        3. Rejected input (wrong phase, no selection, empty input)

        This function intentionally returns early in many cases
        to keep each scenario isolated.
        """
        text = self.text_input.toPlainText().strip()
        if not text:
            return

        # --- Case 1: Human is answering a question asked by an LLM ---
        if self.waiting_for_human_answer:
            llm_index, _ = self.pending_llm_question
            self.waiting_for_human_answer = False
            self.pending_llm_question = None

            # Clear input immediately
            self.text_input.clear()

            # Add the human's answer as REAL dialogue
            for i in range(NUM_LLM_PLAYERS):
                self.dialogue_history[i].append({
                    "speaker": self.human_player_id,
                    "text": text,
                    "visibility": VISIBILITY_PUBLIC,
                    "targets": [],
                })

            # Re-render ALL dialogue views (removes the banner)
            for i in range(NUM_LLM_PLAYERS):
                self.player_labels[i].setText(self.render_dialogue(i))

            # Advance LLM turn state
            self.llm_questions_left[llm_index] -= 1
            self.current_llm_turn += 1
            self.advance_llm_turn()
            return
        
        if self.phase != "human" and not self.waiting_for_human_answer:
            print("It is not your turn to ask questions.")
            return

        if self.waiting_for_llm_answer:
            print("Waiting for another LLM to answer.")
            return
        
        if self.selected_player is None:
            print("Please select a player first")
            return
        # Prevent overlapping LLM requests
        if self.chat_worker and self.chat_worker.isRunning():
            return
        
        
        self.text_input.clear()

        # --- Case 2: Human attempting to ask a question ---

        # Decrement number of questions the human can ask.
        # If the llm asked the human a question,
        # it would have returned earlier.
        self.human_questions_left -= 1

        # Record the human's message as coming from the human player's seat,
        # even though it is stored in the selected LLM's dialogue history.
        # Targets define who may see this message:
        # - public: ignored
        # - whisper: only listed player IDs may view it
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
        # Human ran out of questions, Start LLM phase.
        if self.human_questions_left <= 0:
            self.start_llm_phase()

    # Slot called when a prompt is ready; updates the corresponding label
    # Initial LLM messages are public introductions spoken by that LLM's player seat.
    # These messages appear in all players' public context (if enabled).
    def update_player_text(self, index, text):
        # Store initial LLM message as assistant dialogue
        self.dialogue_history[index].append({
            "speaker": self.llm_player_ids[index],
            "text": text,
            "visibility": VISIBILITY_PUBLIC,
            "targets": [],
        })

        # Render from centralized dialogue
        self.player_labels[index].setText(
            self.render_dialogue(index)
        )

    def closeEvent(self, event):
        if self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        if hasattr(self, "chat_worker") and self.chat_worker.isRunning():
            self.chat_worker.quit()
            self.chat_worker.wait()
        event.accept()


    # LLM responses are always spoken by the LLM's assigned player seat.
    # Responses are not whispered for now, as
    # - LLM replies should decide whispering themselves
    # - Otherwise, a whispered question forces a whispered answer forever
    # Whispered responses will be reintroduced later.
    def on_chat_response(self, player_index, response):
        self.dialogue_history[player_index].append({
            "speaker": self.llm_player_ids[player_index],
            "text": response,
            "visibility": VISIBILITY_PUBLIC,
            "targets": [],
        })

        # Re-render the dialogue after generation
        self.player_labels[player_index].setText(
            self.render_dialogue(player_index)
        )

    def select_player(self, index):

        # If an LLM is currently waiting for an answer, don't allow changing talk targets
        if self.waiting_for_human_answer:
            print("Please answer the current question first.")
            return
                
        self.selected_player = index

        # Reset whisper mode when switching players
        self.whisper_button.setChecked(False)
        self.toggle_whisper(False)

        # Reset all buttons to default style
        self._reset_button_styles()
        
        # Highlight selected button
        self.player_buttons[index].setStyleSheet(SELECTED_BUTTON_STYLE)

        print(f"Selected player {index}")

    def _reset_button_styles(self):
        for button in self.player_buttons:
            button.setStyleSheet(SELECT_BUTTON_STYLE)

    # Centralisation of dialogue
    def render_dialogue(self, player_index, thinking=False):
        """
        Renders the visible dialogue for a given player.

        - Public messages are always shown
        - Whispered messages are shown only if the player is a target
        - Dialogue is rendered from the perspective of a single LLM player,
          filtering whispers and hiding messages not intended for them.
        - 'thinking' adds a temporary UI-only assistant message
        """
        lines = []

        for entry in self.dialogue_history[player_index]:
            speaker_name = player_label(entry["speaker"])
            visibility = entry["visibility"]

            # Public messages: always visible
            if visibility == VISIBILITY_PUBLIC:
                lines.append(f"{speaker_name}: {entry['text']}")

            # Whisper: only visible to targets
            # Only show whispered messages if THIS LLM's player seat is a target
            elif visibility == VISIBILITY_WHISPER:
                if self.llm_player_ids[player_index] in entry["targets"]:
                    lines.append(
                        f"(whisper) {speaker_name}: {entry['text']}"
                    )
                    

        if thinking:
            lines.append(
                f"{player_label(self.llm_player_ids[player_index])}: ⏳ thinking…"
            )
        return "\n\n".join(lines)

    
    def toggle_whisper(self, checked):
        self.whisper_mode = checked
        self.whisper_button.setText(
            "Whisper: ON" if checked else "Whisper: OFF"
        )

    def start_llm_phase(self):
        print("Human phase over. LLMs are now asking questions.")
        self.phase = "llm"
        self.current_llm_turn = 0
        self.advance_llm_turn()

    def advance_llm_turn(self):
        """
        Advances the LLM questioning phase.

        This function may call itself recursively to:
        - Skip LLMs that have no remaining questions
        - Move immediately to the voting phase when done

        The recursion depth is bounded by NUM_LLM_PLAYERS.
        """
        if self.current_llm_turn >= NUM_LLM_PLAYERS:
            self.start_vote_phase()
            return

        llm_index = self.current_llm_turn

        # Reset retry count at the start of this LLM's turn
        self.llm_question_retries[llm_index] = 0

        if self.llm_questions_left[llm_index] <= 0:
            self.current_llm_turn += 1
            self.advance_llm_turn()
            return

        self.ask_llm_to_question(llm_index)

    def ask_llm_to_question(self, llm_index):
        # NOTE:
        # This prompt establishes a STRICT output contract.
        # Any deviation (missing TARGET, invalid VISIBILITY, etc.)
        # must be handled defensively by parse_llm_question().
        prompt = build_prompt(
            llm_index,
            self.dialogue_history,
            self.llm_player_ids,
            INCLUDE_OTHER_PLAYERS_CONTEXT,
        )

        prompt += (
            "\n\nIt is now your turn to ASK A QUESTION.\n"
            "You must ask exactly ONE question.\n"
            "Format your response as:\n"
            "QUESTION:\n"
            "TARGET: Player X\n"
            "VISIBILITY: public or whisper\n"
            "TEXT: <your question>\n"
        )

        self.chat_worker = ChatWorker(llm_index, prompt)
        self.chat_worker.response_ready.connect(self.on_llm_question)
        self.chat_worker.start()


    def on_llm_question(self, llm_index, response):
        parsed = parse_llm_question(response)

        # If parsing fails:
        # - on_llm_question currently retries self.MAX_LLM_QUESTION_RETRIES times
        #   * Tracks retry counts per LLM per turn
        #   * Falls back to a default action (skips question)
        #   * Log malformed output for prompt tuning
        
        if not parsed:
            self.llm_question_retries[llm_index] += 1

            print(
                f"[ERROR] Invalid question from LLM {llm_index} "
                f"(attempt {self.llm_question_retries[llm_index]})"
            )

            if self.llm_question_retries[llm_index] < self.MAX_LLM_QUESTION_RETRIES:
                # Retry asking the same LLM
                self.ask_llm_to_question(llm_index)
                return

            # --- Fallback: skip this LLM's question ---
            print(
                f"[FALLBACK] LLM {llm_index} failed too many times. "
                "Skipping its question."
            )

            self.llm_questions_left[llm_index] -= 1
            self.current_llm_turn += 1
            self.advance_llm_turn()
            return


        target_id, visibility, question = parsed
        
        speaker_id = self.llm_player_ids[llm_index]

        if target_id == self.human_player_id:
            print("LLM asked the human a question.")

            # Store the LLM's question as REAL dialogue
            for i in range(NUM_LLM_PLAYERS):
                self.dialogue_history[i].append({
                    "speaker": speaker_id,
                    "text": question,
                    "visibility": VISIBILITY_PUBLIC,
                    "targets": [],
                })

            # Pause the game waiting for the human's reply
            self.waiting_for_human_answer = True
            self.pending_llm_question = (llm_index, question)

            # Render dialogue + temporary banner
            self.player_labels[llm_index].setText(
                self.render_dialogue(llm_index) +
                f"\n\n❓ {player_label(speaker_id)} asks YOU:\n{question}"
            )
            return


        # Reverse mapping: player seat → controlling LLM index
        # Needed because LLMs think in terms of Player A/B/C,
        # but dialogue history is indexed by LLM index.
        player_id_to_llm = {v: k for k, v in self.llm_player_ids.items()}

        target_llm_index = player_id_to_llm.get(target_id)
        if target_llm_index is None:
            # human target already handled earlier
            return

        
        # Store the question in ALL histories (filtered by visibility later)
        for i in range(NUM_LLM_PLAYERS):
            self.dialogue_history[i].append({
                "speaker": speaker_id,
                "text": question,
                "visibility": visibility,
                "targets": [target_id] if visibility == VISIBILITY_WHISPER else [],
            })

        # Pause turn flow waiting for the TARGET LLM to answer
        self.waiting_for_llm_answer = True
        self.pending_llm_to_llm = (llm_index, target_llm_index, question)
        self.ask_llm_to_answer_llm(target_llm_index)

        # Visually highlight the target LLM as "thinking"
        self.player_labels[target_llm_index].setText(
            self.render_dialogue(target_llm_index, thinking=True)
        )

        return
    
    def ask_llm_to_answer_llm(self, target_llm_index):
        asking_llm_index, _, question = self.pending_llm_to_llm

        prompt = build_prompt(
            target_llm_index,
            self.dialogue_history,
            self.llm_player_ids,
            INCLUDE_OTHER_PLAYERS_CONTEXT,
        )

        prompt += (
            "\n\nYou were just asked a question by another player.\n"
            "Respond naturally and in-character.\n"
            "Do NOT ask a new question.\n"
        )

        self.chat_worker = ChatWorker(target_llm_index, prompt)
        self.chat_worker.response_ready.connect(self.on_llm_to_llm_answer)
        self.chat_worker.start()


    def on_llm_to_llm_answer(self, target_llm_index, response):
        asking_llm_index, _, _ = self.pending_llm_to_llm
        self.pending_llm_to_llm = None
        self.waiting_for_llm_answer = False

        speaker_id = self.llm_player_ids[target_llm_index]

        # Store answer as real dialogue
        for i in range(NUM_LLM_PLAYERS):
            self.dialogue_history[i].append({
                "speaker": speaker_id,
                "text": response,
                "visibility": VISIBILITY_PUBLIC,
                "targets": [],
            })

        # Re-render all views
        for i in range(NUM_LLM_PLAYERS):
            self.player_labels[i].setText(self.render_dialogue(i))

        # NOW consume the asking LLM's question allowance
        self.llm_questions_left[asking_llm_index] -= 1
        self.current_llm_turn += 1
        self.advance_llm_turn()

"""
SECURITY / ROBUSTNESS NOTE:

This function treats LLM output as untrusted input.
Any parsing failure must be handled gracefully to avoid
breaking the game loop or blocking progress.
"""
def parse_llm_question(text):
    """
    Attempts to parse an LLM question directive.
    Returns (target_player_id, visibility, question_text) or None on failure.
    """
    try:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        data = {}

        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.upper()] = v.strip()

        target_label = data.get("TARGET")
        visibility = data.get("VISIBILITY", VISIBILITY_PUBLIC)
        question = data.get("TEXT")

        if not target_label or not question:
            raise ValueError("Missing TARGET or TEXT")

        # Convert "Player X" → seat id
        letter = target_label.replace("Player", "").strip()
        player_id = string.ascii_uppercase.index(letter)

        if visibility not in (VISIBILITY_PUBLIC, VISIBILITY_WHISPER):
            visibility = VISIBILITY_PUBLIC

        return player_id, visibility, question

    except Exception as e:
        print("[LLM PARSE ERROR]", e)
        print(text)
        return None



def initial_player_configs():
    return [UI_TEXT["loading"]] * NUM_LLM_PLAYERS

# LLMWorker handles one-time startup dialogue (introductions)
# Background worker that generates LLM prompts without blocking the UI
# Generates initial role introductions in the background
# to avoid blocking the UI during startup.
class LLMWorker(QThread):
    prompt_ready = pyqtSignal(int, str)

    # Generates prompts sequentially to avoid overloading the local LLM server
    def run(self):
        for index, (style, role) in enumerate(PLAYER_PROFILES):
            text = generate_initial_player_prompt(style, role)
            self.prompt_ready.emit(index, text)

# ChatWorker handles a single conversational response from one LLM
# Handles per-message LLM generation asynchronously
# Only one ChatWorker is allowed at a time to prevent overlap.
class ChatWorker(QThread):
    response_ready = pyqtSignal(int, str)

    def __init__(self, player_index, prompt):
        super().__init__()
        self.player_index = player_index
        self.prompt = prompt

    def run(self):
        response = ollama_generate(self.prompt)
        self.response_ready.emit(self.player_index, response)

# - Ollama Generate Function -
# run in terminal:
#     ollama run llama3.2:3b
# to make ollama_generate work!!

OLLAMA_URL = "http://localhost:11434/api/generate"

# Sends a single non-streaming prompt to the local Ollama server.
# This is a blocking call and will delay app startup if the model is slow.
# It should be run asynchronously.
def ollama_generate(prompt, model="llama3.2:3b"):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.RequestException as e:
        return f"[LLM error: {e}]"


# Constructs a role-specific prompt and delegates generation to Ollama
def generate_initial_player_prompt(style, role_name):
    role = WEREWOLF_ROLES[role_name]

    return ollama_generate(f"""
        You are about to play a game of Werewolf.

        Game overview:
        - The game alternates between day and night.
        - During the day, players discuss and try to identify the Werewolves.
        - Werewolves secretly try to deceive the village.
        - For now, there is NO voting and NO night actions.
        - Focus only on discussion, suspicion, and roleplay.

        Your role (private information):
        - Role: {role_name.upper()}
        - Team: {role["team"]}
        - Description: {role["description"]}

        Personality:
        - You should behave in a {style} manner when speaking.

        Instructions:
        - Do NOT reveal your role.
        - Speak as a human player would in a social deduction game.
        - Be concise, conversational, and strategic.

        Start by introducing yourself to the group in-character.
        """)


# If True, a player will receive other players' PUBLIC dialogue
# in their prompt. Whispered dialogue is never shared.
INCLUDE_OTHER_PLAYERS_CONTEXT = True

def build_prompt( player_index, histories, llm_player_ids,
    include_others=False):
    style, role_name = PLAYER_PROFILES[player_index]
    role = WEREWOLF_ROLES[role_name]
    """
    Builds the full prompt for a single LLM-controlled player.

    The prompt represents that player's subjective view of the game:
    - Their private role information
    - Public dialogue from others (optional)
    - Their own dialogue history
    - Whispered messages only if they were a target
    """

    prompt = [
        "SYSTEM:",
        "You are playing a game of Werewolf.",
        "This is a social deduction game focused on discussion and deception.",
        "There is currently no voting and no night phase.",
        "",
        "You are one of several players in the game.",
        "All participants (including the human) are players.",
        "Speak only as your assigned player.",
        "Your private role information:",
        f"- Role: {role_name.upper()}",
        f"- Team: {role['team']}",
        f"- Description: {role['description']}",
        "",
        f"Your personality: {style}",
        "Do NOT reveal your role directly.",
        "",
    ]



    if include_others:
        # Include only PUBLIC dialogue from other players.
        # Whispered messages are never shared across players.
        # IMPORTANT:
        # Whispered messages are only included if this LLM was a target.
        # Other players are completely unaware these messages exist.
        # This asymmetry is intentional and central to social deduction.
        prompt.append("Other players' dialogue:")
        for i, history in enumerate(histories):
            if i == player_index:
                continue
            for entry in history:
                if entry["visibility"] == VISIBILITY_PUBLIC:
                    prompt.append(
                        f"{player_label(entry['speaker'])}: {entry['text']}"
                    )
        prompt.append("")

    prompt.append("Your dialogue history:")
    for entry in histories[player_index]:
        if entry["visibility"] == VISIBILITY_PUBLIC:
            prompt.append(
                f"{player_label(entry['speaker'])}: {entry['text']}"
            )
        elif entry["visibility"] == VISIBILITY_WHISPER:
            if llm_player_ids[player_index] in entry["targets"]:
                prompt.append(
                    f"(whisper) {player_label(entry['speaker'])}: {entry['text']}"
                )

    prompt.append("")
    # End the prompt with this player's label to cue the LLM to speak in-character.
    prompt.append(
        f"{player_label(llm_player_ids[player_index])}:"
    )

    return "\n".join(prompt)
    


# ----- Run App -----
# LLM prompts are generated before the Qt event loop starts
# so the UI opens with all player text already populated.
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WerewolfGameWindow(initial_player_configs())
    window.show()
    sys.exit(app.exec())

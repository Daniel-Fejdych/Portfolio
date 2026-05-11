import sys
import requests
import string
import random
import tempfile
import os
import time
import threading

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

# --- Offline STT deps ---
# pip install faster-whisper sounddevice scipy numpy
try:
    import numpy as np
    import sounddevice as sd
    from scipy.io.wavfile import write as wav_write
    from faster_whisper import WhisperModel
except Exception:
    np = None
    sd = None
    wav_write = None
    WhisperModel = None

# --- Offline TTS deps ---
# pip install pyttsx3
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

APP_STYLE = """
    QWidget {
        background-color: #f0f8f7;
        color: #0f1927;
        font-family: "Segoe UI", "Inter", sans-serif;
        font-size: 10.5pt;
    }
"""

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

VOICE_BUTTON_STYLE = """
    QPushButton {
        background-color: #10b981;
        color: white;
        border: 1px solid #059669;
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #059669; }
    QPushButton:pressed { background-color: #047857; }
    QPushButton:disabled {
        background-color: #a7f3d0;
        border-color: #6ee7b7;
        color: #f5f5f5;
    }
"""

UI_TEXT = {
    "choose_player": "Choose\nthis Player",
    "submit": "Submit",
    "loading": "⏳ Generating prompt…",
}

VISIBILITY_PUBLIC = "public"
VISIBILITY_WHISPER = "whisper"


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

PLAYER_PROFILES = [
    ("Grigor", "suspicious", "villager"),
    ("Alex", "expert", "villager"),
    ("Emily", "newbie", "villager"),
    ("Elara", "innocent", "werewolf"),
]

SEAT_TO_NAME = {}

NUM_LLM_PLAYERS = len(PLAYER_PROFILES)
NUM_TOTAL_PLAYERS = NUM_LLM_PLAYERS + 1

HUMAN_QUESTIONS_PER_ROUND = 3
LLM_QUESTIONS_PER_ROUND = 1


def player_label(player_id):
    return SEAT_TO_NAME.get(player_id, "You")


# ============================================================
# Whisper Model Cache (关键：模型只加载一次)
# ============================================================

WHISPER_MODEL_CACHE = {}
WHISPER_MODEL_LOCK = threading.Lock()

def get_whisper_model(model_size_or_path: str):
    if WhisperModel is None:
        raise RuntimeError("WhisperModel not available. Install faster-whisper.")

    with WHISPER_MODEL_LOCK:
        if model_size_or_path not in WHISPER_MODEL_CACHE:
            t0 = time.time()
            print(f"[STT] loading WhisperModel = {model_size_or_path} ...")
            WHISPER_MODEL_CACHE[model_size_or_path] = WhisperModel(
                model_size_or_path,
                device="cpu",
                compute_type="int8"
            )
            print(f"[STT] model loaded in {time.time() - t0:.2f}s")
        return WHISPER_MODEL_CACHE[model_size_or_path]


# ---------------------------
# Offline STT Worker (Hold-to-talk)
# ---------------------------

class STTWorker(QThread):
    """
    Push-to-talk Offline STT:
    - press -> start thread, open InputStream and buffer audio
    - release -> request_stop() -> close stream, write wav, transcribe, emit text
    """
    text_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, language="en", model_size="small", samplerate=16000, channels=1):
        super().__init__()
        self.language = language
        self.model_size = model_size
        self.samplerate = samplerate
        self.channels = channels

        self._stop_requested = False
        self._frames = []
        self._stream = None

    def request_stop(self):
        self._stop_requested = True

    def _callback(self, indata, frames, time_info, status):
        # status 可能提示 buffer overflow 等，不直接打断
        self._frames.append(indata.copy())

    def run(self):
        if np is None or sd is None or wav_write is None or WhisperModel is None:
            self.error.emit(
                "Missing STT deps. Install: pip install faster-whisper sounddevice scipy numpy"
            )
            return

        tmp_path = None
        try:
            self._stop_requested = False
            self._frames = []

            # 开始录音
            try:
                self._stream = sd.InputStream(
                    samplerate=self.samplerate,
                    channels=self.channels,
                    dtype="float32",
                    callback=self._callback,
                )
                self._stream.start()
            except Exception as e:
                self.error.emit(f"Failed to open microphone: {e}")
                return

            # 录到 request_stop 为止
            while not self._stop_requested:
                sd.sleep(50)

            # 停止录音
            try:
                if self._stream:
                    self._stream.stop()
                    self._stream.close()
            except Exception:
                pass
            self._stream = None

            if not self._frames:
                self.error.emit("No audio captured.")
                return

            audio = np.concatenate(self._frames, axis=0)

            # 太短不转写
            min_samples = int(self.samplerate * 0.2)
            if audio.shape[0] < min_samples:
                self.error.emit("Recording too short (press and hold a bit longer).")
                return

            # 写临时 wav
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp_path = tmp.name
            tmp.close()

            wav_write(tmp_path, self.samplerate, (audio * 32767).astype(np.int16))

            # 复用模型
            model = get_whisper_model(self.model_size)

            # 关键：尽量“英文为主”
            # task="transcribe" 表示“按原语言转写”，避免走翻译路径
            t1 = time.time()
            try:
                segments, _info = model.transcribe(
                    tmp_path,
                    language=self.language,
                    task="transcribe",
                    # vad_filter=True,  # 需要更稳可以打开（噪声大时有用）
                )
            except TypeError:
                # 兼容某些版本 faster-whisper 不支持 task 参数
                segments, _info = model.transcribe(
                    tmp_path,
                    language=self.language,
                    # vad_filter=True,
                )

            print(f"[STT] transcribe in {time.time() - t1:.2f}s")

            text = "".join(seg.text for seg in segments).strip()
            if not text:
                self.error.emit("No speech recognized (empty result).")
                return

            self.text_ready.emit(text)

        except Exception as e:
            self.error.emit(str(e))
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

class TTSWorker(QThread):
    """
    Offline TTS using pyttsx3 (runs in QThread to avoid freezing UI)
    """
    error = pyqtSignal(str)
    finished_speaking = pyqtSignal()

    def __init__(self, text: str, rate: int = 175, volume: float = 1.0):
        super().__init__()
        self.text = (text or "").strip()
        self.rate = rate
        self.volume = volume

    def run(self):
        if pyttsx3 is None:
            self.error.emit("Missing TTS deps. Install: pip install pyttsx3")
            return
        if not self.text:
            self.error.emit("No text to speak.")
            return

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", int(self.rate))
            engine.setProperty("volume", float(self.volume))
            engine.say(self.text)
            engine.runAndWait()
            self.finished_speaking.emit()
        except Exception as e:
            self.error.emit(str(e))

class WerewolfGameWindow(QWidget):
    def __init__(self, button_configs):
        super().__init__()
        self.resize(1000, 650)
        self.setWindowTitle("Imposter Interface")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)

        # ---- Turn state ----
        self.phase = "human"
        self.human_questions_left = HUMAN_QUESTIONS_PER_ROUND
        self.current_llm_turn = 0
        self.llm_questions_left = {i: LLM_QUESTIONS_PER_ROUND for i in range(NUM_LLM_PLAYERS)}

        self.waiting_for_human_answer = False
        self.pending_llm_question = None

        self.waiting_for_llm_answer = False
        self.pending_llm_to_llm = None

        self.llm_question_retries = {i: 0 for i in range(NUM_LLM_PLAYERS)}
        self.MAX_LLM_QUESTION_RETRIES = 2

        # --- Seating ---
        self.player_seats = list(range(NUM_TOTAL_PLAYERS))
        random.shuffle(self.player_seats)

        self.human_player_id = self.player_seats[-1]

        self.llm_player_ids = {
            llm_index: self.player_seats[llm_index]
            for llm_index in range(NUM_LLM_PLAYERS)
        }

        global SEAT_TO_NAME
        SEAT_TO_NAME.clear()
        for llm_idx, seat_id in self.llm_player_ids.items():
            SEAT_TO_NAME[seat_id] = PLAYER_PROFILES[llm_idx][0]
        SEAT_TO_NAME[self.human_player_id] = "You"

        self.dialogue_history = [[] for _ in range(NUM_LLM_PLAYERS)]
        self.whisper_mode = False

        # STT state
        self.stt_worker = None
        self.audio_busy = False
        self._recording = False

        self.setStyleSheet(APP_STYLE)

        # UI rows
        self.player_labels = []
        self.player_buttons = []
        self.player_speaker_buttons = []
        self.selected_player = None

        for index in range(NUM_LLM_PLAYERS):
            main_layout.addLayout(self._create_player_row(UI_TEXT["loading"], index))

        # Input
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter your text here (or hold mic button to talk)…")
        self.text_input.setMinimumHeight(100)
        self.text_input.setStyleSheet(TEXT_BOX_STYLE)
        main_layout.addWidget(self.text_input)

        # Whisper toggle
        self.whisper_button = QPushButton("Whisper: OFF")
        self.whisper_button.setCheckable(True)
        self.whisper_button.clicked.connect(self.toggle_whisper)
        main_layout.addWidget(self.whisper_button)

        # STT buttons row
        stt_row = QHBoxLayout()

        self.mic_button = QPushButton("🎙️ Hold to Talk (release to transcribe)")
        self.mic_button.setStyleSheet(VOICE_BUTTON_STYLE)
        self.mic_button.pressed.connect(self.start_stt_hold)
        self.mic_button.released.connect(self.stop_stt_hold)
        stt_row.addWidget(self.mic_button)

        self.stt_model_button = QPushButton("Model: small (click to cycle)")
        self.stt_model_button.setCheckable(False)
        self.stt_model_button.clicked.connect(self.cycle_stt_model)
        stt_row.addWidget(self.stt_model_button)

        main_layout.addLayout(stt_row)



        # TTS buttons row
        tts_row = QHBoxLayout()

        self.auto_tts_toggle = QPushButton("Auto Speak: ON")
        self.auto_tts_toggle.setCheckable(True)
        self.auto_tts_toggle.setChecked(True)
        self.auto_tts_toggle.setStyleSheet(VOICE_BUTTON_STYLE)
        self.auto_tts_toggle.clicked.connect(self.toggle_auto_tts)
        tts_row.addWidget(self.auto_tts_toggle)

        self.replay_last_button = QPushButton("🔁 Replay Last")
        self.replay_last_button.setStyleSheet(VOICE_BUTTON_STYLE)
        self.replay_last_button.clicked.connect(self.replay_last)
        tts_row.addWidget(self.replay_last_button)

        main_layout.addLayout(tts_row)

        # TTS state
        # TTS state
        self.tts_worker = None

        # --- Auto TTS / Replay state ---
        self.auto_tts_enabled = True  # 自动朗读开关（默认开）
        self.tts_queue = []  # 朗读排队
        self.last_spoken_text = ""  # 最后一次朗读内容（用于Replay）
        self.last_player_spoken = None  # 最后朗读来自哪个player_index（可选）
        self.speak_initial_intros = False  # 默认不朗读开场自我介绍（避免一开场念四段）

        # Submit
        submit_button = QPushButton(UI_TEXT["submit"])
        submit_button.clicked.connect(self.submit_text)
        main_layout.addWidget(submit_button)

        self.setLayout(main_layout)

        # Start background LLM generation
        self.worker = LLMWorker()
        self.worker.prompt_ready.connect(self.update_player_text)
        self.worker.start()
        self.chat_worker = None

        # STT model config (English-first)
        self.stt_language = "en"
        self.stt_model_size = "small"  # tiny/base/small/medium/large-v3

    def _create_player_row(self, text, index):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)

        button = QPushButton(UI_TEXT["choose_player"])
        speaker_btn = QPushButton("🔊")
        speaker_btn.setFixedSize(ROW_MIN_HEIGHT, ROW_MIN_HEIGHT)
        speaker_btn.setStyleSheet(VOICE_BUTTON_STYLE)
        speaker_btn.clicked.connect(lambda _, n=index: self.replay_player_last(n))
        self.player_speaker_buttons.append(speaker_btn)
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
        row_layout.addWidget(speaker_btn)
        row_layout.addWidget(scroll)
        return row_layout

    # -------------------
    # STT controls (Hold-to-talk)
    # -------------------

    def cycle_stt_model(self):
        options = ["tiny", "base", "small", "medium"]
        cur = options.index(self.stt_model_size) if self.stt_model_size in options else 2
        nxt = (cur + 1) % len(options)
        self.stt_model_size = options[nxt]
        self.stt_model_button.setText(f"Model: {self.stt_model_size} (click to cycle)")
        print("[STT] model_size =", self.stt_model_size)

    def start_stt_hold(self):
        if self.audio_busy or self._recording:
            return
        if self.stt_worker and self.stt_worker.isRunning():
            return

        self.audio_busy = True
        self._recording = True
        self.mic_button.setText("🎙️ Recording... (release to stop)")

        self.stt_worker = STTWorker(
            language=self.stt_language,
            model_size=self.stt_model_size
        )
        self.stt_worker.text_ready.connect(self.on_stt_text)
        self.stt_worker.error.connect(self.on_stt_error)
        self.stt_worker.finished.connect(self.on_stt_done)
        self.stt_worker.start()

    def stop_stt_hold(self):
        if not self._recording:
            return
        if self.stt_worker and self.stt_worker.isRunning():
            self.mic_button.setText("⏳ Transcribing...")
            self.stt_worker.request_stop()

    def on_stt_text(self, text: str):
        cur = self.text_input.toPlainText().strip()
        self.text_input.setText((cur + " " + text).strip() if cur else text)

    def on_stt_error(self, err: str):
        print("[STT ERROR]", err)

    def on_stt_done(self):
        self.audio_busy = False
        self._recording = False
        self.mic_button.setText("🎙️ Hold to Talk (release to transcribe)")

    # -------------------
    # TTS controls
    # -------------------
    def _start_tts(self, text: str, player_index=None):
        text = (text or "").strip()
        if not text:
            return

        # 记录“最后一次朗读内容”，用于 Replay
        self.last_spoken_text = text
        self.last_player_spoken = player_index

        # 如果正在录音/转写 或 正在朗读：加入队列
        if self.audio_busy or (self.tts_worker and self.tts_worker.isRunning()):
            self.tts_queue.append((text, player_index))
            return

        self.audio_busy = True

        self.tts_worker = TTSWorker(text=text, rate=175, volume=1.0)
        self.tts_worker.error.connect(self.on_tts_error)
        self.tts_worker.finished_speaking.connect(self.on_tts_done)
        self.tts_worker.start()

    def replay_player_last(self, player_index: int):
        """Replay this NPC's last public line (if any)."""
        history = self.dialogue_history[player_index]
        for entry in reversed(history):
            if entry.get("visibility") == VISIBILITY_PUBLIC and entry.get("text"):
                self._start_tts(entry["text"], player_index=player_index)
                return
        print("[TTS] No public message to replay for this player.")


    def on_tts_error(self, err: str):
        print("[TTS ERROR]", err)
        self.on_tts_done()

    def on_tts_done(self):
        self.audio_busy = False

        # 如果队列里还有要朗读的，继续播
        if self.tts_queue:
            next_text, next_player = self.tts_queue.pop(0)
            self._start_tts(next_text, player_index=next_player)

    def toggle_auto_tts(self, checked: bool):
        self.auto_tts_enabled = bool(checked)
        self.auto_tts_toggle.setText("Auto Speak: ON" if checked else "Auto Speak: OFF")

    def replay_last(self):
        if not self.last_spoken_text.strip():
            print("[TTS] Nothing to replay.")
            return
        # 直接重复朗读最后一次内容
        self._start_tts(self.last_spoken_text, player_index=self.last_player_spoken)

    # -------------------
    # Game flow (unchanged)
    # -------------------

    def start_vote_phase(self):
        self.phase = "vote"
        print("Voting phase started")

    def submit_text(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            return

        # Case 1: human answering LLM
        if self.waiting_for_human_answer:
            llm_index, _ = self.pending_llm_question
            self.waiting_for_human_answer = False
            self.pending_llm_question = None

            self.text_input.clear()

            for i in range(NUM_LLM_PLAYERS):
                self.dialogue_history[i].append({
                    "speaker": self.human_player_id,
                    "text": text,
                    "visibility": VISIBILITY_PUBLIC,
                    "targets": [],
                })

            for i in range(NUM_LLM_PLAYERS):
                self.player_labels[i].setText(self.render_dialogue(i))

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

        if self.chat_worker and self.chat_worker.isRunning():
            return

        self.text_input.clear()

        # Case 2: human asking
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

    def update_player_text(self, index, text):
        self.dialogue_history[index].append({
            "speaker": self.llm_player_ids[index],
            "text": text,
            "visibility": VISIBILITY_PUBLIC,
            "targets": [],
        })
        self.player_labels[index].setText(self.render_dialogue(index))
        # Auto speak new line
        if self.auto_tts_enabled and (self.speak_initial_intros or len(self.dialogue_history[index]) > 1):
            self._start_tts(text, player_index=index)

    def closeEvent(self, event):
        if self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        if self.chat_worker and self.chat_worker.isRunning():
            self.chat_worker.quit()
            self.chat_worker.wait()
        if self.stt_worker and self.stt_worker.isRunning():
            try:
                self.stt_worker.request_stop()
            except Exception:
                pass
            self.stt_worker.quit()
            self.stt_worker.wait()
        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.quit()
            self.tts_worker.wait()
        event.accept()

    def on_chat_response(self, player_index, response):
        self.dialogue_history[player_index].append({
            "speaker": self.llm_player_ids[player_index],
            "text": response,
            "visibility": VISIBILITY_PUBLIC,
            "targets": [],
        })
        self.player_labels[player_index].setText(self.render_dialogue(player_index))
        # Auto speak new response
        if self.auto_tts_enabled:
            self._start_tts(response, player_index=player_index)

    def select_player(self, index):
        if self.waiting_for_human_answer:
            print("Please answer the current question first.")
            return

        self.selected_player = index

        self.whisper_button.setChecked(False)
        self.toggle_whisper(False)

        for button in self.player_buttons:
            button.setStyleSheet(SELECT_BUTTON_STYLE)

        self.player_buttons[index].setStyleSheet(SELECTED_BUTTON_STYLE)
        print(f"Selected player {index}")

        # Speak this NPC's intro immediately when selected
        intro_text = None
        for entry in self.dialogue_history[index]:
            if entry.get("visibility") == VISIBILITY_PUBLIC and entry.get("text"):
                intro_text = entry["text"].strip()
                break

        if intro_text:
            self._start_tts(intro_text, player_index=index)
        else:
            print("[TTS] Intro not ready yet (LLM still generating). Try again in a moment.")


    def render_dialogue(self, player_index, thinking=False):
        lines = []
        for entry in self.dialogue_history[player_index]:
            speaker_name = player_label(entry["speaker"])
            visibility = entry["visibility"]

            if visibility == VISIBILITY_PUBLIC:
                lines.append(f"{speaker_name}: {entry['text']}")
            elif visibility == VISIBILITY_WHISPER:
                if self.llm_player_ids[player_index] in entry["targets"]:
                    lines.append(f"(whisper) {speaker_name}: {entry['text']}")

        if thinking:
            lines.append(f"{player_label(self.llm_player_ids[player_index])}: ⏳ thinking…")
        return "\n\n".join(lines)

    def toggle_whisper(self, checked):
        self.whisper_mode = checked
        self.whisper_button.setText("Whisper: ON" if checked else "Whisper: OFF")

    def start_llm_phase(self):
        print("Human phase over. LLMs are now asking questions.")
        self.phase = "llm"
        self.current_llm_turn = 0
        self.advance_llm_turn()

    def advance_llm_turn(self):
        if self.current_llm_turn >= NUM_LLM_PLAYERS:
            self.start_vote_phase()
            return

        llm_index = self.current_llm_turn
        self.llm_question_retries[llm_index] = 0

        if self.llm_questions_left[llm_index] <= 0:
            self.current_llm_turn += 1
            self.advance_llm_turn()
            return

        self.ask_llm_to_question(llm_index)

    def ask_llm_to_question(self, llm_index):
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

        if not parsed:
            self.llm_question_retries[llm_index] += 1
            print(f"[ERROR] Invalid question from LLM {llm_index} (attempt {self.llm_question_retries[llm_index]})")

            if self.llm_question_retries[llm_index] < self.MAX_LLM_QUESTION_RETRIES:
                self.ask_llm_to_question(llm_index)
                return

            print(f"[FALLBACK] LLM {llm_index} failed too many times. Skipping its question.")
            self.llm_questions_left[llm_index] -= 1
            self.current_llm_turn += 1
            self.advance_llm_turn()
            return

        target_id, visibility, question = parsed
        speaker_id = self.llm_player_ids[llm_index]

        if target_id == self.human_player_id:
            print("LLM asked the human a question.")

            for i in range(NUM_LLM_PLAYERS):
                self.dialogue_history[i].append({
                    "speaker": speaker_id,
                    "text": question,
                    "visibility": VISIBILITY_PUBLIC,
                    "targets": [],
                })

            self.waiting_for_human_answer = True
            self.pending_llm_question = (llm_index, question)

            self.player_labels[llm_index].setText(
                self.render_dialogue(llm_index) +
                f"\n\n❓ {player_label(speaker_id)} asks YOU:\n{question}"
            )
            return

        player_id_to_llm = {v: k for k, v in self.llm_player_ids.items()}
        target_llm_index = player_id_to_llm.get(target_id)
        if target_llm_index is None:
            return

        for i in range(NUM_LLM_PLAYERS):
            self.dialogue_history[i].append({
                "speaker": speaker_id,
                "text": question,
                "visibility": visibility,
                "targets": [target_id] if visibility == VISIBILITY_WHISPER else [],
            })

        self.waiting_for_llm_answer = True
        self.pending_llm_to_llm = (llm_index, target_llm_index, question)
        self.ask_llm_to_answer_llm(target_llm_index)

        self.player_labels[target_llm_index].setText(
            self.render_dialogue(target_llm_index, thinking=True)
        )

    def ask_llm_to_answer_llm(self, target_llm_index):
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

        for i in range(NUM_LLM_PLAYERS):
            self.dialogue_history[i].append({
                "speaker": speaker_id,
                "text": response,
                "visibility": VISIBILITY_PUBLIC,
                "targets": [],
            })

        for i in range(NUM_LLM_PLAYERS):
            self.player_labels[i].setText(self.render_dialogue(i))

        self.llm_questions_left[asking_llm_index] -= 1
        self.current_llm_turn += 1
        self.advance_llm_turn()


def parse_llm_question(text):
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


class LLMWorker(QThread):
    prompt_ready = pyqtSignal(int, str)

    def run(self):
        for index, (name, style, role) in enumerate(PLAYER_PROFILES):
            text = generate_initial_player_prompt(name, style, role)
            self.prompt_ready.emit(index, text)


class ChatWorker(QThread):
    response_ready = pyqtSignal(int, str)

    def __init__(self, player_index, prompt):
        super().__init__()
        self.player_index = player_index
        self.prompt = prompt

    def run(self):
        response = ollama_generate(self.prompt)
        self.response_ready.emit(self.player_index, response)


OLLAMA_URL = "http://localhost:11434/api/generate"

def ollama_generate(prompt, model="llama3.2:3b"):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.RequestException as e:
        return f"[LLM error: {e}]"


def generate_initial_player_prompt(name, style, role_name):
    role = WEREWOLF_ROLES[role_name]
    return ollama_generate(f"""
You are about to play a game of Werewolf.

Game overview:
- The game alternates between day and night.
- During the day, players discuss and try to identify the Werewolves.
- Werewolves secretly try to deceive the village.
- For now, there is NO voting and NO night actions.
- Focus only on discussion, suspicion, and roleplay.

LANGUAGE RULE (CRITICAL):
- Always respond in English only.
- Do NOT translate your output into Chinese.

Your role (private information):
- Name: {name}
- Role: {role_name.upper()}
- Team: {role["team"]}
- Description: {role["description"]}

Personality:
- You should behave in a {style} manner when speaking.

Instructions:
- Do NOT reveal your role.
- Speak as a human player would in a social deduction game.
- Be concise, conversational, and strategic.

Start by introducing yourself to the group in-character with a SHORT text (one or two sentences).
""".strip())


INCLUDE_OTHER_PLAYERS_CONTEXT = True

def build_prompt(player_index, histories, llm_player_ids, include_others=False):
    name, style, role_name = PLAYER_PROFILES[player_index]
    role = WEREWOLF_ROLES[role_name]

    prompt = [
        "SYSTEM:",
        "You are an expert Werewolf player. Your goal is to WIN.",
        "CRITICAL RULES:",
        "1. STRATEGY: Do not just be polite or roleplay. Analyze every message to find lies. Be suspicious and strategic according to your personality style.",
        "2. WHISPER: Messages starting with '(whisper)' are private. If you receive one, it is a secret alliance or a trap. NEVER reveal the content of a whisper in public dialogue.",
        "3. DECEPTION: If you are a Werewolf, mislead the others without being obvious. If you are a Villager, hunt the Werewolves.",
        "4. CONCISE: Respond directly in one or two short sentences. Avoid long theatrical descriptions or actions between asterisks.",
        "5. LANGUAGE: Always respond in English only. Never translate your output into Chinese.",
        "",
        "YOUR PRIVATE PROFILE:",
        f"- Name: {name}",
        f"- Role: {role_name.upper()}",
        f"- Team: {role['team']}",
        f"- Description: {role['description']}",
        f"- Personality Style: {style}",
        "",
        "Do NOT reveal your role directly. Speak only as your assigned player.",
        "",
    ]

    if include_others:
        prompt.append("Other players' dialogue:")
        for i, history in enumerate(histories):
            if i == player_index:
                continue
            for entry in history:
                if entry["visibility"] == VISIBILITY_PUBLIC:
                    prompt.append(f"{player_label(entry['speaker'])}: {entry['text']}")
        prompt.append("")

    prompt.append("Your dialogue history:")
    for entry in histories[player_index]:
        if entry["visibility"] == VISIBILITY_PUBLIC:
            prompt.append(f"{player_label(entry['speaker'])}: {entry['text']}")
        elif entry["visibility"] == VISIBILITY_WHISPER:
            if llm_player_ids[player_index] in entry["targets"]:
                prompt.append(f"(whisper) {player_label(entry['speaker'])}: {entry['text']}")

    prompt.append("")
    prompt.append(f"{player_label(llm_player_ids[player_index])}:")
    return "\n".join(prompt)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WerewolfGameWindow(initial_player_configs())
    window.show()
    sys.exit(app.exec())
    

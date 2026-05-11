import tkinter as tk
import math
import random
import time
from typing import List, Tuple, Callable


class RouletteWheel:
    def __init__(
        self,
        items: List[Tuple[str, float]],
        on_result: Callable[[str], None] | None = None,
        size: int = 400,
        removal_delay: int = 5000,  # milliseconds
    ):
        """
        items: List of (name, percentage) tuples
        on_result: Callback called with winner name after each spin
        removal_delay: Time to wait before removing winner (ms)
        """
        self.original_items = items
        self.items = items.copy()
        self.on_result = on_result
        self.size = size
        self.removal_delay = removal_delay

        self.angle = 0
        self.is_spinning = False

        self.root = tk.Tk()
        self.root.title("Roulette Wheel")

        self.center = size // 2
        self.radius = size // 2 - 20

        self.canvas = tk.Canvas(self.root, width=size, height=size)
        self.canvas.pack()

        self.spin_button = tk.Button(
            self.root,
            text="Spin 🎡",
            command=self.spin,
            font=("Arial", 12, "bold"),
        )
        self.spin_button.pack(pady=10)

        self.result_label = tk.Label(self.root, font=("Arial", 14, "bold"))
        self.result_label.pack()

        self.colors = self._generate_colors(len(self.items))
        self._normalize_percentages()
        self._draw_wheel()

    # -------------------- Core Logic --------------------

    def spin(self):
        if self.is_spinning or len(self.items) <= 1:
            return

        self.is_spinning = True
        self.result_label.config(text="")

        spin_duration = random.uniform(2.5, 4.0)
        start_time = time.time()
        initial_speed = random.uniform(18, 26)

        def animate():
            elapsed = time.time() - start_time
            if elapsed < spin_duration:
                speed = initial_speed * (1 - elapsed / spin_duration)
                self.angle = (self.angle + speed) % 360
                self._draw_wheel()
                self.root.after(16, animate)
            else:
                self.is_spinning = False
                winner = self._determine_winner()
                self.result_label.config(text=f"🏆 Winner: {winner}")

                if self.on_result:
                    self.on_result(winner)

                # Schedule removal
                self.root.after(self.removal_delay, lambda: self._remove_item(winner))

        animate()

    def _determine_winner(self) -> str:
        pointer_angle = (90 - self.angle) % 360
        cumulative = 0

        for label, percent in self.items:
            cumulative += percent * 3.6
            if pointer_angle <= cumulative:
                return label

        return self.items[-1][0]

    def _remove_item(self, label: str):
        if len(self.items) <= 1:
            return

        self.items = [(l, p) for l, p in self.items if l != label]
        self.colors = self._generate_colors(len(self.items))
        self.angle = 0

        self._normalize_percentages()
        self._draw_wheel()

        if len(self.items) == 1:
            self.result_label.config(text=f"🏆 FINAL WINNER: {self.items[0][0]}")

    def _normalize_percentages(self):
        """Spread remaining items evenly."""
        if not self.items:
            return

        even_percent = 100 / len(self.items)
        self.items = [(label, even_percent) for label, _ in self.items]

    # -------------------- Drawing --------------------

    def _draw_wheel(self):
        self.canvas.delete("all")
        start_angle = self.angle

        for (label, percent), color in zip(self.items, self.colors):
            extent = percent * 3.6

            self.canvas.create_arc(
                20, 20, self.size - 20, self.size - 20,
                start=start_angle,
                extent=extent,
                fill=color,
                outline="black",
            )

            mid = math.radians(start_angle + extent / 2)
            x = self.center + math.cos(mid) * self.radius * 0.65
            y = self.center - math.sin(mid) * self.radius * 0.65

            self.canvas.create_text(
                x, y, text=label, font=("Arial", 10, "bold")
            )

            start_angle += extent

        # Pointer
        self.canvas.create_polygon(
            self.center - 10, 5,
            self.center + 10, 5,
            self.center, 25,
            fill="red",
        )

    def _generate_colors(self, n: int):
        return [
            f"#{random.randint(70,255):02x}{random.randint(70,255):02x}{random.randint(70,255):02x}"
            for _ in range(n)
        ]

    # -------------------- Public API --------------------

    def start(self):
        self.root.mainloop()

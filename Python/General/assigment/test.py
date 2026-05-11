from rTest import RouletteWheel


def on_spin_result(winner):
    print(f"Eliminated: {winner}")


entries = [
    ("Option A", 40),
    ("Option B", 30),
    ("Option C", 20),
    ("Option D", 10),
]

wheel = RouletteWheel(entries, on_result=on_spin_result)
wheel.start()

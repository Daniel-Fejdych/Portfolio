import random

# -----------------------------
# CONFIG
# -----------------------------
NUM_STOCKS = 20
NUM_NPCS = 5
INITIAL_ECONOMY = 1_000_000
PLAYER_START_CASH = 10_000
TURNS = 0

# -----------------------------
# STOCK CLASS
# -----------------------------
class Stock:
    def __init__(self, name):
        self.name = name
        self.total_shares = random.randint(500, 2000)
        self.price = random.uniform(10, 200)
        self.trend = random.choice(["growth", "decline", "volatile", "stable"])

    @property
    def value(self):
        return self.total_shares * self.price

    def update_price(self):
        drift = 0

        if self.trend == "growth":
            drift = random.uniform(0.001, 0.02)
        elif self.trend == "decline":
            drift = random.uniform(-0.02, -0.001)
        elif self.trend == "volatile":
            drift = random.uniform(-0.05, 0.05)
        elif self.trend == "stable":
            drift = random.uniform(-0.005, 0.005)

        noise = random.uniform(-0.01, 0.01)
        self.price *= (1 + drift + noise)

        if self.price < 1:
            self.price = 1

# -----------------------------
# PLAYER CLASS
# -----------------------------
class Player:
    def __init__(self, name, cash):
        self.name = name
        self.cash = cash
        self.portfolio = {i: 0 for i in range(NUM_STOCKS)}

    def net_worth(self, stocks):
        total = self.cash
        for i, shares in self.portfolio.items():
            total += shares * stocks[i].price
        return total

# -----------------------------
# GAME CLASS
# -----------------------------
class Game:
    def __init__(self):
        self.stocks = [Stock(f"Stock{i}") for i in range(NUM_STOCKS)]
        self.players = [Player("You", PLAYER_START_CASH)]

        for i in range(NUM_NPCS):
            self.players.append(Player(f"NPC{i}", 50_000))

        self.total_economy = INITIAL_ECONOMY

    # -------------------------
    # DISPLAY
    # -------------------------
    def show_market(self):
        print("\n=== MARKET ===")
        for i, s in enumerate(self.stocks):
            print(f"{i}: {s.name} | Price: {s.price:.2f} | Shares: {s.total_shares}")

    def show_portfolio(self, player):
        print("\n=== YOUR PORTFOLIO ===")
        for i, shares in player.portfolio.items():
            if shares > 0:
                print(f"{self.stocks[i].name}: {shares} shares")
        print(f"Cash: {player.cash:.2f}")
        print(f"Net Worth: {player.net_worth(self.stocks):.2f}")

    # -------------------------
    # BUY / SELL
    # -------------------------
    def buy(self, player, stock_id, amount):
        stock = self.stocks[stock_id]
        cost = stock.price * amount

        if cost > player.cash:
            print("Not enough cash.")
            return

        if player.portfolio[stock_id] + amount > stock.total_shares:
            print("Not enough shares available.")
            return

        player.cash -= cost
        player.portfolio[stock_id] += amount

        # price impact
        stock.price *= (1 + 0.01 * (amount / stock.total_shares))

    def sell(self, player, stock_id, amount):
        stock = self.stocks[stock_id]

        if player.portfolio[stock_id] < amount:
            print("Not enough shares.")
            return

        revenue = stock.price * amount
        player.cash += revenue
        player.portfolio[stock_id] -= amount

        # price impact
        stock.price *= (1 - 0.01 * (amount / stock.total_shares))

    # -------------------------
    # NPC BEHAVIOR
    # -------------------------
    def npc_turn(self, npc):
        for _ in range(random.randint(1, 3)):
            stock_id = random.randint(0, NUM_STOCKS - 1)
            stock = self.stocks[stock_id]

            action = random.choice(["buy", "sell"])

            if action == "buy":
                amount = random.randint(1, 10)
                cost = stock.price * amount
                if npc.cash >= cost:
                    npc.cash -= cost
                    npc.portfolio[stock_id] += amount
                    stock.price *= 1.002

            else:  # sell
                amount = random.randint(1, 10)
                if npc.portfolio[stock_id] >= amount:
                    npc.cash += stock.price * amount
                    npc.portfolio[stock_id] -= amount
                    stock.price *= 0.998

    # -------------------------
    # ECONOMY UPDATE
    # -------------------------
    def update_economy(self):
        global TURNS
        TURNS += 1

        # general stock movement
        for stock in self.stocks:
            stock.update_price()

        # random crash chance
        if random.random() < 0.05:
            print("\n⚠ MARKET CRASH!")
            for stock in self.stocks:
                stock.price *= random.uniform(0.7, 0.9)

        # slow growth
        growth = random.uniform(0.001, 0.01)
        self.total_economy *= (1 + growth)

    # -------------------------
    # GAME LOOP
    # -------------------------
    def play(self):
        player = self.players[0]

        while True:
            print(f"\n=== TURN {TURNS} ===")
            print(f"Total Economy: {self.total_economy:.2f}")

            print("\n1. View Market")
            print("2. View Portfolio")
            print("3. Buy")
            print("4. Sell")
            print("5. Next Turn")
            print("6. Quit")

            choice = input("Choose: ")

            if choice == "1":
                self.show_market()

            elif choice == "2":
                self.show_portfolio(player)

            elif choice == "3":
                self.show_market()
                sid = int(input("Stock ID: "))
                amt = int(input("Amount: "))
                self.buy(player, sid, amt)

            elif choice == "4":
                self.show_portfolio(player)
                sid = int(input("Stock ID: "))
                amt = int(input("Amount: "))
                self.sell(player, sid, amt)

            elif choice == "5":
                # NPC turns
                for npc in self.players[1:]:
                    self.npc_turn(npc)

                self.update_economy()

            elif choice == "6":
                break

            else:
                print("Invalid choice.")

# -----------------------------
# RUN GAME
# -----------------------------
if __name__ == "__main__":
    game = Game()
    game.play()

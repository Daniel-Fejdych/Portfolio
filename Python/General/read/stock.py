import random
import math

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def random_normal(mean=0.0, std=1.0):
    """Return a normally distributed random number using Box-Muller."""
    u1 = random.random()
    u2 = random.random()
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mean + std * z

def clamp(value, min_val, max_val):
    """Clamp a value between min_val and max_val."""
    return max(min_val, min(value, max_val))

# ----------------------------------------------------------------------
# Stock class
# ----------------------------------------------------------------------
class Stock:
    def __init__(self, name, shares_outstanding, initial_price):
        self.name = name
        self.shares_outstanding = shares_outstanding
        self.price = initial_price

        # Pattern parameters (realistic random walk)
        self.drift = random.uniform(-0.02, 0.04)      # annual drift (~ -2% to +4%)
        self.volatility = random.uniform(0.10, 0.35)  # annual volatility
        self.mean_reversion = random.uniform(0.0, 0.1)  # small mean reversion factor
        self.long_term_price = initial_price

    def market_cap(self):
        return self.price * self.shares_outstanding

    def update_natural_price(self, dt=1.0):
        """Update price according to a geometric Brownian motion with mean reversion."""
        # Mean reversion component
        reversion = self.mean_reversion * (self.long_term_price - self.price) / self.price
        # Random shock
        shock = random_normal(0, self.volatility * math.sqrt(dt))
        # Drift + reversion + noise
        change = (self.drift + reversion) * dt + shock
        self.price *= math.exp(change)
        # Ensure price never becomes zero or negative
        self.price = max(self.price, 0.01)
        # Slowly adapt long-term price to the current price (trend following)
        self.long_term_price = 0.95 * self.long_term_price + 0.05 * self.price

    def apply_trade_impact(self, quantity, is_buy):
        """
        Adjust price based on a trade.
        Buying increases price, selling decreases it.
        The impact is stronger for larger trades relative to shares outstanding.
        """
        impact_factor = 0.005  # 0.5% impact per 10% of outstanding shares
        relative_volume = quantity / self.shares_outstanding
        if is_buy:
            multiplier = 1.0 + impact_factor * relative_volume
        else:
            multiplier = 1.0 - impact_factor * relative_volume
        self.price *= multiplier
        self.price = max(self.price, 0.01)  # safety

# ----------------------------------------------------------------------
# Player class
# ----------------------------------------------------------------------
class Player:
    def __init__(self, name, cash):
        self.name = name
        self.cash = cash
        self.holdings = {}  # stock_name -> shares

    def net_worth(self, stocks):
        """Calculate total wealth using current stock prices."""
        total = self.cash
        for stock in stocks:
            shares = self.holdings.get(stock.name, 0)
            total += shares * stock.price
        return total

    def can_buy(self, stock, quantity):
        """Check if player has enough cash to buy given quantity at current price."""
        return self.cash >= quantity * stock.price

    def can_sell(self, stock, quantity):
        """Check if player owns enough shares of the stock."""
        return self.holdings.get(stock.name, 0) >= quantity

# ----------------------------------------------------------------------
# Game class
# ----------------------------------------------------------------------
class StockTradingGame:
    def __init__(self):
        self.stocks = []
        self.players = []
        self.human_index = 0
        self.turn = 0

        # Economy growth parameters
        self.base_growth = 0.01        # 1% per turn
        self.growth_volatility = 0.005  # extra random up/down
        self.crash_prob = 0.05         # 5% chance per turn
        self.crash_magnitude = -0.2     # crash loses 20% of total economy

        self._init_stocks()
        self._init_players()
        self._sync_total_economy()

    def _init_stocks(self):
        """Create 20 stocks with random names, shares, and initial prices."""
        prefixes = ["Tech", "Energy", "Retail", "Health", "Finance", "Industrial", "Consumer", "Media", "Transport", "Utility"]
        suffixes = ["Corp", "Inc", "Ltd", "Group", "Holdings", "Systems", "Solutions", "Partners", "Ventures", "Dynamics"]

        for i in range(20):
            name = f"{random.choice(prefixes)} {random.choice(suffixes)}"
            shares = random.randint(1000, 10000)
            price = random.uniform(10, 500)
            self.stocks.append(Stock(name, shares, price))

    def _init_players(self):
        """Create human and NPC players with initial cash and share distribution."""
        # Human
        human = Player("Human", 10000.0)
        self.players.append(human)

        # NPCs (5 players)
        npc_names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        for name in npc_names:
            cash = random.uniform(5000, 15000)
            self.players.append(Player(name, cash))

        # Distribute all shares of each stock among all players
        for stock in self.stocks:
            total_shares = stock.shares_outstanding
            # Distribute randomly: human gets some, NPCs get the rest
            shares_left = total_shares
            # Give human a random portion (0% to 30% of total)
            human_shares = int(shares_left * random.uniform(0, 0.3))
            self.players[0].holdings[stock.name] = human_shares
            shares_left -= human_shares

            # Give each NPC a random portion, leaving a small remainder that goes to a random NPC
            npc_players = self.players[1:]
            for p in npc_players:
                if shares_left == 0:
                    break
                max_share = min(shares_left, int(shares_left * random.uniform(0.1, 0.5)))
                if max_share > 0:
                    shares = random.randint(0, max_share)
                    p.holdings[stock.name] = shares
                    shares_left -= shares
            # If any shares remain, give them to the first NPC
            if shares_left > 0:
                npc_players[0].holdings[stock.name] += shares_left

    def _sync_total_economy(self):
        """Ensure total cash + total market cap equals total_economy (just for initial)."""
        total = sum(p.cash for p in self.players) + sum(s.market_cap() for s in self.stocks)
        self.total_economy = total

    def _apply_macro_growth(self):
        """
        Adjust the total economy according to growth/crash,
        then scale all cash and stock prices proportionally to match.
        """
        # Compute current total
        current_total = sum(p.cash for p in self.players) + sum(s.market_cap() for s in self.stocks)

        # Determine growth rate for this turn
        growth = self.base_growth + random_normal(0, self.growth_volatility)

        # Check for crash
        if random.random() < self.crash_prob:
            growth = self.crash_magnitude  # negative growth

        # New target total economy
        target_total = current_total * (1 + growth)

        # Scaling factor
        scale = target_total / current_total

        # Scale all cash and all stock prices
        for p in self.players:
            p.cash *= scale
        for s in self.stocks:
            s.price *= scale

        self.total_economy = target_total

    def _execute_trade(self, buyer, seller, stock, quantity, price):
        """
        Transfer shares and cash between buyer and seller.
        Also update the stock's price based on the trade direction.
        """
        if buyer is seller:
            return False  # can't trade with yourself

        # Check both can do the trade
        if not buyer.can_buy(stock, quantity):
            return False
        if not seller.can_sell(stock, quantity):
            return False

        # Transfer shares
        buyer.holdings[stock.name] = buyer.holdings.get(stock.name, 0) + quantity
        seller.holdings[stock.name] = seller.holdings.get(stock.name, 0) - quantity

        # Transfer cash
        cost = quantity * price
        buyer.cash -= cost
        seller.cash += cost

        # Apply price impact
        # The buyer's action is a buy, the seller's action is a sell.
        # We treat this as a single net trade: buying pressure increases price, selling decreases it.
        # We'll apply both impacts (they partially cancel, but we want to simulate that a buy order raises price and a sell lowers it).
        # To keep it simple, we'll apply one impact per trade based on the buyer's side.
        # For realism, a buy order raises price, a sell order lowers it.
        # Here we know who initiated the trade (the caller will set is_buy based on who initiated).
        # But to keep this function generic, we'll pass is_buy parameter.
        # Actually, we'll pass is_buy flag from the caller.
        # We'll handle price update outside this function to keep it clean.
        return True

    def _human_buy(self):
        """Prompt human to buy shares from NPCs."""
        # Show stocks with indices
        print("\nAvailable stocks:")
        for i, s in enumerate(self.stocks):
            print(f"{i+1:2}. {s.name:20} Price: ${s.price:.2f}  Outstanding: {s.shares_outstanding:,}")

        try:
            choice = int(input("Select stock number: ")) - 1
            if choice < 0 or choice >= len(self.stocks):
                print("Invalid stock number.")
                return
            stock = self.stocks[choice]

            quantity = int(input(f"How many shares of {stock.name} to buy? "))
            if quantity <= 0:
                print("Quantity must be positive.")
                return

            # Check human has enough cash
            if not self.players[0].can_buy(stock, quantity):
                print(f"Insufficient cash. You have ${self.players[0].cash:.2f}, need ${quantity * stock.price:.2f}.")
                return

            # Find total shares available among NPCs
            npcs = self.players[1:]
            total_available = sum(p.holdings.get(stock.name, 0) for p in npcs)
            if total_available < quantity:
                print(f"Not enough shares available from NPCs. Only {total_available} shares available.")
                return

            # Execute trade: human buys from NPCs (collectively)
            # We'll take shares from NPCs proportionally to their holdings
            human = self.players[0]
            remaining = quantity
            for npc in npcs:
                if remaining <= 0:
                    break
                avail = npc.holdings.get(stock.name, 0)
                if avail == 0:
                    continue
                take = min(avail, remaining)
                # Perform the transfer
                human.holdings[stock.name] = human.holdings.get(stock.name, 0) + take
                npc.holdings[stock.name] -= take
                cost = take * stock.price
                human.cash -= cost
                npc.cash += cost
                remaining -= take

            # Apply price increase due to buying pressure
            stock.apply_trade_impact(quantity, is_buy=True)
            print(f"Bought {quantity} shares of {stock.name} at ${stock.price:.2f} (price increased).")

        except ValueError:
            print("Invalid input.")

    def _human_sell(self):
        """Prompt human to sell shares to NPCs."""
        human = self.players[0]

        # Show human's holdings
        print("\nYour holdings:")
        for s in self.stocks:
            shares = human.holdings.get(s.name, 0)
            if shares > 0:
                print(f"{s.name:20} {shares:6} shares @ ${s.price:.2f} = ${shares * s.price:.2f}")

        stock_name = input("Enter stock name to sell: ").strip()
        # Find stock by name (case-insensitive)
        stock = None
        for s in self.stocks:
            if s.name.lower() == stock_name.lower():
                stock = s
                break
        if not stock:
            print("Stock not found.")
            return

        try:
            quantity = int(input(f"How many shares of {stock.name} to sell? "))
            if quantity <= 0:
                print("Quantity must be positive.")
                return

            if not human.can_sell(stock, quantity):
                print(f"You only have {human.holdings.get(stock.name, 0)} shares.")
                return

            # Check if NPCs have enough cash to buy
            npcs = self.players[1:]
            total_cash_needed = quantity * stock.price
            total_npc_cash = sum(p.cash for p in npcs)
            if total_npc_cash < total_cash_needed:
                print(f"NPCs don't have enough cash to buy that many shares. They have ${total_npc_cash:.2f} total.")
                return

            # Sell to NPCs: distribute shares and cash proportionally to NPC cash holdings
            human = self.players[0]
            remaining_shares = quantity
            # Sort NPCs by cash to simulate buying power? We'll just go in order and take cash proportionally.
            for npc in npcs:
                if remaining_shares <= 0:
                    break
                # NPC can spend up to its cash, but we'll buy as many as it can afford at current price
                max_shares_npc = int(npc.cash // stock.price)
                if max_shares_npc <= 0:
                    continue
                take = min(remaining_shares, max_shares_npc)
                if take > 0:
                    # Transfer
                    human.holdings[stock.name] -= take
                    npc.holdings[stock.name] = npc.holdings.get(stock.name, 0) + take
                    cost = take * stock.price
                    human.cash += cost
                    npc.cash -= cost
                    remaining_shares -= take

            if remaining_shares > 0:
                print(f"Warning: Only sold {quantity - remaining_shares} shares. NPCs didn't have enough cash for all.")
            else:
                print(f"Sold {quantity} shares of {stock.name} at ${stock.price:.2f}.")

            # Apply price decrease due to selling pressure
            stock.apply_trade_impact(quantity, is_buy=False)

        except ValueError:
            print("Invalid input.")

    def _show_stock_info(self):
        """Display detailed info for a selected stock."""
        print("\nStocks:")
        for i, s in enumerate(self.stocks):
            print(f"{i+1:2}. {s.name:20} Price: ${s.price:.2f}  Outstanding: {s.shares_outstanding:,}")
        try:
            choice = int(input("Select stock number: ")) - 1
            if 0 <= choice < len(self.stocks):
                s = self.stocks[choice]
                print(f"\n{s.name}")
                print(f"Price: ${s.price:.2f}")
                print(f"Market Cap: ${s.market_cap():,.2f}")
                print(f"Shares Outstanding: {s.shares_outstanding:,}")
                print(f"Drift: {s.drift*100:.2f}%  Volatility: {s.volatility*100:.2f}%")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    def _show_market_summary(self):
        """Show overall market statistics and human's portfolio."""
        total_cash = sum(p.cash for p in self.players)
        total_mcap = sum(s.market_cap() for s in self.stocks)
        print(f"\n--- Market Summary (Turn {self.turn}) ---")
        print(f"Total Economy Value: ${self.total_economy:,.2f}")
        print(f"Total Player Cash: ${total_cash:,.2f}")
        print(f"Total Market Cap: ${total_mcap:,.2f}")
        print(f"Human Wealth: ${self.players[0].net_worth(self.stocks):,.2f}")
        # Show top 5 stocks by market cap
        sorted_stocks = sorted(self.stocks, key=lambda s: s.market_cap(), reverse=True)
        print("\nTop 5 stocks by market cap:")
        for s in sorted_stocks[:5]:
            print(f"{s.name:20} ${s.market_cap():,.2f} (${s.price:.2f})")

    def _npc_trade(self, npc):
        """Perform one random trade for a given NPC (with the human)."""
        human = self.players[0]
        # Randomly decide buy or sell
        if random.random() < 0.5:
            # NPC buys from human
            # Choose a stock that human owns
            candidate_stocks = [s for s in self.stocks if human.holdings.get(s.name, 0) > 0]
            if not candidate_stocks:
                return
            stock = random.choice(candidate_stocks)
            # Max quantity NPC can afford
            max_afford = int(npc.cash // stock.price)
            # Max human can sell
            human_shares = human.holdings.get(stock.name, 0)
            max_qty = min(max_afford, human_shares)
            if max_qty <= 0:
                return
            quantity = random.randint(1, max_qty)
            # Execute trade
            human.holdings[stock.name] -= quantity
            npc.holdings[stock.name] = npc.holdings.get(stock.name, 0) + quantity
            cost = quantity * stock.price
            human.cash += cost
            npc.cash -= cost
            # Apply price increase (NPC buying)
            stock.apply_trade_impact(quantity, is_buy=True)
            # Optional: print message
            # print(f"NPC {npc.name} bought {quantity} shares of {stock.name} from you.")
        else:
            # NPC sells to human
            # Choose a stock NPC owns
            candidate_stocks = [s for s in self.stocks if npc.holdings.get(s.name, 0) > 0]
            if not candidate_stocks:
                return
            stock = random.choice(candidate_stocks)
            # Max quantity NPC can sell
            npc_shares = npc.holdings.get(stock.name, 0)
            # Max human can afford
            max_human_can_buy = int(human.cash // stock.price)
            max_qty = min(npc_shares, max_human_can_buy)
            if max_qty <= 0:
                return
            quantity = random.randint(1, max_qty)
            # Execute trade
            npc.holdings[stock.name] -= quantity
            human.holdings[stock.name] = human.holdings.get(stock.name, 0) + quantity
            cost = quantity * stock.price
            npc.cash += cost
            human.cash -= cost
            # Apply price decrease (NPC selling)
            stock.apply_trade_impact(quantity, is_buy=False)
            # Optional: print message
            # print(f"NPC {npc.name} sold {quantity} shares of {stock.name} to you.")

    def _next_turn(self):
        """Advance the game by one turn."""
        self.turn += 1
        print(f"\n--- Turn {self.turn} ---")

        # 1. Natural price movements for all stocks
        for stock in self.stocks:
            stock.update_natural_price()

        # 2. Human trades already handled in the main loop; we just finalize the turn now.
        # 3. NPC trades (each NPC trades once)
        npcs = self.players[1:]
        for npc in npcs:
            self._npc_trade(npc)

        # 4. Apply macro economic growth/crash and scale the economy
        self._apply_macro_growth()

        # 5. Print a small summary
        print(f"Economy value now: ${self.total_economy:,.2f}")
        print(f"Your net worth: ${self.players[0].net_worth(self.stocks):,.2f}")

    def run(self):
        """Main game loop."""
        print("Welcome to the Stock Trading Game!")
        print("You can buy and sell shares, view stock info, and advance turns.")
        print("The economy grows slowly over time but may crash occasionally.")
        print("NPCs will trade with you each turn to simulate market activity.")

        while True:
            human = self.players[0]
            print(f"\n--- Turn {self.turn} ---")
            print(f"Your cash: ${human.cash:.2f}")
            print(f"Your net worth: ${human.net_worth(self.stocks):,.2f}")
            print("\nOptions:")
            print("  1. Buy shares")
            print("  2. Sell shares")
            print("  3. View stock information")
            print("  4. View market summary")
            print("  5. Next turn")
            print("  6. Quit")

            choice = input("Choose an option: ").strip()
            if choice == '1':
                self._human_buy()
            elif choice == '2':
                self._human_sell()
            elif choice == '3':
                self._show_stock_info()
            elif choice == '4':
                self._show_market_summary()
            elif choice == '5':
                self._next_turn()
            elif choice == '6':
                print("Thanks for playing!")
                break
            else:
                print("Invalid option. Please enter 1-6.")

# ----------------------------------------------------------------------
# Run the game
# ----------------------------------------------------------------------
if __name__ == "__main__":
    game = StockTradingGame()
    game.run()

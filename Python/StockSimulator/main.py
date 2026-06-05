from dataclasses import dataclass

import yfinance as yf
from PyQt6.QtCore import QTimer, QThread
from PyQt6.QtGui import QIntValidator

import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QHBoxLayout, QLabel, QMessageBox, QComboBox, QInputDialog
)


@dataclass
class Stock:
    symbol: str
    price: float = 0.0
    shares: int = 0



class Profile:
    def __init__(self, name: str, funds: float, holdings: dict):
        self.name = name          # username
        self.funds = funds        # available cash
        self.holdings = holdings  # dict {symbol: shares}

    def save(self, directory="profiles"):
        """Save profile to a JSON file inside the given directory."""
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.name}.json")
        data = {
            "name": self.name,
            "funds": self.funds,
            "holdings": self.holdings
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load(name: str, directory="profiles"):
        """Load a profile from a JSON file."""
        filepath = os.path.join(directory, f"{name}.json")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Profile {name} not found")
        with open(filepath, "r") as f:
            data = json.load(f)
        return Profile(data["name"], data["funds"], data["holdings"])

    @staticmethod
    def list_profiles(directory="profiles"):
        """Return a list of existing profile names (without .json extension)."""
        if not os.path.exists(directory):
            return []
        return [f.replace(".json", "") for f in os.listdir(directory) if f.endswith(".json")]



# Starting cash balance for simulated trading.
INITIAL_FUNDS = 10000

# How often should the prices increase.
REFRESH_INTERVAL_MS = 60_000 # 60 seconds


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_profile = None  # will be set after loading/creating a profile

        # Predefined list of stock symbols shown in the UI.
        self.stocks = [Stock('MSFT'), Stock('AAPL'), Stock('GOOG'), Stock('NVDA'),
                             Stock('META'), Stock('TSLA'), Stock('AVGO'), Stock('JPM'),
                             Stock('WMT'), Stock('SHEL')]

        # Number of stocks displayed in the portfolio table.
        self.num_stocks = len(self.stocks)

        # Setup local variables.
        # Global variable to store current available cash.
        self.current_funds = INITIAL_FUNDS

        self.setWindowTitle("Trading Simulator")
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        # Create the portfolio table with columns:
        # ticker symbol, current price, owned shares,
        # quantity input field, and buy/sell actions.
        self.table = QTableWidget()
        self.table.setRowCount(self.num_stocks)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Stock Name", "Stock Price", "Current Stock", "Amount", "Actions"]
        )

        # Store references to quantity input boxes so the
        # buy/sell handlers can access user-entered values.
        self.quantity_inputs = []

        # Populate each row with stock data and controls.
        for row in range(self.num_stocks):
            # List values
            self.table.setItem(row, 0, QTableWidgetItem(self.stocks[row].symbol))
            self.table.setItem(row, 1, QTableWidgetItem(f"{self.stocks[row].price} $"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{self.stocks[row].shares}"))

            # Text box
            line_edit = QLineEdit()
            self.quantity_inputs.append(line_edit)
            self.table.setCellWidget(row, 3, line_edit)
            line_edit.setValidator(QIntValidator(0, 2147483647))

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)

            buy_button = QPushButton("BUY")
            sell_button = QPushButton("SELL")

            # Connect buttons to handlers while preserving
            # the row index associated with the stock.
            buy_button.clicked.connect(
                lambda _, r=row: self.buy_stock(r)
            )
            sell_button.clicked.connect(
                lambda _, r=row: self.sell_stock(r)
            )

            action_layout.addWidget(buy_button)
            action_layout.addWidget(sell_button)

            self.table.setCellWidget(row, 4, action_widget)

        layout.addWidget(self.table)
        profile_layout = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed)
        self.new_profile_btn = QPushButton("New Profile")
        self.new_profile_btn.clicked.connect(self.new_profile)
        self.save_profile_btn = QPushButton("Save Profile")
        self.save_profile_btn.clicked.connect(self.save_current_profile)

        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addWidget(self.new_profile_btn)
        profile_layout.addWidget(self.save_profile_btn)

        layout.insertLayout(0, profile_layout)  # Insert at the top

        # Add a section to display current funds at the bottom.
        self.current_funds_text = QLabel("")
        self.update_funds(self.current_funds)
        layout.addWidget(self.current_funds_text)

        # Create a fetch worker to not freeze the GUI.
        self.worker = FetchWorker(self.stocks, self.table)

        # Retrieve current market prices from Yahoo Finance during startup.
        self.update_prices()

        # Update stock prices every minute
        self.price_timer = QTimer(self)
        self.price_timer.timeout.connect(self.update_prices)
        self.price_timer.start(REFRESH_INTERVAL_MS)

        # Load the profile list from files.
        self.refresh_profile_list()


    # Updates prices table.
    def update_prices(self) -> None:
        self.worker.run()

    def get_quantity(self, row: int) -> tuple[int, float, float]:
        try:
            # Read the desired number of shares from the input field.
            num_shares = int(self.quantity_inputs[row].text())

            share_price = self.stocks[row].price
            # Calculate total prize.
            total_price = num_shares * share_price
            return num_shares, share_price, total_price
        except ValueError:
            return 0, 0, 0

    def buy_stock(self, row: int) -> None:
        """
        Handler for buying
        """
        num_shares_buy, share_price, total_price = self.get_quantity(row)

        # Execute purchase only if sufficient funds exist.
        if 0 <= total_price <= self.current_funds:
            # Update portfolio holdings and available cash balance.
            self.stocks[row].shares += num_shares_buy
            self.current_funds -= total_price
            # Update funds and stocks displays.
            self.update_funds(self.current_funds)
            self.update_stock_held(self.stocks[row].shares, row)


    def sell_stock(self, row: int) -> None:
        """
        Handler for selling
        """
        # Read the number of shares the user wishes to sell.
        num_shares_sell, share_price, total_price = self.get_quantity(row)

        # Ensure the user cannot sell more shares than currently owned.
        if 0 <= num_shares_sell <= self.stocks[row].shares:
            # Update holdings and credit cash from the sale.
            self.stocks[row].shares -= num_shares_sell
            self.current_funds += total_price
            # Update funds and stocks displays.
            self.update_funds(self.current_funds)
            self.update_stock_held(self.stocks[row].shares, row)

    def update_funds(self, new_funds: float) -> None:
        self.current_funds_text.setText(f"Current funds: {new_funds:.2f} $")

    def update_stock_held(self, new_stock_held: int, row: int) -> None:
        self.table.setItem(row, 2, QTableWidgetItem(f'{new_stock_held}'))

    def refresh_profile_list(self):
        """Update the combo box with available profiles."""
        profiles = Profile.list_profiles()
        self.profile_combo.clear()
        self.profile_combo.addItems(profiles)
        if profiles:
            self.profile_combo.setCurrentIndex(0)
        else:
            # No profiles exist → create a default one
            self.create_default_profile()

    def create_default_profile(self):
        """Create a default profile with initial funds and zero holdings."""
        default_holdings = {stock.symbol: 0 for stock in self.stocks}
        default_profile = Profile("Default", INITIAL_FUNDS, default_holdings)
        default_profile.save()
        self.refresh_profile_list()

    def on_profile_changed(self, index):
        if index < 0:
            return
        # Optionally auto-save current profile before switching
        if self.current_profile is not None:
            self.save_current_profile()
        profile_name = self.profile_combo.currentText()
        try:
            self.current_profile = Profile.load(profile_name)
            self.apply_profile_to_ui()
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Could not load profile: {e}")

    def apply_profile_to_ui(self):
        """Update the UI with the loaded profile's funds and holdings."""
        # Update funds display
        self.current_funds = self.current_profile.funds  # keep local copy for convenience
        self.update_funds(self.current_funds)

        # Update each stock's shares in the table and in the Stock objects
        for row, stock in enumerate(self.stocks):
            shares = self.current_profile.holdings.get(stock.symbol, 0)
            stock.shares = shares
            self.update_stock_held(shares, row)

    def save_current_profile(self):
        if self.current_profile is None:
            QMessageBox.information(self, "No Profile", "No profile is currently loaded.")
            return
        # Sync holdings from the stock objects into the profile
        for stock in self.stocks:
            self.current_profile.holdings[stock.symbol] = stock.shares
        self.current_profile.funds = self.current_funds
        self.current_profile.save()
        QMessageBox.information(self, "Saved", f"Profile '{self.current_profile.name}' saved.")

    def new_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Enter username:")
        if not ok or not name.strip():
            return
        # Check if profile already exists
        if name in Profile.list_profiles():
            QMessageBox.warning(self, "Duplicate", "A profile with that name already exists.")
            return
        holdings = {stock.symbol: 0 for stock in self.stocks}
        new_profile = Profile(name.strip(), INITIAL_FUNDS, holdings)
        new_profile.save()
        self.refresh_profile_list()
        # Load the newly created profile
        self.profile_combo.setCurrentText(name.strip())



# FetchWorker fetches new data without blocking GUI.
class FetchWorker(QThread):
    def __init__(self, stock_list: list[Stock], table):
        super().__init__()
        self.stock_list = stock_list
        self.table = table

    def run(self) -> None:
        for row, stock in enumerate(self.stock_list):
            try:
                ticker = yf.Ticker(stock.symbol)
                stock.price = price = float(ticker.info["regularMarketPrice"])
                self.table.setItem(row, 1, QTableWidgetItem(f"{price} $"))
            except Exception as e:
                QMessageBox.warning(self.table,f"Failed to update {stock.symbol}: {e}","",)


# Create and start the Qt application event loop.
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
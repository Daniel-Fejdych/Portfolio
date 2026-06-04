import yfinance as yf

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QHBoxLayout
)
from functools import partial

tick_prices = []

if __name__ == '__main__':
    ticks = ['MSFT', 'AAPL', 'GOOG', 'NVDA', 'META', 'TSLA', 'AVGO', 'JPM', 'WMT', 'SHEL']
    for tick in ticks:
        ticker = yf.Ticker(tick)  # Use tickers.live() for live responses later.
        tick_prices.append(ticker.info["regularMarketPrice"])
        print(tick_prices)


SIZE = 10


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("List Table Example")
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        # Example Size-element lists
        self.list1 = ticks
        self.list2 = tick_prices
        self.list3 = [f"Item3-{i}" for i in range(SIZE)]

        self.table = QTableWidget()
        self.table.setRowCount(SIZE)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Stock Name", "Stock Price $", "Current Stock", "Amount", "Actions"]
        )

        self.line_edits = []

        for row in range(SIZE):
            # List values
            self.table.setItem(row, 0, QTableWidgetItem(self.list1[row]))
            self.table.setItem(row, 1, QTableWidgetItem(str(self.list2[row])))
            self.table.setItem(row, 2, QTableWidgetItem(self.list3[row]))

            # Text box
            line_edit = QLineEdit()
            self.line_edits.append(line_edit)
            self.table.setCellWidget(row, 3, line_edit)

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)

            btn_a = QPushButton("BUY")
            btn_b = QPushButton("SELL")

            btn_a.clicked.connect(
                partial(self.handle_button_click_buy, row)
            )
            btn_b.clicked.connect(
                partial(self.handle_button_click_sell, row)
            )

            action_layout.addWidget(btn_a)
            action_layout.addWidget(btn_b)

            self.table.setCellWidget(row, 4, action_widget)

        layout.addWidget(self.table)

    def handle_button_click_buy(self, row):
        """
        Handler for buying
        """
        text = self.line_edits[row].text()

        print(
            "BUY"
            f"Row: {row}, "
            f"Text: '{text}', "
            f"List1: {self.list1[row]}, "
            f"List2: {self.list2[row]}, "
            f"List3: {self.list3[row]}"
        )

    def handle_button_click_sell(self, row):
        """
        Handler for buying
        """
        text = self.line_edits[row].text()

        print(
            "SELL"
            f"Row: {row}, "
            f"Text: '{text}', "
            f"List1: {self.list1[row]}, "
            f"List2: {self.list2[row]}, "
            f"List3: {self.list3[row]}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
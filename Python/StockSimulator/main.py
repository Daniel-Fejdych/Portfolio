import yfinance as yf


if __name__ == '__main__':
    dat = yf.Ticker("MSFT")
    print(dat.info)
    print(dat.calendar)
    print(dat.analyst_price_targets)
    print(dat.quarterly_income_stmt)
    print(dat.history(period='1mo'))
    print(dat.option_chain(dat.options[0]).calls)
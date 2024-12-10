import os
from dotenv import load_dotenv
import yfinance as yf
import sys
import sqlite3

load_dotenv()

# SQLite configuration
SQLITE_DATABASE_PATH = os.getenv("DB_PATH")

if not os.path.exists(SQLITE_DATABASE_PATH):
    print(f"Error: SQLite file not found at {SQLITE_DATABASE_PATH}")
    sys.exit(1)
    
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
if (ALPHA_VANTAGE_API_KEY is None):
    print("No Alpha Vantage API Key found")
    exit(1)

# Connect to your SQLite database file.
conn = sqlite3.connect(SQLITE_DATABASE_PATH)

# Get a cursor object
cur = conn.cursor()

# Focus on small/mid-cap tech stocks
MARKET_CAP_THRESHOLD = 2_000_000_000
cur.execute(f"SELECT symbol FROM tech_stocks WHERE market_cap >= {MARKET_CAP_THRESHOLD}")


# Fetch all results
results = cur.fetchall()

tickers = [item[0] for item in results]
print(f"Found {len(tickers)} tech stocks with market cap >= {MARKET_CAP_THRESHOLD}")

qqq_ticker = "QQQ"
qqq = yf.Ticker(qqq_ticker)
qqq_pe_ratio = qqq.info.get("trailingPE")

def fetch_stock_data(tickers, qqq_pe_ratio):
    data = {}
    FORWARD_WEIGHT = .4 #less because the projection might be inaccurate
    TRAILING_WEIGHT = .6
    for ticker in tickers:
        try:
            print(f"\rProcessing {ticker}", end="")
            stock = yf.Ticker(ticker)
            earnings_growth = (stock.info.get("earningsGrowth", None) or 0.0)
            # dividend_yield = stock.info.get("dividendYield", None) or 0.0
            current_eps = stock.info.get("trailingEps", 0.0)
            projected_eps = stock.info.get("forwardEps", 0.0)  # Forecasted EPS
            stock_pe_ratio_forward = stock.info.get("forwardPE", 0.0)
            beta = stock.info.get("beta", 1.0)
            curr_price = stock.info.get("currentPrice", 0.0)
            if None in (current_eps, projected_eps, qqq_pe_ratio, curr_price):
                continue
                # raise ValueError(ticker + " ~ " +  "curr_eps: " + str(current_eps) + " | " + "projected_eps: " + str(projected_eps) + " | " + "stock_pe_trailing: " + str(stock_pe_ratio_trailing) + " | " + "stock_pe_forward: " + str(stock_pe_ratio_forward) + " | " + "curr_price: " + str(curr_price))    
            
            # Calculate adjusted growth and valuation metrics
            adjusted_growth = earnings_growth / (1 + beta)  # Risk-adjusted growth
            
            # combined_stock_pe = (stock_pe_ratio_trailing * TRAILING_WEIGHT) + (stock_pe_ratio_forward * FORWARD_WEIGHT)
            if current_eps and projected_eps and curr_price and earnings_growth:
                # growth_rate = ((projected_eps - current_eps) / current_eps)
                fair_value = projected_eps * (1 + earnings_growth) * qqq_pe_ratio
                valuation_gap = ((curr_price - fair_value) / fair_value) * 100
                stock_value = (current_eps + projected_eps) * (qqq_pe_ratio * (1 + adjusted_growth))
                # pl_eval = (earnings_growth + dividend_yield) / max(stock_pe_ratio_forward, 1)

            cur.execute("""
                UPDATE tech_stocks 
                SET 
                    current_eps = ?, 
                    projected_eps = ?, 
                    stock_pe_ratio_forward = ?, 
                    earnings_growth = ?, 
                    beta = ?, 
                    current_price = ?, 
                    intrinsic_value = ?, 
                    fair_value = ?, 
                    valuation_gap = ?, 
                    valuation = ?
                WHERE symbol = ?
            """, (
                current_eps,
                projected_eps,
                stock_pe_ratio_forward,
                earnings_growth,
                beta,
                curr_price,
                stock_value,
                fair_value,
                valuation_gap,
                "overvalued" if valuation_gap > 0 else "undervalued",
                ticker
            ))
            
            conn.commit()
            
        except ValueError as e:
            print(f"Error {e}")
            continue
    return data


fetch_stock_data(tickers, qqq_pe_ratio)

# Close the connection
conn.close()

import os
from dotenv import load_dotenv
import yfinance as yf
import sys
import sqlite3
import json
import pandas as pd
from scipy.stats import zscore

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

#Focus on small/mid-cap tech stocks
MARKET_CAP_THRESHOLD = 2_000_000_000
cur.execute(f"SELECT symbol FROM tech_stocks WHERE market_cap >= {MARKET_CAP_THRESHOLD}")

# Fetch all results
results = cur.fetchall()

tickers = [item[0] for item in results]
# print(tickers)

qqq_ticker = "QQQ"
qqq = yf.Ticker(qqq_ticker)
qqq_pe_ratio = qqq.info.get("trailingPE")

# Define risk-free rate (e.g., U.S. 10-year Treasury bond yield, assumed as 3%)
risk_free_rate = .03

# Define expected market return (e.g., S&P 500 average return, assumed as 8%)
market_return = 0.08

def fetch_stock_data(tickers, risk_free_rate, market_return):
    data = {}
    FORWARD_WEIGHT = .4 #less because the projection might be inaccurate
    TRAILING_WEIGHT = .6
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            earnings_growth = (stock.info.get("earningsGrowth", None) or 0.0)
            dividend_yield = stock.info.get("dividendYield", None) or 0.0
            current_eps = stock.info.get("trailingEps", 0.0)
            projected_eps = stock.info.get("forwardEps", 0.0)  # Forecasted EPS
            stock_pe_ratio_forward = stock.info.get("forwardPE", 0.0)
            stock_pe_ratio_trailing = stock.info.get("trailingPE", 0.0)
            beta = stock.info.get("beta", 1.0)
            curr_price = stock.info.get("currentPrice", 0.0)
            
            # combined_stock_pe = (stock_pe_ratio_trailing * TRAILING_WEIGHT) + (stock_pe_ratio_forward * FORWARD_WEIGHT)
            if projected_eps and stock_pe_ratio_forward and curr_price and earnings_growth:
                discount_rate = risk_free_rate + (beta * (market_return - risk_free_rate))
                intrinsic_value = projected_eps * stock_pe_ratio_forward * (1 + earnings_growth) * (1 - discount_rate)
                fair_value = projected_eps * (1 + earnings_growth) * stock_pe_ratio_forward
                valuation_gap = ((curr_price - intrinsic_value) / intrinsic_value) * 100
            
            data[ticker] = {
                'current_eps': current_eps,
                'projected_eps': projected_eps,
                'stock_pe_ratio_forward': stock_pe_ratio_forward,
                'stock_pe_ratio_trailing': stock_pe_ratio_trailing,
                'earnings_growth': earnings_growth,
                'dividend_yield': dividend_yield,
                'beta': beta,
                'current_price': curr_price,
                'intrinsic_value': intrinsic_value,
                'fair_value': fair_value,
                'valuation_gap': valuation_gap,
                'valuation': "overvalued" if valuation_gap > 0 else "undervalued",
            }
            
        except ValueError as e:
            print(f"Error {e}")
            continue
    return data

# stock_data = fetch_stock_data(tickers, risk_free_rate, market_return)

# Save the results to a JSON file
# with open("stock_data.json", "w") as json_file:
#     json.dump(stock_data, json_file, indent=4)
    
print("Data saved to stock_data.json")

# Load JSON data
with open('stock_data.json', 'r') as file:
    json_data = json.load(file)
    
# Convert to DataFrame
data = pd.DataFrame.from_dict(json_data, orient="index")

# Display the DataFrame

# 1. Remove rows with negative or zero EPS values
data = data[(data['projected_eps'] > 0)]

# 2. Verify PE ratios
date = data[(data['stock_pe_ratio_forward']) > 0]

# 3. Verify Earnings Growth
date = data[(data['earnings_growth']) >= 10]

# 4. Use Z-Score for outlier detection 
data['intrinsic_ratio'] = data['intrinsic_value'] / data['current_price']
data['z_score_intrinsic'] = zscore(data['intrinsic_ratio'])
data = data[(abs(data['z_score_intrinsic']) < 2)]

# 5. Verify Intrinsic Value Ratiox
data = data[(data['intrinsic_ratio'] < 3)]
data = data.drop(columns=["intrinsic_ratio", "z_score_intrinsic"])

# 6. Drop Missing or 0 values
data = data.dropna(subset=["current_price", "intrinsic_value", "fair_value"])
data = data[(data['current_price'] > 0) & 
            (data['intrinsic_value'] > 0) & 
            (data['fair_value'] > 0)]

#update table
new_columns = [
    ("current_eps", "REAL"),
    ("projected_eps", "REAL"),
    ("stock_pe_ratio_forward", "REAL"),
    ("stock_pe_ratio_trailing", "REAL"),
    ("earnings_growth", "REAL"),
    ("dividend_yield", "REAL"),
    ("beta", "REAL"),
    ("current_price", "REAL"),
    ("intrinsic_value", "REAL"),
    ("fair_value", "REAL"),
    ("valuation_gap", "REAL"),
    ("valuation", "TEXT")
]

for column, col_type in new_columns:
    try:
        cur.execute(f"ALTER TABLE tech_stocks ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        # Column already exists
        pass

# Step 2: Update rows with JSON data
for index, row in data.iterrows():
    # Prepare the update query
    update_query = f"""
    UPDATE tech_stocks
    SET {', '.join([f"{key} = ?" for key in data.columns])}
    WHERE symbol = ?
    """
    update_values = tuple(row.values) + (index,)
    cur.execute(update_query, update_values)

# Step 3: Remove rows not in the JSON file (optional)
symbols = tuple(data.index)
delete_query = ("""
DELETE FROM tech_stocks
WHERE symbol NOT IN ({})
""".format(','.join('?' * len(symbols))))
cur.execute(delete_query, symbols)

# # Commit changes
conn.commit()

# Close the connection
conn.close()

# Notes

# Economic Indicator
# Analytics API
# Fundamentals API
# Technical Indicator API later 

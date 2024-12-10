import os
from dotenv import load_dotenv
import yfinance as yf
# import yahoo_fin.stock_info as si
# from yahoo_fin.stock_info import get_analysts_info, get_data, get_quote_data
import sys
import sqlite3
import requests
import json

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

# print(len(si.tickers_nasdaq()))
# q = get_quote_data("AAPL")
# print(q)

# Fetch all results
results = cur.fetchall()

tickers = [item[0] for item in results]
# print(tickers)

#splitting data for api batch requests
# def batch_list(data, size):
#     return [data[i:i + size] for i in range(0, len(data), size)]

# batches = batch_list(tickers, 100)

# Finnhub API for financial data
# RAW_DATA_FILE = "stock_formula_info.json"
# API_KEY_FH = "ctbdl3pr01qgsps90jugctbdl3pr01qgsps90jv0"
# financial_data = {}
# data = []
# for ticker in tickers:
#     url_fh = f"https://finnhub.io/api/v1/stock/metric"
#     params_fh = {
#         "symbol": ticker,
#         "metric": "all",  # Get all available financial metrics
#         "token": API_KEY_FH
#     }
#     response_fh = requests.get(url_fh, params=params_fh)
#     data_fh = response_fh.json()

#     if "metric" in data_fh:
#         financial_data[ticker] = {
#             "eps": data_fh["metric"].get("epsTrailingTwelveMonths"),
#             "pe_ratio": data_fh["metric"].get("peRatio"),
#             "forward_eps": data_fh["metric"].get("epsForward"),
#             "name": ticker
#         }
#     else:
#         print(f"No financial data found for {ticker}")
        
# # Save the financial data to a JSON file
# with open(RAW_DATA_FILE, "w") as file:
#     json.dump(financial_data, file, indent=4)

# print(f"Raw Finnhub financial data saved to {RAW_DATA_FILE}")

# RAW_DATA_FILE = "stock_quotes.json"
# data = []
# url_av = "https://www.alphavantage.co/query"
# for batch in batches:
#     joined_symbols = ",".join(batch)
#     params_av = {
#     "function": "BATCH_STOCK_QUOTES",
#     "symbols": joined_symbols,
#     "apikey": ALPHA_VANTAGE_API_KEY
#     }
#     response_av = requests.get(url_av, params=params_av)
#     print(response_av.json())
#     if response_av.status_code == 200:  # Ensure the request succeeded
#         response_data = response_av.json().get("Stock Quotes", [])
#         data.extend(response_data)
#     else:
#         print(f"Failed to fetch data for batch: {batch}. HTTP Status: {response_av.status_code}")

# # Save raw data to a file
# with open(RAW_DATA_FILE, "w") as file:
#     json.dump(data, file, indent=4)
# print(f"Raw batch stock data saved to {RAW_DATA_FILE}")


qqq_ticker = "QQQ"
qqq = yf.Ticker(qqq_ticker)
qqq_pe_ratio = qqq.info.get("trailingPE")

def fetch_stock_data(tickers, qqq_pe_ratio):
    data = {}
    FORWARD_WEIGHT = .4 #less because the projection might be inaccurate
    TRAILING_WEIGHT = .6
    for ticker in tickers:
        try:
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
            
            data[ticker] = {
                'current_eps': current_eps,
                'projected_eps': projected_eps,
                'stock_pe_ratio_forward': stock_pe_ratio_forward,
                'earnings_growth': earnings_growth,
                # 'dividend_yield': dividend_yield,
                'beta': beta,
                'current_price': curr_price,
                'intrinsic_value': stock_value,
                # 'peter_lynch_evaluation': pl_eval,
                'fair_value': fair_value,
                'valuation_gap': valuation_gap,
                'valuation': "overvalued" if valuation_gap > 0 else "undervalued",
            }
            
        except ValueError as e:
            print(f"Error {e}")
            continue
    return data

stock_data = fetch_stock_data(tickers, qqq_pe_ratio)

# Save the results to a JSON file
with open("stock_data.json", "w") as json_file:
    json.dump(stock_data, json_file, indent=4)
    
print("Data saved to stock_data.json")


# Close the connection
conn.close()


# # API_KEY = "6QC29VG3YZV1ERYA"


# print(f"Loaded Alpha Vantage API Key: {ALPHA_VANTAGE_API_KEY}")



# Notes

# Economic Indicator
# Analytics API
# Fundamentals API
# Technical Indicator API later 
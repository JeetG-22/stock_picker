import os
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
if (ALPHA_VANTAGE_API_KEY is None):
    print("No Alpha Vantage API Key found")
    exit(1)

print(f"Loaded Alpha Vantage API Key: {ALPHA_VANTAGE_API_KEY}")

# Economic Indicator

# Analytics API

# Fundamentals API

# Technical Indicator API later 
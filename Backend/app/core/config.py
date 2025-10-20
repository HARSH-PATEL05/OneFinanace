from dotenv import load_dotenv
import os

load_dotenv()

# General
BASE_URL = "http://127.0.0.1:8000"

# Zerodha
ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY")
ZERODHA_API_SECRET = os.getenv("ZERODHA_API_SECRET")
ZERODHA_REDIRECT = f"{BASE_URL}/zerodha/callback"

# Angel One
ANGEL_API_BASE = os.getenv("ANGEL_API_BASE")
ANGEL_API_KEY = os.getenv("ANGEL_API_KEY")


# Upstox
UPSTOX_CLIENT_ID = os.getenv("UPSTOX_CLIENT_ID")
UPSTOX_CLIENT_SECRET = os.getenv("UPSTOX_CLIENT_SECRET")
UPSTOX_REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI")
UPSTOX_API_BASE = os.getenv("UPSTOX_API_BASE")

# Groww
GROWW_API_KEY = os.getenv("GROWW_API_KEY")
GROWW_API_SECRET = os.getenv("GROWW_API_SECRET")
GROWW_API_BASE = os.getenv("GROWW_API_BASE")
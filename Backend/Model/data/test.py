import os
import yfinance as yf
from datetime import datetime, timedelta
from nsepython import nsefetch
import concurrent.futures
from threading import Lock

# =====================================================
# CONFIG
# =====================================================
SAVE_DIR = "data/core_market_10yr"
os.makedirs(SAVE_DIR, exist_ok=True)

print_lock = Lock()

# 10-year date range
END = datetime.today()
START = END - timedelta(days=365 * 10)


def safe_print(msg: str):
    """Thread-safe print."""
    with print_lock:
        print(msg)


# =====================================================
# INDEX TICKER MAPPING FOR YFINANCE
# =====================================================
INDEX_MAP = {
    "NIFTY 50": "^NSEI",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY FINANCIAL SERVICES": "^NSEFIN",
    "NIFTY NEXT 50": "^NSMIDCP",
    "NIFTY IT": "^CNXIT",
}

CORE_INDICES = list(INDEX_MAP.keys())


# =====================================================
# FETCH STOCKS BELONGING TO A SPECIFIC NSE INDEX
# =====================================================
def get_index_stocks(index_name: str):
    url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_name}"

    try:
        data = nsefetch(url)
        return [item["symbol"] for item in data["data"]]
    except:
        safe_print(f"❌ Could not fetch stocks of: {index_name}")
        return []


# =====================================================
# GENERIC FUNCTION TO DOWNLOAD ANY SYMBOL (INDEX OR STOCK)
# =====================================================
def download_symbol(symbol: str, yf_symbol: str):
    try:
        safe_print(f"⬇ Downloading {symbol} ({yf_symbol}) ...")

        df = yf.download(
            yf_symbol,
            start=START,
            end=END,
            interval="1d",
            auto_adjust=False,
            progress=False,
            timeout=20
        )

        if df is None or df.empty:
            safe_print(f"❌ No data for {symbol} ({yf_symbol})")
            return symbol, False

        df = df[["Open", "High", "Low", "Close", "Volume"]]

        file_name = symbol.replace(" ", "") + ".csv"
        file_path = os.path.join(SAVE_DIR, file_name)
        df.to_csv(file_path)

        safe_print(f"✔ Saved {file_name} ({len(df)} rows)")
        return symbol, True

    except Exception as e:
        safe_print(f"❌ Failed {symbol} ({yf_symbol}) — {e}")
        return symbol, False


# =====================================================
# MAIN DOWNLOADER
# =====================================================
def download_indices_and_stocks(max_workers=20):
    safe_print("\n📌 Fetching core NSE market components...")

    # ---------------------------------------------
    # 1) Download index CSVs
    # ---------------------------------------------
    safe_print("\n📍 Downloading 5 major indices...")
    index_results = {}

    for index_name, yf_symbol in INDEX_MAP.items():
        index_results[index_name] = yf_symbol

    # ---------------------------------------------
    # 2) Fetch stocks inside these indices
    # ---------------------------------------------
    safe_print("\n📍 Fetching all stocks inside these indices...\n")
    all_stocks = set()

    for index_name in CORE_INDICES:
        stocks = get_index_stocks(index_name)
        safe_print(f"{index_name}: {len(stocks)} stocks")
        all_stocks.update(stocks)

    all_stocks = list(all_stocks)

    safe_print(f"\n📊 Total unique stocks to download: {len(all_stocks)}\n")

    # ---------------------------------------------
    # 3) Multithreaded download for all symbols
    # ---------------------------------------------
    success = []
    failed = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:

        # Download indices + stocks
        tasks = {}

        # Add indices first
        for idx_name, yf_symbol in index_results.items():
            tasks[executor.submit(download_symbol, idx_name, yf_symbol)] = idx_name

        # Add stock downloads
        for stock in all_stocks:
            yf_symbol = stock + ".NS"
            tasks[executor.submit(download_symbol, stock, yf_symbol)] = stock

        # Handle results
        for f in concurrent.futures.as_completed(tasks):
            name = tasks[f]
            try:
                _, ok = f.result()
                if ok:
                    success.append(name)
                else:
                    failed.append(name)
            except Exception as e:
                safe_print(f"❌ Error on {name}: {e}")
                failed.append(name)

    # ---------------------------------------------
    # SUMMARY
    # ---------------------------------------------
    safe_print("\n==============================")
    safe_print("📊 FINAL DOWNLOAD SUMMARY")
    safe_print("==============================")
    safe_print(f"✔ Successful: {len(success)}")
    safe_print(f"❌ Failed: {len(failed)}")

    if failed:
        safe_print("\n❌ Failed downloads:")
        for f in failed:
            safe_print(" - " + f)

    safe_print("\n🎉 DONE! All core indices + all their stocks saved.")


# =====================================================
# RUN SCRIPT
# =====================================================
if __name__ == "__main__":
    download_indices_and_stocks(max_workers=20)

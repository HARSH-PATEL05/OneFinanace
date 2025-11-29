import yfinance as yf
from nsepython import nse_eq


# --------------------------------------------------------
# SAFETY HELPERS
# --------------------------------------------------------
def safe_dict(val):
    """Ensure value is a dictionary."""
    return val if isinstance(val, dict) else {}


def safe_get(d, key):
    """Safe .get() even if d is not a dict."""
    return d.get(key) if isinstance(d, dict) else None


# --------------------------------------------------------
# 1) CLEAN NSE DATA (nse_eq)
# --------------------------------------------------------
def get_nse_clean(symbol):
    sym = symbol.replace(".NS", "").upper()

    try:
        raw = nse_eq(sym)
    except Exception as e:
        return {"error": f"NSE error: {str(e)}"}

    raw = safe_dict(raw)

    info = safe_dict(raw.get("info"))
    price = safe_dict(raw.get("priceInfo"))
    industry = safe_dict(raw.get("industryInfo"))
    metadata = safe_dict(raw.get("metadata"))

    intra = safe_dict(price.get("intraDayHighLow"))
    week = safe_dict(price.get("weekHighLow"))

    return {
        "company": {
            "name": info.get("companyName"),
            "symbol": info.get("symbol"),
            "isin": info.get("isin"),
            "listingDate": info.get("listingDate"),
            "industry": info.get("industry"),
            "basicIndustry": industry.get("basicIndustry"),
            "sector": industry.get("sector"),
        },

        "market_data": {
            "lastPrice": price.get("lastPrice"),
            "previousClose": price.get("previousClose"),
            "open": price.get("open"),
            "vwap": price.get("vwap"),
            "dayHigh": intra.get("max"),
            "dayLow": intra.get("min"),

            # NSE volume (may be None)
            "volume": price.get("totalTradedVolume"),
        },

        "52_week": {
            "high": week.get("max"),
            "highDate": week.get("maxDate"),
            "low": week.get("min"),
            "lowDate": week.get("minDate"),
        },

        "price_band": {
            "lowerCircuit": price.get("lowerCP"),
            "upperCircuit": price.get("upperCP")
        },

        "industry_pe": {
            "sectorPE": metadata.get("pdSectorPe"),
            "symbolPE": metadata.get("pdSymbolPe"),
        }
    }


# --------------------------------------------------------
# 2) CLEAN YFINANCE DATA (ticker.info)
# --------------------------------------------------------
def get_yfinance_clean(symbol):
    ticker = yf.Ticker(symbol)

    try:
        info = ticker.info
    except:
        info = {}

    info = safe_dict(info)

    return {
        "market_data": {
            "volume": info.get("volume"),
        },

        "valuation": {
            "marketCap": info.get("marketCap"),
            "currentPrice": info.get("currentPrice"),
            "bookValue": info.get("bookValue"),
            "priceToBook": info.get("priceToBook"),
            "forwardPE": info.get("forwardPE"),
            "trailingPE": info.get("trailingPE"),
            
        },

        "profitability": {
            "grossMargins": info.get("grossMargins"),
            "operatingMargins": info.get("operatingMargins"),
            "profitMargins": info.get("profitMargins"),
            "returnOnAssets": info.get("returnOnAssets"),
            "returnOnEquity": info.get("returnOnEquity"),
        },

        "growth": {
            "revenueGrowth": info.get("revenueGrowth"),
            "earningsGrowth": info.get("earningsGrowth"),
        },

        "financial_health": {
            "debtToEquity": info.get("debtToEquity"),
            "currentRatio": info.get("currentRatio"),
            "quickRatio": info.get("quickRatio"),
            "totalDebt": info.get("totalDebt"),
            "totalCash": info.get("totalCash"),
        },

        "dividends": {
            "dividendYield": info.get("dividendYield"),
            "dividendRate": info.get("dividendRate"),
            "payoutRatio": info.get("payoutRatio"),
        }
    }


# --------------------------------------------------------
# 3) FINAL MERGED FUNDAMENTALS
# --------------------------------------------------------
def get_stock_fundamentals(symbol):
    nse = safe_dict(get_nse_clean(symbol))
    yfin = safe_dict(get_yfinance_clean(symbol))

    nse_market = safe_dict(nse.get("market_data"))
    yfin_market = safe_dict(yfin.get("market_data"))

    # Final merged market_data
    final_market_data = dict(nse_market)
    final_market_data["volume"] = (
        yfin_market.get("volume") or
        nse_market.get("volume") or
        None
    )

    return {
        "symbol": symbol,

        "company": safe_dict(nse.get("company")),
        "market_data": final_market_data,
        "week": safe_dict(nse.get("52_week")),
        "price_band": safe_dict(nse.get("price_band")),
        "industry_pe": safe_dict(nse.get("industry_pe")),

        "valuation": safe_dict(yfin.get("valuation")),
        "profitability": safe_dict(yfin.get("profitability")),
        "growth": safe_dict(yfin.get("growth")),
        "financial_health": safe_dict(yfin.get("financial_health")),
        "dividends": safe_dict(yfin.get("dividends")),
    }


# --------------------------------------------------------
# TEST
# --------------------------------------------------------
if __name__ == "__main__":
    print(get_stock_fundamentals("TCS.NS"))

import os
import json
import time
import queue
import threading
from datetime import datetime, time as dt_time


from typing import Dict, Set, Optional, List, Tuple, Callable
from app.core.market_utils import is_market_open
# ---------- Updated Redis API (safe wrappers) ----------
from redis_client import (
    
    redis_safe_set,
    redis_safe_publish,
    redis_safe_json_get,
    redis_safe_json_set,
)

import requests
import pandas as pd
from io import StringIO

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import update

from app.db import SessionLocal
from app.models import Holding, MutualFund
from app.core.utils import load_credentials
from app.core.config import ANGEL_API_KEY

from SmartApi.smartWebSocketV2 import SmartWebSocketV2


# ============================ CONFIG ============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOKEN_FILE = os.path.join(BASE_DIR, "tokens", "angelone_token.json")
INSTRUMENTS_CACHE = os.path.join(BASE_DIR, "tokens", "instruments_cache.json")

BATCH_INTERVAL = 5  # seconds
INSTRUMENTS_TTL = 12 * 60 * 60
AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"
ANGEL_INSTRUMENTS_URL = (
    "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
)
FEED_TOKEN_REFRESH_INTERVAL = 60 * 60
SUBSCRIBE_CHUNK_SIZE = 1000
# ================================================================


# -------------------------------------------------
# GLOBALS
# -------------------------------------------------
ltp_queue = queue.Queue()
symbol_token_map: Dict[str, str] = {}
token_to_symbol_map: Dict[str, str] = {}
holding_tokens_set: Set[str] = set()
ltp_listeners: List[Callable[[str, float], None]] = []

ltp_cache: Dict[str, float] = {}
instruments_memory_cache: List[dict] = []
_state_lock = threading.RLock()
_instruments_meta: Dict[str, float | int] = {"ts": 0.0, "count": 0}
ws_running = False

# 🚦 NEW: flag to control when WS/LTP should be active (set by scheduler)
market_active = False


# -------------------------- Logging -------------------------------
def log(msg: str, level="INFO"):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {level}: {msg}")


# ------------------- Listener Registration -----------------------
def register_ltp_listener(cb: Callable[[str, float], None]):
    ltp_listeners.append(cb)


def notify_ltp(symbol: str, ltp: float):
    for cb in ltp_listeners:
        try:
            cb(symbol, ltp)
        except Exception:
            pass


# ------------------- Token Handling ------------------------------
def load_tokens_from_file() -> Tuple[Optional[str], Optional[str]]:
    try:
        if not os.path.exists(TOKEN_FILE):
            return None, None

        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        jwt_raw = data.get("jwtToken", "")
        jwt = jwt_raw.replace("Bearer ", "") if isinstance(jwt_raw, str) else ""

        feed = data.get("feedToken", "")

        if not jwt or not feed:
            return None, None

        return jwt, feed

    except Exception as e:
        log(f"load_tokens_from_file failed: {e}", "WARNING")
        return None, None


# ------------------- Instruments Caching --------------------------
def _cache_valid() -> bool:
    ts = _instruments_meta.get("ts", 0)
    if not os.path.exists(INSTRUMENTS_CACHE):
        return False
    return (time.time() - ts) < INSTRUMENTS_TTL


def load_cache() -> Optional[List[dict]]:
    try:
        with open(INSTRUMENTS_CACHE, "r", encoding="utf-8") as f:
            data = json.load(f)

        _instruments_meta["ts"] = float(os.path.getmtime(INSTRUMENTS_CACHE))
        _instruments_meta["count"] = len(data) if isinstance(data, list) else 0

        return data
    except Exception:
        return None


def save_cache(inst: List[dict]):
    try:
        os.makedirs(os.path.dirname(INSTRUMENTS_CACHE), exist_ok=True)
        with open(INSTRUMENTS_CACHE, "w", encoding="utf-8") as f:
            json.dump(inst, f)

        _instruments_meta["ts"] = time.time()
        _instruments_meta["count"] = len(inst)

    except Exception as e:
        log(f"save_cache failed: {e}", "WARNING")


def fetch_instruments(force: bool = False) -> Optional[List[dict]]:
    global instruments_memory_cache

    # 1) Redis (safe)
    if not force:
        cached = redis_safe_json_get("instruments_cache")
        if isinstance(cached, list):
            instruments_memory_cache = cached
            log(f"Loaded instruments from Redis ({len(cached)})")
            return cached

    # 2) File
    if not force and _cache_valid():
        file_cached = load_cache()
        if isinstance(file_cached, list):
            instruments_memory_cache = file_cached
            log(f"Loaded instruments from file cache ({len(file_cached)})")
            redis_safe_json_set("instruments_cache", file_cached)
            return file_cached

    # 3) Remote fetch
    try:
        resp = requests.get(ANGEL_INSTRUMENTS_URL, timeout=12)
        resp.raise_for_status()

        instruments = resp.json()
        if not isinstance(instruments, list):
            raise ValueError("Invalid instrument response")

        save_cache(instruments)
        redis_safe_json_set("instruments_cache", instruments)
        instruments_memory_cache = instruments

        log(f"Fetched instruments remote ({len(instruments)})")
        return instruments

    except Exception as e:
        log(f"Remote fetch failed: {e}", "WARNING")

    # 4) RAM fallback
    if instruments_memory_cache:
        log("Using memory fallback instruments cache", "WARNING")
        return instruments_memory_cache

    log("NO instruments available anywhere ❌", "ERROR")
    return None


# ------------------- Build Symbol Map ------------------------------
def build_symbol_token_map(force=False):
    global symbol_token_map, token_to_symbol_map, holding_tokens_set, _instruments_meta

    with _state_lock:
        old_size = len(symbol_token_map)

        # ----------------------------------------
        # 1) LOAD FROM REDIS (fastest)
        # ----------------------------------------
        if not force:
            cached = redis_safe_json_get("symbol_token_map")
            if isinstance(cached, dict) and cached:
                symbol_token_map = cached
                token_to_symbol_map = {v: k for k, v in cached.items()}
                holding_tokens_set = set(token_to_symbol_map.keys())

                # mark timestamp so we DO NOT rebuild again soon
                _instruments_meta["ts"] = time.time()

                if len(symbol_token_map) != old_size:
                    log(f"Loaded symbol map from Redis ({len(symbol_token_map)})")
                return

        # ----------------------------------------
        # 2) DB HOLDINGS
        # ----------------------------------------
        session = SessionLocal()
        try:
            rows = session.query(Holding).all()
            symbols = {(r.symbol or "").strip().upper() for r in rows if r.symbol}
        except Exception as e:
            log(f"DB holdings load failed: {e}", "ERROR")
            return
        finally:
            session.close()

        if not symbols:
            log("No holdings found → mapping skipped")
            return

        # ----------------------------------------
        # 3) INSTRUMENTS (Redis/File/Remote)
        # ----------------------------------------
        inst = fetch_instruments(force=force)
        if not inst:
            log("No instruments available to map", "ERROR")
            return

        # fresh maps
        symbol_token_map = {}
        token_to_symbol_map = {}
        holding_tokens_set = set()

        # ----------------------------------------
        # 4) BUILD MAP
        # ----------------------------------------
        for row in inst:
            try:
                token = str(row.get("token", "")).strip()
                symbol_json = str(row.get("symbol", "")).strip().upper()
                name_json = str(row.get("name", "")).strip().upper()
                exch = row.get("exch_seg", "").upper()

                if exch != "NSE":
                    continue

                is_equity = symbol_json.endswith("-EQ")

                for sym in symbols:
                    if is_equity and symbol_json == sym + "-EQ":
                        symbol_token_map[sym] = token
                        token_to_symbol_map[token] = sym
                        holding_tokens_set.add(token)
                        break

                    if symbol_json == sym or name_json == sym:
                        symbol_token_map[sym] = token
                        token_to_symbol_map[token] = sym
                        holding_tokens_set.add(token)
                        break

            except Exception:
                continue

        log(f"Mapped {len(holding_tokens_set)} tokens")

        # ----------------------------------------
        # 5) SAVE TO REDIS + UPDATE TIMESTAMP
        # ----------------------------------------
        redis_safe_json_set("symbol_token_map", symbol_token_map)

        # **IMPORTANT:** Prevent constant rebuilding
        _instruments_meta["ts"] = time.time()


# ------------------ Safe float conversion -------------------------
def safe_float(x: object) -> float:
    try:
        return float(str(x))
    except Exception:
        return 0.0


# ------------------- LTP Batch Update -----------------------------
def update_holdings_batch():
    items: Dict[str, float] = {}

    # Empty queue
    while not ltp_queue.empty():
        try:
            token, raw = ltp_queue.get_nowait()
            price_val = safe_float(raw) / 100.0
            items[str(token)] = price_val
        except Exception:
            break

    if not items:
        return

    session = SessionLocal()
    updated = 0

    try:
        for tok, price in items.items():
            symbol = token_to_symbol_map.get(tok)
            if not symbol:
                continue

            # ❌ Do NOT overwrite Redis here.
            # Redis is updated in real-time from WebSocket.
            # This batch worker is only for DB commits every BATCH_INTERVAL.
            stmt = (
                update(Holding)
                .where(Holding.symbol == symbol)
                .values(Ltp=price, updated_at=datetime.utcnow())
            )
            session.execute(stmt)

            updated += 1
            notify_ltp(symbol, price)

        session.commit()

        log(f"Batch LTP commit complete ({updated}/{len(items)})")

    except Exception as e:
        session.rollback()
        log(f"update_holdings_batch ERROR: {e}", "ERROR")

    finally:
        session.close()


# ------------------- MF NAV Update ------------------------------
def update_mf_ltp():
    """
    Updates Mutual Fund NAVs using AMFI ISIN mapping.
    Matches NAV rows by ISIN ('ISIN Div Payout/ ISIN Growth')
    instead of scheme name — ensures exact & correct match.
    """

    MAX_RETRY = 5
    base_wait = 5

    attempt = 0
    while attempt < MAX_RETRY:
        session = SessionLocal()
        try:
            log("Fetching AMFI NAVs (ISIN based)…")

            resp = requests.get(AMFI_URL, timeout=25)
            resp.raise_for_status()

            df = pd.read_csv(StringIO(resp.text), sep=";")

            # Build ISIN → NAV mapping
            nav_map = {}
            for _, row in df.iterrows():
                isin = str(row.get("ISIN Div Payout/ ISIN Growth", "")).strip()
                raw_nav = row.get("Net Asset Value")

                if not isin or raw_nav is None:
                    continue

                try:
                    nav_map[isin] = float(raw_nav)
                except Exception:
                    continue

            if not nav_map:
                log("⚠ NAV map empty! Something went wrong.", "WARNING")
                return

            updated = 0
            unchanged = 0

            # DB update using ISIN match
            for mf in session.query(MutualFund).all():
                isin = (mf.symbol or "").strip()

                if not isin:
                    continue

                nav = nav_map.get(isin)
                if nav is None:
                    continue

                # Update only if changed
                if mf.Ltp != nav:
                    mf.prev_close = mf.Ltp
                    mf.Ltp = nav
                    mf.updated_at = datetime.utcnow()
                    updated += 1
                else:
                    unchanged += 1

            session.commit()
            log(f"📈 MF NAV Update complete: Updated={updated}, Unchanged={unchanged}, Total={updated + unchanged}")

            return

        except Exception as e:
            session.rollback()
            attempt += 1
            log(f"update_mf_ltp attempt {attempt} failed: {e}", "WARNING")
            time.sleep(base_wait * attempt)

        finally:
            session.close()


# ----------------- Daily prev LTP update --------------------------
def daily_prev_ltp_update():
    session = SessionLocal()
    try:
        session.execute(
            update(Holding).values(
                prev_ltp=Holding.Ltp, updated_at=datetime.utcnow()
            )
        )
        session.commit()
        log("Copied LTP → prev_ltp for all holdings")

    except Exception as e:
        session.rollback()
        log(f"daily_prev_ltp_update ERROR: {e}", "ERROR")

    finally:
        session.close()


# ------------------- SmartAPI WebSocket Callback ------------------
def on_data_callback(parsed: dict):
    if not isinstance(parsed, dict):
        return

    token = parsed.get("token")
    ltp_raw = parsed.get("last_traded_price") or parsed.get("ltp")

    if token is None or ltp_raw is None:
        return

    token = str(token)
    if token not in holding_tokens_set:
        return

    symbol = token_to_symbol_map.get(token)
    if not symbol:
        return

    try:
        price = float(ltp_raw) / 100
    except Exception:
        return

    # ✅ Real-time: update Redis immediately
    redis_safe_set(f"ltp:{symbol}", str(price))
    redis_safe_publish("ltp_updates", {"symbol": symbol, "ltp": price})

    # ✅ Also keep in-memory cache fresh for fallback
    ltp_cache[symbol] = price

    try:
        # DB batch worker will commit this every BATCH_INTERVAL seconds
        ltp_queue.put((token, ltp_raw))
    except Exception:
        pass


# ------------------- WebSocket Worker ----------------------------
class WebSocketWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)

        creds = load_credentials(broker_name="angelone") or {}
        self.client_code = creds.get("client_code") or creds.get("clientId")

        self.ws = None
        self.current_tokens: Tuple[Optional[str], Optional[str]] = (None, None)

        self.subscribed: Set[str] = set()
        self.connected_event = threading.Event()
        self.feed_last_refresh = 0

    def _on_open(self):
        self.connected_event.set()
        log("WS connected")

    def _on_close(self):
        self.connected_event.clear()
        log("WS closed")

    def _on_error(self, *args, **kwargs):
        log("WS error", "WARNING")

    def connect_ws(self, jwt: str, feed: str) -> Optional[SmartWebSocketV2]:
        try:
            client = SmartWebSocketV2(
                auth_token=jwt,
                api_key=ANGEL_API_KEY,
                client_code=self.client_code,
                feed_token=feed,
            )

            client.on_data = lambda wsapp, data: on_data_callback(data)
            client.on_open = lambda wsapp: self._on_open()
            client.on_close = lambda wsapp: self._on_close()
            client.on_error = lambda *a, **k: self._on_error()

            threading.Thread(target=client.connect, daemon=True).start()
            return client

        except Exception as e:
            log(f"connect_ws ERROR: {e}", "ERROR")
            return None

    def refresh_feed_token(self):
        now = time.time()
        if now - self.feed_last_refresh < FEED_TOKEN_REFRESH_INTERVAL:
            return

        jwt, feed = load_tokens_from_file()
        if not jwt or not feed:
            return

        self.feed_last_refresh = now
        log("Checked feed token freshness")

    def _subscribe_in_chunks(self, client: SmartWebSocketV2, tokens: List[str]):
        for i in range(0, len(tokens), SUBSCRIBE_CHUNK_SIZE):
            chunk = tokens[i : i + SUBSCRIBE_CHUNK_SIZE]
            payload = [{"exchangeType": 1, "tokens": chunk}]

            try:
                client.subscribe(
                    correlation_id="ltpupdate", mode=1, token_list=payload
                )
            except Exception:
                try:
                    client.subscribe("ltp", 1, payload)
                except Exception as e:
                    log(f"_subscribe_in_chunks fallback failed: {e}", "WARNING")

            time.sleep(0.05)

    def subscribe_missing(self):
        needed = list(holding_tokens_set - self.subscribed)
        if not needed or self.ws is None:
            return

        try:
            self._subscribe_in_chunks(self.ws, needed)
            self.subscribed.update(needed)
            log(f"Subscribed to {len(needed)} new tokens")
        except Exception as e:
            log(f"subscribe_missing failed: {e}", "WARNING")

    def run(self):
        log("WebSocketWorker starting")

        build_symbol_token_map(force=False)

        jwt, feed = load_tokens_from_file()
        if jwt and feed:
            self.current_tokens = (jwt, feed)

        while True:
            # 🔥 Only do anything if market window is active
            if not market_active:
                if self.ws:
                    try:
                        self.ws.close_connection()
                        log("WS closed because market_active=False")
                    except Exception:
                        pass
                    self.ws = None
                    self.subscribed.clear()
                    self.connected_event.clear()

                time.sleep(30)
                continue

            # 🔥 Inside active window, still respect actual market open/holiday
            if not is_market_open():
                if self.ws:
                    try:
                        self.ws.close_connection()
                        log("WS closed because market is not open (holiday/pre/post)")
                    except Exception:
                        pass
                    self.ws = None
                    self.subscribed.clear()
                    self.connected_event.clear()

                time.sleep(10)
                continue

            jwt, feed = load_tokens_from_file()
            if not jwt or not feed:
                log("Waiting for valid tokens…", "WARNING")
                time.sleep(10)
                continue

            # If socket not connected → reconnect
            if self.ws is None or not self.connected_event.is_set():
                try:
                    if self.ws:
                        try:
                            self.ws.close_connection()
                        except Exception:
                            pass

                        self.subscribed.clear()
                        self.connected_event.clear()

                    log("Connecting WebSocket...")
                    client = self.connect_ws(jwt, feed)

                    if client is None:
                        time.sleep(5)
                        continue

                    if not self.connected_event.wait(20):
                        log("WS connect wait timeout", "WARNING")
                        try:
                            client.close_connection()
                        except Exception:
                            pass
                        time.sleep(5)
                        continue

                    self.ws = client
                    self.current_tokens = (jwt, feed)
                    self.subscribed.clear()

                except Exception as e:
                    log(f"WS connect error: {e}", "ERROR")
                    time.sleep(5)
                    continue

            # Housekeeping
            if time.time() - _instruments_meta.get("ts", 0) > 3600:
                build_symbol_token_map(force=False)

            self.refresh_feed_token()

            if self.connected_event.is_set():
                self.subscribe_missing()

            time.sleep(1)


# ------------------- LTP Batch Worker ----------------------------
def start_ltp_batch_worker():
    def worker():
        while True:
            try:
                # 🔥 Only run batch when market window is active AND market is open
                if market_active and is_market_open():
                    log(f"{market_active}:{is_market_open()}")
                    update_holdings_batch()
            except Exception as e:
                log(f"LTP batch worker ERROR: {e}", "ERROR")
            time.sleep(BATCH_INTERVAL)

    threading.Thread(target=worker, daemon=True).start()
    log("LTP batch worker started")


# ---------------- Scheduler ----------------
def enable_market_mode():
    global market_active
    market_active = True
    log("🚀 Market session window ENABLED (WS + LTP batch allowed)")


def disable_market_mode():
    global market_active
    market_active = False
    log("🛑 Market session window DISABLED (WS + LTP batch paused)")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(enable_market_mode, "cron", hour=9, minute=10)
    scheduler.add_job(disable_market_mode, "cron", hour=15, minute=45)

    scheduler.add_job(build_symbol_token_map, "cron", hour=0, minute=10)
    scheduler.add_job(update_mf_ltp, "cron", hour=15, minute=0)
    scheduler.add_job(daily_prev_ltp_update, "cron", hour=23, minute=30)
    scheduler.add_job(lambda: fetch_instruments(force=True), "interval", hours=12)

    scheduler.start()
    log("Scheduler started")

    # 🚀 INITIAL STATE CHECK
    now = datetime.now().time()
    if now >= dt_time(9, 10) and now <= dt_time(15, 45):
        enable_market_mode()
    else:
        disable_market_mode()

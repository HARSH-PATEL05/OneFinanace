# app/main.py
import threading
import time
import json
from datetime import datetime
import traceback
from typing import List

from websocket_angelone.token_updater import TokenRefresher
from websocket_angelone.worker import (
    WebSocketWorker,
    start_scheduler,
    register_ltp_listener,
    update_holdings_batch,
)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.db import create_tables, SessionLocal

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from sqlalchemy import text

# Use runtime redis getter (resilient)
from redis_client import get_redis, redis_safe_json_get

# Routers
from app.routers import user_router
from app.routers.broker_routes import router as broker_router
from app.routers.portfolio_routes import router as portfolio_router
from app.routers.smsparser_data_route import router as smsparser_data_router
from app.routers.account_route import router as account_router
from app.routers.live_updater_routes import router as live_updater_routes
from app.routers.AI_Model_Analysis_route import router as AI_Model_Analysis_route

# Sync engine
from app.crud import process_all_unsynced_transactions

# -------------------------------------------------------
# FASTAPI SETUP
# -------------------------------------------------------
app = FastAPI(title="OneFinance", version="1.0.0", description="AI Financial Advisor")

# Routers
app.include_router(broker_router)
app.include_router(user_router.router)
app.include_router(portfolio_router)
app.include_router(smsparser_data_router)
app.include_router(account_router)
app.include_router(live_updater_routes)
app.include_router(AI_Model_Analysis_route)

# CORS (add more origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------
# BASIC ROUTES
# -------------------------------------------------------
@app.get("/")
def root():
    return {"message": "OneFinance running"}


@app.get("/db-status")
def db_status():
    s = SessionLocal()
    try:
        result = s.execute(text("SELECT current_database();")).fetchone()
        if result:
            return {"connected_database": result[0], "status": "OK"}
        return {"connected_database": None, "status": "No database returned"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        s.close()


# -------------------------------------------------------
# WEBSOCKET (Frontend LTP Updates)
# -------------------------------------------------------
connected_clients: List[WebSocket] = []
_connected_clients_lock = threading.RLock()


@app.websocket("/ws/stocks")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    with _connected_clients_lock:
        connected_clients.append(ws)
    try:
        # keep connection alive — we don't expect client messages
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        with _connected_clients_lock:
            try:
                connected_clients.remove(ws)
            except Exception:
                pass
    except Exception:
        # unexpected error — ensure removal
        with _connected_clients_lock:
            try:
                connected_clients.remove(ws)
            except Exception:
                pass


def push_ltp_update(symbol: str, ltp: float):
    """Send real-time LTP to all websocket clients."""
    message = {"symbol": symbol, "Ltp": ltp}

    import asyncio

    async def _send():
        remove = []
        with _connected_clients_lock:
            clients = list(connected_clients)
        for ws in clients:
            try:
                await ws.send_json(message)
            except Exception:
                remove.append(ws)

        if remove:
            with _connected_clients_lock:
                for ws in remove:
                    try:
                        connected_clients.remove(ws)
                    except Exception:
                        pass

    # run async send in separate thread so caller (worker) is not blocked
    threading.Thread(target=lambda: asyncio.run(_send()), daemon=True).start()


# Worker will call this to send updates
register_ltp_listener(push_ltp_update)


# -------------------------------------------------------
# REDIS PUB/SUB LISTENER → NOTIFY WEBSOCKET
# -------------------------------------------------------
def redis_ltp_listener():
    """
    Listen for Redis LTP updates and push to WebSocket instantly.
    Resilient: retries when Redis is down and continues when recovered.
    """
    while True:
        r = get_redis()
        if not r:
            
            time.sleep(5)
            continue

        try:
            # ignore_subscribe_messages=True to avoid subscribe join messages
            pubsub = r.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe("ltp_updates")
            # print("[Redis] Listening for LTP updates...")

            for msg in pubsub.listen():
                try:
                    # msg example: {'type': 'message', 'channel': b'ltp_updates', 'data': b'...'}
                    if not msg or msg.get("type") != "message":
                        continue

                    raw = msg.get("data")
                    if isinstance(raw, (bytes, bytearray)):
                        raw = raw.decode("utf-8", errors="ignore")

                    if isinstance(raw, str):
                        data = json.loads(raw)
                    else:
                        # unexpected type, skip
                        continue

                    symbol = data.get("symbol")
                    ltp = data.get("ltp")
                    if symbol is None or ltp is None:
                        continue

                    push_ltp_update(symbol, ltp)

                except Exception as e:
                    print(f"[Redis Listener msg error] {e} — continuing")
                    # continue listening
            # if pubsub.listen() exits, try reconnect
            print("[Redis Listener] pubsub.listen() returned — reconnecting")
            time.sleep(1)

        except Exception as e:
            # print(f"[Redis Listener] error: {e} — will retry in 3s")
            time.sleep(3)


# -------------------------------------------------------
# STARTUP EVENTS
# -------------------------------------------------------
# Keep single worker instance
_worker_instance: WebSocketWorker | None = None


@app.on_event("startup")
def on_startup():
    global _worker_instance

    try:
        create_tables()
    except Exception as e:
        print(f"[startup] create_tables error: {e} — continuing")

    # Token refresher
    def start_token_refresher():
        try:
            TokenRefresher().run_forever()
        except Exception:
            print("[TokenRefresher] crashed:\n", traceback.format_exc())

    threading.Thread(target=start_token_refresher, daemon=True).start()

    # Scheduler
    try:
        start_scheduler()
    except Exception:
        print("[startup] start_scheduler error:\n", traceback.format_exc())

    # SmartAPI WebSocket worker (singleton)
    try:
        if _worker_instance is None:
            _worker_instance = WebSocketWorker()
            threading.Thread(target=_worker_instance.run, daemon=True).start()
        else:
            # best-effort to ensure worker runs after reload
            threading.Thread(target=_worker_instance.run, daemon=True).start()
    except Exception:
        print("[startup] WebSocketWorker start error:\n", traceback.format_exc())

    # DB flush loop: drains LTP queue into DB regularly
    def flush_loop():
        while True:
            try:
                update_holdings_batch()
            except Exception as e:
                print(f"[{datetime.now()}] flush_loop error: {e}\n{traceback.format_exc()}")
            time.sleep(5)

    threading.Thread(target=flush_loop, daemon=True).start()

    # Redis pub/sub listener (robust)
    threading.Thread(target=redis_ltp_listener, daemon=True).start()

    # Transaction sync on startup
    def startup_sync():
        db = None
        try:
            db = SessionLocal()
            processed = process_all_unsynced_transactions(db)
            if processed:
                print(f"[SYNC] Startup sync processed {len(processed)} transactions")
        except Exception as e:
            print(f"[SYNC ERROR] Startup sync failed: {e}\n{traceback.format_exc()}")
        finally:
            if db:
                db.close()

    threading.Thread(target=startup_sync, daemon=True).start()

    # Background sync loop (every 5 minutes)
    def sync_loop():
        while True:
            try:
                time.sleep(300)
                db = SessionLocal()
                try:
                    processed = process_all_unsynced_transactions(db)
                    if processed:
                        print(f"[SYNC] Background sync processed {len(processed)} transactions")
                except Exception as e:
                    print(f"[SYNC ERROR] Background sync failed: {e}\n{traceback.format_exc()}")
                finally:
                    db.close()
            except Exception as outer:
                print(f"[SYNC LOOP ERROR] {outer}\n{traceback.format_exc()}")
                time.sleep(5)

    threading.Thread(target=sync_loop, daemon=True).start()


# -------------------------------------------------------
# CACHE INIT
# -------------------------------------------------------
@app.on_event("startup")
async def _cache_startup():
    try:
        FastAPICache.init(InMemoryBackend())
    except Exception:
        print("[cache] FastAPICache init failed, continuing")


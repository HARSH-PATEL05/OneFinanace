import os
import json
import time
from datetime import datetime
import pyotp
from SmartApi import SmartConnect

# Use runtime-safe getter, NOT redis_client variable
from redis_client import get_redis, redis_safe_json_get, redis_safe_json_set

from app.core.utils import load_credentials
from app.core.config import ANGEL_API_KEY

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOKEN_FILE = os.path.join(BASE_DIR, "tokens", "angelone_token.json")

CHECK_INTERVAL_SECONDS = 3600  # 1 hour
REDIS_TOKEN_KEY = "angelone:tokens"


def log(msg: str, level: str = "INFO"):
    print(f"[{datetime.now()}] {level}: {msg}")


# ------------------------------------------------
# FILE I/O for backup
# ------------------------------------------------
def read_tokens_file() -> dict:
    try:
        if not os.path.exists(TOKEN_FILE):
            return {}
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_tokens_file(data: dict):
    try:
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        log(f"Failed to write tokens to file: {e}", "WARNING")


# ------------------------------------------------
# SINGLE-SOURCE token loader
# ------------------------------------------------
def load_tokens() -> dict:
    """
    Load tokens from Redis → fallback to JSON file → always return a dict.
    """

    # 1) Redis
    try:
        cached = redis_safe_json_get(REDIS_TOKEN_KEY)
        if isinstance(cached, dict):
            return cached
    except Exception:
        pass

    # 2) Fallback file
    return read_tokens_file()


def save_tokens(data: dict):
    """
    Save tokens to Redis + file.
    """

    # Redis first
    redis_safe_json_set(REDIS_TOKEN_KEY, data)

    # File backup
    write_tokens_file(data)


# ------------------------------------------------
# TOKEN REFRESHER
# ------------------------------------------------
class TokenRefresher:
    def __init__(self):
        self.current_tokens = load_tokens()

    def full_login(self):
        creds = load_credentials(broker_name="angelone") or {}

        client_code = creds.get("client_code") or creds.get("clientId")
        pin = creds.get("mpin") or creds.get("password")
        totp_secret = creds.get("totp_secret")

        if not client_code:
            raise RuntimeError("Missing client_code in credentials.json")
        if not pin:
            raise RuntimeError("Missing mpin/password in credentials.json")
        if not totp_secret:
            raise RuntimeError("Missing totp_secret")

        # Generate TOTP
        totp = pyotp.TOTP(totp_secret).now()
        log("Generated TOTP")

        obj = SmartConnect(api_key=ANGEL_API_KEY)

        try:
            log(f"Performing full login for {client_code}...")
            resp = obj.generateSession(client_code, pin, totp)

            if not isinstance(resp, dict) or "data" not in resp:
                raise RuntimeError(f"Invalid login response: {resp}")

            data = resp["data"]
            jwt = data.get("jwtToken", "")
            refresh = data.get("refreshToken", "")
            feed = data.get("feedToken", "")

            tokens = {
                "jwtToken": f"{jwt}",
                "refreshToken": refresh,
                "feedToken": feed,
                "last_full_login": datetime.utcnow().isoformat(),
            }

            # Save in Redis + file
            save_tokens(tokens)
            self.current_tokens = tokens

            log("Tokens updated & saved successfully ✅")

        except Exception as e:
            log(f"full_login failed: {e}", "ERROR")
            raise

        # IMPORTANT:
        # DO NOT call terminateSession — doing so kills feeds.
        # We keep the session alive.

    def run_forever(self):
        log("TokenRefresher started")

        while True:
            try:
                last_login = self.current_tokens.get("last_full_login")
                if last_login:
                    try:
                        last_dt = datetime.fromisoformat(last_login)
                        age = (datetime.utcnow() - last_dt).total_seconds()
                        if age < 3600:  # < 60 min
                            log("Tokens still fresh → skip refresh")
                            time.sleep(60)
                            continue
                    except Exception:
                        pass

                # Otherwise refresh via full login
                self.full_login()

            except Exception as e:
                log(f"TokenRefresher error: {e}", "ERROR")
                time.sleep(120)
                continue

            time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    TokenRefresher().run_forever()

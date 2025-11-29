from SmartApi.smartConnect import SmartConnect
from app.api.brokers.broker_base import BrokerBase
from app.core.utils import save_token, load_token, save_credentials, load_credentials
from app.core.config import ANGEL_API_KEY
import pyotp
import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# -------------------------------------
# Safe JSON converter
# -------------------------------------
def ensure_dict(data: Any) -> Dict[str, Any]:
    """Convert bytes/str/None → dict safely."""
    if data is None:
        return {}

    if isinstance(data, dict):
        return data

    if isinstance(data, bytes):
        try:
            return json.loads(data.decode("utf-8"))
        except Exception:
            return {"raw": data.decode(errors="ignore")}

    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception:
            return {"raw": data}

    return {}


class AngelOneBroker(BrokerBase):
    def __init__(self) -> None:
        super().__init__("angelone")
        self.client_code: str = ""
        self.mpin: str = ""
        self.totp_secret: str = ""
        self.sc: Optional[SmartConnect] = None
        self.api_key= ANGEL_API_KEY

    # -------------------------
    # Credentials
    # -------------------------
    def save_credentials(self, creds: Dict[str, Any]) -> None:
        self.client_code = creds.get("client_code") or ""
        self.mpin = creds.get("mpin") or ""
        self.totp_secret = creds.get("totp_secret") or ""
        save_credentials(self.broker_name, creds)

    def load_credentials(self) -> Dict[str, Any]:
        creds = load_credentials(self.broker_name)
        if creds:
            self.client_code = creds.get("client_code") or ""
            self.mpin = creds.get("mpin") or ""
            self.totp_secret = creds.get("totp_secret") or ""
        return creds or {}

    # -------------------------
    # Login URL
    # -------------------------
    def get_login_url(self, user_id: Optional[str] = None) -> str:
        # user_id is optional and not used currently
        return "http://127.0.0.1:8000/brokers/angelone/callback"

    # -------------------------
    # Generate Token
    # -------------------------
    def generate_token(self) -> Dict[str, Any]:
        try:
            creds = self.load_credentials()

            if not self.client_code or not self.mpin or not self.totp_secret:
                return {"error": "Client code, MPIN, and TOTP secret are required"}

            self.sc = SmartConnect(api_key=self.api_key)

            # TOTP
            totp_code = pyotp.TOTP(self.totp_secret).now()

            # Login
            raw = self.sc.generateSession(self.client_code, self.mpin, totp_code)
            data = ensure_dict(raw)
            payload = ensure_dict(data.get("data"))

            jwt_token = (
                payload.get("jwtToken")
                or data.get("jwtToken")
                or payload.get("accessToken")
            )

            if not jwt_token:
                return {"error": "Failed to generate token", "details": data}

            # Save clean dict only
            save_token(self.broker_name, payload)

            return {"status": "success", "token_data": payload}

        except Exception as e:
            logger.exception(f"[AngelOne] Token generation failed: {e}")
            return {"error": str(e)}

    # -------------------------
    # Fetch holdings
    # -------------------------
    def fetch_holdings(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        try:
            token_info = access_token or load_token(self.broker_name)
            token_info = ensure_dict(token_info)

            if not token_info:
                return {"error": "No access token found. Please login first."}

            # SmartConnect client init
            if not self.sc:
                self.sc = SmartConnect(api_key=self.api_key)

            jwt_token = (
                token_info.get("jwtToken")
                or token_info.get("accessToken")
                or token_info.get("token")
            )

            if not jwt_token:
                return {"error": "Invalid token format", "raw": token_info}

            # Proper session attach
            try:
                self.sc.set_session(jwt_token)  # type: ignore
            except Exception:
                pass

            # Fetch holdings
            raw = self.sc.allholding()
            data = ensure_dict(raw)

            return data

        except Exception as e:
            logger.exception(f"[AngelOne] Fetch holdings failed: {e}")
            return {"error": str(e)}

    # -------------------------
    # Mutual Funds (optional)
    # -------------------------
    def fetch_mfs(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        # Currently not supported
        return {"status": "not_supported"}

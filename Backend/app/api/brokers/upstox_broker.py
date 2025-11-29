import requests
from urllib.parse import urlencode
from typing import Optional, Dict, Any
from app.api.brokers.broker_base import BrokerBase
from app.core.config import UPSTOX_CLIENT_ID, UPSTOX_CLIENT_SECRET, UPSTOX_REDIRECT_URI, UPSTOX_API_BASE
from app.core.utils import save_token, load_token
from app.api.brokers.angel_broker import ensure_dict
import logging

logger = logging.getLogger(__name__)


class UpstoxBroker(BrokerBase):
    def __init__(self) -> None:
        super().__init__("upstox")
        # Fallback to "" to ensure str type
        self.client_id: str = UPSTOX_CLIENT_ID or ""
        self.client_secret: str = UPSTOX_CLIENT_SECRET or ""
        self.redirect_uri: str = UPSTOX_REDIRECT_URI or ""
        self.api_base: str = UPSTOX_API_BASE or ""

    def get_login_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "read_trade+write_trade",
            "state": "secure_random_state_123"
        }
        return f"{self.api_base}/login/authorization/dialog?{urlencode(params)}"

    def generate_token(self, request_token: Optional[str] = None) -> Dict[str, Any]:
        if not request_token:
            return {"status": "error", "message": "Request token is required"}

        token_url = f"{self.api_base}/login/authorization/token"
        payload = {
            "code": request_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }

        try:
            response = requests.post(token_url, data=payload, timeout=30)
            response.raise_for_status()
            token_data: Dict[str, Any] = ensure_dict(response.json())
            save_token(self.broker_name, token_data)
            return {"status": "success", "data": token_data}
        except requests.RequestException as e:
            logger.error(f"[UpstoxBroker] Token generation failed: {e}")
            return {"status": "error", "message": str(e)}

    def fetch_holdings(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        if not access_token:
            token_info = ensure_dict(load_token(self.broker_name))
            access_token = token_info.get("access_token") or ""

        if not access_token:
            return {"status": "error", "message": "No access token found. Please log in again."}

        url = f"{self.api_base}/portfolio/long-term-holdings"
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = ensure_dict(response.json())
            holdings = data.get("data") or []

            return {"status": "success", "broker": self.broker_name, "holdings": holdings}
        except requests.RequestException as e:
            logger.error(f"[UpstoxBroker] Fetch holdings failed: {e}")
            return {"status": "error", "message": str(e)}

    def fetch_mfs(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        # Currently not supported
        return {"status": "not_supported"}

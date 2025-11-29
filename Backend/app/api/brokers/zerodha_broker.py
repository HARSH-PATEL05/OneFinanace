from kiteconnect import KiteConnect
from typing import Optional, Dict, Any
from app.core.config import ZERODHA_API_KEY, ZERODHA_API_SECRET
from app.core.utils import save_token, load_token
from app.api.brokers.broker_base import BrokerBase
from app.api.brokers.angel_broker import ensure_dict
import logging

logger = logging.getLogger(__name__)


class ZerodhaBroker(BrokerBase):
    def __init__(self) -> None:
        super().__init__("zerodha")
        api_key: str = ZERODHA_API_KEY or ""
        self.api = KiteConnect(api_key=api_key)

    def get_login_url(self) -> str:
        return self.api.login_url()

    def generate_token(self, request_token: Optional[str] = None) -> Dict[str, Any]:
        if not request_token:
            return {"status": "error", "message": "Request token is required"}

        try:
            raw_data = self.api.generate_session(request_token, api_secret=ZERODHA_API_SECRET or "")
            data: Dict[str, Any] = ensure_dict(raw_data)  # Convert safely to dict

            save_token(self.broker_name, data)
            self.api.set_access_token(data.get("access_token", ""))
            return {"status": "success", "data": data}
        except Exception as e:
            logger.error(f"[ZerodhaBroker] Token generation failed: {e}")
            return {"status": "error", "message": str(e)}

    def fetch_holdings(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        if not access_token:
            token_data: Dict[str, Any] = ensure_dict(load_token(self.broker_name))
            access_token = token_data.get("access_token", "")

        if not access_token:
            return {"status": "error", "message": "No access token found. Please log in again."}

        try:
            self.api.set_access_token(access_token)
            holdings = self.api.holdings()
            return {"status": "success", "broker": self.broker_name, "holdings": holdings}
        except Exception as e:
            logger.error(f"[ZerodhaBroker] Fetch holdings failed: {e}")
            return {"status": "error", "message": str(e)}

    def fetch_mfs(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        if not access_token:
            token_data: Dict[str, Any] = ensure_dict(load_token(self.broker_name))
            access_token = token_data.get("access_token", "")

        if not access_token:
            return {"status": "error", "message": "No access token found. Please log in again."}

        try:
            self.api.set_access_token(access_token)
            mf_data = self.api.mf_holdings()
            return {"status": "success", "broker": self.broker_name, "mutual_funds": mf_data}
        except Exception as e:
            logger.error(f"[ZerodhaBroker] Fetch MFs failed: {e}")
            return {"status": "error", "message": str(e)}

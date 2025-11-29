import requests
import pyotp
from typing import Optional, Dict, Any
from app.api.brokers.broker_base import BrokerBase
from app.core.config import GROWW_API_KEY, GROWW_API_SECRET, GROWW_API_BASE
from app.core.utils import save_token, load_token
from app.api.brokers.angel_broker import ensure_dict
import logging

logger = logging.getLogger(__name__)


class GrowwBroker(BrokerBase):
    def __init__(self) -> None:
        super().__init__("groww")
        # Fallback to "" to satisfy Pylance type checker
        self.api_key: str = GROWW_API_KEY or ""
        self.api_secret: str = GROWW_API_SECRET or ""
        self.api_base: str = GROWW_API_BASE or ""

    def get_login_url(self) -> str:
        return "brokers/groww/callback"

    def generate_token(self) -> Dict[str, Any]:
        try:
            totp = pyotp.TOTP(self.api_secret).now()
            url = f"{self.api_base}/v1/api/token"
            payload = {"api_key": self.api_key, "totp": totp}
            headers = {"accept": "application/json", "Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            token_data: Dict[str, Any] = ensure_dict(response.json())
            save_token(self.broker_name, token_data)

            return {"status": "success", "data": token_data}

        except requests.RequestException as e:
            logger.error(f"[GrowwBroker] Token generation failed: {e}")
            return {"status": "error", "message": str(e)}

    def _get_auth_headers(self, access_token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "X-API-VERSION": "1.0"
        }

    def fetch_holdings(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        if not access_token:
            token_info = ensure_dict(load_token(self.broker_name))
            access_token = (
                token_info.get("access_token")
                or ensure_dict(token_info.get("data")).get("access_token")
                or ""
            )

        if not access_token:
            return {"status": "error", "message": "No access token. Please log in again."}

        url = f"{self.api_base}/v1/api/portfolio/holdings"
        headers = self._get_auth_headers(access_token)

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = ensure_dict(response.json())
            holdings = data.get("payload") or data.get("data") or []

            return {"status": "success", "broker": self.broker_name, "holdings": holdings}
        except requests.RequestException as e:
            logger.error(f"[GrowwBroker] Fetch holdings failed: {e}")
            return {"status": "error", "message": str(e)}

    def fetch_mfs(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        if not access_token:
            token_info = ensure_dict(load_token(self.broker_name))
            access_token = (
                token_info.get("access_token")
                or ensure_dict(token_info.get("data")).get("access_token")
                or ""
            )

        if not access_token:
            return {"status": "error", "message": "No access token. Please log in again."}

        url = f"{self.api_base}/v1/api/mf/investments"
        headers = self._get_auth_headers(access_token)

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = ensure_dict(response.json())
            mf_data = data.get("payload") or data.get("data") or []

            return {"status": "success", "broker": self.broker_name, "mutual_funds": mf_data}
        except requests.RequestException as e:
            logger.error(f"[GrowwBroker] Fetch MFs failed: {e}")
            return {"status": "error", "message": str(e)}

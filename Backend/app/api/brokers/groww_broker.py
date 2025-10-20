import requests
import pyotp
from app.api.brokers.broker_base import BrokerBase
from app.core.config import GROWW_API_KEY, GROWW_API_SECRET, GROWW_API_BASE
from app.core.utils import save_token, load_token


class GrowwBroker(BrokerBase):
    def __init__(self):
        super().__init__("groww")
        self.api_key = GROWW_API_KEY
        self.api_secret = GROWW_API_SECRET
        self.api_base = GROWW_API_BASE  
    def get_login_url(self) -> str:
        return "brokers/groww/callback"
    def generate_token(self) -> dict:
       
        try:
            
            totp_gen = pyotp.TOTP(self.api_secret)
            totp = totp_gen.now()

            
            url = f"{self.api_base}/v1/api/token"
            payload = {"api_key": self.api_key, "totp": totp}
            headers = {"accept": "application/json", "Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            save_token(self.broker_name, token_data)

            return {"status": "success", "data": token_data}

        except requests.RequestException as e:
            return {"status": "error", "message": str(e)}

    def _get_auth_headers(self, access_token: str):
        return {
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "X-API-VERSION": "1.0"
        }

    def fetch_holdings(self, access_token: str = None) -> dict:
        
        if not access_token:
            token_info = load_token(self.broker_name)
            if not token_info:
                return {"error": "No access token. Please log in again."}
            access_token = (
                token_info.get("access_token")
                or token_info.get("data", {}).get("access_token")
            )

        url = f"{self.api_base}/v1/api/portfolio/holdings"
        headers = self._get_auth_headers(access_token)

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            holdings = data.get("payload") or data.get("data") or []
            return {"status": "success", "broker": self.broker_name, "holdings": holdings}
        except requests.RequestException as e:
            return {"status": "error", "message": str(e)}

    def fetch_mfs(self, access_token: str = None) -> dict:
        
        if not access_token:
            token_info = load_token(self.broker_name)
            if not token_info:
                return {"error": "No access token. Please log in again."}
            access_token = (
                token_info.get("access_token")
                or token_info.get("data", {}).get("access_token")
            )

        url = f"{self.api_base}/v1/api/mf/investments"
        headers = self._get_auth_headers(access_token)

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            mf_data = data.get("payload") or data.get("data") or []
            return {"status": "success", "broker": self.broker_name, "mutual_funds": mf_data}
        except requests.RequestException as e:
            return {"status": "error", "message": str(e)}

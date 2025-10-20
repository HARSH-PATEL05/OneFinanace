import requests
from urllib.parse import urlencode
from app.api.brokers.broker_base import BrokerBase
from app.core.config import UPSTOX_CLIENT_ID,UPSTOX_CLIENT_SECRET,UPSTOX_REDIRECT_URI,UPSTOX_API_BASE
from app.core.utils import save_token, load_token

class UpstoxBroker(BrokerBase):
    def __init__(self):
        super().__init__("upstox")
        self.client_id = UPSTOX_CLIENT_ID
        self.client_secret = UPSTOX_CLIENT_SECRET
        self.redirect_uri = UPSTOX_REDIRECT_URI
        self.api_base = UPSTOX_API_BASE

    def get_login_url(self) -> str:

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "read_trade+write_trade",  
            "state": "secure_random_state_123"
            }
        login_url = f"{self.api_base}/login/authorization/dialog?{urlencode(params)}"
        return login_url
    def generate_token(self, request_token: str) -> dict:
       
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
            token_data = response.json()

            
            save_token(self.broker_name, token_data)
            return token_data
        except requests.RequestException as e:
            print(f"[Upstox] Token generation failed: {e}")
            return {"error": str(e)}

    def fetch_holdings(self, access_token: str = None) -> dict:
        if not access_token:
            token_info = load_token(self.broker_name)
            access_token = token_info.get("access_token")

        if not access_token:
            return {"error": "No access token found. Please log in again."}

        holdings_url = f"{self.api_base}/portfolio/long-term-holdings"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        try:
            response = requests.get(holdings_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

        
            if not data or "data" not in data or not data["data"]:
                return {
                "status": "success",
                "broker": self.broker_name,
                "holdings": []
                }

            return {
            "status": "success",
            "broker": self.broker_name,
            "holdings": data["data"]
        }

        except requests.RequestException as e:
            print(f"[Upstox] Fetch holdings failed: {e}")
            return {"error": str(e)}


    def fetch_mfs(self, access_token: str = None) -> dict:
        pass
from SmartApi.smartConnect import SmartConnect
from app.api.brokers.broker_base import BrokerBase
from app.core.utils import save_token, load_token, save_credentials, load_credentials
from app.core.config import ANGEL_API_KEY
import pyotp
import logging

logger = logging.getLogger(__name__)

class AngelOneBroker(BrokerBase):
    def __init__(self):
        super().__init__("angelone")
        self.client_code = None
        self.mpin = None
        self.totp_secret = None
        self.sc = None  
        self.api_key = ANGEL_API_KEY

    def save_credentials(self, creds: dict):
        self.client_code = creds.get("client_code")
        self.mpin = creds.get("mpin")
        self.totp_secret = creds.get("totp_secret")  
        save_credentials(self.broker_name, creds)

    def load_credentials(self):
        creds = load_credentials(self.broker_name)
        if creds:
            self.client_code = creds.get("client_code")
            self.mpin = creds.get("mpin")
            self.totp_secret = creds.get("totp_secret")
        return creds

    def get_login_url(self, user_id: str = None) -> str:
        
        return "http://127.0.0.1:8000/brokers/angelone/callback"

    def generate_token(self) -> dict:
        try:
            creds = self.load_credentials()
            if not creds or not self.client_code or not self.mpin or not self.totp_secret:
                return {"error": "Client code, MPIN, and TOTP secret are required"}

           
            self.sc = SmartConnect(api_key=self.api_key)

           
            totp_code = pyotp.TOTP(self.totp_secret).now()

       
            data = self.sc.generateSession(self.client_code, self.mpin, totp_code)
            access_token = data.get("data", {}).get("jwtToken") or data.get("jwtToken")

            if not access_token:
                return {"error": "Failed to generate access token", "details": data}

            
            save_token(self.broker_name, data.get("data", data))

            return {"status": "success", "token_data": data.get("data", data)}

        except Exception as e:
            logger.exception(f"[AngelOne] Token generation failed: {e}")
            return {"error": str(e)}

    def fetch_holdings(self, access_token: str = None) -> dict:
        try:
          
            token_info = access_token or load_token(self.broker_name)
            if not token_info:
                return {"error": "No access token found. Please login first."}

            if not self.sc:
                self.sc = SmartConnect(api_key=self.api_key)
                jwt_token = token_info.get("jwtToken") or token_info.get("accessToken")
                self.sc.reqsession(jwt_token)

           
            holdings = self.sc.allholding() 
            return holdings

        except Exception as e:
            logger.exception(f"[AngelOne] Fetch holdings failed: {e}")
            return {"error": str(e)}

    def fetch_mfs(self, access_token: str = None) -> dict:
        pass
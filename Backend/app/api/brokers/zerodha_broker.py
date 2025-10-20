from kiteconnect import KiteConnect
from app.core.config import ZERODHA_API_KEY, ZERODHA_API_SECRET
from app.core.utils import save_token, load_token
from app.api.brokers.broker_base import BrokerBase


class ZerodhaBroker(BrokerBase):
    def __init__(self):
        self.api = KiteConnect(api_key=ZERODHA_API_KEY)
        self.broker_name = "zerodha"

    def get_login_url(self):
        return self.api.login_url()

    def generate_token(self, request_token: str):
        data = self.api.generate_session(request_token, api_secret=ZERODHA_API_SECRET)
        save_token(self.broker_name, data)
        self.api.set_access_token(data["access_token"])
        return data

    def fetch_holdings(self):
        token_data = load_token(self.broker_name)
        if not token_data:
            return {"error": "Login required"}
        self.api.set_access_token(token_data["access_token"])
        return self.api.holdings()

    def fetch_mfs(self):
        
        token_data = load_token(self.broker_name)
        if not token_data:
            return {"error": "Login required"}
        self.api.set_access_token(token_data["access_token"])
        try:
            return self.api.mf_holdings()
        except Exception as e:
            return {"error": str(e)}

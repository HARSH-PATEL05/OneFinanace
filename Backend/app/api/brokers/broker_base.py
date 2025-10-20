from abc import ABC, abstractmethod

class BrokerBase(ABC):
    def __init__(self, broker_name: str):
        self.broker_name = broker_name
        self.credentials = {}

    @abstractmethod
    def get_login_url(self, user_id: str = None) -> str:
        pass

    @abstractmethod
    def generate_token(self, request_token: str = None, user_id: str = None) -> dict:
        pass

    @abstractmethod
    def fetch_holdings(self, access_token: str = None) -> dict:
        pass
    
    @abstractmethod
    def fetch_mfs(self, access_token: str = None) -> dict:
        pass

    def save_credentials(self, creds: dict):
        self.credentials = creds

    def get_credentials(self) -> dict:
        return self.credentials

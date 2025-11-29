from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BrokerBase(ABC):
    def __init__(self, broker_name: str) -> None:
        self.broker_name: str = broker_name
        self.credentials: Dict[str, Any] = {}

    @abstractmethod
    def get_login_url(self, user_id: Optional[str] = None) -> str:
        """Return the broker login URL"""
        pass

    @abstractmethod
    def generate_token(
        self, request_token: Optional[str] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate and return token data"""
        pass

    @abstractmethod
    def fetch_holdings(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch and return holdings"""
        pass

    @abstractmethod
    def fetch_mfs(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch and return mutual fund holdings"""
        pass

    def save_credentials(self, creds: Dict[str, Any]) -> None:
        self.credentials = creds

    def get_credentials(self) -> Dict[str, Any]:
        return self.credentials

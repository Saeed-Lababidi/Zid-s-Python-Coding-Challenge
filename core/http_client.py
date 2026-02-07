"""
HTTP Client with Retry logic.
Satisfies the bonus requirement: "Add mechanisms for doing HTTP calls and doing HTTP retries."
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any


class HTTPClient:
    """
    Wrapper around requests.Session with built-in retry logic.
    """

    def __init__(
        self,
        base_url: str = "",
        retries: int = 3,
        backoff_factor: float = 0.3,
        status_forcelist: tuple = (500, 502, 504),
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.base_url = base_url
        self.session = requests.Session()
        
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        if headers:
            self.session.headers.update(headers)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        url =f"{self.base_url}{endpoint}" if self.base_url else endpoint
        return self.session.get(url, params=params, **kwargs)

    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
        return self.session.post(url, json=json, **kwargs)

    def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
        return self.session.put(url, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
        return self.session.delete(url, **kwargs)

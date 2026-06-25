"""Keycloak authentication helper for API tests."""
import os
import time
import httpx
from typing import Optional, Dict, Any


class KeycloakAuth:
    """Handle Keycloak authentication for test clients."""
    
    def __init__(self):
        self.server_url = os.environ.get("KEYCLOAK_SERVER_URL", "")
        self.realm = os.environ.get("KEYCLOAK_REALM", "myapp")
        self.client_id = os.environ.get("KEYCLOAK_CLIENT_ID", "tap-eam-8a473212f5e306df-b")
        self.client_secret = os.environ.get("KEYCLOAK_CLIENT_SECRET", "uly9XIcpLbZr473m2fUX9dPLelrZKg6C")
        
        # Test user credentials - you may need to adjust these
        self.test_username = os.environ.get("TEST_USERNAME", "test_admin")
        self.test_password = os.environ.get("TEST_PASSWORD", "test_password")
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
    @property
    def token_endpoint(self) -> str:
        """Get Keycloak token endpoint."""
        return f"{self.server_url.rstrip('/')}/realms/{self.realm}/protocol/openid-connect/token"
    
    def get_access_token(self) -> str:
        """Get valid access token, refreshing if needed."""
        if self.access_token and self.token_expires_at:
            # Add 30 second buffer before expiry
            if time.time() < (self.token_expires_at - 30):
                return self.access_token
        
        # Need to get new token
        token_data = self._request_token()
        self.access_token = token_data["access_token"]
        
        # Calculate expiry time
        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = time.time() + expires_in
        
        return self.access_token
    
    def _request_token(self) -> Dict[str, Any]:
        """Request new access token from Keycloak."""
        grant_type = os.environ.get("KEYCLOAK_GRANT_TYPE", "password")
        
        if grant_type == "client_credentials":
            # Use client credentials grant (no user required)
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        else:
            # Use password grant (requires test user)
            data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.test_username,
                "password": self.test_password,
            }
        
        with httpx.Client(verify=False) as client:
            response = client.post(self.token_endpoint, data=data)
            response.raise_for_status()
            return response.json()
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers with access token."""
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}


class AuthenticatedClient:
    """HTTP client with automatic Keycloak authentication."""
    
    def __init__(self, base_url: str):
        self.client = httpx.Client(base_url=base_url, timeout=30.0, verify=False)
        self.auth = KeycloakAuth()
        
    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make authenticated request."""
        # Add auth headers to existing headers
        headers = kwargs.get("headers", {})
        headers.update(self.auth.get_auth_headers())
        kwargs["headers"] = headers
        
        return self.client.request(method, url, **kwargs)
        
    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)
        
    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)
        
    def put(self, url: str, **kwargs) -> httpx.Response:
        return self.request("PUT", url, **kwargs)
        
    def delete(self, url: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)
        
    def close(self):
        """Close the client."""
        self.client.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
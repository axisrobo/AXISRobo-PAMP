"""Global test fixtures."""
import os
import pytest
import httpx
from helpers.keycloak_auth import AuthenticatedClient
from helpers.enveloped_client import EnvelopedClient


@pytest.fixture(scope="session")
def base_url():
    return os.environ.get("AXISARCH_BASE_URL", "http://localhost:4000")


@pytest.fixture(scope="session")
def unauthenticated_client(base_url):
    """Unauthenticated client for testing public endpoints."""
    with httpx.Client(base_url=base_url, timeout=30.0, verify=False) as c:
        yield c


@pytest.fixture(scope="session")
def auth_client(base_url):
    """Authenticated client with Keycloak authentication."""
    with AuthenticatedClient(base_url) as client:
        yield client


@pytest.fixture(scope="session")
def client(base_url):
    """Default client - automatically handles authentication based on backend config."""
    # Check if we have Keycloak environment variables set
    grant_type = os.environ.get('KEYCLOAK_GRANT_TYPE', 'password')
    client_id = os.environ.get('KEYCLOAK_CLIENT_ID')
    client_secret = os.environ.get('KEYCLOAK_CLIENT_SECRET')
    
    if grant_type == 'client_credentials' and client_id and client_secret:
        # Use authenticated client when Keycloak is configured
        with AuthenticatedClient(base_url) as client:
            yield EnvelopedClient(client)
    else:
        # Fallback to unauthenticated client
        with httpx.Client(base_url=base_url, timeout=30.0, verify=False) as c:
            yield EnvelopedClient(c)

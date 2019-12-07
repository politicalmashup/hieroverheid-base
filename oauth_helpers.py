
from oauthlib.oauth2 import BackendApplicationClient
from requests.adapters import HTTPAdapter
from requests_oauthlib import OAuth2Session
from urllib3 import Retry

from constants import TAPI_ROOT_URL
from oauth_credentials import client_id, client_secret


def get_client(client_id, scope=None):
    session = OAuth2Session(client=BackendApplicationClient(client_id=client_id), scope=scope)
    retry = Retry(
        connect=2,
        backoff_factor=1,
        status_forcelist=(500, 502, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session


def get_token(client, client_secret, scope):
    token_url = f"{TAPI_ROOT_URL}o/token/"
    return client.fetch_token(
        token_url=token_url,
        client_id=client.client_id,
        client_secret=client_secret,
        scope=scope
    )


def get_client_with_token(client_id, client_secret, scope=None):
    client = get_client(client_id, scope)
    get_token(client, client_secret, scope)
    return client


oauth_client = get_client_with_token(
    client_id=client_id,
    client_secret=client_secret
)


def post_with_client(url, data):
    return oauth_client.post(url, json=data)


def get_with_client(url):
    return oauth_client.get(url)


def delete_with_client(url, id):
    id_url = url + id
    return oauth_client.delete(id_url)

import os

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

TAPI_ROOT_URL = "https://topics-dev.platform.co.nl/"
# TAPI_ROOT_URL = "http://localhost:8000/"
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def get_client(client_id, scope=None):
    return OAuth2Session(client=BackendApplicationClient(client_id=client_id), scope=scope)

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

def post_with_client(client, url, data):
    return client.post(url, json=data)

def get_with_client(client, url):
    return client.get(url)

def delete_with_client(client, url, id):
    id_url = url + id
    return client.delete(id_url)
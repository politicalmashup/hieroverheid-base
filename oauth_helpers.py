
from oauthlib.oauth2 import BackendApplicationClient
from requests.adapters import HTTPAdapter
from requests_oauthlib import OAuth2Session
from urllib3 import Retry

from constants import TAPI_ROOT_URL, TAPI_CLIENT_ID, TAPI_CLIENT_SECRET


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
    client_id=TAPI_CLIENT_ID,
    client_secret=TAPI_CLIENT_SECRET
)


def post_with_client(url, data):
    return oauth_client.post(url, json=data)


def get_with_client(url):
    return oauth_client.get(url)


def delete_with_client(url, id):
    id_url = url + id
    return oauth_client.delete(id_url)


"""
    Copyright 2019 Hendrik Grondijs, Alex Olieman <alex@olieman.net>

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

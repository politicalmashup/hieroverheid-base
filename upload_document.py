import json
import sys

import requests

from oauth_credentials import client_id, client_secret
from oauth_helpers import get_client_with_token

oauth_client = get_client_with_token(
    client_id=client_id,
    client_secret=client_secret
)


def download_doc(doc_id):
    ori_search_url = 'https://ori.argu.co/api/*/_search'
    resp = requests.get(ori_search_url, params={'pretty': 'true', 'q': f'_id:{doc_id}'})
    data = resp.json()
    return data['hits']['hits'][0]['_source']


def upload_doc(doc_id):
    doc_source = download_doc(doc_id)
    tapi_data = {
        'document_id': f'orid:{doc_id}',
        'title': doc_source['name'],
        'sections': [
            {'heading': f'page {i}', 'body': body}
            for i, body in enumerate(doc_source['text'])
        ]
    }
    tapi_url = f'https://topics-dev.platform.co.nl/dev/document/orid:{doc_id}/'
    resp = oauth_client.put(tapi_url, json=tapi_data)
    if resp.ok:
        print(resp.json())
    else:
        print(resp.status_code, resp.text)


if __name__ == '__main__':
    doc_id = sys.argv[1]
    upload_doc(doc_id)

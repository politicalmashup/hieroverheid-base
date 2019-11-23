import argparse
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
    resp = requests.get(ori_search_url, params={'q': f'_id:{doc_id}'})
    data = resp.json()
    try:
        return data['hits']['hits'][0]['_source']
    except (IndexError, KeyError):
        raise IndexError(f'Document {doc_id} was not found.')


def upload_doc(doc_id):
    doc_source = download_doc(doc_id)
    tapi_data = {
        'document_id': f'orid:{doc_id}',
        'title': doc_source['name'],
        'sections': [
            {'heading': f'page {1 + i}', 'body': body or '---'}
            for i, body in enumerate(doc_source['text'])
        ]
    }
    tapi_url = f'https://topics-dev.platform.co.nl/dev/document/orid:{doc_id}/'
    resp = oauth_client.put(tapi_url, json=tapi_data)
    if resp.ok:
        print(resp.text)
    else:
        print(resp.status_code, resp.text, file=sys.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upload ORI documents to the TAPI.')
    parser.add_argument(
        'doc_ids', metavar='doc_id', type=int, nargs='+', help="One or more orid:<doc_id>s"
    )
    args = parser.parse_args()
    for doc_id in args.doc_ids:
        upload_doc(doc_id)

#!/usr/bin/env python3
import argparse
import sys

from elasticsearch import Elasticsearch

from constants import document_list_url, ES_ORI_URL
from oauth_credentials import client_id, client_secret
from oauth_helpers import get_client_with_token

oauth_client = get_client_with_token(
    client_id=client_id,
    client_secret=client_secret
)
es_client = Elasticsearch(ES_ORI_URL)


def download_docs(doc_ids):
    result = es_client.search('o*', body={'query': {
        'ids': {'values': doc_ids}
    }})
    for hit in result['hits']['hits']:
        yield hit['_source']


def upload_docs(args):
    for doc_source in download_docs(args.doc_ids):
        doc_id = doc_source['@id']
        try:
            tapi_data = {
                'document_id': f'orid:{doc_id}',
                'title': doc_source['name'],
                'sections': [
                    {'heading': f'page {1 + i}', 'body': body or '---'}
                    for i, body in enumerate(doc_source['text'])
                ]
            }
        except KeyError:
            print(f'orid:{doc_id} is missing text; is it a document?', file=sys.stderr)
            continue

        tapi_url = f'{document_list_url}orid:{doc_id}/'
        resp = oauth_client.put(tapi_url, json=tapi_data)
        if resp.ok:
            if not args.quiet:
                print(resp.text)
        else:
            print(resp.status_code, resp.text, file=sys.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upload ORI documents to the TAPI.')
    parser.add_argument(
        'doc_ids', metavar='doc_id', type=int, nargs='+', help="One or more orid:<doc_id>s"
    )
    parser.add_argument(
        '--quiet', dest='quiet', action='store_true',
        help='suppress messages to stdout; only write error output'
    )
    args = parser.parse_args()
    upload_docs(args)

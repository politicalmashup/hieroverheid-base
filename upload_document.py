#!/usr/bin/env python3
import argparse
import sys

from elasticsearch import Elasticsearch

from constants import document_list_url, ES_ORI_URL
from es_helpers import scan
from oauth_helpers import oauth_client

es_client = Elasticsearch(ES_ORI_URL)


def download_docs(doc_ids):
    result = scan(
        es_client,
        scroll='2m',
        size=20,
        index='o*',
        query={
            'query': {
                'ids': {'values': doc_ids}
            }
        },
        raise_on_error=False,
    )
    for hit in result:
        yield hit['_source']


def upload_docs(cli_args):
    for doc_source in download_docs(cli_args.doc_ids):
        doc_id = doc_source['@id']
        try:
            if isinstance(doc_source['text'], str):
                print(f'orid:{doc_id} text has not been split into pages', file=sys.stderr)
                continue

            tapi_data = {
                'document_id': f'orid:{doc_id}',
                'title': doc_source['name'],
                'sections': [
                    {'heading': f'page {1 + i}', 'body': body.strip() or '---'}
                    for i, body in enumerate(doc_source['text'][:5000])
                ]
            }
        except KeyError:
            print(f'orid:{doc_id} is missing text; is it a document?', file=sys.stderr)
            continue

        tapi_url = f'{document_list_url}orid:{doc_id}/'
        resp = oauth_client.put(tapi_url, json=tapi_data)
        if resp.ok:
            if not cli_args.quiet:
                print(resp.text)
        else:
            print(resp.status_code, resp.text, doc_id, file=sys.stderr)


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

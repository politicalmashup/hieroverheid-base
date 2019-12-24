#!/usr/bin/env python3
import argparse
import re
import sys
from itertools import zip_longest
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from tqdm import tqdm

from constants import ES_ORI_URL, ORSI_FILTER, document_list_url
from oauth_helpers import oauth_client

es_client = Elasticsearch(ES_ORI_URL)
here = Path(__file__).parent
state_dir = here / 'index-state'


def shorten_index_name(full_name):
    return '_'.join(full_name.split('_')[:-1])


def get_modified_indices(index_filter=ORSI_FILTER):
    index_files = state_dir.glob('*.ids')
    index_state = dict([
        f_path.name.split('.')[:2]
        for f_path in index_files
    ])
    indices_str = es_client.cat.indices(index_filter, h='index,docs.count')
    modified_indices = []
    for line in indices_str.split('\n'):
        if line:
            full_name, doc_count = line.split()
            name = shorten_index_name(full_name)
            if index_state.get(name) != doc_count:
                modified_indices.append([name, doc_count])

    return modified_indices


def get_doc_ids(index):
    print(f'getting doc IDs for index {index} ...', file=sys.stderr)
    result = scan(
        es_client,
        index=index,
        query={
            '_source': False,
            'query': {
                'bool': {
                    'filter': [
                        {'term': {
                            '@type.keyword': 'MediaObject',
                        }},
                        {'exists': {'field': 'text'}},
                    ],
                },
            },
            "script_fields": {
                "text-is-list": {
                    "script": "params['_source']['text'] instanceof List"
                }
            }
        },
    )
    doc_ids = sorted(
        (
            hit['_id']
            for hit in result
            if hit['fields']['text-is-list'][0] is True
        ),
        key=lambda did: (len(did), did),
    )
    return doc_ids


def update_index_state(index_filter=ORSI_FILTER):
    modified_indices = get_modified_indices(index_filter)
    for name, doc_count in modified_indices:
        index_ids = get_doc_ids(f'{name}_*')
        if index_ids:
            print(f'index {name} contains {len(index_ids)} valid MediaObjects', file=sys.stderr)
        else:
            print(f'index {name} does not contain MediaObjects', file=sys.stderr)
            continue

        existing_state_files = state_dir.glob(f'{name}.*.ids')
        old_lines = []
        for old_state in existing_state_files:
            with old_state.open() as f:
                old_lines = list(filter(None, f))
            old_state.unlink()

        if old_lines:
            doc_ids = old_lines[-1].split()
            last_doc_id = doc_ids[-1]
            index_ids = index_ids[1 + index_ids.index(last_doc_id):]

        state_file = state_dir / f'{name}.{doc_count}.ids'
        with state_file.open('w') as f:
            for line in old_lines:
                f.write(line)

            chunks = [
                filter(None, chunk)
                for chunk in zip_longest(*[iter(index_ids)] * 200)
            ]
            for chunk in chunks:
                print(' '.join(chunk), file=f)


def tapi_doc_exists(doc_id):
    tapi_url = f'{document_list_url}orid:{doc_id}/'
    resp = oauth_client.head(tapi_url)
    return resp.ok


def get_new_batches(index_filter=ORSI_FILTER, revisit=False):
    index_files = state_dir.glob(f'{index_filter}.ids')
    for f_path in index_files:
        new_batches = []
        with f_path.open() as f:
            lines = list(filter(None, f))

        for line in reversed(lines):
            doc_ids = line.split()
            if tapi_doc_exists(doc_ids[-1]):
                # this line should be fully loaded
                if revisit:
                    continue
                else:  # assume that all previous lines have been loaded
                    break
            elif tapi_doc_exists(doc_ids[0]):
                unloaded_line = slice_partial_line(doc_ids)
                if unloaded_line:
                    new_batches.append(unloaded_line)
                # else:
                #     raise ValueError(f'got empty (unloaded) line: {line!r} {unloaded_line!r}')
            else:
                new_batches.append(line)

        for line in tqdm(reversed(new_batches), desc=f_path.name, total=len(new_batches)):
            print(line.rstrip(), flush=True)


def slice_partial_line(doc_ids, lo=0, hi=None):
    if hi is None:
        hi = len(doc_ids)

    while lo < hi:
        mid = lo + (hi - lo) // 2
        if tapi_doc_exists(doc_ids[mid]):
            lo = mid + 1
        else:
            hi = mid - 1

    ids_slice = doc_ids[lo:]
    return ' '.join(ids_slice) if ids_slice else None


def index_filter_type(arg_value, pattern=re.compile(r'^o[\w-]+\*$')):
    if not pattern.match(arg_value):
        raise argparse.ArgumentTypeError('filter must start with "o" and end with "*"')
    return arg_value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Update index state and return ORIDs of documents that are not in the TAPI.'
    )
    parser.add_argument(
        'index_filter',
        nargs='?',
        default='o*',
        type=index_filter_type,
        help='Elasticsearch index filter (also used for index-state glob)'
    )
    parser.add_argument('--revisit', action='store_true')
    args = parser.parse_args()
    update_index_state(args.index_filter)
    get_new_batches(args.index_filter, args.revisit)

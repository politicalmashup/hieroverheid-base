#!/usr/bin/env python3
from itertools import zip_longest
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

from constants import ES_ORI_URL, ORSI_FILTER

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
    result = scan(
        es_client,
        index=index,
        query={
            '_source': False,
            'query': {
                'match_all': {},
            },
        },
    )
    doc_ids = sorted(
        (hit['_id'] for hit in result),
        key=lambda did: (len(did), did),
    )
    return doc_ids


def update_index_state(index_filter=ORSI_FILTER):
    modified_indices = get_modified_indices(index_filter)
    for name, doc_count in modified_indices:
        index_ids = get_doc_ids(f'{name}_*')
        assert len(index_ids) == int(doc_count), \
            f'ES count is {doc_count} but I got {len(index_ids)} IDs'
        existing_state_files = state_dir.glob(f'{name}.*.ids')
        for old_state in existing_state_files:
            old_state.unlink()

        state_file = state_dir / f'{name}.{doc_count}.ids'
        with state_file.open('w') as f:
            chunks = [
                filter(None, chunk)
                for chunk in zip_longest(*[iter(index_ids)] * 500)
            ]
            for chunk in chunks:
                print(' '.join(chunk), file=f)




"""
def get_new_batches()
- read reverse lines from *.ids
- HEAD last ID
- ok? next file : HEAD first
- if not first.ok: print(line)

new_batches.py | parallel 'tee >(upload_document.py ...) | make_abbr_hoards'
"""


if __name__ == '__main__':
    update_index_state('osi_*')

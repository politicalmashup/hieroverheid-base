#!/usr/bin/env python3
from pathlib import Path

from elasticsearch import Elasticsearch

from constants import ES_ORI_URL

es_client = Elasticsearch(ES_ORI_URL)
here = Path(__file__).parent
state_dir = here / 'index-state'


def shorten_index_name(full_name):
    return '_'.join(full_name.split('_')[:-1])


def get_modified_indices():
    index_files = state_dir.glob('*.ids')
    index_state = dict([
        f_name.split('.')[:2]
        for f_name in index_files
    ])
    indices_str = es_client.cat.indices('o*', h='index,docs.count')
    modified_indices = []
    for line in indices_str.split('\n'):
        if line:
            full_name, doc_count = line.split()
            name = shorten_index_name(full_name)
            if index_state.get(name) != doc_count:
                modified_indices.append([full_name, doc_count])

    # todo: see if get_doc_ids() will work with short index names
    return modified_indices

"""
def get_doc_ids(index)
- save as <index>.<count>.ids
- max 500 doc ids per line

def update_index_state():
- get_modified_indices()
- get_doc_ids(index)
- ?

def get_new_batches()
- read reverse lines from *.ids
- HEAD last ID
- ok? next file : HEAD first
- if not first.ok: print(line)

new_batches.py | parallel 'tee >(upload_document.py ...) | make_abbr_hoards'
"""


if __name__ == '__main__':
    get_modified_indices()

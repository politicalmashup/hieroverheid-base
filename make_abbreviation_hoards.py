#!/usr/bin/env python3
import re
import sys
from argparse import ArgumentParser

from constants import document_list_url, wordhoard_list_url, custom_topics_url
from oauth_helpers import oauth_client
from wordhoard_helpers import post_wordhoard_payload, find_super_items

doc_id_re = re.compile(r'orid:(\d+)')


def log_hoard_action(item_id, item_type, count_created, count_updated):
    print(f"{item_type}\t{item_id}\t+{count_created}\t~{count_updated}")


def update_hoards_for_docs(doc_ids):
    """
    Update word hoards with the abbreviations of specified documents.
    """
    for doc_id in doc_ids:
        abbr_data = get_abbreviations(doc_id)
        abbr_topics = {
            topic_data['abbreviation']: topic_data
            for topic_data in abbr_data['topics']
        }
        for topic_data in abbr_data['topics']:
            topic_data['sources'] = [
                doc_id_re.search(source).group(1)
                for source in topic_data['sources']
            ]

        parent_id, grandparent_id, committee_id = find_super_items(doc_id)
        existing_hoards_resp = oauth_client.get(wordhoard_list_url, params={
            'name': [
                f'orid:{orid}_abbreviations'
                for orid in (doc_id, parent_id, grandparent_id, committee_id)
                if orid
            ]
        })
        existing_hoards = {
            int(doc_id_re.search(hoard_data['name']).group(1)): hoard_data
            for hoard_data in existing_hoards_resp.json()['items']
        }
        for item_id, item_type in [
            (doc_id, 'document'),
            (parent_id, 'parent'),
            (grandparent_id, 'grandparent'),
            (committee_id, 'committee'),
        ]:
            if item_id:
                item_hoard = existing_hoards.get(item_id)
                if item_hoard:
                    update_hoard(item_id, item_type, item_hoard, abbr_topics)
                else:
                    create_new_hoard(item_id, item_type, abbr_data)


def create_new_hoard(item_id, item_type, abbr_data):
    """
    Create a new word hoard with fresh topics for this item.
    """
    new_topics_resp = oauth_client.post(custom_topics_url, json=abbr_data)
    status, err = post_wordhoard_payload(
        item_id, item_type, new_topics_resp.json()['topics'], wh_type='abbreviations'
    )
    if status == 201:
        log_hoard_action(item_id, item_type, len(abbr_data['topics']), 0)
    else:
        log_hoard_action(item_id, item_type, 'E', 0)
        print(status, err, file=sys.stderr)


def update_hoard(item_id, item_type, item_hoard, abbr_topics):
    """
    Update an existing item's word hoard.
    """
    item_hoard_url = f"{wordhoard_list_url}{item_hoard['id']}/"
    get_resp = oauth_client.get(item_hoard_url)
    item_hoard = get_resp.json()
    hoard_topics = {
        topic_data['abbreviation']: topic_data
        for topic_data in item_hoard['topics']
    }
    topics_to_update = []
    item_topics = abbr_topics.copy()
    for abbr, topic_data in hoard_topics.items():
        if abbr in item_topics:
            new_topic_data = item_topics.pop(abbr)
            if new_topic_data['sources'][0] not in topic_data['sources']:
                # this relies on a DSE bug; the intention is to append
                topic_data['sources'] = new_topic_data['sources']  # FIXME: see above
                if (
                        new_topic_data['canonical_name'].lower()
                        != topic_data['canonical_name'].lower()
                ):
                    # this relies on a DSE bug; the intention is to append
                    topic_data['names'] = [new_topic_data['canonical_name']]  # FIXME: see above

                topics_to_update.append(topic_data)

    count_created = 0
    if item_topics:
        new_topics_resp = oauth_client.post(custom_topics_url, json={
            'topics': list(item_topics.values())
        })
        if new_topics_resp.ok:
            status, err = post_wordhoard_payload(
                item_id, item_type, new_topics_resp.json()['topics'],
                wordhoard_id=item_hoard['id'],
                wh_type='abbreviations'
            )
            if status == 204:
                count_created = len(item_topics)
            else:
                count_created = 'E'
        else:
            count_created = 'E'
            print('create', new_topics_resp.status_code, new_topics_resp.text, file=sys.stderr)

    count_updated = 0
    if topics_to_update:
        old_topics_resp = oauth_client.put(custom_topics_url, json={
            topic_data['id']: topic_data
            for topic_data in topics_to_update
        })
        if old_topics_resp.ok:
            count_updated = len(topics_to_update)
        else:
            count_updated = 'E'
            print('update', old_topics_resp.status_code, old_topics_resp.text, file=sys.stderr)

    log_hoard_action(item_id, item_type, count_created, count_updated)


def get_abbreviations(doc_id):
    """
    Get abbreviations for a single document.
    """
    doc_abbreviations_url = f'{document_list_url}orid:{doc_id}/abbreviations/'
    resp = oauth_client.get(doc_abbreviations_url)
    return resp.json()


def update_all_hoards(_):
    """
    Update word hoards with the abbreviations of all documents.
    """
    resp = oauth_client.get(document_list_url)
    document_list = resp.json()['documents']
    document_ids = [
        int(doc['document_id'].split(':')[1])
        for doc in document_list
    ]
    print('updating hoards for documents:', document_ids, file=sys.stderr)
    update_hoards_for_docs(document_ids)


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Update word hoards with abbreviation topics.'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        'doc_ids', metavar='doc_id', type=int, nargs='*', default=[],
        help="Any number of orid:<doc_id>s"
    )
    group.add_argument(
        '--all', dest='update_hoards', action='store_const',
        const=update_all_hoards, default=update_hoards_for_docs,
        help='update the hoards for all existing documents (instead of for <doc_id>s)'
    )
    args = parser.parse_args()
    args.update_hoards(args.doc_ids)

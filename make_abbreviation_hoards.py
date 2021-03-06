#!/usr/bin/env python3
import re
import sys
from argparse import ArgumentParser

from tqdm import tqdm

from constants import document_list_url, wordhoard_list_url, custom_topics_url
from new_batches import state_dir
from oauth_helpers import oauth_client
from wordhoard_helpers import post_wordhoard_payload, find_super_items

doc_id_re = re.compile(r'orid:(\d+)')


def log_hoard_action(item_id, item_type, count_created, count_updated):
    print(f"{item_type}\t{item_id}\t+{count_created}\t~{count_updated}", flush=True)


def update_hoards_for_docs(*doc_ids):
    """
    Update word hoards with the abbreviations of specified documents.
    """
    for doc_id in doc_ids:
        abbr_data = get_abbreviations(doc_id)
        if abbr_data is None or not abbr_data['topics']:
            continue

        parent_id, grandparent_id, committee_id = find_super_items(doc_id)
        existing_hoards_resp = oauth_client.get(wordhoard_list_url, params={
            'name': [
                f'orid:{orid}_abbreviations'
                for orid in (doc_id, parent_id, grandparent_id, committee_id)
                if orid
            ]
        })
        if not existing_hoards_resp.ok:
            print(
                existing_hoards_resp.status_code,
                f'GET Word Hoard list for ORIDs {doc_id, parent_id, grandparent_id, committee_id}',
                file=sys.stderr
            )
            continue

        abbr_topics = {
            topic_data['abbreviation']: topic_data
            for topic_data in abbr_data['topics']
        }
        for topic_data in abbr_data['topics']:
            topic_data['sources'] = [
                doc_id_re.search(source).group(1)
                for source in topic_data['sources']
            ]

        existing_hoards = {
            int(doc_id_re.search(hoard_data['name']).group(1)): hoard_data
            for hoard_data in existing_hoards_resp.json()['items']
        }
        for item_id, item_type in [  # general -> specific order
            (committee_id, 'committee'),
            (grandparent_id, 'grandparent'),
            (parent_id, 'parent'),
            (doc_id, 'document'),
        ]:
            if item_id:
                item_hoard = existing_hoards.get(item_id)
                if item_hoard:
                    update_hoard(item_id, item_type, item_hoard, abbr_topics)
                else:
                    create_new_hoard(item_id, item_type, abbr_topics)


def get_abbreviations(doc_id):
    """
    Get abbreviations for a single document.
    """
    doc_abbreviations_url = f'{document_list_url}orid:{doc_id}/abbreviations/'
    resp = oauth_client.get(doc_abbreviations_url)
    if not resp.ok:
        print(resp.status_code, resp.text, doc_id, file=sys.stderr)
        return None

    return resp.json()


def create_new_hoard(item_id, item_type, abbr_topics):
    """
    Create a new word hoard with fresh and existing topics for this item.
    """
    topics_to_create = [
        topic_data
        for topic_data in abbr_topics.values()
        if 'id' not in topic_data
    ]
    if topics_to_create:
        new_topics_resp = oauth_client.post(custom_topics_url, json={'topics': topics_to_create})
        if new_topics_resp.ok:
            new_topics = new_topics_resp.json()['topics']
            for topic_data in new_topics:
                abbr_topics[topic_data['abbreviation']].update(topic_data)
        else:
            print(
                new_topics_resp.status_code,
                f'POST topics',
                new_topics_resp.text,
                file=sys.stderr
            )
            return

    status, err = post_wordhoard_payload(
        item_id, item_type, abbr_topics.values(), wh_type='abbreviations'
    )
    if status == 201:
        log_hoard_action(item_id, item_type, len(abbr_topics), 0)
    else:
        log_hoard_action(item_id, item_type, 'E', 0)


def update_hoard(item_id, item_type, item_hoard, abbr_topics):
    """
    Update an existing item's word hoard.
    """
    item_hoard_url = f"{wordhoard_list_url}{item_hoard['id']}/"
    get_resp = oauth_client.get(item_hoard_url)
    if not get_resp.ok:
        print(get_resp.status_code, f'GET {item_hoard_url}', get_resp.text, file=sys.stderr)
        return

    item_hoard = get_resp.json()
    hoard_topics = {  # FIXME: the key may be None for definition topics
        topic_data['abbreviation'].lower(): topic_data
        for topic_data in item_hoard['topics']
        if 'abbreviation' in topic_data  # this is a quick fix
    }
    topics_to_update, item_topics = merge_with_existing(abbr_topics, hoard_topics)

    count_created = 0
    if item_topics:
        new_topics_resp = oauth_client.post(custom_topics_url, json={
            'topics': list(item_topics.values())
        })
        if new_topics_resp.ok:
            new_topics = new_topics_resp.json()['topics']
            for topic_data in new_topics:
                abbr_topics[topic_data['abbreviation']].update(topic_data)
            status, err = post_wordhoard_payload(
                item_id, item_type, new_topics,
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


def merge_with_existing(abbr_topics, hoard_topics):
    """
    Merge topics that have near-duplicate abbreviations.
    This mutates abbr_topics by updating them with existing topic data (including ID)
    """
    topics_to_update = []
    name_map = {
        topic_data['canonical_name']: short_lower
        for short_lower, topic_data in hoard_topics.items()
    }
    for short, topic_data in sorted(abbr_topics.items()):
        long = topic_data['canonical_name']
        short_lower = short.lower()
        if short_lower in hoard_topics:
            # normalize case
            existing_topic = hoard_topics[short_lower]
            if any(source not in existing_topic['sources'] for source in topic_data['sources']):
                topics_to_update.append(existing_topic)
                existing_topic['sources'] = add_sources(
                    existing_topic['sources'], topic_data['sources']
                )
                if short != existing_topic['abbreviation']:
                    existing_topic['names'].append(short)

                if existing_topic['canonical_name'].lower() != long.lower():
                    existing_topic['names'].append(long)
                    name_map[long] = short_lower

                existing_topic['names'] = list(sorted(set(existing_topic['names'])))

            topic_data.update(existing_topic)

        elif long in name_map:
            existing_abbr = name_map[long]
            existing_topic = hoard_topics[existing_abbr]
            if any(source not in existing_topic['sources'] for source in topic_data['sources']):
                topics_to_update.append(existing_topic)
                existing_topic['sources'] = add_sources(
                    existing_topic['sources'], topic_data['sources']
                )
                expected_abbr = abbreviate_term(long.lower())
                if (
                        short != existing_topic['abbreviation']
                        and short_lower.startswith(expected_abbr)
                        and len(short_lower) <= len(existing_abbr)
                        and short_lower[-1].isalpha()
                ):
                    # the new abbreviation seems better
                    hoard_topics[short_lower] = existing_topic
                    existing_topic['names'].append(existing_topic['abbreviation'])
                    existing_topic['abbreviation'] = short
                    name_map[long] = short_lower
                    del hoard_topics[existing_abbr]
                else:
                    # add the new abbr as an alternative name
                    existing_topic['names'].append(short)

                existing_topic['names'] = list(sorted(set(existing_topic['names'])))

            topic_data.update(existing_topic)

    item_topics = {
        abbr: topic_data
        for abbr, topic_data in abbr_topics.items()
        if 'id' not in topic_data
    }

    return topics_to_update, item_topics


def add_sources(old_sources, new_sources):

    def source_sort_key(source):
        return len(source), source

    return list(
        sorted(
            set(old_sources) | set(new_sources),
            key=source_sort_key
        )
    )


abbreviate_re = re.compile(r'(\w)[a-z]+')


def abbreviate_term(long_form):
    abbr = abbreviate_re.sub(r'\1', long_form)
    if '-' in abbr:
        return abbr.replace('-', '').replace(' ', '-')

    return abbr.replace(' ', '')


def update_hoards_for_index(index_filter):
    """
    Update word hoards with the abbreviations of all documents in the specified index.
    """
    index_files = state_dir.glob(f'{index_filter}.ids')
    for f_path in index_files:
        with f_path.open() as f:
            lines = list(filter(None, f))

        total = sum(1 + line.count(' ') for line in lines)
        with tqdm(desc=f_path.name, total=total) as progress_bar:
            for line in lines:
                document_ids = line.split()
                for doc_id in document_ids:
                    update_hoards_for_docs(int(doc_id))
                    progress_bar.update(1)


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
        '--index', help='update all hoards for the given index filter'
    )
    args = parser.parse_args()
    if args.index:
        update_hoards_for_index(args.index)
    else:
        update_hoards_for_docs(*args.doc_ids)

"""
    Copyright 2019 Alex Olieman <alex@olieman.net>

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

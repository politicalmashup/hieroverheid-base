#!/usr/bin/env python3
import argparse
import sys
from itertools import chain

from constants import wordhoard_list_url, wordhoard_topics_url
from make_abbreviation_hoards import doc_id_re
from oauth_helpers import oauth_client
from wordhoard_helpers import find_super_items


def drop_doc_hoards(cli_args):
    """
    Delete hoards (and their topics) for the specified documents.
    """
    for doc_id in cli_args.doc_ids:
        parent_id, grandparent_id, committee_id = find_super_items(doc_id)
        hoard_names = list(chain.from_iterable([
            (f'orid:{orid}_abbreviations', f'orid:{orid}_definitions')
            for orid in (doc_id, parent_id, grandparent_id, committee_id)
            if orid
        ]))
        existing_hoards_resp = oauth_client.get(wordhoard_list_url, params={
            'name': hoard_names
        })
        if not existing_hoards_resp.ok:
            print(
                existing_hoards_resp.status_code,
                f'GET Word Hoard list for ORIDs {doc_id, parent_id, grandparent_id, committee_id}',
                file=sys.stderr
            )
            continue

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
            item_hoard = existing_hoards.get(item_id)
            if not item_hoard:
                continue

            hoard_id = item_hoard['id']
            if cli_args.drop_topics:
                topics_resp = oauth_client.delete(wordhoard_topics_url % hoard_id)
                if topics_resp.ok:
                    print(f'deleted topics in {hoard_id} for orid:{item_id}', flush=True)
                elif topics_resp.status_code != 404:
                    print(
                        topics_resp.status_code,
                        f'failed to delete topics in hoard {hoard_id} for orid:{item_id}',
                        file=sys.stderr
                    )

            hoard_resp = oauth_client.delete(f'{wordhoard_list_url}{hoard_id}/')
            if hoard_resp.ok:
                print(f'deleted hoard {hoard_id} for orid:{item_id}', flush=True)
            else:
                print(
                    hoard_resp.status_code,
                    f'failed to remove hoard {hoard_id} for orid:{item_id}',
                    item_id,
                    file=sys.stderr
                )

    print('finished deletion')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Delete Word Hoards in the TAPI that were created for ORI documents.'
    )
    parser.add_argument(
        'doc_ids', metavar='doc_id', type=int, nargs='+', help="One or more orid:<doc_id>s"
    )
    parser.add_argument(
        '--and-topics', dest='drop_topics', action='store_true',
        help='also delete the topics that were designated in these hoards'
             ' (NB topics may be in designated in multiple hoards)'
    )
    parser.add_argument(
        '--non-interactive', dest='skip_confirmation', action='store_true',
        help='skip the confirmation prompt'
    )
    # TODO: make hoard type configurable; it currently deletes both types
    args = parser.parse_args()
    if args.skip_confirmation:
        confirmation = 'drop hoards'
    else:
        confirmation = input(
            f'If you are sure you want to delete the Word Hoards corresponding to '
            f'{len(args.doc_ids)} documents, type "drop hoards" and confirm with <return>: '
        )
    if confirmation == 'drop hoards':
        drop_doc_hoards(args)

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


import requests

from constants import ID_ORI_URL, wordhoard_topics_url, wordhoard_list_url
from oauth_helpers import post_with_client


def get_linkeddata(orid):
    response = requests.get(url=f'{ID_ORI_URL}{orid}.jsonld')
    if not response.ok:
        raise IndexError(f'item orid:{orid} did not resolve')
    return response.json()


def find_super_items(ori_doc_id):
    # doc_id een "schema:MediaObject"
    # heeft een linkje dc:isReferencedBy
    # linkje wijst naar (wss) meeting:AgendaItem
    # AgendaItem heeft een schema:superEvent
    # superEvent is van het type meeting:Meeting
    # en een Meeting heeft een meeting:committee (de organisatie die we willen hebben.)

    try:
        doc_json = get_linkeddata(ori_doc_id)  # schema:MediaObject
        parent_orid = doc_json['dc:isReferencedBy']["@id"].split(":")[1]
    except (KeyError, IndexError):
        return None, None, None

    try:
        parent_data = get_linkeddata(parent_orid)  # meeting:AgendaItem or :Meeting
    except IndexError:
        return parent_orid, None, None

    committee_orid = (
        parent_data.get("meeting:committee", {}).get("@id", ":").split(":")[1] or None
    )
    try:
        grandparent_orid = parent_data['schema:superEvent']["@id"].split(":")[1]
    except KeyError:
        return parent_orid, None, committee_orid

    try:
        meeting_item_json = get_linkeddata(grandparent_orid)  # meeting:Meeting
        orid_committee = meeting_item_json["meeting:committee"]["@id"].split(":")[1]
    except (KeyError, IndexError):
        return parent_orid, grandparent_orid, None
    else:
        return parent_orid, grandparent_orid, orid_committee


def empty_wordhoard_payload(orid, rdf_type, wh_type):
    return {
        'topics': {},
        'description': f"Mined {wh_type} for {orid} of type {rdf_type}",
        'name': f"{orid}_{wh_type}",
        'detection_settings': {
            'names': {
                'ignore_case': True
            }
        }
    }


def post_wordhoard_payload(doc_id, rdf_type, topics, wordhoard_id=None, wh_type='definitions'):
    orid = "orid:" + str(doc_id)
    wordhoard_payload = empty_wordhoard_payload(orid, rdf_type, wh_type)
    for topic in topics:
        #  Key to local_name mappings (local_name is None in our case)
        topic_id = topic['id']
        wordhoard_payload['topics'][topic_id] = None

    if wordhoard_id:
        response = post_with_client(wordhoard_topics_url % wordhoard_id, data=wordhoard_payload)
    else:
        response = post_with_client(wordhoard_list_url, data=wordhoard_payload)

    if response.ok:
        return response.status_code, None
    else:
        print(response.status_code, response.text)
        if wordhoard_id:
            print(wordhoard_payload)
            input("Wordhoard update POST error...")
        else:
            input("Wordhoard create POST error...")
        return response.status_code, response.text

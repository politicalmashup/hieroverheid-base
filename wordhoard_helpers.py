import json

import requests

from constants import ID_ORI_URL, custom_wordhoard_topics_url, custom_wordhoards_url
from oauth_helpers import post_with_client
from upload_glossarys_to_tapi import oauth_client


def get_linkeddata(orid):
    orid = str(orid)
    response = requests.get(url=ID_ORI_URL + orid + ".jsonld")
    return json.loads(response.content.decode('utf-8'))


def find_AgendaPunt_Agenda_and_Committee(ori_doc_id):
    # doc_id een "schema:MediaObject"
    # heeft een linkje dc:isReferencedBy
    # linkje wijst naar (wss) meeting:AgendaItem
    # AgendaItem heeft een schema:superEvent
    # superEvent is van het type meeting:Meeting
    # en een Meeting heeft een meeting:committee (de organisatie die we willen hebben.)

    try:
        doc_json = get_linkeddata(ori_doc_id) # schema:MediaObject
        orid_agendaItem = doc_json['dc:isReferencedBy']["@id"].split(":")[1]
    except:
        return (None, None, None)

    try:
        agenda_item_json = get_linkeddata(orid_agendaItem) # meeting:AgendaItem
        orid_agenda = agenda_item_json['schema:superEvent']["@id"].split(":")[1]
    except:
        return (orid_agendaItem, None, None)

    try:
        meeting_item_json = get_linkeddata(orid_agenda) # meeting:Meeting
        orid_committee = meeting_item_json["meeting:committee"]["@id"].split(":")[1]
    except:
        return (orid_agendaItem, orid_agenda, None)
    else:
        return (orid_agendaItem, orid_agenda, orid_committee)


def empty_wordhoard_payload(orid, rdf_type):
    return {
        'topics': {},
        'description': f"Mined definitions for {orid} of type {rdf_type}",
        'name': f"{orid}_definitions",
        'detection_settings': {
            'names': {
                'ignore_case': True
            }
        }
    }


def post_wordhoard_payload(doc_id, rdf_type, topics, wordhoard_id=None):
    orid = "orid:" + str(doc_id)
    wordhoard_payload = empty_wordhoard_payload(orid, rdf_type)
    for topic in topics:
        #  Key to local_name mappings (local_name is None in our case)
        topic_id = topic['id']
        # if wordhoard_id:
        #     topic_id = topic_id.replace("-","")

        wordhoard_payload['topics'][topic_id] = None

    if wordhoard_id:
        # wordhoard_id = wordhoard_id.replace("-","")
        response = post_with_client(oauth_client, custom_wordhoard_topics_url % wordhoard_id, data=wordhoard_payload)
    else:
        response = post_with_client(oauth_client, custom_wordhoards_url, data=wordhoard_payload)

    if response.ok:
        return (response.status_code, None)
    else:
        print(response.status_code, response.text)
        if wordhoard_id:
            print(wordhoard_payload)
            input("Wordhoard update POST error...")
        else:
            input("Wordhoard create POST error...")
        return (response.status_code, response.text)

import os
import json

from constants import (
    custom_topics_url,
    custom_wordhoards_url
)
from oauth_helpers import get_with_client, get_client_with_token, post_with_client
from wordhoard_helpers import find_AgendaPunt_Agenda_and_Committee, post_wordhoard_payload


with open('oauth_credentials.json', 'r') as f:
    oauth_credentials = json.load(f)

oauth_client = get_client_with_token(
    client_id=oauth_credentials['client_id'],
    client_secret=oauth_credentials['client_secret']
)

def main():
    collected_glossarys = sorted(os.listdir('glossarys'))[1:] # exclude the .gitignore file

    for gl in collected_glossarys:
        with open(f'glossarys/{gl}', 'r') as f:
            raw_data = json.load(f)

        doc_id = raw_data['id']
        doc_name = raw_data['doc_name']
        created_wordhoards = {}
        errors = []
        print(f"POSTing glossary of <{doc_name}> to <{custom_topics_url}>")

        # If the wordhoard accompanying this document already exist, we can skip this file.
        # Check this by querying /custom/wordhoard/
        res = get_with_client(client=oauth_client, url=custom_wordhoards_url)
        res_dict = json.loads(res.content.decode('utf-8'))
        custom_wordhoard_list = res_dict["items"]
        custom_wordhoard_names = [item['name'] for item in custom_wordhoard_list]
        intended_wordhoard_name = f"{doc_id}_definitions"

        if intended_wordhoard_name in custom_wordhoard_names:
            print("Already found a wordhoard corresponding to this document. Skipping this extracted glossary.")
            continue

        # If the glossary for this doc is empty, skip this file.
        glossary = raw_data['glossary']
        if len(list(glossary)) == 0:
            print("No glossary definitions found in this document. Skipping...")
            continue


        topics = []
        for topic in glossary:
            # Clean the description of the topic
            description = glossary[topic].strip()
            topics.append({
                'canonical_name': topic,
                'description': description,
                'sources': [raw_data['id']]
            })

        data = { "topics": topics }
        response = post_with_client(oauth_client, custom_topics_url, data=data)
        if response.ok:
            custom_topic_response_dictionary = json.loads(response.content.decode('utf-8'))
        else:
            print(response.status_code, response.text)
            input("custom topic POST error..")
            continue

        print("Creating wordhoards...")
        # Create the wordhoards
        # First check if we can find our expected linked data structure
        # document <-- agendaItem <-- agenda <-- committee
        try:
            orid_agenda, orid_agendaItem, orid_committee = find_AgendaPunt_Agenda_and_Committee(doc_id)
        except Exception as e:
            input("Problem getting the expected linked data structure - ", e)
            errors.append(e)
            continue

        # First the document wordhoard
        status, err = post_wordhoard_payload(doc_id, 'document', custom_topic_response_dictionary['topics'])
        if status is not 201:
            print(status)
            errors.append(err)

        # Agenda Items
        intended_wordhoard_name = f"{orid_agendaItem}_definitions"
        wordhoard_id = None
        for wordhoard in custom_wordhoard_list:
            if wordhoard['name'] == intended_wordhoard_name:
                wordhoard_id = wordhoard['id']
        status, err = post_wordhoard_payload(orid_agendaItem, 'agendaItem', custom_topic_response_dictionary['topics'], wordhoard_id)
        if status is not 201:
            print(status)
            errors.append(err)


        # Agenda's
        intended_wordhoard_name = f"{orid_agenda}_definitions"
        wordhoard_id = None
        for wordhoard in custom_wordhoard_list:
            if wordhoard['name'] == intended_wordhoard_name:
                wordhoard_id = wordhoard['id']
        status, err = post_wordhoard_payload(orid_agenda, 'agenda', custom_topic_response_dictionary['topics'], wordhoard_id)
        if status is not 201:
            print(status)
            errors.append(err)


        # Committee's
        intended_wordhoard_name = f"{orid_committee}_definitions"
        wordhoard_id = None
        for wordhoard in custom_wordhoard_list:
            if wordhoard['name'] == intended_wordhoard_name:
                wordhoard_id = wordhoard['id']
        status, err = post_wordhoard_payload(orid_committee, 'committee', custom_topic_response_dictionary['topics'], wordhoard_id)
        if status is not 201:
            print(status)
            errors.append(err)

        if len(errors) > 0:
            print(errors)
            input("Found errors..")
        print("Created & updated wordhoards...")

        with open("upload_output.json",'r') as f:
            output = json.load(f)

        output["uploaded"].append({
            "doc_id": doc_id,
            "json_source_file_local": doc_name + ".json",
            "newly_created_topics": topics,
            "errors": []
        })

        with open("upload_output.json", 'w') as f:
            json.dump(output, f, indent=2)


if __name__ == '__main__':
    main()


# POST nieuwe Custom Topics:
# ID: dit is de ID die het document bij ORI heeft gekregen.
# Canonical name: De "key" van het begrip.
# Description: De "value" van het begrip.

# Create or update een wordhoard die de naam (Name, veld dat nog niet bestaat) heeft 'doc_id'.
# Name: "{doc_id}_definitions" / {agendapunt_id}_definitions / {agenda_id}_definitions / {org_id}_definitions
# Description: "Mined definitions for {ori_id}"
# D.m.v. een lijst van topics te sturen.
# local_name = None

# Een daar moeten iig de topics inzitten die bij dat document horen.
# Als er een clash is op topic naam dan wordt er niks mee gedaan. Als t goed is krijg je de conflicten terug.
# Eruit filteren en dan opnieuw proberen. Dit willen we wel loggen, als deze clashes ontstaan.
# De eerste poging mag gewoon blijven staan.

# GET annotaties heeft parameter wordhoard_ids

# Gebruik id.openraadsinformatie.nl om bij een doc_id het bijbehorende angedapunt, vergadering en organisatie te zoeken.

# Voor elke agendapunt, agenda en elke organisatie/commisie maken we een wordhoard.

# (misschien zitten sommigen in de ES response)
# doc_id een "schema:MediaObject"
# heeft een linkje dc:isReferencedBy
# linkje wijst naar (wss) meeting:AgendaItem
# AgendaItem heeft een schema:superEvent
# superEvent is van het type meeting:Meeting
# en een Meeting heeft een meeting:committee (de organisatie die we willen hebben.)

# schema:name is een readable naam (gebruik als wordhoard description voor agendapunt, agenda, org/commissie)




import os
import requests
import json

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

TAPI_ROOT_URL = "https://topics-dev.platform.co.nl/"
custom_topics_url = f"{TAPI_ROOT_URL}dev/custom/topic/"
custom_wordhoards_url = f"{TAPI_ROOT_URL}dev/custom/wordhoard/"
ID_ORI_URL = "https://id.openraadsinformatie.nl/"

# Login to TAPI
# login_url = "https://topics-dev.platform.co.nl/auth/login/"
# session = requests.Session()
#
# login_page = session.get(login_url)
# s2 = login_page.content.decode().split('csrfmiddlewaretoken')[1]
# csrfmiddlewaretoken = s2[9:].split("\'")[0]
#
# with open('credentials.json', 'r') as f:
#     credentials = json.load(f)
# username = credentials["username"]
# password = credentials["password"]
#
# res = session.post(
#     login_url,
#     headers={'Referer': 'https://topics-dev.platform.co.nl/auth/login/'},
#     data={
#         'csrfmiddlewaretoken': csrfmiddlewaretoken,
#         'username': username,
#         'password': password
#     }
# )
#
# if res.status_code == 200:
#     print("Login succesful")

def find_AgendaPunt_Agenda_and_Committee(ori_doc_id):
    pass


# Use Oauth2 instead
with open('oauth_credentials.json', 'r') as f:
    oauth_credentials = json.load(f)


def get_client(client_id, scope=None):
    return OAuth2Session(client=BackendApplicationClient(client_id=client_id), scope=scope)

def get_token(client, client_secret, scope):
    token_url = f"{TAPI_ROOT_URL}o/token/"
    return client.fetch_token(
        token_url=token_url,
        client_id=client.client_id,
        client_secret=client_secret,
        scope=scope
    )

def get_client_with_token(client_id, client_secret, scope=None):
    client = get_client(client_id, scope)
    get_token(client, client_secret, scope)
    return client

def post_with_client(client, url, data):
    return client.post(url, json=data)

def get_with_client(client, url):
    return client.get(url)


oauth_client = get_client_with_token(
    client_id=oauth_credentials['client_id'],
    client_secret=oauth_credentials['client_secret']
)

collected_glossarys = os.listdir('glossarys')


created_topics = {}


for gl in collected_glossarys[1:]:
    with open(f'glossarys/{gl}', 'r') as f:
        raw_data = json.load(f)

    doc_id = raw_data['id']
    doc_name = raw_data['doc_name']
    print(f"POSTing glossary of <{doc_name}> to <{custom_topics_url}>")

    # If the wordhoard accompanying this document already exist, we can skip this file.
    # Check this by querying /custom/wordhoard/
    res = get_with_client(client=oauth_client, url=custom_wordhoards_url)
    res_dict = json.loads(res.content.decode('utf-8'))
    custom_wordhoard_list = res_dict["items"]
    custom_wordhoard_names = [item['name'] for item in custom_wordhoard_list]
    intended_wordhoad_name = f"{doc_id}_definitions"

    if intended_wordhoad_name in custom_wordhoard_names:
        print("Already found a wordhoard corresponding to this document. Skipping this extracted glossary.")
        continue


    glossary = raw_data['glossary']
    topics = []
    for topic in glossary:
        topics.append({
            'canonical_name': topic,
            'description': glossary[topic],
            'sources': [raw_data['id']]
        })

    data = {
        "topics": topics
    }

    response = post_with_client(oauth_client, custom_topics_url, data=data)
    if response.ok:
        custom_topic_response_dictionary = json.loads(response.content.decode('utf-8'))
    else:
        print(response.status_code, response.text)
        input("custom topic POST error..")
        continue

    print(custom_topic_response_dictionary)
    for topic in custom_topic_response_dictionary['topics']:
        created_topics[topic['id']] = topic['canonical_name']
    input("input...")
    # break


    # Create the wordhoards
    # First the document wordhoard
    wordhoard_payload = {
        'topics': {},
        'description': f"Mined definitions for {doc_id}",
        'name': f"{doc_id}_definitions",
        'detection_settings': {
            'names': {
                'ignore_case': True
            }
        }
    }


    for topic in custom_topic_response_dictionary['topics']:
        #  Key to local_name mappings (local_name is None in our case)
        wordhoard_payload['topics'][topic['id']] = None

    # print(wordhoard_payload)

    response = post_with_client(oauth_client, custom_wordhoards_url, data=wordhoard_payload)
    if response.ok:
        custom_wordhoard_response_dictionary = json.loads(response.content.decode('utf-8'))
    else:
        print(response.status_code, response.text)
        input("wordhoard POST error...")
        continue

    print(custom_wordhoard_response_dictionary)

    input('input...')

    find_AgendaPunt_Agenda_and_Committee(ori_doc_id)






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




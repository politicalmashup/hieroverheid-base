import json

from oauth_helpers import get_with_client, get_client_with_token, delete_with_client, TAPI_ROOT_URL

custom_topics_url = f"{TAPI_ROOT_URL}dev/custom/topic/"
custom_wordhoards_url = f"{TAPI_ROOT_URL}dev/custom/wordhoard/"

with open('oauth_credentials.json', 'r') as f:
    oauth_credentials = json.load(f)

oauth_client = get_client_with_token(client_id=oauth_credentials['client_id'], client_secret=oauth_credentials['client_secret'])

input(f"This will delete all topics & wordhoards for this application <{oauth_credentials['client_id']}>. Press Enter to continue...")

# Get topics list
res = get_with_client(oauth_client, custom_topics_url)
res_dict = json.loads(res.content.decode('utf-8'))
topics = res_dict['topics']
print(f"Found {len(topics)} topics")

for topic in topics:
    id = topic['id']
    res = delete_with_client(oauth_client, custom_topics_url, id)
    if res.status_code != 204:
        print(f"DELETE not successful for topic: {id}")
    else:
        print(f"DELETE successful for topic: {id}")


# Get wordhoard list
res = get_with_client(oauth_client, custom_wordhoards_url)
res_dict = json.loads(res.content.decode('utf-8'))
wordhoards = res_dict['items']
print(f"Found {len(wordhoards)} wordhoards")

# Delete each wordhoard
for wordhoard in wordhoards:
    id = wordhoard['id']
    res = delete_with_client(oauth_client, custom_wordhoards_url, id)
    if res.status_code != 204:
        print(f"DELETE not successful for wordhoard: {id}")
    else:
        print(f"DELETE successful for wordhoard: {id}")
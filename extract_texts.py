import requests
import json

# Get PDFs matching seach query
url = "https://api.openraadsinformatie.nl/v1/elastic/ori_*/_search"
headers = {'content-type': 'application/json'}
with open('ori_query.json', 'rb') as f:
    data = f.read()

response = requests.post(
    url=url,
    data=data,
    headers=headers
)

response_dict = json.loads(response.content)
with open('ori_response.json','w') as f:
    json.dump(response_dict, f, indent=2)

number_of_hits = response_dict["hits"]["total"]["value"]
all_hits = response_dict["hits"]["hits"]

print(f"Found {number_of_hits} documents.")
cont = input('Do you want to download these documents and extract the text using TAPI? (y/n) ')








if (cont != 'y'):
    exit(0)

# Take only 1 while testing
# all_hits = all_hits[1:3]

#login to tapi
print("\nLogging in to TAPI...")
base_url = "https://topics-dev.platform.co.nl/dev/text/extract/"
login_url="https://topics-dev.platform.co.nl/auth/login/"
session = requests.Session()

login_page = session.get(
    login_url
)

s2 = login_page.content.decode().split('csrfmiddlewaretoken')[1]
csrfmiddlewaretoken = s2[9:].split("\'")[0]

with open('credentials.json', 'r') as f:
    credentials = json.load(f)

m_username = credentials["username"]
m_password = credentials["password"]

r = session.post(
    login_url,
    headers={'Referer': 'https://topics-dev.platform.co.nl/auth/login/'},
    data={
        'csrfmiddlewaretoken': csrfmiddlewaretoken,
        'username': m_username,
        'password': m_password
    }
)

print("Login succesful.\n")

texts = []

for hit in all_hits:
    if hit["_source"]["name"] in [entry["name"] for entry in texts]:
        ind = [entry["name"] for entry in texts].index(hit["_source"]["name"])
        if hit["_source"]["size_in_bytes"] == texts[ind]["size_in_bytes"]:
            print(f"x Already found {hit['_source']['name']}, skipping...")
            continue


    print(f"- Downloading {hit['_source']['name']}.pdf and extracting text...")
    # Write to disk
    document_url = hit["_source"]["url"]
    response = requests.get(document_url)
    with open('pdfs/' + hit["_source"]["name"] + '.pdf', 'wb') as f:
        f.write(response.content)

    # Extract text with TAPI
    url = hit["_source"]["url"]
    response = session.get(
        url=base_url,
        params={"url": url}
    )
    file_text = json.loads(response.content.decode())['file_text']

    texts.append({
        'id': hit["_source"]["@id"],
        "size_in_bytes": hit["_source"]["size_in_bytes"],
        'name': hit["_source"]["name"],
        'url': hit["_source"]["url"],
        'text': file_text
    })

with open('extracted_texts.json', 'w') as f:
    json.dump(texts, f, indent=2)



# Find begrippenlijst in these texts

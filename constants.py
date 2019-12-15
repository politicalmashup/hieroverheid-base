import os

from dotenv import load_dotenv

load_dotenv()
TAPI_ROOT_URL = os.getenv('TAPI_ROOT_URL', "https://topics-dev.platform.co.nl/")
if 'localhost' in TAPI_ROOT_URL:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

document_list_url = f"{TAPI_ROOT_URL}dev/document/"
custom_topics_url = f"{TAPI_ROOT_URL}dev/custom/topic/"
wordhoard_list_url = f"{TAPI_ROOT_URL}dev/custom/wordhoard/"
wordhoard_topics_url = f"{TAPI_ROOT_URL}dev/custom/wordhoard/%s/topics/"
ID_ORI_URL = "https://id.openraadsinformatie.nl/"
ES_ORI_URL = "https://api.openraadsinformatie.nl/v1/elastic/"

ORSI_FILTER = 'o*'

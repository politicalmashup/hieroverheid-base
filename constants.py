import os

from dotenv import load_dotenv

load_dotenv()
TAPI_CLIENT_ID = os.getenv('TAPI_CLIENT_ID')
TAPI_CLIENT_SECRET = os.getenv('TAPI_CLIENT_SECRET')
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


"""
    Copyright 2019 Hendrik Grondijs, Alex Olieman <alex@olieman.net>

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

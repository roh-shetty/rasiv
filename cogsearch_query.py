import os
import urllib
import requests
import random
from collections import OrderedDict
from IPython.display import display, HTML

from dotenv import load_dotenv
load_dotenv("credentials.env")

def cog_query(service_name,index_name,query):
    # Setup the Payloads header
    headers = {'Content-Type': 'application/json','api-key': os.environ['AZURE_SEARCH_KEY']}
    service_name = "cogs-ras"
    index_name = "cog-ras-index"

    url = 'https://{}.search.windows.net/indexes/{}/docs'.format(service_name, index_name)
    url += '?api-version={}'.format(os.environ['AZURE_SEARCH_API_VERSION'])
    url += '&search={}'.format(query)
    url += '&$count=true'
    url += '&highlight=merged_text'

    resp = requests.get(url, headers=headers)

    print(url)
    print(resp.status_code)        

    search_results = resp.json()
    print(search_results)
    return search_results

if __name__ == "__main__":
    service_name = ""
    index_name = ""
    query=""
    cog_query(service_name, index_name,query)





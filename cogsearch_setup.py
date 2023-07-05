from azure.core.credentials import AzureKeyCredential
from langchain.document_loaders import DirectoryLoader
from azure.storage.blob import BlobServiceClient
import os
import json
import requests
from dotenv import load_dotenv
load_dotenv("credentials.env")


def cog_setup(query):
    # Blob Storage Connection -- To read files
    BLOB_CONTAINER_NAME = "rasiv-container"
    DATASOURCE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=rasivc;AccountKey=LbHSGFe6qKMNkxlL9AC2E7vuGptj1S8MVB01/RLMy7X2AowHzIjkpVwNgoYOgJvdT5ZyZspm4JAo+ASttSbY9g==;EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(DATASOURCE_CONNECTION_STRING)
    raw_container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
    docUrlBase = raw_container_client.primary_endpoint
    

    print("\nProcessing Blobs:")

    blob_list = raw_container_client.list_blobs()

    for blob in blob_list:
        docUrl =  f'{docUrlBase}/{blob.name}'
        local_file = f"./data/rasiv/original/{blob.name}"
        with open(local_file,"wb") as f:
            data = raw_container_client.download_blob(blob)
            data.readinto(f)
    path_to_document = './data/rasiv/original/'
    loader = DirectoryLoader(path_to_document)
    documents = loader.load()
    print(documents)



    # Setup the Payloads header
    headers = {'Content-Type': 'application/json','api-key': "pPWJMGYrm5vtAJWDdnPvcKqf44mF89xAFxcABlepsaAzSeAiPozQ"}
    params = {'api-version': "https://cogs-ras.search.windows.net"}

    service_name = "cogs-ras"
    api_version = "2019-05-06"

    headers = {
        'Content-Type': 'application/json',
        'api-key': 'pPWJMGYrm5vtAJWDdnPvcKqf44mF89xAFxcABlepsaAzSeAiPozQ'
    }

    # The following code sends the json paylod to Azure Search engine to create the Datasource
    datasource_name = "blob-datasource"
    uri = f"https://{service_name}.search.windows.net/datasources?api-version={api_version}"

    datasource_payload = {
        "name": datasource_name,
        "description": "RASIV files to demonstrate cognitive search capabilities.",
        "type": "azureblob",
        "credentials": {
            "connectionString": DATASOURCE_CONNECTION_STRING
        },
        "container": {
            "name": BLOB_CONTAINER_NAME
        }
    }

    resp = requests.post(uri, headers=headers, data=json.dumps(datasource_payload))
    print(resp.status_code)
    print(resp.ok)

    # Create a skillset
    import os
    skillset_payload = {
        "description": "Extract entities, detect language and extract key-phrases",
        "skills":
        [
            {
                "@odata.type": "#Microsoft.Skills.Vision.OcrSkill",
                "description": "Extract text (plain and structured) from image.",
                "context": "/document/normalized_images/*",
                "defaultLanguageCode": "en",
                "detectOrientation": True,
                "inputs": [
                    {
                    "name": "image",
                    "source": "/document/normalized_images/*"
                    }
                ],
                    "outputs": [
                    {
                    "name": "text",
                    "targetName" : "images_text"
                    }
                ]
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.MergeSkill",
                "description": "Create merged_text, which includes all the textual representation of each image inserted at the right location in the content field. This is useful for PDF and other file formats that supported embedded images.",
                "context": "/document",
                "insertPreTag": " ",
                "insertPostTag": " ",
                "inputs": [
                    {
                    "name":"text", "source": "/document/content"
                    },
                    {
                    "name": "itemsToInsert", "source": "/document/normalized_images/*/images_text"
                    },
                    {
                    "name":"offsets", "source": "/document/normalized_images/*/contentOffset"
                    }
                ],
                "outputs": [
                    {
                    "name": "mergedText", 
                    "targetName" : "merged_text"
                    }
                ]
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.LanguageDetectionSkill",
                "context": "/document",
                "description": "If you have multilingual content, adding a language code is useful for filtering",
                "inputs": [
                    {
                    "name": "text",
                    "source": "/document/content"
                    }
                ],
                "outputs": [
                    {
                    "name": "languageCode",
                    "targetName": "language"
                    }
                ]
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.SplitSkill",
                "context": "/document",
                "textSplitMode": "pages",
                "maximumPageLength": 5000, # 5000 is default
                "defaultLanguageCode": "en",
                "inputs": [
                    {
                        "name": "text",
                        "source": "/document/content"
                    },
                    {
                        "name": "languageCode",
                        "source": "/document/language"
                    }
                ],
                "outputs": [
                    {
                        "name": "textItems",
                        "targetName": "pages"
                    }
                ]
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.KeyPhraseExtractionSkill",
                "context": "/document/pages/*",
                "maxKeyPhraseCount": 2,
                "defaultLanguageCode": "en",
                "inputs": [
                    {
                        "name": "text", 
                        "source": "/document/pages/*"
                    },
                    {
                        "name": "languageCode",
                        "source": "/document/language"
                    }
                ],
                "outputs": [
                    {
                        "name": "keyPhrases",
                        "targetName": "keyPhrases"
                    }
                ]
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.V3.EntityRecognitionSkill",
                "context": "/document/pages/*",
                "categories": ["Person", "Location", "Organization", "DateTime", "URL", "Email"],
                "minimumPrecision": 0.5, 
                "defaultLanguageCode": "en",
                "inputs": [
                    {
                        "name": "text", 
                        "source":"/document/pages/*"
                    },
                    {
                        "name": "languageCode",
                        "source": "/document/language"
                    }
                ],
                "outputs": [
                    {
                        "name": "persons", 
                        "targetName": "persons"
                    },
                    {
                        "name": "locations", 
                        "targetName": "locations"
                    },
                    {
                        "name": "organizations", 
                        "targetName": "organizations"
                    },
                    {
                        "name": "dateTimes", 
                        "targetName": "dateTimes"
                    },
                    {
                        "name": "urls", 
                        "targetName": "urls"
                    },
                    {
                        "name": "emails", 
                        "targetName": "emails"
                    }
                ]
            }
        ],
        "cognitiveServices": {
            "@odata.type": "#Microsoft.Azure.Search.CognitiveServicesByKey",
            "description": os.environ['COG_SERVICES_NAME'],
            "key": os.environ['COG_SERVICES_KEY']
        }
    }

    skillset_name = 'cog-ras-skillset'
    uri = f"https://{service_name}.search.windows.net/skillsets/{skillset_name}?api-version=os.environ{['AZURE_SEARCH_API_VERSION']}"
    resp = requests.put(uri, headers=headers, data=json.dumps(skillset_payload))
    print(resp.status_code)
    print(resp.ok)


    # Create an index
    # Queries operate over the searchable fields and filterable fields in the index
    index_name = 'cog-ras-index'
    index_payload = {
        "name": index_name,
        "fields": [
            {"name": "id", "type": "Edm.String", "key": "true", "searchable": "false", "retrievable": "true", "sortable": "false", "filterable": "false","facetable": "false"},
            {"name": "title", "type": "Edm.String", "searchable": "true", "retrievable": "true", "facetable": "false", "filterable": "true", "sortable": "false"},
            {"name": "content", "type": "Edm.String", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "false","facetable": "false"},
            {"name": "language", "type": "Edm.String", "searchable": "false", "retrievable": "true", "sortable": "true", "filterable": "true", "facetable": "true"},
            {"name": "pages","type": "Collection(Edm.String)", "searchable": "false", "retrievable": "true", "sortable": "false", "filterable": "false", "facetable": "false"},
            {"name": "images_text", "type": "Collection(Edm.String)", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "false", "facetable": "false"},
            {"name": "keyPhrases", "type": "Collection(Edm.String)", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "true", "facetable": "true"},
            {"name": "persons", "type": "Collection(Edm.String)", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "false", "facetable": "false"},
            {"name": "locations", "type": "Collection(Edm.String)", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "true", "facetable": "true"},
            {"name": "organizations", "type": "Collection(Edm.String)", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "true", "facetable": "true"},
            {"name": "dateTimes", "type": "Collection(Edm.String)", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "false", "facetable": "false"},
            {"name": "urls", "type": "Collection(Edm.String)", "searchable": "false", "retrievable": "true", "sortable": "false", "filterable": "false", "facetable": "false"},
            {"name": "emails", "type": "Collection(Edm.String)", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "true", "facetable": "false"},
            {"name": "metadata_storage_name", "type": "Edm.String", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "false", "facetable": "false"},
            {"name": "metadata_storage_path", "type": "Edm.String", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "false", "facetable": "false"}
        ],
        "semantic": {
        "configurations": [
            {
            "name": "my-semantic-config",
            "prioritizedFields": {
                "titleField": 
                    {
                        "fieldName": "title"
                    },
                "prioritizedContentFields": [
                    {
                        "fieldName": "content"
                    }
                    ]
            }
            }
        ]
        }
    }

    index_name = 'cog-ras-index'
    uri = f"https://{service_name}.search.windows.net/indexes/{index_name}?api-version={api_version}"

    resp = requests.put(uri, headers=headers, data=json.dumps(index_payload))
    print(resp.status_code)
    print(resp.ok)

    # Create an indexer
    indexer_name = 'cog-ras-indexer'
    indexer_payload = {
        "name": indexer_name,
        "dataSourceName": datasource_name,
        "targetIndexName": index_name,
        "skillsetName": skillset_name,
        "schedule" : { "interval" : "PT2H"}, # How often do you want to check for new content in the data source
        "fieldMappings": [
            {
            "sourceFieldName" : "metadata_storage_path",
            "targetFieldName" : "id",
            "mappingFunction" : { "name" : "base64Encode" }
            },
            {
            "sourceFieldName" : "metadata_title",
            "targetFieldName" : "title"
            }
        ],
        "outputFieldMappings":
        [
            {
                "sourceFieldName": "/document/content",
                "targetFieldName": "content"
            },
            {
                "sourceFieldName": "/document/pages/*",
                "targetFieldName": "pages"
            },
            {
                "sourceFieldName" : "/document/normalized_images/*/images_text",
                "targetFieldName" : "images_text"
            },
            {
                "sourceFieldName": "/document/language",
                "targetFieldName": "language"
            },
            {
                "sourceFieldName": "/document/pages/*/keyPhrases/*",
                "targetFieldName": "keyPhrases"
            },
            {
            "sourceFieldName" : "/document/pages/*/persons/*", 
            "targetFieldName" : "persons"
            },
            {
            "sourceFieldName" : "/document/pages/*/locations/*", 
            "targetFieldName" : "locations"
            },
            {
                "sourceFieldName": "/document/pages/*/organizations/*",
                "targetFieldName": "organizations"
            },
            {
                "sourceFieldName": "/document/pages/*/dateTimes/*",
                "targetFieldName": "dateTimes"
            },
            {
                "sourceFieldName": "/document/pages/*/urls/*",
                "targetFieldName": "urls"
            },
            {
                "sourceFieldName": "/document/pages/*/emails/*",
                "targetFieldName": "emails"
            }
        ],
        "parameters":
        {
            "maxFailedItems": -1,
            "maxFailedItemsPerBatch": -1,
            "configuration":
            {
                "dataToExtract": "contentAndMetadata",
                "imageAction": "generateNormalizedImages"
            }
        }
    }

    indexer_name = 'cog-ras-indexer'
    uri = f"https://{service_name}.search.windows.net/indexers/{indexer_name}?api-version={api_version}"

    resp = requests.put(uri, headers=headers, data=json.dumps(indexer_payload))
    print(resp.status_code)
    print(resp.ok)

    return service_name,index_name


if __name__ == "__main__":
    query =""
    cog_setup(query)








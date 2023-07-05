from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
import os
import json
import pandas as pd
import requests
from dotenv import load_dotenv
load_dotenv("credentials.env")





class feedback:
    def __init__(self,query,summary_response):
        self.query = query
        self.summary_response = summary_response
        #self.fb_text = fb_text
        #self.fb_doc = fb_doc
        #self.fb_flag = fb_flag
        
    def blob_connection(self):
        # Blob Storage Connection -- To write SME feedback docs to blob storage
        BLOB_CONTAINER_NAME = "rasiv-container"
        DATASOURCE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=rasivc;AccountKey=LbHSGFe6qKMNkxlL9AC2E7vuGptj1S8MVB01/RLMy7X2AowHzIjkpVwNgoYOgJvdT5ZyZspm4JAo+ASttSbY9g==;EndpointSuffix=core.windows.net"
        blob_service_client = BlobServiceClient.from_connection_string(DATASOURCE_CONNECTION_STRING)
        raw_container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        docUrlBase = raw_container_client.primary_endpoint
        return raw_container_client


      
    def blob_fb_entry(self):
        head = ["query","summarized_response"] #"feedback_text","feedback_doc","feedback_flag"]
        value = [[query, summary_response]] #,fb_text,fb_doc,fb_flag]

        if summary_response != "":
            #fb_flag = 'Y'
            df = pd.DataFrame(value,index= head,columns = head)
            output = df.to_csv(index=False,encoding= "utf-8")
            print(output)
            blob_client = feedback_sme.blob_connection()
            blob_client.get_blob_client("feedback.csv")
            # upload data
            blob_client.upload_blob(name="feedback",data=output, blob_type="BlockBlob")
        else:
            #fb_flag = 'N'
            df = pd.DataFrame(value,columns = head)
            output = df.to_csv(index=False,encoding= "utf-8")
            print(output)
            blob_client = feedback_sme.blob_connection()
            blob_client.get_blob_client("feedback.csv")
            # upload data
            blob_client.upload_blob(output, blob_type="BlockBlob")
        return output


if __name__ == "__main__":
    query ="cc"
    summary_response ="dddddd"
    #fb_text=""
    #fb_doc=""
    #fb_flag=""
    
    feedback_sme = feedback(query,summary_response) 
    feedback_sme.blob_fb_entry()
    
        


        







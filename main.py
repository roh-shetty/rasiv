import os
from importlib import import_module
import pandas as pd
import openai
from langchain.llms import AzureOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.base import Embeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings import CohereEmbeddings
from langchain.vectorstores import FAISS
from openai.embeddings_utils import get_embedding, cosine_similarity

from dotenv import load_dotenv
load_dotenv("credentials.env")
openai_api_key = os.getenv("OPENAI_API_KEY")

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi.staticfiles import StaticFiles
import re

app = FastAPI()
security = HTTPBasic()

#templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


openai.api_type = "azure"
openai.api_version = "2022-12-01"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")    


@app.get("/generate/{project}", response_class=HTMLResponse)
def home(request: Request, project: str):
    
    from generate_embeddings_lc import create_vectors
    ret = create_vectors(project)

    final_msg = f"Embeddings created for {project}<br>"
    final_msg += ret
    return final_msg

@app.get("/cogsearch/{query}", response_class=HTMLResponse)
def home(request: Request, cogsearch: str, query:str):
    service_name = ""
    index_name = ""

    from cogsearch_setup import cog_setup
    from cogsearch_query import cog_query
    service_name,index_name = cog_setup(query)

    search_result = cog_query(service_name,index_name,query)
    final_msg = f"Search Results for the query:\n {search_result}<br>"
    return final_msg


query = ""
response_summary = ""
@app.get("/rasiv/{query_text}", response_class=HTMLResponse)
async def home(request: Request,query_text: str, response_summary_text: str):
    query =""
    response_summary =""
    item = {"query": query, "response_summary": response_summary}
    query = query_text
    response_summary = response_summary_text
    #var_list.append(query)
    #var_list.append(response_summary)
    from feedback_sme import feedback
    feedback.blob_fb_entry(query,response_summary)
    return query,response_summary






    
if __name__ == "__main__":
    uvicorn.run("main:app")
import os
from importlib import import_module
import pandas as pd
import openai
from langchain.llms import AzureOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.base import Embeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from openai.embeddings_utils import get_embedding, cosine_similarity

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi.staticfiles import StaticFiles
import re

app = FastAPI()
security = HTTPBasic()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


DELIMITER = "\n* "
MAX_SECTION_LENGTH = 1500
TEMPERATURE = 0.0
MAX_TOKENS = 1000
TOP_P = 0.7
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0
BEST_OF = 1
STOP = None
USER_CREDENTIALS = {"username": os.getenv("DEMO_USERNAME"), "password": os.getenv("DEMO_PASSWORD")}
openai.api_type = "azure"
openai.api_version = "2022-12-01"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")    

@app.get("/", response_class=HTMLResponse)
def home(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    valid_username = USER_CREDENTIALS["username"]
    valid_password = USER_CREDENTIALS["password"]
    if not (credentials.username == valid_username and credentials.password == valid_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/search/{project}", response_class=HTMLResponse)
def search_docs(request: Request, project: str, credentials: HTTPBasicCredentials = Depends(security)):
    valid_username = USER_CREDENTIALS["username"]
    valid_password = USER_CREDENTIALS["password"]
    if not (credentials.username == valid_username and credentials.password == valid_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return templates.TemplateResponse("search.html", {"request": request, "project": project})

@app.get("/chat/{project}", response_class=HTMLResponse)
def home(request: Request, project: str, credentials: HTTPBasicCredentials = Depends(security)):
    valid_username = USER_CREDENTIALS["username"]
    valid_password = USER_CREDENTIALS["password"]
    if not (credentials.username == valid_username and credentials.password == valid_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return templates.TemplateResponse("index.html", {"request": request, "project": project})


def load_qa(project):
    from langchain.prompts import PromptTemplate

    prompt_template = """I want you to act like an insurance provider. Please provide the answer with all the inclusions and exclusions corresponding to the services I ask about. Answer all the questions asked. Provide a detailed answer to the below question in a minimum of three to four sentences, as truthfully as possible in as human of a way, or answer based on the keyword and the keyword context provided below, and if the answer is not contained within the text below, say "I don't know."\n\nContext:\n

    {context}

    Question: {question}
    Answer:"""
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    chain_type_kwargs = {"prompt": PROMPT}
    VECTOR_STORE_PATH = "./data/"+project+"/storage/"
    
    embeddings: Embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002", chunk_size=1
    )
    new_db = FAISS.load_local(folder_path=VECTOR_STORE_PATH, embeddings=embeddings)
    retriever = new_db.as_retriever()
    retriever.search_kwargs['distance_metric'] = 'cos'
    retriever.search_kwargs['k'] = 3
    llm = AzureOpenAI(deployment_name="text-davinci-003", model_name="text-davinci-003", 
        temperature=TEMPERATURE, max_tokens=MAX_TOKENS, top_p=TOP_P, 
        frequency_penalty=FREQUENCY_PENALTY, presence_penalty=PRESENCE_PENALTY, best_of=BEST_OF,
        model_kwargs={
            "api_key": openai.api_key,
            "api_base": openai.api_base,
            "api_type": openai.api_type,
            "api_version": openai.api_version
        })
    qa = RetrievalQA.from_chain_type(
        llm=llm, 
        chain_type="stuff", 
        retriever=retriever, 
        chain_type_kwargs=chain_type_kwargs, 
        return_source_documents=True)
    return llm, qa

@app.get("/getChatBotResponse_project")
def get_bot_response_project(msg: str, project: str, with_resp: bool = True):
    ret = {}
    ret["query"] = msg
    llm, qa = load_qa(project)
    docs = qa({"query": msg})
    d = docs["source_documents"]

    repl = "NewCo"
    subs = "anthem"
    subs = ["anthem", "humana"]
    # join the list of substrings with a pipe separator to create a regex pattern
    pattern = '|'.join(map(re.escape, subs))
    # regex used for ignoring cases and replacing all substrings
    res = re.sub('(?i)'+pattern, lambda m: repl, docs['result'])
    ret['result']  = res

    if docs['result'].strip().strip('\n') == "I don't know." :
        ret['Flag'] = 'True'
    else:
        ret['Flag'] = 'False'
    if with_resp:
        context_list = []
        for record in d:
            pdf_string = os.path.basename(record.metadata['file_path'])
            pdf = 'File: ' + str(pdf_string) + '<br/> '  + 'Page: ' + str(record.metadata['page_number']) 
            context_list.append(pdf)
        ret['Pdf_list'] = context_list
    print(ret)
    return ret


@app.get("/generate/{project}", response_class=HTMLResponse)
def home(request: Request, project: str, credentials: HTTPBasicCredentials = Depends(security)):
    valid_username = USER_CREDENTIALS["username"]
    valid_password = USER_CREDENTIALS["password"]
    if not (credentials.username == valid_username and credentials.password == valid_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    from generate_embeddings_lc import create_vectors
    ret = create_vectors(project)

    final_msg = f"Embeddings created for {project}<br>"
    final_msg += ret
    return final_msg


@app.get("/evaluate/{project}", response_class=HTMLResponse)
def home(request: Request, project: str, credentials: HTTPBasicCredentials = Depends(security)):
    valid_username = USER_CREDENTIALS["username"]
    valid_password = USER_CREDENTIALS["password"]
    if not (credentials.username == valid_username and credentials.password == valid_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    from langchain.evaluation.qa import QAEvalChain
    final_msg = ""

    module_name = f"data.{project}.evaluate.questions"
    module = import_module(module_name)
    examples = module.examples

    llm, qa = load_qa(project)
    predictions = qa.apply(examples)

    eval_chain = QAEvalChain.from_llm(llm)
    graded_outputs = eval_chain.evaluate(examples, predictions)

    for i, eg in enumerate(examples):
        final_msg += f"Example {i}:<br>"
        final_msg += "Question: " + predictions[i]['query'] + "<br>"
        final_msg += "Real Answer: " + predictions[i]['answer'] + "<br>"
        final_msg += "Predicted Answer: " + predictions[i]['result'] + "<br>"
        final_msg += "Predicted Grade: " + graded_outputs[i]['text'] + "<br><br>"

    
    return final_msg



if __name__ == "__main__":
    uvicorn.run("main:app")
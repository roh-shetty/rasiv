import os
import openai
from langchain.llms import AzureOpenAI
from langchain.embeddings import OpenAIEmbeddings
from llama_index import LangchainEmbedding
from llama_index import (
    GPTVectorStoreIndex,
    GPTEmptyIndex,
    LLMPredictor,
    PromptHelper,
    ServiceContext
)
import logging
import sys
from llama_index import download_loader
from llama_index.tools.query_engine import QueryEngineTool
from llama_index.query_engine.router_query_engine import RouterQueryEngine
from llama_index.selectors.llm_selectors import LLMSingleSelector

openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_version = "2022-12-01"

llm = AzureOpenAI(deployment_name='text-davinci-003',model_name='text-davinci-003', temperature=0.0, model_kwargs={
    "api_key": openai.api_key,
    "api_base": openai.api_base,
    "api_type": openai.api_type,
    "api_version": openai.api_version,
})


llm_predictor = LLMPredictor(llm=llm)

embedding_llm = LangchainEmbedding(
    OpenAIEmbeddings(
        model="text-embedding-ada-002",
        deployment="MB_Embedding_Model",
        openai_api_key= openai.api_key,
        openai_api_base=openai.api_base,
        openai_api_type=openai.api_type,
        openai_api_version=openai.api_version
    ),
    embed_batch_size=1,
)


service_context = ServiceContext.from_defaults(
    llm_predictor=llm_predictor,
    embed_model=embedding_llm
)

vector_index = VectorStoreIndex.from_documents(documents, service_context=service_context)

query_engine1 = vector_index.as_query_engine()
response = query_engine1.query("To whom should RA parts orders be submitted to?")
#display(Markdown(f"<b>{response}</b>"))





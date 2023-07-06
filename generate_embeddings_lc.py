import os, logging, time
import json
import openai
from langchain.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain.document_loaders.base import BaseLoader
from langchain.embeddings.base import Embeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import TextSplitter, TokenTextSplitter
from langchain.vectorstores import FAISS, VectorStore
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def create_vectors(project):
    start_time = time.time()
    res = ""

    # STATIC PATHS
    DOCUMENT_PATH: str = "./data/"+project+"/originals/"
    VECTOR_STORE_PATH: str = "./data/"+project+"/storage/"
    OPENAI_EMBEDDING_MODEL_NAME: str = "text-embedding-ada-002"

    # INDEXING PARAMETERS
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 20

    # OPENAI API PARAMETERS
    openai.api_type = "azure"
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai.api_version = "2022-12-01"
    openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")

    print("Loading Directory...")
    loader: BaseLoader = DirectoryLoader(
        DOCUMENT_PATH, glob="*.pdf", loader_cls=PyMuPDFLoader, recursive=True
    )

    print("Splitting into Chunks...")
    text_splitter: TextSplitter = TokenTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )

    print("Now calling load_and_split...")
    documents = loader.load_and_split(text_splitter=text_splitter)
    print("Documents loaded...")

    print("Now calling embeddings...")
    embeddings: Embeddings = OpenAIEmbeddings(
        model=OPENAI_EMBEDDING_MODEL_NAME, chunk_size=1
    )
    print("Embeddings done...")


    vector_store: VectorStore = FAISS.from_documents(
        documents=documents, embedding=embeddings
    )
    vector_store.save_local(folder_path=VECTOR_STORE_PATH)
    print("Embeddings saved to " + VECTOR_STORE_PATH)

    end_time = time.time()

    time_taken = end_time - start_time
    minutes, seconds = divmod(time_taken, 60)
    time_msg = f"Time taken: {int(minutes)} minutes {int(seconds)} seconds"
    print(time_msg)

    return time_msg


if __name__ == "__main__":
    create_vectors("pepsico")
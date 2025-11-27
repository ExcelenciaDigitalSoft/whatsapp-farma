from langchain_community.document_loaders import PyPDFLoader  # type: ignore
from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
from langchain_community.embeddings import OllamaEmbeddings  # type: ignore
from langchain_community.vectorstores import Chroma  # type: ignore
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def indexar_pdfs(carpeta_pdfs: str = "pdfs"):
    """Carga e indexa todos los PDFs de la carpeta."""
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_HOST)
    vector_store = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

    for archivo in os.listdir(carpeta_pdfs):
        if archivo.endswith(".pdf"):
            path = os.path.join(carpeta_pdfs, archivo)
            loader = PyPDFLoader(path)
            docs = loader.load()

            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_documents(docs)
            vector_store.add_documents(chunks)
            print(f"✅ {archivo} indexado correctamente")

    vector_store.persist()

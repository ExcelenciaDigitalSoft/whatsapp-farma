from langchain_community.document_loaders import PyPDFLoader  # type: ignore
from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
from langchain_ollama import OllamaEmbeddings  # type: ignore
from langchain_chroma import Chroma  # type: ignore
from langchain_openai import OpenAIEmbeddings  # type: ignore
import os
import time

PERSIST_DIR = "chroma_db"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def procesar_pdf(pdf_path: str):
    """Extrae texto del PDF, lo divide en chunks y los indexa en Chroma de forma segura."""
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=400)
    chunks = splitter.split_documents(docs)

    print(f"Total de chunks a indexar {len(chunks)}")

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    vectorstore = Chroma(embedding_function=embeddings, persist_directory=PERSIST_DIR)

    batch_size = 16
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        try:
            vectorstore.add_documents(batch)
            print(f"Procesado lote {i//batch_size + 1} de {((len(chunks)-1)//batch_size) + 1}")
            time.sleep(0.5)  # Espera corta para evitar saturar Ollama
        except Exception as e:
            print(f"⚠️ Error procesando lote {i//batch_size + 1}: {e}")
            time.sleep(2)
    
    print("✅ PDF indexado y guardado en Chroma.")
    return vectorstore
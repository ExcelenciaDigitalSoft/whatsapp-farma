from dotenv import load_dotenv
load_dotenv()
from langchain_ollama import OllamaLLM, OllamaEmbeddings  # type: ignore
from langchain_chroma import Chroma  # type: ignore
from langchain.chains import RetrievalQA, ConversationalRetrievalChain  # type: ignore
from langchain.prompts import PromptTemplate  # type: ignore
from langchain.memory import ConversationBufferMemory  # type: ignore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # type: ignore
from app.services.chattigo_service import enviar_a_agente  # type: ignore
import os
import logging

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    openai_api_key=OPENAI_API_KEY
)

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

PERSIST_DIR = "chroma_db"

qa_chain = None
_session_chains = {}

def _build_retriever_from_persist():
    if not os.path.exists(PERSIST_DIR):
        return None
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
    )
    # subir a k=10 o 12 mejora mucho la precisión
    return vectorstore.as_retriever(search_kwargs={"k": 10})

def inicializar_chain_si_existe():
    global qa_chain
    retriever = _build_retriever_from_persist()
    if retriever is None:
        print("⚠️ No se encontró base de datos Chroma. No se inicializa el chain.")
        return
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        verbose=False
    )
    print("✅ Chain de QA inicializado correctamente desde Chroma.")

prompt_template = """
Eres un asistente de atención al cliente de Eventos y Viajes.
Tu única fuente de información es el siguiente documento.
Siempre debes responder en primera persona plural (nosotros, nuestro, etc.) y de forma amable.
Debes responder exclusivamente con la información que contenga.
Debes priorizar la información relacionada con el colegio del usuario, si se especifica en el contexto.
Si la pregunta no está respondida explícitamente, responde exactamente:
"No tengo esa información en este momento."

Contexto del documento:
{context}

Pregunta del usuario:
{question}

Respuesta:
"""

def crear_chain_para_pdf(vectorstore: Chroma):
    global qa_chain
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={
            "prompt": PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
        }
    )
    _session_chains.clear()
    print("✅ Chain RAG configurado con el nuevo pdf.")


async def preguntar_pdf(pregunta: str, msisdn: str | None = None, nombre_usuario: str | None = None):
    global qa_chain
    if qa_chain is None:
        return "⚠️ No se ha cargado ningún PDF aún."
    
    try:
        prompt = (
            "Sos un asistente de atención al cliente de *Eventos Egresados*. "
            "Tu única fuente de información es el documento de preguntas frecuentes cargado en el sistema. "
            "Cada sección del documento contiene preguntas y respuestas concretas. "
            "Debes responder únicamente con información textual proveniente del documento, "
            "sin agregar ni inventar detalles. "
            "Si la pregunta es ambigua (por ejemplo, 'cuánto cuesta la cena'), "
            "intentá inferir el contexto más probable según la información del documento "
            "(por ejemplo, año o tipo de evento) y respondé con los valores correctos. "
            "Incluí montos, fechas, horarios o contactos tal como aparecen en el texto original. "
            "Usá un tono amable, natural y cercano (por ejemplo: 'Podés...', 'Te recomendamos...', 'Atendemos de...'). "
            "Siempre respondé en español y en primera persona plural (nosotros). "
            "Si no encontrás información sobre el tema, respondé exactamente: "
            "'No tengo esa información disponible en este momento.'\n\n"
            f"Pregunta: {pregunta}"
        )
         
        result = qa_chain.invoke({"query": prompt})
        answer = result.get("result", "").strip()

        if not answer:
            return "⚠️ No pude generar respuesta ahora mismo. Intenta nuevamente."
        
        replacements = {
            "nosotros atendemos": "atendemos",
            "Nosotros atendemos": "Atendemos",
            "ellos atienden": "atendemos",
            "abren": "abrimos",
            "Abren": "Abrimos",
            "pueden venir": "podés venir",
            "ustedes pueden": "podés",
        }
        for old, new in replacements.items():
            answer = answer.replace(old, new)

        if "No tengo esa información disponible en este momento" in answer:
            logger.info("Derivando conversación a un agente humano...")

            if msisdn:
                try:
                    await enviar_a_agente(
                        msisdn=msisdn,
                        mensaje="Te voy a derivar con un agente humano para que pueda ayudarte mejor.",
                        nombre_usuario=nombre_usuario,
                    )
                    return "Derivado a un agente humano. En breve te atenderán."
                except Exception as e:
                    logger.error(f"Error al derivar a agente: {e}")
                    return "⚠️ No tengo esa información y todos nuestros agentes estan ocupados. Por favor, intentá más tarde"
        
        return answer
    

    except Exception as e:
        print(f"❌ Error en qa_chain.invoke(): {e}")
        return "⚠️ No pude generar respuesta ahora mismo. Intenta nuevamente."

def _create_session_chain(session_id: str) -> ConversationalRetrievalChain | None:
    """Crea un chain conversacional persistente."""
    if session_id in _session_chains:
        return _session_chains[session_id]

    retriever = _build_retriever_from_persist()
    if retriever is None:
        return None

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    conv_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=False,
        verbose=False
    )

    _session_chains[session_id] = conv_chain
    return conv_chain

def chat(session_id: str, pregunta: str) -> str:
    conv = _create_session_chain(session_id)
    if conv is None:
        return "⚠️ No se ha cargado ningún PDF aún."

    result = conv.invoke({
        "question": (
            pregunta +
            " (responde solo con información del documento en español, de forma natural y concisa)"
        )
    })
    return result["answer"]
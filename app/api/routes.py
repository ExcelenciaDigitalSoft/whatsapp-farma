from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from app.services.pdf_service import procesar_pdf
from app.services.langchain_service import preguntar_pdf, crear_chain_para_pdf, chat
from app.services.webhook_service import procesar_mensaje
from app.models.whatsapp import WebhookPayload
import logging

router = APIRouter()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Sube un PDF, lo procesa e indexa como el documento activo."""
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")
    try:
        path = f"temp_{file.filename}"
        with open(path, "wb") as f:
            f.write(await file.read())

        vectorstore = procesar_pdf(path)
        crear_chain_para_pdf(vectorstore)

        return {"message": f"✅ PDF '{file.filename}' procesado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ask-pdf")
async def ask_pdf(q: str):
    """
    Permite hacer una pregunta sobre el último PDF subido.
    """
    q_original = q
    q = (
        q
        + " (responde en español, de forma natural, amable y en primera persona plural, "
          "como si fueras parte del equipo de Esteban Vazquez Eventos)"
    )

    # Llamada con await si la función es asíncrona
    from inspect import iscoroutinefunction
    if iscoroutinefunction(preguntar_pdf):
        respuesta = await preguntar_pdf(q)
    else:
        respuesta = preguntar_pdf(q)

    return {"pregunta": q_original, "respuesta": respuesta}



@router.post("/api/webhook")
async def webhook(payload: dict = Body(...)):
    """
    Endpoint para recibir mensajes de WhatsApp a través de Chattigo.
    """
    try:
        respuesta = await procesar_mensaje(payload)
        return respuesta
    except Exception as e:
        logger.error(f"Error al procesar el webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
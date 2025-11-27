import os
import httpx
import uuid
import logging
from typing import Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CHATTIGO_LOGIN_URL = os.getenv("CHATTIGO_LOGIN_URL")
CHATTIGO_MESSAGE_URL = os.getenv("CHATTIGO_MESSAGE_URL")
CHATTIGO_USERNAME = os.getenv("CHATTIGO_USERNAME")
CHATTIGO_PASSWORD = os.getenv("CHATTIGO_PASSWORD")
EVE_WHATSAPP_NUMBER = os.getenv("EVE_WHATSAPP_NUMBER")

#Cache del token
_token_cache: dict[str, Any] = {"access_token": None, "expires_at": None}

async def get_chattigo_token() -> str | None:
    """
    Obtiene y cachea un token de acceso válido para Chattigo.
    Si el token expira, genera uno nuevo automáticamente.
    """
    now = datetime.utcnow()
    if _token_cache["access_token"] and _token_cache["expires_at"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    try:
        if not CHATTIGO_LOGIN_URL:
            raise ValueError("CHATTIGO_LOGIN_URL not configured")
        payload = {"username": CHATTIGO_USERNAME, "password": CHATTIGO_PASSWORD}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(CHATTIGO_LOGIN_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")

            if not token:
                raise ValueError("No se recibió token en la respuesta de Chattigo")
            
            # Guardar token con vencimiento de 50 minutos
            _token_cache["access_token"] = token
            _token_cache["expires_at"] = now + timedelta(minutes=50)
            logger.info("Token de Chattigo obtenido correctamente")
            return token
        
    except Exception as e:
        logger.error(f"❌ Error al obtener token de Chattigo: {e}")
        return None
    
async def enviar_mensaje_whatsapp(msisdn: str, mensaje: str, nombre_usuario: str | None = None):
    """
    Envía un mensaje de texto por WhatsApp al usuario indicado a través de Chattigo.
    """
    token = await get_chattigo_token()
    if not token:
        logger.error("❌ No se pudo obtener token para enviar mensaje")
        return False

    payload = {
        "id": "1234567890",
        "did": EVE_WHATSAPP_NUMBER,
        "msisdn": msisdn,
        "type": "text",
        "channel": "WHATSAPP",
        "content": mensaje,
        "name": nombre_usuario or "Usuario",
        "isAttachment": False
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        if not CHATTIGO_MESSAGE_URL:
            logger.error("CHATTIGO_MESSAGE_URL not configured")
            return False
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(CHATTIGO_MESSAGE_URL, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Mensaje enviado a {msisdn}: {mensaje}")
            return True
    except Exception as e:
        logger.error(f"❌ Error al enviar mensaje por Chattigo: {e}")
        return False
    
async def enviar_a_agente(msisdn: str, mensaje: str, nombre_usuario: str | None = None):
    """
    Deriva la conversación a un agente humano a través del endpoint oficial de Chattigo API-BOT.
    """
    token = await get_chattigo_token()
    if not token:
        logger.error("No se pudo obtener token para enviar mensaje al agente")
        return False

    # Endpoint correcto para transferencias
    CHATTIGO_TRANSFER_URL = "https://massive.chattigo.com/api-bot/outbound"

    payload = {
        "id": str(int(datetime.now().timestamp() * 1000)),
        "idChat": 0,  # si no tenés este dato, se puede enviar 0
        "chatType": "OUTBOUND",
        "did": EVE_WHATSAPP_NUMBER,
        "msisdn": msisdn,
        "type": "transfer",  # CLAVE: este tipo genera la transferencia
        "channel": "WHATSAPP",
        "channelId": 14031,  # opcional, pero puede estar en tu payload
        "channelProvider": "APICLOUDBSP",
        "content": mensaje,
        "name": nombre_usuario or "Usuario",
        "idCampaign": "8890",  # reemplazar si tu campaña tiene otro ID
        "isAttachment": False,
        "stateAgent": "BOT"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(CHATTIGO_TRANSFER_URL, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Transferencia enviada al agente para {msisdn}")
            return True
    except Exception as e:
        logger.error(f"Error al transferir conversación a agente: {e}")
        return False

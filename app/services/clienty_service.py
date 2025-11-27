import os
import httpx
import logging

logger = logging.getLogger(__name__)

CLIENTY_AUTH = os.getenv("CLIENTY_AUTH")
CLIENTY_BASE_URL = "https://eventosviajes.clienty.co/api/integration/lead"

async def get_lead_by_phone(phone: str):
    """
    Busca un lead en Clienty por su número de teléfono o teléfono secundario.
    """
    # Normaliza el número (últimos 9 dígitos)
    phone = phone[-10:]
    logger.info(f"Número recibido: {phone}")

    if not CLIENTY_AUTH:
        logger.error("CLIENTY_AUTH no está definido en el entorno")
        return None

    headers = {"Authorization": f"Basic {CLIENTY_AUTH}"}
    url = f"{CLIENTY_BASE_URL}?filters%5Bsearch%5D={phone}"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            leads = data.get("data", {}).get("data", [])
            if leads:
                lead = leads[0]
                nombre = lead.get("name", "")
                apellido = lead.get("lastName", "")
                email = lead.get("email", "")
                phone = lead.get("phone2") or lead.get("phone")
                colegio_tag = None
                if lead.get("tags"):
                    colegio_tag = lead["tags"][0]["name"]

                lead_info = {
                    "nombre": nombre.strip(),
                    "apellido": apellido.strip(),
                    "nombre_completo": f"{nombre} {apellido}".strip(),
                    "email": email.strip(),
                    "telefono": phone,
                    "colegio": colegio_tag or "No especificado"
                }

                logger.info(f"Lead encontrado: {lead_info}")
                return lead_info
            else:
                logger.info("No se encontró lead con ese número")
                return None
    except httpx.HTTPStatusError as e:
        logger.error(f"Error al consultar Clienty: {e.response.status_code} {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Error general al consultar Clienty: {e}")
        return None

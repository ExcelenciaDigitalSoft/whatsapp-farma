import logging
from datetime import datetime, timedelta
from app.services.langchain_service import chat  # type: ignore
from app.services.clienty_service import get_lead_by_phone
from app.services.chattigo_service import enviar_mensaje_whatsapp, enviar_a_agente  # type: ignore
from app.services.mongo_service import guardar_mensaje

logger = logging.getLogger(__name__)

# Control de saludos y tiempos
usuarios_saludados = {}
SALUDOS = ["hola", "buenas", "hola!", "buen día", "buenas tardes", "buenas noches", "que tal", "Hola!", "Hola !", " Hola !"]
TIEMPO_RE_SALUDO = timedelta(hours=24)

# Palabras que activan filtrado de contenido
PALABRAS_PROHIBIDAS = [
    "sexual", "abus", "explotación", "pornografía", "violación", "inapropiado"
]


def limpiar_respuesta(respuesta: str) -> str:
    """Filtra contenido sensible o respuestas vacías."""
    if not respuesta:
        return "No tengo información disponible en este momento."
    texto = respuesta.lower()
    if any(p in texto for p in PALABRAS_PROHIBIDAS):
        logger.warning("Respuesta filtrada por contenido inapropiado.")
        return "Perdón, no tengo información sobre ese tema. ¿Querés que te ayude con otra consulta?"
    return respuesta


async def procesar_mensaje(payload: dict):
    """
    Procesa el mensaje recibido desde el webhook de Chattigo (API Massive).

    Reglas de negocio:
    1. Si el usuario está en Clienty → usa IA normalmente (PDF).
    2. Si el usuario NO está en Clienty → usa IA igualmente, excepto si se detecta
       que habla de egresados (entonces se envían los links de inscripción).
    3. Si el usuario registrado habla de egresados → usa IA con su contexto (nombre, colegio).
    4. Si la IA responde con “no sé” o “no tengo info” → se deriva a un agente humano.
    5. Si el usuario solo saluda → responde con un mensaje de saludo.
    """
    try:
        # --- FORMATO DIRECTO DESDE CHATTIGO MASSIVE ---
        user_message = payload.get("content", "").strip()
        session_id = str(payload.get("msisdn"))
        nombre_contacto = payload.get("name", "Usuario")

        if not user_message or not session_id:
            logger.warning("Payload inválido o sin datos de mensaje.")
            return {"respuesta_ia": "No se encontró ningún mensaje válido."}

        logger.info(f"Mensaje de {session_id}: {user_message}")

        guardar_mensaje(
            msisdn=session_id,
            role="usuario",
            contenido=user_message,
            nombre_usuario=nombre_contacto
        )

        texto_lower = user_message.lower()

        # --- DETECCIÓN DE INTENCIÓN DE HABLAR CON UN AGENTE ---
        solicitudes_agente = [
            "hablar con un agente", "comunicarme con un agente",
            "comunicarme con alguien", "hablar con alguien",
            "hablar con una persona", "quiero un humano",
            "necesito una persona", "quiero hablar con soporte",
            "atención al cliente", "quiero hablar con una persona real"
        ]

        if any(frase in texto_lower for frase in solicitudes_agente):
            logger.info(f"El usuario {session_id} pidió hablar con un agente.")
            try:
                await enviar_a_agente(
                    msisdn=session_id,
                    mensaje="Te voy a derivar con un agente humano para que pueda ayudarte mejor.",
                    nombre_usuario=nombre_contacto,
                )
                return {"respuesta_ia": "Derivado a un agente humano a pedido del usuario."}
            except Exception as e:
                logger.error(f"Error al derivar a agente humano (pedido directo): {e}")
                return {"respuesta_ia": "No pude transferirte a un agente humano. Por favor, intentá más tarde."}

        # --- BUSCAR USUARIO EN CLIENTY ---
        lead = await get_lead_by_phone(session_id)

        # --- SI EL USUARIO NO ESTÁ REGISTRADO ---
        if not lead:
            logger.info(f"No se encontró lead para {session_id}. Analizando mensaje...")

            # Palabras clave asociadas a EGRESADOS
            palabras_egresados = [
                "egresado", "egresados", "promo", "promoción",
                "fiesta", "baile", "cena", "graduación", "entrada", "colegio"
            ]

            # Si el mensaje tiene relación con egresados → enviar link de inscripción
            if any(p in texto_lower for p in palabras_egresados):
                logger.info(f"Consulta detectada como EGRESADOS para {session_id}")
                respuesta_egresados = (
                    "Parece que tu consulta es sobre nuestras fiestas de egresados y no tenemos agendado tu numero en nuestro sistema.\n\n"
                    "Podés inscribirte directamente completando uno de estos formularios:\n"
                    "2025: https://forms.gle/a9KoN5WcygQwdfLY7\n"
                    "2026: https://forms.gle/bqNfvopvkjwqr3WF8\n\n"
                )
                try:
                    guardar_mensaje(
                        msisdn=session_id,
                        role="bot",
                        contenido=respuesta_egresados,
                        nombre_usuario=nombre_contacto
                    )

                    await enviar_mensaje_whatsapp(session_id, respuesta_egresados, "Usuario no registrado")
                    return {"respuesta_ia": respuesta_egresados}
                except Exception as e:
                    logger.error(f"Error al enviar mensaje de inscripción de egresados: {e}")
                    return {"respuesta_ia": "No pude enviar el link de inscripción. Por favor, intentá más tarde."}

            # Si NO habla de egresados → seguir con IA normalmente
            logger.info(f"Usuario no registrado, pero consulta general. Continuando flujo con IA.")
            nombre_completo = ""
            nombre = ""
            colegio = "No especificado"
        else:
            # --- USUARIO ENCONTRADO ---
            nombre_completo = lead.get("nombre_completo")
            nombre = lead.get("nombre")
            colegio = lead.get("colegio", "No especificado")

        # --- CONTEXTO PERSONALIZADO PARA LA IA ---
        if lead:
            # Usuario registrado → aplicar contexto
            contexto_usuario = (
                f"El usuario que escribe se llama {nombre_completo} y pertenece a {colegio}."
            )
            if colegio and "no especificado" not in colegio.lower():
                pregunta_filtrada = (
                    f"{contexto_usuario} El usuario pertenece al {colegio}. "
                    f"Si la pregunta está relacionada con precios, "
                    f"responde exclusivamente con los valores correspondientes a ese colegio. "
                    f"Pregunta: {user_message}"
                )
            else:
                pregunta_filtrada = f"{contexto_usuario} {user_message}"
        else:
            # Usuario no registrado → no incluir contexto falso
            pregunta_filtrada = user_message

        ahora = datetime.now()
        ultimo_saludo = usuarios_saludados.get(session_id)
        es_saludo = any(saludo in texto_lower for saludo in SALUDOS)
        paso_tiempo = (ultimo_saludo is None) or ((ahora - ultimo_saludo) > TIEMPO_RE_SALUDO)

        # --- SALUDOS AUTOMÁTICOS ---
        if es_saludo and paso_tiempo:
            usuarios_saludados[session_id] = ahora
            saludo = (
                f"Hola {nombre.split()[0]}! Soy el asistente virtual de Eventos Viajes. ¿Querés que te pase información sobre fiestas de egresados, bodas o eventos sociales?"
                if nombre else
                "Hola! Soy el asistente virtual de Eventos Viajes. ¿Querés que te pase información sobre fiestas de egresados, bodas o eventos sociales?"
            )
            guardar_mensaje(
                msisdn=session_id,
                role="bot",
                contenido=saludo,
                nombre_usuario=nombre_completo
            )
            await enviar_mensaje_whatsapp(session_id, saludo, nombre_completo)
            return {"respuesta_ia": saludo}


        # --- RESPUESTA DE LA IA ---
        # --- Ajuste del prompt para tono institucional (primera persona plural) ---
        prompt_final = (
            f"{pregunta_filtrada}\n\n"
            "IMPORTANTE: Siempre respondé como si fueras parte del equipo de Esteban Vazquez Eventos. "
            "Usá un tono amable, cálido y profesional, siempre en primera persona plural (nosotros, nuestro, estamos, ofrecemos, podés contactarnos, etc.). "
            "Nunca hables en tercera persona ni digas 'ellos', 'la empresa', 'el organizador', etc. "
            "Si no encontrás información en el documento, decí exactamente: 'No tengo esa información en este momento.'"
        )

        ai_response = chat(session_id, prompt_final)
        ai_response = limpiar_respuesta(ai_response)

        usuarios_saludados[session_id] = ahora
        logger.info(f"Respuesta final de la IA para {session_id}: {ai_response}")

        # --- DERIVAR A AGENTE SI LA IA NO SABE RESPONDER ---
        respuestas_invalidas = [
            "no tengo esa información",
            "no sé",
            "no puedo ayudarte",
            "no tengo información disponible",
            "no tengo información sobre eso",
            "no cuento con esa información",
            "no puedo responder eso",
            "no dispongo de esa información",
            "no se proporciona información"
        ]

        if any(frase in ai_response.lower() for frase in respuestas_invalidas):
            logger.warning(f"Respuesta inválida detectada para {session_id}: '{ai_response}' → derivando a agente humano.")
            try:
                await enviar_a_agente(
                    msisdn=session_id,
                    mensaje="No tengo esa información en este momento, pero te derivo con un agente para que pueda asistirte enseguida.",
                    nombre_usuario=nombre_completo,
                )
                return {"respuesta_ia": "Derivado a un agente humano. En breve te atenderán."}
            except Exception as e:
                logger.error(f"Error al derivar a agente humano: {e}")
                return {"respuesta_ia": "No pude transferirte a un agente humano. Por favor, intentá más tarde."}

        # --- RESPUESTA NORMAL DEL BOT ---
        try:
            guardar_mensaje(
                msisdn=session_id,
                role="bot",
                contenido=ai_response,
                nombre_usuario=nombre_completo
            )
            await enviar_mensaje_whatsapp(session_id, ai_response, nombre_completo)
        except Exception as e:
            logger.error(f"Error al enviar mensaje de WhatsApp por Chattigo: {e}")

        return {"respuesta_ia": ai_response}

    except Exception as e:
        logger.error(f"Error en procesar_mensaje: {e}")
        return {"respuesta_ia": "Ocurrió un error al procesar tu mensaje."}

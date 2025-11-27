def normalizar_numero_whatsapp(numero: str) -> str:
    """
    Limpia y normaliza un número de WhatsApp para búsqueda en Clienty.
    """
    if not numero:
        return ""
    numero = numero.strip().replace("+", "")
    if numero.startswith("549"):
        numero = numero[3:]
    elif numero.startswith("54"):
        numero = numero[2:]
    return numero

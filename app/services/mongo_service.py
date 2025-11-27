import os
import logging

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure


logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME")


_mongo_client = None

def get_mongo_client():
    """
    Obtiene la conexión a MongoDB.
    Si no existe, la crea. Si falla, retorna None.
    """
    global _mongo_client
    
    if _mongo_client is not None:
        return _mongo_client
    
    try:
        _mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

        _mongo_client.admin.command('ping')
        logger.info("✅ Conexión a MongoDB establecida correctamente")
        return _mongo_client
    except (ServerSelectionTimeoutError, ConnectionFailure) as e:
        logger.error(f"❌ Error al conectar a MongoDB: {e}")
        _mongo_client = None
        return None

def guardar_mensaje(msisdn: str, role: str, contenido: str, nombre_usuario: str | None = None):
    """
    Guarda un mensaje en MongoDB.
    
    Args:
        msisdn (str): Número de teléfono del usuario (clave del documento)
        role (str): "usuario" o "bot"
        contenido (str): Contenido del mensaje
        nombre_usuario (str): Nombre del usuario (opcional, se guarda solo en primera instancia)
    
    Returns:
        bool: True si se guardó correctamente, False en caso de error
    """
    try:
        client = get_mongo_client()
        if client is None:
            logger.warning("⚠️ MongoDB no está disponible. Mensaje no guardado en BD.")
            return False

        if not DATABASE_NAME or not COLLECTION_NAME:
            logger.error("❌ DATABASE_NAME or COLLECTION_NAME not configured")
            return False

        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        msisdn_normalizado = str(msisdn).strip()
        
        # Mensaje a guardar
        mensaje = {
            "timestamp": datetime.utcnow(),
            "role": role,
            "contenido": contenido
        }
        
        # Buscar si ya existe un documento para este usuario
        documento_existente = collection.find_one({"_id": msisdn_normalizado})
        
        if documento_existente:
            # Si existe, agregar el mensaje al array de mensajes
            collection.update_one(
                {"_id": msisdn_normalizado},
                {
                    "$push": {"mensajes": mensaje},
                    "$set": {"ultima_actualizacion": datetime.utcnow()}
                }
            )
            logger.info(f"✅ Mensaje guardado para usuario existente {msisdn_normalizado}")
        else:
            # Si no existe, crear un nuevo documento
            nuevo_documento = {
                "_id": msisdn_normalizado,
                "nombre_usuario": nombre_usuario or "Sin nombre",
                "fecha_creacion": datetime.utcnow(),
                "ultima_actualizacion": datetime.utcnow(),
                "mensajes": [mensaje]
            }
            collection.insert_one(nuevo_documento)
            logger.info(f"✅ Nuevo documento creado para usuario {msisdn_normalizado}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al guardar mensaje en MongoDB: {e}")
        return False

def cerrar_conexion_mongo():
    """
    Cierra la conexión a MongoDB.
    Útil para cleanup en shutdown.
    """
    global _mongo_client
    if _mongo_client is not None:
        try:
            _mongo_client.close()
            logger.info("✅ Conexión a MongoDB cerrada")
            _mongo_client = None
        except Exception as e:
            logger.error(f"Error al cerrar conexión MongoDB: {e}")

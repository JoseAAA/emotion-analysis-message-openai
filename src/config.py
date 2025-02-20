"""
config.py

Módulo para cargar y exponer variables de entorno y configuraciones
relacionadas con la aplicación. Lee datos de .env (claves, URL, modelo, mapeos, etc.)
y maneja logs para advertir si hay problemas con parseos JSON.

Autor: JoseAAA
"""

import os
import json
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv()

# -------------------------------------------------------
# Credenciales y configuraciones de la API
# -------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
LANGUAGE = os.getenv("LANGUAGE", "es")

if not OPENAI_API_KEY:
    logger.error("Falta configurar 'OPENAI_API_KEY' en .env.")
    raise ValueError("Falta configurar 'OPENAI_API_KEY' en .env.")

# -------------------------------------------------------
# Mapeos de remitentes en formato JSON
# -------------------------------------------------------
whatsapp_mapping_str = os.getenv("WHATSAPP_SENDER_MAPPING", "{}")
telegram_mapping_str = os.getenv("TELEGRAM_SENDER_MAPPING", "{}")
SENDER_FALLBACK = os.getenv("SENDER_FALLBACK", "Otro")

try:
    WHATSAPP_SENDER_MAPPING = json.loads(whatsapp_mapping_str)
except json.JSONDecodeError:
    logger.warning("No se pudo parsear WHATSAPP_SENDER_MAPPING como JSON. Usando {} por defecto.")
    WHATSAPP_SENDER_MAPPING = {}

try:
    TELEGRAM_SENDER_MAPPING = json.loads(telegram_mapping_str)
except json.JSONDecodeError:
    logger.warning("No se pudo parsear TELEGRAM_SENDER_MAPPING como JSON. Usando {} por defecto.")
    TELEGRAM_SENDER_MAPPING = {}

# -------------------------------------------------------
# Stopwords personalizadas, emociones, etiqueta desconocida
# -------------------------------------------------------
custom_stopwords_str = os.getenv("CUSTOM_STOPWORDS", "[]")
try:
    CUSTOM_STOPWORDS = set(json.loads(custom_stopwords_str))
except json.JSONDecodeError:
    logger.warning("No se pudo parsear CUSTOM_STOPWORDS como JSON. Usando set() por defecto.")
    CUSTOM_STOPWORDS = set()

valid_emotions_str = os.getenv("VALID_EMOTIONS", "[]")
try:
    VALID_EMOTIONS = json.loads(valid_emotions_str)
except json.JSONDecodeError:
    logger.warning("No se pudo parsear VALID_EMOTIONS como JSON. Usando lista vacía por defecto.")
    VALID_EMOTIONS = []

UNKNOWN_EMOTION_LABEL = os.getenv("UNKNOWN_EMOTION_LABEL", "Neutro")

# -------------------------------------------------------
# Rutas de datos
# -------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

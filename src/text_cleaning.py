"""
text_cleaning.py

Funciones para limpiar y normalizar texto en español, 
incluyendo extracción de emojis, eliminación de URLs, etc.
"""

import re
import regex
import logging
import spacy
import nltk
from nltk.corpus import stopwords
from config import CUSTOM_STOPWORDS

logger = logging.getLogger(__name__)

nlp = spacy.load("es_core_news_sm")

stopwords_spacy = nlp.Defaults.stop_words
stopwords_nltk = set(stopwords.words("spanish"))
spanish_stopwords = stopwords_spacy.union(stopwords_nltk).union(CUSTOM_STOPWORDS)

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
EMOJI_PATTERN = regex.compile(
    "[" 
    u"\U0001F600-\U0001F64F"
    u"\U0001F300-\U0001F5FF"
    u"\U0001F680-\U0001F6FF"
    u"\U0001F1E0-\U0001F1FF"
    "]+", 
    flags=regex.UNICODE
)
MENTION_PATTERN = re.compile(r'@\w+')
PHONE_PATTERN = re.compile(r'\+\d{1,3}[- ]?\d{6,14}')
DATE_PATTERN = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
TIME_PATTERN = re.compile(r'\b\d{1,2}:\d{2}\b')
REPEATED_CHARS = re.compile(r'(.)\1{2,}')


def extract_emojis(text: str) -> str:
    """
    Extrae todos los emojis de un texto y los devuelve concatenados en orden de aparición.

    Args:
        text (str): El texto original con emojis.

    Returns:
        str: Una cadena que contiene solo los emojis encontrados, en orden.
             Si no se encuentra ninguno, retorna cadena vacía.
    """
    if not text.strip():
        return ""

    # Buscar todos los match de EMOJI_PATTERN y concatenarlos
    found_emojis = EMOJI_PATTERN.findall(text)
    return "".join(found_emojis)


def clean_text(text: str) -> str:
    """
    Limpia y normaliza un texto en español:
    
    1) Convierte a minúsculas y elimina saltos de línea.
    2) Elimina URLs, emojis, menciones, teléfonos, fechas y horas.
    3) Quita puntuación, reduce repeticiones y espacios extra.
    4) Lematiza con spaCy y filtra stopwords (incluyendo las personalizadas).

    Args:
        text (str): El texto original que se desea limpiar.

    Returns:
        str: El texto limpio y normalizado.
    """
    if not text.strip():
        logger.debug("clean_text: Texto vacío o solo espacios.")
        return ""

    text = text.lower().replace("\n", " ").replace("\r", " ")

    text = URL_PATTERN.sub('', text)
    text = EMOJI_PATTERN.sub('', text)
    text = MENTION_PATTERN.sub('', text)
    text = PHONE_PATTERN.sub('', text)
    text = DATE_PATTERN.sub('', text)
    text = TIME_PATTERN.sub('', text)

    text = re.sub(r'[^\w\s]', ' ', text)
    text = REPEATED_CHARS.sub(r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()

    doc = nlp(text)
    tokens = [
        token.lower_
        for token in doc
        if token.text.lower() not in spanish_stopwords and not token.like_num
    ]
    return ' '.join(tokens)

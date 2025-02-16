"""
emotion_analysis.py

Módulo para análisis de emociones usando la API estilo openai (OpenAI, DeepSeek, etc.).
Incluye una función para clasificar una lista de textos en lotes (batch),
optimizando el uso de la API para ser más rápido, barato y confiable.
"""

import json
import logging
from typing import List
import openai
from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    OPENAI_API_MODEL,
    VALID_EMOTIONS,
    UNKNOWN_EMOTION_LABEL
)

logger = logging.getLogger(__name__)

# Configurar la API (OpenAI, DeepSeek, etc.)
openai.api_key = OPENAI_API_KEY
openai.api_base = OPENAI_API_BASE  # "https://api.openai.com" o "https://api.deepseek.com"


def classify_texts_in_bulk(
    texts: List[str],
    max_per_chunk: int = 50,
    max_tokens_response: int = 300
) -> List[str]:
    """
    Clasifica una lista de textos en una sola emoción (entre VALID_EMOTIONS),
    enviándolos en lotes (batch) para reducir el número de llamadas a la API 
    y, por ende, minimizar costos.

    Usa la interfaz openai.chat.completions.create y las variables definidas 
    en config.py (OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_API_MODEL, etc.).

    El prompt es minimalista para ahorrar tokens, y se configuran lotes 
    (max_per_chunk) y un número de tokens para la respuesta (max_tokens_response) 
    de modo que sea confiable, rápido y barato.

    Args:
        texts (List[str]): Lista de textos a clasificar.
        max_per_chunk (int, opcional): Tamaño del lote (batch) 
            para cada llamada a la API. Lotes más grandes => menos llamadas => menor costo,
            pero se requiere un 'max_tokens_response' mayor para no truncar el JSON.
            Por defecto 50.
        max_tokens_response (int, opcional): Límite de tokens para la respuesta JSON.
            Subir si se trunca el JSON en lotes grandes. Por defecto 200.

    Returns:
        List[str]: Lista con la emoción clasificada para cada texto, 
        en el mismo orden que 'texts'. Si no se puede parsear la respuesta 
        o la emoción no coincide con VALID_EMOTIONS, se retorna UNKNOWN_EMOTION_LABEL.
    """
    results = []

    # Prompt mínimo en 'system' para ahorrar tokens
    system_prompt = (
        "Eres un sistema de clasificación de emociones en español. "
        "Recibirás un bloque de oraciones enumeradas, y tu respuesta debe ser "
        "EXCLUSIVAMENTE un objeto JSON con la forma:\n"
        "{ \"1\": \"amor\", \"2\": \"ira\", ... }\n"
        "sin texto adicional. Emociones posibles: "
        f"{', '.join(VALID_EMOTIONS)}. No agregues explicaciones."
        f"Si no coincide, usa \"{UNKNOWN_EMOTION_LABEL}\"."
    )

    # Procesar la lista en lotes
    total_texts = len(texts)
    logger.info(f"Se van a clasificar {total_texts} textos en lotes de {max_per_chunk}.")

    for start_idx in range(0, total_texts, max_per_chunk):
        batch = texts[start_idx : start_idx + max_per_chunk]
        logger.debug(f"Lote de {len(batch)} textos, índice {start_idx} a {start_idx + len(batch) - 1}.")

        # Crear un texto enumerado
        enumerated_text = "\n".join(
            f"{i+1}) {txt}" for i, txt in enumerate(batch)
        )

        user_prompt = (
            "Clasifica cada oración enumerada en una de las emociones. "
            "Devuelve SOLO un JSON. Ejemplo:\n"
            "{ \"1\": \"alegría\", \"2\": \"ira\" }\n\n"
            f"{enumerated_text}"
        )

        try:
            response = openai.chat.completions.create(
                model=OPENAI_API_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt}
                ],
                temperature=0.0,  # Evita respuestas largas y creativas
                max_tokens=max_tokens_response
            )
            content = response.choices[0].message.content.strip()
            logger.debug(f"Respuesta de la API (lote {start_idx}): {content[:100]}...")

            # Parsear el JSON devuelto
            try:
                parsed_json = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(f"No se pudo parsear el JSON en el lote {start_idx}:\n{content}")
                # Llenar con UNKNOWN_EMOTION_LABEL para este lote
                for _ in batch:
                    results.append(UNKNOWN_EMOTION_LABEL)
                continue

            # Extraer la emoción para cada texto en este lote
            for i in range(len(batch)):
                key = str(i + 1)
                raw_emo = parsed_json.get(key, UNKNOWN_EMOTION_LABEL).lower()
                if raw_emo not in [emo.lower() for emo in VALID_EMOTIONS]:
                    raw_emo = UNKNOWN_EMOTION_LABEL
                results.append(raw_emo)

        except Exception as e:
            logger.error(f"Error al llamar a la API en el lote {start_idx}: {e}")
            # Si falla la llamada entera, llenamos con UNKNOWN_EMOTION_LABEL
            for _ in batch:
                results.append(UNKNOWN_EMOTION_LABEL)

    logger.info("Clasificación de emociones completada.")
    return results

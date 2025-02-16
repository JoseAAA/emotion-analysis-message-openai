"""
pipeline.py

Script principal que orquesta:
1) Carga de datos (WhatsApp, Telegram, etc.)
2) Mapeo de remitentes (según config.py)
3) Extracción de emojis (mensaje_emojis)
4) Limpieza de texto (message_clean)
5) Análisis de emociones por lotes
6) Guardado en Excel

Incluye logging para un mejor seguimiento de la ejecución.
"""

import os
import logging
import pandas as pd
from pathlib import Path

# Importar configuración y funciones
from config import (
    DATA_DIR,
    WHATSAPP_SENDER_MAPPING,
    TELEGRAM_SENDER_MAPPING,
    SENDER_FALLBACK
)
from data_parsers import parse_whatsapp_lines, parse_telegram_html
from text_cleaning import clean_text, extract_emojis
from emotion_analysis import classify_texts_in_bulk

logger = logging.getLogger(__name__)

def main():
    """
    Punto de entrada principal del pipeline.

    1) Carga y parsea mensajes de WhatsApp y Telegram desde data/raw/.
    2) Aplica un mapeo de remitentes (definido en config.py)
       para homogeneizar nombres en el reporte.
    3) Extrae los emojis en una columna 'message_emoji'.
    4) Limpia y normaliza el texto en 'message_clean'.
    5) Clasifica las emociones por lotes (classify_texts_in_bulk)
       para reducir costos en la API.
    6) Guarda el resultado final en data/processed/mensajes_procesados.xlsx.
    """

    logger.info("Iniciando pipeline de procesamiento de mensajes...")

    # 1. Cargar datos de WhatsApp
    whatsapp_dir = os.path.join(DATA_DIR, "raw", "WhatsApp")
    if not os.path.exists(whatsapp_dir):
        logger.warning(f"No se encontró el directorio de WhatsApp: {whatsapp_dir}")

    all_whatsapp_dfs = []
    for fname in os.listdir(whatsapp_dir):
        if fname.endswith(".txt"):
            full_path = os.path.join(whatsapp_dir, fname)
            logger.info(f"Procesando archivo WhatsApp: {full_path}")
            try:
                df_part = parse_whatsapp_lines(full_path)
                all_whatsapp_dfs.append(df_part)
            except Exception as e:
                logger.error(f"Error al parsear {full_path}: {e}")

    if all_whatsapp_dfs:
        df_whatsapp = pd.concat(all_whatsapp_dfs, ignore_index=True)
        df_whatsapp.sort_values("datetime", inplace=True)
        df_whatsapp.reset_index(drop=True, inplace=True)
        logger.info(f"WhatsApp: Se cargaron {df_whatsapp.shape[0]} mensajes.")
    else:
        logger.warning("No se encontraron mensajes de WhatsApp.")
        df_whatsapp = pd.DataFrame(columns=["datetime", "sender", "message"])

    # Mapear remitentes según config.py
    if not df_whatsapp.empty:
        df_whatsapp["sender"] = df_whatsapp["sender"].map(WHATSAPP_SENDER_MAPPING).fillna(SENDER_FALLBACK)
        df_whatsapp["tipo"] = "WhatsApp"

    # 2. Cargar datos de Telegram
    telegram_dir = os.path.join(DATA_DIR, "raw", "Telegram")
    if not os.path.exists(telegram_dir):
        logger.warning(f"No se encontró el directorio de Telegram: {telegram_dir}")

    all_telegram_dfs = []
    for fname in os.listdir(telegram_dir):
        if fname.endswith(".html"):
            full_path = os.path.join(telegram_dir, fname)
            logger.info(f"Procesando archivo Telegram: {full_path}")
            try:
                df_part = parse_telegram_html(full_path)
                all_telegram_dfs.append(df_part)
            except Exception as e:
                logger.error(f"Error al parsear {full_path}: {e}")

    if all_telegram_dfs:
        df_telegram = pd.concat(all_telegram_dfs, ignore_index=True)
        df_telegram.sort_values("datetime", inplace=True)
        df_telegram.reset_index(drop=True, inplace=True)
        logger.info(f"Telegram: Se cargaron {df_telegram.shape[0]} mensajes.")
    else:
        logger.warning("No se encontraron mensajes de Telegram.")
        df_telegram = pd.DataFrame(columns=["datetime", "sender", "message"])

    if not df_telegram.empty:
        df_telegram["sender"] = df_telegram["sender"].map(TELEGRAM_SENDER_MAPPING).fillna(SENDER_FALLBACK)
        df_telegram["tipo"] = "Telegram"

    # 3. Unificar ambos DataFrames y ordenar cronológicamente
    if df_whatsapp.empty and df_telegram.empty:
        logger.warning("No hay datos de WhatsApp ni de Telegram para procesar.")
        return

    df = pd.concat([df_whatsapp, df_telegram], ignore_index=True)
    df.sort_values("datetime", inplace=True)
    df.reset_index(drop=True, inplace=True)
    logger.info(f"Mensajes unificados: {df.shape[0]} filas.")

    # 4. Extraer emojis y limpiar texto
    logger.info("Extrayendo emojis y limpiando texto...")
    df["message_emoji"] = df["message"].apply(extract_emojis)   # Nueva columna con los emojis
    df["message_clean"] = df["message"].apply(clean_text)        # Limpieza del texto

    # Filtrar mensajes muy cortos
    df["n_tokens"] = df["message_clean"].apply(lambda x: len(x.split()))
    df_filtrado = df[df["n_tokens"] > 1].copy()
    logger.info(f"Mensajes con más de 1 token: {df_filtrado.shape[0]}")

    # 5. Análisis de emociones por lotes
    logger.info("Clasificando emociones por lotes para reducir costos...")
    texts_to_classify = df_filtrado["message_clean"].tolist()
    emotions_pred = classify_texts_in_bulk(
        texts=texts_to_classify,
        max_per_chunk=30,         # Ajusta según tus necesidades
        max_tokens_response=300   # Suficiente para ~50 items
    )
    df_filtrado["emotion"] = emotions_pred

    # 6. Guardar resultado en Excel
    output_path = Path(DATA_DIR) / "processed" / "data_messages.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_filtrado.to_excel(output_path, index=False)

    logger.info(f"Archivo Excel guardado en: {output_path}")
    logger.info("Pipeline completado con éxito.")


if __name__ == "__main__":
    # Configurar logging (nivel INFO por defecto)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main()

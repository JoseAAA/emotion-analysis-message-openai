"""
data_parsers.py

Funciones para parsear archivos de WhatsApp, Telegram, u otras plataformas.
Devuelven DataFrames con las columnas [datetime, sender, message].
Incluye logging para mayor trazabilidad.
"""

import os
import re
import datetime
import logging
import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_whatsapp_lines(filepath: str) -> pd.DataFrame:
    """
    Parsea un archivo .txt de WhatsApp con el formato:
    '3/1/2022, 8:30 a. m. - Nombre: Mensaje'

    El resultado se devuelve como un DataFrame con columnas:
      - datetime (datetime): Fecha y hora del mensaje.
      - sender (str): Remitente del mensaje.
      - message (str): Contenido del mensaje.

    Args:
        filepath (str): Ruta absoluta o relativa al archivo .txt de WhatsApp.

    Returns:
        pd.DataFrame: DataFrame con columnas [datetime, sender, message].

    Raises:
        ValueError: Si el archivo no cumple con el formato esperado o no puede parsear la fecha/hora.
    """
    logger.info(f"parse_whatsapp_lines: Iniciando parseo de {filepath}")
    pattern = re.compile(
        r'^(\d{1,2}\/\d{1,2}\/\d{4}),\s*(\d{1,2}:\d{2}\s?[ap]\.?m\.?)\s*-\s*(.*)$',
        re.IGNORECASE
    )

    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                match = pattern.match(line)
                if not match:
                    # Líneas que no cumplen el formato (mensajes de sistema, etc.)
                    logger.debug(f"Línea {line_num} no cumple el formato esperado, se ignora.")
                    continue

                date_str = match.group(1)  # Ej: "3/1/2022"
                time_str = match.group(2)  # Ej: "8:30 a. m."
                content = match.group(3)   # Ej: "Nombre: Mensaje"

                # Normalización de la hora (eliminando espacios, reemplazando a.m./p.m.)
                time_str = (time_str
                            .replace(' ', '')
                            .replace('a. m.', 'AM')
                            .replace('p. m.', 'PM')
                            .replace('a.m.', 'AM')
                            .replace('p.m.', 'PM')
                            .replace('.', '')
                            .replace(' ', '')
                           )
                # Ej final: "8:30AM" o "10:57PM"

                try:
                    dt = datetime.datetime.strptime(date_str + ' ' + time_str, "%d/%m/%Y %I:%M%p")
                except ValueError:
                    logger.debug(f"Línea {line_num}: No se pudo parsear fecha/hora -> {date_str} {time_str}")
                    continue

                if ': ' in content:
                    sender, message = content.split(': ', 1)
                else:
                    sender = "SYSTEM"
                    message = content

                data.append({
                    'datetime': dt,
                    'sender': sender,
                    'message': message
                })

        df = pd.DataFrame(data, columns=["datetime", "sender", "message"])
        logger.info(f"parse_whatsapp_lines: Se parsearon {len(df)} mensajes de {filepath}")
        return df

    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {filepath}")
        return pd.DataFrame(columns=["datetime", "sender", "message"])
    except Exception as e:
        logger.error(f"Error inesperado al parsear {filepath}: {e}")
        return pd.DataFrame(columns=["datetime", "sender", "message"])


def parse_telegram_html(filepath: str) -> pd.DataFrame:
    """
    Parsea un archivo .html exportado de Telegram Desktop.

    - Ignora mensajes de servicio (solo fechas o avisos).
    - Extrae fecha/hora del atributo 'title' en <div class="pull_right date details">.
    - Extrae el remitente en <div class="from_name"> (si existe).
    - Extrae el texto del mensaje en <div class="text">.

    El resultado se devuelve como un DataFrame con columnas:
      - datetime (datetime): Fecha y hora del mensaje.
      - sender (str): Remitente del mensaje.
      - message (str): Contenido del mensaje.

    Args:
        filepath (str): Ruta absoluta o relativa al archivo .html exportado de Telegram.

    Returns:
        pd.DataFrame: DataFrame con columnas [datetime, sender, message].

    Raises:
        ValueError: Si no se puede parsear la fecha/hora o no encuentra contenido.
    """
    logger.info(f"parse_telegram_html: Iniciando parseo de {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        messages_list = []
        # Buscar todos los divs que contengan mensajes (excluyendo servicios)
        msg_divs = soup.find_all("div", class_=re.compile(r"message default clearfix"))
        last_sender = None  # Para manejar mensajes "joined" sin from_name

        for div_num, msg_div in enumerate(msg_divs, start=1):
            # Omitir mensajes de servicio
            if "service" in msg_div.get("class", []):
                logger.debug(f"Div {div_num}: Mensaje de servicio, se ignora.")
                continue

            date_div = msg_div.find("div", class_="pull_right date details")
            if not date_div or not date_div.has_attr("title"):
                logger.debug(f"Div {div_num}: No se encontró date details o 'title'. Se ignora.")
                continue

            date_str = date_div["title"]  # Ej: "DD.MM.YYYY HH:MM:SS UTC-05:00"
            parted = date_str.split(" UTC")[0].strip()  # "DD.MM.YYYY HH:MM:SS"
            try:
                dt = datetime.datetime.strptime(parted, "%d.%m.%Y %H:%M:%S")
            except ValueError:
                logger.debug(f"Div {div_num}: No se pudo parsear fecha/hora -> {parted}")
                continue

            from_div = msg_div.find("div", class_="from_name")
            if from_div:
                sender = from_div.get_text(strip=True)
                last_sender = sender
            else:
                sender = last_sender if last_sender else "Unknown"

            text_div = msg_div.find("div", class_="text")
            if not text_div:
                logger.debug(f"Div {div_num}: No se encontró <div class='text'>, se ignora.")
                continue

            message_text = text_div.get_text("\n", strip=True)
            if not message_text:
                logger.debug(f"Div {div_num}: Mensaje vacío, se ignora.")
                continue

            messages_list.append({
                "datetime": dt,
                "sender": sender,
                "message": message_text
            })

        df = pd.DataFrame(messages_list, columns=["datetime", "sender", "message"])
        logger.info(f"parse_telegram_html: Se parsearon {len(df)} mensajes de {filepath}")
        return df

    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {filepath}")
        return pd.DataFrame(columns=["datetime", "sender", "message"])
    except Exception as e:
        logger.error(f"Error inesperado al parsear {filepath}: {e}")
        return pd.DataFrame(columns=["datetime", "sender", "message"])

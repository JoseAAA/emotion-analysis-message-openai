# Análisis y Reporte de Chats

<div align="center">
  <img 
    src="https://raw.githubusercontent.com/JoseAAA/emotion-analysis-message-openai/main/img/reporte.jpg" 
    alt="Reporte de Mensajes" 
    width="600" 
    height="350" />
</div>

Este proyecto **unifica y analiza** mensajes de **WhatsApp** y **Telegram**, permitiendo:
- **Extraer emojis** de cada mensaje.
- **Limpiar** el texto (eliminando URLs, menciones, stopwords, etc.).
- **Clasificar emociones** en lotes (para abaratar costos en la API).
- **Generar** un Excel final listo para su visualización (por ejemplo, en Power BI).

## 1. Objetivo General

1. **Descargar** y **centralizar** chats de WhatsApp y Telegram.  
2. **Mapear** los remitentes a nombres más simples para un reporte.  
3. **Extraer** todos los **emojis** en una columna “mensaje_emojis”.  
4. **Limpiar** el texto en otra columna (“message_clean”), eliminando URLs, stopwords, etc.  
5. **Clasificar** las emociones por lotes (reduciendo costos).  
6. **Generar** un Excel final (`mensajes_procesados.xlsx`) en `data/processed/`.

## 2. Estructura de Archivos

```bash
MiProyecto/
├── .env                # Variables de entorno (API Key, Mapeos, Stopwords, etc.)
├── requirements.txt    # Dependencias
├── data/
│   ├── raw/
│   │   ├── WhatsApp/   # Archivos .txt exportados de WhatsApp
│   │   └── Telegram/   # Archivos .html exportados de Telegram
│   ├── processed/
│   │   └── data_message.xlsx (resultado final)
│   └── external/ (opcional)
├── src/
│   ├── config.py
│   ├── data_parsers.py
│   ├── text_cleaning.py
│   ├── emotion_analysis.py
│   └── pipeline.py
└── README.md

```

- **`data/raw/`**: Coloca los `.txt` de WhatsApp y `.html` de Telegram.  
- **`data/processed/`**: Se guarda el Excel final `data_message.xlsx`.  
- **`src/`**: Contiene el código (config, parseo, limpieza, análisis de emociones, pipeline).  
- **`.env`**: Variables de entorno (clave de API, mapeos de remitentes, stopwords, etc.).

## 3. Requisitos

- **Python 3.11** (recomendado).  
- **Windows 11** (probado), aunque debería funcionar en otros SO con Python 3.11.  
- **Entorno virtual** (recomendado): `venv` o `conda`.  
- **API Key** de OpenAI o DeepSeek (si es compatible).

### 3.1 Costo Aproximado
- Con `gpt-3.5-turbo`, ~\$1 cada **30,000 mensajes**, gracias a:
  1. **Batching** (menos llamadas).  
  2. **Prompt minimalista**.  
  3. **temperature=0.0** (menos tokens de salida).


- El proyecto implementa:
  1. Batching (menos llamadas).
2. Prompt minimalista.
3. temperature=0.0 (menos tokens de salida).
  
> En pruebas con 30,000 mensajes, tomó ~40 minutos y costó ~$1 en total.

**Por qué usamos OpenAI**: No se han encontrado modelos de emociones en español con igual rendimiento y tolerancia a errores ortográficos. GPT-3.5 Turbo brinda rapidez, confiabilidad y bajo costo para este escenario.

## 4. Cómo Obtener los Datos

### 4.1 WhatsApp
1. En tu móvil, ve a **Ajustes** → **Chats** → **Exportar Chat**.  
2. Elige si incluir multimedia o no.  
3. Obtendrás un archivo `.txt`.  
4. Ponlo en `data/raw/WhatsApp/`.

### 4.2 Telegram
1. En **Telegram Desktop**, ve a Menú → **Export chat history**.  
2. Selecciona **HTML**.  
3. Copia el archivo `.html` a `data/raw/Telegram/`.

## 5. Variables de Entorno (.env)

Ejemplo:

```ini
# Clave, URL y modelo de OpenAI
OPENAI_API_KEY=tu_api_key
OPENAI_API_BASE=url_api
OPENAI_API_MODEL=modelo_api

# Mapeos de remitentes
WHATSAPP_SENDER_MAPPING='{"Pepito1234": "Pepe", "Fulanito5555": "Fulano"}'
TELEGRAM_SENDER_MAPPING='{"Pepito1234": "Pepe", "Fulanito5555": "Fulano"}'
SENDER_FALLBACK="Otro"

# Stopwords
CUSTOM_STOPWORDS='["pues", "asi", "digo", "tampoco", "che", "oye", "oki", "jaja", "jajaja", "q", "xq", "ok", "pq", "multimedia"]'

# Emociones
VALID_EMOTIONS='["amor", "alegría", "sorpresa", "tristeza", "ira", "miedo"]'
UNKNOWN_EMOTION_LABEL="Neutro"
```

1. `OPENAI_API_KEY`: tu clave secreta.
2. `OPENAI_API_BASE`: https://api.openai.com (o URL de DeepSeek).
3. `OPENAI_API_MODEL`: "gpt-3.5-turbo" u otro.
4. `WHATSAPP_SENDER_MAPPING`, `TELEGRAM_SENDER_MAPPING`: Diccionarios JSON para renombrar remitentes.
5. `CUSTOM_STOPWORDS`: Stopwords adicionales.
6. `VALID_EMOTIONS` y `UNKNOWN_EMOTION_LABEL`: Para la clasificación de emociones.

## 6. Instalación y Configuración

1. Clona este repositorio o descárgalo.
2. Crea un entorno virtual

```bash
python -m venv venv
venv\Scripts\activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. SpaCy (modelo español):

```bash
python -m spacy download es_core_news_sm
```

5. NLTK Stopwords:

```bash
python -c "import nltk; nltk.download('stopwords')"
```

6. Crea/edita el archivo .env con tu API Key y configuraciones.

## 7 Ejecución del Pipeline

```bash
python src/pipeline.py
```

1. Lee todos los .txt en data/raw/WhatsApp/ y .html en data/raw/Telegram/.
2. Mapea remitentes (ej. "Pepito1234" → "Pepe").
3. Extrae emojis en la columna mensaje_emojis.
4. Limpia el texto en la columna message_clean.
5. Clasifica emociones (batch) => menor costo (~$1 / 30k mensajes).
6. Genera data/processed/mensajes_procesados.xlsx.

## 8. Resultado y Visualización

En data/processed/data_message.xlsx tendrás columnas como:

- datetime, sender, message, tipo,
- mensaje_emojis,
- message_clean,
- emotion,
- n_tokens, etc.

Con ello puedes hacer reportes en Power BI, Tableau o cualquier otra herramienta de BI:

- Distribución de emociones,
- Evolución de mensajes por fecha,
- Emojis más usados (columna mensaje_emojis),
etc.

## 9. Sugerencias para Reducir Costos

- Batching (max_per_chunk=30 o 50) => menos llamadas => menor costo.
- Prompt minimalista => menos tokens enviados.
- temperature=0.0 => respuestas cortas y deterministas.
- ~$1 cada 30,000 mensajes (dependerá de la longitud real).

## 10. Mejoras Futuras

- Soporte a más plataformas (Slack, Messenger).
- Docker para encapsular todo.
- Automatizar con CI/CD y MLOps (monitoreo de costos, logs).
- Interfaz web con Streamlit para cargar chats sin usar la consola.
- Análisis avanzado (sentimientos múltiples, detección de sarcasmo, etc.).

## 11. Contribución
- Fork este repositorio.
- Crea una rama (feature/nueva-funcionalidad).
- Haz tus cambios, pruebas, y envía un pull request.

## 12. Conclusión
El proyecto Análisis y Reporte de Chats con Python 3.11 permite:

- Centralizar chats de WhatsApp y Telegram,
- Extraer emojis,
- Limpiar texto,
- Clasificar emociones en lotes (menos costo),
- Exportar un Excel final.
- ¡Ojalá te resulte útil y fácil de replicar! Cualquier aporte o duda es bienvenido.


## 💻 Contribuidores 

<table>
  <tr>
    <td align="center">
        <a href="#Foto">
            <img src="https://raw.githubusercontent.com/JoseAAA/emotion-analysis-message-openai/main/img/jose.jpg" target="_blank" height="80px" alt=""/>
            <br /><sub><b>Jose-Alarcon</b> </sub>
        </a>
        <br />
        <a href="#analisis" title="Analisis">📈</a> 
        <a href="https://github.com/JoseAAA" target="_blank" title="Github">:octocat:</a>
    </td>
    <td align="center">
        <a href="#Foto">
            <img src="https://raw.githubusercontent.com/JoseAAA/emotion-analysis-message-openai/main/img/mayu.jpg" height="80px" alt="" target="_blank"/>
            <br /><sub><b>Mayumy-Carrasco</b></sub>
        </a>
        <br />
        <a href="#analisis" title="Analisis">📊</a> 
        <a href="https://github.com/MayumyCH" target="_blank" title="Github">:octocat:</a>
    </td>
  </tr>
</table>

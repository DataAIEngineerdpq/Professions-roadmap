"""
SUB-PASO 2b.1: EXTRACCIÓN DE SKILLS CON LLM (cloud o local)
==========================================================

Este archivo expone UNA sola función pública: extraer_skills_con_llm(texto).
El resto del pipeline la llama sin saber ni importarle si por detrás usa la nube
o un modelo local. Ese es el patrón de "proveedor intercambiable": el interruptor
de config.py decide cuál se usa.

A diferencia del diccionario (que solo encuentra lo conocido), el LLM DESCUBRE
skills que no anticipaste, porque entiende el texto.
"""

import os
import re
import json

from dotenv import load_dotenv

import config

# Lee el archivo .env y carga sus valores como variables de entorno.
# Así la API key vive en .env (que NUNCA se sube a git), no en el código.
load_dotenv()


# ---------------------------------------------------------------------------
# El prompt: la instrucción que le damos al modelo
# ---------------------------------------------------------------------------

# Le pedimos que devuelva SOLO un JSON con la lista de skills, para poder leerlo
# con un programa. Si le dejáramos responder en prosa, tendríamos que adivinar
# cómo separar las skills de su explicación.
INSTRUCCION = (
    "Sos un extractor de skills técnicas de ofertas de empleo. "
    "De la siguiente descripción, extraé ÚNICAMENTE las skills técnicas, "
    "herramientas y tecnologías concretas (lenguajes, frameworks, bases de datos, "
    "servicios cloud, herramientas de datos). No incluyas habilidades blandas ni "
    "frases genéricas. Respondé SOLO con un objeto JSON con esta forma exacta: "
    '{"skills": ["Skill1", "Skill2"]}  sin ningún texto adicional.'
)


# ---------------------------------------------------------------------------
# Proveedor 1: NUBE (API de Anthropic)
# ---------------------------------------------------------------------------

def _extraer_cloud(texto: str) -> list[str]:
    """Llama a la API de Anthropic para extraer las skills del texto."""
    from anthropic import Anthropic

    # La API key se lee de la variable de entorno, nunca se escribe en el código.
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta ANTHROPIC_API_KEY. Ponela en el archivo .env "
            "(mirá .env.example) o como variable de entorno."
        )

    cliente = Anthropic(api_key=api_key)
    respuesta = cliente.messages.create(
        model=config.MODELO_CLOUD,
        max_tokens=1000,
        system=INSTRUCCION,
        messages=[{"role": "user", "content": texto}],
    )
    # La respuesta trae bloques de contenido; el texto está en el primero.
    contenido = respuesta.content[0].text
    return _parsear_skills(contenido)


# ---------------------------------------------------------------------------
# Proveedor 2: LOCAL (Ollama)
# ---------------------------------------------------------------------------

def _extraer_local(texto: str) -> list[str]:
    """Llama a un modelo local vía Ollama para extraer las skills del texto."""
    import requests

    payload = {
        "model": config.MODELO_LOCAL,
        "messages": [
            {"role": "system", "content": INSTRUCCION},
            {"role": "user", "content": texto},
        ],
        "stream": False,      # queremos la respuesta completa de una, no en pedazos
        "format": "json",     # le pedimos a Ollama que devuelva JSON válido
    }
    respuesta = requests.post(config.OLLAMA_URL, json=payload, timeout=120)
    respuesta.raise_for_status()
    contenido = respuesta.json()["message"]["content"]
    return _parsear_skills(contenido)


# ---------------------------------------------------------------------------
# Utilidad compartida: leer el JSON que devuelve el modelo
# ---------------------------------------------------------------------------

def _parsear_skills(texto_respuesta: str) -> list[str]:
    """Extrae la lista de skills del texto que devolvió el modelo.

    Los LLM a veces agregan texto antes o después del JSON. Por eso buscamos el
    primer bloque JSON (objeto {...} o lista [...]) en vez de asumir que TODA la
    respuesta es JSON puro. Así es más robusto ante respuestas 'sucias'.
    """
    coincidencia = re.search(r"\{.*\}|\[.*\]", texto_respuesta, re.DOTALL)
    if not coincidencia:
        return []
    try:
        datos = json.loads(coincidencia.group(0))
    except json.JSONDecodeError:
        return []

    # Aceptamos tanto {"skills": [...]} como una lista [...] directa.
    if isinstance(datos, dict):
        datos = datos.get("skills", [])
    if not isinstance(datos, list):
        return []
    return [str(s).strip() for s in datos if str(s).strip()]


# ---------------------------------------------------------------------------
# La interfaz común: lo único que el resto del pipeline necesita llamar
# ---------------------------------------------------------------------------

def extraer_skills_con_llm(texto: str) -> list[str]:
    """Extrae skills usando el proveedor elegido en config.LLM_PROVIDER."""
    if config.LLM_PROVIDER == "cloud":
        return _extraer_cloud(texto)
    if config.LLM_PROVIDER == "local":
        return _extraer_local(texto)
    raise ValueError(
        f"LLM_PROVIDER desconocido: '{config.LLM_PROVIDER}'. Usá 'cloud' o 'local'."
    )

"""
CACHÉ DEL LLM
=============
Guarda, para cada texto de oferta ya procesado, las skills que devolvió el LLM.
Así no le pedimos dos veces lo mismo (importante porque el LLM local es lento).

La "llave" de cada entrada es una huella (hash) del TEXTO de la oferta, no su id.
¿Por qué del texto? Porque si la descripción cambia, queremos re-procesarla; si es
idéntica, reusamos. El hash cambia solo cuando el texto cambia.
"""

import json
import hashlib
from pathlib import Path

CARPETA_CACHE = Path(__file__).resolve().parent.parent / "data" / "cache"
RUTA_CACHE = CARPETA_CACHE / "llm_skills_cache.json"


def huella_texto(texto: str) -> str:
    """Devuelve una huella corta y única del texto (su hash SHA-256)."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def cargar_cache() -> dict:
    """Lee el caché del disco. Si no existe todavía, devuelve uno vacío."""
    if RUTA_CACHE.exists():
        with open(RUTA_CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_cache(cache: dict) -> None:
    """Escribe el caché al disco (crea la carpeta si hace falta)."""
    CARPETA_CACHE.mkdir(parents=True, exist_ok=True)
    with open(RUTA_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

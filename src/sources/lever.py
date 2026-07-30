"""
CONECTOR: LEVER (páginas de empresas)
=====================================
Otro ATS muy usado. Cada empresa tiene un "site name" y una API pública en JSON:

    https://api.lever.co/v0/postings/<EMPRESA>?mode=json

¿Cómo encontrás el nombre? En su página de carreras la URL suele ser
jobs.lever.co/spotify  → el nombre es "spotify".

La respuesta de Lever es una LISTA (no un objeto con clave "jobs"). El título del
puesto está en "text" y la ubicación en categories.location.
"""

import requests

from .base import normalizar, titulo_contiene_rol

API_URL = "https://api.lever.co/v0/postings/{empresa}"

# Nombres de ejemplo. Verificá y sumá los que quieras.
EMPRESAS = [
    "spotify",
    "netflix",
]


def buscar_en_empresa(empresa: str, rol: str) -> list[dict]:
    """Trae las vacantes de UNA empresa (Lever) que coincidan con el rol."""
    url = API_URL.format(empresa=empresa)
    respuesta = requests.get(url, params={"mode": "json"}, timeout=20)

    if respuesta.status_code == 404:
        return []
    respuesta.raise_for_status()

    ofertas = respuesta.json()   # ¡ojo! Lever devuelve una lista directamente
    resultados: list[dict] = []
    for o in ofertas:
        if titulo_contiene_rol(o.get("text", ""), rol):
            ubicacion = (o.get("categories") or {}).get("location")
            resultados.append(normalizar(
                source="lever",
                external_id=o.get("id"),
                title=o.get("text"),
                company=empresa,
                location=ubicacion,
                url=o.get("hostedUrl"),
                description_html=o.get("description", ""),
                raw=o,
            ))
    return resultados


def buscar(rol: str) -> list[dict]:
    """Recorre todas las empresas de EMPRESAS y junta sus vacantes para el rol."""
    resultados: list[dict] = []
    for empresa in EMPRESAS:
        resultados.extend(buscar_en_empresa(empresa, rol))
    return resultados

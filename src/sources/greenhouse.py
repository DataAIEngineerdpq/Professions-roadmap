"""
CONECTOR: GREENHOUSE (páginas de empresas)
==========================================
Muchas empresas publican sus vacantes con Greenhouse. Cada empresa tiene un "board
token" (un identificador corto) y una API pública en JSON, sin API key:

    https://boards-api.greenhouse.io/v1/boards/<TOKEN>/jobs?content=true

¿Cómo encontrás el token de una empresa? Entrá a su página de carreras. Si la URL es
del estilo  boards.greenhouse.io/stripe  entonces el token es "stripe".

Para agregar más empresas, sumá sus tokens a la lista EMPRESAS de abajo.
"""

import requests

from .base import normalizar, titulo_contiene_rol

API_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"

# Tokens de ejemplo. Verificá cada uno (algunos cambian con el tiempo) y sumá los que
# te interesen. Si un token ya no existe, el código lo salta sin romperse (ver abajo).
EMPRESAS = [
    "stripe",
    "airbnb",
    "gitlab",
]


def buscar_en_empresa(token: str, rol: str) -> list[dict]:
    """Trae las vacantes de UNA empresa que coincidan con el rol."""
    url = API_URL.format(token=token)
    respuesta = requests.get(url, params={"content": "true"}, timeout=20)

    # Si la empresa ya no tiene board público (404), devolvemos vacío en vez de romper.
    if respuesta.status_code == 404:
        return []
    respuesta.raise_for_status()

    ofertas = respuesta.json().get("jobs", [])
    resultados: list[dict] = []
    for o in ofertas:
        if titulo_contiene_rol(o.get("title", ""), rol):
            # La ubicación viene anidada: {"location": {"name": "Berlin"}}
            ubicacion = (o.get("location") or {}).get("name")
            resultados.append(normalizar(
                source="greenhouse",
                external_id=o.get("id"),
                title=o.get("title"),
                company=token,             # el token identifica a la empresa
                location=ubicacion,
                url=o.get("absolute_url"),
                description_html=o.get("content", ""),  # HTML de la descripción
                raw=o,
            ))
    return resultados


def buscar(rol: str) -> list[dict]:
    """Recorre todas las empresas de EMPRESAS y junta sus vacantes para el rol."""
    resultados: list[dict] = []
    for token in EMPRESAS:
        resultados.extend(buscar_en_empresa(token, rol))
    return resultados

"""
CONECTOR: REMOTIVE
==================
Board de empleos remotos (70k+ ofertas). API pública, sin API key.
Docs: https://github.com/remotive-com/remote-jobs-api
La lista viene en "jobs" y el título está en "title". Consejo de Remotive: no
consultar más de un par de veces al día (sus datos no cambian tan rápido).
"""

import requests

from .base import normalizar, titulo_contiene_rol

API_URL = "https://remotive.com/api/remote-jobs"


def buscar(rol: str) -> list[dict]:
    """Trae ofertas remotas de Remotive relacionadas al rol, ya normalizadas."""
    respuesta = requests.get(API_URL, params={"search": rol}, timeout=20)
    respuesta.raise_for_status()
    ofertas = respuesta.json().get("jobs", [])

    resultados: list[dict] = []
    for o in ofertas:
        if titulo_contiene_rol(o.get("title", ""), rol):
            resultados.append(normalizar(
                source="remotive",
                external_id=o.get("id"),
                title=o.get("title"),
                company=o.get("company_name"),
                location=o.get("candidate_required_location"),
                url=o.get("url"),
                description_html=o.get("description", ""),
                remote=True,
                raw=o,
            ))

    return resultados

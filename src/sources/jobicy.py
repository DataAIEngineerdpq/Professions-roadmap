"""
CONECTOR: JOBICY
================
Board de empleos remotos (mucho de América y Europa). API pública, sin API key.
Docs: https://jobicy.com/jobs-rss-feed
El parámetro "tag" busca en título y descripción. La lista viene en "jobs" y el
título del puesto está en "jobTitle".
"""

import requests

from .base import normalizar, titulo_contiene_rol

API_URL = "https://jobicy.com/api/v2/remote-jobs"


def buscar(rol: str, cantidad: int = 50) -> list[dict]:
    """Trae ofertas remotas de Jobicy relacionadas al rol, ya normalizadas."""
    # Jobicy permite buscar directo con "tag", así traemos menos basura desde el origen.
    respuesta = requests.get(
        API_URL, params={"count": cantidad, "tag": rol}, timeout=15
    )
    respuesta.raise_for_status()
    ofertas = respuesta.json().get("jobs", [])

    resultados: list[dict] = []
    for o in ofertas:
        # Aun con el "tag", filtramos por título para ser estrictos con el rol.
        if titulo_contiene_rol(o.get("jobTitle", ""), rol):
            resultados.append(normalizar(
                source="jobicy",
                external_id=o.get("id"),
                title=o.get("jobTitle"),
                company=o.get("companyName"),
                location=o.get("jobGeo"),
                url=o.get("url"),
                description_html=o.get("jobDescription", ""),
                remote=True,               # Jobicy es 100% remoto
                raw=o,
            ))

    return resultados

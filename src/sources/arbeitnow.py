"""
CONECTOR: ARBEITNOW
===================
Board de empleos de Europa. API pública, sin API key.
Docs: https://www.arbeitnow.com/api/job-board-api
La lista de empleos viene dentro de la clave "data". El título está en "title".
"""

import requests

from .base import normalizar, titulo_contiene_rol

API_URL = "https://www.arbeitnow.com/api/job-board-api"


def buscar(rol: str, max_paginas: int = 3) -> list[dict]:
    """Trae ofertas de Arbeitnow cuyo título contenga el rol, ya normalizadas."""
    resultados: list[dict] = []

    for pagina in range(1, max_paginas + 1):
        respuesta = requests.get(API_URL, params={"page": pagina}, timeout=15)
        respuesta.raise_for_status()
        ofertas = respuesta.json().get("data", [])

        if not ofertas:      # página vacía = no hay más resultados
            break

        for o in ofertas:
            if titulo_contiene_rol(o.get("title", ""), rol):
                resultados.append(normalizar(
                    source="arbeitnow",
                    external_id=o.get("slug"),
                    title=o.get("title"),
                    company=o.get("company_name"),
                    location=o.get("location"),
                    url=o.get("url"),
                    description_html=o.get("description", ""),
                    remote=o.get("remote"),
                    raw=o,
                ))

    return resultados

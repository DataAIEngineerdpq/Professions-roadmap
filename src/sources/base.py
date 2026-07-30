"""
BASE DE LOS CONECTORES
======================

Cada fuente (Arbeitnow, Jobicy, etc.) devuelve los datos con nombres distintos.
Este archivo define el "idioma común" al que TODAS las fuentes se traducen, para que
el resto del pipeline no tenga que saber de dónde vino cada oferta.

A ese formato común se le llama "esquema normalizado".
"""


def normalizar(
    source: str,
    external_id: str,
    title: str,
    company: str,
    location: str,
    url: str,
    description_html: str,
    remote: bool | None = None,
    raw: dict | None = None,
) -> dict:
    """Construye UNA oferta en el formato común.

    Fijate en la clave 'raw': ahí guardamos la oferta ORIGINAL tal como llegó de la
    fuente, sin tocar. Así respetamos la regla de oro de la ingesta (conservar el crudo)
    y además tenemos los campos comunes ya listos para el resto del pipeline.
    """
    return {
        "source": source,               # de qué fuente vino (ej: "arbeitnow")
        "external_id": str(external_id), # id único de la oferta DENTRO de esa fuente
        "title": title,                  # título del puesto
        "company": company,              # empresa
        "location": location,            # ubicación (texto libre)
        "remote": remote,                # True/False/None si no se sabe
        "url": url,                      # enlace para postularse
        "description_html": description_html,  # descripción cruda (con HTML); se limpia en el Paso 2
        "raw": raw or {},                # la oferta original completa, sin modificar
    }


def titulo_contiene_rol(titulo: str, rol: str) -> bool:
    """True si el título del puesto contiene el rol buscado (ignorando mayúsculas)."""
    return rol.lower() in (titulo or "").lower()

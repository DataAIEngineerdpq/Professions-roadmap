"""
UTILIDADES DE TEXTO COMPARTIDAS
===============================
Funciones que usan varios archivos del pipeline. Al vivir en un solo lugar,
si hay que corregir algo se corrige una vez (principio DRY: no te repitas).
"""

import re
import html


def limpiar_html(texto_html: str) -> str:
    """Convierte una descripción con HTML en texto plano legible."""
    # 1) Quitamos las etiquetas <...> reemplazándolas por un espacio.
    sin_etiquetas = re.sub(r"<[^>]+>", " ", texto_html or "")
    # 2) Convertimos entidades como &nbsp; o &amp; a su carácter real.
    texto = html.unescape(sin_etiquetas)
    # 3) Colapsamos espacios múltiples en uno solo y recortamos los bordes.
    return re.sub(r"\s+", " ", texto).strip()

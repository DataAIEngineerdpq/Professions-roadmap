"""
PASO 1 DEL PIPELINE: INGESTA
============================

Objetivo de este archivo:
  - Llamar a una API pública de empleos (Arbeitnow, gratis y sin login).
  - Buscar ofertas cuyo TÍTULO contenga el rol que nos interesa (ej: "data engineer").
  - Guardar las ofertas "crudas" (tal cual llegan) en data/raw/ como un archivo JSON.

Por qué guardamos "crudo":
  En Data Engineering se separa la ingesta (traer datos SIN modificarlos) del
  procesamiento (limpiarlos y transformarlos). Guardar el crudo nos deja re-procesar
  después sin tener que volver a golpear la API. A esto se le llama capa "raw" o "bronze".
"""

import json                      # para convertir datos Python <-> texto JSON
import datetime                  # para ponerle fecha/hora al archivo que guardamos
from pathlib import Path         # forma moderna y cómoda de manejar rutas de archivos

import requests                  # librería para hacer peticiones HTTP (llamar a la API)


# ---------------------------------------------------------------------------
# Configuración: qué buscamos y de dónde
# ---------------------------------------------------------------------------

# La API de Arbeitnow. Devuelve empleos en formato JSON, sin necesidad de API key.
API_URL = "https://www.arbeitnow.com/api/job-board-api"

# El rol que queremos. Cambiá esto por el que te interese ("data analyst", "backend", etc.)
ROL_BUSCADO = "data engineer"

# Cuántas páginas de resultados recorrer (cada página trae ~100 empleos).
# Empezá con pocas para no esperar mucho; luego podés subirlo.
MAX_PAGINAS = 3

# Carpeta donde dejaremos el archivo crudo. Se calcula relativa a este script,
# así funciona sin importar desde dónde ejecutes el programa.
CARPETA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


# ---------------------------------------------------------------------------
# Funciones: cada una hace UNA cosa. Así el código se lee y se prueba mejor.
# ---------------------------------------------------------------------------

def descargar_pagina(pagina: int) -> list[dict]:
    """Descarga una página de empleos de la API y devuelve la lista de ofertas.

    'pagina' es el número de página (1, 2, 3...).
    Devuelve una lista de diccionarios; cada diccionario es una oferta de empleo.
    """
    # Le pasamos el número de página como parámetro en la URL: ?page=1
    respuesta = requests.get(API_URL, params={"page": pagina}, timeout=15)

    # Si la API respondió con un error (404, 500...), esto lanza una excepción
    # y detiene el programa con un mensaje claro, en vez de continuar con datos rotos.
    respuesta.raise_for_status()

    # La respuesta viene en JSON. .json() la convierte en un diccionario de Python.
    # La API pone la lista de empleos dentro de la clave "data".
    datos = respuesta.json()
    return datos.get("data", [])


def contiene_rol(oferta: dict, rol: str) -> bool:
    """Devuelve True si el TÍTULO de la oferta contiene el rol buscado.

    Comparamos todo en minúsculas para que 'Data Engineer' y 'data engineer'
    se consideren iguales.
    """
    titulo = oferta.get("title", "").lower()
    return rol.lower() in titulo


def ingerir() -> list[dict]:
    """Recorre varias páginas, filtra por el rol y junta todas las ofertas que coinciden."""
    ofertas_encontradas: list[dict] = []

    for numero_pagina in range(1, MAX_PAGINAS + 1):
        print(f"Descargando página {numero_pagina}...")
        ofertas_de_la_pagina = descargar_pagina(numero_pagina)

        # Si una página viene vacía, no hay más resultados: cortamos.
        if not ofertas_de_la_pagina:
            print("  (página vacía, no hay más resultados)")
            break

        # Nos quedamos solo con las ofertas cuyo título contiene el rol.
        coincidencias = [o for o in ofertas_de_la_pagina if contiene_rol(o, ROL_BUSCADO)]
        print(f"  {len(coincidencias)} coincidencias de {len(ofertas_de_la_pagina)} ofertas")

        ofertas_encontradas.extend(coincidencias)

    return ofertas_encontradas


def guardar_crudo(ofertas: list[dict]) -> Path:
    """Guarda las ofertas en un archivo JSON dentro de data/raw/ y devuelve su ruta."""
    # Nos aseguramos de que la carpeta exista (si no, la crea).
    CARPETA_RAW.mkdir(parents=True, exist_ok=True)

    # Nombre de archivo con fecha y hora para no pisar descargas anteriores.
    # Ej: data_engineer_2026-07-30_14-05-33.json
    marca_tiempo = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre = f"{ROL_BUSCADO.replace(' ', '_')}_{marca_tiempo}.json"
    ruta = CARPETA_RAW / nombre

    # Escribimos el JSON. ensure_ascii=False conserva tildes y ñ; indent=2 lo deja legible.
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(ofertas, archivo, ensure_ascii=False, indent=2)

    return ruta


# ---------------------------------------------------------------------------
# Punto de entrada: esto se ejecuta cuando corrés `python src/ingest.py`
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Buscando ofertas de: '{ROL_BUSCADO}'\n")
    ofertas = ingerir()

    if not ofertas:
        print("\nNo se encontraron ofertas con ese rol. Probá con otro término.")
        return

    ruta = guardar_crudo(ofertas)
    print(f"\n✅ Listo: {len(ofertas)} ofertas guardadas en:\n   {ruta}")


# Esta línea hace que main() solo corra si ejecutás este archivo directamente,
# no si lo importás desde otro archivo. Es una convención estándar de Python.
if __name__ == "__main__":
    main()

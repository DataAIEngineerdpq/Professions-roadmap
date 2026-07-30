"""
PASO 1 DEL PIPELINE: INGESTA (multi-fuente)
===========================================

Este archivo es el ORQUESTADOR. No sabe hablar con ninguna API en particular:
solo le pide a cada conector (en src/sources/) que traiga sus ofertas del rol
buscado, junta todo en un formato común y lo guarda crudo en data/raw/.

Ventaja del diseño: para agregar una fuente nueva, creás un conector y lo sumás
al diccionario FUENTES. Este archivo casi no cambia.
"""

import json
import datetime
from pathlib import Path

# Importamos cada conector. Cada uno expone una función buscar(rol).
from sources import arbeitnow, jobicy, remotive, greenhouse, lever


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

ROL_BUSCADO = "data engineer"

# Diccionario de fuentes: nombre -> función que las trae.
# Comentá una línea para desactivar temporalmente una fuente.
FUENTES = {
    "arbeitnow": arbeitnow.buscar,
    "jobicy": jobicy.buscar,
    "remotive": remotive.buscar,
    "greenhouse": greenhouse.buscar,
    "lever": lever.buscar,
}

CARPETA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


# ---------------------------------------------------------------------------
# Lógica
# ---------------------------------------------------------------------------

def ingerir(rol: str) -> list[dict]:
    """Corre TODAS las fuentes y junta sus ofertas en una sola lista normalizada.

    Punto clave de robustez: envolvemos cada fuente en un try/except. Si una API
    se cae o cambia, esa fuente devuelve un error visible PERO las demás siguen.
    Un pipeline profesional nunca deja que una fuente rota tumbe a todas.
    """
    todas: list[dict] = []

    for nombre, buscar in FUENTES.items():
        try:
            ofertas = buscar(rol)
            print(f"  {nombre:12} → {len(ofertas)} ofertas")
            todas.extend(ofertas)
        except Exception as error:
            print(f"  {nombre:12} → ERROR: {error}")

    return todas


def deduplicar(ofertas: list[dict]) -> list[dict]:
    """Quita ofertas repetidas usando su URL como huella única."""
    vistas = set()
    unicas = []
    for o in ofertas:
        clave = o.get("url")
        if clave and clave not in vistas:
            vistas.add(clave)
            unicas.append(o)
    return unicas


def guardar_crudo(ofertas: list[dict], rol: str) -> Path:
    """Guarda todas las ofertas normalizadas en data/raw/ con fecha y hora."""
    CARPETA_RAW.mkdir(parents=True, exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre = f"{rol.replace(' ', '_')}_{marca}.json"
    ruta = CARPETA_RAW / nombre
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(ofertas, archivo, ensure_ascii=False, indent=2)
    return ruta


def main() -> None:
    print(f"Buscando '{ROL_BUSCADO}' en {len(FUENTES)} fuentes:\n")
    ofertas = ingerir(ROL_BUSCADO)

    antes = len(ofertas)
    ofertas = deduplicar(ofertas)
    print(f"\nTotal: {antes} ofertas ({antes - len(ofertas)} duplicadas quitadas)")

    if not ofertas:
        print("No se encontró nada. Probá con otro rol.")
        return

    ruta = guardar_crudo(ofertas, ROL_BUSCADO)
    print(f"✅ {len(ofertas)} ofertas guardadas en:\n   {ruta}")


if __name__ == "__main__":
    main()

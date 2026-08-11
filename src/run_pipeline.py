"""
ORQUESTADOR DEL PIPELINE
========================

Ejecuta las etapas del pipeline de punta a punta, o solo las que le pidas.

  python src/run_pipeline.py              → todas las etapas
  python src/run_pipeline.py --desde curar → salta la ingesta y el LLM (rápido)
  python src/run_pipeline.py --solo arbol  → solo reconstruye el árbol

POR QUÉ ETAPAS SELECTIVAS: la etapa de extracción con LLM es lenta (minutos).
Las demás son de segundos. Separarlas te deja iterar rápido en la parte liviana
sin repetir la pesada. Además el pipeline es IDEMPOTENTE (correrlo dos veces da
el mismo resultado) y REANUDABLE (el caché evita rehacer lo ya procesado).
"""

import sys
import json
import glob
import argparse
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent

ETAPAS = ["ingesta", "extraer", "curar", "arbol"]


def correr_script(nombre: str) -> bool:
    """Ejecuta otro script del pipeline. Devuelve True si salió bien."""
    print(f"\n{'='*60}\n  ETAPA: {nombre}\n{'='*60}")
    resultado = subprocess.run([sys.executable, str(SRC / nombre)])
    if resultado.returncode != 0:
        print(f"  ⚠️  {nombre} terminó con error.")
        return False
    return True


def etapa_curar() -> bool:
    """Auto-curación: aplica los filtros y hace crecer el diccionario solo."""
    print(f"\n{'='*60}\n  ETAPA: auto-curación\n{'='*60}")
    sys.path.insert(0, str(SRC))
    import auto_curate

    # Última tanda de candidatas descubiertas por el LLM
    archivos = sorted(glob.glob(str(RAIZ / "data" / "processed" / "candidates_*.json")))
    if not archivos:
        print("  No hay candidatas todavía (corré la etapa 'extraer' primero).")
        return True

    with open(archivos[-1], encoding="utf-8") as f:
        candidatas = json.load(f)

    # Cuántas ofertas hay, para el umbral adaptativo
    crudos = sorted(glob.glob(str(RAIZ / "data" / "raw" / "*.json")))
    crudos = [c for c in crudos if not Path(c).name.startswith("_")]
    total_ofertas = len(json.load(open(crudos[-1], encoding="utf-8"))) if crudos else 0

    with open(SRC / "skills.json", encoding="utf-8") as f:
        diccionario = json.load(f)

    aprobadas, stats = auto_curate.curar(candidatas, total_ofertas, diccionario)

    print(f"  Candidatas crudas:      {stats['crudas']}")
    print(f"  Tras normalizar:        {stats['tras_normalizar']}")
    print(f"  Tras reglas:            {stats['tras_reglas']}")
    print(f"  Umbral (≥{stats['umbral']} ofertas):    {stats['tras_frecuencia']}")
    print(f"  Tras validación LLM:    {stats['aprobadas']}")

    agregadas = auto_curate.agregar_al_diccionario(aprobadas)
    print(f"\n  ✅ {agregadas} skills nuevas agregadas al diccionario automáticamente.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline del roadmap de skills")
    parser.add_argument("--desde", choices=ETAPAS, help="empezar desde esta etapa")
    parser.add_argument("--solo", choices=ETAPAS, help="correr solo esta etapa")
    args = parser.parse_args()

    if args.solo:
        etapas = [args.solo]
    elif args.desde:
        etapas = ETAPAS[ETAPAS.index(args.desde):]
    else:
        etapas = ETAPAS

    print(f"Etapas a ejecutar: {' → '.join(etapas)}")

    for etapa in etapas:
        if etapa == "ingesta":
            if not correr_script("ingest.py"):
                break
        elif etapa == "extraer":
            if not correr_script("enrich_skills.py"):
                break
        elif etapa == "curar":
            if not etapa_curar():
                break
        elif etapa == "arbol":
            if not correr_script("categorize_skills.py"):
                break

    print(f"\n{'='*60}\n  ✅ Pipeline terminado\n{'='*60}")


if __name__ == "__main__":
    main()

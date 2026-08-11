"""
RECONSTRUIR EL DICCIONARIO DESDE LAS CANDIDATAS (con filtro de ruido)
=====================================================================

Recupera las skills descubiertas por el LLM (data/processed/candidates_*.json)
y las agrega al diccionario, PERO filtrando automáticamente el ruido que
detectamos que rompía la categorización: nombres de empresa, frases genéricas
de marketing, y duplicados en español.

Te muestra qué va a agregar y qué va a descartar ANTES de escribir nada.
"""

import json
import glob
from pathlib import Path

RUTA_DICCIONARIO = Path(__file__).resolve().parent / "skills.json"
CARPETA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"

# Ruido detectado: no son skills técnicas. Se descartan automáticamente.
# (Comparación en minúsculas.)
RUIDO = {
    # Nombres de empresa / producto ajeno al stack
    "stripe", "clari", "stripe payments api", "google analytics 4",
    # Sectores o modelos de negocio, no tecnologías
    "e-commerce", "ridesharing", "pricing models", "product development",
    # Frases genéricas de oferta
    "ai features", "ai tools", "platforms", "services", "backend code",
    "incident handling", "compliance", "governance", "automation",
    "data integrity", "data performance", "scalability", "scalable systems",
    "experimentation", "data platform", "data products", "big data",
    "cloud", "cloud computing", "cloud services", "cloud native engineering",
    "artificial intelligence", "data engineer", "data engineering",
    "api", "api architectures", "real-time ai/ml workloads",
    "data stewardship", "análisis de datos alternativos",
    "tecnología de análisis de datos", "ia",
    # Variantes que ya cubre otra entrada
    "nosql databases",
}


def cargar_diccionario() -> dict:
    with open(RUTA_DICCIONARIO, encoding="utf-8") as f:
        return json.load(f)


def cargar_todas_las_candidatas() -> dict:
    """Junta las candidatas de TODOS los archivos candidates_*.json."""
    archivos = sorted(glob.glob(str(CARPETA_PROCESSED / "candidates_*.json")))
    if not archivos:
        raise FileNotFoundError("No hay candidates_*.json en data/processed/")
    todas: dict[str, int] = {}
    for ruta in archivos:
        with open(ruta, encoding="utf-8") as f:
            for skill, cuenta in json.load(f).items():
                todas[skill] = max(todas.get(skill, 0), cuenta)
    return todas


def ya_conocida(skill: str, diccionario: dict) -> bool:
    s = skill.lower()
    if s in {c.lower() for c in diccionario}:
        return True
    for variantes in diccionario.values():
        if s in {v.lower() for v in variantes}:
            return True
    return False


def main() -> None:
    diccionario = cargar_diccionario()
    candidatas = cargar_todas_las_candidatas()

    print(f"Diccionario actual: {len(diccionario)} skills.")
    print(f"Candidatas encontradas: {len(candidatas)}\n")

    a_agregar = []
    descartadas = []
    for skill in candidatas:
        if ya_conocida(skill, diccionario):
            continue
        if skill.lower() in RUIDO:
            descartadas.append(skill)
        else:
            a_agregar.append(skill)

    print(f"❌ Se DESCARTAN {len(descartadas)} por ruido:")
    print(f"   {', '.join(descartadas)}\n")
    print(f"✅ Se AGREGAN {len(a_agregar)} skills:")
    print(f"   {', '.join(a_agregar)}\n")

    confirmacion = input("¿Aplicar estos cambios? Escribí 'si': ").strip().lower()
    if confirmacion != "si":
        print("Cancelado. No se cambió nada.")
        return

    for skill in a_agregar:
        diccionario[skill] = [skill.lower()]

    with open(RUTA_DICCIONARIO, "w", encoding="utf-8") as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=2)

    print(f"\n✅ El diccionario ahora tiene {len(diccionario)} skills.")
    print("   IMPORTANTE: hacé commit ahora para no volver a perderlo:")
    print('   git add src/skills.json && git commit -m "Rebuild skills dictionary from candidates"')


if __name__ == "__main__":
    main()

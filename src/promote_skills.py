"""
SUB-PASO 2b.3: PROMOVER CANDIDATAS AL DICCIONARIO (human-in-the-loop)
====================================================================

Lee las skills candidatas que descubrió el LLM (el último candidates_*.json),
te las muestra una por una, y agrega al diccionario (skills.json) las que aprobás.

Así el diccionario CRECE con lo que la IA encontró, pero solo con tu visto bueno.
Después de promover una skill, el diccionario rápido ya la reconoce y deja de
aparecer como candidata: el círculo se cierra.
"""

import json
import glob
from pathlib import Path

CARPETA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
RUTA_DICCIONARIO = Path(__file__).resolve().parent / "skills.json"


def cargar_diccionario() -> dict:
    with open(RUTA_DICCIONARIO, encoding="utf-8") as f:
        return json.load(f)


def guardar_diccionario(diccionario: dict) -> None:
    with open(RUTA_DICCIONARIO, "w", encoding="utf-8") as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=2)


def cargar_ultimas_candidatas() -> dict:
    archivos = sorted(glob.glob(str(CARPETA_PROCESSED / "candidates_*.json")))
    if not archivos:
        raise FileNotFoundError(
            "No hay candidates_*.json. Corré antes: python src/enrich_skills.py"
        )
    with open(archivos[-1], encoding="utf-8") as f:
        return json.load(f)


def ya_conocida(skill: str, diccionario: dict) -> bool:
    """True si la skill ya está en el diccionario (como canónica o variante)."""
    s = skill.lower()
    if s in {c.lower() for c in diccionario}:
        return True
    for variantes in diccionario.values():
        if s in {v.lower() for v in variantes}:
            return True
    return False


def promover(diccionario: dict, aprobadas: list[str]) -> int:
    """Agrega las skills aprobadas al diccionario. Devuelve cuántas se agregaron.

    Cada skill nueva entra como nombre canónico con su versión en minúscula como
    primera variante. Las que ya existían se saltan (no duplicamos).
    """
    agregadas = 0
    for skill in aprobadas:
        if not ya_conocida(skill, diccionario):
            diccionario[skill] = [skill.lower()]
            agregadas += 1
    return agregadas


def main() -> None:
    diccionario = cargar_diccionario()
    candidatas = cargar_ultimas_candidatas()

    print(f"Diccionario actual: {len(diccionario)} skills.")
    print("Revisá cada candidata:  [s] agregar   [n] ignorar   [q] terminar\n")

    aprobadas: list[str] = []
    for skill, cuenta in candidatas.items():
        # Si por algún motivo ya la conocemos, la saltamos sin preguntar.
        if ya_conocida(skill, diccionario):
            continue
        respuesta = input(f"  ¿Agregar '{skill}'  (apareció en {cuenta} ofertas)? [s/n/q]: ").strip().lower()
        if respuesta == "q":
            break
        if respuesta == "s":
            aprobadas.append(skill)

    if not aprobadas:
        print("\nNo agregaste ninguna skill. El diccionario queda igual.")
        return

    cuantas = promover(diccionario, aprobadas)
    guardar_diccionario(diccionario)
    print(f"\n✅ Agregadas {cuantas} skills nuevas: {', '.join(aprobadas)}")
    print(f"   El diccionario ahora tiene {len(diccionario)} skills.")


if __name__ == "__main__":
    main()

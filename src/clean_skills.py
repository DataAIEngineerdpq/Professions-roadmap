"""
LIMPIADOR DE DICCIONARIO (human-in-the-loop, igual que promote_skills.py)
==========================================================================
Te muestra cada skill del diccionario, una por una, y podés sacarla si no es
una skill técnica real (nombres de empresa, frases de marketing, duplicados
en otro idioma, etc.). Esto reduce el ruido que confunde al LLM más adelante.
"""

import json
from pathlib import Path

RUTA_DICCIONARIO = Path(__file__).resolve().parent / "skills.json"


def main() -> None:
    with open(RUTA_DICCIONARIO, encoding="utf-8") as f:
        diccionario = json.load(f)

    print(f"Diccionario actual: {len(diccionario)} skills.")
    print("Revisá cada una:  [Enter] mantener   [n] SACAR   [q] terminar\n")

    a_sacar = []
    for skill in list(diccionario.keys()):
        respuesta = input(f"  '{skill}'  ¿sacar? [Enter=no / n=sí / q=terminar]: ").strip().lower()
        if respuesta == "q":
            break
        if respuesta == "n":
            a_sacar.append(skill)

    if not a_sacar:
        print("\nNo se sacó nada. El diccionario queda igual.")
        return

    for skill in a_sacar:
        del diccionario[skill]

    with open(RUTA_DICCIONARIO, "w", encoding="utf-8") as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Se sacaron {len(a_sacar)} entradas: {', '.join(a_sacar)}")
    print(f"   El diccionario ahora tiene {len(diccionario)} skills.")


if __name__ == "__main__":
    main()

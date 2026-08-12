"""
DIAGNÓSTICO: ver qué devuelve REALMENTE el LLM al clasificar un lote
====================================================================
Toma 8 skills que sabemos que fallaron y muestra la respuesta cruda del modelo,
sin procesar. Así vemos con nuestros ojos qué está pasando, en vez de suponer.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import categorize_skills as c

# Skills que fallaron en tu última corrida (bloque contiguo del final)
LOTE_PROBLEMA = ["React", "Angular", "Vue.js", "Node.js", "Express", "MongoDB", "HTML", "CSS"]


def main() -> None:
    texto_entrada = "Skills a clasificar:\n" + "\n".join(f"- {s}" for s in LOTE_PROBLEMA)

    print("ENTRADA que le mandamos al modelo:")
    print("-" * 60)
    print(texto_entrada)
    print("-" * 60)
    print("\nLlamando al LLM...\n")

    contenido = c.llamar_llm(texto_entrada)

    print("RESPUESTA CRUDA del modelo (sin procesar):")
    print("=" * 60)
    print(contenido)
    print("=" * 60)

    print("\nAhora vemos cómo la interpreta nuestro código:")
    resultado = c.clasificar_lote(LOTE_PROBLEMA)
    print(f"\nSkills que nuestro código logró extraer: {len(resultado)} de {len(LOTE_PROBLEMA)}")
    print(json.dumps(resultado, ensure_ascii=False, indent=2)[:800])

    faltantes = [s for s in LOTE_PROBLEMA if s not in resultado]
    if faltantes:
        print(f"\n⚠️  No aparecieron: {faltantes}")
        print("   → Comparalo con la respuesta cruda de arriba para ver por qué.")


if __name__ == "__main__":
    main()

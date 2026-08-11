"""
SUB-PASO 3.1: CATEGORIZAR SKILLS EN UN ÁRBOL (categoría -> nivel -> skills)
===========================================================================

DISEÑO (v2, corrige el problema de categorías duplicadas de la v1):

En vez de pedirle al LLM que arme el árbol completo de una sola vez (tarea muy
grande y abierta para un modelo local chico, que terminaba "olvidando" categorías
ya creadas e inventando duplicados), hacemos dos cosas:

  1) Le damos una lista de categorías FIJA (no inventa nuevas) -> elección
     múltiple, mucho más fácil de acertar que generación libre.
  2) Clasificamos en LOTES chicos (~15 skills a la vez), no las 98 juntas.

El LLM nos devuelve una clasificación PLANA (skill -> categoría + nivel). El
árbol anidado lo construye nuestro propio código Python al final, no el LLM.
Como es un diccionario de Python, es IMPOSIBLE que haya categorías duplicadas:
la estructura de datos lo impide por construcción, no por suerte.
"""

import re
import json
from pathlib import Path

import config

RUTA_DICCIONARIO = Path(__file__).resolve().parent / "skills.json"
RUTA_SALIDA = Path(__file__).resolve().parent.parent / "data" / "processed" / "roadmap_tree.json"

NIVELES_VALIDOS = ["Fundamento", "Intermedio", "Avanzado"]

# Lista FIJA de categorías. El LLM elige entre estas, no inventa nuevas.
# Podés editar esta lista vos mismo si querés otras categorías.
CATEGORIAS = [
    "Lenguajes",
    "Bases de Datos",
    "Orquestación",
    "Cloud",
    "Streaming",
    "Procesamiento Distribuido",
    "DevOps/Infraestructura",
    "BI/Analytics",
    "Machine Learning/IA",
    "Arquitectura y Gobernanza de Datos",
    "Otras",
]

TAMANO_LOTE = 8  # lotes chicos: si uno falla, se pierde menos y es más fácil de acertar

INSTRUCCION = (
    "Sos un arquitecto de curricula de Data Engineering. Para cada skill de la "
    "lista, elegí EXACTAMENTE una categoría de esta lista cerrada (no inventes "
    f"otras): {CATEGORIAS}. También asignale un nivel, que debe ser EXACTAMENTE "
    'una de: "Fundamento", "Intermedio", "Avanzado". '
    "Respondé SOLO con un objeto JSON plano (una entrada por skill), sin texto "
    'adicional, con esta forma exacta: '
    '{"NombreSkill": {"categoria": "CategoriaElegida", "nivel": "NivelElegido"}}'
)


def cargar_skills() -> list[str]:
    with open(RUTA_DICCIONARIO, encoding="utf-8") as f:
        diccionario = json.load(f)
    return list(diccionario.keys())


def en_lotes(lista: list, tamano: int):
    """Parte una lista en trozos de a 'tamano' elementos."""
    for i in range(0, len(lista), tamano):
        yield lista[i:i + tamano]


def llamar_llm(texto_entrada: str) -> str:
    """Hace UNA llamada al proveedor activo y devuelve el texto de respuesta."""
    if config.LLM_PROVIDER == "cloud":
        from anthropic import Anthropic
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Falta ANTHROPIC_API_KEY en .env")
        cliente = Anthropic(api_key=api_key)
        respuesta = cliente.messages.create(
            model=config.MODELO_CLOUD,
            max_tokens=2000,
            system=INSTRUCCION,
            messages=[{"role": "user", "content": texto_entrada}],
        )
        return respuesta.content[0].text
    else:
        import requests
        payload = {
            "model": config.MODELO_LOCAL,
            "messages": [
                {"role": "system", "content": INSTRUCCION},
                {"role": "user", "content": texto_entrada},
            ],
            "stream": False,
            "format": "json",
            "options": {"num_predict": 4096, "num_ctx": 8192},
        }
        r = requests.post(config.OLLAMA_URL, json=payload, timeout=config.OLLAMA_TIMEOUT)
        r.raise_for_status()
        return r.json()["message"]["content"]


def clasificar_lote(skills_lote: list[str]) -> dict:
    """Clasifica UN lote chico de skills. Devuelve {skill: {categoria, nivel}}.

    Si algo sale mal, MOSTRAMOS la respuesta cruda del modelo (recortada) en vez
    de fallar en silencio. Sin esto, un lote que falla es una caja negra: no
    sabés si el modelo no respondió, respondió mal formado, o qué pasó.
    """
    texto_entrada = "Skills a clasificar:\n" + "\n".join(f"- {s}" for s in skills_lote)
    contenido = llamar_llm(texto_entrada)

    coincidencia = re.search(r"\{.*\}", contenido, re.DOTALL)
    if not coincidencia:
        print(f"    ⚠️  Lote sin JSON reconocible. Respuesta cruda del modelo:")
        print(f"       {contenido[:300]!r}")
        return {}

    try:
        resultado = json.loads(coincidencia.group(0))
    except json.JSONDecodeError as error:
        print(f"    ⚠️  JSON mal formado ({error}). Respuesta cruda:")
        print(f"       {coincidencia.group(0)[:300]!r}")
        return {}

    if not resultado:
        print(f"    ⚠️  El modelo devolvió un JSON vacío para este lote.")

    return resultado


def construir_arbol(clasificacion_plana: dict) -> dict:
    """Convierte {skill: {categoria, nivel}} en el árbol anidado categoría->nivel->skills.

    Como armamos el árbol nosotros (no el LLM), es estructuralmente imposible
    tener categorías duplicadas: es un dict de Python, cada clave existe una vez.
    """
    arbol: dict = {}
    for skill, info in clasificacion_plana.items():
        categoria = info.get("categoria") if isinstance(info, dict) else None
        nivel = info.get("nivel") if isinstance(info, dict) else None

        if categoria not in CATEGORIAS:
            categoria = "Otras"
        if nivel not in NIVELES_VALIDOS:
            nivel = "Intermedio"

        arbol.setdefault(categoria, {n: [] for n in NIVELES_VALIDOS})
        if skill not in arbol[categoria][nivel]:
            arbol[categoria][nivel].append(skill)

    return arbol


def reincorporar_omitidas(arbol: dict, skills_originales: list[str]) -> tuple[dict, list[str]]:
    """Si algún lote falló y dejó skills sin clasificar, las suma a 'Sin Clasificar'
    en vez de perderlas. Devuelve el árbol y la lista de omitidas (para avisar)."""
    vistas = {s for niveles in arbol.values() for lst in niveles.values() for s in lst}
    faltantes = [s for s in skills_originales if s not in vistas]
    if faltantes:
        arbol.setdefault("Sin Clasificar", {n: [] for n in NIVELES_VALIDOS})
        arbol["Sin Clasificar"]["Intermedio"].extend(faltantes)
    return arbol, faltantes


def main() -> None:
    skills = cargar_skills()
    lotes = list(en_lotes(skills, TAMANO_LOTE))
    print(f"Clasificando {len(skills)} skills en {len(lotes)} lotes de hasta {TAMANO_LOTE}...\n")

    clasificacion_plana: dict = {}
    for i, lote in enumerate(lotes, start=1):
        print(f"  Lote {i}/{len(lotes)} ({len(lote)} skills)...")
        resultado_lote = clasificar_lote(lote)
        clasificacion_plana.update(resultado_lote)

    arbol = construir_arbol(clasificacion_plana)
    arbol, faltantes = reincorporar_omitidas(arbol, skills)

    if faltantes:
        print(f"\n⚠️  {len(faltantes)} skills sin clasificar (algún lote falló): {faltantes}")
        print("   → Se agregaron a 'Sin Clasificar'.\n")
    else:
        print("\n✅ Las 100% de las skills quedaron clasificadas.\n")

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
        json.dump(arbol, f, ensure_ascii=False, indent=2)

    for categoria, niveles in arbol.items():
        total = sum(len(v) for v in niveles.values())
        print(f"  {categoria:35} ({total} skills)")

    print(f"\n✅ Árbol guardado en:\n   {RUTA_SALIDA}")


if __name__ == "__main__":
    main()

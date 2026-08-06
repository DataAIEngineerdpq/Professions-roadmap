"""
SUB-PASO 2a.3: EXTRACTOR DE SKILLS
==================================

Objetivo: recorrer cada oferta cruda, y usando el diccionario (skills.json),
detectar qué skills menciona. El resultado —cada oferta con su lista de skills—
es el insumo directo del árbol/roadmap.

Esto convierte la capa "bronze" (crudo) en la capa "silver" (limpio y estructurado).
Leemos de data/raw/ y escribimos en data/processed/. Nunca tocamos el crudo original.
"""

import re
import json
import glob
import datetime
from pathlib import Path

from text_utils import limpiar_html

CARPETA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
CARPETA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
RUTA_DICCIONARIO = Path(__file__).resolve().parent / "skills.json"


def cargar_diccionario() -> dict:
    """Carga skills.json: nombre canónico -> lista de variantes."""
    with open(RUTA_DICCIONARIO, encoding="utf-8") as f:
        return json.load(f)


def compilar_patrones(diccionario: dict) -> dict:
    """Prepara un buscador (regex) por cada variante de cada skill.

    Aquí está la decisión clave. NO buscamos la skill como simple 'texto contenido',
    porque eso daría FALSOS POSITIVOS: buscar 'sql' como subcadena lo encontraría
    dentro de 'postgresql', 'mysql' y 'nosql', y contaría SQL donde no corresponde.

    La solución es exigir "límites de palabra": que antes y después del término no
    haya otra letra o número. Así 'sql' coincide con 'SQL' suelto, pero NO dentro de
    'postgresql'. El patrón (?<![a-z0-9]) ... (?![a-z0-9]) hace exactamente eso.
    """
    patrones: dict[str, list] = {}
    for canonica, variantes in diccionario.items():
        lista = []
        for variante in variantes:
            patron = r"(?<![a-z0-9])" + re.escape(variante.lower()) + r"(?![a-z0-9])"
            lista.append(re.compile(patron))
        patrones[canonica] = lista
    return patrones


def extraer_skills(texto: str, patrones: dict) -> list[str]:
    """Devuelve la lista de skills canónicas encontradas en el texto."""
    texto = texto.lower()
    encontradas = []
    for canonica, lista_regex in patrones.items():
        # any(...) = si CUALQUIERA de las variantes aparece, la skill está presente.
        if any(regex.search(texto) for regex in lista_regex):
            encontradas.append(canonica)
    return encontradas


def cargar_ultimo_crudo() -> tuple[str, list[dict]]:
    """Abre el JSON más reciente de data/raw/ (ignorando archivos que empiecen con _)."""
    archivos = sorted(glob.glob(str(CARPETA_RAW / "*.json")))
    archivos = [a for a in archivos if not Path(a).name.startswith("_")]
    if not archivos:
        raise FileNotFoundError("No hay archivos en data/raw/. Corré antes src/ingest.py")
    ruta = archivos[-1]
    with open(ruta, encoding="utf-8") as f:
        return ruta, json.load(f)


def procesar() -> None:
    diccionario = cargar_diccionario()
    patrones = compilar_patrones(diccionario)
    ruta_origen, ofertas = cargar_ultimo_crudo()

    print(f"Procesando {len(ofertas)} ofertas con {len(diccionario)} skills del diccionario...\n")

    resultado = []
    conteo_global: dict[str, int] = {}

    for oferta in ofertas:
        texto = limpiar_html(oferta.get("description_html", ""))
        skills = extraer_skills(texto, patrones)

        # Guardamos una versión limpia y liviana de la oferta (sin el HTML pesado).
        resultado.append({
            "source": oferta.get("source"),
            "title": oferta.get("title"),
            "company": oferta.get("company"),
            "location": oferta.get("location"),
            "url": oferta.get("url"),
            "skills": skills,
        })

        # Vamos contando en cuántas ofertas aparece cada skill.
        for s in skills:
            conteo_global[s] = conteo_global.get(s, 0) + 1

    # Guardamos el resultado en la capa "silver".
    CARPETA_PROCESSED.mkdir(parents=True, exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta_salida = CARPETA_PROCESSED / f"skills_{marca}.json"
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    # Mostramos el ranking de skills más pedidas (ahora sí, skills limpias).
    print("Skills más pedidas (en cuántas ofertas aparecen):")
    for skill, cuenta in sorted(conteo_global.items(), key=lambda x: -x[1]):
        print(f"  {skill:20} {cuenta}")

    print(f"\n✅ Resultado guardado en:\n   {ruta_salida}")


if __name__ == "__main__":
    procesar()

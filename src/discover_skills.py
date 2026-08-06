"""
SUB-PASO 2a.1: DESCUBRIDOR DE SKILLS CANDIDATAS
===============================================

Objetivo: antes de decidir qué skills buscar, este script LEE tus ofertas ya
descargadas y saca a la superficie los términos que más se repiten. Así ves con
tus propios ojos qué skills están pidiendo las empresas, sin adivinar nada.

No decide qué es una skill: solo te muestra candidatos. Vos (con ayuda del LLM más
adelante) elegís cuáles pasan al diccionario. A eso se le llama "human-in-the-loop":
la máquina propone, el humano dispone.
"""

import re
import html
import json
import glob
from pathlib import Path
from collections import Counter

CARPETA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# Palabras comunes del inglés (y algo de alemán) que NO son skills. Las ignoramos
# para que no ensucien el ranking. Esta lista se puede ampliar cuando veas ruido.
PALABRAS_IGNORADAS = {
    "the", "and", "for", "with", "you", "our", "your", "will", "are", "not",
    "have", "has", "this", "that", "from", "was", "were", "als", "und",
    "die", "der", "das", "mit", "von", "für", "ein", "eine", "work", "team",
    "role", "experience", "skills", "data", "including", "such", "using", "use",
    "new", "who", "all", "can", "help", "make", "more", "across", "within",
    "into", "these", "their", "them", "they", "what", "when", "where", "which",
    "about", "also", "well", "years", "year", "strong", "good", "best", "like",
    "join", "looking", "build", "building", "working", "solutions", "products",
    "product", "business", "company", "platform", "engineering", "engineer",
    "technical", "technologies", "technology", "systems", "system", "tools",
    "tool", "environment", "ability", "quality", "high", "real", "time",
    "management", "manage", "support", "develop", "development", "design",
    # Ruido detectado en tus 19 ofertas reales:
    "in", "an", "of", "on", "to", "we", "is", "as", "or", "at", "if", "be",
    "it", "us", "by", "do", "re", "ll", "teams", "impact", "practices",
    "drive", "requirements", "deliver", "opportunity", "services",
    "performance", "engineers", "platforms", "world", "culture", "key",
}


def limpiar_html(texto_html: str) -> str:
    """Convierte una descripción con HTML en texto plano legible."""
    # 1) Quitamos las etiquetas <...> reemplazándolas por un espacio.
    sin_etiquetas = re.sub(r"<[^>]+>", " ", texto_html or "")
    # 2) Convertimos entidades como &nbsp; o &amp; a su carácter real.
    texto = html.unescape(sin_etiquetas)
    # 3) Colapsamos espacios múltiples en uno solo y recortamos los bordes.
    return re.sub(r"\s+", " ", texto).strip()


def tokenizar(texto: str) -> list[str]:
    """Parte el texto en palabras/términos, en minúsculas.

    El patrón acepta letras y números, y permite separadores internos como
    + # / . -  para capturar términos técnicos como 'ci/cd', 'node.js' o 'c#'.
    """
    return re.findall(r"[a-z0-9]+(?:[+#./\-][a-z0-9]+)*", texto.lower())


def descubrir(ofertas: list[dict], top: int = 40) -> list[tuple[str, int]]:
    """Cuenta en CUÁNTAS ofertas aparece cada término y devuelve los más frecuentes.

    Ojo: contamos por OFERTA, no por repetición. Si 'python' aparece 5 veces en una
    misma oferta, cuenta 1. Lo que nos importa es en cuántas ofertas se pide, que es
    justo la señal de qué tan demandada está una skill.
    """
    conteo: Counter = Counter()
    for oferta in ofertas:
        texto = limpiar_html(oferta.get("description_html", ""))
        # set(...) elimina repetidos DENTRO de una misma oferta.
        terminos_unicos = {
            t for t in tokenizar(texto)
            if t not in PALABRAS_IGNORADAS and not t.isdigit() and len(t) >= 3
        }
        for termino in terminos_unicos:
            conteo[termino] += 1
    return conteo.most_common(top)


def cargar_ultimo_crudo() -> list[dict]:
    """Abre el archivo JSON más reciente de data/raw/."""
    archivos = sorted(glob.glob(str(CARPETA_RAW / "*.json")))
    # Ignoramos archivos de muestra que empiecen con "_".
    archivos = [a for a in archivos if not Path(a).name.startswith("_")]
    if not archivos:
        raise FileNotFoundError("No hay archivos en data/raw/. Corré antes src/ingest.py")
    with open(archivos[-1], encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    ofertas = cargar_ultimo_crudo()
    print(f"Analizando {len(ofertas)} ofertas...\n")
    print(f"{'TÉRMINO':22} EN CUÁNTAS OFERTAS")
    print("-" * 42)
    for termino, cuenta in descubrir(ofertas):
        print(f"{termino:22} {cuenta}")
    print("\nRevisá esta lista y marcá cuáles son skills reales para el diccionario.")


if __name__ == "__main__":
    main()

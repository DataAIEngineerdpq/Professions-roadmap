"""
PRUEBA DE HUMO DEL LLM
======================
Hace UNA sola llamada real al proveedor elegido (cloud o local), sobre la primera
oferta de tu último archivo crudo. Sirve para confirmar que tu configuración
(API key o Ollama) funciona ANTES de procesar todas las ofertas.
"""

import sys
import json
import glob
from pathlib import Path

import config
from text_utils import limpiar_html
from llm_extractor import extraer_skills_con_llm

CARPETA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def main() -> None:
    # Buscar el último archivo crudo
    archivos = sorted(glob.glob(str(CARPETA_RAW / "*.json")))
    archivos = [a for a in archivos if not Path(a).name.startswith("_")]
    if not archivos:
        print("No hay archivos en data/raw/. Corré antes: python src/ingest.py")
        sys.exit(1)

    ofertas = json.load(open(archivos[-1], encoding="utf-8"))
    if not ofertas:
        print("El archivo no tiene ofertas.")
        sys.exit(1)

    oferta = ofertas[0]
    texto = limpiar_html(oferta.get("description_html", ""))

    print(f"Proveedor activo: {config.LLM_PROVIDER}")
    print(f"Oferta de prueba: {oferta.get('title')} @ {oferta.get('company')}\n")
    print("Llamando al LLM (esto puede tardar unos segundos)...\n")

    # Envolvemos en try/except para dar un mensaje claro si algo falla.
    try:
        skills = extraer_skills_con_llm(texto)
    except Exception as error:
        print(f"❌ La llamada falló: {error}\n")
        print("Pistas:")
        print("  - Si usás 'cloud': ¿está tu ANTHROPIC_API_KEY en el archivo .env?")
        print("  - Si usás 'local': ¿está Ollama corriendo y descargaste el modelo?")
        sys.exit(1)

    print(f"✅ ¡Funcionó! El LLM extrajo {len(skills)} skills:")
    print("  ", skills)


if __name__ == "__main__":
    main()

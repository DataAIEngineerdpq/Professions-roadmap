"""
SUB-PASO 2b.2: EXTRACCIÓN HÍBRIDA (diccionario + LLM con caché)
==============================================================

Para cada oferta:
  1) Diccionario (rápido, gratis): detecta las skills CONOCIDAS.
  2) LLM (con caché): descubre skills, incluidas las que no anticipaste.
  3) Las skills del LLM que NO están en el diccionario se guardan como
     CANDIDATAS para que vos las revises (puerta de validación).

Salidas:
  - data/processed/enriched_<fecha>.json  → cada oferta con sus skills.
  - data/processed/candidates_<fecha>.json → skills nuevas por revisar.
"""

import json
import glob
import datetime
from pathlib import Path

import config
from text_utils import limpiar_html, recortar
# Reusamos el motor de diccionario que ya escribimos en el Paso 2a:
from extract_skills import cargar_diccionario, compilar_patrones, extraer_skills
from llm_extractor import extraer_skills_con_llm
import skill_cache

CARPETA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
CARPETA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"


def construir_conjunto_conocidas(diccionario: dict) -> set:
    """Arma un conjunto con TODO lo que el diccionario ya conoce (en minúsculas):
    nombres canónicos + todas sus variantes. Sirve para decidir qué es 'nuevo'."""
    conocidas = {canonica.lower() for canonica in diccionario}
    for variantes in diccionario.values():
        for v in variantes:
            conocidas.add(v.lower())
    return conocidas


def cargar_ultimo_crudo() -> list[dict]:
    archivos = sorted(glob.glob(str(CARPETA_RAW / "*.json")))
    archivos = [a for a in archivos if not Path(a).name.startswith("_")]
    if not archivos:
        raise FileNotFoundError("No hay archivos en data/raw/. Corré antes src/ingest.py")
    with open(archivos[-1], encoding="utf-8") as f:
        return json.load(f)


def procesar() -> None:
    diccionario = cargar_diccionario()
    patrones = compilar_patrones(diccionario)
    conocidas = construir_conjunto_conocidas(diccionario)

    cache = skill_cache.cargar_cache()
    ofertas = cargar_ultimo_crudo()

    print(f"Procesando {len(ofertas)} ofertas (híbrido: diccionario + LLM con caché)...\n")

    resultado = []
    candidatas: dict[str, int] = {}   # skill nueva -> en cuántas ofertas apareció
    llamadas_llm = 0
    aciertos_cache = 0

    for i, oferta in enumerate(ofertas, start=1):
        texto = limpiar_html(oferta.get("description_html", ""))

        # --- 1) Diccionario: skills conocidas (rápido) ---
        skills_dic = extraer_skills(texto, patrones)

        # --- 2) LLM con caché: descubrir ---
        # Al LLM le mandamos solo un fragmento (más rápido y más preciso).
        # El diccionario, en cambio, ya leyó el texto completo arriba.
        texto_para_llm = recortar(texto, max_caracteres=1500)
        # La llave del caché incluye el modelo: si cambiás de modelo, se re-procesa
        # (los resultados de un modelo no valen para otro).
        modelo_activo = config.MODELO_LOCAL if config.LLM_PROVIDER == "local" else config.MODELO_CLOUD
        clave_cache = f"{config.LLM_PROVIDER}:{modelo_activo}:{texto_para_llm}"
        huella = skill_cache.huella_texto(clave_cache)
        if huella in cache:
            skills_llm = cache[huella]
            aciertos_cache += 1
        else:
            print(f"  [{i}/{len(ofertas)}] llamando al LLM...")
            skills_llm = extraer_skills_con_llm(texto_para_llm)
            cache[huella] = skills_llm
            llamadas_llm += 1
            skill_cache.guardar_cache(cache)   # guardamos incremental, por si se corta

        # --- 3) Candidatas: lo que el LLM trajo y el diccionario no conoce ---
        for s in skills_llm:
            if s.lower() not in conocidas:
                candidatas[s] = candidatas.get(s, 0) + 1

        resultado.append({
            "source": oferta.get("source"),
            "title": oferta.get("title"),
            "company": oferta.get("company"),
            "url": oferta.get("url"),
            "skills": skills_dic,              # oficial: validado por diccionario
            "descubiertas_llm": skills_llm,    # crudo del LLM, para referencia
        })

    # Guardar resultados
    CARPETA_PROCESSED.mkdir(parents=True, exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    ruta_enriched = CARPETA_PROCESSED / f"enriched_{marca}.json"
    with open(ruta_enriched, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    # Candidatas ordenadas por frecuencia (las más pedidas primero)
    candidatas_ordenadas = dict(sorted(candidatas.items(), key=lambda x: -x[1]))
    ruta_candidatas = CARPETA_PROCESSED / f"candidates_{marca}.json"
    with open(ruta_candidatas, "w", encoding="utf-8") as f:
        json.dump(candidatas_ordenadas, f, ensure_ascii=False, indent=2)

    # Resumen
    print(f"\n  LLM: {llamadas_llm} llamadas nuevas, {aciertos_cache} reusadas del caché")
    print(f"\n🔎 {len(candidatas_ordenadas)} skills candidatas nuevas (para revisar):")
    for skill, cuenta in list(candidatas_ordenadas.items())[:15]:
        print(f"     {skill:35} {cuenta}")

    print(f"\n✅ Guardado:")
    print(f"   {ruta_enriched}")
    print(f"   {ruta_candidatas}")


if __name__ == "__main__":
    procesar()

"""
AUTO-CURACIÓN DE SKILLS (sin intervención humana)
=================================================

Reemplaza la aprobación manual por cuatro capas de filtrado automático,
ordenadas de más barata a más cara (no le pagamos al LLM por revisar basura
que una regla gratis puede descartar):

  1) Normalizar        → colapsa variantes (Scikit-learn = scikit-learn)
  2) Reglas            → descarta frases largas, oraciones, no-skills
  3) Frecuencia        → umbral ADAPTATIVO al tamaño del dataset (5%, mínimo 2)
  4) Validación LLM    → una sola llamada en lote, solo para las candidatas nuevas

Una skill validada entra al registro y NO se vuelve a validar: el costo se amortiza.
"""

import re
import json
from pathlib import Path

import config

RUTA_DICCIONARIO = Path(__file__).resolve().parent / "skills.json"

# --- Capa 2: reglas estructurales -------------------------------------------

# Palabras que delatan una frase de oferta, no una skill técnica.
PALABRAS_NO_SKILL = {
    "working", "experience", "team", "culture", "opportunity", "benefits",
    "salary", "remote", "hybrid", "office", "compliance", "governance",
    "stewardship", "scalability", "automation", "integrity", "performance",
    "platforms", "services", "products", "features", "tools", "systems",
    "engineer", "engineering", "developer", "development", "management",
}

MAX_PALABRAS = 4          # una skill real rara vez tiene más de 4 palabras
MAX_CARACTERES = 30       # ni más de ~30 caracteres ("Bronze-, Silver- und Gold-Layer-Architekturen" es una frase, no una skill)
MIN_CARACTERES = 2


def normalizar_nombre(skill: str) -> str:
    """Devuelve una forma canónica para comparar: minúsculas, sin espacios extra,
    sin paréntesis explicativos. 'DBT (Data Build Tool)' -> 'dbt'."""
    s = skill.strip()
    s = re.sub(r"\s*\([^)]*\)", "", s)     # quita "(...)"
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def pasa_reglas(skill: str) -> bool:
    """Capa 2: descarta lo que estructuralmente no puede ser una skill."""
    s = skill.strip()
    if len(s) < MIN_CARACTERES:
        return False
    if len(s) > MAX_CARACTERES:
        return False
    palabras = s.split()
    if len(palabras) > MAX_PALABRAS:
        return False
    # Si TODAS sus palabras son genéricas, es una frase de oferta, no una skill.
    if all(p.lower().strip(",.") in PALABRAS_NO_SKILL for p in palabras):
        return False
    # Descarta entradas que terminan en punto (son oraciones).
    if s.endswith("."):
        return False
    return True


def umbral_adaptativo(total_ofertas: int, porcentaje: float = 0.05, minimo: int = 2) -> int:
    """Capa 3: cuántas ofertas debe mencionar una skill para considerarse señal.

    Adaptativo: con 19 ofertas el umbral es 2; con 2000 ofertas sube a 100.
    Así el sistema se auto-calibra al crecer, sin tocar código.
    """
    return max(minimo, int(total_ofertas * porcentaje))


def validar_con_llm(candidatas: list[str]) -> set[str]:
    """Capa 4: una sola llamada en lote. Devuelve el subconjunto que el LLM
    considera tecnologías/skills técnicas reales."""
    if not candidatas:
        return set()

    instruccion = (
        "De la siguiente lista, devolvé SOLO las que son tecnologías, herramientas, "
        "lenguajes, frameworks o skills técnicas concretas. Descartá nombres de "
        "empresa, sectores, modalidades de trabajo y frases genéricas. "
        'Respondé SOLO con JSON: {"validas": ["Skill1", "Skill2"]}'
    )
    entrada = "\n".join(f"- {c}" for c in candidatas)

    try:
        if config.LLM_PROVIDER == "cloud":
            from anthropic import Anthropic
            import os
            cliente = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            r = cliente.messages.create(
                model=config.MODELO_CLOUD, max_tokens=2000,
                system=instruccion, messages=[{"role": "user", "content": entrada}],
            )
            contenido = r.content[0].text
        else:
            import requests
            r = requests.post(config.OLLAMA_URL, json={
                "model": config.MODELO_LOCAL,
                "messages": [
                    {"role": "system", "content": instruccion},
                    {"role": "user", "content": entrada},
                ],
                "stream": False, "format": "json",
                "options": {"num_predict": 2048, "num_ctx": 8192},
            }, timeout=config.OLLAMA_TIMEOUT)
            r.raise_for_status()
            contenido = r.json()["message"]["content"]

        m = re.search(r"\{.*\}", contenido, re.DOTALL)
        if not m:
            # Si el LLM falla, NO bloqueamos el pipeline: dejamos pasar lo que
            # ya superó frecuencia y reglas (degradación elegante).
            return set(candidatas)
        return set(json.loads(m.group(0)).get("validas", candidatas))
    except Exception as error:
        print(f"    (validación LLM omitida: {error})")
        return set(candidatas)


def curar(conteo_candidatas: dict, total_ofertas: int, diccionario: dict,
          usar_llm: bool = True) -> tuple[list[str], dict]:
    """Aplica las 4 capas y devuelve (skills aprobadas, estadísticas)."""
    stats = {"crudas": len(conteo_candidatas)}

    # Conocidas ya en el diccionario (normalizadas para comparar)
    conocidas = {normalizar_nombre(c) for c in diccionario}
    for variantes in diccionario.values():
        conocidas.update(normalizar_nombre(v) for v in variantes)

    # --- Capa 1: normalizar y colapsar duplicados ---
    por_forma: dict[str, tuple[str, int]] = {}
    for skill, cuenta in conteo_candidatas.items():
        forma = normalizar_nombre(skill)
        if forma in conocidas:
            continue
        if forma in por_forma:
            # Mismo concepto escrito distinto: sumamos frecuencias.
            nombre_previo, cuenta_previa = por_forma[forma]
            por_forma[forma] = (nombre_previo, cuenta_previa + cuenta)
        else:
            por_forma[forma] = (skill, cuenta)
    stats["tras_normalizar"] = len(por_forma)

    # --- Capa 2: reglas estructurales ---
    tras_reglas = {f: v for f, v in por_forma.items() if pasa_reglas(v[0])}
    stats["tras_reglas"] = len(tras_reglas)

    # --- Capa 3: frecuencia adaptativa ---
    umbral = umbral_adaptativo(total_ofertas)
    stats["umbral"] = umbral
    tras_frecuencia = [v[0] for v in tras_reglas.values() if v[1] >= umbral]
    stats["tras_frecuencia"] = len(tras_frecuencia)

    # --- Capa 4: validación LLM (solo lo que llegó hasta acá) ---
    if usar_llm and tras_frecuencia:
        validas = validar_con_llm(tras_frecuencia)
        aprobadas = [s for s in tras_frecuencia if s in validas]
    else:
        aprobadas = tras_frecuencia
    stats["aprobadas"] = len(aprobadas)

    return aprobadas, stats


def agregar_al_diccionario(aprobadas: list[str]) -> int:
    """Suma las skills aprobadas al diccionario. Devuelve cuántas se agregaron."""
    with open(RUTA_DICCIONARIO, encoding="utf-8") as f:
        diccionario = json.load(f)

    conocidas = {normalizar_nombre(c) for c in diccionario}
    for variantes in diccionario.values():
        conocidas.update(normalizar_nombre(v) for v in variantes)

    agregadas = 0
    for skill in aprobadas:
        if normalizar_nombre(skill) not in conocidas:
            diccionario[skill] = [skill.lower()]
            conocidas.add(normalizar_nombre(skill))
            agregadas += 1

    with open(RUTA_DICCIONARIO, "w", encoding="utf-8") as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=2)
    return agregadas

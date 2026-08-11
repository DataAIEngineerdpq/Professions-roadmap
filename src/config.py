"""
CONFIGURACIÓN DEL PIPELINE
==========================
Acá vive el "interruptor" (toggle) para elegir qué motor de LLM usar.
Cambiás UN valor y todo el pipeline usa el proveedor que elijas, sin tocar
ninguna otra línea de código. Más adelante, este mismo interruptor será un
botón real en la interfaz de tu app.
"""

# ============================================================
#  EL TOGGLE: elegí "cloud" o "local"
# ============================================================
#   "cloud"  → API de Anthropic. Rápido y de alta calidad. Requiere API key
#              y tiene un costo por uso (bajísimo para este proyecto).
#   "local"  → Ollama corriendo en tu compu. Gratis y privado, pero requiere
#              instalar Ollama y descargar un modelo.
LLM_PROVIDER = "local"

# ============================================================
#  Qué modelo usar en cada caso (podés cambiarlos)
# ============================================================
# Haiku 4.5 es el modelo pequeño, rápido y económico de Anthropic, ideal para
# extraer datos. Pensado exactamente para tareas como esta.
MODELO_CLOUD = "claude-haiku-4-5"

# El modelo que tengas descargado en Ollama (ej: "llama3.1", "qwen2.5", "mistral").
MODELO_LOCAL = "llama3.2"

# Dirección donde corre Ollama en tu compu (valor por defecto de Ollama).
OLLAMA_URL = "http://localhost:11434/api/chat"

# Cuántos segundos esperar la respuesta de Ollama antes de rendirse.
# Los modelos locales en CPU pueden ser lentos, sobre todo la primera vez.
# Si te da timeout, subí este número.
OLLAMA_TIMEOUT = 300

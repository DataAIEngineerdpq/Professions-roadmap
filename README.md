# Roadmap Interactivo de Profesiones

Proyecto de aprendizaje de **Data Engineering**: un pipeline que recoge ofertas de
empleo reales, extrae las skills que piden las empresas para un rol, y las muestra
como un **árbol interactivo** (roadmap) que se ve en compu y celular.

## Fuentes de datos (legales, gratis, sin login)

- **Arbeitnow** — `https://www.arbeitnow.com/api/job-board-api` (la que usamos ahora)
- Más adelante sumaremos: Jobicy, Himalayas, RemoteOK.

> Nota: no usamos LinkedIn porque su scraping viola sus términos, te banea la IP
> enseguida y es una bandera roja en un portafolio. Estas APIs dan datos limpios
> y te dejan concentrarte en lo que importa: el pipeline.

## Plan por pasos (aprender haciendo)

1. **Ingesta** ← estás aquí. Traer ofertas por rol y guardarlas crudas. (`src/ingest.py`)
2. **Procesamiento**: limpiar el HTML de las descripciones y extraer skills.
3. **Almacenamiento**: guardar en PostgreSQL.
4. **API**: exponer los datos con FastAPI.
5. **Frontend**: el árbol interactivo (React).
6. **Docker**: empaquetar todo con docker-compose.
7. **Orquestación + observabilidad**: Airflow, Prometheus + Grafana.

## Cómo correr el Paso 1

Necesitás Python 3.10 o superior instalado.

```bash
# 1. Entrá a la carpeta del proyecto
cd roadmap-project

# 2. (Recomendado) creá un entorno virtual aislado
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate

# 3. Instalá las dependencias
pip install -r requirements.txt

# 4. Ejecutá la ingesta
python src/ingest.py
```

Vas a ver algo como:

```
Buscando ofertas de: 'data engineer'
Descargando página 1...
  4 coincidencias de 100 ofertas
...
✅ Listo: 11 ofertas guardadas en:
   .../data/raw/data_engineer_2026-07-30_22-16-28.json
```

Para buscar otro rol, cambiá la variable `ROL_BUSCADO` al inicio de `src/ingest.py`.

## Estructura

```
roadmap-project/
├── README.md
├── requirements.txt
├── data/
│   └── raw/            # ofertas crudas descargadas (capa "bronze")
└── src/
    └── ingest.py       # Paso 1: ingesta
```

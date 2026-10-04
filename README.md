# ⚡ DevPulse — Radar Tecnológico Inteligente & Autónomo

**DevPulse** es una plataforma automatizada y de alta velocidad diseñada para agregar, clasificar, sintetizar y presentar las últimas noticias del mundo informático y tecnológico con lectura rápida en 15 segundos y enlaces directos a las fuentes originales.

---

## 🚀 Características Principales

1. **Pipeline de Ingesta Asíncrono (`collector.py`):**
   - **Hacker News (Algolia API):** Historias filtradas con umbral de puntos y etiquetas técnicas.
   - **GitHub Releases:** Monitoreo concurrente de lanzamientos oficiales de repositorios clave (`react`, `next.js`, `rust`, `python`, `go`, `pytorch`, `bun`, `deno`, etc.).
   - **Curated Tech RSS/Atom Feeds:** Blogs oficiales de ingeniería (V8 Engine, Changelog, Simon Willison, GitHub Engineering, Mozilla Hacks, etc.).
2. **Motor de Decisión Laya (`classifier.py`):**
   - Integración nativa con `from laya import Router` (motor System 1 no-autoregresivo de sub-40ms).
   - **Relevancia (`noul`):** Decisión binaria de idoneidad técnica.
   - **Tópicos (`choice`):** Clasificación en 5 categorías estándar:
     - `Modelos IA & Machine Learning`
     - `Nuevas Herramientas & Developer Tools`
     - `Frameworks & Librerías`
     - `Funciones de Lenguajes (JS, Python, Rust, etc.)`
     - `DevOps, Cloud & Seguridad`
   - **Calibración de Impacto (`score` 1 - 100):** Escala ponderada según trascendencia de la noticia.
3. **Módulo de Resumen Breve (`summarizer.py`):**
   - Generación instantánea de 2 a 3 viñetas (*Key Highlights*) por artículo.
   - Tiempo de lectura estimado (~15 segundos) preservando el enlace original.
4. **Agente Autónomo en Background (`scheduler.py`):**
   - Funciona sin intervención humana: rastrea y procesa noticias cada 15 minutos de forma automática.
5. **Base de Datos SQLite de Alto Rendimiento (`database.py`):**
   - Modo WAL (`Write-Ahead Logging`), índices optimizados y deduplicación por `source_url`.
6. **Dashboard Moderno (Tailwind CSS + Alpine.js):**
   - Modo oscuro/claro persistente.
   - Búsqueda en tiempo real con debounce.
   - Filtros dinámicos por tópico y por umbral de impacto.
   - Badges visuales de impacto y viñetas de lectura rápida expandibles.

---

## 📁 Estructura del Proyecto

```
DevPulse/
├── requirements.txt         # Dependencias Python
├── README.md                # Documentación
├── data/
│   └── devpulse.sqlite3     # Base de datos SQLite (creada automáticamente)
├── devpulse/
│   ├── __init__.py
│   ├── config.py            # Configuración, feeds, repos y umbrales
│   ├── database.py          # Capa de almacenamiento SQLite WAL e índices
│   ├── classifier.py        # Motor de decisión Laya (noul, choice, score)
│   ├── summarizer.py        # Extractor de Key Highlights (lectura 15s)
│   ├── collector.py         # Ingesta asíncrona concurrente (HN, GitHub, RSS)
│   ├── scheduler.py         # Planificador autónomo en background
│   └── main.py              # Servidor API FastAPI y servicio de frontend
├── frontend/
│   ├── index.html           # Interfaz Dashboard/Reader
│   └── static/
│       ├── css/
│       │   └── style.css    # Estilos y microinteracciones
│       └── js/
│           └── app.js       # Lógica reactiva con Alpine.js
└── tests/
    ├── __init__.py
    └── test_pipeline.py     # Suite de pruebas unitarias e integración
```

---

## 🛠️ Instalación y Puesta en Marcha Local

### Prerrequisitos
- Python 3.10 o superior (recomendado Python 3.11 - 3.13)

### 1. Clonar el Repositorio y Crear el Entorno Virtual
```bash
git clone https://github.com/CarlosGaubert/DevPulse.git
cd DevPulse
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la Suite de Pruebas Automatizadas
```bash
pytest -v tests/test_pipeline.py
```

### 4. Iniciar DevPulse
```bash
python run.py
```
*(O directamente con uvicorn: `uvicorn devpulse.main:app --host 0.0.0.0 --port 8080 --reload`)*

Abre tu navegador en:
👉 **http://localhost:8080**

> [!NOTE]
> Al iniciar el servidor, el **Agente Autónomo** ejecuta inmediatamente la sincronización en segundo plano, consultando Hacker News, GitHub Releases y los feeds RSS configurados.

---

## 📡 Endpoints de la API REST

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Carga el Dashboard / Lector Editorial interactivo. |
| `GET` | `/api/news` | Listado paginado con filtros (`topic`, `sort_by`, `search`, `min_score`, `page`, `page_size`, `lang`). |
| `GET` | `/api/topics` | Lista de tópicos disponibles con el conteo de artículos en cada uno. |
| `GET` | `/api/stats` | Estadísticas del sistema (noticias verificadas, promedio de impacto, fuentes, seguridad). |
| `GET` | `/api/languages` | Idiomas soportados para la interfaz y traducción (`es`, `en`, `pt`, `fr`, `de`). |
| `POST` | `/api/translate` | Traducción con Escudo de Terminología Técnica y caché de alta velocidad. |
| `GET` | `/api/feeds` | Listado de fuentes del sistema y feeds RSS/Atom personalizados. |
| `POST` | `/api/feeds` | Valida en vivo y agrega un nuevo feed RSS/Atom personalizado. |
| `DELETE` | `/api/feeds/{id}` | Elimina un feed personalizado. |
| `POST` | `/api/feeds/{id}/toggle` | Pausa o reactiva una fuente personalizada. |
| `POST` | `/api/refresh` | Dispara una recolección manual asíncrona en segundo plano. |
| `GET` | `/api/scheduler/status` | Estado en tiempo real del radar autónomo y próxima ejecución. |

---

## 🛡️ Seguridad & Escudo Antimalware Web

DevPulse analiza preventivamente cada enlace e historia antes de su publicación:
- **Inspección de Dominios:** Detección de dominios efímeros y TLDs de riesgo (`.zip`, `.mov`, etc.).
- **Bloqueo de Descargas Peligrosas:** Bloqueo automático de ejecutables camuflados (`.exe`, `.scr`, `.bat`).
- **Puntuación de Seguridad:** Cada noticia incluye su estado de verificación (`VERIFICADO_SEGURO` / `BLOQUEADO`) y puntuación de auditoría.

---

## 🌐 Escudo de Terminología Técnica (*Technical Terminology Shield*)

Para preservar la precisión técnica en las traducciones automáticas:
- Enmascara nombres de lenguajes (`Rust`, `Go`, `Python`, `Swift`), frameworks (`React`, `Vue`, `Spring`) y versiones SemVer (`1.85.0`) con tokens neutros antes de traducir.
- Evita traducciones ambiguas (ej. *Rust* nunca se traduce como *óxido*, *Go* nunca como *ir*, *Release* como *Versión/Lanzamiento* y no *liberación*).


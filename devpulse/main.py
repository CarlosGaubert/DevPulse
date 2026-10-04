"""
DevPulse - FastAPI Application Server
Provides REST endpoints for news browsing, filtering, metrics, and autonomous ingestion.
"""
import os
import math
import logging
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Query, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from devpulse.config import TOPICS, BASE_DIR, RSS_FEEDS, GITHUB_REPOS
from devpulse.database import (
    init_db, get_articles, get_topics_with_counts, get_stats,
    get_custom_feeds, add_custom_feed, delete_custom_feed, toggle_custom_feed
)
from devpulse.scheduler import scheduler
from devpulse.translator import (
    init_translation_cache, translate_text, translate_article_payload,
    SUPPORTED_LANGUAGES, normalize_lang_code
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("devpulse.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown lifecycle events."""
    logger.info("DevPulse backend starting up...")
    init_db()
    init_translation_cache()
    # Start autonomous background collector loop
    scheduler.start()
    yield
    logger.info("DevPulse backend shutting down...")
    scheduler.stop()

app = FastAPI(
    title="DevPulse API",
    description="Automated Tech News Aggregation & Classification with Laya Decision Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Frontend files
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

from pydantic import BaseModel, HttpUrl

class TranslationRequest(BaseModel):
    text: str
    target: str = "es"

class CustomFeedCreate(BaseModel):
    name: str
    url: str
    topic: Optional[str] = "Herramientas de Desarrollo & CLI"

class FeedToggleRequest(BaseModel):
    is_active: bool

@app.get("/api/languages")
async def get_languages():
    """Retorna la lista de idiomas soportados con banderas y nombres."""
    return {"languages": [{"code": k, **v} for k, v in SUPPORTED_LANGUAGES.items()]}

@app.get("/api/news")
async def list_news(
    topic: Optional[str] = Query(None, description="Filtrar por tópico"),
    sort_by: str = Query("importance", pattern="^(importance|date)$", description="Criterio de ordenación"),
    search: Optional[str] = Query(None, description="Búsqueda por texto en título o contenido"),
    min_score: Optional[int] = Query(None, ge=1, le=100, description="Puntuación mínima de impacto"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(15, ge=1, le=100, description="Artículos por página"),
    lang: str = Query("es", pattern="^(es|en|pt|fr|de)$", description="Idioma de entrega: 'es', 'en', 'pt', 'fr', 'de'")
):
    """Retorna listado paginado de noticias con traducción automática integrada para múltiples idiomas."""
    articles, total = get_articles(
        topic=topic,
        sort_by=sort_by,
        search=search,
        min_score=min_score,
        page=page,
        page_size=page_size
    )

    # Automatic translation for requested language
    target_code = normalize_lang_code(lang)
    if target_code != "en" or any(a.get("explanatory_dialogue") for a in articles):
        articles = [translate_article_payload(a, target_lang=target_code) for a in articles]

    total_pages = max(1, math.ceil(total / page_size))
    return {
        "items": articles,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "lang": target_code
    }

@app.post("/api/translate")
async def handle_translate(req: TranslationRequest):
    """Traduce cualquier texto técnico a cualquiera de los idiomas soportados con caché de alto rendimiento."""
    translated = translate_text(req.text, target_lang=req.target)
    return {"original": req.text, "translated": translated, "target": req.target}

@app.get("/api/topics")
async def list_topics():
    """Retorna los tópicos disponibles con el conteo actual de noticias."""
    topics = get_topics_with_counts()
    return {"topics": topics}

@app.get("/api/stats")
async def get_dashboard_stats():
    """Retorna métricas generales del sistema."""
    stats = get_stats()
    scheduler_status = scheduler.status
    return {
        **stats,
        "scheduler": scheduler_status
    }

@app.post("/api/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks):
    """
    Dispara una recolección manual inmediata sin bloquear la petición.
    """
    if scheduler.status["is_syncing"]:
        return JSONResponse(
            status_code=409,
            content={"status": "in_progress", "message": "Ya existe una sincronización en curso."}
        )

    background_tasks.add_task(scheduler.run_once)
    return {
        "status": "triggered",
        "message": "Sincronización iniciada en segundo plano."
    }

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Retorna el estado del motor autónomo de sincronización."""
    return scheduler.status

@app.get("/api/feeds")
async def list_all_feeds():
    """Retorna las fuentes del sistema y las fuentes RSS personalizadas agregadas por el usuario."""
    custom = get_custom_feeds()
    return {
        "system_feeds": [
            {"name": f["name"], "url": f["url"], "type": "RSS", "topic": f.get("default_topic", "General")}
            for f in RSS_FEEDS
        ],
        "github_repos": GITHUB_REPOS,
        "custom_feeds": custom,
        "total_custom": len(custom)
    }

@app.post("/api/feeds")
async def create_custom_feed(feed: CustomFeedCreate, background_tasks: BackgroundTasks):
    """
    Valida y registra un nuevo feed RSS/Atom personalizado.
    Inicia inmediatamente la recolección en segundo plano.
    """
    import httpx
    import feedparser

    url_str = feed.url.strip()
    if not (url_str.startswith("http://") or url_str.startswith("https://")):
        raise HTTPException(status_code=400, detail="La URL del feed debe comenzar con http:// o https://")

    # Validar feed en vivo
    try:
        async with httpx.AsyncClient(headers={"User-Agent": "DevPulse-TechRadar/2.0"}, follow_redirects=True, timeout=8.0) as client:
            resp = await client.get(url_str)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"No se pudo acceder al feed (Código HTTP {resp.status_code})")
            
            parsed = feedparser.parse(resp.text)
            if not parsed.entries and not parsed.feed.get("title"):
                raise HTTPException(status_code=400, detail="La URL proporcionada no parece ser un feed RSS o Atom válido.")
            
            detected_title = feed.name.strip() or parsed.feed.get("title", "Feed Personalizado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error validando feed RSS: {str(e)}")

    try:
        created = add_custom_feed(
            name=detected_title,
            url=url_str,
            topic=feed.topic or "Herramientas de Desarrollo & CLI"
        )
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Error al registrar feed (posible duplicado): {str(e)}")

    # Iniciar recolección en background
    background_tasks.add_task(scheduler.run_once)

    return {
        "status": "created",
        "feed": created,
        "message": f"Feed '{detected_title}' agregado con éxito y encolado para recolección."
    }

@app.delete("/api/feeds/{feed_id}")
async def remove_custom_feed(feed_id: int):
    """Elimina una fuente RSS personalizada."""
    success = delete_custom_feed(feed_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feed personalizado no encontrado.")
    return {"status": "deleted", "id": feed_id}

@app.post("/api/feeds/{feed_id}/toggle")
async def toggle_feed_status(feed_id: int, req: FeedToggleRequest):
    """Habilita o deshabilita temporalmente una fuente RSS personalizada."""
    success = toggle_custom_feed(feed_id, req.is_active)
    if not success:
        raise HTTPException(status_code=404, detail="Feed personalizado no encontrado.")
    return {"status": "updated", "id": feed_id, "is_active": req.is_active}


@app.api_route("/", methods=["GET", "HEAD"])
async def serve_index():
    """Sirve la interfaz de usuario web de DevPulse."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(
        {"message": "DevPulse API en línea. Frontend no encontrado en /frontend/index.html"},
        status_code=200
    )

"""
DevPulse - Unit and Integration Tests
Tests database operations, summarizer, classifier, security guard, and API endpoints.
"""
import pytest
from starlette.testclient import TestClient

from devpulse.database import (
    init_db, save_article, article_exists, get_articles, get_topics_with_counts, get_stats
)
from devpulse.summarizer import extract_key_highlights, clean_html_and_markdown, generate_explanatory_dialogue
from devpulse.security_guard import security_guard
from devpulse.classifier import get_classifier
from devpulse.main import app

def setup_module():
    init_db()

def test_security_guard_protection():
    # 1. Safe tech URL
    safe_res = security_guard.audit_article(
        title="PyTorch 2.6 Released with Improved CUDA Graph Support",
        source_url="https://pytorch.org/blog/pytorch-2-6/",
        content="Official release notes from PyTorch engineering."
    )
    assert safe_res["is_safe"] is True
    assert safe_res["status"] == "VERIFIED_SAFE"
    assert safe_res["safety_score"] >= 90

    # 2. Malicious executable download disguised as tech update
    malware_res = security_guard.audit_article(
        title="Download Node.js V22 Fast Installer",
        source_url="http://node-update.zip/installer.exe",
        content="Click to run executable."
    )
    assert malware_res["is_safe"] is False
    assert malware_res["status"] == "BLOCKED"

    # 3. Phishing scam pattern
    phishing_res = security_guard.audit_article(
        title="Claim your GitHub Developer Airdrop Tokens",
        source_url="https://github-reward-tokens.com/claim-airdrop",
        content="Connect your wallet to claim tokens."
    )
    assert phishing_res["is_safe"] is False

def test_explanatory_dialogue_and_highlights():
    title = "DeepSeek V3 Model Weights and Architecture Released"
    content = "DeepSeek AI releases their frontier mixture-of-experts model with 671B parameters and 37B active per token."
    
    dialogue = generate_explanatory_dialogue(title, content, "Modelos IA & Machine Learning")
    assert "¿Qué representa este avance?" in dialogue or "inteligencia artificial" in dialogue
    assert len(dialogue) > 60

    bullets, read_time = extract_key_highlights(title, content)
    assert len(bullets) >= 2
    assert 10 <= read_time <= 30

def test_database_crud():
    test_url = "https://github.com/rust-lang/rust/releases/tag/1.85.0-test"
    
    saved = save_article(
        title="Rust 1.85.0 Testing Release",
        source_name="GitHub (rust-lang/rust)",
        source_url=test_url,
        published_at="2026-10-03T18:00:00Z",
        topic="Funciones de Lenguajes (JS, Python, Rust, etc.)",
        importance_score=75,
        summary_bullets=["Rust 1.85 introducing 2024 edition stabilization"],
        read_time_seconds=15,
        raw_content="Official rust release notes.",
        explanatory_dialogue="Actualización clave en el compilador de Rust para garantizar mayor seguridad de memoria.",
        safety_status="VERIFIED_SAFE",
        safety_score=98,
        safety_details="Enlace HTTPS verificado sin amenazas."
    )
    assert saved is True or article_exists(test_url) is True

    # Duplicate insert should be safely ignored
    duplicate_saved = save_article(
        title="Rust 1.85.0 Duplicate",
        source_name="GitHub",
        source_url=test_url,
        published_at="2026-10-03T18:00:00Z",
        topic="Funciones de Lenguajes (JS, Python, Rust, etc.)",
        importance_score=75,
        summary_bullets=["Duplicate"],
    )
    assert duplicate_saved is False

    # Query articles
    items, total = get_articles(topic="Funciones de Lenguajes (JS, Python, Rust, etc.)", page_size=10, page=1)
    assert total >= 1
    assert any(a["source_url"] == test_url for a in items)
    matched = next(a for a in items if a["source_url"] == test_url)
    assert matched["explanatory_dialogue"] != ""
    assert matched["safety_status"] == "VERIFIED_SAFE"

def test_classifier_engine():
    classifier = get_classifier()
    res = classifier.classify(
        "OpenAI releases Whisper V4 audio speech recognition model",
        "State of the art speech to text with reduced latency."
    )
    assert "is_relevant" in res
    assert res["is_relevant"] is True
    assert "topic" in res
    assert 1 <= res["importance_score"] <= 100

def test_api_endpoints():
    client = TestClient(app)
    
    # GET /api/news
    resp = client.get("/api/news")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0
    first_item = data["items"][0]
    assert "explanatory_dialogue" in first_item
    assert "safety_status" in first_item

    # GET /api/topics
    resp_topics = client.get("/api/topics")
    assert resp_topics.status_code == 200
    assert "topics" in resp_topics.json()

    # GET /api/stats
    resp_stats = client.get("/api/stats")
    assert resp_stats.status_code == 200
    assert "total_articles" in resp_stats.json()
    assert "verified_safe_count" in resp_stats.json()

    # POST /api/translate
    resp_trans = client.post("/api/translate", json={"text": "Software Engineering Breakthroughs", "target": "es"})
    assert resp_trans.status_code == 200
    assert "translated" in resp_trans.json()
    assert len(resp_trans.json()["translated"]) > 0

def test_translation_caching():
    from devpulse.translator import translate_text, set_cached_translation, get_cached_translation
    
    text = "Breakthrough performance in neural network inference"
    set_cached_translation(text, "es", "Rendimiento revolucionario en la inferencia de redes neuronales")
    cached = get_cached_translation(text, "es")
    assert cached == "Rendimiento revolucionario en la inferencia de redes neuronales"
    
    res = translate_text(text, target_lang="es")
    assert res == "Rendimiento revolucionario en la inferencia de redes neuronales"

def test_custom_feeds_crud_and_api():
    from devpulse.database import add_custom_feed, get_custom_feeds, delete_custom_feed, toggle_custom_feed
    
    # 1. Add custom feed
    test_feed_url = "https://news.ycombinator.com/rss-test-custom"
    feed = add_custom_feed("HN Test RSS", test_feed_url, "Herramientas de Desarrollo & CLI")
    assert feed["id"] is not None
    assert feed["name"] == "HN Test RSS"
    
    # 2. Query feeds
    feeds = get_custom_feeds()
    assert any(f["id"] == feed["id"] for f in feeds)

    # 3. Toggle feed
    toggle_custom_feed(feed["id"], False)
    active_feeds = get_custom_feeds(only_active=True)
    assert not any(f["id"] == feed["id"] for f in active_feeds)

    # 4. API list feeds
    client = TestClient(app)
    resp = client.get("/api/feeds")
    assert resp.status_code == 200
    data = resp.json()
    assert "system_feeds" in data
    assert "custom_feeds" in data

    # 5. API languages
    resp_lang = client.get("/api/languages")
    assert resp_lang.status_code == 200
    languages = resp_lang.json()["languages"]
    assert len(languages) >= 5
    codes = [l["code"] for l in languages]
    assert "es" in codes and "en" in codes and "pt" in codes

    # 6. Delete feed
    deleted = delete_custom_feed(feed["id"])
    assert deleted is True

def test_technical_terminology_shield():
    from devpulse.translator import translate_text

    # 1. Rust must NEVER become óxido or oxido
    rust_text = "Rust 1.85.0 Testing Release with compiler stability"
    translated = translate_text(rust_text, target_lang="es")
    assert "Rust" in translated
    assert "óxido" not in translated.lower()
    assert "oxido" not in translated.lower()
    assert "liberación de prueba" not in translated.lower()

    # 2. Go programming language must not become 'Ir'
    go_text = "Go 1.24 memory allocator improvements"
    go_trans = translate_text(go_text, target_lang="es")
    assert "Go" in go_trans

@pytest.mark.anyio
async def test_translate_articles_batch_async():
    from devpulse.translator import translate_articles_batch_async

    sample_articles = [
        {
            "id": 101,
            "title": "Rust 1.85.0 Testing Release",
            "explanatory_dialogue": "Actualización clave en el compilador de Rust.",
            "summary_bullets": ["Rust 1.85 features async closures"],
            "topic": "Funciones de Lenguajes (JS, Python, Rust, etc.)"
        },
        {
            "id": 102,
            "title": "React 19 Server Components Architecture",
            "explanatory_dialogue": "Nueva arquitectura de componentes en React 19.",
            "summary_bullets": ["React Server Actions improved"],
            "topic": "Frameworks Web (React, Vue, etc.)"
        }
    ]

    # Test Spanish batch translation
    translated = await translate_articles_batch_async(sample_articles, target_lang="es")
    assert len(translated) == 2
    assert translated[0]["lang"] == "es"
    assert "Rust" in translated[0]["title"]
    assert "React" in translated[1]["title"]




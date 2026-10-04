"""
DevPulse - Configuration settings with fresh tech focus and recency windows
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = os.getenv("DEVPULSE_DB_PATH", str(DATA_DIR / "devpulse.sqlite3"))

# Autonomous Sync settings
SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "15"))
AUTO_SYNC_ON_STARTUP = os.getenv("AUTO_SYNC_ON_STARTUP", "true").lower() in ("true", "1", "yes")

# Low-Memory Cloud Mode: Auto-detects Render free tier (512MB RAM) or explicit flag
LOW_MEMORY_MODE = (
    os.getenv("LOW_MEMORY_MODE", "").lower() in ("true", "1", "yes")
    or os.getenv("RENDER") == "true"
    or os.getenv("IS_RENDER") == "true"
)

# Recency Filter: Discard stale items older than MAX_AGE_DAYS
MAX_AGE_DAYS = int(os.getenv("MAX_AGE_DAYS", "21"))

# Ingestion settings
HN_MIN_POINTS = int(os.getenv("HN_MIN_POINTS", "10"))
HN_LIMIT = int(os.getenv("HN_LIMIT", "30"))

# Target GitHub repositories to track latest releases (Fast-moving modern tech)
GITHUB_REPOS = [
    "astral-sh/uv",
    "oven-sh/bun",
    "denoland/deno",
    "vercel/next.js",
    "tailwindlabs/tailwindcss",
    "facebook/react",
    "vuejs/core",
    "sveltejs/svelte",
    "microsoft/TypeScript",
    "fastapi/fastapi",
    "pytorch/pytorch",
    "rust-lang/rust",
    "python/cpython",
    "golang/go",
    "huggingface/transformers",
    "ollama/ollama",
]

# Curated High-Quality Tech RSS & Atom Feeds
RSS_FEEDS = [
    {
        "name": "Simon Willison Weblog (AI & LLMs)",
        "url": "https://simonwillison.net/atom/everything/",
        "default_topic": "Modelos IA & Machine Learning"
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "default_topic": "Modelos IA & Machine Learning"
    },
    {
        "name": "Vercel News & Releases",
        "url": "https://vercel.com/atom",
        "default_topic": "Frameworks & Librerías"
    },
    {
        "name": "Changelog News",
        "url": "https://changelog.com/feed",
        "default_topic": "Nuevas Herramientas & Developer Tools"
    },
    {
        "name": "V8 JavaScript Engine",
        "url": "https://v8.dev/blog.atom",
        "default_topic": "Funciones de Lenguajes (JS, Python, Rust, etc.)"
    },
    {
        "name": "GitHub Engineering Blog",
        "url": "https://github.blog/engineering/feed/",
        "default_topic": "DevOps, Cloud & Seguridad"
    },
    {
        "name": "Rust Blog",
        "url": "https://blog.rust-lang.org/feed.xml",
        "default_topic": "Funciones de Lenguajes (JS, Python, Rust, etc.)"
    },
    {
        "name": "Python Insider",
        "url": "https://blog.python.org/feeds/posts/default",
        "default_topic": "Funciones de Lenguajes (JS, Python, Rust, etc.)"
    },
    {
        "name": "Cloudflare Blog",
        "url": "https://blog.cloudflare.com/rss/",
        "default_topic": "DevOps, Cloud & Seguridad"
    }
]

# Allowed Topics
TOPICS = [
    "Modelos IA & Machine Learning",
    "Nuevas Herramientas & Developer Tools",
    "Frameworks & Librerías",
    "Funciones de Lenguajes (JS, Python, Rust, etc.)",
    "DevOps, Cloud & Seguridad"
]

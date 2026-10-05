"""
DevPulse - Universal Translation Engine
Provides caching, multi-provider translation, and bilingual support for news and UI.
"""
import sqlite3
import logging
import re
import urllib.parse
import asyncio
from typing import Optional, Dict, Any, List, Tuple
import httpx
from devpulse.config import DB_PATH

logger = logging.getLogger("devpulse.translator")

# In-memory LRU cache
_MEM_CACHE: Dict[str, str] = {}

# ==============================================================================
# 🛡️ TECHNICAL TERMINOLOGY SHIELD (Glosario de Protección Tecnológica)
# Términos que NUNCA deben traducirse literalmente (ej. Rust != óxido, Go != ir)
# ==============================================================================
PROTECTED_TECH_TERMS = [
    # Lenguajes de Programación
    "Rust", "Go", "Golang", "Python", "JavaScript", "TypeScript", "Kotlin", "Swift",
    "Ruby", "PHP", "C++", "C#", "Scala", "Elixir", "Erlang", "Haskell", "Lua", "Julia",
    "Zig", "Dart", "Clojure", "WebAssembly", "Wasm", "Solidity", "Assembly", "Bash", "Shell",
    # Frameworks & Librerías
    "React", "Vue", "Angular", "Svelte", "Next.js", "Nuxt", "SolidJS", "Astro", "Remix",
    "FastAPI", "Flask", "Django", "Express", "NestJS", "Spring Boot", "Spring", "Laravel",
    "Ruby on Rails", "Rails", "Flutter", "React Native", "Tauri", "Electron", "PyTorch",
    "TensorFlow", "JAX", "Keras", "Pandas", "NumPy", "Polars", "Tailwind", "Tailwind CSS",
    # Modelos IA & Proveedores
    "DeepSeek", "OpenAI", "Anthropic", "Claude", "ChatGPT", "GPT-4o", "GPT-4", "Gemini",
    "Mistral", "Llama", "Ollama", "Grok", "Qwen", "Hugging Face", "Whisper", "Stable Diffusion",
    "Midjourney", "Sora", "Runway", "LLM", "LLMs", "MoE", "RAG", "Transformer", "Transformers",
    # Runtimes, Contenedores, Nube & BD
    "Node.js", "Node", "Bun", "Deno", "Docker", "Kubernetes", "K8s", "Podman", "Linux",
    "Ubuntu", "Debian", "Arch Linux", "Git", "GitHub", "GitLab", "Bitbucket", "PostgreSQL",
    "Postgres", "MySQL", "MariaDB", "SQLite", "Redis", "MongoDB", "Kafka", "RabbitMQ",
    "Nginx", "Apache", "Caddy", "Cloudflare", "AWS", "Azure", "GCP", "Vercel", "Netlify",
    "Supabase", "Firebase", "Prisma", "GraphQL", "REST", "gRPC", "API", "APIs", "SDK",
    "CLI", "IDE", "VS Code", "Neovim", "Vim", "CUDA", "LLVM", "V8", "WebKit", "Chromium",
    "Firefox", "Safari"
]

PROTECTED_TECH_TERMS.sort(key=len, reverse=True)

VERSION_REGEX = re.compile(r'\b[vV]?\d+(\.\d+)+(-[a-zA-Z0-9.]+)?\b')

def mask_technical_terms(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Sustituye nombres de tecnologías y versiones por tokens neutros __TKX__
    antes de la traducción para evitar traducciones erróneas (ej. 'Rust' -> 'óxido').
    """
    if not text:
        return text, {}

    placeholders: Dict[str, str] = {}
    counter = 0

    # 1. Enmascarar números de versión semántica (ej. 1.85.0, v2.6)
    def mask_ver(m):
        nonlocal counter
        ph = f"__DEVVER{counter}__"
        placeholders[ph] = m.group(0)
        counter += 1
        return ph

    masked = VERSION_REGEX.sub(mask_ver, text)

    # 2. Enmascarar términos y nombres propios técnicos con límite de palabra
    for term in PROTECTED_TECH_TERMS:
        escaped = re.escape(term)
        pattern = re.compile(rf'(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])', re.IGNORECASE)
        matches = list(pattern.finditer(masked))
        if matches:
            for m in reversed(matches):
                ph = f"__DEVTECH{counter}__"
                placeholders[ph] = term
                counter += 1
                start, end = m.span()
                masked = masked[:start] + ph + masked[end:]

    return masked, placeholders

def unmask_technical_terms(text: str, placeholders: Dict[str, str]) -> str:
    """Restaura los términos técnicos originales a partir de los tokens neutros."""
    if not text or not placeholders:
        return text

    result = text
    for ph, orig in placeholders.items():
        result = re.sub(re.escape(ph), orig, result, flags=re.IGNORECASE)
        core_token = ph.strip("_")
        broken_token = rf'__\s*{core_token}\s*__'
        result = re.sub(broken_token, orig, result, flags=re.IGNORECASE)

    return result

def clean_software_domain_translations(text: str, target_lang: str) -> str:
    """
    Corrige expresiones técnicas que hayan sido traducidas con connotaciones erróneas.
    """
    if not text:
        return text

    if target_lang == "es":
        text = re.sub(r'\b(óxido|oxido)\b', 'Rust', text, flags=re.IGNORECASE)
        text = re.sub(r'\bliberaci[oó]n de prueba\b', 'Versión de prueba', text, flags=re.IGNORECASE)
        text = re.sub(r'\bliberaci[oó]n oficial\b', 'Lanzamiento oficial', text, flags=re.IGNORECASE)
        text = re.sub(r'\bliberaci[oó]n\b', 'Lanzamiento', text, flags=re.IGNORECASE)
        text = re.sub(r'\bbicho(s)?\b', 'bug\\1', text, flags=re.IGNORECASE)
    elif target_lang == "pt":
        text = re.sub(r'\b(ferrugem)\b', 'Rust', text, flags=re.IGNORECASE)
        text = re.sub(r'\blibera[cç][aã]o de teste\b', 'Versão de teste', text, flags=re.IGNORECASE)
        text = re.sub(r'\blibera[cç][aã]o\b', 'Lançamento', text, flags=re.IGNORECASE)
    elif target_lang == "fr":
        text = re.sub(r'\b(rouille)\b', 'Rust', text, flags=re.IGNORECASE)
        text = re.sub(r'\blib[eé]ration\b', 'Version', text, flags=re.IGNORECASE)
    elif target_lang == "de":
        text = re.sub(r'\b(rost)\b', 'Rust', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfreigabe\b', 'Release', text, flags=re.IGNORECASE)

    return text

def init_translation_cache():
    """Initializes persistent translation cache and purges old bad translations."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translations_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_hash TEXT UNIQUE NOT NULL,
                    source_text TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trans_hash ON translations_cache(source_hash);")
            conn.execute("""
                DELETE FROM translations_cache 
                WHERE translated_text LIKE '%óxido%' 
                   OR translated_text LIKE '%oxido%'
                   OR translated_text LIKE '%ferrugem%'
                   OR translated_text LIKE '%rouille%'
                   OR translated_text LIKE '%Liberación de prueba%';
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"Error initializing translation cache: {e}")

def get_cache_key(text: str, target_lang: str) -> str:
    import hashlib
    clean = text.strip()
    return hashlib.sha256(f"{target_lang}:{clean}".encode("utf-8")).hexdigest()

def get_cached_translation(text: str, target_lang: str) -> Optional[str]:
    if not text:
        return ""
    key = get_cache_key(text, target_lang)
    if key in _MEM_CACHE:
        return _MEM_CACHE[key]

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT translated_text FROM translations_cache WHERE source_hash = ? LIMIT 1;", (key,))
            row = cursor.fetchone()
            if row:
                _MEM_CACHE[key] = row[0]
                return row[0]
    except Exception:
        pass
    return None

def set_cached_translation(text: str, target_lang: str, translated: str):
    if not text or not translated:
        return
    key = get_cache_key(text, target_lang)
    _MEM_CACHE[key] = translated

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO translations_cache (source_hash, source_text, target_lang, translated_text)
                VALUES (?, ?, ?, ?);
            """, (key, text, target_lang, translated))
            conn.commit()
    except Exception as e:
        logger.debug(f"Failed to persist translation: {e}")

SUPPORTED_LANGUAGES = {
    "es": {"name": "Español", "flag": "🇪🇸", "tag": "es-ES"},
    "en": {"name": "English", "flag": "🇬🇧", "tag": "en-US"},
    "pt": {"name": "Português", "flag": "🇵🇹", "tag": "pt-PT"},
    "fr": {"name": "Français", "flag": "🇫🇷", "tag": "fr-FR"},
    "de": {"name": "Deutsch", "flag": "🇩🇪", "tag": "de-DE"},
}

def normalize_lang_code(code: str) -> str:
    """Normalize language code to 2-letter format, default 'es'."""
    clean = (code or "").lower().strip()[:2]
    return clean if clean in SUPPORTED_LANGUAGES else "es"

_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "*/*",
}

async def _fetch_translation_remote(masked_text: str, target_code: str, source_lang: str = "auto") -> Optional[str]:
    """
    Direct multi-tier translation request:
    1. Google Translate via dict-chrome-ex client (highly reliable, no datacenter blocks)
    2. Google Translate via webapp client
    3. MyMemory API with 2-letter language codes
    """
    src = source_lang if source_lang != "auto" else "auto"

    async with httpx.AsyncClient(headers=_HTTP_HEADERS, timeout=3.0, follow_redirects=True) as client:
        # Tier 1: Google dict-chrome-ex
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&sl={src}&tl={target_code}&dt=t&q=" + urllib.parse.quote(masked_text)
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    result = "".join(s[0] for s in data[0] if s and isinstance(s, list) and s[0])
                    if result:
                        return result
        except Exception as e:
            logger.debug(f"Tier 1 (dict-chrome-ex) error: {e}")

        # Tier 2: Google webapp client
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=webapp&sl={src}&tl={target_code}&dt=t&q=" + urllib.parse.quote(masked_text)
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    result = "".join(s[0] for s in data[0] if s and isinstance(s, list) and s[0])
                    if result:
                        return result
        except Exception as e:
            logger.debug(f"Tier 2 (webapp) error: {e}")

        # Tier 3: MyMemory with 2-letter codes (en|es, es|en, etc.)
        try:
            mm_src = "en" if src == "auto" else src[:2]
            mm_tgt = target_code[:2]
            if mm_src == mm_tgt:
                return masked_text

            mm_url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(masked_text)}&langpair={mm_src}|{mm_tgt}"
            resp = await client.get(mm_url)
            if resp.status_code == 200:
                mm_data = resp.json()
                translated = mm_data.get("responseData", {}).get("translatedText")
                if translated and not translated.startswith("MYMEMORY WARNING"):
                    return translated
        except Exception as e:
            logger.debug(f"Tier 3 (MyMemory) error: {e}")

    return None

def _fetch_translation_remote_sync(masked_text: str, target_code: str, source_lang: str = "auto") -> Optional[str]:
    """Synchronous fallback for CLI or tests."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, _fetch_translation_remote(masked_text, target_code, source_lang)).result(timeout=4.0)
        else:
            return loop.run_until_complete(_fetch_translation_remote(masked_text, target_code, source_lang))
    except Exception:
        # Direct urllib sync call as failsafe
        try:
            import urllib.request
            import json
            src = source_lang if source_lang != "auto" else "auto"
            url = f"https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&sl={src}&tl={target_code}&dt=t&q=" + urllib.parse.quote(masked_text)
            req = urllib.request.Request(url, headers=_HTTP_HEADERS)
            with urllib.request.urlopen(req, timeout=3.0) as r:
                data = json.loads(r.read().decode("utf-8"))
                return "".join(s[0] for s in data[0] if s and isinstance(s, list) and s[0])
        except Exception as e:
            logger.debug(f"Sync translation failsafe error: {e}")
            return None

async def translate_text_async(text: str, target_lang: str = "es", source_lang: str = "auto") -> str:
    """
    Translates a text string asynchronously with Technical Terminology Shield
    and persistent SQLite caching.
    """
    if not text or not text.strip():
        return ""

    target_code = normalize_lang_code(target_lang)
    cached = get_cached_translation(text, target_code)
    if cached:
        sanitized = clean_software_domain_translations(cached, target_code)
        if sanitized != cached:
            set_cached_translation(text, target_code, sanitized)
        return sanitized

    masked_text, placeholders = mask_technical_terms(text)
    translated = await _fetch_translation_remote(masked_text, target_code, source_lang)

    if not translated:
        translated = text
    else:
        translated = unmask_technical_terms(translated, placeholders)

    translated = clean_software_domain_translations(translated, target_code)
    set_cached_translation(text, target_code, translated)
    return translated

def translate_text(text: str, target_lang: str = "es", source_lang: str = "auto") -> str:
    """
    Synchronous wrapper for translate_text_async.
    """
    if not text or not text.strip():
        return ""

    target_code = normalize_lang_code(target_lang)
    cached = get_cached_translation(text, target_code)
    if cached:
        sanitized = clean_software_domain_translations(cached, target_code)
        if sanitized != cached:
            set_cached_translation(text, target_code, sanitized)
        return sanitized

    masked_text, placeholders = mask_technical_terms(text)
    translated = _fetch_translation_remote_sync(masked_text, target_code, source_lang)

    if not translated:
        translated = text
    else:
        translated = unmask_technical_terms(translated, placeholders)

    translated = clean_software_domain_translations(translated, target_code)
    set_cached_translation(text, target_code, translated)
    return translated

def translate_article_payload(article: Dict[str, Any], target_lang: str = "es") -> Dict[str, Any]:
    """
    Synchronous translation of a single article payload.
    """
    target_code = normalize_lang_code(target_lang)

    orig_title = article.get("title", "")
    if target_code == "en":
        translated_title = orig_title
    else:
        translated_title = translate_text(orig_title, target_lang=target_code)

    orig_dialogue = article.get("explanatory_dialogue", "")
    if target_code == "es":
        translated_dialogue = orig_dialogue
    else:
        translated_dialogue = translate_text(orig_dialogue, target_lang=target_code, source_lang="es") if orig_dialogue else ""

    bullets = article.get("summary_bullets", [])
    translated_bullets = []
    for b in bullets:
        if target_code == "es":
            translated_bullets.append(b)
        else:
            translated_bullets.append(translate_text(b, target_lang=target_code, source_lang="auto"))

    new_art = dict(article)
    new_art["title"] = translated_title or orig_title
    new_art["explanatory_dialogue"] = translated_dialogue or orig_dialogue
    new_art["summary_bullets"] = translated_bullets or bullets
    new_art["is_translated"] = (target_code != "es")
    new_art["lang"] = target_code
    return new_art

async def translate_articles_batch_async(articles: List[Dict[str, Any]], target_lang: str = "es") -> List[Dict[str, Any]]:
    """
    High-performance parallel async translator for an entire page of articles.
    Performs translations concurrently with caching and a semaphore limit.
    """
    if not articles:
        return []

    target_code = normalize_lang_code(target_lang)
    semaphore = asyncio.Semaphore(10)

    async def sem_translate(text: str, src: str = "auto") -> str:
        async with semaphore:
            return await translate_text_async(text, target_lang=target_code, source_lang=src)

    # Prepare translation tasks for all articles
    tasks = []
    task_keys = []

    for idx, art in enumerate(articles):
        # 1. Title
        orig_title = art.get("title", "")
        if target_code != "en" and orig_title:
            task_keys.append((idx, "title", None))
            tasks.append(sem_translate(orig_title, "auto"))

        # 2. Dialogue
        orig_dialogue = art.get("explanatory_dialogue", "")
        if target_code != "es" and orig_dialogue:
            task_keys.append((idx, "explanatory_dialogue", None))
            tasks.append(sem_translate(orig_dialogue, "es"))

        # 3. Bullets
        if target_code != "es":
            bullets = art.get("summary_bullets", [])
            for b_idx, b in enumerate(bullets):
                task_keys.append((idx, "bullet", b_idx))
                tasks.append(sem_translate(b, "auto"))

    # Execute all translation tasks in parallel
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    else:
        results = []

    # Map results back to articles
    translated_articles = [dict(a) for a in articles]
    for art in translated_articles:
        art["is_translated"] = (target_code != "es")
        art["lang"] = target_code
        if target_code != "es":
            art["summary_bullets"] = list(art.get("summary_bullets", []))

    for (a_idx, field, b_idx), res in zip(task_keys, results):
        if isinstance(res, Exception) or not res:
            continue
        if field == "title":
            translated_articles[a_idx]["title"] = res
        elif field == "explanatory_dialogue":
            translated_articles[a_idx]["explanatory_dialogue"] = res
        elif field == "bullet" and b_idx is not None:
            if b_idx < len(translated_articles[a_idx]["summary_bullets"]):
                translated_articles[a_idx]["summary_bullets"][b_idx] = res

    return translated_articles


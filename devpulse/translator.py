"""
DevPulse - Universal Translation Engine
Provides caching, multi-provider translation, and bilingual support for news and UI.
"""
import sqlite3
import logging
import re
from typing import Optional, Dict, Any, List, Tuple
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

# Ordenar por longitud descendente para que "Spring Boot" tenga precedencia sobre "Spring"
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
        # Word boundary seguro para caracteres alfanuméricos y especiales como C++
        pattern = re.compile(rf'(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])', re.IGNORECASE)
        
        matches = list(pattern.finditer(masked))
        if matches:
            for m in reversed(matches):
                ph = f"__DEVTECH{counter}__"
                placeholders[ph] = term  # Preservar mayúsculas oficiales (ej. 'Rust', 'Python')
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
        # Reemplazar placeholder directo o con posibles espacios añadidos por el traductor
        result = re.sub(re.escape(ph), orig, result, flags=re.IGNORECASE)
        core_token = ph.strip("_")
        broken_token = rf'__\s*{core_token}\s*__'
        result = re.sub(broken_token, orig, result, flags=re.IGNORECASE)

    return result

def clean_software_domain_translations(text: str, target_lang: str) -> str:
    """
    Corrige expresiones técnicas que hayan sido traducidas con connotaciones erróneas.
    Ej: 'Liberación de prueba' -> 'Versión de prueba', 'óxido' -> 'Rust'.
    """
    if not text:
        return text

    if target_lang == "es":
        # Corrección obligatoria de Rust si se filtró en caché previa
        text = re.sub(r'\b(óxido|oxido)\b', 'Rust', text, flags=re.IGNORECASE)
        # Corrección de terminología de lanzamientos software
        text = re.sub(r'\bliberaci[oó]n de prueba\b', 'Versión de prueba', text, flags=re.IGNORECASE)
        text = re.sub(r'\bliberaci[oó]n oficial\b', 'Lanzamiento oficial', text, flags=re.IGNORECASE)
        text = re.sub(r'\bliberaci[oó]n\b', 'Lanzamiento', text, flags=re.IGNORECASE)
        # Correcciones de bugs y errores
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
    """Initializes the persistent translation cache table and purges obsolete mistranslations."""
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
            
            # Purgar traducciones erróneas previas (como 'óxido' o 'liberación de prueba')
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

def translate_text(text: str, target_lang: str = "es", source_lang: str = "auto") -> str:
    """
    Translates a text string to target_lang (es, en, pt, fr, de) with
    Technical Terminology Shield (preserves Rust, Python, Go, version tags, etc.)
    and persistent SQLite caching.
    """
    if not text or not text.strip():
        return ""

    target_code = normalize_lang_code(target_lang)
    cached = get_cached_translation(text, target_code)
    if cached:
        # Sanitize any legacy cached entries (e.g. from before shield was active)
        sanitized = clean_software_domain_translations(cached, target_code)
        if sanitized != cached:
            set_cached_translation(text, target_code, sanitized)
        return sanitized

    # 1. Mask protected technical terms and SemVer numbers
    masked_text, placeholders = mask_technical_terms(text)

    # 2. Attempt Translation with providers
    translated = None
    try:
        from deep_translator import MyMemoryTranslator
        src_tag = "en-US"
        tgt_tag = SUPPORTED_LANGUAGES.get(target_code, {}).get("tag", "es-ES")
        if target_code == "en":
            src_tag = "es-ES"
            tgt_tag = "en-US"

        t = MyMemoryTranslator(source=src_tag, target=tgt_tag)
        translated = t.translate(masked_text)
    except Exception as e:
        logger.debug(f"MyMemoryTranslator error for {target_code}: {e}")

    # Fallback to GoogleTranslator if needed
    if not translated:
        try:
            from deep_translator import GoogleTranslator
            gt = GoogleTranslator(source=source_lang, target=target_code)
            translated = gt.translate(masked_text)
        except Exception as e:
            logger.debug(f"GoogleTranslator fallback failed for {target_code}: {e}")

    if not translated:
        # Graceful fallback: return original text
        translated = text
    else:
        # 3. Unmask protected technical terms (restore Rust, Go, Python, v1.85.0, etc.)
        translated = unmask_technical_terms(translated, placeholders)

    # 4. Clean domain software vocabulary (e.g. 'Liberación de prueba' -> 'Versión de prueba')
    translated = clean_software_domain_translations(translated, target_code)

    set_cached_translation(text, target_code, translated)
    return translated

def translate_article_payload(article: Dict[str, Any], target_lang: str = "es") -> Dict[str, Any]:
    """
    Translates title, explanatory dialogue, and summary bullets of an article to the target language.
    """
    target_code = normalize_lang_code(target_lang)

    # 1. Translate Title (original is usually English)
    orig_title = article.get("title", "")
    if target_code == "en":
        translated_title = orig_title
    else:
        translated_title = translate_text(orig_title, target_lang=target_code)

    # 2. Translate Explanatory Dialogue (original is Spanish)
    orig_dialogue = article.get("explanatory_dialogue", "")
    if target_code == "es":
        translated_dialogue = orig_dialogue
    else:
        translated_dialogue = translate_text(orig_dialogue, target_lang=target_code, source_lang="es") if orig_dialogue else ""

    # 3. Translate Summary Bullets
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


import re
from typing import List, Tuple, Dict, Any
from bs4 import BeautifulSoup
from devpulse.translator import translate_text

# ==============================================================================
# 🧠 DICCIONARIO DE DOMINIOS TÉCNICOS & ARQUITECTURA
# Permite interpretar con precisión el impacto real de cada tecnología sin frases genéricas
# ==============================================================================
TECH_DOMAINS = [
    {
        "pattern": r"\b(webassembly|wasm|wasmgc|jspi)\b",
        "name": "WebAssembly",
        "context": "en el entorno de ejecución WebAssembly y motores de navegador",
        "problem": "la penalización de rendimiento en llamadas indirectas y la complejidad de coordinar código síncrono con APIs asíncronas",
        "benefit": "acelerar aplicaciones web complejas, motores gráficos y lenguajes compilados (Rust, C++, Dart/Flutter) con rendimiento cercano a código nativo"
    },
    {
        "pattern": r"\b(v8|v8 engine|javascript engine|spider_?monkey|javascriptcore)\b",
        "name": "Motores JavaScript / V8",
        "context": "en el motor de ejecución de Chromium, Node.js y Deno",
        "problem": "los cuellos de botella de parseo, compilación JIT y tiempo de arranque en aplicaciones web modernas",
        "benefit": "reducir tiempos de carga inicial (startup time), disminuir latencia de compilación y optimizar el consumo de CPU y memoria"
    },
    {
        "pattern": r"\b(rust|cargo|rustc)\b",
        "name": "Ecosistema Rust",
        "context": "en el lenguaje Rust y su compilador rustc",
        "problem": "la gestión estricta de concurrencia, tiempos de compilación y ergonomía de sintaxis en sistemas de memoria segura",
        "benefit": "escribir software de infraestructura robusto, de alta velocidad y libre de condiciones de carrera con soporte nativo de edición"
    },
    {
        "pattern": r"\b(python|cpython|pypy|pep\s*\d+|gil|uvicorn|fastapi|django)\b",
        "name": "Ecosistema Python",
        "context": "en el ecosistema de Python y desarrollo backend / datos",
        "problem": "limitaciones de concurrencia del GIL, tipado estático gradual y tiempos de procesamiento en tareas intensivas",
        "benefit": "simplificar el desarrollo de APIs, mejorar el rendimiento en ejecución concurrente y acelerar flujos de trabajo en producción"
    },
    {
        "pattern": r"\b(react|next\.?js|turbopack|server components|vue|nuxt|svelte|astro|tailwind)\b",
        "name": "Frameworks Web & UI",
        "context": "en el desarrollo frontend y renderizado web moderno",
        "problem": "la sobrecarga de hidratación en el cliente, complejidad en el manejo de estado y tiempos de compilación en desarrollo",
        "benefit": "mejorar métricas de Core Web Vitals, acelerar compilaciones y desacoplar la lógica de servidor y cliente con componentes modernos"
    },
    {
        "pattern": r"\b(llm|llms|deepseek|claude|openai|gpt-?4|anthropic|qwen|mistral|ollama|transformer|rag|diffusion|whisper)\b",
        "name": "Modelos de IA & Machine Learning",
        "context": "en el despliegue e inferencia de inteligencia artificial y modelos de lenguaje",
        "problem": "el elevado consumo de VRAM/cómputo por token, la latencia en inferencia y la consistencia en el razonamiento de agentes autónomos",
        "benefit": "desplegar modelos más eficientes, reducir costes de API por millón de tokens y orquestar flujos de ingeniería con mayor fidelidad"
    },
    {
        "pattern": r"\b(cloudflare|workers|edge|serverless|fastly|vercel|aws|lambda|gcp|azure)\b",
        "name": "Nube, Edge & Serverless",
        "context": "en la infraestructura de nube distribuida y computación en el borde (Edge)",
        "problem": "la latencia geográfica de servidores centrales y el coste de escalar servicios globales con estado",
        "benefit": "ejecutar código con latencia de un dígito de milisegundos junto a los usuarios y simplificar despliegues sin gestionar servidores dedicados"
    },
    {
        "pattern": r"\b(docker|kubernetes|k8s|podman|container|helm|ci/cd|github actions|terraform)\b",
        "name": "DevOps, Contenedores & CI/CD",
        "context": "en la orquestación de contenedores y automatización de despliegues",
        "problem": "la sobrecarga operativa en clústeres, complejidad de configuraciones y lentitud en los ciclos de entrega de código",
        "benefit": "estandarizar entornos de producción reproducibles, optimizar el uso de nodos y acelerar los pipelines de validación y despliegue"
    },
    {
        "pattern": r"\b(cve|vulnerability|exploit|malware|zero-?day|backdoor|rce|injection|security advisory)\b",
        "name": "Seguridad & Ciberdefensa",
        "context": "en la seguridad de software y protección de la cadena de suministro",
        "problem": "vulnerabilidades de ejecución remota de código, escalada de privilegios o paquetes comprometidos que exponen infraestructura crítica",
        "benefit": "auditar dependencias, aplicar parches de mitigación y blindar entornos de producción contra vectores de ataque activos"
    },
    {
        "pattern": r"\b(postgres|postgresql|sqlite|database|sql|vector search|redis|mongodb|mysql)\b",
        "name": "Bases de Datos & Almacenamiento",
        "context": "en la capa de persistencia de datos, consultas e indexación",
        "problem": "cuellos de botella en lecturas/escrituras masivas, contención de bloqueos y latencia en búsquedas sobre vectores o texto no estructurado",
        "benefit": "optimizar planes de ejecución, reducir tiempos de respuesta en consultas críticas y asegurar alta disponibilidad con motores fiables"
    },
    {
        "pattern": r"\b(git|github|gitlab|version control|repository|code review)\b",
        "name": "Control de Versiones & Git",
        "context": "en la gestión de código fuente y colaboración de ingeniería",
        "problem": "fricciones en repositorios masivos (monorepos), sincronización distribuida y dependencia de plataformas propietarias",
        "benefit": "mantener operaciones de control de versiones rápidas, flujos de revisión transparentes y pipelines de integración resilientes"
    },
    {
        "pattern": r"\b(linux|kernel|gpu|vulkan|mesa|driver|amd|nvidia|intel|wayland)\b",
        "name": "Linux, Kernel & Gráficos",
        "context": "en el sistema operativo Linux y controladores de bajo nivel",
        "problem": "la compatibilidad de hardware, sobrecoste de llamadas al sistema y eficiencia en el manejo de memoria gráfica",
        "benefit": "mayor estabilidad en servidores, soporte extendido para hardware moderno y mejor rendimiento en cargas intensivas de cómputo y renderizado"
    },
    {
        "pattern": r"\b(act|law|bill|senate|congress|ban|regulation|copyright|pope|ethic|safety policy)\b",
        "name": "Regulación, Políticas & Privacidad Tech",
        "context": "en el marco regulatorio y estándares de privacidad de la industria digital",
        "problem": "incertidumbre legal sobre el uso de datos, supervisión automatizada y cumplimiento de nuevas normativas de IA y software",
        "benefit": "anticipar cambios de cumplimiento normativo (compliance), proteger la privacidad de usuarios y blindar arquitecturas de producto"
    }
]

def clean_html_and_markdown(text: str) -> str:
    """Elimina etiquetas HTML, formato markdown ruidoso y texto residual de agregadores."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")

    text = re.sub(r'#+\s*', '', text)  # Quitar encabezados markdown
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [texto](url) -> texto
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'Puntos en Hacker News:\s*\d+\s*\|\s*Comentarios:\s*\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_high_signal_sentences(content: str) -> List[str]:
    """Extrae las oraciones con mayor densidad técnica, métricas cuantitativas y cambios de arquitectura."""
    cleaned = clean_html_and_markdown(content)
    raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    candidates = []

    for s in raw_sentences:
        s = s.strip()
        if len(s) < 28 or len(s) > 280:
            continue
        lower_s = s.lower()
        if any(bp in lower_s for bp in [
            "subscribe", "click here", "sign up", "cookie", "privacy policy", 
            "all rights reserved", "in this blog post", "in this article", 
            "share on", "leave a comment", "written by", "read more"
        ]):
            continue
        
        # Ponderar por información técnica concreta
        score = 0
        if re.search(r'\b\d+(\.\d+)?(%|ms|s|x|gb|mb|kb|v\d+)?\b', s):
            score += 4  # Métricas o números concretos
        if re.search(r'\b(optimiz|speedup|faster|reduc|improv|support|implement|perform|architectur|allocat|compil|runtim|latenc|bench)\w*', s, re.I):
            score += 3  # Verbos de ingeniería
        if re.search(r'\b(api|v8|wasm|rust|python|memory|thread|async|kernel|server|cach|token|weight|model)\w*', s, re.I):
            score += 2  # Sustantivos técnicos clave
            
        candidates.append((score, s))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [c[1] for c in candidates[:4]]

def generate_explanatory_dialogue(title: str, content: str = "", topic: str = "") -> str:
    """
    Produce un diálogo explicativo detallado, claro y específico que responde:
    ¿Qué es esta tecnología? ¿Qué problema técnico resuelve? ¿Cómo impacta a los ingenieros?
    """
    clean_title = clean_html_and_markdown(title)
    clean_body = clean_html_and_markdown(content)
    full_text = f"{clean_title} {clean_body}".lower()

    # 1. Identificar el dominio técnico
    matched_domain = None
    for d in TECH_DOMAINS:
        if re.search(d["pattern"], full_text):
            matched_domain = d
            break

    # 2. Extraer oraciones técnicas de alto valor del contenido
    top_sentences = extract_high_signal_sentences(content)
    
    # 3. Detectar la naturaleza del cambio
    is_perf = bool(re.search(r'\b(optimiz|speed|fast|perform|reduc|accelerat|inlin|deopt|latenc)\w*', full_text))
    is_release = bool(re.search(r'\b(release|v\d+\.|\d+\.\d+|introduc|announc|launch|new version)\w*', full_text))
    is_security = bool(re.search(r'\b(secur|cve|vulnerab|exploit|threat|protect|malware|patch)\w*', full_text))

    if matched_domain and top_sentences:
        # Contenido rico + Dominio identificado: Máxima precisión
        primary_fact = top_sentences[0]
        translated_fact = translate_text(primary_fact, "es").strip()
        # Formatear minúscula inicial si procede
        if translated_fact and not translated_fact[0].isupper():
            translated_fact = translated_fact[0].lower() + translated_fact[1:]

        dialogue = (
            f"¿Qué problema resuelve y por qué es relevante? «{clean_title}» introduce un avance significativo {matched_domain['context']}. "
            f"El detalle técnico clave es que {translated_fact.rstrip('.')}. "
            f"En la práctica, esta solución aborda {matched_domain['problem']}, permitiendo a los ingenieros {matched_domain['benefit']} "
            f"sin comprometer la estabilidad del sistema en entornos productivos."
        )
    elif matched_domain:
        # Dominio identificado, síntesis a partir del título
        dialogue = (
            f"¿Qué representa este hito y por qué seguirlo de cerca? «{clean_title}» impacta de forma directa {matched_domain['context']}. "
            f"Esta iniciativa busca mitigar {matched_domain['problem']}, ofreciendo una arquitectura pensada para {matched_domain['benefit']}. "
            f"Para los desarrolladores, representa una referencia obligada al tomar decisiones de arquitectura, compatibilidad y evolución de su pila técnica."
        )
    elif top_sentences:
        # Contenido rico con dominio general
        translated_fact = translate_text(top_sentences[0], "es").strip()
        dialogue = (
            f"¿Cuál es el trasfondo técnico de esta novedad? «{clean_title}» aporta una solución orientada a modernizar flujos de ingeniería. "
            f"El avance central reporta que {translated_fact.rstrip('.')}. "
            f"Para los equipos de desarrollo, esto reduce fricciones operativas, optimiza el consumo de recursos en producción y abre nuevas alternativas arquitectónicas."
        )
    else:
        # Síntesis orientada a la acción del título
        if is_security:
            action_desc = "un aviso crítico de seguridad y mitigación de amenazas"
            impact_desc = "identificar vectores de ataque potenciales, aplicar parches correctivos y proteger la integridad de los despliegues"
        elif is_perf:
            action_desc = "una optimización técnica focalizada en rendimiento y baja latencia"
            impact_desc = "reducir el consumo de CPU y memoria, acelerando el tiempo de respuesta de aplicaciones en producción"
        elif is_release:
            action_desc = "un lanzamiento oficial con refinamientos de arquitectura y compatibilidad"
            impact_desc = "incorporar nuevas capacidades de desarrollo, eliminar dependencias obsoletas y mejorar la estabilidad del código"
        else:
            action_desc = "un desarrollo relevante en la industria del software"
            impact_desc = "adoptar patrones modernos de diseño de sistemas y elevar la calidad de los flujos de ingeniería"

        dialogue = (
            f"¿Por qué importa a los desarrolladores? «{clean_title}» representa {action_desc}. "
            f"Su relevancia radica en que permite a los equipos {impact_desc}, "
            f"ayudando a tomar mejores decisiones técnicas y evitando problemas de escalabilidad a largo plazo."
        )

    return dialogue

def extract_key_highlights(title: str, content: str = "", max_bullets: int = 3) -> Tuple[List[str], int]:
    """
    Genera 2 a 3 viñetas concretas, claras y con alta densidad informativa en español.
    Retorna: (bullets_list, estimated_read_time_seconds)
    """
    clean_title = clean_html_and_markdown(title)
    clean_body = clean_html_and_markdown(content)
    full_text = f"{clean_title} {clean_body}".lower()

    matched_domain = None
    for d in TECH_DOMAINS:
        if re.search(d["pattern"], full_text):
            matched_domain = d
            break

    top_sentences = extract_high_signal_sentences(content)
    is_perf = bool(re.search(r'\b(optimiz|speed|fast|perform|reduc|accelerat|inlin|deopt|latenc)\w*', full_text))
    is_release = bool(re.search(r'\b(release|v\d+\.|\d+\.\d+|introduc|announc|launch|new)\w*', full_text))
    is_security = bool(re.search(r'\b(secur|cve|vulnerab|exploit|threat|protect|malware|patch)\w*', full_text))

    bullets: List[str] = []

    # Viñeta 1: El hito central traducido y limpio
    trans_title = translate_text(clean_title, "es")
    clean_h1 = re.sub(r'^(lanzamiento e impacto|hito principal|novedad):\s*', '', trans_title, flags=re.I).strip()
    clean_h1 = clean_h1[0].upper() + clean_h1[1:] if clean_h1 else clean_title
    bullets.append(clean_h1)

    # Viñeta 2: Métrica o detalle técnico extraído del contenido
    if top_sentences:
        b2 = translate_text(top_sentences[0], "es").strip()
        b2 = re.sub(r'^(por ejemplo|in this blog post|in this article|we explain)\s*,?\s*', '', b2, flags=re.I).strip()
        b2 = b2[0].upper() + b2[1:] if b2 else ""
        if b2 and b2 not in bullets:
            bullets.append(b2)

    # Viñeta 3: Segunda métrica o consecuencia práctica
    if len(top_sentences) > 1 and len(bullets) < max_bullets:
        b3 = translate_text(top_sentences[1], "es").strip()
        b3 = re.sub(r'^(por ejemplo|furthermore|additionally|además)\s*,?\s*', '', b3, flags=re.I).strip()
        b3 = b3[0].upper() + b3[1:] if b3 else ""
        if b3 and b3 not in bullets:
            bullets.append(b3)

    # Rellenar si el contenido original era muy breve (ej. links de Hacker News)
    if len(bullets) < 2 and matched_domain:
        bullets.append(f"Objetivo de ingeniería: diseñado para {matched_domain['benefit']}.")

    if len(bullets) < max_bullets:
        if is_security:
            bullets.append("Acción recomendada: auditar dependencias y aplicar parches de seguridad de forma prioritaria.")
        elif is_perf:
            bullets.append("Impacto en producción: reduce latencia y sobrecarga de CPU en cargas de trabajo intensivas.")
        elif is_release:
            bullets.append("Disponibilidad: listo para evaluación en entornos de desarrollo y actualización recomendada.")
        elif matched_domain:
            bullets.append(f"Contexto: optimización relevante {matched_domain['context']}.")
        else:
            bullets.append("Relevancia para la industria: establece patrones modernos para arquitecturas de software escalables.")

    bullets = bullets[:max_bullets]
    total_words = sum(len(b.split()) for b in bullets)
    read_time = max(10, min(30, int(total_words / 3.2)))

    return bullets, read_time

def process_news_detail(title: str, content: str = "", topic: str = "") -> Dict[str, Any]:
    """
    Retorna el detalle completo sintetizado: diálogo explicativo + ideas principales + tiempo de lectura.
    """
    dialogue = generate_explanatory_dialogue(title, content, topic)
    bullets, read_time = extract_key_highlights(title, content)
    return {
        "explanatory_dialogue": dialogue,
        "summary_bullets": bullets,
        "read_time_seconds": read_time
    }


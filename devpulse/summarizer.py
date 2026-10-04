"""
DevPulse - Intelligent News Synthesizer
Generates:
1. Explanatory Dialogue ("Diálogo Explicativo"): A conversational, clear explanation
   answering what this is, why it matters, and how it impacts engineers.
2. Key Highlights ("Ideas Principales"): 2-3 high-signal bullet points.
3. 15-second estimated reading time.
"""
import re
from typing import List, Tuple, Dict, Any
from bs4 import BeautifulSoup

def clean_html_and_markdown(text: str) -> str:
    """Strip HTML tags, raw URLs, and markdown noise."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")

    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_explanatory_dialogue(title: str, content: str = "", topic: str = "") -> str:
    """
    Produces a clear, engaging, conversational technical explanation (Diálogo Explicativo)
    detailing what problem this technology solves and why developers should care.
    """
    clean_title = clean_html_and_markdown(title)
    clean_body = clean_html_and_markdown(content)
    
    # Identify subject & action
    lower_t = clean_title.lower()

    if "model" in lower_t or "llm" in lower_t or "deepseek" in lower_t or "claude" in lower_t or "gpt" in lower_t or "ai" in lower_t:
        dialogue = (
            f"¿Qué representa este avance? Con «{clean_title}», el ecosistema de inteligencia artificial da un paso clave "
            f"en eficiencia de inferencia y capacidad de razonamiento. Para los desarrolladores, esto se traduce en menor latencia, "
            f"costes reducidos al desplegar modelos en producción y nuevas posibilidades para orquestar agentes autónomos con mayor fiabilidad."
        )
    elif "release" in lower_t or "v1." in lower_t or "v2." in lower_t or "v3." in lower_t or "versión" in lower_t:
        dialogue = (
            f"¿Por qué es importante esta actualización? «{clean_title}» introduce refinamientos críticos de rendimiento, compatibilidad "
            f"y ergonomía de desarrollo. Resuelve fricciones históricas en el ciclo de vida del software, optimizando tiempos de compilación "
            f"o ejecución para equipos que construyen sobre esta pila tecnológica."
        )
    elif "vulnerability" in lower_t or "cve" in lower_t or "security" in lower_t or "exploit" in lower_t:
        dialogue = (
            f"¿Cuál es el impacto en seguridad? La alerta «{clean_title}» expone vectores de ataque que podrían comprometer la integridad "
            f"de entornos en la nube o cadenas de dependencias. Se recomienda revisar configuraciones, auditar paquetes y aplicar parches de mitigación de inmediato."
        )
    elif "rust" in lower_t or "python" in lower_t or "go" in lower_t or "typescript" in lower_t or "javascript" in lower_t:
        dialogue = (
            f"¿Qué cambia en el lenguaje? En «{clean_title}», se abordan mejoras en el sistema de tipos, gestión de memoria y primitivas de concurrencia. "
            f"Permite a los ingenieros escribir código más seguro y expresivo con menores sobrecostes en tiempo de ejecución."
        )
    else:
        # Contextual synthesis from body if available
        first_sentence = clean_body.split(".")[0] if clean_body and len(clean_body) > 40 else ""
        if first_sentence and len(first_sentence) < 160:
            dialogue = (
                f"¿De qué se trata y qué aporta? {first_sentence.strip()}. «{clean_title}» surge como una solución moderna pensada "
                f"para simplificar la arquitectura, acelerar flujos de trabajo de ingeniería y elevar los estándares de la industria técnica."
            )
        else:
            dialogue = (
                f"¿Por qué seguir de cerca esta noticia? «{clean_title}» marca una evolución técnica relevante en su categoría. "
                f"Facilita a los desarrolladores herramientas más modernas, patrones de arquitectura escalables y soluciones directas a desafíos de producción."
            )

    return dialogue

def extract_key_highlights(title: str, content: str = "", max_bullets: int = 3) -> Tuple[List[str], int]:
    """
    Generate 2 to 3 concise, information-dense bullet points for a 15-second read.
    Returns: (bullets_list, estimated_read_time_seconds)
    """
    cleaned_content = clean_html_and_markdown(content)
    cleaned_title = clean_html_and_markdown(title)

    raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned_content)
    meaningful_sentences = []

    for s in raw_sentences:
        s = s.strip()
        if len(s) < 25 or len(s) > 280:
            continue
        lower_s = s.lower()
        if any(bp in lower_s for bp in ["subscribe", "click here", "sign up", "cookie", "privacy policy", "all rights reserved"]):
            continue
        meaningful_sentences.append(s)

    bullets: List[str] = []

    # Highlight 1: The Core Event / Title
    if ":" in cleaned_title or " - " in cleaned_title:
        bullets.append(cleaned_title)
    else:
        bullets.append(f"Hito principal: {cleaned_title}")

    # Prioritize technical signal keywords
    signal_keywords = [
        "introduces", "features", "release", "support", "performance", "improves",
        "faster", "added", "breaking", "api", "model", "architecture", "security",
        "novedad", "soporte", "rendimiento", "optimización", "nueva versión", "nuevo",
        "permite", "integra", "corrige", "vulnerabilidad", "diseñado para", "benchmark"
    ]

    scored_sentences = []
    for s in meaningful_sentences:
        score = sum(1 for kw in signal_keywords if kw in s.lower())
        if re.search(r'\b\d+(\.\d+)?%?\b', s):
            score += 1
        scored_sentences.append((score, s))

    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    for _, s in scored_sentences:
        if len(bullets) >= max_bullets:
            break
        if not any(w in s for w in bullets[0].split()[:3] if len(w) > 4):
            bullets.append(s)

    # Fallbacks
    if len(bullets) < 2:
        if cleaned_content and len(cleaned_content) > 30 and cleaned_content not in bullets:
            bullets.append(cleaned_content[:180].rstrip() + ("..." if len(cleaned_content) > 180 else ""))
        else:
            bullets.append("Novedades técnicas y mejoras de arquitectura detalladas en la fuente original.")

    if len(bullets) < 3 and len(meaningful_sentences) > 0:
        for s in meaningful_sentences:
            if s not in bullets:
                bullets.append(s)
                break

    bullets = bullets[:max_bullets]
    total_words = sum(len(b.split()) for b in bullets)
    read_time = max(10, min(30, int(total_words / 3.5)))

    return bullets, read_time

def process_news_detail(title: str, content: str = "", topic: str = "") -> Dict[str, Any]:
    """
    Extracts complete synthesized detail: dialogue + key highlights + read time.
    """
    dialogue = generate_explanatory_dialogue(title, content, topic)
    bullets, read_time = extract_key_highlights(title, content)
    return {
        "explanatory_dialogue": dialogue,
        "summary_bullets": bullets,
        "read_time_seconds": read_time
    }

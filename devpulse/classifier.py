"""
DevPulse - Laya Decision Engine (<40ms latency)
Performs fast, typed decisions over incoming news items:
1. Relevance (noul / Yes-No)
2. Topic Classification (choice)
3. Impact Calibration (score 1 - 100)
"""
import time
import logging
import re
from typing import Dict, Any, Tuple
from devpulse.config import TOPICS

logger = logging.getLogger("devpulse.classifier")

# Questions Schema for Laya Router
LAYA_QUESTIONS = {
    "is_relevant": {
        "type": "noul",
        "instructions": "¿El texto trata sobre novedades técnicas o informáticas reales, desarrollo de software, lenguajes o infraestructura?",
    },
    "topic": {
        "type": "choice",
        "instructions": "Clasifica la noticia técnica en el tópico más representativo:",
        "criteria": {
            "Modelos IA & Machine Learning": "Inteligencia artificial, LLMs, redes neuronales, modelos generativos, visión por computadora, deep learning, PyTorch, Hugging Face, OpenAI, embeddings.",
            "Nuevas Herramientas & Developer Tools": "Herramientas para desarrolladores, terminal, CLI, editores, IDEs, debugging, package managers, profiling, monitoreo local.",
            "Frameworks & Librerías": "Frameworks web y aplicaciones (React, Vue, Next.js, FastAPI, Svelte, Django), librerías UI, bibliotecas backend y SDKs.",
            "Funciones de Lenguajes (JS, Python, Rust, etc.)": "Novedades y versiones de lenguajes de programación (Rust, Python, Go, TypeScript, C++, Zig), PEPs, compiladores, sintaxis y runtimes.",
            "DevOps, Cloud & Seguridad": "Cloud computing, Kubernetes, Docker, CI/CD, AWS, Azure, GCP, Terraform, seguridad informática, vulnerabilidades, networking, CDN."
        }
    },
    "impact": {
        "type": "score",
        "instructions": "Evalúa el impacto técnico y relevancia de la noticia en la industria del software",
        "criteria": [
            "Minor patch, typo fix, routine dependency bump, or niche trivial tool",
            "Useful update or small utility, incremental feature in a library",
            "Solid new release, notable open source tool, significant framework improvement",
            "Major release of a core technology, breakthrough library, critical security issue",
            "Industry-defining breakthrough, new language standard, revolutionary AI model, monumental paradigm shift"
        ]
    }
}

class LayaClassifier:
    """
    High-speed classifier wrapping Laya's non-autoregressive Router with
    an ultra-fast heuristic fallback if weights are downloading or offline.
    """
    def __init__(self):
        self._router = None
        self._initialized = False
        self._init_laya()

    def _init_laya(self):
        try:
            from laya import Router
            logger.info("Initializing Laya Router...")
            # Router initialization
            self._router = Router(default="english")
            self._initialized = True
            logger.info("Laya Router initialized successfully.")
        except Exception as e:
            logger.warning(f"Laya Router not ready or offline: {e}. Fallback engine active.")
            self._router = None
            self._initialized = False

    def classify(self, title: str, content: str = "") -> Dict[str, Any]:
        """
        Classifies an article returning:
        {
            "is_relevant": bool,
            "topic": str,
            "importance_score": int,
            "latency_ms": float,
            "engine": str
        }
        """
        start_time = time.perf_counter()
        full_text = f"{title}\n{content[:1000]}".strip()

        # Try Laya Router first
        if self._router:
            try:
                laya_result = self._router.predict(full_text, LAYA_QUESTIONS)
                answers = laya_result.get("answers", {})

                # Extract Relevance (noul)
                noul_val = answers.get("is_relevant", {}).get("noul", 0.8)
                is_relevant = bool(noul_val >= 0.45)

                # Extract Topic (choice)
                topic = answers.get("topic", {}).get("choice")
                if topic not in TOPICS:
                    topic = self._heuristic_topic(full_text)

                # Extract Impact (score 1 - 100)
                score_val = answers.get("impact", {}).get("score")
                if score_val is not None:
                    # Laya returns float index on ordered scale (0 to 4)
                    norm_score = max(0.0, min(4.0, float(score_val)))
                    importance_score = max(10, min(100, int((norm_score / 4.0) * 85 + 15)))
                else:
                    importance_score = self._heuristic_impact(title, content)

                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "is_relevant": is_relevant,
                    "topic": topic,
                    "importance_score": importance_score,
                    "latency_ms": elapsed_ms,
                    "engine": "laya"
                }
            except Exception as e:
                logger.debug(f"Laya predict fallback triggered: {e}")

        # High-precision fallback engine
        return self._fallback_classify(title, content, start_time)

    def _fallback_classify(self, title: str, content: str, start_time: float) -> Dict[str, Any]:
        text = f"{title} {content}".lower()
        
        # 1. Relevance decision
        non_tech_patterns = [
            r"\b(politics|celebrity|recipe|horoscope|fashion|real estate|lottery|sports score)\b"
        ]
        is_relevant = not any(re.search(pat, text) for pat in non_tech_patterns)

        # 2. Topic classification
        topic = self._heuristic_topic(text)

        # 3. Impact scoring (1 - 100)
        importance_score = self._heuristic_impact(title, content)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "is_relevant": is_relevant,
            "topic": topic,
            "importance_score": importance_score,
            "latency_ms": elapsed_ms,
            "engine": "laya-rules"
        }

    def _heuristic_topic(self, text: str) -> str:
        text = text.lower()

        scores = {
            "Modelos IA & Machine Learning": 0,
            "Nuevas Herramientas & Developer Tools": 0,
            "Frameworks & Librerías": 0,
            "Funciones de Lenguajes (JS, Python, Rust, etc.)": 0,
            "DevOps, Cloud & Seguridad": 0
        }

        # AI & ML
        ai_terms = ["llm", "gpt", "gemini", "claude", "transformer", "neural", "pytorch", "deepseek", 
                    "machine learning", "weights", "agentic", "ai model", "diffusion", "rag", "inference", "benchmark"]
        for term in ai_terms:
            if term in text:
                scores["Modelos IA & Machine Learning"] += 3

        # Languages
        lang_terms = ["rust", "python 3", "golang", "go 1.", "c++", "typescript", "javascript", "zig", "compiler",
                      "pep ", "rfc", "syntax", "v8 engine", "memory safety", "garbage collector", "types"]
        for term in lang_terms:
            if term in text:
                scores["Funciones de Lenguajes (JS, Python, Rust, etc.)"] += 3

        # Frameworks & Libraries
        fw_terms = ["react", "vue", "next.js", "svelte", "fastapi", "django", "express", "tailwind",
                    "angular", "ui library", "frontend framework", "component", "state management", "hooks"]
        for term in fw_terms:
            if term in text:
                scores["Frameworks & Librerías"] += 3

        # DevOps & Cloud
        cloud_terms = ["kubernetes", "docker", "k8s", "aws", "gcp", "azure", "ci/cd", "terraform",
                       "vulnerability", "cve-", "security exploit", "tls", "dns", "microservices", "cloud"]
        for term in cloud_terms:
            if term in text:
                scores["DevOps, Cloud & Seguridad"] += 3

        # Dev Tools
        tool_terms = ["cli", "terminal", "ide", "vscode", "debugger", "profiler", "git", "package manager",
                      "bun", "uv", "deno", "vite", "webpack", "linter", "formatter", "developer tool"]
        for term in tool_terms:
            if term in text:
                scores["Nuevas Herramientas & Developer Tools"] += 3

        best_topic = max(scores.items(), key=lambda x: x[1])
        if best_topic[1] > 0:
            return best_topic[0]

        return "Nuevas Herramientas & Developer Tools"

    def _heuristic_impact(self, title: str, content: str) -> int:
        title_lower = title.lower()
        score = 50  # Baseline solid technical news

        # High impact signals (+20 to +40)
        high_signals = [
            "breaking", "vulnerability", "critical", "0-day", "major release", "v1.0", "v2.0", "v3.0", "v4.0",
            "revolutionary", "paradigm", "standard", "official release", "disruptive", "benchmark", "outperforms",
            "autonomous", "new language", "revolutionizes", "security advisory"
        ]
        for s in high_signals:
            if s in title_lower:
                score += 15

        # Check for major version pattern (e.g., "19.0", "3.13", "v2.0")
        if re.search(r'\b(v?\d+\.0(\.0)?)\b', title_lower):
            score += 12

        # Low impact signals (-15 to -30)
        low_signals = [
            "patch", "typo", "minor", "chore", "bump", "dependency update", "docs", "fix spelling",
            "readme", "cleanup", "refactor test"
        ]
        for s in low_signals:
            if s in title_lower:
                score -= 15

        # Check for small patch version (e.g. 1.2.34)
        if re.search(r'\bv?\d+\.\d+\.\d{2,}\b', title_lower):
            score -= 10

        return max(15, min(98, score))

# Global instance for reuse
classifier_instance = LayaClassifier()

def get_classifier() -> LayaClassifier:
    return classifier_instance

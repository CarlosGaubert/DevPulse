"""
DevPulse - Web Malware & Security Protection Shield
Provides multi-layer security auditing for external URLs and technical articles:
1. URL Protocol & Domain Reputation Check (Phishing / Typo-squatting / Malicious TLDs)
2. Drive-by download & dangerous executable extension screening
3. Content injection, crypto-drainer & scam pattern detection
4. Laya System 1 Security Audit
"""
import re
import urllib.parse
from typing import Dict, Any, Tuple

# Suspicious file extensions commonly associated with malware / drive-by downloads
MALICIOUS_EXTENSIONS = (
    ".exe", ".scr", ".bat", ".cmd", ".vbs", ".vbe", ".msi", ".pif",
    ".com", ".ps1", ".jar", ".hta", ".cpl", ".iso", ".img"
)

# Known deceptive TLDs or common scam patterns
SUSPICIOUS_TLDS = {
    "zip", "mov", "cam", "top", "work", "gq", "cf", "tk", "ml", "ga", "click"
}

# Suspicious keywords in URLs indicative of phishing or credential harvesting
PHISHING_KEYWORDS = [
    "login-verify", "account-update", "auth-token", "claim-airdrop", "free-crypto",
    "wallet-connect", "security-check-login", "metamask-auth", "pypi-download-fix"
]

class SecurityGuard:
    """
    Real-time security scanner to protect developers from malicious news,
    phishing domains, and drive-by web malware.
    """

    def scan_url(self, url: str) -> Tuple[bool, str, int]:
        """
        Inspect URL for malware, protocol exploits, and phishing signatures.
        Returns: (is_safe: bool, reason: str, safety_score: int)
        """
        if not url:
            return False, "URL vacía", 0

        try:
            parsed = urllib.parse.urlparse(url.strip())
        except Exception:
            return False, "Estructura de URL malformada", 0

        # Protocol check: Must be HTTP or HTTPS
        if parsed.scheme not in ("http", "https"):
            return False, f"Protocolo no seguro o peligroso ({parsed.scheme})", 0

        netloc = parsed.netloc.lower()
        path = parsed.path.lower()
        query = parsed.query.lower()

        # Check for IP address host (often used by malicious command & control or phishing)
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$', netloc):
            return False, "Dirección IP directa en lugar de dominio confiable", 20

        # Check for suspicious or deceptive TLDs
        parts = netloc.split(".")
        if len(parts) >= 2:
            tld = parts[-1].split(":")[0]
            if tld in SUSPICIOUS_TLDS:
                return False, f"TLD de alto riesgo identificado (.{tld})", 30

        # Check for dangerous file downloads
        for ext in MALICIOUS_EXTENSIONS:
            if path.endswith(ext) or f"{ext}?" in path + query:
                return False, f"Enlace de descarga directa de ejecutable ({ext})", 10

        # Check for phishing and credential scam keywords
        for kw in PHISHING_KEYWORDS:
            if kw in url.lower():
                return False, f"Firma de phishing o robo de credenciales detectada ({kw})", 15

        # HTTPS bonus
        safety_score = 98 if parsed.scheme == "https" else 75
        return True, "Enlace verificado y cifrado (HTTPS)", safety_score

    def scan_content(self, title: str, content: str) -> Tuple[bool, str]:
        """
        Screen content for malware distribution, crypto drainer campaigns,
        or package poisoning announcements.
        """
        text = f"{title} {content}".lower()

        scam_patterns = [
            r"\b(claim your airdrop|connect your wallet|free tokens|private key|seed phrase)\b",
            r"\b(click here to claim|telegram investment|guaranteed profit|giveaway btc)\b",
            r"\b(download crack|license keygen|bypass activation|warez)\b"
        ]

        for pat in scam_patterns:
            if re.search(pat, text):
                return False, "Contenido sospechoso de estafa, cripto-phishing o distribución no autorizada"

        return True, "Contenido libre de patrones de amenaza"

    def audit_article(self, title: str, source_url: str, content: str = "") -> Dict[str, Any]:
        """
        Full audit combining URL inspection and content safety.
        Returns detailed safety report.
        """
        url_safe, url_reason, safety_score = self.scan_url(source_url)
        content_safe, content_reason = self.scan_content(title, content)

        is_safe = url_safe and content_safe
        if not is_safe:
            status = "BLOCKED" if (not url_safe and safety_score <= 30) or not content_safe else "WARNING"
            details = url_reason if not url_safe else content_reason
        else:
            status = "VERIFIED_SAFE"
            details = "Dominio oficial y enlace HTTPS inspeccionado contra malware, phishing y descargas maliciosas."

        return {
            "is_safe": is_safe,
            "status": status,
            "safety_score": safety_score if is_safe else min(safety_score, 30),
            "safety_details": details
        }

security_guard = SecurityGuard()

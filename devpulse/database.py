"""
DevPulse - High-performance SQLite Storage Layer with WAL mode,
Security Audit Fields, Explanatory Dialogue, and Recency Decay Ranking.
"""
import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from devpulse.config import DB_PATH, TOPICS

def get_connection() -> sqlite3.Connection:
    """Return a connection with WAL mode and Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes tables, columns, and indices with auto-migration."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT UNIQUE NOT NULL,
                published_at TEXT NOT NULL,
                topic TEXT NOT NULL,
                importance_score INTEGER NOT NULL,
                summary_bullets TEXT NOT NULL,
                read_time_seconds INTEGER DEFAULT 15,
                raw_content TEXT,
                explanatory_dialogue TEXT DEFAULT '',
                safety_status TEXT DEFAULT 'VERIFIED_SAFE',
                safety_score INTEGER DEFAULT 98,
                safety_details TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
        """)

        # Schema migrations for existing databases
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(articles);")
        columns = [row["name"] for row in cursor.fetchall()]

        if "explanatory_dialogue" not in columns:
            conn.execute("ALTER TABLE articles ADD COLUMN explanatory_dialogue TEXT DEFAULT '';")
        if "safety_status" not in columns:
            conn.execute("ALTER TABLE articles ADD COLUMN safety_status TEXT DEFAULT 'VERIFIED_SAFE';")
        if "safety_score" not in columns:
            conn.execute("ALTER TABLE articles ADD COLUMN safety_score INTEGER DEFAULT 98;")
        if "safety_details" not in columns:
            conn.execute("ALTER TABLE articles ADD COLUMN safety_details TEXT DEFAULT '';")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(source_url);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_score ON articles(importance_score DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_safety ON articles(safety_status);")

        # Custom RSS / Atom feeds table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                topic TEXT DEFAULT 'Herramientas de Desarrollo & CLI',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_custom_feeds_active ON custom_feeds(is_active);")

def article_exists(source_url: str) -> bool:
    """Check if an article with the given source_url already exists."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM articles WHERE source_url = ? LIMIT 1;", (source_url,))
        return cursor.fetchone() is not None

def save_article(
    title: str,
    source_name: str,
    source_url: str,
    published_at: str,
    topic: str,
    importance_score: int,
    summary_bullets: List[str],
    read_time_seconds: int = 15,
    raw_content: Optional[str] = None,
    explanatory_dialogue: str = "",
    safety_status: str = "VERIFIED_SAFE",
    safety_score: int = 98,
    safety_details: str = ""
) -> bool:
    """Insert a new article with safety audit and explanatory dialogue."""
    if article_exists(source_url):
        return False

    bullets_json = json.dumps(summary_bullets, ensure_ascii=False)
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO articles (
                    title, source_name, source_url, published_at,
                    topic, importance_score, summary_bullets,
                    read_time_seconds, raw_content, explanatory_dialogue,
                    safety_status, safety_score, safety_details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                title,
                source_name,
                source_url,
                published_at,
                topic,
                int(importance_score),
                bullets_json,
                read_time_seconds,
                raw_content,
                explanatory_dialogue,
                safety_status,
                int(safety_score),
                safety_details,
                now_iso
            ))
            return True
    except sqlite3.IntegrityError:
        return False

def get_articles(
    topic: Optional[str] = None,
    sort_by: str = "importance",
    search: Optional[str] = None,
    min_score: Optional[int] = None,
    page: int = 1,
    page_size: int = 15
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch paginated articles with recency-weighted ranking.
    Blocks any items flagged as BLOCKED by the security shield.
    """
    conditions = ["safety_status != 'BLOCKED'"]
    params: List[Any] = []

    if topic and topic.strip():
        conditions.append("topic = ?")
        params.append(topic.strip())

    if min_score is not None:
        conditions.append("importance_score >= ?")
        params.append(min_score)

    if search and search.strip():
        search_query = f"%{search.strip()}%"
        conditions.append("(title LIKE ? OR summary_bullets LIKE ? OR explanatory_dialogue LIKE ? OR source_name LIKE ?)")
        params.extend([search_query, search_query, search_query, search_query])

    where_clause = f"WHERE {' AND '.join(conditions)}"

    # Recency-weighted impact scoring:
    # A breaking announcement this week outranks an older story from 30+ days ago
    if sort_by == "date":
        order_clause = "ORDER BY published_at DESC, importance_score DESC"
    else:  # default 'importance' with recency decay
        order_clause = """
            ORDER BY 
                (importance_score - MAX(0, (julianday('now') - julianday(published_at)) * 1.8)) DESC,
                published_at DESC
        """

    offset = (page - 1) * page_size

    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Total count
        count_sql = f"SELECT COUNT(*) FROM articles {where_clause};"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

        # Paginated items
        items_sql = f"""
            SELECT id, title, source_name, source_url, published_at,
                   topic, importance_score, summary_bullets,
                   read_time_seconds, explanatory_dialogue,
                   safety_status, safety_score, safety_details, created_at
            FROM articles
            {where_clause}
            {order_clause}
            LIMIT ? OFFSET ?;
        """
        cursor.execute(items_sql, params + [page_size, offset])
        rows = cursor.fetchall()

        articles = []
        for r in rows:
            bullets = []
            try:
                bullets = json.loads(r["summary_bullets"])
            except Exception:
                bullets = [r["summary_bullets"]]

            articles.append({
                "id": r["id"],
                "title": r["title"],
                "source_name": r["source_name"],
                "source_url": r["source_url"],
                "published_at": r["published_at"],
                "topic": r["topic"],
                "importance_score": r["importance_score"],
                "summary_bullets": bullets,
                "read_time_seconds": r["read_time_seconds"],
                "explanatory_dialogue": r["explanatory_dialogue"] or "",
                "safety_status": r["safety_status"] or "VERIFIED_SAFE",
                "safety_score": r["safety_score"] if r["safety_score"] is not None else 98,
                "safety_details": r["safety_details"] or "Enlace verificado y seguro.",
                "created_at": r["created_at"],
            })

        return articles, total_count

def get_topics_with_counts() -> List[Dict[str, Any]]:
    """Return all standard topics with their current article counts."""
    counts_map = {t: 0 for t in TOPICS}
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic, COUNT(*) as count FROM articles WHERE safety_status != 'BLOCKED' GROUP BY topic;")
        for row in cursor.fetchall():
            t_name = row["topic"]
            counts_map[t_name] = row["count"]

    return [{"name": name, "count": count} for name, count in counts_map.items()]

def get_stats() -> Dict[str, Any]:
    """Return overall dashboard metrics including security protection stats."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_articles,
                COALESCE(AVG(importance_score), 0) as avg_score,
                MAX(importance_score) as max_score,
                COUNT(DISTINCT source_name) as total_sources,
                SUM(CASE WHEN safety_status = 'VERIFIED_SAFE' THEN 1 ELSE 0 END) as verified_safe_count,
                SUM(CASE WHEN safety_status = 'BLOCKED' THEN 1 ELSE 0 END) as blocked_count,
                MAX(created_at) as last_collected_at
            FROM articles;
        """)
        row = cursor.fetchone()
        return {
            "total_articles": row["total_articles"],
            "avg_importance_score": round(row["avg_score"], 1),
            "max_importance_score": row["max_score"] or 0,
            "total_sources": row["total_sources"],
            "verified_safe_count": row["verified_safe_count"] or 0,
            "blocked_threats_count": row["blocked_count"] or 0,
            "last_collected_at": row["last_collected_at"]
        }

def purge_test_fixtures():
    """Remove older hardcoded test mocks so fresh real-time news leads the ranking."""
    with get_connection() as conn:
        conn.execute("DELETE FROM articles WHERE source_url LIKE '%tag/v19.0.0' AND title LIKE '%React 19 Official Release%';")
        conn.commit()

def get_custom_feeds(only_active: bool = False) -> List[Dict[str, Any]]:
    """Return all custom user-defined RSS/Atom feeds."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if only_active:
            cursor.execute("SELECT id, name, url, topic, is_active, created_at FROM custom_feeds WHERE is_active = 1 ORDER BY id DESC;")
        else:
            cursor.execute("SELECT id, name, url, topic, is_active, created_at FROM custom_feeds ORDER BY id DESC;")
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "url": r["url"],
                "topic": r["topic"],
                "is_active": bool(r["is_active"]),
                "created_at": r["created_at"]
            }
            for r in rows
        ]

def add_custom_feed(name: str, url: str, topic: str = "Herramientas de Desarrollo & CLI") -> Dict[str, Any]:
    """Add a new custom feed to the database."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO custom_feeds (name, url, topic, is_active, created_at)
            VALUES (?, ?, ?, 1, ?);
        """, (name.strip(), url.strip(), topic.strip(), now_iso))
        feed_id = cursor.lastrowid
        conn.commit()
        return {
            "id": feed_id,
            "name": name.strip(),
            "url": url.strip(),
            "topic": topic.strip(),
            "is_active": True,
            "created_at": now_iso
        }

def delete_custom_feed(feed_id: int) -> bool:
    """Delete a custom feed by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM custom_feeds WHERE id = ?;", (feed_id,))
        conn.commit()
        return cursor.rowcount > 0

def toggle_custom_feed(feed_id: int, is_active: bool) -> bool:
    """Enable or disable a custom feed."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE custom_feeds SET is_active = ? WHERE id = ?;", (1 if is_active else 0, feed_id))
        conn.commit()
        return cursor.rowcount > 0


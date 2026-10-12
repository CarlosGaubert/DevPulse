"""
DevPulse - Re-synthesize Existing Database Articles
Upgrades dialogues and key highlights across all existing articles to high-signal quality.
"""
import sqlite3
import logging
from devpulse.config import DB_PATH
from devpulse.summarizer import process_news_detail
from devpulse.database import update_article_synthesis, get_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("devpulse.migration")

def resynthesize_all_articles():
    logger.info(f"Connecting to database at {DB_PATH}...")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, raw_content, topic FROM articles ORDER BY id ASC;")
        rows = cursor.fetchall()
        logger.info(f"Found {len(rows)} articles to re-synthesize.")

        updated_count = 0
        for r in rows:
            art_id = r["id"]
            title = r["title"]
            content = r["raw_content"] or ""
            topic = r["topic"] or ""

            detail = process_news_detail(title, content, topic)
            update_article_synthesis(
                article_id=art_id,
                explanatory_dialogue=detail["explanatory_dialogue"],
                summary_bullets=detail["summary_bullets"],
                read_time_seconds=detail["read_time_seconds"]
            )
            updated_count += 1
            if updated_count % 25 == 0:
                logger.info(f"Processed {updated_count}/{len(rows)} articles...")

        # Purge bad/identical cached entries
        cursor.execute("""
            DELETE FROM translations_cache 
            WHERE (source_text = translated_text AND target_lang != 'en' AND LENGTH(source_text) > 12)
               OR translated_text LIKE '%óxido%'
               OR translated_text LIKE '%Liberación de prueba%';
        """)
        conn.commit()
        logger.info(f"Successfully re-synthesized all {updated_count} articles and cleaned cache.")

if __name__ == "__main__":
    resynthesize_all_articles()

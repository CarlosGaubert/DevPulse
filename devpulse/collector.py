"""
DevPulse - High-speed Asynchronous Collector with Recency Enforcement & Security Shield
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import httpx
import feedparser
from dateutil import parser as date_parser

from devpulse.config import (
    HN_MIN_POINTS, HN_LIMIT, GITHUB_REPOS, RSS_FEEDS, MAX_AGE_DAYS
)
from devpulse.database import article_exists, save_article, get_custom_feeds
from devpulse.classifier import get_classifier
from devpulse.summarizer import process_news_detail
from devpulse.security_guard import security_guard

logger = logging.getLogger("devpulse.collector")

HEADERS = {
    "User-Agent": "DevPulse-TechRadar/2.0 (+https://github.com/devpulse)",
    "Accept": "application/json, application/xml, text/xml, */*"
}

class CollectorService:
    def __init__(self, concurrency_limit: int = 6):
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.classifier = get_classifier()

    def _is_recent(self, iso_date_str: str) -> bool:
        """Enforce recency: discard stale items older than MAX_AGE_DAYS."""
        try:
            dt = date_parser.parse(iso_date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
            return dt >= cutoff
        except Exception:
            return True

    async def fetch_hacker_news(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch current high-signal tech stories from Algolia HN API (both trending & latest)."""
        urls = [
            # Top trending stories with points
            f"https://hn.algolia.com/api/v1/search?tags=story&numericFilters=points>={HN_MIN_POINTS}&hitsPerPage={HN_LIMIT}",
            # Immediate latest stories
            f"https://hn.algolia.com/api/v1/search_by_date?tags=story&numericFilters=points>={HN_MIN_POINTS}&hitsPerPage={HN_LIMIT}"
        ]
        stories = []
        for url in urls:
            try:
                async with self.semaphore:
                    resp = await client.get(url, timeout=12.0)
                    if resp.status_code != 200:
                        continue
                    data = resp.json()

                for hit in data.get("hits", []):
                    story_url = hit.get("url")
                    title = hit.get("title")
                    if not story_url or not title:
                        continue

                    created_at = hit.get("created_at") or datetime.now(timezone.utc).isoformat()
                    if not self._is_recent(created_at):
                        continue

                    points = hit.get("points", 0)
                    comments = hit.get("num_comments", 0)

                    stories.append({
                        "title": title.strip(),
                        "source_name": "Hacker News",
                        "source_url": story_url.strip(),
                        "published_at": created_at,
                        "content": f"Puntos en Hacker News: {points} | Comentarios: {comments}",
                    })
            except Exception as e:
                logger.error(f"Error fetching Hacker News from {url}: {e}")
        return stories

    async def fetch_github_release(self, client: httpx.AsyncClient, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch latest release for a specific GitHub repository, enforcing recency."""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            async with self.semaphore:
                resp = await client.get(url, timeout=10.0)
                if resp.status_code != 200:
                    return None
                data = resp.json()

            published_at = data.get("published_at") or datetime.now(timezone.utc).isoformat()
            # If release is older than MAX_AGE_DAYS, skip so stale releases don't occupy frontpage
            if not self._is_recent(published_at):
                return None

            tag = data.get("tag_name", "")
            name = data.get("name") or tag
            body = data.get("body", "") or ""
            html_url = data.get("html_url", f"https://github.com/{repo}/releases")

            repo_name = repo.split("/")[-1].capitalize()
            title = f"{repo_name} Release {name}"

            return {
                "title": title,
                "source_name": f"GitHub ({repo})",
                "source_url": html_url,
                "published_at": published_at,
                "content": body[:2000],
            }
        except Exception as e:
            logger.debug(f"Error fetching GitHub release for {repo}: {e}")
            return None

    async def fetch_github_releases(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch latest releases concurrently."""
        tasks = [self.fetch_github_release(client, repo) for repo in GITHUB_REPOS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid = []
        for r in results:
            if isinstance(r, dict) and r:
                valid.append(r)
        return valid

    async def fetch_rss_feed(self, client: httpx.AsyncClient, feed_info: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch and parse a single curated RSS/Atom feed with recency check."""
        name = feed_info["name"]
        url = feed_info["url"]
        items = []
        try:
            async with self.semaphore:
                resp = await client.get(url, timeout=12.0)
                if resp.status_code != 200:
                    return items
                feed_data = feedparser.parse(resp.text)

            for entry in feed_data.entries[:12]:
                link = entry.get("link")
                title = entry.get("title")
                if not link or not title:
                    continue

                pub_date = entry.get("published") or entry.get("updated")
                if pub_date:
                    try:
                        dt = date_parser.parse(pub_date)
                        pub_iso = dt.isoformat()
                    except Exception:
                        pub_iso = datetime.now(timezone.utc).isoformat()
                else:
                    pub_iso = datetime.now(timezone.utc).isoformat()

                # Discard stale items
                if not self._is_recent(pub_iso):
                    continue

                summary = entry.get("summary") or entry.get("description") or ""

                items.append({
                    "title": title.strip(),
                    "source_name": name,
                    "source_url": link.strip(),
                    "published_at": pub_iso,
                    "content": summary[:2500],
                })
        except Exception as e:
            logger.error(f"Error fetching RSS feed {name}: {e}")
        return items

    async def fetch_rss_feeds(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch from all default and custom user-defined RSS feeds concurrently."""
        all_feeds = list(RSS_FEEDS)
        try:
            custom = get_custom_feeds(only_active=True)
            for cf in custom:
                all_feeds.append({
                    "name": cf["name"],
                    "url": cf["url"],
                    "default_topic": cf.get("topic", "Herramientas de Desarrollo & CLI")
                })
        except Exception as e:
            logger.debug(f"Error loading custom feeds: {e}")

        tasks = [self.fetch_rss_feed(client, feed) for feed in all_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        items = []
        for r in results:
            if isinstance(r, list):
                items.extend(r)
        return items

    async def run_pipeline(self) -> Dict[str, Any]:
        """
        Runs the full ingestion, security screening, Laya decision,
        explanatory dialogue generation, and storage pipeline.
        """
        start_time = datetime.now(timezone.utc)
        logger.info("Executing autonomous pipeline with security auditing...")

        raw_articles: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
            hn_task = self.fetch_hacker_news(client)
            gh_task = self.fetch_github_releases(client)
            rss_task = self.fetch_rss_feeds(client)

            results = await asyncio.gather(hn_task, gh_task, rss_task, return_exceptions=True)

            for res in results:
                if isinstance(res, list):
                    raw_articles.extend(res)

        logger.info(f"Gathered {len(raw_articles)} raw candidate articles. Screening and processing...")

        saved_count = 0
        skipped_duplicates = 0
        skipped_irrelevant = 0
        blocked_threats = 0

        for item in raw_articles:
            url = item["source_url"]
            if article_exists(url):
                skipped_duplicates += 1
                continue

            title = item["title"]
            content = item.get("content", "")

            # 1. Security & Malware Shield Audit
            security_report = security_guard.audit_article(title, url, content)
            if security_report["status"] == "BLOCKED":
                logger.warning(f"Security Shield BLOCKED suspicious item: {title} ({url})")
                blocked_threats += 1
                continue

            # 2. Laya Classification (<40ms decision)
            classification = self.classifier.classify(title, content)
            if not classification["is_relevant"]:
                skipped_irrelevant += 1
                continue

            topic = classification["topic"]
            score = classification["importance_score"]

            # 3. Explanatory Dialogue & Key Highlights
            detail = process_news_detail(title, content, topic)

            # 4. Save to Database
            saved = save_article(
                title=title,
                source_name=item["source_name"],
                source_url=url,
                published_at=item["published_at"],
                topic=topic,
                importance_score=score,
                summary_bullets=detail["summary_bullets"],
                read_time_seconds=detail["read_time_seconds"],
                raw_content=content,
                explanatory_dialogue=detail["explanatory_dialogue"],
                safety_status=security_report["status"],
                safety_score=security_report["safety_score"],
                safety_details=security_report["safety_details"]
            )

            if saved:
                saved_count += 1

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Pipeline complete in {duration:.2f}s: {saved_count} saved, "
            f"{skipped_duplicates} duplicates, {blocked_threats} blocked threats, "
            f"{skipped_irrelevant} filtered out."
        )

        return {
            "total_raw": len(raw_articles),
            "saved": saved_count,
            "skipped_duplicates": skipped_duplicates,
            "blocked_threats": blocked_threats,
            "skipped_irrelevant": skipped_irrelevant,
            "duration_seconds": round(duration, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

collector_service = CollectorService()

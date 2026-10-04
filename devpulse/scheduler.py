"""
DevPulse - Autonomous Background Scheduler
Runs periodic ingestion without human intervention.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from devpulse.config import SYNC_INTERVAL_MINUTES
from devpulse.collector import collector_service

logger = logging.getLogger("devpulse.scheduler")

class AutonomousScheduler:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._is_running = False
        self._is_syncing = False
        self._last_result: Optional[Dict[str, Any]] = None
        self._last_run_at: Optional[datetime] = None
        self._next_run_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "is_active": self._is_running,
            "is_syncing": self._is_syncing,
            "sync_interval_minutes": SYNC_INTERVAL_MINUTES,
            "last_run_at": self._last_run_at.isoformat() if self._last_run_at else None,
            "next_run_at": self._next_run_at.isoformat() if self._next_run_at else None,
            "last_result": self._last_result,
        }

    async def run_once(self) -> Dict[str, Any]:
        """Trigger an immediate sync safely with mutex locking."""
        if self._lock.locked():
            logger.info("Sync already in progress. Skipping concurrent request.")
            return {"status": "already_running", "message": "Sincronización ya en curso"}

        async with self._lock:
            self._is_syncing = True
            try:
                logger.info("Executing scheduled ingestion...")
                result = await collector_service.run_pipeline()
                self._last_run_at = datetime.now(timezone.utc)
                self._last_result = result
                self._next_run_at = self._last_run_at + timedelta(minutes=SYNC_INTERVAL_MINUTES)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Scheduler execution error: {e}", exc_info=True)
                return {"status": "error", "error": str(e)}
            finally:
                self._is_syncing = False

    async def _loop(self):
        """Infinite autonomous loop running in the background."""
        logger.info(f"Autonomous Scheduler started. Interval: every {SYNC_INTERVAL_MINUTES} minutes.")
        
        # Initial run on startup
        try:
            await self.run_once()
        except Exception as e:
            logger.error(f"Initial run failed: {e}")

        while self._is_running:
            try:
                sleep_seconds = SYNC_INTERVAL_MINUTES * 60
                self._next_run_at = datetime.now(timezone.utc) + timedelta(seconds=sleep_seconds)
                await asyncio.sleep(sleep_seconds)
                if not self._is_running:
                    break
                await self.run_once()
            except asyncio.CancelledError:
                logger.info("Scheduler task cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(60)

    def start(self):
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._loop())

    def stop(self):
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()

scheduler = AutonomousScheduler()

import os
import asyncio
from typing import Optional

# Try importing APScheduler, with graceful native asyncio fallback
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False

from app.database import SessionLocal
from app.services.alert_engine import check_and_create_alerts

scheduler = AsyncIOScheduler() if HAS_APSCHEDULER else None
_asyncio_task: Optional[asyncio.Task] = None
_running: bool = False


def run_scheduled_alert_check():
    """
    Scheduled task executed periodically by APScheduler.
    Instantiates an isolated DB session, executes alert scan, and ensures clean session cleanup.
    """
    print("[APScheduler] Running scheduled crowd density & alert monitoring scan...")
    db = SessionLocal()
    try:
        new_alerts = check_and_create_alerts(db, dedup_window_minutes=15)
        print(f"[APScheduler] Scan complete. Generated {len(new_alerts)} new alert(s).")
    except Exception as e:
        print(f"[APScheduler] Error during alert check execution: {e}")
    finally:
        db.close()


async def _asyncio_loop_worker(interval_minutes: int):
    global _running
    while _running:
        try:
            await asyncio.sleep(interval_minutes * 60)
            if _running:
                run_scheduled_alert_check()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Scheduler] Background loop error: {e}")


def start_scheduler(interval_minutes: int = 5):
    """
    Starts the background monitoring job during FastAPI startup.
    """
    global _running, _asyncio_task
    if os.getenv("ENABLE_SCHEDULER", "true").lower() in ("false", "0"):
        print("[APScheduler] Background scheduler disabled by configuration.")
        return

    _running = True
    if HAS_APSCHEDULER and scheduler:
        if not scheduler.running:
            scheduler.add_job(
                run_scheduled_alert_check,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="metro_crowd_alert_scanner",
                name="Periodic Metro Crowd Alert Scanner",
                replace_existing=True,
            )
            scheduler.start()
            print(f"[APScheduler] Background alert monitoring started (interval: every {interval_minutes} min).")
    else:
        # Fallback to asyncio task
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                _asyncio_task = asyncio.create_task(_asyncio_loop_worker(interval_minutes))
                print(f"[AsyncScheduler] Background monitoring started (interval: every {interval_minutes} min).")
        except Exception:
            pass


def shutdown_scheduler():
    """
    Cleanly shuts down the scheduler during FastAPI server termination.
    """
    global _running, _asyncio_task
    _running = False
    if HAS_APSCHEDULER and scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        print("[APScheduler] Background alert monitoring cleanly shut down.")
    if _asyncio_task and not _asyncio_task.done():
        _asyncio_task.cancel()
        print("[AsyncScheduler] Background monitoring task cleanly cancelled.")

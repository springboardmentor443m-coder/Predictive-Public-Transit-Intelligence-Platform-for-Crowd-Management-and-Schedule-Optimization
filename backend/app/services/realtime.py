import asyncio
import logging
from collections import OrderedDict

from app.services import socketio_state
from app.services.crowd_service import get_all_live_snapshots, log_sensor_event

logger = logging.getLogger(__name__)

_MAX_TRACKED_ALERT_IDS = 1000
_emitted_alert_ids: OrderedDict[str, None] = OrderedDict()


async def broadcast_loop() -> None:
    sio = socketio_state.get_sio()
    if sio is None:
        logger.warning("Socket.IO not initialized; realtime broadcast disabled")
        return
    logger.info("Realtime broadcast loop started (crowd updates + alert engine)")
    while True:
        try:
            from app.core.database import SessionLocal

            def collect():
                db = SessionLocal()
                try:
                    snapshots = get_all_live_snapshots(db)
                    for snap in snapshots:
                        log_sensor_event(snap)

                    from app.services.alert_service import (
                        evaluate_alerts,
                        recent_unbroadcast_alerts,
                    )

                    evaluate_alerts(db)
                    fresh_alerts = recent_unbroadcast_alerts(db)
                    return snapshots, fresh_alerts
                finally:
                    db.close()

            snapshots, fresh_alerts = await asyncio.to_thread(collect)

            for snap in snapshots or []:
                await sio.emit("crowd_update", snap, room=None)

            for alert in fresh_alerts:
                alert_id = alert["id"]
                if alert_id in _emitted_alert_ids:
                    continue
                _emitted_alert_ids[alert_id] = None
                while len(_emitted_alert_ids) > _MAX_TRACKED_ALERT_IDS:
                    _emitted_alert_ids.popitem(last=False)
                await sio.emit("alert", alert, room=None)
        except Exception as e:
            logger.warning(f"broadcast error: {e}")
        await asyncio.sleep(5)

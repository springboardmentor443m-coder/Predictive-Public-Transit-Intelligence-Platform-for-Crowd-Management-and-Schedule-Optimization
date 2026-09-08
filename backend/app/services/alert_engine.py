import logging
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.models.station import Station
from app.models.alert import Alert
from app.services.ml_loader import predict_crowd_density

# Configure logger for structured notification simulation
logger = logging.getLogger("metroflow.alerts")


def simulate_notification(alert: Alert) -> None:
    """
    Simulates sending dispatch notifications (SMS / Push Notification / Control Room Dispatch).
    Uses structured logging to provide clear proof of notification triggers for project reviewers.
    """
    station_display = alert.station_code or "NETWORK"
    log_msg = (
        f"[NOTIFY] Would send {alert.severity.upper()} alert for Station '{station_display}' "
        f"via SMS/Push: \"{alert.message}\" (Logged At: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')})"
    )
    print(log_msg)
    logger.info(log_msg)


def check_and_create_alerts(
    db: Session,
    dedup_window_minutes: int = 15,
) -> List[Alert]:
    """
    Scans all network stations, predicts real-time crowd density, and generates alerts
    for stations experiencing 'high' or 'critical' congestion.
    
    Includes a 15-minute deduplication window to suppress duplicate alerts for ongoing surges.
    """
    now = datetime.now(timezone.utc)
    dedup_threshold = now - timedelta(minutes=dedup_window_minutes)

    # 1. Retrieve all stations in network
    stations = db.execute(select(Station)).scalars().all()
    newly_created_alerts: List[Alert] = []

    for station in stations:
        # Direct in-process prediction call (zero network/HTTP overhead)
        density, label, _ = predict_crowd_density(
            station_code=station.station_code,
            timestamp=now,
            db=db,
        )

        # Only trigger for 'high' or 'critical' platform congestion
        if label in ["high", "critical"]:
            # 2. Check deduplication: Is there an existing unresolved alert within the window?
            existing_alert = db.execute(
                select(Alert).where(
                    and_(
                        Alert.station_code == station.station_code,
                        Alert.resolved == False,
                        Alert.created_at >= dedup_threshold,
                    )
                )
            ).scalars().first()

            if not existing_alert:
                # 3. Create fresh alert
                action_text = (
                    "Platform crowd density is critically high. Recommend dispatching 4 additional trains/hour."
                    if label == "critical"
                    else "Platform crowding is elevated. Recommend increasing dispatch frequency by 2 trains/hour."
                )
                message = f"Station {station.name_en} ({station.line}) crowd density reached {density:.1f}%. {action_text}"

                new_alert = Alert(
                    station_code=station.station_code,
                    alert_type="overcrowding",
                    severity=label,
                    message=message,
                    created_at=now,
                    resolved=False,
                )
                db.add(new_alert)
                newly_created_alerts.append(new_alert)

    # 4. Commit all newly generated alerts and dispatch simulated notifications
    if newly_created_alerts:
        db.commit()
        for alert in newly_created_alerts:
            db.refresh(alert)
            simulate_notification(alert)

    return newly_created_alerts

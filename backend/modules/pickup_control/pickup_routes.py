"""
O20: Pickup Control Routes - Admin API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, timezone

from core.db import db
from core.security import get_current_admin
from modules.pickup_control.pickup_repo import PickupRepo
from modules.pickup_control.pickup_engine import PickupControlEngine

router = APIRouter(prefix="/pickup-control", tags=["Pickup Control"])


@router.get("/risk")
async def get_risk_list(
    days: int = 7, 
    limit: int = 100,
    current_user: dict = Depends(get_current_admin)
):
    """Get list of shipments at pickup point for N+ days"""
    repo = PickupRepo(db)
    items = await repo.list_risk_shipments(min_days=days, limit=limit)
    return {
        "items": items,
        "count": len(items),
        "filter_days": days
    }


@router.get("/kpi")
async def get_pickup_kpi(current_user: dict = Depends(get_current_admin)):
    """Get pickup control KPI stats"""
    repo = PickupRepo(db)
    kpi = await repo.get_pickup_kpi()
    return kpi


@router.post("/run")
async def run_pickup_control(
    body: dict = {},
    current_user: dict = Depends(get_current_admin)
):
    """Manually trigger pickup control processing"""
    limit = int(body.get("limit", 300))
    
    # Get NP service if available
    np_service = None
    try:
        from modules.delivery.np.np_tracking_service import NPTrackingService
        np_service = NPTrackingService(db)
    except ImportError:
        pass
    
    engine = PickupControlEngine(db, np_service=np_service)
    result = await engine.run_once(limit=limit)
    return result


@router.post("/process/{ttn}")
async def process_single_ttn(
    ttn: str,
    current_user: dict = Depends(get_current_admin)
):
    """Process single TTN manually"""
    np_service = None
    try:
        from modules.delivery.np.np_tracking_service import NPTrackingService
        np_service = NPTrackingService(db)
    except ImportError:
        pass
    
    engine = PickupControlEngine(db, np_service=np_service)
    result = await engine.process_single_ttn(ttn)
    return result


@router.post("/mute/{ttn}")
async def mute_ttn(
    ttn: str,
    body: dict = {},
    current_user: dict = Depends(get_current_admin)
):
    """Mute reminders for specific TTN"""
    days = int(body.get("days", 7))
    repo = PickupRepo(db)
    await repo.mute_ttn(ttn, days=days)
    return {"ok": True, "ttn": ttn, "muted_days": days}


@router.post("/send-reminder/{ttn}")
async def send_reminder_now(
    ttn: str,
    body: dict = {},
    current_user: dict = Depends(get_current_admin)
):
    """Force send reminder for TTN right now"""
    level = body.get("level", "D5")
    
    # Find order
    order = await db["orders"].find_one({"shipment.ttn": ttn}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get phone
    delivery = order.get("delivery") or {}
    recipient = delivery.get("recipient") or {}
    phone = recipient.get("phone") or order.get("buyer_phone")
    
    if not phone:
        raise HTTPException(status_code=400, detail="No phone number")
    
    # Import templates
    from modules.pickup_control.pickup_templates import sms_pickup_template
    
    # Get days at point
    days_at = (order.get("shipment") or {}).get("daysAtPoint") or 0
    
    text = sms_pickup_template(level, ttn, order_id=order.get("id"), days=int(days_at))
    dedupe_key = f"pickup_manual:{ttn}:{datetime.now(timezone.utc).isoformat()}"
    
    repo = PickupRepo(db)
    await repo.enqueue_sms(phone, text, dedupe_key, {
        "order_id": order.get("id"),
        "ttn": ttn,
        "level": level,
        "manual": True
    })
    
    return {"ok": True, "ttn": ttn, "phone": phone, "level": level}


@router.get("/order/{order_id}")
async def get_order_pickup_status(
    order_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Get pickup status for specific order"""
    order = await db["orders"].find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    shipment = order.get("shipment") or {}
    reminders = (order.get("reminders") or {}).get("pickup") or {}
    
    return {
        "order_id": order_id,
        "ttn": shipment.get("ttn"),
        "status": order.get("status"),
        "pickup_point_type": shipment.get("pickupPointType"),
        "arrival_at": shipment.get("arrivalAt"),
        "days_at_point": shipment.get("daysAtPoint"),
        "deadline_free_at": shipment.get("deadlineFreeAt"),
        "risk": shipment.get("risk"),
        "reminders": {
            "sent_levels": reminders.get("sentLevels") or [],
            "last_sent_at": reminders.get("lastSentAt"),
            "cooldown_until": reminders.get("cooldownUntil"),
            "muted": reminders.get("muted", False)
        }
    }

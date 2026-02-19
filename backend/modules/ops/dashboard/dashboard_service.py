# O7: Ops Dashboard Service
from motor.motor_asyncio import AsyncIOMotorDatabase
from modules.finance.finance_service import FinanceService
from modules.ops.analytics.shipping_analytics_service import ShippingAnalyticsService

class OpsDashboardService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.finance = FinanceService(db)
        self.shipping = ShippingAnalyticsService(db)
        self.orders = db["orders"]
        self.notifs = db["notification_queue"]
        self.customers = db["customers"]

    async def notifications_stats(self, date_from: str, date_to: str):
        pipeline = [
            {"$match": {"created_at": {"$gte": date_from, "$lte": date_to}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        rows = await self.notifs.aggregate(pipeline).to_list(length=20)
        m = {r["_id"]: r["count"] for r in rows}
        return {
            "sent": m.get("SENT", 0),
            "failed": m.get("FAILED", 0),
            "pending": m.get("PENDING", 0),
        }

    async def orders_funnel(self, date_from: str, date_to: str):
        pipeline = [
            {"$match": {"created_at": {"$gte": date_from, "$lte": date_to}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        rows = await self.orders.aggregate(pipeline).to_list(length=50)
        m = {r["_id"]: r["count"] for r in rows}
        return {
            "NEW": m.get("NEW", 0),
            "AWAITING_PAYMENT": m.get("AWAITING_PAYMENT", 0),
            "PAID": m.get("PAID", 0),
            "PROCESSING": m.get("PROCESSING", 0),
            "SHIPPED": m.get("SHIPPED", 0),
            "DELIVERED": m.get("DELIVERED", 0),
            "CANCELED": m.get("CANCELED", 0),
            "REFUNDED": m.get("REFUNDED", 0),
        }

    async def crm_stats(self):
        pipeline = [
            {"$group": {"_id": "$segment", "count": {"$sum": 1}}}
        ]
        rows = await self.customers.aggregate(pipeline).to_list(20)
        return {r["_id"]: r["count"] for r in rows}

    async def build(self, date_from: str, date_to: str):
        finance_summary = await self.finance.summary(date_from, date_to)
        finance_daily = await self.finance.daily(date_from, date_to)
        shipping_daily = await self.shipping.stats_by_day(date_from, date_to)
        funnel = await self.orders_funnel(date_from, date_to)
        notif = await self.notifications_stats(date_from, date_to)
        crm = await self.crm_stats()

        revenue = float(finance_summary.get("revenue", 0))
        net = float(finance_summary.get("net", 0))
        shipments = sum(int(x.get("ttnCount", 0)) for x in shipping_daily)
        delivered = funnel.get("DELIVERED", 0)

        return {
            "range": {"from": date_from, "to": date_to},
            "kpi": {
                "revenue": revenue,
                "net": net,
                "orders_total": sum(funnel.values()),
                "shipments": shipments,
                "delivered": delivered,
                "notifications": notif,
                "crm_segments": crm,
            },
            "finance": {
                "summary": finance_summary,
                "daily": finance_daily,
            },
            "shipping": {
                "daily": shipping_daily,
            },
            "orders": {
                "funnel": funnel,
            },
        }

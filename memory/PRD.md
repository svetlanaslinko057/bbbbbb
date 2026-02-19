# Y-Store E-Commerce Marketplace - PRD

## Overview
Y-Store is a full-featured e-commerce marketplace with React + FastAPI + MongoDB + Telegram Admin Bot.

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Radix UI, Recharts
- **Backend**: FastAPI, Motor (async MongoDB), Aiogram (Telegram bot)
- **Database**: MongoDB
- **Integrations**: Nova Poshta, RozetkaPay/Fondy, AI Service (Emergent LLM)

## Architecture - Module Structure

```
/app/backend/modules/
├── admin/           # Admin dashboard APIs
├── auth/            # JWT authentication
├── automation/      # Auto-trigger rules (O11)
├── bot/             # Telegram admin bot
│   ├── bot_permissions.py   # O13: Multi-admin roles
│   ├── bot_runtime.py       # O13: Quiet mode
│   └── wizards/             # TTN, Broadcast, Incidents
├── cart/            # Shopping cart
├── content/         # CMS (slides, sections, promotions)
├── crm/             # Customer relationship management
├── delivery/        # Nova Poshta integration + TTN
├── finance/         # Financial ledger, payouts
├── guard/           # O14: Fraud & KPI Guard
├── risk/            # O16: Customer Risk Score
├── timeline/        # O17: Customer Event Timeline
├── analytics_intel/ # O18: Analytics Intelligence
├── pickup_control/  # O20: Pickup Control Engine ✅ NEW
│   ├── pickup_engine.py     # Main processing
│   ├── pickup_policy.py     # Branch/Locker rules
│   ├── pickup_repo.py       # MongoDB operations
│   ├── pickup_templates.py  # SMS/Email templates
│   ├── pickup_routes.py     # Admin API
│   └── pickup_scheduler.py  # Background job (30min)
├── jobs/            # Background schedulers
├── notifications/   # Email/SMS notifications
├── ops/             # Operations dashboard
├── orders/          # Order management + state machine
├── payments/        # Fondy/RozetkaPay webhooks
├── products/        # Product catalog
└── reviews/         # Customer reviews
```

## O20: Pickup Control Engine (Feb 19, 2026)

### Purpose
Reduce returns and unpicked shipments by:
1. Tracking days at Nova Poshta pickup points
2. Sending automated reminders to customers
3. Alerting admins about high-risk shipments
4. Measuring pickup KPIs

### Reminder Schedule

**Branch (7 days free storage):**
- D2: Soft reminder (day 2)
- D5: "Free storage ending soon"
- D7: "Last day / risk of return"

**Locker (5 days before transfer):**
- L1: Soft reminder (day 1)
- L3: "2 days left"
- L5: "Last day, will move to branch"

### Anti-Spam Protection
- Max 1 SMS per 24h per TTN
- Dedupe by level (D2/D5/D7 sent only once)
- Quiet hours (09:00-20:30 Kyiv time)
- User opt-out respected
- Idempotent processing

### API Endpoints
```
GET  /api/v2/admin/pickup-control/kpi           # KPI stats (2+/5+/7+ days)
GET  /api/v2/admin/pickup-control/risk?days=N   # Risk shipments list
POST /api/v2/admin/pickup-control/run           # Trigger processing
POST /api/v2/admin/pickup-control/mute/{ttn}    # Mute TTN reminders
POST /api/v2/admin/pickup-control/send-reminder/{ttn}  # Manual reminder
GET  /api/v2/admin/pickup-control/order/{id}    # Order pickup status
```

### KPI Metrics
- `at_point_2plus`: Shipments 2+ days at point
- `at_point_5plus`: Shipments 5+ days at point
- `at_point_7plus`: Shipments 7+ days (HIGH risk)
- `amount_at_risk`: Total amount at risk (7+ days)

### Admin Alerts
When `at_point_7plus >= 3` OR `amount_at_risk >= 10000 UAH`:
→ Telegram alert with runbook buttons

### Frontend Component
`/frontend/src/components/admin/PickupControl.js`
- KPI cards (2+/5+/7+ days, amount at risk)
- Risk shipments table with filters
- Actions: Send reminder, Mute TTN
- Run engine button

## All O13-O20 Modules Summary

| Module | Status | Description |
|--------|--------|-------------|
| O13 | ✅ | Multi-Admin Roles (OWNER/OPERATOR/VIEWER) |
| O14 | ✅ | Guard Engine (Fraud + KPI alerts) |
| O16 | ✅ | Risk Score Engine (0-100) |
| O17 | ✅ | Customer Timeline |
| O18 | ✅ | Analytics Intelligence |
| O19 | ✅ | Web Admin UI (Analytics Dashboard) |
| O20 | ✅ | Pickup Control Engine |

## Test Results (Feb 19, 2026)
- O13-O18: 15/15 backend tests passed (100%)
- O20: 5/5 pickup control tests passed (100%)
- Total: 20/20 backend tests passed

## Credentials
- Admin: admin@ystore.ua / admin123
- Telegram Bot: 8239151803:AAFBBuflCH5JPWUxwN9UfifCeHgS6cqxYTg
- Nova Poshta: 5cb1e3ebc23e75d737fd57c1e056ecc9

## Known Limitations
- External preview URL (platform issue) - APIs work on localhost

## Backlog

### P0 - Critical
- Fix external URL routing

### P1 - High Priority  
- O20.3: Return Management Engine
- Telegram bot commands (/pickup_risk, /kpi)
- COD-specific aggressive reminders

### P2 - Enhancements
- Predict return probability (rule-based)
- Auto-cancel policy for 30+ days
- Viber notifications channel

## Last Updated
February 19, 2026

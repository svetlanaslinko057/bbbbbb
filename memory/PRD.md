# Y-Store E-Commerce Marketplace - PRD

## Overview
Y-Store is a full-featured e-commerce marketplace built with React + FastAPI + MongoDB + Telegram Admin Bot.

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Radix UI, Recharts
- **Backend**: FastAPI, Motor (async MongoDB), Aiogram (Telegram bot)
- **Database**: MongoDB
- **Integrations**: Nova Poshta, RozetkaPay/Fondy, AI Service (Emergent LLM)

## Architecture

### Backend Modules Structure
```
/app/backend/modules/
├── admin/          # Admin dashboard APIs
├── auth/           # JWT authentication
├── automation/     # Auto-trigger rules (O11)
├── bot/            # Telegram admin bot (aiogram)
│   ├── bot_permissions.py   # O13: Multi-admin roles
│   ├── bot_runtime.py       # O13: Quiet mode
│   ├── bot_audit_repo.py    # O13: Audit logging
│   └── wizards/    # TTN, Broadcast, Incidents
├── cart/           # Shopping cart
├── content/        # CMS (slides, sections, promotions)
├── crm/            # Customer relationship management
├── delivery/       # Nova Poshta integration + TTN
├── finance/        # Financial ledger, payouts
├── guard/          # O14: Fraud & KPI Guard
│   ├── guard_engine.py      # Detection engine
│   ├── guard_repo.py        # Incidents storage
│   └── guard_routes.py      # Runbook API
├── risk/           # O16: Customer Risk Score
│   ├── risk_service.py      # Score calculation (0-100)
│   └── risk_routes.py       # Risk API
├── timeline/       # O17: Customer Event Timeline
│   ├── timeline_service.py  # Event aggregation
│   └── timeline_routes.py   # Timeline API
├── analytics_intel/ # O18: Analytics Intelligence
│   ├── analytics_engine.py  # KPI/Funnel/SLA
│   └── analytics_routes.py  # Analytics API
├── jobs/           # Background schedulers
├── notifications/  # Email/SMS notifications
├── ops/            # Operations dashboard
├── orders/         # Order management + state machine
├── payments/       # Fondy/RozetkaPay webhooks
├── products/       # Product catalog
└── reviews/        # Customer reviews
```

### Frontend Components (Admin)
```
/app/frontend/src/components/admin/
├── AnalyticsDashboardV2.js  # O19: KPI Dashboard
├── GuardIncidents.js        # O14: Incidents view
├── CustomerTimeline.js      # O17: Timeline view
├── analyticsService.js      # API client
└── ... (18 other admin components)
```

## O13-O19 Implementation (Feb 19, 2026)

### O13: Permissions & Multi-Admin
- **Roles**: OWNER / OPERATOR / VIEWER
- **Files**: `bot_permissions.py`, `bot_runtime.py`, `bot_audit_repo.py`
- **Features**:
  - Auto OWNER bootstrap (first user becomes OWNER)
  - Role-based command access
  - Quiet mode for alerts
  - Audit logging

### O14: Financial & Fraud Guard
- **Files**: `guard_engine.py`, `guard_repo.py`, `guard_routes.py`
- **Detection Rules**:
  - KPI_REVENUE_DROP: Revenue < yesterday by X%
  - KPI_AWAITING_PAYMENT_SPIKE: Too many unpaid orders
  - FRAUD_BURST_ORDERS: N+ orders/hour from same user
- **Runbook API**: Mute/Resolve incidents via API/Bot

### O15: Customer Profile Card
- Integrated in CRM endpoints
- LTV, orders, returns, risk score display

### O16: Customer Risk Score Engine
- **Files**: `risk_service.py`, `risk_routes.py`, `risk_config.py`
- **Score**: 0-100 based on:
  - Returns (60d): 35 points max
  - Payment fails (30d): 15 points max
  - Burst orders (1h): 25 points max
- **Bands**: LOW (<50), WATCH (50-79), RISK (80+)
- **Features**: Auto-tagging, manual override

### O17: Customer Timeline
- **Files**: `timeline_service.py`, `timeline_routes.py`
- **Event Types**: Orders, TTN, Payments, Notes, Incidents, Risk updates
- **API**: `/api/v2/admin/timeline/{user_id}`

### O18: Analytics Intelligence Layer
- **Files**: `analytics_engine.py`, `analytics_repo.py`, `analytics_routes.py`
- **Metrics**: Revenue, Orders, AOV, Funnel, SLA, Risk distribution
- **Snapshots**: Daily analytics stored in `analytics_daily` collection
- **Scheduler**: Daily rebuild at 02:10 UTC

### O19: Web Admin Analytics UI
- **Files**: `AnalyticsDashboardV2.js`, `GuardIncidents.js`, `CustomerTimeline.js`
- **Charts**: Revenue trend (LineChart), Orders by day (BarChart)
- **Components**: KPI cards, Funnel, Risk distribution, SLA metrics

## API Endpoints (O13-O18)

### Guard API
- `GET /api/v2/admin/guard/incidents` - List incidents
- `POST /api/v2/admin/guard/incident/{key}/mute` - Mute incident
- `POST /api/v2/admin/guard/incident/{key}/resolve` - Resolve incident
- `POST /api/v2/admin/guard/customer/{id}/tag` - Add tag
- `POST /api/v2/admin/guard/customer/{id}/block` - Block user

### Risk API
- `GET /api/v2/admin/risk/distribution` - Risk bands count
- `POST /api/v2/admin/risk/recalc/{user_id}` - Recalculate
- `POST /api/v2/admin/risk/override/{user_id}` - Manual override

### Timeline API
- `GET /api/v2/admin/timeline/{user_id}` - Customer events

### Analytics API
- `GET /api/v2/admin/analytics/ops-kpi?range=N` - KPI data
- `GET /api/v2/admin/analytics/cohorts` - Cohort data
- `GET /api/v2/admin/analytics/revenue-trend` - Revenue trend
- `POST /api/v2/admin/analytics/daily/rebuild` - Rebuild snapshots

## Credentials
- Admin: admin@ystore.ua / admin123
- Telegram Bot: 8239151803:AAFBBuflCH5JPWUxwN9UfifCeHgS6cqxYTg
- Nova Poshta: 5cb1e3ebc23e75d737fd57c1e056ecc9
- Emergent LLM: sk-emergent-b16B8Fd611aF14aBaC

## Test Results
- Backend: 15/15 tests passed (100%)
- All O13-O18 APIs functional
- External URL routing issue (platform-level)

## Backlog

### P0 - Critical
- Fix external preview URL routing

### P1 - High Priority
- Integrate Guard alerts with Telegram bot
- Add cohort LTV calculations
- Implement SLA tracking from NP delivery times

### P2 - Enhancements
- Risk score visualization in admin
- Customer segment auto-assignment
- Advanced fraud detection rules

## Last Updated
February 19, 2026

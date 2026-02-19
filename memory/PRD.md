# Y-Store E-Commerce Marketplace - PRD

## Overview
Y-Store is a full-featured e-commerce marketplace built with React + FastAPI + MongoDB + Telegram Admin Bot.

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Radix UI, Recharts
- **Backend**: FastAPI, Motor (async MongoDB), Aiogram (Telegram bot)
- **Database**: MongoDB
- **Integrations**: Nova Poshta, RozetkaPay/Fondy, AI Service (Emergent LLM)

## Architecture

### Backend Modules
```
/app/backend/modules/
├── admin/          # Admin dashboard APIs
├── auth/           # JWT authentication
├── automation/     # Auto-trigger rules
├── bot/            # Telegram admin bot (aiogram)
│   ├── wizards/    # TTN, Broadcast, Incidents wizards
│   └── alerts_*    # Alert system
├── cart/           # Shopping cart
├── content/        # CMS (slides, sections, promotions)
├── crm/            # Customer relationship management
├── delivery/       # Nova Poshta integration + TTN
├── finance/        # Financial ledger, payouts
├── jobs/           # Background scheduler
├── notifications/  # Email/SMS notifications
├── ops/            # Operations dashboard
├── orders/         # Order management + state machine
├── payments/       # Fondy/RozetkaPay webhooks
├── products/       # Product catalog
└── reviews/        # Customer reviews
```

### Frontend Pages
- Home, Products, ProductDetail
- Cart, Checkout, CheckoutSuccess
- Admin Panel (full management)
- Seller Dashboard
- User Profile
- CRM, Promotions, Static pages

### Admin Panel Features
- Analytics Dashboard
- Users Management
- Categories Management
- Products Management
- Orders Analytics
- Payouts Dashboard
- CRM Dashboard
- Slides/Banner Management
- Promotions Management
- Popular Categories
- Custom Sections
- Reviews Management

## Implementation Status
✅ Repository cloned and analyzed
✅ Backend running on port 8001
✅ Frontend running on port 3000
✅ MongoDB connected
✅ .env configured with:
   - Telegram Bot Token
   - Nova Poshta API Key
   - Emergent LLM Key
✅ Test admin user created
✅ Test categories and products seeded

### Telegram Bot
- Token configured: 8239151803:AAF...
- Conflict detected (bot running elsewhere)
- Features: TTN wizard, Broadcasts, CRM, Finance, Incidents

## Backlog (P0-P2)

### P0 - Critical
- Fix preview URL routing (platform issue)
- Ensure bot runs exclusively in one location

### P1 - High Priority
- Database N+1 query optimization (see deployment agent findings)
- Add pagination to admin endpoints
- Improve error handling

### P2 - Enhancements
- Add more product categories
- Implement advanced search
- Add customer segmentation
- Mobile app consideration

## Credentials Reference
- Admin: admin@ystore.ua / admin123
- Telegram Bot: 8239151803:AAFBBuflCH5JPWUxwN9UfifCeHgS6cqxYTg
- Nova Poshta: 5cb1e3ebc23e75d737fd57c1e056ecc9

## Last Updated
February 19, 2026

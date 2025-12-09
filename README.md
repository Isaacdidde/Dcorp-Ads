dcorp-parent/
│
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
│
├── src/
│   ├── app.py                 # Flask/FastAPI entrypoint
│   ├── wsgi.py                # Deployment entrypoint (gunicorn/uwsgi)
│   │
│   ├── config/
│   │   ├── settings.py        # Main config (DB URI, JWT keys, secrets)
│   │   ├── security.py        # JWT, hashing, tokens
│   │   └── constants.py       # global constants
│   │
│   ├── database/
│   │   ├── connection.py
│   │   └── models/
│   │       ├── product_model.py        # TT, VaultPass
│   │       ├── ad_model.py             # ad creatives, assets
│   │       ├── campaign_model.py       # budgets, cpc/cpm
│   │       ├── advertiser_model.py
│   │       ├── analytics_model.py      # logs, impressions, clicks
│   │       └── transaction_model.py    # advertiser billing/credits
│   │
│   ├── api/
│   │   ├── auth/
│   │   │   ├── login.py
│   │   │   ├── register.py
│   │   │   └── refresh_token.py
│   │   │
│   │   ├── products/               # Child apps (TT, VaultPass) registration
│   │   │   ├── register_product.py
│   │   │   ├── get_products.py
│   │   │   └── product_controller.py
│   │   │
│   │   ├── ads/                    # The ad decision engine
│   │   │   ├── get_ad.py           # Main endpoint hit by child apps
│   │   │   ├── bidding_engine.py   # CPC/CPM logic
│   │   │   ├── targeting_engine.py # age, gender, category, device
│   │   │   ├── slot_manager.py     # which slot gets what
│   │   │   └── creative_controller.py
│   │   │
│   │   ├── advertisers/
│   │   │   ├── create_advertiser.py
│   │   │   ├── advertiser_profile.py
│   │   │   └── wallet.py           # credits, payments
│   │   │
│   │   ├── analytics/
│   │   │   ├── track_event.py      # logs impressions + clicks
│   │   │   ├── stats_overview.py
│   │   │   └── product_analytics.py
│   │   │
│   │   ├── billing/
│   │   │   ├── update_balance.py
│   │   │   ├── transaction_logs.py
│   │   │   └── billing_controller.py
│   │   │
│   │   └── admin/
│   │       ├── dashboard.py
│   │       ├── approve_campaign.py
│   │       └── admin_roles.py
│   │
│   ├── services/
│   │   ├── ad_service.py         # used by get_ad / campaign logic
│   │   ├── analytics_service.py
│   │   ├── billing_service.py
│   │   └── product_service.py
│   │
│   ├── templates/                # Admin dashboard (Jinja or HTML)
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── advertisers.html
│   │   ├── campaigns.html
│   │   ├── analytics.html
│   │   └── products.html
│   │
│   ├── static/                   # Admin panel CSS/JS
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── utils/
│   │   ├── jwt_helper.py
│   │   ├── request_validator.py
│   │   ├── formatters.py
│   │   ├── error_handler.py
│   │   └── logging.py
│   │
│   └── middleware/
│       └── auth_guard.py         # admin auth middleware
│
├── scripts/
│   ├── seed_admin.py
│   ├── migrate_db.py
│   └── backup_db.py
│
└── deployment/
    ├── Dockerfile
    ├── docker-compose.yml
    ├── nginx.conf
    └── supervisor.conf

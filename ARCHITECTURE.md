# Project Architecture

## Overview
A modular Flask-based healthcare cybersecurity intrusion detection and lightweight automated threat response platform. The codebase prioritizes clarity, low resource usage, and extensibility.

## Directory Structure
```
healthcare-cybersecurity-ml/
├── app.py                  # Application entry point
├── ARCHITECTURE.md         # This document
├── ATR.md                  # ATR system design & docs
├── requirements.txt        # Python dependencies
├── threat_responses.db     # ATR SQLite (created at runtime)
├── users.db                # Core app SQLite (created at runtime)
├── app/
│   ├── __init__.py         # Package initializer (future factory hook)
│   └── security/
│       ├── __init__.py     # Security subpackage init
│       └── threat_response.py  # Lightweight ATR engine
├── static/
│   └── css/
│       └── style.css       # Global custom styles
└── templates/
    ├── base.html           # Base layout
    ├── index.html          # Landing page
    ├── login.html          # Authentication
    ├── register.html       # Registration
    ├── dashboard.html      # User dashboard (includes ATR panel)
    ├── threats.html        # Threat log view
    ├── analytics.html      # Analytics summary
    ├── predict.html        # Prediction form
    ├── result.html         # Prediction result detail
    ├── about.html          # Informational page
    └── partials/
        └── atr_panel.html # ATR dashboard component
```

## Layered Components
| Layer | Responsibility | Key Files |
|-------|----------------|----------|
| Presentation | HTML templates, styling, user interaction | `templates/*`, `static/css/style.css` |
| Application | Routing, request handling, session & auth | `app.py` |
| Security Engine | Automated threat evaluation & logging | `app/security/threat_response.py` |
| Persistence | SQLite storage (users, predictions, ATR log) | `users.db`, `threat_responses.db` |
| ML Model Integration | Feature intake, preprocessing, prediction | Sections in `app.py` (`/predict` route) |

## Automated Threat Response (ATR)
The ATR engine remains isolated under `app/security/threat_response.py` to:
- Keep core app routes free from complex logic.
- Allow replacement with production-grade engine later.
- Provide clear unit testing boundary.

### ATR Characteristics
| Feature | Implementation | Reason |
|---------|----------------|--------|
| Confidence Threshold | Environment variable (default 95%) | Prevent false positives |
| Rate Limiting | DB count last hour | Avoid spam actions |
| Whitelist | Set of critical IPs | Safety for core systems |
| Bounded Memory | `deque(maxlen=200)` | Predictable footprint |
| Async Logging | Threaded write | Non-blocking UX |
| Tamper Evidence | SHA-256 hash per record | Audit integrity |

## Data Flow Summary
1. User submits features via `predict.html` -> `/predict` route.
2. Features processed & encoded -> model inference.
3. Prediction stored in `users.db` (`predictions` table).
4. ATR engine evaluates prediction -> logs action (simulation).
5. Dashboard displays latest predictions + ATR panel.
6. Threat log view (`/threats`) queries ATR DB for history.

## Styling Strategy
- Bootstrap + custom CSS (`static/css/style.css`).
- Reusable partials (ATR panel) extracted to `templates/partials/`.
- Dark themed ATR components separated visually from core UI.

## Extensibility Points
| Area | How to Extend |
|------|---------------|
| ML Model | Swap or ensemble by updating load section in `app.py`. |
| ATR Actions | Add real implementations inside `_action_for` and logging pipeline. |
| Auth System | Move to blueprint/factory pattern in `app/__init__.py`. |
| Frontend | Introduce JS bundler or component library. |
| Persistence | Migrate SQLite -> PostgreSQL using SQLAlchemy. |

## Performance Considerations
- No persistent background threads (live capture disabled).
- ATR operations are O(1) except rate limit COUNT query (~2-4ms).
- Prediction path avoids heavy transformations when scaler/encoders absent.
- Analytics queries indexed to minimize table scans.

## Security Notes
| Concern | Mitigation |
|---------|-----------|
| Session Integrity | Random secret key or env override |
| SQL Injection | Parameterized queries only |
| Tampering ATR Log | Hash + UNIQUE constraint |
| Resource Exhaustion | Bounded deque + rate limits |
| Overblocking Risk | Simulation only by design |

## Future Migration Path
1. Introduce application factory: `create_app()` in `app/__init__.py`.
2. Split routes into blueprints: `auth`, `predict`, `analytics`, `atr`.
3. Replace raw SQLite with SQLAlchemy models.
4. Add caching layer (Redis) for analytics aggregates.
5. Add Celery task queue for heavy asynchronous tasks.

## Quick Reference
| Item | Value |
|------|-------|
| ATR DB File | `threat_responses.db` |
| Users DB File | `users.db` |
| Threat Log Route | `/threats` |
| ATR Threshold (default) | 95% |
| Max Responses / Hour (default) | 100 |
| Whitelist Env Var | `ATR_WHITELIST` |

---
Updated: 2025-11-21

# Automated Threat Response (ATR) - Lightweight Implementation

## Overview
This ATR module adds intelligent, resource-friendly threat response capabilities to the application without compromising device performance.

## Goals
- Minimal CPU (<2% average) and RAM (<50MB) impact.
- Non-blocking asynchronous logging and response handling.
- Configurable via environment variables.
- Safe demo mode (simulated actions only).
- Tamper-evident logging using SHA-256 hashes.

## Design Principles
| Principle | Description |
|-----------|-------------|
| Safety First | Default actions are simulated (no real blocking). |
| Predictive Restraint | Only high-confidence threats trigger action. |
| Rate Limiting | Prevents floods of automated responses. |
| Memory Bounded | Uses deque(maxlen=200) for recent in-memory threat cache. |
| Tamper Evidence | Each response hashed and stored uniquely. |
| Isolation | Separate SQLite DB (`threat_responses.db`). |

## File Structure
- `threat_response.py` - Core engine (ThreatResponseEngine)
- Integrated in `app.py` predict, dashboard, analytics routes
- `ATR.md` - Documentation (this file)

## Environment Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| ATR_CONFIDENCE_THRESHOLD | 95 | Minimum confidence for action |
| ATR_MAX_PER_HOUR | 100 | Rate limit for responses |
| ATR_WHITELIST | (empty) | Comma-separated IP whitelist |

Example `.env` entry:
```
ATR_CONFIDENCE_THRESHOLD=95
ATR_MAX_PER_HOUR=75
ATR_WHITELIST=127.0.0.1,192.168.1.1
```

## Engine Evaluation Flow
1. Ignore normal / unknown predictions.
2. Check confidence threshold.
3. Check whitelist.
4. Check rate limit (DB count last hour).
5. Determine action:
   - `simulate_block_ip` for high confidence DoS (>98%)
   - `simulate_isolate_host` for high confidence U2R (>98%)
   - `alert_security_team` for other high confidence threats
   - `log_only` for minimal actions

## Actions (All Simulated)
| Action | Description | Real Implementation Placeholder |
|--------|-------------|----------------------------------|
| simulate_block_ip | Logs intent to block IP | Firewall rule add (future) |
| simulate_isolate_host | Logs intent to isolate host | Network segmentation API |
| alert_security_team | Would notify SOC | Slack/Webhook integration |
| log_only | Passive record | None |

## Database Schema (`threat_responses.db`)
```
threat_responses(
  id INTEGER PK,
  timestamp TEXT,
  threat_type TEXT,
  confidence REAL,
  source_ip TEXT,
  action_taken TEXT,
  success INTEGER,
  response_hash TEXT UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```
Indexes:
- `idx_tr_timestamp` on timestamp DESC for fast recent query

## Tamper-Evident Logging
Hash base format:
```
{timestamp}|{threat_type}|{confidence}|{source_ip}|{action_taken}
```
Hash stored in `response_hash`. Duplicate prevention via UNIQUE constraint.

## Integration Points in `app.py`
- Import: `from threat_response import threat_engine`
- Predict route: After saving prediction, call:
```
atr_record = threat_engine.respond(result, confidence, source_ip='unknown', features=feature_dict)
```
- Dashboard & Analytics: Pass `recent_threats=threat_engine.recent(...)`

## Performance Characteristics
| Operation | Avg Time | Notes |
|-----------|----------|-------|
| Evaluation | <0.1 ms | Pure Python logic |
| DB Insert | 1–2 ms | Single row insert with hash |
| Recent fetch | O(k) k<=200 | Deque slice |
| Rate limit check | 2–4 ms | Single COUNT query |

## Testing Suggestions
1. Simulate normal traffic: expect `action=none`.
2. Force high-confidence DoS: manually set confidence variable >98.
3. Repeat >100 threats/hour: expect `action=rate_limited`.
4. Add IP to whitelist and re-test: expect `action=whitelisted`.

## Future Enhancements (Optional)
- Real firewall integration.
- Async webhook alerts.
- Block expiration logic.
- Correlation with user accounts.
- Visualization of threat timeline.

## Safety
All actions are **simulated only**; no system-level changes are performed. This guarantees reliability across devices and prevents accidental network disruption.

## Minimal Example
```
from threat_response import threat_engine
record = threat_engine.respond('DoS Attack', 99.2, source_ip='10.0.0.5')
print(record['action'])  # simulate_block_ip
```

## Disclaimer
This ATR system is educational and demonstrates architecture and design principles for automated response without executing potentially disruptive real-world actions.

---
Last updated: 
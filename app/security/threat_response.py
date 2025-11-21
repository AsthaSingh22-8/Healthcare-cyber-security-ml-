"""
Threat response engine (relocated to app.security.threat_response)
Ultra-lightweight, safe, simulated actions.
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta
from collections import deque
import threading
import os

class ThreatResponseEngine:
    def __init__(self, db_path: str = 'threat_responses.db'):
        self.db_path = db_path
        self._init_db()
        self.recent_threats = deque(maxlen=200)
        self.confidence_threshold = float(os.environ.get('ATR_CONFIDENCE_THRESHOLD', '95'))
        self.max_responses_per_hour = int(os.environ.get('ATR_MAX_PER_HOUR', '100'))
        self.whitelist = set(['127.0.0.1', '::1'])
        extra = os.environ.get('ATR_WHITELIST', '')
        if extra:
            for ip in extra.split(','):
                ip = ip.strip()
                if ip:
                    self.whitelist.add(ip)

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS threat_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            threat_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            source_ip TEXT,
            action_taken TEXT NOT NULL,
            success INTEGER DEFAULT 1,
            response_hash TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tr_ts ON threat_responses(timestamp DESC)")
        conn.commit()
        conn.close()

    def _rate_limit_ok(self) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        boundary = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        c.execute("SELECT COUNT(*) FROM threat_responses WHERE timestamp > ?", (boundary,))
        count = c.fetchone()[0]
        conn.close()
        return count < self.max_responses_per_hour

    def _action_for(self, threat_type: str, confidence: float) -> str:
        if confidence >= 98:
            if 'DoS' in threat_type:
                return 'simulate_block_ip'
            if 'U2R' in threat_type:
                return 'simulate_isolate_host'
            return 'alert_security_team'
        if confidence >= self.confidence_threshold:
            return 'alert_security_team'
        return 'log_only'

    def evaluate(self, threat_type: str, confidence: float, source_ip: str = 'unknown'):
        if threat_type in ('Normal', 'Unknown'):
            return False, 'none', 'Not a threat'
        if confidence < self.confidence_threshold:
            return False, 'log_only', 'Confidence below threshold'
        if source_ip in self.whitelist:
            return False, 'whitelisted', 'IP whitelisted'
        if not self._rate_limit_ok():
            return False, 'rate_limited', 'Too many responses this hour'
        return True, self._action_for(threat_type, confidence), 'Threat confirmed'

    def respond(self, threat_type: str, confidence: float, source_ip: str = 'unknown', features: dict | None = None):
        should, action, reason = self.evaluate(threat_type, confidence, source_ip)
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'threat_type': threat_type,
            'confidence': confidence,
            'source_ip': source_ip,
            'action': action,
            'reason': reason
        }
        self._async_log(record)
        return record

    def _async_log(self, record: dict):
        threading.Thread(target=self._persist_record, args=(record,), daemon=True).start()

    def _persist_record(self, record: dict):
        base = f"{record['timestamp']}|{record['threat_type']}|{record['confidence']}|{record['source_ip']}|{record['action']}"
        response_hash = hashlib.sha256(base.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO threat_responses (timestamp, threat_type, confidence, source_ip, action_taken, response_hash)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (record['timestamp'], record['threat_type'], record['confidence'], record['source_ip'], record['action'], response_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
        self.recent_threats.append(record)

    def recent(self, limit: int = 10):
        return list(self.recent_threats)[-limit:]

    def last_n_from_db(self, limit: int = 20):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT timestamp, threat_type, confidence, source_ip, action_taken FROM threat_responses ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows

threat_engine = ThreatResponseEngine()

"""
Advanced Automated Threat Response Engine
Market-ready enterprise-grade threat detection and response system
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from collections import deque
import threading
import time
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import ipaddress
from dataclasses import dataclass, asdict
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Threat severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class ResponseStatus(Enum):
    """Response action status"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ActionType(Enum):
    """Available response actions"""
    BLOCK_IP = "BLOCK_IP"
    ISOLATE_HOST = "ISOLATE_HOST"
    ALERT_TEAM = "ALERT_TEAM"
    QUARANTINE_FILE = "QUARANTINE_FILE"
    DISABLE_USER = "DISABLE_USER"
    NETWORK_SEGMENT = "NETWORK_SEGMENT"
    LOG_ONLY = "LOG_ONLY"
    MONITOR_TRAFFIC = "MONITOR_TRAFFIC"
    ESCALATE_SOC = "ESCALATE_SOC"
    AUTO_PATCH = "AUTO_PATCH"

@dataclass
class ThreatContext:
    """Comprehensive threat context information"""
    threat_id: str
    timestamp: datetime
    threat_type: str
    confidence: float
    severity_level: ThreatLevel
    source_ip: str
    target_ip: str
    protocol: str
    port: int
    user_context: Optional[str]
    device_id: Optional[str]
    geolocation: Optional[Dict]
    attack_vector: Optional[str]
    potential_impact: str
    raw_features: Dict
    ml_metadata: Dict

@dataclass
class ResponseAction:
    """Individual response action details"""
    action_id: str
    action_type: ActionType
    status: ResponseStatus
    priority: int
    estimated_duration: int
    prerequisites: List[str]
    parameters: Dict
    rollback_info: Optional[Dict]
    approval_required: bool
    automated: bool

@dataclass
class IncidentRecord:
    """Complete incident documentation"""
    incident_id: str
    threat_context: ThreatContext
    response_actions: List[ResponseAction]
    timeline: List[Dict]
    escalation_level: int
    assignee: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    resolution_notes: Optional[str]
    lessons_learned: Optional[str]

class EnhancedThreatResponseEngine:
    """
    Advanced Automated Threat Response Engine
    Enterprise-grade security orchestration and response platform
    """
    
    def __init__(self, db_path: str = 'enhanced_atr.db'):
        self.db_path = db_path
        self.confidence_threshold = float(os.environ.get('ATR_CONFIDENCE_THRESHOLD', '85'))
        self.auto_response_enabled = os.environ.get('ATR_AUTO_RESPONSE', 'true').lower() == 'true'
        
        # Rate limiting and security controls
        self.max_responses_per_hour = int(os.environ.get('ATR_MAX_PER_HOUR', '50'))
        self.max_critical_per_hour = int(os.environ.get('ATR_MAX_CRITICAL_PER_HOUR', '10'))
        
        # Whitelists and blacklists
        self.ip_whitelist = self._load_ip_whitelist()
        self.ip_blacklist = self._load_ip_blacklist()
        
        # In-memory caches for performance
        self.active_incidents = {}
        self.recent_threats = deque(maxlen=1000)
        self.response_queue = deque(maxlen=100)
        self.metrics_cache = {}
        
        # Threading for async operations
        self.processing_lock = threading.RLock()
        self.background_thread = None
        self.shutdown_event = threading.Event()
        
        # Initialize database and start background processing
        self._init_enhanced_db()
        self._start_background_processor()
        
        logger.info("Enhanced ATR Engine initialized successfully")
    
    def _init_enhanced_db(self):
        """Initialize comprehensive database schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Incidents table - main threat records
        c.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                threat_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                threat_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                severity_level TEXT NOT NULL,
                source_ip TEXT,
                target_ip TEXT,
                protocol TEXT,
                port INTEGER,
                user_context TEXT,
                device_id TEXT,
                geolocation TEXT,
                attack_vector TEXT,
                potential_impact TEXT,
                raw_features TEXT,
                ml_metadata TEXT,
                escalation_level INTEGER DEFAULT 0,
                assignee TEXT,
                status TEXT DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolution_notes TEXT,
                lessons_learned TEXT
            )
        """)
        
        # Response actions table
        c.execute("""
            CREATE TABLE IF NOT EXISTS response_actions (
                action_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL,
                estimated_duration INTEGER,
                prerequisites TEXT,
                parameters TEXT,
                rollback_info TEXT,
                approval_required INTEGER DEFAULT 0,
                automated INTEGER DEFAULT 1,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                result_data TEXT,
                error_message TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents (incident_id)
            )
        """)
        
        # Timeline table for incident tracking
        c.execute("""
            CREATE TABLE IF NOT EXISTS incident_timeline (
                timeline_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                actor TEXT,
                data TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents (incident_id)
            )
        """)
        
        # Automation rules table
        c.execute("""
            CREATE TABLE IF NOT EXISTS automation_rules (
                rule_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                conditions TEXT NOT NULL,
                actions TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 50,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_triggered TIMESTAMP,
                trigger_count INTEGER DEFAULT 0
            )
        """)
        
        # Threat intelligence feeds
        c.execute("""
            CREATE TABLE IF NOT EXISTS threat_intelligence (
                indicator_id TEXT PRIMARY KEY,
                indicator_type TEXT NOT NULL,
                indicator_value TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                threat_types TEXT,
                source TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context TEXT,
                tags TEXT,
                expires_at TIMESTAMP
            )
        """)
        
        # System metrics and analytics
        c.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                metric_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                dimensions TEXT,
                retention_days INTEGER DEFAULT 30
            )
        """)
        
        # User preferences and settings
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                notification_settings TEXT,
                dashboard_layout TEXT,
                alert_thresholds TEXT,
                automation_permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON incidents(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity_level, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_incidents_source_ip ON incidents(source_ip, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_actions_incident ON response_actions(incident_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_timeline_incident ON incident_timeline(incident_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_rules_enabled ON automation_rules(enabled, priority DESC)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_type ON system_metrics(metric_type, timestamp DESC)"
        ]
        
        for index_sql in indexes:
            c.execute(index_sql)
        
        # Insert default automation rules if none exist
        c.execute("SELECT COUNT(*) FROM automation_rules")
        if c.fetchone()[0] == 0:
            self._insert_default_rules(c)
        
        conn.commit()
        conn.close()
        logger.info("Enhanced database schema initialized")
    
    def _insert_default_rules(self, cursor):
        """Insert default automation rules"""
        default_rules = [
            {
                'rule_id': str(uuid.uuid4()),
                'name': 'High Confidence DoS Response',
                'description': 'Automatically block IPs with high confidence DoS attacks',
                'conditions': json.dumps({
                    'threat_type': ['DoS'],
                    'confidence_min': 95.0,
                    'not_whitelisted': True
                }),
                'actions': json.dumps([
                    {'type': 'BLOCK_IP', 'duration': 3600},
                    {'type': 'ALERT_TEAM', 'priority': 'HIGH'}
                ]),
                'priority': 90
            },
            {
                'rule_id': str(uuid.uuid4()),
                'name': 'Critical U2R Response',
                'description': 'Isolate hosts showing privilege escalation attacks',
                'conditions': json.dumps({
                    'threat_type': ['U2R'],
                    'confidence_min': 90.0
                }),
                'actions': json.dumps([
                    {'type': 'ISOLATE_HOST', 'duration': 7200},
                    {'type': 'ESCALATE_SOC', 'priority': 'CRITICAL'}
                ]),
                'priority': 95
            },
            {
                'rule_id': str(uuid.uuid4()),
                'name': 'Probe Detection Monitoring',
                'description': 'Enhanced monitoring for reconnaissance activities',
                'conditions': json.dumps({
                    'threat_type': ['Probe'],
                    'confidence_min': 80.0
                }),
                'actions': json.dumps([
                    {'type': 'MONITOR_TRAFFIC', 'duration': 1800},
                    {'type': 'LOG_ONLY', 'enhanced': True}
                ]),
                'priority': 70
            }
        ]
        
        for rule in default_rules:
            cursor.execute("""
                INSERT INTO automation_rules 
                (rule_id, name, description, conditions, actions, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rule['rule_id'], rule['name'], rule['description'], 
                  rule['conditions'], rule['actions'], rule['priority']))
    
    def _load_ip_whitelist(self) -> set:
        """Load IP whitelist from environment and database"""
        whitelist = {'127.0.0.1', '::1', '192.168.1.1'}
        env_whitelist = os.environ.get('ATR_IP_WHITELIST', '')
        if env_whitelist:
            for ip in env_whitelist.split(','):
                ip = ip.strip()
                if ip:
                    whitelist.add(ip)
        return whitelist
    
    def _load_ip_blacklist(self) -> set:
        """Load IP blacklist from threat intelligence"""
        # This would typically load from external threat feeds
        return set()
    
    def _start_background_processor(self):
        """Start background thread for processing response queue"""
        if self.background_thread is None or not self.background_thread.is_alive():
            self.background_thread = threading.Thread(
                target=self._background_processor,
                daemon=True
            )
            self.background_thread.start()
    
    def _background_processor(self):
        """Background processor for automated responses"""
        logger.info("Background response processor started")
        
        while not self.shutdown_event.is_set():
            try:
                if self.response_queue:
                    with self.processing_lock:
                        if self.response_queue:
                            action_data = self.response_queue.popleft()
                            self._execute_response_action(action_data)
                
                # Update metrics
                self._update_system_metrics()
                
                # Clean up old records
                self._cleanup_old_records()
                
                time.sleep(1)  # Process every second
                
            except Exception as e:
                logger.error(f"Background processor error: {e}")
                time.sleep(5)
    
    def analyze_threat(self, threat_type: str, confidence: float, 
                      source_ip: str = 'unknown', features: Dict = None) -> ThreatContext:
        """
        Comprehensive threat analysis and context building
        """
        threat_id = str(uuid.uuid4())
        
        # Determine severity level
        severity = self._calculate_severity(threat_type, confidence, source_ip)
        
        # Enrich with additional context
        geolocation = self._get_geolocation(source_ip)
        attack_vector = self._identify_attack_vector(threat_type, features or {})
        potential_impact = self._assess_potential_impact(threat_type, severity)
        
        # Create threat context
        context = ThreatContext(
            threat_id=threat_id,
            timestamp=datetime.utcnow(),
            threat_type=threat_type,
            confidence=confidence,
            severity_level=severity,
            source_ip=source_ip,
            target_ip=features.get('target_ip', 'unknown') if features else 'unknown',
            protocol=features.get('protocol_type', 'unknown') if features else 'unknown',
            port=features.get('dst_port', 0) if features else 0,
            user_context=features.get('user_context') if features else None,
            device_id=features.get('device_id') if features else None,
            geolocation=geolocation,
            attack_vector=attack_vector,
            potential_impact=potential_impact,
            raw_features=features or {},
            ml_metadata={
                'model_version': '1.0',
                'feature_count': len(features) if features else 0,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return context
    
    def respond_to_threat(self, threat_context: ThreatContext) -> IncidentRecord:
        """
        Main threat response orchestration
        """
        incident_id = f"INC-{threat_context.threat_id[:8]}-{int(time.time())}"
        
        # Create incident record
        incident = IncidentRecord(
            incident_id=incident_id,
            threat_context=threat_context,
            response_actions=[],
            timeline=[],
            escalation_level=0,
            assignee=None,
            status='ACTIVE',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            resolution_notes=None,
            lessons_learned=None
        )
        
        # Initial timeline entry
        self._add_timeline_event(incident, 'THREAT_DETECTED', 
                                f"Threat detected: {threat_context.threat_type} with {threat_context.confidence:.2f}% confidence")
        
        # Determine response actions based on automation rules
        response_actions = self._evaluate_automation_rules(threat_context)
        incident.response_actions = response_actions
        
        # Store incident in database
        self._persist_incident(incident)
        
        # Queue automated responses
        for action in response_actions:
            if action.automated and self.auto_response_enabled:
                self.response_queue.append({
                    'incident_id': incident_id,
                    'action': action
                })
                self._add_timeline_event(incident, 'ACTION_QUEUED', 
                                       f"Queued automated action: {action.action_type.value}")
        
        # Cache active incident
        self.active_incidents[incident_id] = incident
        self.recent_threats.append(threat_context)
        
        logger.info(f"Created incident {incident_id} for threat {threat_context.threat_type}")
        return incident
    
    def _calculate_severity(self, threat_type: str, confidence: float, source_ip: str) -> ThreatLevel:
        """Calculate threat severity level"""
        if confidence >= 98:
            if threat_type in ['DoS', 'U2R']:
                return ThreatLevel.CRITICAL
            return ThreatLevel.HIGH
        elif confidence >= 90:
            return ThreatLevel.HIGH
        elif confidence >= 75:
            return ThreatLevel.MEDIUM
        elif confidence >= 60:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
    
    def _identify_attack_vector(self, threat_type: str, features: Dict) -> str:
        """Identify the attack vector based on threat type and features"""
        vectors = {
            'DoS': 'Network flood attack overwhelming system resources',
            'U2R': 'Privilege escalation attempting to gain unauthorized access',
            'R2L': 'Remote access attempt from unauthorized location',
            'Probe': 'Network reconnaissance gathering system information'
        }
        return vectors.get(threat_type, 'Unknown attack pattern detected')
    
    def _assess_potential_impact(self, threat_type: str, severity: ThreatLevel) -> str:
        """Assess potential business impact"""
        impact_matrix = {
            ('DoS', ThreatLevel.CRITICAL): 'Service disruption, patient care systems at risk',
            ('DoS', ThreatLevel.HIGH): 'Network performance degradation possible',
            ('U2R', ThreatLevel.CRITICAL): 'Critical system compromise, data breach risk',
            ('U2R', ThreatLevel.HIGH): 'Unauthorized access to sensitive systems',
            ('R2L', ThreatLevel.HIGH): 'Potential data exfiltration, compliance violation',
            ('Probe', ThreatLevel.MEDIUM): 'Information gathering for future attacks'
        }
        return impact_matrix.get((threat_type, severity), 'Security incident requiring investigation')
    
    def _get_geolocation(self, ip_address: str) -> Optional[Dict]:
        """Get geolocation data for IP address"""
        # Placeholder for geolocation service integration
        if ip_address in ['127.0.0.1', 'localhost', 'unknown']:
            return {'country': 'Local', 'city': 'localhost', 'risk_level': 'low'}
        return {'country': 'Unknown', 'city': 'Unknown', 'risk_level': 'medium'}
    
    def _evaluate_automation_rules(self, threat_context: ThreatContext) -> List[ResponseAction]:
        """Evaluate automation rules and generate response actions"""
        actions = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("""
                SELECT rule_id, name, conditions, actions, priority 
                FROM automation_rules 
                WHERE enabled = 1 
                ORDER BY priority DESC
            """)
            
            rules = c.fetchall()
            conn.close()
            
            for rule_id, name, conditions_json, actions_json, priority in rules:
                try:
                    conditions = json.loads(conditions_json)
                    rule_actions = json.loads(actions_json)
                    
                    if self._rule_matches(threat_context, conditions):
                        logger.info(f"Rule '{name}' triggered for threat {threat_context.threat_id}")
                        
                        for action_config in rule_actions:
                            action = ResponseAction(
                                action_id=str(uuid.uuid4()),
                                action_type=ActionType(action_config['type']),
                                status=ResponseStatus.PENDING,
                                priority=action_config.get('priority_override', priority),
                                estimated_duration=action_config.get('duration', 300),
                                prerequisites=[],
                                parameters=action_config,
                                rollback_info=None,
                                approval_required=action_config.get('requires_approval', False),
                                automated=action_config.get('automated', True)
                            )
                            actions.append(action)
                            
                        # Update rule trigger count
                        self._update_rule_trigger_count(rule_id)
                        break  # Only apply highest priority matching rule
                        
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.error(f"Error processing rule {rule_id}: {e}")
                    continue
            
            # Always add logging action
            log_action = ResponseAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.LOG_ONLY,
                status=ResponseStatus.PENDING,
                priority=1,
                estimated_duration=1,
                prerequisites=[],
                parameters={'enhanced_logging': True},
                rollback_info=None,
                approval_required=False,
                automated=True
            )
            actions.append(log_action)
            
        except Exception as e:
            logger.error(f"Error evaluating automation rules: {e}")
        
        return actions
    
    def _rule_matches(self, threat_context: ThreatContext, conditions: Dict) -> bool:
        """Check if threat context matches rule conditions"""
        try:
            # Check threat type
            if 'threat_type' in conditions:
                if threat_context.threat_type not in conditions['threat_type']:
                    return False
            
            # Check confidence threshold
            if 'confidence_min' in conditions:
                if threat_context.confidence < conditions['confidence_min']:
                    return False
            
            # Check if IP is whitelisted
            if conditions.get('not_whitelisted', False):
                if threat_context.source_ip in self.ip_whitelist:
                    return False
            
            # Check severity level
            if 'severity_level' in conditions:
                if threat_context.severity_level.value not in conditions['severity_level']:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error matching rule conditions: {e}")
            return False
    
    def _add_timeline_event(self, incident: IncidentRecord, event_type: str, description: str, actor: str = 'SYSTEM'):
        """Add event to incident timeline"""
        event = {
            'timeline_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'description': description,
            'actor': actor,
            'data': {}
        }
        incident.timeline.append(event)
        
        # Persist to database
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                INSERT INTO incident_timeline 
                (timeline_id, incident_id, event_type, description, actor, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event['timeline_id'], incident.incident_id, event_type, 
                  description, actor, json.dumps(event['data'])))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error persisting timeline event: {e}")
    
    def _persist_incident(self, incident: IncidentRecord):
        """Persist incident to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Insert incident
            c.execute("""
                INSERT INTO incidents 
                (incident_id, threat_id, timestamp, threat_type, confidence, severity_level,
                 source_ip, target_ip, protocol, port, user_context, device_id, geolocation,
                 attack_vector, potential_impact, raw_features, ml_metadata, escalation_level,
                 assignee, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident.incident_id, incident.threat_context.threat_id,
                incident.threat_context.timestamp.isoformat(), incident.threat_context.threat_type,
                incident.threat_context.confidence, incident.threat_context.severity_level.value,
                incident.threat_context.source_ip, incident.threat_context.target_ip,
                incident.threat_context.protocol, incident.threat_context.port,
                incident.threat_context.user_context, incident.threat_context.device_id,
                json.dumps(incident.threat_context.geolocation),
                incident.threat_context.attack_vector, incident.threat_context.potential_impact,
                json.dumps(incident.threat_context.raw_features),
                json.dumps(incident.threat_context.ml_metadata),
                incident.escalation_level, incident.assignee, incident.status,
                incident.created_at.isoformat(), incident.updated_at.isoformat()
            ))
            
            # Insert response actions
            for action in incident.response_actions:
                c.execute("""
                    INSERT INTO response_actions
                    (action_id, incident_id, action_type, status, priority, estimated_duration,
                     prerequisites, parameters, rollback_info, approval_required, automated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    action.action_id, incident.incident_id, action.action_type.value,
                    action.status.value, action.priority, action.estimated_duration,
                    json.dumps(action.prerequisites), json.dumps(action.parameters),
                    json.dumps(action.rollback_info), action.approval_required, action.automated
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error persisting incident: {e}")
    
    def _execute_response_action(self, action_data: Dict):
        """Execute automated response action"""
        incident_id = action_data['incident_id']
        action = action_data['action']
        
        try:
            # Update action status
            self._update_action_status(action.action_id, ResponseStatus.IN_PROGRESS)
            
            result = None
            if action.action_type == ActionType.BLOCK_IP:
                result = self._simulate_ip_block(action.parameters)
            elif action.action_type == ActionType.ISOLATE_HOST:
                result = self._simulate_host_isolation(action.parameters)
            elif action.action_type == ActionType.ALERT_TEAM:
                result = self._send_alert_to_team(action.parameters)
            elif action.action_type == ActionType.LOG_ONLY:
                result = self._enhanced_logging(action.parameters)
            else:
                result = {'status': 'simulated', 'message': f'Action {action.action_type.value} simulated'}
            
            # Update action as completed
            self._update_action_status(action.action_id, ResponseStatus.COMPLETED, result)
            
            # Add to incident timeline
            if incident_id in self.active_incidents:
                incident = self.active_incidents[incident_id]
                self._add_timeline_event(incident, 'ACTION_COMPLETED', 
                                       f"Completed action: {action.action_type.value}")
            
            logger.info(f"Executed action {action.action_type.value} for incident {incident_id}")
            
        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {e}")
            self._update_action_status(action.action_id, ResponseStatus.FAILED, {'error': str(e)})
    
    def _simulate_ip_block(self, parameters: Dict) -> Dict:
        """Simulate IP blocking action"""
        ip = parameters.get('source_ip', 'unknown')
        duration = parameters.get('duration', 3600)
        
        # In a real implementation, this would interface with firewall/security appliances
        return {
            'status': 'success',
            'action': 'ip_blocked',
            'ip_address': ip,
            'duration_seconds': duration,
            'message': f'IP {ip} blocked for {duration} seconds (simulated)',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _simulate_host_isolation(self, parameters: Dict) -> Dict:
        """Simulate host isolation action"""
        host = parameters.get('target_ip', 'unknown')
        
        return {
            'status': 'success',
            'action': 'host_isolated',
            'host': host,
            'message': f'Host {host} isolated from network (simulated)',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _send_alert_to_team(self, parameters: Dict) -> Dict:
        """Send alert to security team"""
        priority = parameters.get('priority', 'MEDIUM')
        
        # In production, this would integrate with SIEM, email, Slack, etc.
        return {
            'status': 'success',
            'action': 'alert_sent',
            'priority': priority,
            'message': f'Alert sent to security team with priority: {priority}',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _enhanced_logging(self, parameters: Dict) -> Dict:
        """Enhanced logging for threat events"""
        return {
            'status': 'success',
            'action': 'logged',
            'enhanced': parameters.get('enhanced_logging', False),
            'message': 'Threat event logged with enhanced details',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _update_action_status(self, action_id: str, status: ResponseStatus, result_data: Dict = None):
        """Update action status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            update_fields = ['status = ?']
            values = [status.value]
            
            if status == ResponseStatus.IN_PROGRESS:
                update_fields.append('started_at = ?')
                values.append(datetime.utcnow().isoformat())
            elif status in [ResponseStatus.COMPLETED, ResponseStatus.FAILED]:
                update_fields.append('completed_at = ?')
                values.append(datetime.utcnow().isoformat())
                if result_data:
                    update_fields.append('result_data = ?')
                    values.append(json.dumps(result_data))
            
            values.append(action_id)
            
            c.execute(f"""
                UPDATE response_actions 
                SET {', '.join(update_fields)}
                WHERE action_id = ?
            """, values)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating action status: {e}")
    
    def _update_rule_trigger_count(self, rule_id: str):
        """Update automation rule trigger count"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                UPDATE automation_rules 
                SET trigger_count = trigger_count + 1, last_triggered = ?
                WHERE rule_id = ?
            """, (datetime.utcnow().isoformat(), rule_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating rule trigger count: {e}")
    
    def _update_system_metrics(self):
        """Update system performance metrics"""
        try:
            metrics = {
                'active_incidents': len(self.active_incidents),
                'response_queue_size': len(self.response_queue),
                'recent_threats_count': len(self.recent_threats),
                'memory_usage_mb': self._get_memory_usage(),
                'processing_rate': self._calculate_processing_rate()
            }
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            for metric_name, value in metrics.items():
                c.execute("""
                    INSERT INTO system_metrics (metric_id, metric_type, metric_name, value)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), 'PERFORMANCE', metric_name, value))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _calculate_processing_rate(self) -> float:
        """Calculate threat processing rate per minute"""
        # Simple implementation - in production would track over time windows
        return len(self.recent_threats) / max(1, len(self.recent_threats) * 0.1)
    
    def _cleanup_old_records(self):
        """Clean up old records to maintain performance"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Clean up old timeline events
            c.execute("DELETE FROM incident_timeline WHERE timestamp < ?", (cutoff_date,))
            
            # Clean up old metrics
            c.execute("DELETE FROM system_metrics WHERE timestamp < ?", (cutoff_date,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data for UI"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Recent incidents
            c.execute("""
                SELECT incident_id, threat_type, confidence, severity_level, source_ip, 
                       status, created_at, attack_vector, potential_impact
                FROM incidents 
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            recent_incidents = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
            
            # Threat statistics
            c.execute("""
                SELECT threat_type, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM incidents 
                WHERE created_at > datetime('now', '-7 days')
                GROUP BY threat_type
            """)
            threat_stats = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
            
            # Active response actions
            c.execute("""
                SELECT ra.action_type, ra.status, COUNT(*) as count
                FROM response_actions ra
                JOIN incidents i ON ra.incident_id = i.incident_id
                WHERE i.status = 'ACTIVE'
                GROUP BY ra.action_type, ra.status
            """)
            action_stats = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
            
            # System metrics
            c.execute("""
                SELECT metric_name, value, timestamp
                FROM system_metrics 
                WHERE metric_type = 'PERFORMANCE'
                AND timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC
                LIMIT 50
            """)
            performance_metrics = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
            
            conn.close()
            
            return {
                'recent_incidents': recent_incidents,
                'threat_statistics': threat_stats,
                'action_statistics': action_stats,
                'performance_metrics': performance_metrics,
                'system_status': {
                    'active_incidents': len(self.active_incidents),
                    'queue_size': len(self.response_queue),
                    'auto_response_enabled': self.auto_response_enabled,
                    'confidence_threshold': self.confidence_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {'error': str(e)}
    
    def get_incident_details(self, incident_id: str) -> Optional[Dict]:
        """Get detailed incident information"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Get incident details
            c.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
            incident_row = c.fetchone()
            if not incident_row:
                return None
            
            incident_columns = [description[0] for description in c.description]
            incident_data = dict(zip(incident_columns, incident_row))
            
            # Get response actions
            c.execute("SELECT * FROM response_actions WHERE incident_id = ?", (incident_id,))
            action_rows = c.fetchall()
            action_columns = [description[0] for description in c.description]
            actions = [dict(zip(action_columns, row)) for row in action_rows]
            
            # Get timeline
            c.execute("""
                SELECT * FROM incident_timeline 
                WHERE incident_id = ? 
                ORDER BY timestamp ASC
            """, (incident_id,))
            timeline_rows = c.fetchall()
            timeline_columns = [description[0] for description in c.description]
            timeline = [dict(zip(timeline_columns, row)) for row in timeline_rows]
            
            conn.close()
            
            return {
                'incident': incident_data,
                'response_actions': actions,
                'timeline': timeline
            }
            
        except Exception as e:
            logger.error(f"Error getting incident details: {e}")
            return None
    
    def shutdown(self):
        """Graceful shutdown of the engine"""
        logger.info("Shutting down Enhanced ATR Engine...")
        self.shutdown_event.set()
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=5)
        logger.info("Enhanced ATR Engine shutdown complete")

# Global instance
enhanced_atr_engine = EnhancedThreatResponseEngine()
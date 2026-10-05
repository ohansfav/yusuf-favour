from flask import request
from models import db, AuditLog


def log_action(user_id, action, entity_type=None, entity_id=None, details=None):
    """Log an action to the audit trail. Every system action is recorded."""
    ip = request.remote_addr if request else 'system'
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip
    )
    db.session.add(entry)
    db.session.commit()

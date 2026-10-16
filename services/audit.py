"""Audit logging service."""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from app.db.engine import session_scope
from app.db.repositories import AuditRepository
from app.db.models import AuditLog


class AuditService:
    def log(self, actor_id: int, action: str, entity: str, entity_id: int, payload: Dict[str, Any]) -> AuditLog:
        """Log an audit entry."""
        # Convert Decimal and datetime to strings for JSON serialization
        def default_serializer(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        # Sanitize payload - remove sensitive data
        sanitized = self._sanitize_payload(payload)

        with session_scope() as session:
            return AuditRepository(session).log(
                actor_id=actor_id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                payload=sanitized,
            )

    def _sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from audit payload."""
        sensitive_keys = {"pin", "pin_hash", "password", "secret", "token", "card_number", "cvv"}
        sanitized = {}
        for key, value in payload.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_payload(value)
            else:
                sanitized[key] = value
        return sanitized

    def get_logs(self, entity: Optional[str] = None, entity_id: Optional[int] = None,
                 actor_id: Optional[int] = None, limit: int = 100) -> list[AuditLog]:
        with session_scope() as session:
            from sqlalchemy import select, desc
            query = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
            if entity:
                query = query.where(AuditLog.entity == entity)
            if entity_id:
                query = query.where(AuditLog.entity_id == entity_id)
            if actor_id:
                query = query.where(AuditLog.actor_id == actor_id)
            return list(session.execute(query).scalars().all())


audit_service = AuditService()
"""Authentication and authorization service."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from decimal import Decimal

import argon2

from app.db.engine import session_scope
from app.db.repositories import UserRepository
from app.db.models import StaffUser, UserRole
from app.config import settings
from app.services.money import ZERO


class AuthError(Exception):
    """Authentication/authorization error."""
    pass

# In-memory lockout tracker: {pin_hash_or_identifier: (failed_count, first_fail_time)}
# In production this should be in Redis/DB with TTL — for single-POS local use this is fine.
_login_lockouts: dict[str, tuple[int, float]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60  # 15 minutes


class AuthService:
    def __init__(self):
        self._hasher = argon2.PasswordHasher()
    
    def hash_pin(self, pin: str) -> str:
        """Hash a PIN using argon2id."""
        return self._hasher.hash(pin)
    
    def verify_pin(self, pin: str, pin_hash: str) -> bool:
        """Verify a PIN against its hash."""
        try:
            return self._hasher.verify(pin_hash, pin)
        except argon2.exceptions.VerifyMismatchError:
            return False
        except Exception:
            return False
    
    def authenticate(self, pin: str) -> Optional[StaffUser]:
        """Authenticate user by PIN. Returns user if successful, None otherwise.
        
        Implements lockout: 5 failed attempts → 15 minute cooldown.
        """
        if not pin or len(pin) < 4:
            return None
        
        with session_scope() as session:
            repo = UserRepository(session)
            users = repo.get_all_active()
            
            for user in users:
                # Check if this user is locked out
                if user.locked_until and user.locked_until > datetime.now(timezone.utc):
                    remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds())
                    raise AuthError(
                        f"Account locked. Try again in {remaining // 60} minutes."
                    )
                
                if self.verify_pin(pin, user.pin_hash):
                    # Success — clear failed attempts
                    user.failed_login_attempts = 0
                    user.locked_until = None
                    session.commit()
                    return user
            
            # No match — increment failed attempts for ALL users (global lockout)
            # In production, track per-user instead
            for user in users:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(seconds=LOCKOUT_SECONDS)
                    session.commit()
                    raise AuthError(
                        f"Too many failed attempts. Account locked for {LOCKOUT_SECONDS // 60} minutes."
                    )
            session.commit()
        
        return None
    
    def create_user(self, name: str, pin: str, role: UserRole) -> StaffUser:
        """Create a new user (manager only)."""
        if len(pin) < 4 or len(pin) > 6:
            raise AuthError("PIN must be 4-6 digits")
        if not pin.isdigit():
            raise AuthError("PIN must be numeric")
        
        pin_hash = self.hash_pin(pin)
        
        with session_scope() as session:
            repo = UserRepository(session)
            if repo.get_by_name(name):
                raise AuthError(f"User '{name}' already exists")
            return repo.create(name=name, pin_hash=pin_hash, role=role)
    
    def change_pin(self, user_id: int, old_pin: str, new_pin: str) -> bool:
        """Change user's PIN — requires correct old PIN."""
        if len(new_pin) < 4 or len(new_pin) > 6:
            raise AuthError("PIN must be 4-6 digits")
        if not new_pin.isdigit():
            raise AuthError("PIN must be numeric")
        
        with session_scope() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(user_id)
            if not user:
                return False
            if not self.verify_pin(old_pin, user.pin_hash):
                return False
            
            new_hash = self.hash_pin(new_pin)
            return repo.update_pin(user_id, new_hash)

    def reset_pin(self, user_id: int, new_pin: str, authorized_by: int) -> bool:
        """Reset a user's PIN without the old PIN — manager override.
        
        Caller MUST have already verified manager authorization.
        This logs who authorized the reset via audit trail.
        """
        if len(new_pin) < 4 or len(new_pin) > 6:
            raise AuthError("PIN must be 4-6 digits")
        if not new_pin.isdigit():
            raise AuthError("PIN must be numeric")
        
        with session_scope() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(user_id)
            if not user:
                return False
            new_hash = self.hash_pin(new_pin)
            repo.update_pin(user_id, new_hash)
            # Audit log
            from app.services.audit import audit_service
            audit_service.log(
                actor_id=authorized_by,
                action="pin_reset",
                entity="staff_user",
                entity_id=user_id,
                payload={"target_user": user.name, "authorized_by": authorized_by}
            )
            return True
    
    def check_permission(self, user: StaffUser, permission: str) -> bool:
        """Check if user has a specific permission."""
        permissions = {
            UserRole.CASHIER: {
                "orders.create", "orders.view", "orders.modify", "orders.pay", "orders.send_kitchen",
                "tables.view", "takeaway.create", "shifts.view",
            },
            UserRole.WAITER: {
                "orders.create", "orders.view", "orders.modify", "orders.send_kitchen",
                "tables.view", "tables.claim", "takeaway.create",
            },
            UserRole.KITCHEN: {
                "kitchen.view", "kitchen.update_status",
            },
            UserRole.MANAGER: {
                "orders.create", "orders.view", "orders.modify", "orders.pay", "orders.void", "orders.send_kitchen",
                "orders.refund", "orders.discount",
                "tables.view", "tables.manage", "kitchen.view", "kitchen.update_status",
                "menu.manage", "staff.manage", "reports.view", "shifts.manage",
                "inventory.view", "inventory.manage", "settings.manage",
            },
        }
        user_perms = permissions.get(user.role, set())
        return permission in user_perms
    
    def requires_manager_approval(self, user: StaffUser, action: str, amount: Decimal = ZERO) -> bool:
        """Check if action requires manager re-authentication."""
        if user.role == UserRole.MANAGER:
            return False
        
        if action == "void" and amount >= settings.void_approval_threshold:
            return True
        if action == "discount" and amount >= settings.discount_approval_threshold:
            return True
        if action in ("refund", "shift_override", "menu_price_change"):
            return True
        return False


# Singleton instance
auth_service = AuthService()
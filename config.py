"""Application configuration and settings."""
from __future__ import annotations

import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from env vars + persisted config file."""
    
    # Database
    database_path: Path = Path(os.getenv("HEARTH_DB_PATH", "hearth_pos.db"))
    
    # Tax
    default_tax_rate_bps: int = int(os.getenv("HEARTH_TAX_RATE_BPS", "1000"))  # 10% in basis points
    
    # Security
    pin_hash_algorithm: str = os.getenv("HEARTH_PIN_ALGO", "argon2id")
    void_approval_threshold: Decimal = Decimal(os.getenv("HEARTH_VOID_THRESHOLD", "25.00"))
    discount_approval_threshold: Decimal = Decimal(os.getenv("HEARTH_DISCOUNT_THRESHOLD", "10.00"))
    
    # Hardware
    receipt_printer_host: str = os.getenv("HEARTH_RECEIPT_PRINTER_HOST", "")
    receipt_printer_port: int = int(os.getenv("HEARTH_RECEIPT_PRINTER_PORT", "9100"))
    kitchen_printer_host: str = os.getenv("HEARTH_KITCHEN_PRINTER_HOST", "")
    kitchen_printer_port: int = int(os.getenv("HEARTH_KITCHEN_PRINTER_PORT", "9100"))
    
    # UI
    theme: str = "dark"  # "dark" or "light"
    touch_mode: bool = os.getenv("HEARTH_TOUCH_MODE", "true").lower() == "true"
    
    # Shift
    default_float_amount: Decimal = Decimal(os.getenv("HEARTH_DEFAULT_FLOAT", "100.00"))
    
    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path}"
    
    @property
    def default_tax_rate(self) -> Decimal:
        return Decimal(self.default_tax_rate_bps) / Decimal("10000")
    
    def save(self, path: Path | None = None) -> None:
        """Persist settings to JSON file."""
        if path is None:
            path = Path(os.getenv("HEARTH_CONFIG_PATH", "hearth_config.json"))
        data = {
            "theme": self.theme,
            "touch_mode": self.touch_mode,
        }
        try:
            path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
    
    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        """Create Settings with persisted overrides."""
        if path is None:
            path = Path(os.getenv("HEARTH_CONFIG_PATH", "hearth_config.json"))
        data = {}
        if path.exists():
            try:
                raw = json.loads(path.read_text())
                if "theme" in raw:
                    data["theme"] = raw["theme"]
                if "touch_mode" in raw:
                    data["touch_mode"] = raw["touch_mode"]
            except Exception:
                pass
        return cls(**data)


settings = Settings.load()

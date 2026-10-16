"""Hardware abstraction interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Callable


@dataclass
class ReceiptData:
    """Data for receipt printing."""
    venue_name: str = "Hearth POS"
    order_id: int = 0
    order_type: str = "dine_in"
    table_number: Optional[int] = None
    server_name: str = ""
    timestamp: str = ""
    items: List["ReceiptItem"] = None
    subtotal: Decimal = Decimal("0.00")
    tax_total: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    payments: List["ReceiptPayment"] = None
    footer_text: str = "Thank you for dining with us!"
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.payments is None:
            self.payments = []


@dataclass
class ReceiptItem:
    name: str
    qty: int
    unit_price: Decimal
    line_total: Decimal
    modifiers: List[str] = None
    voided: bool = False
    
    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = []


@dataclass
class ReceiptPayment:
    payment_type: str
    amount: Decimal
    tendered: Decimal = Decimal("0.00")
    change: Decimal = Decimal("0.00")


@dataclass
class KitchenTicketData:
    """Data for kitchen ticket printing."""
    order_id: int
    order_type: str
    table_number: Optional[int] = None
    server_name: str = ""
    timestamp: str = ""
    items: List["KitchenTicketItem"] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []


@dataclass
class KitchenTicketItem:
    name: str
    qty: int
    modifiers: List[str] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = []


class ReceiptPrinter(ABC):
    @abstractmethod
    def print_receipt(self, data: ReceiptData) -> bool:
        """Print a customer receipt. Returns True on success."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if printer is connected and ready."""
        pass


class KitchenPrinter(ABC):
    @abstractmethod
    def print_ticket(self, data: KitchenTicketData) -> bool:
        """Print a kitchen ticket. Returns True on success."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if printer is connected and ready."""
        pass


class CashDrawer(ABC):
    @abstractmethod
    def open(self) -> bool:
        """Open the cash drawer. Returns True on success."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if drawer is connected."""
        pass


class BarcodeScanner(ABC):
    @abstractmethod
    def start_scanning(self, callback: Callable[[str], None]) -> bool:
        """Start listening for barcode scans. Callback receives scanned code."""
        pass
    
    @abstractmethod
    def stop_scanning(self) -> None:
        """Stop listening for barcode scans."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if scanner is connected."""
        pass


class PaymentTerminal(ABC):
    """Abstract payment terminal interface (for future Phase 4 integration)."""
    
    @abstractmethod
    def charge(self, amount: Decimal, callback: Callable[[bool, str], None]) -> bool:
        """Initiate a charge. Callback receives (success, transaction_id_or_error)."""
        pass
    
    @abstractmethod
    def refund(self, transaction_id: str, amount: Decimal, callback: Callable[[bool, str], None]) -> bool:
        """Initiate a refund."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if terminal is connected and ready."""
        pass
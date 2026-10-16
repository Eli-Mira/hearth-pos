"""Fake hardware adapters for development and testing."""
from __future__ import annotations

import time
import threading
from decimal import Decimal
from typing import Callable, List, Optional

from app.hardware.interfaces import (
    ReceiptPrinter, KitchenPrinter, CashDrawer, BarcodeScanner, PaymentTerminal,
    ReceiptData, KitchenTicketData
)
from app.config import settings


class FakeReceiptPrinter(ReceiptPrinter):
    """In-memory receipt printer for development."""
    
    def __init__(self):
        self._last_receipt: Optional[ReceiptData] = None
        self._printed_receipts: List[ReceiptData] = []
        self._available = True
    
    def print_receipt(self, data: ReceiptData) -> bool:
        self._last_receipt = data
        self._printed_receipts.append(data)
        print(f"[FAKE RECEIPT] Order #{data.order_id} - Total: ${data.total}")
        return True
    
    def is_available(self) -> bool:
        return self._available
    
    def get_last_receipt(self) -> Optional[ReceiptData]:
        return self._last_receipt
    
    def get_all_receipts(self) -> List[ReceiptData]:
        return list(self._printed_receipts)
    
    def clear(self) -> None:
        self._last_receipt = None
        self._printed_receipts.clear()
    
    def set_available(self, available: bool) -> None:
        self._available = available


class FakeKitchenPrinter(KitchenPrinter):
    """In-memory kitchen printer for development."""
    
    def __init__(self):
        self._last_ticket: Optional[KitchenTicketData] = None
        self._printed_tickets: List[KitchenTicketData] = []
        self._available = True
    
    def print_ticket(self, data: KitchenTicketData) -> bool:
        self._last_ticket = data
        self._printed_tickets.append(data)
        print(f"[FAKE KITCHEN] Order #{data.order_id} ({data.order_type}) - {len(data.items)} items")
        return True
    
    def is_available(self) -> bool:
        return self._available
    
    def get_last_ticket(self) -> Optional[KitchenTicketData]:
        return self._last_ticket
    
    def get_all_tickets(self) -> List[KitchenTicketData]:
        return list(self._printed_tickets)
    
    def clear(self) -> None:
        self._last_ticket = None
        self._printed_tickets.clear()
    
    def set_available(self, available: bool) -> None:
        self._available = available


class FakeCashDrawer(CashDrawer):
    """In-memory cash drawer for development."""
    
    def __init__(self):
        self._open_count = 0
        self._last_opened: Optional[float] = None
        self._available = True
    
    def open(self) -> bool:
        self._open_count += 1
        self._last_opened = time.time()
        print(f"[FAKE DRAWER] Drawer opened (count: {self._open_count})")
        return True
    
    def is_available(self) -> bool:
        return self._available
    
    def get_open_count(self) -> int:
        return self._open_count
    
    def get_last_opened(self) -> Optional[float]:
        return self._last_opened
    
    def set_available(self, available: bool) -> None:
        self._available = available


class FakeBarcodeScanner(BarcodeScanner):
    """Simulated barcode scanner for development."""
    
    def __init__(self):
        self._callback: Optional[Callable[[str], None]] = None
        self._scanning = False
        self._available = True
    
    def start_scanning(self, callback: Callable[[str], None]) -> bool:
        self._callback = callback
        self._scanning = True
        return True
    
    def stop_scanning(self) -> None:
        self._callback = None
        self._scanning = False
    
    def is_available(self) -> bool:
        return self._available
    
    def simulate_scan(self, code: str) -> None:
        """Simulate a barcode scan for testing."""
        if self._callback and self._scanning:
            self._callback(code)
    
    def set_available(self, available: bool) -> None:
        self._available = available


class FakePaymentTerminal(PaymentTerminal):
    """Simulated payment terminal for development (always approves)."""
    
    def __init__(self):
        self._available = True
        self._last_transaction_id = None
    
    def charge(self, amount: Decimal, callback: Callable[[bool, str], None]) -> bool:
        # Simulate network delay
        def delayed_response():
            time.sleep(0.5)
            txn_id = f"TXN_{int(time.time() * 1000)}"
            self._last_transaction_id = txn_id
            callback(True, txn_id)
        
        threading.Thread(target=delayed_response, daemon=True).start()
        return True
    
    def refund(self, transaction_id: str, amount: Decimal, callback: Callable[[bool, str], None]) -> bool:
        def delayed_response():
            time.sleep(0.5)
            callback(True, f"REFUND_{transaction_id}")
        
        threading.Thread(target=delayed_response, daemon=True).start()
        return True
    
    def is_available(self) -> bool:
        return self._available
    
    def set_available(self, available: bool) -> None:
        self._available = available


# Global instances for easy access in development
fake_receipt_printer = FakeReceiptPrinter()
fake_kitchen_printer = FakeKitchenPrinter()
fake_cash_drawer = FakeCashDrawer()
fake_barcode_scanner = FakeBarcodeScanner()
fake_payment_terminal = FakePaymentTerminal()
"""ESC/POS hardware adapters for real printers and cash drawers."""
from __future__ import annotations

import socket
import time
from decimal import Decimal
from typing import Optional, List

from app.hardware.interfaces import (
    ReceiptPrinter, KitchenPrinter, CashDrawer,
    ReceiptData, KitchenTicketData
)
from app.config import settings


class EscposReceiptPrinter(ReceiptPrinter):
    """ESC/POS receipt printer over TCP (network)."""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or settings.receipt_printer_host
        self.port = port or settings.receipt_printer_port
        self._printer = None
        self._connected = False
    
    def _connect(self) -> bool:
        if not self.host:
            return False
        try:
            from escpos.printer import Network
            self._printer = Network(self.host, self.port)
            self._connected = True
            return True
        except Exception as e:
            print(f"[ESC/POS] Failed to connect to receipt printer: {e}")
            self._printer = None
            self._connected = False
            return False
    
    def _ensure_connected(self) -> bool:
        """Ensure printer is connected; reconnect if needed."""
        if not self._connected:
            return self._connect()
        return True
    
    def print_receipt(self, data: ReceiptData) -> bool:
        if not self._ensure_connected():
            return False
        
        try:
            p = self._printer
            
            # Header
            p.set(align='center', bold=True, height=2, width=2)
            p.text(f"{data.venue_name}\n")
            p.set(align='center', bold=False, height=1, width=1)
            p.text(f"{data.order_type.replace('_', ' ').title()}")
            if data.table_number:
                p.text(f" - Table {data.table_number}")
            p.text("\n")
            p.text(f"Server: {data.server_name}\n")
            p.text(f"Time: {data.timestamp}\n")
            p.text("-" * 32 + "\n")
            
            # Items
            for item in data.items:
                if item.voided:
                    p.set(bold=True)
                    p.text(f"VOID: {item.name} x{item.qty}\n")
                    p.set(bold=False)
                else:
                    p.set(align='left')
                    p.text(f"{item.name} x{item.qty}\n")
                    for mod in item.modifiers:
                        p.text(f"  + {mod}\n")
                    p.set(align='right')
                    p.text(f"${item.line_total:.2f}\n")
                p.text("\n")
            
            # Totals
            p.text("-" * 32 + "\n")
            p.set(align='right')
            p.text(f"Subtotal: ${data.subtotal:.2f}\n")
            p.text(f"Tax:      ${data.tax_total:.2f}\n")
            p.set(bold=True)
            p.text(f"TOTAL:    ${data.total:.2f}\n")
            p.set(bold=False)
            
            # Payments
            if data.payments:
                p.text("-" * 32 + "\n")
                for pay in data.payments:
                    p.text(f"{pay.payment_type.replace('_', ' ').title()}: ${pay.amount:.2f}\n")
                    if pay.payment_type == "cash" and pay.tendered > 0:
                        p.text(f"  Tendered: ${pay.tendered:.2f}\n")
                        p.text(f"  Change:   ${pay.change:.2f}\n")
            
            # Footer
            p.text("-" * 32 + "\n")
            p.set(align='center')
            p.text(f"{data.footer_text}\n\n\n")
            
            # Cut paper
            p.cut()
            return True
            
        except Exception as e:
            print(f"[ESC/POS] Receipt print failed: {e}")
            self._connected = False
            return False
    
    def is_available(self) -> bool:
        """Return True if printer is connected; attempt reconnect if not."""
        return self._ensure_connected()


class EscposKitchenPrinter(KitchenPrinter):
    """ESC/POS kitchen printer over TCP (network)."""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or settings.kitchen_printer_host
        self.port = port or settings.kitchen_printer_port
        self._printer = None
        self._connected = False
    
    def _connect(self) -> bool:
        if not self.host:
            return False
        try:
            from escpos.printer import Network
            self._printer = Network(self.host, self.port)
            self._connected = True
            return True
        except Exception as e:
            print(f"[ESC/POS] Failed to connect to kitchen printer: {e}")
            self._printer = None
            self._connected = False
            return False
    
    def _ensure_connected(self) -> bool:
        """Ensure printer is connected; reconnect if needed."""
        if not self._connected:
            return self._connect()
        return True
    
    def print_ticket(self, data: KitchenTicketData) -> bool:
        if not self._ensure_connected():
            return False
        
        try:
            p = self._printer
            
            # Kitchen ticket header - large and clear
            p.set(align='center', bold=True, height=3, width=3)
            p.text("KITCHEN ORDER\n")
            p.set(align='left', bold=False, height=1, width=1)
            p.text("-" * 40 + "\n")
            p.set(bold=True)
            p.text(f"Order #{data.order_id}  ({data.order_type.upper()})")
            if data.table_number:
                p.text(f"  TABLE {data.table_number}")
            p.text("\n")
            p.text(f"Server: {data.server_name}\n")
            p.text(f"Time: {data.timestamp}\n")
            p.text("-" * 40 + "\n")
            
            # Items
            for item in data.items:
                p.set(bold=True, height=2, width=2)
                p.text(f"{item.qty}x {item.name}\n")
                p.set(bold=False, height=1, width=1)
                for mod in item.modifiers:
                    p.text(f"    + {mod}\n")
                if item.notes:
                    p.text(f"    NOTE: {item.notes}\n")
                p.text("\n")
            
            p.text("-" * 40 + "\n")
            p.text(f"Items: {len(data.items)}\n\n\n")
            p.cut()
            return True
            
        except Exception as e:
            print(f"[ESC/POS] Kitchen ticket print failed: {e}")
            self._connected = False
            return False
    
    def is_available(self) -> bool:
        if not self._connected:
            return self._connect()
        return self._connected


class EscposCashDrawer(CashDrawer):
    """Cash drawer controlled via ESC/POS printer kick command."""
    
    def __init__(self, receipt_printer: EscposReceiptPrinter = None):
        self.receipt_printer = receipt_printer
        self._available = False
    
    def open(self) -> bool:
        # Cash drawer is typically kicked via the receipt printer
        # ESC/POS kick command: ESC p m t1 t2 (m=0 for pin 2, m=1 for pin 5)
        try:
            if self.receipt_printer and self.receipt_printer._printer:
                # Kick drawer on pin 2 (default), 100ms pulse
                self.receipt_printer._printer._raw(b'\x1b\x70\x00\x19\x64')
                print("[ESC/POS] Cash drawer kick sent")
                return True
            return False
        except Exception as e:
            print(f"[ESC/POS] Cash drawer kick failed: {e}")
            return False
    
    def is_available(self) -> bool:
        return self._available
    
    def set_available(self, available: bool) -> None:
        self._available = available
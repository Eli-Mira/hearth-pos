"""Money handling utilities using Decimal for precision."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext

# Set precision high enough for all calculations
getcontext().prec = 28

# Quantization constants
CENTS = Decimal("0.01")
ZERO = Decimal("0.00")


def quantize(amount: Decimal) -> Decimal:
    """Quantize to 2 decimal places using banker's rounding (ROUND_HALF_UP)."""
    return amount.quantize(CENTS, rounding=ROUND_HALF_UP)


def add(*amounts: Decimal) -> Decimal:
    """Add multiple decimal amounts with quantization only on final result."""
    return quantize(sum(amounts, ZERO))


def subtract(a: Decimal, b: Decimal) -> Decimal:
    """Subtract b from a with quantization."""
    return quantize(quantize(a) - quantize(b))


def multiply(amount: Decimal, factor: int | Decimal) -> Decimal:
    """Multiply amount by factor with quantization."""
    return quantize(quantize(amount) * quantize(Decimal(str(factor))))


def divide(amount: Decimal, divisor: int | Decimal) -> Decimal:
    """Divide amount by divisor with quantization."""
    return quantize(quantize(amount) / quantize(Decimal(str(divisor))))


def calculate_tax(base: Decimal, rate_bps: int) -> Decimal:
    """Calculate tax amount from base price and rate in basis points."""
    rate = Decimal(rate_bps) / Decimal("10000")
    return quantize(base * rate)


def decompose_tax_inclusive(price: Decimal, rate_bps: int) -> tuple[Decimal, Decimal]:
    """Decompose tax-inclusive price into (base, tax)."""
    rate = Decimal(rate_bps) / Decimal("10000")
    base = quantize(price / (Decimal("1") + rate))
    tax = quantize(price - base)
    return base, tax


def calculate_split(total: Decimal, ways: int) -> list[Decimal]:
    """Split total evenly across ways, distributing remainder to last payer."""
    if ways <= 0:
        raise ValueError("Split ways must be positive")
    if ways == 1:
        return [quantize(total)]
    
    base_split = quantize(total / ways)
    remainder = quantize(total - (base_split * ways))
    
    splits = [base_split] * ways
    if remainder != ZERO:
        splits[-1] = quantize(splits[-1] + remainder)
    
    return splits


def calculate_change(tendered: Decimal, total: Decimal) -> Decimal:
    """Calculate change due (never negative)."""
    diff = quantize(tendered - total)
    return max(diff, ZERO)


def format_money(amount: Decimal) -> str:
    """Format decimal as currency string."""
    return f"{quantize(amount):.2f}"
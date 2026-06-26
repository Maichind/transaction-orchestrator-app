from enum import Enum


class TransactionStatus(str, Enum):
    """Supported transaction states."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class TransactionType(str, Enum):
    """Supported transaction types."""
    PAYMENT = "payment"
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"

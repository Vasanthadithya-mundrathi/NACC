"""
Node Pairing Logic
Generates and verifies 6-digit pairing codes for secure node initialization.
"""

import secrets
import string
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class PairingSession:
    code: str
    node_id: str
    created_at: float
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

def generate_pairing_code(length: int = 6) -> str:
    """Generate a secure random numeric code."""
    alphabet = string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_session(node_id: str, ttl_seconds: int = 300) -> PairingSession:
    """Create a new pairing session with a unique code."""
    code = generate_pairing_code()
    now = time.time()
    return PairingSession(
        code=code,
        node_id=node_id,
        created_at=now,
        expires_at=now + ttl_seconds
    )

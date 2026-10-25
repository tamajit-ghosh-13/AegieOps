"""Immutable Incident Ledger with Cryptographic Hash Chaining (AegisOps Sprint 4).

Append-only, cryptographically auditable timeline storing every state transition,
telemetry assertion, operator approval, and executed operational command.
Chained with SHA-256 Merkle hashes for SOC2/ISO 27001 tamper verification.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from audit.crypto_ledger import (
    CryptographicIncidentLedger,
    CryptographicLedgerEntry,
    GENESIS_HASH,
    get_crypto_ledger,
)


class LedgerEntry(BaseModel):
    ledger_id: int
    incident_id: str
    event_type: str
    actor: str
    payload: dict[str, Any] = Field(default_factory=dict)
    prev_hash: str = GENESIS_HASH
    current_hash: str = ""
    signature: str = ""
    created_at: str


class IncidentLedger:
    def __init__(self, conn_str: str | None = None) -> None:
        self._crypto_ledger = CryptographicIncidentLedger(conn_str=conn_str)

    def record_event(
        self,
        incident_id: str,
        event_type: str,
        payload: dict[str, Any] | BaseModel,
        actor: str = "aegis-system",
    ) -> LedgerEntry:
        """Append an immutable, cryptographically chained event to the ledger."""
        c_entry = self._crypto_ledger.record_event(
            incident_id=incident_id,
            event_type=event_type,
            payload=payload,
            actor=actor,
        )
        return LedgerEntry(
            ledger_id=c_entry.ledger_id,
            incident_id=c_entry.incident_id,
            event_type=c_entry.event_type,
            actor=c_entry.actor,
            payload=c_entry.payload,
            prev_hash=c_entry.prev_hash,
            current_hash=c_entry.current_hash,
            signature=c_entry.signature,
            created_at=c_entry.created_at,
        )

    def get_all_entries(self, limit: int = 100) -> list[LedgerEntry]:
        """Fetch recent cryptographic audit entries across all incidents."""
        entries = self._crypto_ledger.get_all_entries(limit=limit)
        return [
            LedgerEntry(
                ledger_id=e.ledger_id,
                incident_id=e.incident_id,
                event_type=e.event_type,
                actor=e.actor,
                payload=e.payload,
                prev_hash=e.prev_hash,
                current_hash=e.current_hash,
                signature=e.signature,
                created_at=e.created_at,
            )
            for e in entries
        ]

    def get_audit_trail(self, incident_id: str) -> list[LedgerEntry]:
        """Fetch the full sequential cryptographic audit trail for an incident."""
        trail = self._crypto_ledger.get_audit_trail(incident_id)
        return [
            LedgerEntry(
                ledger_id=e.ledger_id,
                incident_id=e.incident_id,
                event_type=e.event_type,
                actor=e.actor,
                payload=e.payload,
                prev_hash=e.prev_hash,
                current_hash=e.current_hash,
                signature=e.signature,
                created_at=e.created_at,
            )
            for e in trail
        ]

    def verify_chain_integrity(self, incident_id: str | None = None) -> tuple[bool, str, list[int]]:
        """Verify the cryptographic hash-chain across all entries."""
        return self._crypto_ledger.verify_chain_integrity(incident_id)


_LEDGER: IncidentLedger | None = None


def get_incident_ledger() -> IncidentLedger:
    global _LEDGER
    if _LEDGER is None:
        _LEDGER = IncidentLedger()
    return _LEDGER

"""
Minimalistische Referenzimplementierung der LAP-Kernprimitive für den Unterricht.

WICHTIG: Es gibt (Stand Juli 2026) kein offizielles, verbreitetes LAP-SDK -
das Protokoll stammt aus einer sehr jungen Forschungsarbeit (Zhu et al.,
"LAP: An Agent-to-Instrument Protocol for Autonomous Science", Juni 2026,
arXiv:2606.03755). Diese Datei bildet die vier zentralen Primitive aus dem
Paper nachvollziehbar in Python nach:

  - InstrumentCard    signierte* Fähigkeits- und Grenzwertbeschreibung
  - Reservation        exklusive Belegung des Instruments
  - Safety-Fence        Bestätigungs-Token vor gefährlichen Operationen
  - MeasurementResult   physikalisch typisiertes, unsicherheitsbehaftetes Ergebnis

  (*Signierung ist hier zugunsten der Einfachheit weggelassen.)

Das ist KEINE zertifizierte Implementierung des tatsächlichen Wire-Protokolls,
sondern eine didaktische Annäherung, um die Konzepte greifbar zu machen.
"""
from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class InstrumentCard:
    name: str
    description: str
    capabilities: list[str]
    physical_limits: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "physical_limits": self.physical_limits,
        }


@dataclass
class MeasurementResult:
    value: float
    unit: str
    uncertainty: float
    quantity: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "unit": self.unit,
            "uncertainty": self.uncertainty,
            "quantity": self.quantity,
            "timestamp": self.timestamp,
        }


class ReservationDenied(Exception):
    pass


class SafetyFenceRequired(Exception):
    """Wird geworfen, wenn eine gefährliche/irreversible Aktion erst nach
    expliziter Bestätigung ausgeführt werden darf."""

    def __init__(self, token: str):
        self.token = token
        super().__init__(f"Bestätigung erforderlich, Token: {token}")


class Instrument:
    """Basisklasse für einen LAP-Instrument-Agenten.

    Kapselt Reservation und Safety-Fence-Handshake, damit konkrete
    Instrument-Agenten (Wartung, Nachschub, ...) nur noch ihre eigentliche
    physische Aktion und die resultierende Messung implementieren müssen.
    """

    def __init__(self, card: InstrumentCard, hazardous_actions: set[str] | None = None):
        self.card = card
        self.hazardous_actions = hazardous_actions or set()
        self._reserved_by: str | None = None
        self._reserved_until: float = 0.0
        self._pending_tokens: dict[str, tuple[str, dict]] = {}

    # --- Reservation ------------------------------------------------------
    def reserve(self, requester: str, duration_seconds: int = 120) -> None:
        if self._reserved_by and time.time() < self._reserved_until:
            raise ReservationDenied(f"Instrument bereits reserviert von {self._reserved_by}")
        self._reserved_by = requester
        self._reserved_until = time.time() + duration_seconds

    def release(self, requester: str) -> None:
        if self._reserved_by == requester:
            self._reserved_by = None

    def _check_reserved(self, requester: str) -> None:
        if self._reserved_by != requester or time.time() > self._reserved_until:
            raise ReservationDenied("Keine gültige Reservierung für diese Aktion.")

    # --- Safety-Fence -------------------------------------------------------
    def _issue_token(self, action: str, params: dict) -> str:
        raw = f"{action}:{params}:{secrets.token_hex(8)}"
        token = hashlib.sha256(raw.encode()).hexdigest()[:16]
        self._pending_tokens[token] = (action, params)
        return token

    def request_action(self, requester: str, action: str, params: dict) -> MeasurementResult:
        """Führt eine Aktion aus. Bei gefährlichen Aktionen wird stattdessen
        SafetyFenceRequired geworfen - der Aufrufer muss dann confirm_action
        mit dem Token erneut aufrufen."""
        self._check_reserved(requester)
        if action in self.hazardous_actions:
            raise SafetyFenceRequired(self._issue_token(action, params))
        return self._execute(action, params)

    def confirm_action(self, requester: str, token: str) -> MeasurementResult:
        self._check_reserved(requester)
        if token not in self._pending_tokens:
            raise ValueError("Unbekannter oder abgelaufener Bestätigungs-Token.")
        action, params = self._pending_tokens.pop(token)
        return self._execute(action, params)

    def _execute(self, action: str, params: dict) -> MeasurementResult:
        raise NotImplementedError

"""Small fail-closed gateway and local issuer. HMAC is a prototype choice.

The signing secret exists only in the coordinator. No secret/token is sent to
shadow processes. An epoch accepts one complete signal plan, not per-tick calls.
"""
import hashlib
import hmac
import json
import secrets
import threading
import time

from .contracts import ACTIONS, canonical


class TokenIssuer:
    def __init__(self):
        self._key = secrets.token_bytes(32)

    def issue(self, branch, expires):
        claims = {"branch_id": branch.branch_id, "experiment_id": branch.experiment_id,
                  "epoch": branch.epoch, "role": branch.role, "site_id": "J1",
                  "action": branch.action, "exp": expires, "nonce": secrets.token_hex(16)}
        payload = canonical(claims)
        return payload.hex() + "." + hmac.new(self._key, payload, hashlib.sha256).hexdigest()

    def verify(self, token):
        try:
            encoded, signature = token.split(".")
            payload = bytes.fromhex(encoded)
            expected = hmac.new(self._key, payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError("signature mismatch")
            claims = json.loads(payload)
            if not isinstance(claims, dict):
                raise ValueError("claims must be an object")
            return claims
        except (ValueError, TypeError, AttributeError) as exc:
            raise PermissionError("invalid token") from exc


class ActuatorGateway:
    def __init__(self, issuer, world, capability, experiment_id):
        self.issuer, self.world, self.capability = issuer, world, capability
        self.experiment_id = experiment_id
        self.current_epoch = -1
        self.owner = None
        self._claimed = False
        self._lock = threading.Lock()
        self.audit = []

    def open_epoch(self, epoch, production_branch_id):
        with self._lock:
            if epoch <= self.current_epoch:
                raise ValueError("epochs cannot be reused")
            self.current_epoch, self.owner, self._claimed = epoch, production_branch_id, False

    def actuate(self, token, action):
        with self._lock:
            claims = {}
            try:
                claims = self.issuer.verify(token)
                if claims.get("role") != "PRODUCTION":
                    raise PermissionError("role denied")
                if (claims.get("epoch") != self.current_epoch or
                    claims.get("experiment_id") != self.experiment_id or claims.get("site_id") != "J1" or
                    claims.get("branch_id") != self.owner):
                    raise PermissionError("identity/epoch mismatch")
                if type(claims.get("exp")) not in (float, int) or not time.time() < claims["exp"]:
                    raise PermissionError("expired token")
                if action not in ACTIONS or action != claims.get("action"):
                    raise PermissionError("invalid or unbound action")
                if self._claimed:
                    raise PermissionError("epoch already actuated")
                self._claimed = True  # Fail closed even if the downstream call fails.
                correlation = f"{self.experiment_id}:{self.current_epoch}:{self.owner}"
                self.world.apply_plan(action, self.capability, correlation)
                self.audit.append(self._event(claims, "ALLOWED", "authorized", action))
            except PermissionError as exc:
                self.audit.append(self._event(claims, "BLOCKED", str(exc), action))
                raise

    def _event(self, claims, result, reason, action):
        return {"experiment_id": self.experiment_id, "epoch": self.current_epoch,
                "branch_id": claims.get("branch_id"), "role": claims.get("role"),
                "component": "actuator_gateway", "layer": "L2", "result": result,
                "reason": reason, "action": action}


class VirtualActuator:
    def __init__(self, branch, limit):
        if branch.role not in ("SHADOW", "MIRROR"):
            raise PermissionError("virtual actuator requires non-production identity")
        self.branch, self.limit, self.entries = branch, limit, []

    def actuate(self, action, sequence):
        if action not in ACTIONS or len(self.entries) >= self.limit:
            raise ValueError("invalid virtual action or buffer overflow")
        self.entries.append({"experiment_id": self.branch.experiment_id,
                             "branch_id": self.branch.branch_id, "role": self.branch.role,
                             "snapshot_id": self.branch.parent_snapshot_id,
                             "sequence_number": sequence, "action": action, "component": "virtual_actuator",
                             "result": "VIRTUAL_ONLY", "would_have_targeted": "authoritative_test_world"})

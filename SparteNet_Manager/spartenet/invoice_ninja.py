"""Direkte Invoice-Ninja-Integration fuer den SparteNet Manager.

Das Modul verwendet nur die Python-Standardbibliothek und kapselt:
- Invoice-Ninja-API-Zugriffe (Clients, Produkte, Rechnungen, Zahlungen)
- idempotente Kunden- und Rechnungserstellung
- persistente Outbox mit Wiederholungen
- deduplizierte Verarbeitung eingehender Invoice-Ninja-Webhooks
- Uebergabe bestaetigter Zahlungen an die SparteNet-Automation

Die Einbindung in den HTTP-Router des Managers erfolgt ueber
``InvoiceNinjaIntegration.handle_webhook``. Das Modul startet selbst keinen
Webserver und importiert absichtlich keine SparteNet-internen Module.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import random
import re
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional

LOG = logging.getLogger(__name__)
JsonDict = dict[str, Any]
EventCallback = Callable[[str, JsonDict], Any]


class InvoiceNinjaError(RuntimeError):
    """Basisklasse fuer Integrationsfehler."""


class InvoiceNinjaConfigError(InvoiceNinjaError):
    """Fehlerhafte oder unvollstaendige Konfiguration."""


class InvoiceNinjaHTTPError(InvoiceNinjaError):
    """HTTP-Fehler der Invoice-Ninja-API."""

    def __init__(self, status: int, message: str, body: Any = None):
        super().__init__(f"Invoice Ninja HTTP {status}: {message}")
        self.status = status
        self.body = body


class InvoiceNinjaTemporaryError(InvoiceNinjaError):
    """Wiederholbarer Netzwerk- oder Serverfehler."""


class InvoiceNinjaValidationError(InvoiceNinjaError):
    """Ungueltige Integrations- oder Fachdaten."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _decimal(value: Any, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise InvoiceNinjaValidationError(f"{field_name} ist keine gueltige Zahl") from exc
    if not result.is_finite():
        raise InvoiceNinjaValidationError(f"{field_name} ist nicht endlich")
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _money(value: Any) -> str:
    return format(_decimal(value, "Betrag"), ".2f")


def _nonempty(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise InvoiceNinjaValidationError(f"{field_name} fehlt")
    return text


def _safe_json(raw: bytes) -> Any:
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"raw": raw.decode("utf-8", "replace")}


def _data(value: Any) -> Any:
    """Entfernt die uebliche Invoice-Ninja-Huelle {data: ...}."""
    if isinstance(value, dict) and "data" in value:
        return value["data"]
    return value


def _first(items: Any) -> Optional[JsonDict]:
    items = _data(items)
    if isinstance(items, list):
        return next((x for x in items if isinstance(x, dict)), None)
    return items if isinstance(items, dict) else None


def _atomic_json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def read_secret(path: str | os.PathLike[str]) -> str:
    try:
        value = Path(path).read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise InvoiceNinjaConfigError(f"Geheimnisdatei nicht lesbar: {path}") from exc
    if not value:
        raise InvoiceNinjaConfigError(f"Geheimnisdatei ist leer: {path}")
    return value


@dataclass(frozen=True)
class InvoiceNinjaConfig:
    base_url: str
    token: str
    state_dir: Path
    timeout: float = 20.0
    retry_count: int = 2
    webhook_secret: str = ""
    webhook_signature_header: str = "X-SparteNet-Signature"
    user_agent: str = "SparteNet-Manager/InvoiceNinja"
    verify_tls: bool = True
    send_invoice: bool = False
    mark_sent: bool = False
    currency_id: str = ""
    default_terms: str = ""

    @classmethod
    def from_env(cls) -> "InvoiceNinjaConfig":
        base_url = os.environ.get("SPARTENET_INVOICE_NINJA_URL", "").strip()
        token = os.environ.get("SPARTENET_INVOICE_NINJA_TOKEN", "").strip()
        token_file = os.environ.get("SPARTENET_INVOICE_NINJA_TOKEN_FILE", "").strip()
        secret = os.environ.get("SPARTENET_INVOICE_NINJA_WEBHOOK_SECRET", "").strip()
        secret_file = os.environ.get("SPARTENET_INVOICE_NINJA_WEBHOOK_SECRET_FILE", "").strip()
        if token_file:
            token = read_secret(token_file)
        if secret_file:
            secret = read_secret(secret_file)
        return cls(
            base_url=base_url,
            token=token,
            state_dir=Path(os.environ.get("SPARTENET_INVOICE_NINJA_STATE_DIR", "/var/lib/spartenet/invoice-ninja")),
            timeout=float(os.environ.get("SPARTENET_INVOICE_NINJA_TIMEOUT", "20")),
            retry_count=int(os.environ.get("SPARTENET_INVOICE_NINJA_RETRY_COUNT", "2")),
            webhook_secret=secret,
            verify_tls=os.environ.get("SPARTENET_INVOICE_NINJA_VERIFY_TLS", "1") not in {"0", "false", "False"},
            send_invoice=os.environ.get("SPARTENET_INVOICE_NINJA_SEND", "0") in {"1", "true", "True"},
            mark_sent=os.environ.get("SPARTENET_INVOICE_NINJA_MARK_SENT", "0") in {"1", "true", "True"},
            currency_id=os.environ.get("SPARTENET_INVOICE_NINJA_CURRENCY_ID", "").strip(),
            default_terms=os.environ.get("SPARTENET_INVOICE_NINJA_TERMS", "").strip(),
        ).validated()

    def validated(self) -> "InvoiceNinjaConfig":
        if not re.match(r"^https?://[^\s]+$", self.base_url):
            raise InvoiceNinjaConfigError("SPARTENET_INVOICE_NINJA_URL ist ungueltig")
        if not self.token:
            raise InvoiceNinjaConfigError("Invoice-Ninja-API-Token fehlt")
        if self.timeout <= 0:
            raise InvoiceNinjaConfigError("timeout muss groesser als 0 sein")
        return self


class InvoiceNinjaClient:
    """Kleiner, testbarer Client fuer die Invoice-Ninja-v5-REST-API."""

    def __init__(self, config: InvoiceNinjaConfig, opener: Any = None):
        self.config = config.validated()
        context = ssl.create_default_context()
        if not config.verify_tls:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        self._opener = opener or urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))

    def request(
        self,
        method: str,
        path: str,
        payload: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        idempotency_key: str = "",
    ) -> Any:
        url = f"{self.config.base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
        q = {k: v for k, v in (query or {}).items() if v not in (None, "")}
        if q:
            url += "?" + urllib.parse.urlencode(q, doseq=True)
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "X-API-TOKEN": self.config.token,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
            "User-Agent": self.config.user_agent,
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        attempts = max(1, self.config.retry_count + 1)
        for attempt in range(attempts):
            req = urllib.request.Request(url, data=body, method=method.upper(), headers=headers)
            try:
                with self._opener.open(req, timeout=self.config.timeout) as response:
                    return _safe_json(response.read())
            except urllib.error.HTTPError as exc:
                response_body = _safe_json(exc.read())
                message = response_body.get("message") if isinstance(response_body, dict) else str(response_body)
                if exc.code in {408, 425, 429, 500, 502, 503, 504} and attempt + 1 < attempts:
                    self._sleep(attempt, exc.headers.get("Retry-After"))
                    continue
                raise InvoiceNinjaHTTPError(exc.code, str(message or exc.reason), response_body) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt + 1 < attempts:
                    self._sleep(attempt)
                    continue
                raise InvoiceNinjaTemporaryError(f"Invoice Ninja nicht erreichbar: {exc}") from exc
        raise InvoiceNinjaTemporaryError("Invoice-Ninja-Aufruf fehlgeschlagen")

    @staticmethod
    def _sleep(attempt: int, retry_after: Optional[str] = None) -> None:
        try:
            seconds = min(30.0, float(retry_after)) if retry_after else min(8.0, 0.5 * (2 ** attempt) + random.random() / 4)
        except ValueError:
            seconds = 1.0
        time.sleep(seconds)

    def status(self) -> JsonDict:
        result = self.request("GET", "clients", query={"per_page": 1})
        return {"ok": True, "antwort": result}

    def list_clients(self, email: str = "", per_page: int = 20) -> Any:
        return self.request("GET", "clients", query={"email": email, "per_page": per_page})

    def create_client(self, payload: Mapping[str, Any], idempotency_key: str = "") -> JsonDict:
        return _first(self.request("POST", "clients", payload, idempotency_key=idempotency_key)) or {}

    def show_client(self, client_id: str) -> JsonDict:
        return _first(self.request("GET", f"clients/{client_id}")) or {}

    def update_client(self, client_id: str, payload: Mapping[str, Any]) -> JsonDict:
        return _first(self.request("PUT", f"clients/{client_id}", payload)) or {}

    def list_products(self, product_key: str = "", per_page: int = 100) -> Any:
        return self.request("GET", "products", query={"product_key": product_key, "per_page": per_page})

    def list_invoices(self, client_id: str = "", invoice_number: str = "", per_page: int = 100) -> Any:
        return self.request("GET", "invoices", query={"client_id": client_id, "invoice_number": invoice_number, "per_page": per_page})

    def show_invoice(self, invoice_id: str) -> JsonDict:
        return _first(self.request("GET", f"invoices/{invoice_id}")) or {}

    def create_invoice(self, payload: Mapping[str, Any], send: bool = False, mark_sent: bool = False, idempotency_key: str = "") -> JsonDict:
        query = {"send_email": "true" if send else "false", "mark_sent": "true" if mark_sent else "false"}
        return _first(self.request("POST", "invoices", payload, query=query, idempotency_key=idempotency_key)) or {}

    def show_payment(self, payment_id: str) -> JsonDict:
        return _first(self.request("GET", f"payments/{payment_id}")) or {}


@dataclass
class JsonStore:
    path: Path
    default_factory: Callable[[], Any] = dict
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    def read(self) -> Any:
        with self._lock:
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                return self.default_factory()
            except (OSError, json.JSONDecodeError) as exc:
                raise InvoiceNinjaError(f"Statusdatei nicht lesbar: {self.path}") from exc

    def write(self, data: Any) -> None:
        with self._lock:
            _atomic_json_write(self.path, data)

    def update(self, callback: Callable[[Any], Any]) -> Any:
        with self._lock:
            data = self.read()
            result = callback(data)
            self.write(data)
            return result


@dataclass
class OutboxJob:
    id: str
    kind: str
    payload: JsonDict
    created_at: str = field(default_factory=_utc_now)
    status: str = "pending"
    attempts: int = 0
    next_attempt_at: float = 0.0
    last_error: str = ""
    result: JsonDict = field(default_factory=dict)


class PersistentOutbox:
    def __init__(self, path: Path):
        self.store = JsonStore(path, list)

    def enqueue(self, kind: str, payload: Mapping[str, Any], unique_key: str = "") -> OutboxJob:
        def change(rows: list[JsonDict]) -> OutboxJob:
            if unique_key:
                for row in rows:
                    if row.get("payload", {}).get("unique_key") == unique_key and row.get("status") in {"pending", "processing", "done"}:
                        return OutboxJob(**row)
            data = dict(payload)
            if unique_key:
                data["unique_key"] = unique_key
            job = OutboxJob(id=uuid.uuid4().hex, kind=kind, payload=data)
            rows.append(asdict(job))
            return job
        return self.store.update(change)

    def process(self, handlers: Mapping[str, Callable[[JsonDict], JsonDict]], limit: int = 20) -> list[JsonDict]:
        now = time.time()
        rows = self.store.read()
        selected = [r for r in rows if r.get("status") in {"pending", "retry"} and float(r.get("next_attempt_at") or 0) <= now][:limit]
        results: list[JsonDict] = []
        for row in selected:
            row["status"] = "processing"
            self.store.write(rows)
            try:
                handler = handlers[row["kind"]]
                result = handler(dict(row["payload"])) or {}
                row.update(status="done", result=result, last_error="", finished_at=_utc_now())
            except InvoiceNinjaValidationError as exc:
                row.update(status="failed", last_error=str(exc), finished_at=_utc_now())
            except Exception as exc:
                row["attempts"] = int(row.get("attempts") or 0) + 1
                row["status"] = "failed" if row["attempts"] >= 8 else "retry"
                row["next_attempt_at"] = time.time() + min(3600, 30 * (2 ** min(row["attempts"], 7)))
                row["last_error"] = str(exc)[:1000]
                LOG.exception("Invoice-Ninja-Outbox-Auftrag %s fehlgeschlagen", row.get("id"))
            self.store.write(rows)
            results.append(dict(row))
        return results


class InvoiceNinjaIntegration:
    def __init__(self, config: InvoiceNinjaConfig, event_callback: EventCallback, client: Optional[InvoiceNinjaClient] = None):
        self.config = config.validated()
        self.client = client or InvoiceNinjaClient(config)
        self.event_callback = event_callback
        self.mapping = JsonStore(config.state_dir / "mapping.json", dict)
        self.processed = JsonStore(config.state_dir / "processed_webhooks.json", dict)
        self.outbox = PersistentOutbox(config.state_dir / "outbox.json")

    @staticmethod
    def booking_key(sparte: str, parzelle: Any, period: str = "") -> str:
        sparte = re.sub(r"[^A-Za-z0-9_-]", "", _nonempty(sparte, "Sparte").upper())
        p = _nonempty(parzelle, "Parzelle")
        period = period or str(date.today().year)
        return f"SN-{sparte}-{p}-{period}"

    def ensure_client(self, member: Mapping[str, Any]) -> JsonDict:
        email = _nonempty(member.get("email"), "E-Mail")
        existing_id = str(member.get("invoice_ninja_client_id") or "")
        if existing_id:
            return self.client.show_client(existing_id)
        result = _data(self.client.list_clients(email=email))
        candidates = result if isinstance(result, list) else []
        exact = []
        for candidate in candidates:
            contacts = candidate.get("contacts") or ([candidate.get("contact")] if candidate.get("contact") else [])
            if any(str(c.get("email") or "").casefold() == email.casefold() for c in contacts if isinstance(c, dict)):
                exact.append(candidate)
        if len(exact) > 1:
            raise InvoiceNinjaValidationError(f"Mehrere Invoice-Ninja-Kunden mit E-Mail {email} gefunden")
        if exact:
            return exact[0]
        first_name = str(member.get("vorname") or "").strip()
        last_name = str(member.get("nachname") or "").strip()
        name = str(member.get("name") or f"{first_name} {last_name}").strip() or email
        payload: JsonDict = {
            "name": name,
            "contacts": [{"first_name": first_name, "last_name": last_name, "email": email, "phone": str(member.get("telefon") or "")}],
        }
        if self.config.currency_id:
            payload["currency_id"] = self.config.currency_id
        for key in ("address1", "address2", "city", "state", "postal_code", "country_id", "vat_number", "id_number"):
            if member.get(key) not in (None, ""):
                payload[key] = member[key]
        idem = "spartenet-client-" + hashlib.sha256(email.casefold().encode()).hexdigest()[:32]
        return self.client.create_client(payload, idempotency_key=idem)

    def invoice_payload(self, client_id: str, booking: Mapping[str, Any], tariff: Mapping[str, Any]) -> JsonDict:
        key = str(booking.get("booking_key") or self.booking_key(booking.get("sparte"), booking.get("parzelle"), str(booking.get("period") or "")))
        price = _money(tariff.get("preis"))
        tariff_name = _nonempty(booking.get("tarif") or tariff.get("name"), "Tarif")
        description = str(tariff.get("beschreibung") or f"SparteNet-Tarif {tariff_name}, Sparte {booking['sparte']}, Parzelle {booking['parzelle']}")
        item: JsonDict = {
            "product_key": str(tariff.get("product_key") or f"SPARTENET-{tariff_name.upper()}"),
            "notes": description,
            "quantity": float(_decimal(tariff.get("menge", 1), "Menge")),
            "cost": float(Decimal(price)),
        }
        for field_name in ("tax_name1", "tax_rate1", "tax_name2", "tax_rate2"):
            if tariff.get(field_name) not in (None, ""):
                item[field_name] = tariff[field_name]
        private = {
            "system": "spartenet",
            "booking_key": key,
            "sparte": booking["sparte"],
            "parzelle": booking["parzelle"],
            "tarif": tariff_name,
        }
        payload: JsonDict = {
            "client_id": client_id,
            "line_items": [item],
            "public_notes": str(booking.get("public_notes") or description),
            "private_notes": json.dumps(private, ensure_ascii=False, separators=(",", ":")),
            "custom_value1": str(booking["sparte"]),
            "custom_value2": str(booking["parzelle"]),
            "custom_value3": tariff_name,
            "custom_value4": key,
        }
        if self.config.default_terms:
            payload["terms"] = self.config.default_terms
        for field_name in ("date", "due_date", "po_number", "discount", "footer", "terms"):
            if booking.get(field_name) not in (None, ""):
                payload[field_name] = booking[field_name]
        return payload

    def create_booking_invoice(self, booking: Mapping[str, Any], member: Mapping[str, Any], tariff: Mapping[str, Any]) -> JsonDict:
        key = str(booking.get("booking_key") or self.booking_key(booking.get("sparte"), booking.get("parzelle"), str(booking.get("period") or "")))
        mappings = self.mapping.read()
        if key in mappings and mappings[key].get("invoice_id"):
            invoice = self.client.show_invoice(mappings[key]["invoice_id"])
            return {"created": False, "booking_key": key, "client": {}, "invoice": invoice}
        client = self.ensure_client(member)
        client_id = _nonempty(client.get("id"), "Invoice-Ninja-Kunden-ID")
        invoice = self.client.create_invoice(
            self.invoice_payload(client_id, {**booking, "booking_key": key}, tariff),
            send=self.config.send_invoice,
            mark_sent=self.config.mark_sent,
            idempotency_key="spartenet-invoice-" + hashlib.sha256(key.encode()).hexdigest()[:32],
        )
        invoice_id = _nonempty(invoice.get("id"), "Invoice-Ninja-Rechnungs-ID")
        mapping = {
            "booking_key": key,
            "sparte": booking["sparte"],
            "parzelle": booking["parzelle"],
            "tarif": booking.get("tarif") or tariff.get("name"),
            "email": member.get("email", ""),
            "name": member.get("name") or f"{member.get('vorname', '')} {member.get('nachname', '')}".strip(),
            "client_id": client_id,
            "invoice_id": invoice_id,
            "invoice_number": invoice.get("number", ""),
            "amount": invoice.get("amount", tariff.get("preis", "")),
            "created_at": _utc_now(),
        }
        mappings[key] = mapping
        self.mapping.write(mappings)
        return {"created": True, "booking_key": key, "client": client, "invoice": invoice, "mapping": mapping}

    def queue_booking_invoice(self, booking: Mapping[str, Any], member: Mapping[str, Any], tariff: Mapping[str, Any]) -> OutboxJob:
        key = str(booking.get("booking_key") or self.booking_key(booking.get("sparte"), booking.get("parzelle"), str(booking.get("period") or "")))
        return self.outbox.enqueue("create_invoice", {"booking": dict(booking), "member": dict(member), "tariff": dict(tariff)}, unique_key=key)

    def process_outbox(self, limit: int = 20) -> list[JsonDict]:
        return self.outbox.process({"create_invoice": lambda p: self.create_booking_invoice(p["booking"], p["member"], p["tariff"])}, limit=limit)

    def verify_webhook(self, raw_body: bytes, supplied_signature: str) -> None:
        if not self.config.webhook_secret:
            raise InvoiceNinjaConfigError("Webhook-Geheimnis ist nicht konfiguriert")
        supplied = supplied_signature.strip()
        if supplied.lower().startswith("sha256="):
            supplied = supplied.split("=", 1)[1]
        expected = hmac.new(self.config.webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied):
            raise InvoiceNinjaValidationError("Webhook-Signatur ungueltig")

    def handle_webhook(self, raw_body: bytes, headers: Mapping[str, str], verify_signature: bool = True) -> JsonDict:
        if verify_signature:
            lower_headers = {str(k).lower(): str(v) for k, v in headers.items()}
            signature = lower_headers.get(self.config.webhook_signature_header.lower(), "")
            self.verify_webhook(raw_body, signature)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvoiceNinjaValidationError("Webhook enthaelt kein gueltiges JSON") from exc
        event_id = self._event_id(payload, raw_body)
        processed = self.processed.read()
        if event_id in processed:
            return {"ok": True, "duplicate": True, "event_id": event_id, "result": processed[event_id].get("result", {})}
        payment_id = self._extract_id(payload, "payment")
        invoice_id = self._extract_id(payload, "invoice")
        if payment_id:
            payment = self.client.show_payment(payment_id)
            invoice_id = invoice_id or self._invoice_id_from_payment(payment)
        else:
            payment = {}
        if not invoice_id:
            raise InvoiceNinjaValidationError("Webhook enthaelt keine ermittelbare Rechnungs-ID")
        invoice = self.client.show_invoice(invoice_id)
        mapping = self._mapping_for_invoice(invoice_id, invoice)
        if not mapping:
            raise InvoiceNinjaValidationError(f"Keine Spartenet-Zuordnung fuer Rechnung {invoice_id}")
        amount = self._payment_amount(payment, invoice)
        paid_in_full = self._is_paid_in_full(invoice)
        event_name = "zahlung" if paid_in_full else "zahlung_teilweise"
        event_data = {
            "sparte": mapping["sparte"],
            "parzelle": mapping["parzelle"],
            "tarif": mapping.get("tarif", ""),
            "betrag": _money(amount),
            "referenz": invoice.get("number") or mapping.get("invoice_number") or invoice_id,
            "rechnung": invoice.get("number") or mapping.get("invoice_number") or "",
            "email": mapping.get("email", ""),
            "name": mapping.get("name", ""),
            "quelle": "Invoice Ninja",
            "invoice_ninja_invoice_id": invoice_id,
            "invoice_ninja_payment_id": payment_id,
            "vollstaendig_bezahlt": paid_in_full,
        }
        result = self.event_callback(event_name, event_data)
        processed[event_id] = {"processed_at": _utc_now(), "payment_id": payment_id, "invoice_id": invoice_id, "event": event_name, "result": result}
        if len(processed) > 5000:
            processed = dict(list(processed.items())[-5000:])
        self.processed.write(processed)
        return {"ok": True, "duplicate": False, "event_id": event_id, "event": event_name, "data": event_data, "result": result}

    @staticmethod
    def _event_id(payload: Mapping[str, Any], raw_body: bytes) -> str:
        for key in ("event_id", "webhook_id", "delivery_id", "id"):
            if payload.get(key):
                return f"invoice-ninja:{key}:{payload[key]}"
        return "invoice-ninja:sha256:" + hashlib.sha256(raw_body).hexdigest()

    @staticmethod
    def _extract_id(payload: Mapping[str, Any], kind: str) -> str:
        candidates: list[Any] = [payload.get(f"{kind}_id")]
        for root in (payload, payload.get("data"), payload.get("payload")):
            if isinstance(root, dict):
                obj = root.get(kind)
                if isinstance(obj, dict):
                    candidates.extend([obj.get("id"), obj.get("hashed_id")])
                candidates.extend([root.get(f"{kind}_id"), root.get("id") if root.get("entity") == kind else None])
        return next((str(x) for x in candidates if x not in (None, "")), "")

    @staticmethod
    def _invoice_id_from_payment(payment: Mapping[str, Any]) -> str:
        invoices = payment.get("invoices") or payment.get("paymentables") or []
        for item in invoices:
            if not isinstance(item, dict):
                continue
            invoice_id = item.get("invoice_id") or item.get("id")
            if invoice_id:
                return str(invoice_id)
        return str(payment.get("invoice_id") or "")

    def _mapping_for_invoice(self, invoice_id: str, invoice: Mapping[str, Any]) -> Optional[JsonDict]:
        mappings = self.mapping.read()
        for row in mappings.values():
            if str(row.get("invoice_id")) == str(invoice_id):
                return row
        key = str(invoice.get("custom_value4") or "")
        if key and key in mappings:
            return mappings[key]
        notes = str(invoice.get("private_notes") or "")
        try:
            note_data = json.loads(notes)
        except json.JSONDecodeError:
            note_data = {}
        key = str(note_data.get("booking_key") or "") if isinstance(note_data, dict) else ""
        return mappings.get(key) if key else None

    @staticmethod
    def _payment_amount(payment: Mapping[str, Any], invoice: Mapping[str, Any]) -> Any:
        for key in ("amount", "applied", "credited"):
            if payment.get(key) not in (None, ""):
                return payment[key]
        return invoice.get("paid_to_date") or invoice.get("amount", 0)

    @staticmethod
    def _is_paid_in_full(invoice: Mapping[str, Any]) -> bool:
        balance = invoice.get("balance")
        if balance not in (None, ""):
            return _decimal(balance, "Rechnungssaldo") <= Decimal("0.00")
        amount = _decimal(invoice.get("amount", 0), "Rechnungsbetrag")
        paid = _decimal(invoice.get("paid_to_date", 0), "Gezahlter Betrag")
        return amount > Decimal("0.00") and paid >= amount


def spartenet_event_callback(event_name: str, data: JsonDict) -> Any:
    """Adapter fuer die vorhandene SparteNet-Funktion akt_automation_ausloesen.

    Den Importpfad ggf. an die Paketstruktur des Managers anpassen.
    """
    try:
        from .automation import akt_automation_ausloesen
    except ImportError:
        from automation import akt_automation_ausloesen  # type: ignore
    return akt_automation_ausloesen(event_name, data)


def build_integration_from_env(event_callback: EventCallback = spartenet_event_callback) -> InvoiceNinjaIntegration:
    return InvoiceNinjaIntegration(InvoiceNinjaConfig.from_env(), event_callback)


__all__ = [
    "InvoiceNinjaClient",
    "InvoiceNinjaConfig",
    "InvoiceNinjaConfigError",
    "InvoiceNinjaError",
    "InvoiceNinjaHTTPError",
    "InvoiceNinjaIntegration",
    "InvoiceNinjaTemporaryError",
    "InvoiceNinjaValidationError",
    "OutboxJob",
    "PersistentOutbox",
    "build_integration_from_env",
    "read_secret",
    "spartenet_event_callback",
]

"""SparteNet Manager – Gast-Voucher: Vorlagen, Voucher am Gateway auslesen, erstellen (übertragen), drucken, löschen

Vorlagen liegen im Manager (UniFi kennt keine Voucher-Vorlagen): Gültigkeit, Geräte je Voucher, Datenvolumen, Bandbreite, Drucktext.
Aus den Vouchern am Gateway schlägt der Manager Vorlagen vor (gleiche Einstellungen = ein Vorschlag).
Erstellen und Löschen am Gateway nur mit Vorschau und Bestätigung.
"""
from collections import Counter

from .karten import *  # noqa: F401,F403 – alle Namen der vorherigen Module

VOUCHER_PFAD = "/v1/sites/{site}/hotspot/vouchers"
VOUCHER_VORLAGEN_STANDARD = [
    {"id": "tag", "name": "Tagesgast", "minuten": 1440, "geraete": 1, "daten_mb": 0, "down_kbps": 0, "up_kbps": 0, "text": "Gast-WLAN für einen Tag"},
    {"id": "wochenende", "name": "Wochenende", "minuten": 2880, "geraete": 2, "daten_mb": 0, "down_kbps": 0, "up_kbps": 0, "text": "Gast-WLAN für das Wochenende"},
    {"id": "woche", "name": "Woche", "minuten": 10080, "geraete": 2, "daten_mb": 0, "down_kbps": 0, "up_kbps": 0, "text": "Gast-WLAN für eine Woche"},
]
_V_FELDER = {"minuten": (1, 1_000_000, "Gültigkeit (Minuten)"), "geraete": (1, 1000, "Geräte je Voucher"), "daten_mb": (0, 1_048_576, "Datenvolumen (MB)"),
             "down_kbps": (0, 100_000, "Download (kbit/s)"), "up_kbps": (0, 100_000, "Upload (kbit/s)")}


def dauer_text(minuten):
    m = int(minuten or 0)
    if m and m % 1440 == 0:
        t = m // 1440
        return f"{t} Tag" + ("e" if t != 1 else "")
    if m and m % 60 == 0:
        return f"{m // 60} Stunde" + ("n" if m != 60 else "")
    return f"{m} Minuten"


def _vorlage_pruefen(v, ids):
    if not isinstance(v, dict):
        raise Fehler("Ungültige Vorlage.")
    name = text_einzeilig(v.get("name") or "", 40).strip()
    if not name:
        raise Fehler("Jede Vorlage braucht einen Namen.")
    aus = {"id": re.sub(r"[^a-z0-9_-]", "", str(v.get("id") or "").lower())[:24] or secrets.token_hex(4), "name": name,
           "text": text_einzeilig(v.get("text") or "", 120)}
    while aus["id"] in ids:
        aus["id"] = secrets.token_hex(4)
    for k, (lo, hi, bez) in _V_FELDER.items():
        try:
            x = int(float(str(v.get(k, 0) or 0).replace(",", ".")))
        except (TypeError, ValueError):
            raise Fehler(f"Vorlage „{name}“: {bez} muss eine Zahl sein.")
        if k in ("down_kbps", "up_kbps") and x and x < 2:
            raise Fehler(f"Vorlage „{name}“: {bez} mindestens 2 (oder 0 = unbegrenzt).")
        if not lo <= x <= hi:
            raise Fehler(f"Vorlage „{name}“: {bez} zwischen {lo} und {hi}.")
        aus[k] = x
    return aus


def voucher_vorlagen(d):
    roh = d.get("voucher_vorlagen")
    if not isinstance(roh, list) or not roh:
        return [dict(v) for v in VOUCHER_VORLAGEN_STANDARD]
    aus, ids = [], set()
    for v in roh:
        try:
            x = _vorlage_pruefen(v, ids)
        except Fehler:
            continue
        ids.add(x["id"]); aus.append(x)
    return aus or [dict(v) for v in VOUCHER_VORLAGEN_STANDARD]


def akt_voucher_vorlagen(d, b=None):
    if b is None:
        return {"vorlagen": voucher_vorlagen(d), "standard": VOUCHER_VORLAGEN_STANDARD, "log": []}
    roh = b.get("vorlagen")
    if not isinstance(roh, list) or not roh:
        raise Fehler("Mindestens eine Vorlage ist nötig.")
    if len(roh) > 30:
        raise Fehler("Höchstens 30 Vorlagen.")
    aus, ids = [], set()
    for v in roh:
        x = _vorlage_pruefen(v, ids)
        if x["name"].lower() in {y["name"].lower() for y in aus}:
            raise Fehler(f"Vorlage „{x['name']}“ gibt es doppelt.")
        ids.add(x["id"]); aus.append(x)
    d["voucher_vorlagen"] = aus
    speichere(d)
    journal(f"Voucher-Vorlagen gespeichert: {', '.join(v['name'] for v in aus)}")
    return {"vorlagen": aus, "standard": VOUCHER_VORLAGEN_STANDARD, "log": [f"✔ {len(aus)} Vorlage(n) gespeichert."]}


def _einstellungen(v):
    """Vergleichsschlüssel einer Vorlage bzw. eines Vouchers"""
    return (int(v.get("minuten") or 0), int(v.get("geraete") or 1), int(v.get("daten_mb") or 0), int(v.get("down_kbps") or 0), int(v.get("up_kbps") or 0))


def _aus_gateway(x):
    return {"minuten": x.get("timeLimitMinutes") or 0, "geraete": x.get("authorizedGuestLimit") or 1, "daten_mb": x.get("dataUsageLimitMBytes") or 0,
            "down_kbps": x.get("rxRateLimitKbps") or 0, "up_kbps": x.get("txRateLimitKbps") or 0}


def _status(x):
    if x.get("expired"):
        return "abgelaufen"
    if x.get("activatedAt") or int(x.get("authorizedGuestCount") or 0) > 0:
        grenze = int(x.get("authorizedGuestLimit") or 1)
        return "in Benutzung" if int(x.get("authorizedGuestCount") or 0) < grenze or not grenze else "voll belegt"
    return "unbenutzt"


def akt_voucher_liste(d):
    """Voucher am Gateway auslesen; dazu Vorlagen-Vorschläge aus Einstellungen, die noch keine Vorlage hat"""
    roh = Gateway(d).alle(VOUCHER_PFAD)
    vorlagen = voucher_vorlagen(d)
    nach_einst = {_einstellungen(v): v["name"] for v in vorlagen}
    zeilen, vorschlaege = [], {}
    for x in roh:
        e = _aus_gateway(x)
        k = _einstellungen(e)
        vorlage = nach_einst.get(k, "")
        zeilen.append({"id": x.get("id"), "code": x.get("code", ""), "name": x.get("name", ""), **e, "dauer": dauer_text(e["minuten"]),
                       "genutzt": int(x.get("authorizedGuestCount") or 0), "erstellt": x.get("createdAt", ""), "aktiviert": x.get("activatedAt") or "",
                       "ablauf": x.get("expiresAt") or "", "status": _status(x), "vorlage": vorlage})
        if not vorlage:
            vs = vorschlaege.setdefault(k, {**e, "name": x.get("name") or dauer_text(e["minuten"]), "anzahl": 0})
            vs["anzahl"] += 1
    zeilen.sort(key=lambda z: z["erstellt"], reverse=True)
    zahl = Counter(z["status"] for z in zeilen)
    return {"zeilen": zeilen, "vorschlaege": sorted(vorschlaege.values(), key=lambda v: -v["anzahl"]),
            "log": [f"{len(zeilen)} Voucher am Gateway: " + ", ".join(f"{n} {s}" for s, n in sorted(zahl.items())) if zeilen else "Keine Voucher am Gateway."]}


def akt_voucher(d, anzahl, minuten, name, ausfuehren, vorlage=None):
    """Voucher nach Vorlage (oder nur mit Gültigkeit) am Gateway erstellen – ohne „ausfuehren“ nur Vorschau"""
    try:
        anzahl = int(anzahl)
    except (TypeError, ValueError):
        raise Fehler("Anzahl muss eine Zahl sein.")
    if not 1 <= anzahl <= 1000:
        raise Fehler("Anzahl 1–1000.")
    if vorlage:
        v = next((x for x in voucher_vorlagen(d) if x["id"] == vorlage), None)
        if not v:
            raise Fehler("Vorlage nicht gefunden.")
    else:
        v = _vorlage_pruefen({"name": name or "Gast", "minuten": minuten or 1440, "geraete": 1}, set())
    name = text_einzeilig(name or v["name"], 40).strip() or v["name"]
    body = {"count": anzahl, "name": name, "timeLimitMinutes": v["minuten"]}
    if v["geraete"] != 1:
        body["authorizedGuestLimit"] = v["geraete"]
    if v["daten_mb"]:
        body["dataUsageLimitMBytes"] = v["daten_mb"]
    if v["down_kbps"]:
        body["rxRateLimitKbps"] = v["down_kbps"]
    if v["up_kbps"]:
        body["txRateLimitKbps"] = v["up_kbps"]
    beschreibung = (f"{anzahl} Voucher „{name}“: {dauer_text(v['minuten'])}, {v['geraete']} Gerät(e) je Voucher"
                    + (f", {v['daten_mb']} MB" if v["daten_mb"] else ", Datenvolumen unbegrenzt")
                    + (f", Download {v['down_kbps'] / 1000:g} Mbit/s" if v["down_kbps"] else "") + (f", Upload {v['up_kbps'] / 1000:g} Mbit/s" if v["up_kbps"] else ""))
    if not ausfuehren:
        return {"log": [f"Vorschau: {beschreibung}. Am Gateway ändert sich noch nichts.", json.dumps(body, ensure_ascii=False)]}
    g = Gateway(d)
    start = time.time()
    a = g.req("POST", VOUCHER_PFAD, body)
    liste = (a.get("vouchers") or a.get("data") or []) if isinstance(a, dict) else (a or [])
    codes = [x["code"] for x in liste if isinstance(x, dict) and x.get("code")]
    if not codes:   # manche Versionen antworten ohne Codes → frisch erstellte nachlesen
        try:
            neu = [x for x in g.alle(VOUCHER_PFAD) if x.get("name") == name]
            neu.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            codes = [x["code"] for x in neu[:anzahl] if x.get("code")]
        except Fehler:
            pass
    journal(f"Voucher erstellt: {beschreibung} (seit {time.strftime('%H:%M:%S', time.localtime(start))})")
    return {"log": [f"✔ {beschreibung} – am Gateway erstellt." + ("" if codes else " Codes unter „Voucher am Gateway“.")],
            "codes": codes, "minuten": v["minuten"], "dauer": dauer_text(v["minuten"]), "text": v.get("text") or "", "geraete": v["geraete"]}


def akt_voucher_loeschen(d, ids, ausfuehren):
    ids = [str(i) for i in (ids or []) if re.fullmatch(r"[A-Za-z0-9-]{1,64}", str(i))]
    if not ids:
        raise Fehler("Keine Voucher ausgewählt.")
    g = Gateway(d)
    vorhanden = {x.get("id"): x for x in g.alle(VOUCHER_PFAD)}
    weg = [vorhanden[i] for i in ids if i in vorhanden]
    if not weg:
        raise Fehler("Die ausgewählten Voucher gibt es am Gateway nicht mehr – bitte neu auslesen.")
    text = ", ".join(f"{x.get('code')} ({_status(x)})" for x in weg[:10]) + (" …" if len(weg) > 10 else "")
    if not ausfuehren:
        benutzt = sum(1 for x in weg if _status(x) in ("in Benutzung", "voll belegt"))
        return {"log": [f"Vorschau: {len(weg)} Voucher löschen – {text}."]
                + ([f"⚠ {benutzt} davon sind gerade in Benutzung – die Gäste verlieren den Zugang."] if benutzt else [])}
    ok, log = 0, []
    for x in weg:
        try:
            g.req("DELETE", f"{VOUCHER_PFAD}/{x['id']}")
            ok += 1
        except Fehler as e:
            log.append(f"✖ {x.get('code')}: {e}")
    journal(f"Voucher gelöscht: {ok} von {len(weg)} ({text})")
    return {"log": [f"✔ {ok} von {len(weg)} Voucher gelöscht."] + log}


# ---- Druck wie die Zugangskarten der Parzellen (Kartendesign), mit Gast-WLAN, Code, Laufzeit und Ende ----------------
def _ortszeit(utc):
    """UTC → Ortszeit (Standard Europe/Berlin, änderbar mit SPARTENET_ZEITZONE); ohne Zeitzonen-Datenbank: Sommerzeit-Regel der EU"""
    import datetime as dt
    try:
        from zoneinfo import ZoneInfo
        return utc.astimezone(ZoneInfo(os.environ.get("SPARTENET_ZEITZONE", "Europe/Berlin")))
    except Exception:
        def letzter_sonntag(jahr, monat):
            t = dt.datetime(jahr, monat, 31, 1, tzinfo=dt.timezone.utc)
            return t - dt.timedelta(days=(t.weekday() + 1) % 7)
        sommer = letzter_sonntag(utc.year, 3) <= utc < letzter_sonntag(utc.year, 10)
        return utc.astimezone(dt.timezone(dt.timedelta(hours=2 if sommer else 1)))


def _zeit_text(iso=None, plus_minuten=None):
    import datetime as dt
    if iso:
        try:
            t = dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            return str(iso)
    else:
        t = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=int(plus_minuten or 0))
    return _ortszeit(t).strftime("%d.%m.%Y, %H:%M Uhr")


def akt_voucher_druck(d, b):
    """Voucher (Auswahl aus der Liste oder gerade erstellte Codes) im Kartendesign drucken"""
    b = b or {}
    ids, codes = {str(x) for x in (b.get("ids") or [])}, {re.sub(r"\D", "", str(x)) for x in (b.get("codes") or [])}
    if not ids and not codes:
        raise Fehler("Keine Voucher ausgewählt.")
    alle = Gateway(d).alle(VOUCHER_PFAD)
    wahl = [x for x in alle if x.get("id") in ids or re.sub(r"\D", "", str(x.get("code", ""))) in codes]
    if not wahl:
        raise Fehler("Die ausgewählten Voucher gibt es am Gateway nicht (mehr) – bitte neu auslesen.")
    plan = plan_aktiv(d)
    pre = plan.get("praefix") or "SparteNet.de"
    sp = next((s for s in plan["sparten"] if s["kz"] == b.get("sparte")), plan["sparten"][0] if plan["sparten"] else {"kz": "", "name": "SparteNet"})
    ssid = text_einzeilig(b.get("wlan") or "", 32).strip() or wlan_ssid(d, sp["kz"], "gaeste")
    nach_einst = {_einstellungen(v): v for v in voucher_vorlagen(d)}
    zeilen, abgelaufen = [], 0
    for x in sorted(wahl, key=lambda x: x.get("code", "")):
        e = _aus_gateway(x)
        laufzeit = dauer_text(e["minuten"])
        if x.get("expiresAt"):
            ende = _zeit_text(x["expiresAt"])
        elif b.get("ab_jetzt"):
            ende = _zeit_text(plus_minuten=e["minuten"])
        else:
            ende = f"{laufzeit} nach der ersten Anmeldung"
        abgelaufen += bool(x.get("expired"))
        c = str(x.get("code", ""))
        code = f"{c[:5]}-{c[5:]}" if len(c) == 10 and c.isdigit() else c
        v = nach_einst.get(_einstellungen(e)) or {}
        zugang = [("WLAN", ssid, "ssid"), ("Voucher-Code", code, "pw"),
                  ("Laufzeit", laufzeit + (f" · bis {e['geraete']} Geräte" if e["geraete"] > 1 else "") + (f" · {e['daten_mb']} MB" if e["daten_mb"] else ""), "wert"),
                  ("Gültig bis", ende, "wert")]
        zeilen.append({"Parzelle": "Gast", "WLAN": ssid, "Passwort": "", "Titel": "Gast-WLAN", "Unter": v.get("text") or f"Ihr Gast-Zugang für {laufzeit}",
                       "Scan": "Handy-Kamera auf den Code richten, mit dem WLAN verbinden und im Browser den Voucher-Code eingeben",
                       "Fuss": "Die Laufzeit beginnt mit der ersten Anmeldung. Bei Fragen: SparteNet.de", "Zugang": zugang})
    html = karten_html(d["design"], sp["name"], sp["kz"], zeilen)
    journal(f"Voucher gedruckt: {len(zeilen)} ({ssid})")
    return {"html": html, "log": [f"✔ {len(zeilen)} Voucher im Kartendesign zum Drucken geöffnet (WLAN „{ssid}“)."]
            + ([f"⚠ {abgelaufen} davon sind abgelaufen."] if abgelaufen else [])}


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

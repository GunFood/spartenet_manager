"""SparteNet Manager – Mitgliederbereich (/mein): Anmeldung für Pächter mit E-Mail-Code

Ein Mitglied meldet sich mit seiner beim Verein hinterlegten E-Mail-Adresse an und bekommt einen 6-stelligen Code per E-Mail
(kein Passwort nötig, 10 Minuten gültig). Danach sieht es je Parzelle: Tarif mit Laufzeit, Rechnungen (PDF), seine Geräte im
Parzellen-Netz (an der IP erkennbar: 10.<Sparte>.<Parzelle>.<Gerät>), Anfragen und kann den Tarif wechseln, neu buchen oder die
Laufzeit verlängern.

Bezahlen: „anfrage“ (Wunsch geht als geprüfte Anfrage an den Vorstand) oder „bezahldienst“: der Manager legt einen Zahlungsauftrag
(Referenz SN-…) an und leitet zum Bezahldienst weiter – entweder über eine Link-Vorlage oder eine eigene Schnittstelle (z. B. n8n,
Stripe/PayPal/Mollie über einen kleinen Dienst), die die Bezahl-Adresse liefert. Bestätigt wird die Zahlung über
POST /mein/zahlung-webhook (HMAC-SHA256-Signatur mit dem gemeinsamen Geheimnis) oder über die API (/api/v1/ereignis „zahlung“ mit
„referenz“). Erst dann wird gebucht – am Gateway wie jede andere Buchung (Laufzeit, Zuteilung, Automationen).
"""
from .app import *  # noqa: F401,F403 – alle Namen der vorherigen Module
import urllib.request as _ur

MB_STANDARD = {"aktiv": False, "tarifwechsel": True, "downgrade": True, "neubuchung": True, "verlaengern": True, "geraete": True, "modus": "anfrage",
               "link_api": "", "checkout_vorlage": "", "hinweis": "", "minuten": 30, "adresse": "",
               "titel": "Mitgliederbereich", "text_anmeldung": "", "zeige_rechnungen": True, "zeige_anfragen": True, "neue_anfrage": True,
               "zugangskarte": True, "profil": True, "personen": True, "geraete_trennen": False, "geraete_sperren": False, "tarife": [],
               "downgrade_monate": 3, "downgrade_stufe": True, "downgrade_freigabe": False, "zusatzgeraete": True, "zusatz_preis": 1.0, "zusatz_max": 5, "wechsel_rechnung": True, "stoerung_zeigen": True, "stoerung_farbe": "#b42318",
               "stoerung_meldung": "Achtung: {geraet} ist aktuell ausgefallen (seit {seit}). Ein Störungsticket {ticket} ist erstellt und an den Verein verschickt – wir kümmern uns darum.",
               "stoerung_text": ""}
_MB_SITZ, _MB_CODES = {}, {}
_MB_LOCK = threading.Lock()
_GRENZEN.update({"mb_logo": (60, 3600), "mb_code": (5, 3600), "mb_code_mail": (3, 900), "mb_anmelden": (10, 900), "mb_aktion": (30, 3600)})
_GERAETE_CACHE = {"zeit": 0, "liste": [], "fehler": ""}
AUSLOESER["zahlung_mitglied"] = "Mitglied hat im Mitgliederbereich bezahlt (Tarif/Laufzeit gebucht)"


def mb_einstellungen(d):
    roh = d.get("mitgliederbereich") if isinstance(d.get("mitgliederbereich"), dict) else {}
    e = dict(MB_STANDARD)
    for k, s in MB_STANDARD.items():
        if k in roh:
            if isinstance(s, list):
                e[k] = [str(x) for x in roh[k]] if isinstance(roh[k], list) else []
            else:
                try:
                    e[k] = bool(roh[k]) if isinstance(s, bool) else (float(roh[k]) if isinstance(s, float) else (int(roh[k]) if isinstance(s, int) else str(roh[k])))
                except (TypeError, ValueError):
                    pass
    g = seiten_design(d, "mein")                  # Titel und Texte stehen unter „Oberfläche gestalten → Mitgliederbereich“
    e["titel"], e["text_anmeldung"], e["hinweis"] = g.get("titel") or "Mitgliederbereich", g.get("text_anmeldung", ""), g.get("hinweis", "")
    e["geheim_gesetzt"] = bool(roh.get("geheim"))
    return e


def _mb_geheim(d):
    return str(((d.get("mitgliederbereich") or {}) if isinstance(d.get("mitgliederbereich"), dict) else {}).get("geheim") or "")


def akt_mitgliederbereich(d, b=None, ich=""):
    """Einstellungen (Administrator). {"geheim_neu": true} erzeugt das Webhook-Geheimnis neu – wird nur einmal angezeigt."""
    roh = d.get("mitgliederbereich") if isinstance(d.get("mitgliederbereich"), dict) else {}
    extra = {}
    if b is not None:
        texte = {k: b[k] for k in ("titel", "text_anmeldung", "hinweis") if k in b}
        if texte:                                    # Titel und Texte gehören zur Gestaltung des Mitgliederbereichs
            d.setdefault("seiten_design", {})["mein"] = seite_pruefen(d, texte, MEIN_DESIGN_STANDARD, seiten_design(d, "mein"))
        for k, s in MB_STANDARD.items():
            if k not in b or k in texte:
                continue
            v = b[k]
            if isinstance(s, bool):
                roh[k] = bool(v)
            elif k == "zusatz_preis":
                try:
                    roh[k] = round(float(str(v if v not in (None, "") else 1).replace(",", ".")), 2)
                except ValueError:
                    raise Fehler("Preis je Zusatzgerät: eine Zahl, z. B. 1,00.")
                if not 0 <= roh[k] <= 1000:
                    raise Fehler("Preis je Zusatzgerät: 0 bis 1000 € im Jahr.")
            elif k in ("downgrade_monate", "zusatz_max"):
                try:
                    roh[k] = max(0, min(24 if k == "downgrade_monate" else 50, int(v or 0)))
                except (TypeError, ValueError):
                    raise Fehler("Monate und Anzahl Zusatzgeräte: ganze Zahlen.")
            elif isinstance(s, int):
                roh[k] = max(5, min(240, int(v or 30)))
            elif k == "tarife":
                namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
                if not isinstance(v, list) or any(x not in namen for x in v):
                    raise Fehler("Buchbare Tarife: nur vorhandene Tarife auswählen.")
                roh[k] = [str(x) for x in v]
            elif k == "titel":
                roh[k] = text_einzeilig(v or "", 80) or "Mitgliederbereich"
            elif k == "stoerung_farbe":
                if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(v or "")):
                    raise Fehler("Farbe der Störungsmeldung: Form #RRGGBB.")
                roh[k] = str(v).lower()
            elif k in ("stoerung_meldung", "stoerung_text"):
                roh[k] = str(v or "").replace("\r", "").strip()[:800]
            elif k == "modus":
                if v not in ("anfrage", "bezahldienst"):
                    raise Fehler("Modus: anfrage oder bezahldienst.")
                roh[k] = v
            elif k == "adresse":
                v = text_einzeilig(v or "", 200).strip().rstrip("/")
                if v and not re.match(r"^https?://[A-Za-z0-9.:\[\]-]+(/[^\s]*)?$", v):
                    raise Fehler("Öffentliche Adresse: z. B. https://wlan.meine-sparte.de")
                roh[k] = v
            elif k == "link_api":
                v = text_einzeilig(v or "", 500).strip()
                if v and not re.match(r"^https://[^\s]+$", v):
                    raise Fehler("Schnittstelle des Bezahldienstes: Adresse mit https:// angeben.")
                roh[k] = v
            elif k == "checkout_vorlage":
                v = text_einzeilig(v or "", 800).strip()
                if v and not re.match(r"^https://[^\s]+$", v):
                    raise Fehler("Link-Vorlage: Adresse mit https:// angeben.")
                roh[k] = v
            else:
                roh[k] = text_einzeilig(v or "", 600)
        if b.get("apps_abmelden"):
            d["mitglied_apps"] = {}
            journal(f"Alle Mitglieder-Apps abgemeldet durch {ich}")
        if b.get("geheim_neu"):
            roh["geheim"] = secrets.token_urlsafe(32)
            extra["geheim"] = roh["geheim"]
        if roh.get("modus") == "bezahldienst" and not (roh.get("link_api") or roh.get("checkout_vorlage")):
            raise Fehler("Für den Bezahldienst bitte eine Link-Vorlage oder die Schnittstelle (Adresse) angeben.")
        d["mitgliederbereich"] = roh
        speichere(d)
        journal(f"Mitgliederbereich-Einstellungen gespeichert durch {ich}" + (" (Webhook-Geheimnis neu)" if extra else ""))
    auf = sorted(zahlungsauftraege(d).items(), key=lambda x: x[1].get("erstellt", ""), reverse=True)[:100]
    return {"einstellungen": mb_einstellungen(d), "alle_tarife": [{"name": t["name"], "preis": t.get("preis", 0)} for t in sorted(tarife_pruefen(d["tarife"]), key=tarif_rang)],
            "antraege": len(tarif_antraege(d)), "versand": mb_versand_bereit(d), "apps": len([x for x in mitglied_apps(d).values() if x.get("ablauf", 0) > time.time()]), "auftraege": [{"referenz": r, **{k: a.get(k) for k in ("sparte", "parzelle", "tarif", "art", "betrag", "status", "erstellt", "bezahlt_am", "name")}}
                                                                for r, a in auf],
            **extra, "log": (["✔ Gespeichert."] + (["Neues Webhook-Geheimnis – jetzt kopieren, es wird nur einmal angezeigt."] if extra else [])) if b is not None else []}


# ---- Anmeldung mit E-Mail-Code ---------------------------------------------------------------------------------------
def _mb_hash(x):
    return hashlib.sha256(("SparteNet-Mitglied|" + str(x)).encode()).hexdigest()


def mb_mitglieder_von(d, email):
    """Parzellen, auf die diese E-Mail-Adresse Zugriff hat – als Mitglied oder als weitere Person der Parzelle.
    Ergebnis: {Mitglied-Id: Mitglied aus Sicht der Person (Name/E-Mail/Telefon der Person)}"""
    e = name_norm(email)
    aus = {}
    if not e:
        return aus
    for i, m in mitglieder(d).items():
        pe = next((x for x in personen(m) if x.get("email") and name_norm(x["email"]) == e), None)
        if pe:
            aus[i] = person_sicht(m, pe)
    return aus


def _parzellen_ids(d, kz, p):
    """alle Mitglieder-Einträge derselben Parzelle (falls mehrere einzeln angelegt sind)"""
    return {i for i, m in mitglieder(d).items() if kz and m.get("sparte") == kz and str(m.get("parzelle") or "") == str(p)}


def mb_versand_bereit(d):
    """Einmalcodes gehen über den E-Mail-Versand des Managers (Automationen → E-Mail-Versand)"""
    s = smtp_einstellungen(d)
    return bool(s["host"] and s["absender"])


def mb_code_anfordern(d, b, quelle):
    """Einmalcode (6 Ziffern, 10 Minuten, nur einmal gültig) per E-Mail über den E-Mail-Versand des Managers"""
    email = str(b.get("email") or "").strip()
    antwort = {"ok": True, "text": "Wenn die Adresse bei uns hinterlegt ist, kommt jetzt ein Einmalcode per E-Mail (10 Minuten gültig)."}
    if not re.fullmatch(r"[^@\s,;<>]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,}", email):
        raise Fehler("Bitte eine gültige E-Mail-Adresse eingeben.")
    if not mb_versand_bereit(d):                  # für alle Adressen gleich – verrät nicht, ob es die Adresse gibt
        LOG.warning("Mitgliederbereich: Einmalcode angefordert, aber der E-Mail-Versand ist nicht eingerichtet")
        raise Fehler("Die Anmeldung ist gerade nicht möglich (E-Mail-Versand des Vereins nicht eingerichtet) – bitte beim Verein melden.")
    _grenze("mb_code", quelle)
    _grenze("mb_code_mail", name_norm(email))
    treffer = mb_mitglieder_von(d, email)
    if not treffer:
        LOG.info("Mitgliederbereich: Code für unbekannte Adresse angefordert")
        return antwort
    email = next(iter(treffer.values()))["email"]          # an die hinterlegte Adresse, nicht an die eingetippte
    m = next(iter(treffer.values()))
    code = f"{secrets.randbelow(1000000):06d}"
    with _MB_LOCK:
        _MB_CODES[name_norm(email)] = {"hash": _mb_hash(code), "bis": time.time() + 600, "versuche": 0}
    wo = "in der App „SparteNet Mitglied“" if b.get("app") else "im " + mb_einstellungen(d)["titel"]
    try:
        email_senden(d, email, f"Ihr Einmalcode: {code}", None,
                     f"<p>Hallo {html_mod.escape(m.get('vorname') or '')},</p><p>Ihr Einmalcode zum Anmelden {html_mod.escape(wo)} lautet:</p>"
                     f"<p style='font-size:28px;letter-spacing:6px;font-weight:bold'>{code}</p>"
                     "<p>Er gilt 10 Minuten und nur für eine Anmeldung. Geben Sie ihn nicht weiter – der Verein fragt nie danach.<br>"
                     "Haben Sie keinen Code angefordert, können Sie diese E-Mail ignorieren.</p>", sparte=m.get("sparte") or None)
    except Fehler as f:
        with _MB_LOCK:
            _MB_CODES.pop(name_norm(email), None)
        LOG.warning("Mitgliederbereich: Einmalcode nicht gesendet: %s", f)
        journal("Mitgliederbereich: Einmalcode konnte nicht gesendet werden (E-Mail-Versand prüfen)")
        raise Fehler("Der Code konnte gerade nicht gesendet werden – bitte später erneut versuchen oder beim Verein melden.")
    return antwort


def mb_logo_zur_email(d, email, quelle):
    """Vereinslogo (Spartenlogo) zur eingegebenen E-Mail-Adresse – damit das Mitglied gleich „seinen“ Verein sieht"""
    _grenze("mb_logo", quelle)
    kz = sparte_aus_email(d, email)
    e = mb_einstellungen(d)
    st = {"stoerungen": mb_stoerungen(d, e, kz) if kz else mb_stoerungen(d, e, None, nur_alle=True),
          "stoerung_text": e["stoerung_text"], "stoerung_farbe": e["stoerung_farbe"]}      # Störungen passend zur Sparte
    if not seiten_design(d, "mein").get("vereinslogo", True):
        return {"logo": "", **st}
    i = sparten_logo_id(d, kz) if kz else ""
    return ({"logo": f"/spartenlogo/{urllib.parse.quote(kz)}?v={i[:6]}", "name": _sparten_kz(d).get(kz, kz)} if i else {"logo": ""}) | st


def mb_stoerung_oeffentlich(d, quelle):
    """Anmeldeseite ohne E-Mail: nur Störungen, die alle Sparten betreffen"""
    _grenze("mb_logo", quelle)
    e = mb_einstellungen(d)
    return {"stoerungen": mb_stoerungen(d, e, None, nur_alle=True), "stoerung_text": e["stoerung_text"], "stoerung_farbe": e["stoerung_farbe"]}


def mb_anmelden(d, b, quelle):
    _grenze("mb_anmelden", quelle)
    e = name_norm(b.get("email"))
    code = re.sub(r"\D", "", str(b.get("code") or ""))
    with _MB_LOCK:
        c = _MB_CODES.get(e)
        if not c or time.time() > c["bis"] or c["versuche"] >= 5:
            _MB_CODES.pop(e, None)
            raise Fehler("Der Code ist abgelaufen oder ungültig – bitte einen neuen anfordern.")
        if not hmac.compare_digest(c["hash"], _mb_hash(code)):
            c["versuche"] += 1
            raise Fehler("Der Code stimmt nicht.")
        _MB_CODES.pop(e, None)
        t = secrets.token_urlsafe(32)
        jetzt = time.time()
        for k in [k for k, v in _MB_SITZ.items() if v["bis"] < jetzt]:
            del _MB_SITZ[k]
        _MB_SITZ[_mb_hash(t)] = {"email": e, "bis": jetzt + 12 * 3600, "zuletzt": jetzt}
    journal("Mitgliederbereich: Anmeldung eines Mitglieds")
    return t


def mb_sitzung(d, t):
    """E-Mail (normalisiert) der Sitzung oder None (abgelaufen nach X Minuten ohne Aktivität)"""
    if not t:
        return None
    with _MB_LOCK:
        s = _MB_SITZ.get(_mb_hash(t))
        jetzt = time.time()
        if not s or s["bis"] < jetzt or jetzt - s["zuletzt"] > mb_einstellungen(d)["minuten"] * 60:
            _MB_SITZ.pop(_mb_hash(t), None)
            return None
        s["zuletzt"] = jetzt
        return s["email"]


def mb_abmelden(t):
    with _MB_LOCK:
        _MB_SITZ.pop(_mb_hash(t or ""), None)


# ---- Mitglieder-App: dauerhafter Schlüssel „snm_<id>_<geheim>“ (nur als Prüfsumme gespeichert) -----------------------
MB_APP_TAGE = max(1, int(os.environ.get("SPARTENET_MITGLIED_APP_TAGE", "180") or 180))
_MBA_RE = re.compile(r"^snm_([0-9a-f]{10})_([A-Za-z0-9_-]{30,80})$")


def mitglied_apps(d):
    a = d.get("mitglied_apps")
    if not isinstance(a, dict):
        a = {}
        d["mitglied_apps"] = a
    return a


def mb_app_anlegen(d, email, geraet):
    """nach erfolgreicher Code-Anmeldung: Schlüssel für die Mitglieder-App (höchstens 10 Geräte je E-Mail-Adresse)"""
    e = name_norm(email)
    a = mitglied_apps(d)
    jetzt = time.time()
    for k in [k for k, x in a.items() if x.get("ablauf", 0) < jetzt]:
        del a[k]
    eigene = sorted((k for k, x in a.items() if x.get("email") == e), key=lambda k: a[k].get("angelegt", ""))
    for k in eigene[:-9]:
        del a[k]                                     # ältestes Gerät fällt raus
    i, geheim = secrets.token_hex(5), secrets.token_urlsafe(32)
    a[i] = {"email": e, "hash": _mb_hash("app|" + geheim), "geraet": text_einzeilig(geraet or "App", 60) or "App",
            "angelegt": time.strftime("%Y-%m-%d %H:%M"), "zuletzt": "", "ablauf": jetzt + MB_APP_TAGE * 86400}
    speichere(d)
    journal("Mitgliederbereich: Mitglieder-App angemeldet")
    return f"snm_{i}_{geheim}"


def mb_app_pruefen(d, kopf):
    """E-Mail (normalisiert) für einen gültigen Mitglieder-App-Schlüssel, sonst None"""
    roh = str(kopf or "")
    if not roh.lower().startswith("bearer snm_"):
        return None
    m = _MBA_RE.match(roh[7:].strip())
    if not m:
        return None
    x = mitglied_apps(d).get(m.group(1))
    if not x or x.get("ablauf", 0) < time.time() or not hmac.compare_digest(x.get("hash", ""), _mb_hash("app|" + m.group(2))):
        return None
    if not mb_mitglieder_von(d, x["email"]):
        return None                                  # Mitglied gelöscht oder E-Mail geändert
    jetzt = time.strftime("%Y-%m-%d %H:%M")
    if x.get("zuletzt", "")[:15] != jetzt[:15]:
        with SCHREIB_SPERRE:
            d2 = lade()
            y = mitglied_apps(d2).get(m.group(1))
            if y:
                y["zuletzt"] = jetzt
                speichere(d2)
    return x["email"]


def mb_app_entfernen(d, kopf):
    m = _MBA_RE.match(str(kopf or "")[7:].strip())
    if m and mitglied_apps(d).pop(m.group(1), None):
        speichere(d)


# ---- Daten für das Mitglied ------------------------------------------------------------------------------------------
def _parzellen_netz_plan(d, kz, p):
    try:
        plan = plan_aktiv(d)
    except Fehler:
        return None
    n = next((n for n in plan["netze"] if n["sparte"] == kz and str(n.get("parzelle", "")) == str(p)), None)
    if n and n.get("netz"):
        return n["netz"]
    sp = next((s for s in plan["sparten"] if s["kz"] == kz), None)
    return f"10.{sp['sid']}.{int(p)}.0/24" if sp and sp.get("sid") is not None else None


def _geraet_ref(kz, p, mac):
    """undurchsichtige Kennung eines Geräts für das Mitglied – verrät weder MAC- noch IP-Adresse"""
    return hashlib.sha256(f"SparteNet-Geraet|{kz}|{p}|{str(mac).lower()}".encode()).hexdigest()[:20]


def _geraete_roh(d, kz, p):
    """(Liste der Clients im Netz der Parzelle, Fehlertext) – Client-Liste des Gateways, 60 s zwischengespeichert"""
    netz = _parzellen_netz_plan(d, kz, p)
    if not netz:
        return [], "Für diese Parzelle ist kein Netz geplant."
    if time.time() - _GERAETE_CACHE["zeit"] > 60:
        try:
            _GERAETE_CACHE.update(liste=Gateway(d).alle("/v1/sites/{site}/clients"), fehler="", zeit=time.time())
        except Exception as e:
            _GERAETE_CACHE.update(fehler="Geräteliste gerade nicht abrufbar.", zeit=time.time() - 30)
            LOG.warning("Mitgliederbereich: Geräte nicht abrufbar: %s", e)
    try:
        n = ipaddress.ip_network(netz, strict=False)
    except ValueError:
        return [], "Netz der Parzelle ungültig."
    aus = []
    for c in _GERAETE_CACHE["liste"]:
        ip = c.get("ipAddress") or ""
        try:
            if ip and ipaddress.ip_address(ip) in n:
                aus.append(c)
        except ValueError:
            continue
    aus.sort(key=lambda c: int(str(c.get("ipAddress")).rsplit(".", 1)[-1]))
    return aus, _GERAETE_CACHE["fehler"]


def gesperrte_geraete(d):
    g = d.get("mb_gesperrte_geraete")
    if not isinstance(g, dict):
        g = {}
        d["mb_gesperrte_geraete"] = g
    return g


def mb_geraete(d, kz, p):
    """Geräte im Netz der Parzelle – fortlaufend nummeriert, ohne IP- und MAC-Adresse; dazu „x von y“ nach dem Tarif
    und die vom Mitglied gesperrten Geräte (WLAN-Geräte trennen bzw. Geräte sperren, wenn eingeschaltet)"""
    roh, fehler = _geraete_roh(d, kz, p)
    aus = [{"nr": i + 1, "name": c.get("name") or c.get("hostname") or "Gerät", "ref": _geraet_ref(kz, p, c.get("macAddress") or ""),
            "art": {"WIRELESS": "WLAN", "WIRED": "Kabel"}.get(str(c.get("type") or "").upper(), c.get("type") or ""), "seit": c.get("connectedAt") or ""}
           for i, c in enumerate(roh)]
    tarif = ((d.get("buchungen") or {}).get(kz) or {}).get(str(p), "")
    t = next((x for x in tarife_pruefen(d["tarife"]) if x["name"] == tarif), None)
    gesp = [{"ref": x["ref"], "name": x.get("name", "Gerät"), "zeit": x.get("zeit", "")} for x in (d.get("mb_gesperrte_geraete") or {}).get(f"{kz}-{p}", [])]
    return {"geraete": aus, "anzahl": len(aus), "max": geraete_im_tarif(d, t, kz, p) if t else 0, "zusatz": zusatz_geraete(d, kz, p), "tarif": tarif,
            "gesperrt": gesp, "fehler": fehler}


def mb_geraet_trennen(d, kz, p, b):
    """Gerät der Parzelle trennen oder sperren – nur mit Bestätigung und nur, wenn der Administrator es unter
    „Mitgliederbereich“ einschaltet (Änderung am Gateway):
    - trennen (kick-sta): nur WLAN; die Verbindung wird beendet, das Gerät darf sich bei Bedarf sofort wieder verbinden
    - sperren ("sperren": true, block-sta): das Gerät kommt nicht mehr ins Netz, bis das Mitglied es wieder zulässt"""
    sperren = bool(b.get("sperren"))
    e = mb_einstellungen(d)
    if sperren and not e["geraete_sperren"]:
        raise Fehler("Geräte sperren ist hier nicht eingeschaltet – bitte beim Verein melden.")
    if not sperren and not e["geraete_trennen"]:
        raise Fehler("Geräte trennen ist hier nicht eingeschaltet – bitte beim Verein melden.")
    if not b.get("bestaetigt"):
        raise Fehler("Bitte das Sperren bestätigen." if sperren else "Bitte das Trennen bestätigen.")
    ref = str(b.get("ref") or "")
    _GERAETE_CACHE["zeit"] = 0                     # frische Liste: das Gerät muss jetzt im Netz der Parzelle sein
    roh, _f = _geraete_roh(d, kz, p)
    c = next((c for c in roh if c.get("macAddress") and hmac.compare_digest(_geraet_ref(kz, p, c["macAddress"]), ref)), None)
    if not c:
        raise Fehler("Dieses Gerät ist gerade nicht im Netz Ihrer Parzelle.")
    mac = str(c["macAddress"]).lower()
    if sperren:
        Gateway(d).legacy_cmd("cmd/stamgr", {"cmd": "block-sta", "mac": mac})
        liste = gesperrte_geraete(d).setdefault(f"{kz}-{p}", [])
        if not any(x.get("mac") == mac for x in liste):
            liste.append({"ref": ref, "mac": mac, "name": text_einzeilig(c.get("name") or c.get("hostname") or "Gerät", 60), "zeit": time.strftime("%d.%m.%Y %H:%M")})
        del liste[:-20]
        _GERAETE_CACHE["zeit"] = 0
        speichere(d)
        journal(f"Mitgliederbereich: Gerät in {kz} Parzelle {p} vom Mitglied gesperrt")
        return {"ok": True, "text": "Das Gerät ist gesperrt und kommt nicht mehr ins Netz. Unter „Gesperrte Geräte“ können Sie es wieder zulassen."}
    if str(c.get("type") or "").upper() == "WIRED":
        raise Fehler("Geräte am Kabel können nicht getrennt werden – nur WLAN-Geräte.")
    Gateway(d).legacy_cmd("cmd/stamgr", {"cmd": "kick-sta", "mac": mac})
    _GERAETE_CACHE["zeit"] = 0
    journal(f"Mitgliederbereich: WLAN-Gerät in {kz} Parzelle {p} vom Mitglied getrennt")
    return {"ok": True, "text": "Das Gerät ist vom WLAN getrennt. Es kann sich bei Bedarf jederzeit wieder verbinden."}


def mb_geraet_zulassen(d, kz, p, b):
    """vom Mitglied gesperrtes Gerät wieder zulassen (unblock-sta) – auch wenn das Sperren inzwischen ausgeschaltet ist"""
    liste = gesperrte_geraete(d).get(f"{kz}-{p}", [])
    x = next((x for x in liste if hmac.compare_digest(str(x.get("ref", "")), str(b.get("ref") or ""))), None)
    if not x:
        raise Fehler("Dieses Gerät ist für Ihre Parzelle nicht gesperrt.")
    Gateway(d).legacy_cmd("cmd/stamgr", {"cmd": "unblock-sta", "mac": x["mac"]})
    liste.remove(x)
    speichere(d)
    journal(f"Mitgliederbereich: Gerät in {kz} Parzelle {p} vom Mitglied wieder zugelassen")
    return {"ok": True, "text": "Das Gerät ist wieder zugelassen und kann sich neu verbinden."}


def akt_mitglied_trennen_pruefen(d):
    """Administrator: lässt das Gateway über die UniFi-Cloud das Trennen/Sperren von Geräten zu?
    Harmloser Test: „kick-sta“ an eine MAC-Adresse, die es nicht gibt (00:00:00:00:00:00) – trennt nichts, sperrt nichts.
    Die offizielle Network-Schnittstelle (Integration API) kennt für Geräte nur Gastzugang erlauben/entziehen, deshalb nutzt
    das Trennen die klassische Schnittstelle cmd/stamgr (kick-sta) über den Cloud-Connector."""
    g = Gateway(d)
    code, a = http("POST", f"{g.leg_base}/cmd/stamgr", g.key, {"cmd": "kick-sta", "mac": "00:00:00:00:00:00"})
    text = a if isinstance(a, str) else json.dumps(a)
    if code < 300 or (code == 400 and "api.err" in text):
        ok, meldung = True, ("✔ Das Gateway nimmt Befehle zum Trennen an (klassische Schnittstelle über die Cloud erreichbar). "
                             "Mitglieder können Geräte trennen, sobald der Schalter eingeschaltet ist.")
    elif code in (401, 403):
        ok, meldung = False, (f"✖ Abgelehnt ({code}): Der API-Schlüssel darf keine Befehle an Geräte senden. "
                              "Bitte einen Schlüssel eines Kontos mit Administratorrechten (Site Manager → API) verwenden.")
    elif code == 405:
        ok, meldung = False, "✖ Die UniFi-Cloud lässt diesen Befehl nicht durch (405) – Geräte trennen ist über die Cloud nicht möglich."
    elif code == 404:
        ok, meldung = False, "✖ Die klassische Schnittstelle ist über die Cloud nicht erreichbar (404) – Firmware/Network-Version prüfen."
    else:
        ok, meldung = False, f"✖ Unerwartete Antwort vom Gateway ({code}): {text[:200]}"
    journal(f"Geräte-trennen-Prüfung: {'möglich' if ok else 'nicht möglich'} ({code})")
    return {"ok": ok, "code": code, "log": [meldung]}


def _tarif_info(t):
    return {"name": t["name"], "down": t["down"], "up": t["up"], "preis": t.get("preis", 0), "geraete": t.get("geraete", 0),
            "laufzeit": laufzeit_text(t.get("laufzeit", 0), t.get("laufzeit_einheit", "tage"))}


def tarif_rang(t):
    """Reihenfolge für Up-/Downgrade: Preis, dann Download, dann Upload"""
    return (float(t.get("preis") or 0), float(t.get("down") or 0), float(t.get("up") or 0)) if t else (0, 0, 0)


def tarif_seit(d, kz, p):
    """Zeitpunkt des letzten Tarifwechsels bzw. der Buchung (für die Wartezeit vor einem Downgrade)"""
    k = f"{kz}-{int(p)}"
    t = (d.get("tarif_seit") or {}).get(k) or (laufzeiten(d).get(k) or {}).get("start")
    try:
        return float(t or 0)
    except (TypeError, ValueError):
        return 0.0


def _tarif_ereignis(typ, daten, d):
    """merkt sich den Zeitpunkt jeder Buchung bzw. jedes Tarifwechsels; bei Kündigung entfallen auch die Zusatzgeräte"""
    if typ not in ("buchung", "kuendigung") or d is None or not str(daten.get("parzelle") or "").isdigit():
        return
    k = f"{daten.get('sparte')}-{int(daten['parzelle'])}"
    if typ == "buchung":
        alt = daten.get("tarif_alt") or ""
        if alt and alt != daten.get("tarif"):          # Restguthaben: nicht genutzte Laufzeit des alten Tarifs gutschreiben (läuft vor dem Neustart der Laufzeit)
            lz = laufzeiten(d).get(k) or {}
            rest = restwert(d, daten.get("sparte"), daten["parzelle"]) if lz.get("tarif") == alt else 0
            if rest > 0:
                guthaben_buchen(d, daten.get("sparte"), daten["parzelle"], rest,
                                f"Restguthaben {alt} (Laufzeit bis {time.strftime('%d.%m.%Y', time.localtime(lz['ende']))})")
        d.setdefault("tarif_seit", {})[k] = time.time()
    else:
        (d.get("tarif_seit") or {}).pop(k, None)
        (d.get("zusatzgeraete") or {}).pop(k, None)


EREIGNIS_EMPFAENGER.insert(0, _tarif_ereignis)


def downgrade_info(d, kz, p, e=None):
    """Wechsel in einen kleineren Tarif: welche Tarife (nur eine Stufe nach unten) und ab wann (x Monate nach dem letzten Wechsel)"""
    e = e or mb_einstellungen(d)
    alle = {x["name"]: x for x in tarife_pruefen(d["tarife"])}
    akt = alle.get(((d.get("buchungen") or {}).get(kz) or {}).get(str(p), ""))
    if not akt:
        return {"ziele": [], "ab": 0, "ab_text": ""}
    kleiner = sorted((t for t in mb_buchbar(d) if tarif_rang(t) < tarif_rang(akt)), key=tarif_rang, reverse=True)
    ziele = [t["name"] for t in (kleiner[:1] if e["downgrade_stufe"] else kleiner)]
    seit = tarif_seit(d, kz, p)
    ab = plus_laufzeit(seit, e["downgrade_monate"], "monate") if e["downgrade_monate"] and seit else 0
    if ab <= time.time():
        ab = 0
    return {"ziele": ziele, "ab": ab, "ab_text": time.strftime("%d.%m.%Y", time.localtime(ab)) if ab else "", "monate": e["downgrade_monate"]}


def _geraete_zaehlen(d, kz, p):
    """verbundene Geräte der Parzelle (frisch vom Gateway). Ist das Gateway nicht erreichbar, zählt 0 – die Grenze setzt dann
    der DHCP-Bereich des Tarifs am Gateway durch."""
    _GERAETE_CACHE["zeit"] = 0
    try:
        return len(_geraete_roh(d, kz, p)[0])
    except Fehler:
        return 0


def downgrade_pruefen(d, kz, p, ziel, e=None):
    """Regeln für den Wechsel in einen kleineren Tarif – wirft Fehler mit verständlichem Text:
    nur eine Stufe nach unten, frühestens x Monate nach dem letzten Wechsel, und nicht mehr Geräte verbunden als der neue Tarif erlaubt"""
    e = e or mb_einstellungen(d)
    info = downgrade_info(d, kz, p, e)
    aktuell = ((d.get("buchungen") or {}).get(kz) or {}).get(str(p), "")
    if ziel["name"] not in info["ziele"]:
        if info["ziele"]:
            raise Fehler(f"Ein kleinerer Tarif geht nur eine Stufe nach unten – von {aktuell} zu {info['ziele'][0]}.")
        raise Fehler("Einen kleineren Tarif gibt es hier nicht.")
    if info["ab"]:
        raise Fehler(f"Ein Wechsel in einen kleineren Tarif ist frühestens ab {info['ab_text']} möglich ({info['monate']} Monate nach dem letzten Tarifwechsel).")
    erlaubt = geraete_im_tarif(d, ziel, kz, p)
    if erlaubt:
        if zusatz_geraete(d, kz, p) > zusatz_platz(ziel):
            raise Fehler(f"Im Tarif {ziel['name']} ist Platz für höchstens {zusatz_platz(ziel)} Zusatzgeräte – bitte vorher Zusatzgeräte reduzieren.")
        n = _geraete_zaehlen(d, kz, p)
        if n > erlaubt:
            raise Fehler(f"Zu viele Geräte: {n} sind verbunden, {ziel['name']} erlaubt {erlaubt}. Bitte vorher {n - erlaubt} Gerät(e) sperren "
                         "oder ausschalten – dann ist der Wechsel möglich.")


def _wechsel_rechnung(d, kz, p, tarif, wer):
    """nach einem Tarifwechsel (ohne Bezahldienst): Rechnung über den neuen Tarif mit neuer Laufzeit, abzüglich Guthaben
    (Restguthaben des alten Tarifs). Übersteigt das Guthaben den Preis, bleibt der Rest für spätere Rechnungen stehen."""
    if not mb_einstellungen(d)["wechsel_rechnung"]:
        return None
    t = next((x for x in tarife_pruefen(d["tarife"]) if x["name"] == tarif), None)
    if not t or not float(t.get("preis") or 0):
        return None
    lz = laufzeiten(d).get(f"{kz}-{int(p)}") or {}
    bis = f" bis {time.strftime('%d.%m.%Y', time.localtime(lz['ende']))}" if lz.get("ende") else ""
    pos = [{"text": f"WLAN-Tarif „{tarif}“, Parzelle {p}, neue Laufzeit ab {time.strftime('%d.%m.%Y')}{bis}", "menge": 1,
            "einzel": round(float(t["preis"]), 2), "gesamt": round(float(t["preis"]), 2)}]
    abzug, g = _guthaben_positionen(d, kz, p, float(t["preis"]))
    try:
        _rid, x = rechnung_anlegen(d, kz, p, tarif, pos + abzug, wer, notiz="Tarifwechsel")
    except Fehler as f:
        LOG.warning("Rechnung zum Tarifwechsel nicht angelegt: %s", f)
        return None
    if g:
        guthaben_buchen(d, kz, p, -g, f"verrechnet mit Rechnung {x['nr']}")
    return x


def _zusatz_setzen(d, kz, p, n, wer):
    z = d.setdefault("zusatzgeraete", {})
    k = f"{kz}-{int(p)}"
    if n:
        z[k] = int(n)
    else:
        z.pop(k, None)
    speichere(d)
    journal(f"Zusatzgeräte {kz} Parzelle {p}: jetzt {n} ({wer})")


def akt_zusatzgeraete(d, b, ich):
    """Manager: Zusatzgeräte einer Parzelle setzen ({"sparte", "parzelle", "anzahl"}) – ohne Prüfung der verbundenen Geräte"""
    kz, p = str(b.get("sparte") or ""), str(b.get("parzelle") or "")
    if not p.isdigit():
        raise Fehler("Parzelle fehlt.")
    t = next((x for x in tarife_pruefen(d["tarife"]) if x["name"] == ((d.get("buchungen") or {}).get(kz) or {}).get(p)), None)
    try:
        n = int(b.get("anzahl") or 0)
    except (TypeError, ValueError):
        raise Fehler("Anzahl Zusatzgeräte: ganze Zahl.")
    if n and (not t or not t.get("geraete")):
        raise Fehler("Zusatzgeräte gibt es nur bei einem Tarif mit begrenzter Geräteanzahl.")
    if not 0 <= n <= zusatz_platz(t):
        raise Fehler(f"Im Tarif {t['name']} passen 0 bis {zusatz_platz(t)} Zusatzgeräte ins Netz (Netzmaske /{t['praefix']}).")
    _zusatz_setzen(d, kz, p, n, ich)
    return {"log": [f"✔ {kz} Parzelle {p}: {n} Zusatzgerät(e) – ans Gateway über „Tarife → Übertragen“."]}


def mb_buchbar(d):
    """im Mitgliederbereich buchbare Tarife (Auswahl in den Einstellungen; leer = alle)"""
    wahl = mb_einstellungen(d)["tarife"]
    return [t for t in tarife_pruefen(d["tarife"]) if not wahl or t["name"] in wahl]


def mb_tickets(d, mid, m):
    """nur die Tickets dieser Parzelle: fest zugeordnet (an ein Mitglied der Parzelle) – oder ohne Zuordnung mit passender E-Mail und Parzelle"""
    kz, p = m.get("sparte", ""), str(m.get("parzelle") or "")
    ids = _parzellen_ids(d, kz, p) | {mid}
    aus, gesehen = [], set()
    for x in ids:
        for i, t in mitglied_tickets(d, x):
            k = t.get("kontakt") or {}
            if i not in gesehen and (k.get("mitglied") in ids or (not k.get("mitglied") and str(t.get("sparte") or "") == kz and str(t.get("parzelle") or "") == p)):
                gesehen.add(i)
                aus.append((i, t))
    aus.sort(key=lambda x: x[1].get("erstellt", ""), reverse=True)
    return aus


def tarif_antraege(d, kz=None, p=None, offen=True):
    """[(ticket_id, ticket)] mit Tarif-Antrag (Downgrade, oder Buchung/Verlängerung im Modus „Anfrage“)"""
    return [(i, t) for i, t in tickets_daten(d)["liste"].items() if isinstance(t.get("antrag"), dict)
            and (kz is None or t["antrag"].get("sparte") == kz) and (p is None or str(t["antrag"].get("parzelle")) == str(p))
            and (not offen or t["antrag"].get("status") == "offen")]


def mb_stoerungen(d, e, kz, nur_alle=False):
    """Meldungen für die Störungsanzeige im Mitgliederbereich (nur_alle: nur Geräte ohne Spartenzuordnung – für die Anmeldeseite)"""
    if not e["stoerung_zeigen"]:
        return []
    aus = []
    for s in aktuelle_stoerungen(d, kz, nur_alle):
        t = (e["stoerung_meldung"] or MB_STANDARD["stoerung_meldung"])
        for k, v in (("geraet", s["geraet"]), ("modell", s["modell"]), ("seit", s["seit"]), ("ticket", s["ticket"])):
            t = t.replace("{" + k + "}", v)
        aus.append({**s, "text": re.sub(r"\s{2,}", " ", t.replace("()", "")).strip()})
    return aus


def mb_daten(d, email):
    e = mb_einstellungen(d)
    tarife = [{**_tarif_info(t), "rang": list(tarif_rang(t))} for t in mb_buchbar(d)]
    parz = []
    for mid, m in sorted(mb_mitglieder_von(d, email).items(), key=lambda x: (x[1].get("sparte", ""), str(x[1].get("parzelle", "")))):
        kz, p = m.get("sparte", ""), str(m.get("parzelle") or "")
        tarif = ((d.get("buchungen") or {}).get(kz) or {}).get(p, "") if kz and p else ""
        lz = laufzeiten(d).get(f"{kz}-{p}") if kz and p.isdigit() else None
        gesp = zugang_gesperrt(d).get(f"{kz}-{p}") if kz and p.isdigit() else None
        rechn = [{"id": i, "nr": x.get("nr"), "datum": x.get("datum"), "faellig": x.get("faellig"), "brutto": x.get("brutto"), "bezahlt": x.get("bezahlt"),
                  "status": R_STATUS.get(x.get("status"), x.get("status"))} for i, x in rechnungen_daten(d)["liste"].items()
                 if x.get("status") != "storniert" and (x.get("mitglied") == mid or (kz and x.get("sparte") == kz and str(x.get("parzelle") or "") == p))]
        rechn.sort(key=lambda x: x.get("datum") or "", reverse=True)
        akt_t = next((t for t in tarife_pruefen(d["tarife"]) if t["name"] == tarif), None)
        antr = [{"nr": t["nr"], "art": t["antrag"]["art"], "tarif": t["antrag"]["tarif"], "erstellt": t.get("erstellt", "")}
                for _i, t in tarif_antraege(d, kz, p) if kz and p]
        tk = [{"nr": t.get("nr"), "betreff": t.get("betreff", ""), "status": T_STATUS.get(t.get("status"), ""), "erstellt": t.get("erstellt", ""),
               "loesung": t.get("loesung", "")} for _i, t in mb_tickets(d, mid, m)][:20] if e["zeige_anfragen"] else []
        offen_auftrag = next(({"referenz": r, "tarif": a.get("tarif"), "art": a.get("art"), "betrag": a.get("betrag")} for r, a in zahlungsauftraege(d).items()
                              if a.get("mitglied") == mid and a.get("status") == "offen" and a.get("erstellt", "") > time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() - 86400))), None)
        sl = sparten_logo_id(d, kz)
        parz.append({"id": mid, "sparte": kz, "sparte_name": _sparten_kz(d).get(kz, kz), "parzelle": p,
                     "sparte_logo": f"/spartenlogo/{urllib.parse.quote(kz)}?v={sl[:6]}" if sl else "", "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(),
                     "haupt": bool(m.get("_haupt")), "personen": _mb_personen(d, mid),
                     "tarif": tarif, "laufzeit": ({"start": time.strftime("%d.%m.%Y %H:%M", time.localtime(lz["start"])), "ende": time.strftime("%d.%m.%Y %H:%M", time.localtime(lz["ende"])),
                                                   "aktiv": lz.get("status") == "aktiv", "rest_tage": max(0, int((lz["ende"] - time.time()) // 86400))} if lz else None),
                     "gesperrt": bool(gesp), "rechnungen": rechn, "offen": round(sum(float(x["brutto"] or 0) - float(x["bezahlt"] or 0) for x in rechn), 2),
                     "tickets": tk, "auftrag": offen_auftrag, "stoerungen": mb_stoerungen(d, e, kz), "antraege": antr, "rang": list(tarif_rang(akt_t)) if akt_t else None,
                     **({"tarif_laufzeit": laufzeit_text(akt_t.get("laufzeit", 0), akt_t.get("laufzeit_einheit", "tage")) if akt_t.get("laufzeit") else "unbegrenzt",
                         "tarif_preis": akt_t.get("preis", 0), "tarif_down": akt_t["down"], "tarif_up": akt_t["up"], "tarif_geraete": akt_t.get("geraete", 0),
                         "zusatz": zusatz_geraete(d, kz, p), "zusatz_platz": min(e["zusatz_max"], zusatz_platz(akt_t)),
                         "geraete_erlaubt": geraete_im_tarif(d, akt_t, kz, p), "downgrade": downgrade_info(d, kz, p, e),
                         "restwert": restwert(d, kz, p)} if akt_t else {}),
                     "guthaben": guthaben(d, kz, p) if kz and p.isdigit() else 0})
    return {"mitglied": parz[0]["name"] if parz else "", "parzellen": parz, "tarife": tarife,
            "erlaubt": {k: e[k] for k in ("tarifwechsel", "downgrade", "neubuchung", "verlaengern", "geraete", "zeige_rechnungen", "zeige_anfragen", "neue_anfrage", "zugangskarte", "profil", "personen", "geraete_trennen", "geraete_sperren", "zusatzgeraete", "downgrade_freigabe")},
            "zusatz_preis": e["zusatz_preis"], "profil": mb_profil(d, email),
            "modus": e["modus"], "hinweis": e["hinweis"], "titel": e["titel"], "kategorien": list(ticket_kategorien(d)),
            "stoerung_text": e["stoerung_text"] if e["stoerung_zeigen"] else "", "stoerung_farbe": e["stoerung_farbe"],
            "logo_verein": "/seitenbild/portal/logo" if seitenbild(d, "portal", "logo") else ""}


def _mb_parzelle(d, email, mid):
    m = mb_mitglieder_von(d, email).get(str(mid or ""))
    if not m or not m.get("sparte") or not str(m.get("parzelle") or "").isdigit():
        raise Fehler("Parzelle nicht gefunden.")
    return str(mid), m, m["sparte"], str(m["parzelle"])


# ---- Profil und weitere Personen der Parzelle ---------------------------------------------------------------------------
_MB_EMAILWECHSEL = {}


def _mb_personen(d, mid):
    m = mitglieder(d).get(mid) or {}
    return [{"vorname": x.get("vorname", ""), "nachname": x.get("nachname", ""), "email": x.get("email", ""), "haupt": x["haupt"]} for x in personen(m)]


def mb_profil(d, email):
    """eigene Angaben: Vorname, Nachname und Parzelle(n) nur zum Lesen; Telefon, Mobil und E-Mail änderbar"""
    treffer = sorted(mb_mitglieder_von(d, email).items(), key=lambda x: (x[1].get("sparte", ""), str(x[1].get("parzelle", ""))))
    if not treffer:
        return {}
    m = treffer[0][1]
    return {"vorname": m.get("vorname", ""), "nachname": m.get("nachname", ""), "email": m.get("email", ""), "telefon": m.get("telefon", ""),
            "mobil": m.get("mobil", ""), "haupt": any(x.get("_haupt") for _i, x in treffer),
            "parzellen": [f"{_sparten_kz(d).get(x.get('sparte', ''), x.get('sparte', ''))} · Parzelle {x.get('parzelle', '')}" for _i, x in treffer]}


def _mb_person_eintraege(d, email):
    """[(Mitglied, Eintrag)] – der Eintrag ist das Mitglied selbst oder eine weitere Person mit dieser E-Mail-Adresse"""
    e = name_norm(email)
    aus = []
    for m in mitglieder(d).values():
        if m.get("email") and name_norm(m["email"]) == e:
            aus.append((m, m))
        for w in m.get("weitere") or []:
            if isinstance(w, dict) and w.get("email") and name_norm(w["email"]) == e:
                aus.append((m, w))
    return aus


def _email_gueltig(x):
    return bool(re.fullmatch(r"[^@\s,;<>]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,}", x))


def mb_profil_speichern(d, email, b):
    """Telefon und Mobil sofort; eine neue E-Mail-Adresse erst nach dem Code, der an die neue Adresse geht"""
    if not mb_einstellungen(d)["profil"]:
        raise Fehler("Das Profil kann hier nicht geändert werden – bitte beim Verein melden.")
    werte = {k: text_einzeilig(b.get(k) or "", 30).strip() for k in ("telefon", "mobil") if k in b}
    for k, t in (("telefon", "Telefonnummer"), ("mobil", "Mobilnummer")):
        if werte.get(k) and not _TEL_RE.match(werte[k]):
            raise Fehler(f"{t}: nur Ziffern, Leerzeichen und + ( ) / -.")
    eintraege = _mb_person_eintraege(d, email)
    if not eintraege:
        raise Fehler("Profil nicht gefunden.")
    for m, x in eintraege:
        x.update(werte)
        m["geaendert"] = time.strftime("%Y-%m-%d %H:%M")
    antwort = {"ok": True, "text": "Gespeichert."}
    neu = str(b.get("email") or "").strip().lower()
    if neu and name_norm(neu) != name_norm(email):
        if not _email_gueltig(neu):
            raise Fehler("Bitte eine gültige E-Mail-Adresse eingeben.")
        if mb_mitglieder_von(d, neu):
            raise Fehler("Diese E-Mail-Adresse ist schon bei einem Mitglied eingetragen – bitte beim Verein melden.")
        if not mb_versand_bereit(d):
            raise Fehler("Die E-Mail-Adresse kann gerade nicht geändert werden (E-Mail-Versand des Vereins nicht eingerichtet).")
        _grenze("mb_code_mail", name_norm(neu))
        code = f"{secrets.randbelow(1000000):06d}"
        with _MB_LOCK:
            _MB_EMAILWECHSEL[name_norm(email)] = {"neu": neu, "hash": _mb_hash(code), "bis": time.time() + 600, "versuche": 0}
        m0 = eintraege[0][1]
        email_senden(d, neu, f"Bestätigungscode: {code}", None,
                     f"<p>Hallo {html_mod.escape(m0.get('vorname') or '')},</p><p>mit diesem Code bestätigen Sie Ihre neue E-Mail-Adresse für den Mitgliederbereich:</p>"
                     f"<p style='font-size:28px;letter-spacing:6px;font-weight:bold'>{code}</p><p>Er gilt 10 Minuten. Haben Sie das nicht veranlasst, ignorieren Sie diese E-Mail.</p>",
                     sparte=eintraege[0][0].get("sparte") or None)
        antwort = {"ok": True, "bestaetigen": True, "text": f"Gespeichert. An {neu} ist ein Code unterwegs – bitte eingeben, um die neue E-Mail-Adresse zu bestätigen."}
    speichere(d)
    journal("Mitgliederbereich: Profil eines Mitglieds geändert")
    return antwort


def mb_profil_bestaetigen(d, email, b):
    alt = name_norm(email)
    code = re.sub(r"\D", "", str(b.get("code") or ""))
    with _MB_LOCK:
        w = _MB_EMAILWECHSEL.get(alt)
        if not w or time.time() > w["bis"] or w["versuche"] >= 5:
            _MB_EMAILWECHSEL.pop(alt, None)
            raise Fehler("Der Code ist abgelaufen oder ungültig – bitte die E-Mail-Adresse erneut speichern.")
        if not hmac.compare_digest(w["hash"], _mb_hash(code)):
            w["versuche"] += 1
            raise Fehler("Der Code stimmt nicht.")
        _MB_EMAILWECHSEL.pop(alt, None)
    neu = w["neu"]
    if mb_mitglieder_von(d, neu):
        raise Fehler("Diese E-Mail-Adresse ist inzwischen schon eingetragen – bitte beim Verein melden.")
    eintraege = _mb_person_eintraege(d, email)
    if not eintraege:
        raise Fehler("Profil nicht gefunden.")
    alte_adresse = eintraege[0][1].get("email", "")
    for m, x in eintraege:
        x["email"] = neu
        m["geaendert"] = time.strftime("%Y-%m-%d %H:%M")
    for a in mitglied_apps(d).values():          # angemeldete Apps bleiben angemeldet
        if a.get("email") == alt:
            a["email"] = name_norm(neu)
    with _MB_LOCK:
        for s in _MB_SITZ.values():
            if s.get("email") == alt:
                s["email"] = name_norm(neu)
    speichere(d)
    journal("Mitgliederbereich: E-Mail-Adresse eines Mitglieds geändert (mit Code bestätigt)")
    _mb_mail(d, {"email": alte_adresse, "vorname": eintraege[0][1].get("vorname", ""), "sparte": eintraege[0][0].get("sparte")},
             "Ihre E-Mail-Adresse wurde geändert", f"<p>Ihre E-Mail-Adresse für den Mitgliederbereich wurde auf <b>{html_mod.escape(neu)}</b> geändert. "
             "Waren Sie das nicht, melden Sie sich bitte sofort beim Verein.</p>")
    return {"ok": True, "text": "Ihre neue E-Mail-Adresse ist bestätigt.", "email": neu}


def mb_person_neu(d, email, b):
    """der Pächter trägt eine weitere Person seiner Parzelle ein (Mitpächter, Partner …) – sie meldet sich mit ihrer E-Mail-Adresse an"""
    if not mb_einstellungen(d)["personen"]:
        raise Fehler("Weitere Personen kann hier nur der Verein eintragen.")
    mid, m, kz, p = _mb_parzelle(d, email, b.get("id"))
    if not m.get("_haupt"):
        raise Fehler("Weitere Personen kann nur der Pächter der Parzelle eintragen.")
    neu = {k: text_einzeilig(b.get(k) or "", 120).strip() for k in ("vorname", "nachname", "email", "telefon", "mobil")}
    if not (neu["vorname"] and neu["nachname"]):
        raise Fehler("Bitte Vorname und Nachname angeben.")
    if not _email_gueltig(neu["email"]):
        raise Fehler("Bitte eine gültige E-Mail-Adresse angeben – damit meldet sich die Person an.")
    rec = mitglieder(d)[mid]
    rec["weitere"] = weitere_pruefen([dict(x) for x in (rec.get("weitere") or []) if isinstance(x, dict)] + [neu], rec.get("email", ""))
    rec["geaendert"] = time.strftime("%Y-%m-%d %H:%M")
    speichere(d)
    journal(f"Mitgliederbereich: weitere Person für {kz} Parzelle {p} vom Pächter eingetragen")
    wo = mb_einstellungen(d)["titel"]
    _mb_mail(d, {"email": neu["email"], "vorname": neu["vorname"], "sparte": kz}, f"Sie sind für Parzelle {p} eingetragen",
             f"<p>{html_mod.escape(m.get('vorname', ''))} {html_mod.escape(m.get('nachname', ''))} hat Sie als weitere Person für Parzelle {p} "
             f"({html_mod.escape(_sparten_kz(d).get(kz, kz))}) eingetragen.</p><p>Sie können sich jetzt im {html_mod.escape(wo)} oder in der App „SparteNet Mitglied“ "
             "mit dieser E-Mail-Adresse und einem Einmalcode anmelden.</p>")
    return {"ok": True, "text": f"{neu['vorname']} {neu['nachname']} ist eingetragen und per E-Mail informiert."}


def mb_person_entfernen(d, email, b):
    if not mb_einstellungen(d)["personen"]:
        raise Fehler("Weitere Personen kann hier nur der Verein ändern.")
    mid, m, kz, p = _mb_parzelle(d, email, b.get("id"))
    if not m.get("_haupt"):
        raise Fehler("Weitere Personen kann nur der Pächter der Parzelle entfernen.")
    weg = name_norm(b.get("email"))
    rec = mitglieder(d)[mid]
    vorher = [x for x in (rec.get("weitere") or []) if isinstance(x, dict)]
    rec["weitere"] = [x for x in vorher if name_norm(x.get("email")) != weg]
    if len(rec["weitere"]) == len(vorher):
        raise Fehler("Diese Person ist bei Ihrer Parzelle nicht eingetragen.")
    rec["geaendert"] = time.strftime("%Y-%m-%d %H:%M")
    speichere(d)
    journal(f"Mitgliederbereich: weitere Person bei {kz} Parzelle {p} vom Pächter entfernt")
    return {"ok": True, "text": "Die Person ist entfernt."}


# ---- App-Updates: neue APK (Mitglieder-App oder Manager-App) im Manager hochladen, die App lädt sie herunter -------------
APP_ARTEN = {"mitglied": "Mitglieder-App „SparteNet Mitglied“", "manager": "Manager-App „SparteNet Manager“"}


def app_apk_pfad(art):
    return os.path.join(HIER, f"SparteNet_{'Mitglied' if art == 'mitglied' else 'Manager'}_App.apk")


def _app_dateien(d):
    a = d.get("app_dateien")
    if not isinstance(a, dict):
        a = {}
        d["app_dateien"] = a
    return a


def app_update_info(d, art):
    """Angaben zur hochgeladenen Version (ohne Datei: leer) – für die App, um ein Update zu melden"""
    a = (d.get("app_dateien") or {}).get(art) if isinstance(d.get("app_dateien"), dict) else None
    if not isinstance(a, dict) or not os.path.isfile(app_apk_pfad(art)):
        return {}
    return {k: a.get(k) for k in ("version_code", "version_name", "sha256", "groesse", "hinweis", "hochgeladen")}


def app_apk_lesen(d, art):
    if not app_update_info(d, art):
        raise Fehler("Kein Update hinterlegt.")
    with open(app_apk_pfad(art), "rb") as f:
        return f.read()


def akt_app_update(d, b=None, ich=""):
    """Administrator: hochgeladene Versionen beider Apps ansehen oder eine entfernen ({"art": "mitglied", "entfernen": true})"""
    log = []
    if isinstance(b, dict) and b.get("entfernen"):
        art = b.get("art")
        if art not in APP_ARTEN:
            raise Fehler("Unbekannte App.")
        _app_dateien(d).pop(art, None)
        try:
            os.remove(app_apk_pfad(art))
        except FileNotFoundError:
            pass
        speichere(d)
        journal(f"App-Update ({art}) entfernt durch {ich}")
        log = [f"✔ Update der {APP_ARTEN[art]} entfernt – die App meldet kein Update mehr."]
    return {"apps": {k: {"titel": t, **app_update_info(d, k)} for k, t in APP_ARTEN.items()}, "log": log}


def apk_version(roh):
    """liest versionCode, versionName und Paketname aus der APK (binäres AndroidManifest.xml) – (code, name, paket) oder (None, "", "")"""
    import struct
    try:
        with zipfile.ZipFile(io.BytesIO(roh)) as z:
            m = z.read("AndroidManifest.xml")
    except (zipfile.BadZipFile, KeyError):
        return None, "", ""
    if len(m) < 8 or struct.unpack_from("<H", m, 0)[0] != 0x0003:
        return None, "", ""
    strings, res_ids, pos = [], [], 8
    while pos + 8 <= len(m):
        typ, kopf, groesse = struct.unpack_from("<HHI", m, pos)
        if groesse < 8:
            break
        if typ == 0x0001:                          # String-Pool
            anzahl, _stile, flags, start = struct.unpack_from("<IIII", m, pos + 8)
            utf8 = bool(flags & 0x100)
            for n in range(anzahl):
                o = pos + start + struct.unpack_from("<I", m, pos + kopf + 4 * n)[0]
                if utf8:
                    o += 2 if m[o] & 0x80 else 1               # Länge in UTF-16-Zeichen
                    laenge = ((m[o] & 0x7F) << 8 | m[o + 1]) if m[o] & 0x80 else m[o]
                    o += 2 if m[o] & 0x80 else 1
                    strings.append(m[o:o + laenge].decode("utf-8", "replace"))
                else:
                    laenge = struct.unpack_from("<H", m, o)[0]
                    if laenge & 0x8000:
                        laenge = ((laenge & 0x7FFF) << 16) | struct.unpack_from("<H", m, o + 2)[0]
                        o += 2
                    strings.append(m[o + 2:o + 2 + 2 * laenge].decode("utf-16-le", "replace"))
        elif typ == 0x0180:                        # Ressourcen-Kennungen der Attributnamen
            res_ids = list(struct.unpack_from(f"<{(groesse - kopf) // 4}I", m, pos + kopf))
        elif typ == 0x0102:                        # erstes Element: <manifest …>
            a_start, a_groesse, a_anzahl = struct.unpack_from("<HHH", m, pos + kopf + 8)
            code, name, paket = None, "", ""
            for n in range(a_anzahl):
                o = pos + kopf + a_start + n * a_groesse
                _ns, nm, rohwert, _sz, _r, dtyp, daten = struct.unpack_from("<IIIHBBI", m, o)
                rid = res_ids[nm] if nm < len(res_ids) else 0
                text = strings[rohwert] if rohwert != 0xFFFFFFFF and rohwert < len(strings) else (strings[daten] if dtyp == 0x03 and daten < len(strings) else "")
                if rid == 0x0101021B:
                    code = daten if dtyp in (0x10, 0x11) else (int(text) if text.isdigit() else None)
                elif rid == 0x0101021C:
                    name = text
                elif nm < len(strings) and strings[nm] == "package":
                    paket = text
            return code, name, paket
        pos += groesse
    return None, "", ""


APP_PAKETE = {"mitglied": "de.spartenet.mitglied", "manager": "de.spartenet.manager"}


def akt_app_update_hochladen(d, q, roh, ich):
    """neue APK hochladen (?art=mitglied|manager&hinweis=…; versionCode und -name liest der Manager aus der APK, sonst
    ?version_code=…&version_name=…). Die App meldet das Update,
    lädt die Datei herunter, prüft die SHA-256-Prüfsumme und startet die Installation. Android installiert ein Update nur,
    wenn die APK mit demselben Schlüssel signiert ist wie die installierte App."""
    art = (q.get("art") or [""])[0]
    if art not in APP_ARTEN:
        raise Fehler("Bitte wählen: Mitglieder-App oder Manager-App.")
    apk_code, apk_name, apk_paket = apk_version(roh or b"")        # Versionsnummer und -name stehen in der APK selbst
    if apk_paket and apk_paket.split(".debug")[0] != APP_PAKETE[art]:
        raise Fehler(f"Diese APK gehört nicht zur {APP_ARTEN[art]} (Paket {apk_paket}) – bitte die richtige App wählen.")
    roh_vc = (q.get("version_code") or [""])[0].strip()
    try:
        vc = apk_code if apk_code is not None else int(roh_vc)
    except ValueError:
        raise Fehler("Die Versionsnummer ließ sich nicht aus der APK lesen – bitte versionCode als ganze Zahl angeben.")
    vn = text_einzeilig(apk_name or (q.get("version_name") or [""])[0], 60).strip() or str(vc)
    hinweis = text_einzeilig((q.get("hinweis") or [""])[0], 300).strip()
    if not 1 <= vc <= 2_100_000_000:
        raise Fehler("Versionsnummer (versionCode) muss größer als 0 sein.")
    alt = app_update_info(d, art)
    if alt and vc <= int(alt.get("version_code") or 0):
        raise Fehler(f"Die Versionsnummer muss größer sein als die bisherige ({alt.get('version_code')}).")
    if not roh or len(roh) < 1000 or not roh.startswith(b"PK\x03\x04"):
        raise Fehler("Das ist keine APK-Datei.")
    try:
        with zipfile.ZipFile(io.BytesIO(roh)) as z:
            namen = set(z.namelist())
    except zipfile.BadZipFile:
        raise Fehler("Das ist keine gültige APK-Datei.")
    if "AndroidManifest.xml" not in namen or not any(n.startswith("classes") and n.endswith(".dex") for n in namen):
        raise Fehler("Das ist keine Android-App (AndroidManifest.xml oder classes.dex fehlt).")
    ziel = app_apk_pfad(art)
    with open(ziel + ".neu", "wb") as f:
        f.write(roh)
    os.replace(ziel + ".neu", ziel)
    _app_dateien(d)[art] = {"version_code": vc, "version_name": vn, "hinweis": hinweis, "sha256": hashlib.sha256(roh).hexdigest(),
                            "groesse": len(roh), "hochgeladen": time.strftime("%d.%m.%Y %H:%M"), "von": ich}
    speichere(d)
    journal(f"App-Update {art}: Version {vn} ({vc}) hochgeladen durch {ich}")
    r = akt_app_update(d)
    r["log"] = [f"✔ {APP_ARTEN[art]}: Version {vn} hochgeladen. Die Apps melden das Update beim nächsten Öffnen."]
    return r


# ---- Zahlungsaufträge -------------------------------------------------------------------------------------------------
def zahlungsauftraege(d):
    z = d.get("zahlungsauftraege")
    if not isinstance(z, dict):
        z = {}
        d["zahlungsauftraege"] = z
    return z


def _link_erzeugen(d, e, ref, a, basis):
    werte = {"referenz": ref, "betrag": f"{a['betrag']:.2f}", "betrag_cent": str(int(round(a["betrag"] * 100))), "email": a.get("email", ""),
             "beschreibung": a["beschreibung"], "rueckkehr": f"{basis}/mein?zahlung={ref}", "abbruch": f"{basis}/mein?zahlung=abbruch"}
    if e["link_api"]:
        roh = json.dumps({**werte, "betrag": a["betrag"], "sparte": a["sparte"], "parzelle": a["parzelle"], "tarif": a["tarif"],
                          "webhook": f"{basis}/mein/zahlung-webhook"}).encode()
        r = _ur.Request(e["link_api"], data=roh, method="POST", headers={"Content-Type": "application/json", "User-Agent": f"SparteNet/{VERSION}",
                                                                       "X-SparteNet-Signatur": "sha256=" + hmac.new(_mb_geheim(d).encode(), roh, hashlib.sha256).hexdigest()})
        try:
            with _ur.urlopen(r, timeout=15) as o:
                url = json.loads(o.read(200_000) or b"{}").get("url", "")
        except Exception as x:
            LOG.warning("Bezahldienst-Schnittstelle: %s", x)
            raise Fehler("Der Bezahldienst ist gerade nicht erreichbar – bitte später erneut versuchen.")
        if not re.match(r"^https://[^\s]+$", str(url)):
            raise Fehler("Der Bezahldienst hat keine gültige Bezahl-Adresse geliefert.")
        return url
    return re.sub(r"\{(\w+)\}", lambda mm: urllib.parse.quote(werte.get(mm.group(1), mm.group(0)), safe=""), e["checkout_vorlage"])


def _mb_ticket(d, mid, m, kz, p, betreff, text, status="neu", antrag=None):
    tid, tk = ticket_anlegen(d, {"betreff": betreff, "text": text, "status": status,
                                 "kategorie": "Buchung / Tarif" if "Buchung / Tarif" in ticket_kategorien(d) else "Sonstiges",
                                 "sparte": kz, "parzelle": p, "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(), "email": m.get("email", "")},
                             "Mitgliederbereich", "Mitgliederbereich")
    tk.setdefault("kontakt", {}).update(mitglied=mid, art="mitglied", geprueft=True, vorname=m.get("vorname", ""), nachname=m.get("nachname", ""))
    if antrag:
        tk["antrag"] = {**antrag, "status": "offen", "mitglied": mid}
    speichere(d)
    return tid, tk


def mb_buchen(d, email, b, basis):
    """Tarif wechseln, neu buchen oder Laufzeit verlängern.
    Upgrade (teurer/schneller): jederzeit – sofort gebucht bzw. über den Bezahldienst. Downgrade: nur als Antrag, der im Ticketsystem
    freigegeben werden muss. Neu buchen/Verlängern: im Modus „Anfrage“ als Antrag zur Freigabe, sonst über den Bezahldienst."""
    e = mb_einstellungen(d)
    mid, m, kz, p = _mb_parzelle(d, email, b.get("id"))
    art = b.get("art")
    if art not in ("neu", "wechsel", "verlaengern", "zusatz"):
        raise Fehler("Unbekannte Aktion.")
    aktuell = ((d.get("buchungen") or {}).get(kz) or {}).get(p, "")
    if art == "zusatz":
        return _mb_zusatz(d, e, mid, m, kz, p, aktuell, b, basis)
    tarif = str(b.get("tarif") or (aktuell if art == "verlaengern" else ""))
    alle = {x["name"]: x for x in tarife_pruefen(d["tarife"])}
    t = alle.get(tarif)
    if not t or (art != "verlaengern" and tarif not in {x["name"] for x in mb_buchbar(d)}):
        raise Fehler("Bitte einen der angebotenen Tarife wählen.")
    if art == "neu" and (aktuell or not e["neubuchung"]):
        raise Fehler("Neu buchen ist hier nicht möglich." if not e["neubuchung"] else "Die Parzelle hat schon einen Tarif – bitte „Tarif wechseln“.")
    if art == "verlaengern" and (not e["verlaengern"] or not aktuell or tarif != aktuell or not t.get("laufzeit")):
        raise Fehler("Verlängern ist für diesen Tarif nicht möglich.")
    upgrade = art == "wechsel" and tarif_rang(t) > tarif_rang(alle.get(aktuell))
    if art == "wechsel":
        if not aktuell:
            raise Fehler("Noch kein Tarif gebucht – bitte „Tarif buchen“.")
        if tarif == aktuell:
            raise Fehler("Bitte einen anderen Tarif wählen.")
        if upgrade and not e["tarifwechsel"]:
            raise Fehler("Ein Tarifwechsel ist hier nicht möglich – bitte beim Verein melden.")
        if not upgrade and not e["downgrade"]:
            raise Fehler("Ein Wechsel in einen kleineren Tarif ist hier nicht möglich – bitte beim Verein melden.")
    offen = tarif_antraege(d, kz, p)
    if offen and not upgrade:
        raise Fehler(f"Für diese Parzelle liegt schon ein Antrag beim Verein ({offen[0][1]['nr']}) – bitte die Entscheidung abwarten.")
    name = f"{m.get('vorname', '')} {m.get('nachname', '')}".strip()
    beschr = {"neu": f"Buchung {tarif}", "wechsel": f"{'Upgrade' if upgrade else 'Downgrade'} {aktuell} → {tarif}", "verlaengern": f"Verlängerung {tarif}"}[art] + f" · {kz} Parzelle {p}"
    preis = geld(float(t.get("preis") or 0))
    antrag = {"art": art, "sparte": kz, "parzelle": int(p), "tarif": tarif, "tarif_alt": aktuell}
    if art == "wechsel" and not upgrade:
        downgrade_pruefen(d, kz, p, t, e)          # eine Stufe, Wartezeit, nicht zu viele Geräte
    if art == "wechsel" and not upgrade and e["downgrade_freigabe"]:   # Downgrade mit Freigabe im Ticketsystem
        _tid, tk = _mb_ticket(d, mid, m, kz, p, f"Antrag: {beschr}", f"Antrag aus dem Mitgliederbereich: Wechsel von {aktuell} zu {tarif} ({preis}). "
                              "Bitte im Ticket freigeben oder ablehnen.", antrag=antrag)
        return {"ok": True, "text": f"Ihr Antrag {tk['nr']} auf Wechsel zu {tarif} ist beim Verein eingegangen. Ein Wechsel in einen kleineren Tarif muss freigegeben werden – Sie bekommen Bescheid."}
    if e["modus"] == "anfrage":
        if art == "wechsel":                       # Upgrade jederzeit, Downgrade nach den Regeln: sofort buchen (neue Laufzeit), Vorstand per Ticket informieren
            akt_buchungen_speichern(d, kz, {p: tarif})   # schreibt das Restguthaben des alten Tarifs gut
            re_x = _wechsel_rechnung(d, kz, p, tarif, "Mitgliederbereich")
            _tid, tk = _mb_ticket(d, mid, m, kz, p, beschr, f"{'Upgrade' if upgrade else 'Downgrade'} im Mitgliederbereich gebucht: {aktuell} → {tarif} ({preis}). "
                                  "Zur Info – bereits umgesetzt, die Laufzeit beginnt neu.", status="erledigt")
            journal(f"Mitgliederbereich: {beschr} gebucht ({tk['nr']})")
            _mb_mail(d, m, f"Tarif gewechselt: {tarif}", f"<p>Ihr Tarif für Parzelle {p} ist jetzt <b>{html_mod.escape(tarif)}</b> (vorher {html_mod.escape(aktuell)}). "
                     "Die Laufzeit beginnt mit dem Wechsel neu.</p>")
            rt = (f" Rechnung {re_x['nr']} über {geld(re_x['brutto'])} (Restguthaben angerechnet)." if re_x else "") + \
                 (f" Verbleibendes Guthaben: {geld(guthaben(d, kz, p))}." if guthaben(d, kz, p) else "")
            return {"ok": True, "text": f"Erledigt – Ihr Tarif ist jetzt {tarif}, die Laufzeit beginnt neu.{rt} Die Änderung wird im WLAN vom Verein übernommen."}
        _tid, tk = _mb_ticket(d, mid, m, kz, p, f"Antrag: {beschr}", f"Antrag aus dem Mitgliederbereich: {beschr} ({preis}). Bitte im Ticket freigeben oder ablehnen.", antrag=antrag)
        return {"ok": True, "text": f"Danke! Ihr Antrag {tk['nr']} ist beim Verein eingegangen. Sie bekommen Bescheid, sobald er freigegeben ist."}
    ref = "SN-" + secrets.token_hex(5).upper()
    a = {"mitglied": mid, "sparte": kz, "parzelle": int(p), "tarif": tarif, "tarif_alt": aktuell, "art": art, "betrag": round(float(t.get("preis") or 0), 2),
         "email": m.get("email", ""), "name": name, "beschreibung": beschr, "status": "offen", "erstellt": time.strftime("%Y-%m-%d %H:%M")}
    if a["betrag"] <= 0:
        raise Fehler("Für diesen Tarif ist kein Preis hinterlegt – bitte beim Verein melden.")
    if art == "wechsel":                           # Restguthaben des alten Tarifs und vorhandenes Guthaben anrechnen
        a["angerechnet"] = min(a["betrag"], round(restwert(d, kz, p) + guthaben(d, kz, p), 2))
        a["betrag"] = round(a["betrag"] - a["angerechnet"], 2)
        if a["betrag"] <= 0:                       # vollständig durch Guthaben gedeckt: sofort buchen
            akt_buchungen_speichern(d, kz, {p: tarif})
            guthaben_buchen(d, kz, p, -a["angerechnet"], f"angerechnet auf {beschr}")
            _mb_ticket(d, mid, m, kz, p, beschr, f"Im Mitgliederbereich gebucht, vollständig mit Guthaben verrechnet ({geld(a['angerechnet'])}).", status="erledigt")
            return {"ok": True, "text": f"Erledigt – Ihr Tarif ist jetzt {tarif}, vollständig mit Ihrem Guthaben verrechnet. "
                                        f"Verbleibendes Guthaben: {geld(guthaben(d, kz, p))}."}
    url = _link_erzeugen(d, e, ref, a, basis)
    z = zahlungsauftraege(d)
    z[ref] = a
    for k in sorted(z, key=lambda r: z[r].get("erstellt", ""))[:-2000]:
        z.pop(k, None)
    speichere(d)
    journal(f"Zahlungsauftrag {ref} angelegt: {beschr}, {geld(a['betrag'])}")
    return {"ok": True, "url": url, "referenz": ref}


def _mb_zusatz(d, e, mid, m, kz, p, aktuell, b, basis):
    """Zusatzgeräte buchen oder reduzieren ({"art": "zusatz", "anzahl": neue Gesamtzahl}). Preis je Gerät und Jahr; mehr Geräte sofort
    (Abrechnung mit der Jahresrechnung) bzw. über den Bezahldienst; weniger nur, wenn nicht mehr Geräte verbunden sind."""
    if not e["zusatzgeraete"]:
        raise Fehler("Zusatzgeräte sind hier nicht buchbar – bitte beim Verein melden.")
    t = next((x for x in tarife_pruefen(d["tarife"]) if x["name"] == aktuell), None)
    if not t:
        raise Fehler("Bitte zuerst einen Tarif buchen.")
    if not t.get("geraete"):
        raise Fehler(f"Im Tarif {aktuell} sind beliebig viele Geräte erlaubt – Zusatzgeräte sind nicht nötig.")
    try:
        neu = int(b.get("anzahl"))
    except (TypeError, ValueError):
        raise Fehler("Bitte die Anzahl der Zusatzgeräte angeben.")
    hoechst = min(e["zusatz_max"], zusatz_platz(t))
    if not 0 <= neu <= hoechst:
        raise Fehler(f"Im Tarif {aktuell} sind 0 bis {hoechst} Zusatzgeräte möglich.")
    alt = zusatz_geraete(d, kz, p)
    if neu == alt:
        raise Fehler("Die Anzahl ist unverändert.")
    preis = e["zusatz_preis"]
    if neu < alt:
        erlaubt = int(t["geraete"]) + neu
        n = _geraete_zaehlen(d, kz, p)
        if n > erlaubt:
            raise Fehler(f"Zu viele Geräte: {n} sind verbunden, mit {neu} Zusatzgerät(en) sind {erlaubt} erlaubt. Bitte vorher {n - erlaubt} Gerät(e) sperren oder ausschalten.")
        _zusatz_setzen(d, kz, p, neu, "Mitgliederbereich")
        _mb_ticket(d, mid, m, kz, p, f"Zusatzgeräte {alt} → {neu} · {kz} Parzelle {p}", "Im Mitgliederbereich reduziert. Zur Info – bereits umgesetzt.", status="erledigt")
        return {"ok": True, "text": f"Erledigt – Sie haben jetzt {neu} Zusatzgerät(e), insgesamt {erlaubt} Geräte."}
    mehr = neu - alt
    betrag = round(mehr * preis, 2)
    beschr = f"{mehr} Zusatzgerät(e) ({alt} → {neu}) · {kz} Parzelle {p}"
    if e["modus"] == "anfrage" or betrag <= 0:
        _zusatz_setzen(d, kz, p, neu, "Mitgliederbereich")
        _mb_ticket(d, mid, m, kz, p, f"Zusatzgeräte {alt} → {neu} · {kz} Parzelle {p}",
                   f"Im Mitgliederbereich gebucht: {mehr} × {geld(preis)} im Jahr. Zur Info – bereits umgesetzt; Netz am Gateway über „Tarife“ übernehmen.", status="erledigt")
        _mb_mail(d, m, "Zusatzgeräte gebucht", f"<p>Für Parzelle {p} sind jetzt <b>{neu} Zusatzgerät(e)</b> gebucht ({geld(preis)} je Gerät und Jahr, "
                 "abgerechnet mit der Jahresrechnung).</p>")
        return {"ok": True, "text": f"Erledigt – {neu} Zusatzgerät(e) gebucht, insgesamt {int(t['geraete']) + neu} Geräte. "
                                    f"Je Gerät {geld(preis)} im Jahr (mit der Jahresrechnung). Die Änderung am WLAN übernimmt der Verein."}
    ref = "SN-" + secrets.token_hex(5).upper()
    a = {"mitglied": mid, "sparte": kz, "parzelle": int(p), "tarif": aktuell, "tarif_alt": aktuell, "art": "zusatz", "anzahl": neu, "betrag": betrag,
         "email": m.get("email", ""), "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(), "beschreibung": beschr, "status": "offen",
         "erstellt": time.strftime("%Y-%m-%d %H:%M")}
    url = _link_erzeugen(d, e, ref, a, basis)
    zahlungsauftraege(d)[ref] = a
    speichere(d)
    journal(f"Zahlungsauftrag {ref} angelegt: {beschr}, {geld(betrag)}")
    return {"ok": True, "url": url, "referenz": ref}


def _mb_mail(d, m, betreff, inhalt):
    if not m.get("email"):
        return
    try:
        email_senden(d, m["email"], betreff, None, f"<p>Hallo {html_mod.escape(m.get('vorname') or '')},</p>{inhalt}", sparte=m.get("sparte") or None)
    except Exception as x:
        LOG.warning("Mitgliederbereich: E-Mail nicht gesendet: %s", x)


def akt_tarif_antrag(d, b, ich, erlaubt=None):
    """Tarif-Antrag aus dem Mitgliederbereich freigeben ({"id", "freigeben": true}) oder ablehnen ({"id", "freigeben": false, "grund"})"""
    from .tickets import _holen as _ticket_holen
    tid = str(b.get("id") or "")
    t = _ticket_holen(d, tid, ich, erlaubt)
    a = t.get("antrag") if isinstance(t.get("antrag"), dict) else None
    if not a or a.get("status") != "offen":
        raise Fehler("Kein offener Tarif-Antrag in diesem Ticket.")
    kz, p, tarif = a["sparte"], str(a["parzelle"]), a["tarif"]
    m = mitglieder(d).get(a.get("mitglied")) or {"email": (t.get("kontakt") or {}).get("email", ""), "vorname": (t.get("kontakt") or {}).get("vorname", "")}
    if b.get("freigeben"):
        aktuell = ((d.get("buchungen") or {}).get(kz) or {}).get(p, "")
        if aktuell != (a.get("tarif_alt") or ""):
            raise Fehler(f"Der Tarif der Parzelle hat sich inzwischen geändert (jetzt „{aktuell or 'keiner'}“) – bitte ablehnen und neu beantragen lassen.")
        if a["art"] == "verlaengern":
            _verlaengern(d, kz, p, 1, f"Antrag {t['nr']} ({ich})")
        else:
            akt_buchungen_speichern(d, kz, {p: tarif})
            if a["art"] == "wechsel" and mb_einstellungen(d)["modus"] == "anfrage":
                _wechsel_rechnung(d, kz, p, tarif, ich)
        a.update(status="freigegeben", entschieden=time.strftime("%Y-%m-%d %H:%M"), von=ich)
        loesung = f"Freigegeben durch {ich}: {t.get('betreff', '').replace('Antrag: ', '')} – gebucht."
        _mb_mail(d, m, f"[{t['nr']}] Ihr Antrag ist freigegeben", f"<p>Ihr Antrag <b>{html_mod.escape(t['nr'])}</b> ({html_mod.escape(t.get('betreff', ''))}) ist freigegeben und gebucht.</p>")
    else:
        grund = str(b.get("grund") or "").strip()[:1000]
        if not grund:
            raise Fehler("Bitte einen Grund für die Ablehnung angeben – er geht an das Mitglied.")
        a.update(status="abgelehnt", entschieden=time.strftime("%Y-%m-%d %H:%M"), von=ich, grund=grund)
        loesung = f"Abgelehnt durch {ich}: {grund}"
        _mb_mail(d, m, f"[{t['nr']}] Ihr Antrag wurde abgelehnt", f"<p>Ihr Antrag <b>{html_mod.escape(t['nr'])}</b> ({html_mod.escape(t.get('betreff', ''))}) wurde leider abgelehnt.</p>{text_zu_html(grund)}")
    speichere(d)
    journal(f"Tarif-Antrag {t['nr']} {a['status']} durch {ich}")
    r = akt_ticket_schliessen(d, {"id": tid, "loesung": loesung}, ich, erlaubt)
    r["log"] = [f"✔ Antrag {a['status']}." + (" Buchung ausgeführt." if a["status"] == "freigegeben" else "") + " Mitglied per E-Mail informiert."]
    return r


def zahlungsauftrag_bezahlt(d, ref, betrag=None, quelle=""):
    """Zahlung bestätigt → Buchung ausführen (einmalig). Gibt Text zurück oder wirft Fehler."""
    a = zahlungsauftraege(d).get(str(ref or "").upper())
    if not a:
        raise Fehler("Zahlungsauftrag nicht gefunden.")
    if a["status"] == "bezahlt":
        return f"{ref} war schon bezahlt."
    if betrag is not None and abs(float(betrag) - float(a["betrag"])) > 0.01:
        a["status"], a["fehler"] = "fehler", f"Betrag {betrag} statt {a['betrag']}"
        speichere(d)
        raise Fehler("Betrag stimmt nicht mit dem Auftrag überein – bitte von Hand prüfen.")
    kz, p = a["sparte"], str(a["parzelle"])
    if a["art"] == "verlaengern":
        _verlaengern(d, kz, p, 1, f"Bezahlt ({ref})")
    elif a["art"] == "zusatz":
        _zusatz_setzen(d, kz, p, int(a.get("anzahl") or 0), f"Bezahlt ({ref})")
    else:
        akt_buchungen_speichern(d, kz, {p: a["tarif"]})
        if a.get("angerechnet"):
            guthaben_buchen(d, kz, p, -float(a["angerechnet"]), f"angerechnet auf {a.get('beschreibung', '')} ({ref})")
    a.update(status="bezahlt", bezahlt_am=time.strftime("%Y-%m-%d %H:%M"), quelle=text_einzeilig(quelle, 80))
    speichere(d)
    journal(f"Zahlung bestätigt {ref}: {a['beschreibung']} ({geld(a['betrag'])}) – gebucht")
    ereignis("zahlung_mitglied", {"sparte": kz, "parzelle": int(p), "tarif": a["tarif"], "tarif_alt": a.get("tarif_alt", ""), "betrag": f"{a['betrag']:.2f}",
                                  "referenz": ref, "email": a.get("email", ""), "name": a.get("name", ""), "quelle": quelle or "Bezahldienst"}, d)
    try:
        email_senden(d, a["email"], f"Zahlung erhalten: {a['beschreibung']}", None,
                     f"<p>Hallo {html_mod.escape(a.get('name') or '')},</p><p>vielen Dank – Ihre Zahlung über {geld(a['betrag'])} ist eingegangen.</p>"
                     f"<p><b>{html_mod.escape(a['beschreibung'])}</b> ist gebucht (Referenz {ref}). Die Änderung am WLAN wird vom Verein übernommen.</p>", sparte=a.get("sparte"))
    except Exception as x:
        LOG.warning("Bestätigung zu %s nicht gesendet: %s", ref, x)
    return f"{ref}: {a['beschreibung']} gebucht."


def mb_webhook(d, roh, signatur):
    geheim = _mb_geheim(d)
    if not geheim:
        raise Fehler("Kein Webhook-Geheimnis eingerichtet.")
    soll = "sha256=" + hmac.new(geheim.encode(), roh, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(soll, str(signatur or "").strip()):
        raise Fehler("Signatur ungültig.")
    b = json.loads(roh or b"{}")
    if str(b.get("status") or "bezahlt").lower() not in ("bezahlt", "paid", "succeeded", "completed"):
        a = zahlungsauftraege(d).get(str(b.get("referenz") or "").upper())
        if a and a["status"] == "offen":
            a["status"] = "abgebrochen"
            speichere(d)
        return {"ok": True, "text": "nicht bezahlt – nichts gebucht"}
    return {"ok": True, "text": zahlungsauftrag_bezahlt(d, b.get("referenz"), b.get("betrag"), "Bezahldienst (Webhook)")}


# ---- öffentliche Anfragen unter /mein/… ------------------------------------------------------------------------------
def mb_anfrage(pfad, b, email, quelle, basis):
    """(Status, Antwort) für angemeldete Mitglieder"""
    d = lade()
    if not mb_einstellungen(d)["aktiv"]:
        return 404, {"fehler": "Der Mitgliederbereich ist nicht eingeschaltet."}
    if not email:
        return 401, {"fehler": "Bitte anmelden.", "anmelden": True}
    try:
        if pfad == "/mein/daten":
            return 200, mb_daten(d, email)
        if pfad == "/mein/geraete":
            _mid, _m, kz, p = _mb_parzelle(d, email, (b or {}).get("id"))
            if not mb_einstellungen(d)["geraete"]:
                raise Fehler("Die Geräteanzeige ist ausgeschaltet.")
            return 200, mb_geraete(d, kz, p)
        _grenze("mb_aktion", email)
        if pfad in ("/mein/geraet_trennen", "/mein/geraet_zulassen"):
            if not mb_einstellungen(d)["geraete"]:
                raise Fehler("Die Geräteanzeige ist ausgeschaltet.")
            with SCHREIB_SPERRE:
                d = lade()
                _mid, _m, kz, p = _mb_parzelle(d, email, (b or {}).get("id"))
                return 200, (mb_geraet_trennen if pfad.endswith("trennen") else mb_geraet_zulassen)(d, kz, p, b or {})
        aktionen = {"/mein/profil": mb_profil_speichern, "/mein/profil_bestaetigen": mb_profil_bestaetigen,
                    "/mein/person_neu": mb_person_neu, "/mein/person_entfernen": mb_person_entfernen}
        if pfad in aktionen:
            with SCHREIB_SPERRE:
                return 200, aktionen[pfad](lade(), email, b or {})
        if pfad == "/mein/buchen":
            with SCHREIB_SPERRE:
                return 200, mb_buchen(lade(), email, b or {}, basis)
        if pfad == "/mein/zugangskarte":
            if not mb_einstellungen(d)["zugangskarte"]:
                raise Fehler("Die Zugangskarte ist hier nicht abrufbar – bitte beim Verein melden.")
            mid, m, kz, p = _mb_parzelle(d, email, (b or {}).get("id"))
            z = next((z for z in lese_ppsk(kz) if str(z.get("Parzelle")) == p and z.get("Passwort")), None)
            if not z or not ((d.get("buchungen") or {}).get(kz) or {}).get(p):
                raise Fehler("Für diese Parzelle gibt es gerade keinen WLAN-Zugang.")
            zeile = {**z, "WLAN": wlan_ssid(d, kz)}
            karte = zugangskarte_pdf(d, kz, zeile, _sparten_kz(d).get(kz, kz))
            email_senden(d, m["email"], f"Ihre WLAN-Zugangskarte für Parzelle {p}", None,
                         f"<p>Hallo {html_mod.escape(m.get('vorname') or '')},</p><p>anbei Ihre WLAN-Zugangskarte für Parzelle {p}.</p>",
                         anhaenge=[(f"Zugangskarte_Parzelle_{p}.pdf", karte, "application/pdf")], sparte=kz)
            journal(f"Mitgliederbereich: Zugangskarte {kz} Parzelle {p} gesendet")
            return 200, {"ok": True, "text": "Die Zugangskarte ist per E-Mail unterwegs."}
        if pfad == "/mein/ticket":
            if not mb_einstellungen(d)["neue_anfrage"]:
                raise Fehler("Neue Anfragen sind hier ausgeschaltet.")
            mid, m, kz, p = _mb_parzelle(d, email, (b or {}).get("id"))
            if not str((b or {}).get("betreff") or "").strip():
                raise Fehler("Bitte einen Betreff angeben.")
            with SCHREIB_SPERRE:
                d = lade()
                roh = {"betreff": b["betreff"], "text": str(b.get("text") or "")[:5000], "kategorie": b.get("kategorie") if b.get("kategorie") in ticket_kategorien(d) else "Sonstiges",
                       "sparte": kz, "parzelle": p, "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(), "email": m.get("email", "")}
                tid, t = ticket_anlegen(d, roh, "Mitgliederbereich", "Mitgliederbereich")
                t.setdefault("kontakt", {}).update(mitglied=mid, art="mitglied", geprueft=True, vorname=m.get("vorname", ""), nachname=m.get("nachname", ""))
                speichere(d)
            return 200, {"ok": True, "text": f"Danke! Ihre Anfrage hat die Nummer {t['nr']}."}
        return 404, {"fehler": "Unbekannte Funktion."}
    except Fehler as f:
        return 400, {"fehler": str(f)}
    except Exception:
        ref = secrets.token_hex(3)
        LOG.error("Mitgliederbereich Fehler %s:\n%s", ref, traceback.format_exc())
        return 500, {"fehler": f"Es ist ein Fehler aufgetreten (Nr. {ref})."}


def mb_rechnung_pdf(d, email, rid):
    x = rechnungen_daten(d)["liste"].get(str(rid or ""))
    eigene = mb_mitglieder_von(d, email)
    parzellen = {(m.get("sparte"), str(m.get("parzelle") or "")) for m in eigene.values()}
    if not x or (x.get("mitglied") not in eigene and (x.get("sparte"), str(x.get("parzelle") or "")) not in parzellen):
        raise Fehler("Rechnung nicht gefunden.")
    return rechnung_pdf(d, x), f"Rechnung_{x['nr']}.pdf"


def mein_seite(d, design=None, inline=False, vorschau=False):
    """Seite /mein – Aussehen aus „Oberfläche gestalten → Mitgliederbereich“ (ohne eigene Gestaltung wie die Kontakt-Seite)"""
    g = design or seiten_design(d, "mein")
    titel = html_mod.escape(g.get("titel") or "Mitgliederbereich")
    seite = portal_seite(d, g, inline=inline, art="mein")
    kopf, rest = seite.split("<body", 1)
    kopf = re.sub(r"<title>.*?</title>", f"<title>{titel}</title>", kopf, flags=re.S)
    body_tag, rest = rest.split(">", 1)
    knoepfe = ('<div id="kopf_knoepfe"><button id="b_farbe" onclick="farbeWeiter()" title="Ansicht">◐</button>'
               '<button id="b_ab" onclick="abmelden()" hidden>Abmelden</button></div>')
    header = rest[:rest.index("</header>")].replace("<header>", "<header>" + knoepfe, 1).replace(
        '<div id="titel"></div>', f'<div id="titel">{titel}</div><div id="kopf_logos"></div><div id="kopf_hallo"></div>') + "</header>"
    fuss = re.search(r"<footer>.*?</footer>", seite, re.S)
    text = html_mod.escape(g["text_anmeldung"]).replace("\n", "<br>") if g.get("text_anmeldung") else (
        "Mit der E-Mail-Adresse, die beim Verein für Ihre Parzelle hinterlegt ist. Der Verein schickt Ihnen einen Einmalcode per E-Mail – ein Passwort ist nicht nötig.")
    html = (MEIN_HTML.replace("__KOPF__", kopf + "<body" + body_tag + ">" + header).replace("__FUSS__", fuss.group(0) if fuss else "")
            .replace("__ANMELDETEXT__", text).replace("__VEREINSLOGO__", "1" if g.get("vereinslogo", True) else ""))
    if vorschau:                                  # Vorschau im Editor: Anmeldung und Beispieldaten nebeneinander, ohne Server-Abfrage
        html = html.replace("laden();</script>", "vorschau(" + json.dumps(_mb_beispiel(d, g), ensure_ascii=False).replace("</", "<\\/") + ");</script>")
    return html


def _mb_beispiel(d, g):
    sp = next(iter(kalk_sparten(d).items()), ("BW", {"name": "Beispielsparte"}))
    sl = sparten_logo_uri(d, sp[0]) if g.get("vereinslogo", True) else ""
    t = [{**_tarif_info(x), "rang": list(tarif_rang(x))} for x in tarife_pruefen(d["tarife"])][:3]
    return {"mitglied": "Erika Muster", "hinweis": g.get("hinweis", ""), "titel": g.get("titel", ""), "modus": "anfrage", "kategorien": ["Sonstiges"],
            "erlaubt": {"tarifwechsel": True, "downgrade": True, "neubuchung": True, "verlaengern": True, "geraete": True, "zeige_rechnungen": True,
                        "zeige_anfragen": True, "neue_anfrage": True, "zugangskarte": True, "profil": True, "personen": True, "geraete_trennen": True, "geraete_sperren": True, "zusatzgeraete": True, "downgrade_freigabe": False},
            "zusatz_preis": 1.0, "profil": {"vorname": "Erika", "nachname": "Muster", "email": "erika@example.org", "telefon": "", "mobil": "0170 1234567", "haupt": True,
                       "parzellen": [f"{sp[1].get('name', sp[0])} · Parzelle 12"]},
            "tarife": t, "parzellen": [{"id": "x", "sparte": sp[0], "sparte_name": sp[1].get("name", sp[0]), "parzelle": "12", "sparte_logo": sl,
                                        "tarif": t[0]["name"] if t else "", "rang": t[0]["rang"] if t else None, "tarif_laufzeit": "unbegrenzt",
                                        "tarif_geraete": t[0]["geraete"] if t else 0, "zusatz": 1, "zusatz_platz": 3, "geraete_erlaubt": (t[0]["geraete"] + 1) if t and t[0]["geraete"] else 0,
                                        "downgrade": {"ziele": [], "ab": 0, "ab_text": ""},
                                        "laufzeit": None, "gesperrt": False, "offen": 0, "rechnungen": [{"id": "r", "nr": "RE-2026-0001", "datum": "2026-03-01", "brutto": 120, "status": "bezahlt"}],
                                        "tickets": [{"nr": "T-0001", "betreff": "WLAN langsam", "status": "geschlossen", "erstellt": "2026-05-02 18:10", "loesung": "Access Point neu gestartet"}],
                                        "auftrag": None, "antraege": [], "haupt": True,
                                        "personen": [{"vorname": "Erika", "nachname": "Muster", "email": "erika@example.org", "haupt": True},
                                                     {"vorname": "Max", "nachname": "Muster", "email": "max@example.org", "haupt": False}],
                                        "stoerungen": [{"geraet": "Access Point Festwiese", "text": MB_STANDARD["stoerung_meldung"].replace("{geraet}", "Access Point Festwiese").replace("{seit}", "18.10.2026 19:40").replace("{ticket}", "T-0042").replace("{modell}", "")}]}],
            "stoerung_text": mb_einstellungen(d)["stoerung_text"], "stoerung_farbe": mb_einstellungen(d)["stoerung_farbe"]}


MEIN_HTML = r"""__KOPF__<main>
<style>header{position:relative}#kopf_knoepfe{position:absolute;top:10px;right:10px;display:flex;gap:6px}#kopf_knoepfe button{background:none;border:1px solid currentColor;color:var(--kt);border-radius:8px;padding:5px 9px;font:inherit;font-size:15px;cursor:pointer;opacity:.9}
@media(max-width:560px){#kopf_knoepfe{position:static;justify-content:flex-end;margin:-8px -8px 6px}}
#kopf_logos{display:flex;gap:10px;justify-content:center;align-items:center;margin-top:8px}#kopf_logos img{height:44px;width:auto;max-width:120px;object-fit:contain;background:#fff;border-radius:10px;padding:3px}#kopf_logos:empty{display:none}#kopf_hallo{margin-top:6px;font-weight:600}#kopf_hallo:empty{display:none}
.zeile{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.zeile>*{flex:1}.klein{font-size:13px;color:var(--m)}.tabelle{width:100%;border-collapse:collapse;font-size:14px}
.tabelle td,.tabelle th{padding:7px 6px;border-bottom:1px solid var(--l);text-align:left}.wert{font-size:22px;font-weight:700}.knoepfe{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.k2{border:1px solid var(--l);background:var(--c);color:var(--t);border-radius:calc(var(--ecken) * .7);padding:10px 14px;cursor:pointer;font:inherit}.k2:hover{border-color:var(--a)}.k2.akt{border-color:var(--a);box-shadow:inset 0 -3px 0 var(--a);font-weight:600}
.tarife{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;margin-top:10px}.tarif{border:1.5px solid var(--l);border-radius:var(--ecken);padding:12px;cursor:pointer;background:var(--c)}
.tarif.akt{border-color:var(--a);box-shadow:0 0 0 2px var(--a) inset}.tarif b{font-size:17px}.gesperrt{background:#fde8e6;color:#b42318;border-radius:8px;padding:8px 10px;margin-top:8px}
.balken{height:8px;border-radius:4px;background:var(--l);overflow:hidden;margin:6px 0}.balken i{display:block;height:100%;background:var(--a)}.balken.voll i{background:#b42318}
.nr{display:inline-block;background:var(--a);color:#fff;border-radius:6px;padding:2px 8px;font-size:13px;white-space:nowrap}.geraet{display:flex;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--l)}
.fest{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--l);padding:8px 0}.fest span{color:var(--m);font-size:13px}.fest b{font-weight:500}
.reiter{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 14px}.reiter button{flex:1;min-width:70px;padding:10px 4px;font-size:14px}.tab[hidden]{display:none}.wahl label{display:flex;gap:8px;align-items:center;color:var(--t);font-size:15px;margin:6px 0}.wahl input{width:auto}
.zwei>*{min-width:0}#v_login{max-width:640px;margin-left:auto;margin-right:auto}
@media(min-width:900px){main{max-width:min(1160px,94vw)!important}.zwei{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}#v_daten .reiter{max-width:720px}}</style>
<div id="l_stoerung"></div><div id="v_login" class="karte" style="display:none"><h2 style="margin-top:0">Anmelden</h2><p class="hint">__ANMELDETEXT__</p>
<label for="l_email">E-Mail-Adresse</label><input id="l_email" type="email" autocomplete="email" oninput="logoNachEmail()" onchange="logoNachEmail()" onkeydown="if(event.key=='Enter')codeAnfordern()"><button class="los" id="l_b1" onclick="codeAnfordern()">Code per E-Mail senden</button>
<div id="l_code_box" style="display:none"><label for="l_code">Einmalcode aus der E-Mail</label><input id="l_code" onkeydown="if(event.key=='Enter')anmelden()" inputmode="numeric" autocomplete="one-time-code" maxlength="6" style="font-size:22px;letter-spacing:6px;text-align:center"><button class="los" onclick="anmelden()">Anmelden</button></div>
<div class="msg" id="m_login"></div><p class="hint" id="l_app"></p></div>
<div id="v_daten" style="display:none"><div class="reiter" id="reiter"><button class="k2 akt" data-r="start" onclick="reiter('start')">Übersicht</button><button class="k2" data-r="rechnungen" onclick="reiter('rechnungen')">Rechnungen</button><button class="k2" data-r="support" onclick="reiter('support')">Support</button><button class="k2" data-r="profil" onclick="reiter('profil')">Profil</button></div>
<div style="margin-bottom:10px"><select id="d_parz" onchange="zeigen()" style="max-width:340px"></select></div>
<div id="d_stoerung"></div><div class="msg" id="m_daten"></div>
<div class="tab" id="t_start"><p class="hint" id="d_hinweis"></p><div class="zwei"><div class="karte"><h2 style="margin-top:0">Mein Tarif</h2><div id="d_tarif"></div><div id="d_wechsel"></div></div>
<div class="karte" id="s_geraete"><h2 style="margin-top:0">Meine Geräte im WLAN</h2><div id="d_verbrauch"></div><div id="d_geraete">…</div><div id="d_getrennt"></div><div id="d_trennen"></div>
<div class="knoepfe"><button class="k2" onclick="geraete()">Aktualisieren</button><button class="k2" id="b_trennen" onclick="trennenZeigen(false)">⛓ Gerät trennen</button><button class="k2" id="b_sperren" onclick="trennenZeigen(true)">⛔ Gerät sperren</button><button class="k2" id="b_karte" onclick="karte()">Zugangskarte per E-Mail</button></div></div></div></div>
<div class="tab" id="t_rechnungen" hidden><div class="karte" id="s_rechnungen"><h2 style="margin-top:0">Meine Rechnungen</h2><div id="d_rechnungen"></div></div></div>
<div class="tab" id="t_support" hidden><div class="karte" id="s_anfragen"><h2 style="margin-top:0">Support</h2><p class="hint">Fragen, Störungen oder Wünsche? Legen Sie ein Ticket an – Sie bekommen die Antwort per E-Mail.</p>
<details style="margin-top:10px" id="s_neu"><summary style="cursor:pointer;font-weight:600">Ticket anlegen</summary><label for="t_kat">Worum geht es?</label><select id="t_kat"></select><label for="t_betreff">Betreff</label><input id="t_betreff" maxlength="160" onkeydown="if(event.key=='Enter'){event.preventDefault();$('t_text').focus()}"><label for="t_text">Nachricht</label><textarea id="t_text" maxlength="5000" onkeydown="if(event.key=='Enter'&&(event.ctrlKey||event.metaKey))ticket()" placeholder="Strg+Enter sendet"></textarea><button class="los" onclick="ticket()">Ticket senden</button></details><div class="msg" id="m_ticket"></div>
<h3 id="h_tickets">Meine Tickets</h3><div id="d_tickets"></div></div></div>
<div class="tab" id="t_profil" hidden><div class="zwei"><div><div class="karte"><h2 style="margin-top:0">Mein Profil</h2><div id="p_fest"></div>
<label for="p_mobil">Rufnummer (Mobil)</label><input id="p_mobil" type="tel" maxlength="30" autocomplete="tel"><label for="p_telefon">Telefon</label><input id="p_telefon" type="tel" maxlength="30"><label for="p_email">E-Mail-Adresse</label><input id="p_email" type="email" maxlength="200" autocomplete="email">
<p class="hint" style="margin:6px 0 0">Eine neue Adresse bestätigen Sie mit einem Code, der an sie geschickt wird.</p><button class="los" id="p_los" onclick="profilSpeichern()">Speichern</button>
<div id="p_code_box" style="display:none"><label for="p_code">Code aus der E-Mail an die neue Adresse</label><input id="p_code" inputmode="numeric" maxlength="6" style="font-size:22px;letter-spacing:6px;text-align:center" onkeydown="if(event.key=='Enter')codeBestaetigen()"><button class="los" onclick="codeBestaetigen()">Bestätigen</button></div><div class="msg" id="m_profil"></div></div>
<div class="karte" id="s_personen"><h2 style="margin-top:0" id="h_personen">Personen der Parzelle</h2><div id="d_personen"></div>
<details id="s_person_neu" style="margin-top:10px"><summary style="cursor:pointer;font-weight:600">👤 Neues Mitglied in der Parzelle anlegen</summary><p class="hint">Die Person meldet sich mit ihrer E-Mail-Adresse und einem Einmalcode an und bekommt eine Info per E-Mail.</p>
<div class="zeile"><div><label for="n_vorname">Vorname</label><input id="n_vorname" maxlength="120"></div><div><label for="n_nachname">Nachname</label><input id="n_nachname" maxlength="120"></div></div><label for="n_email">E-Mail-Adresse</label><input id="n_email" type="email" maxlength="200">
<div class="zeile"><div><label for="n_mobil">Rufnummer (Mobil, optional)</label><input id="n_mobil" type="tel" maxlength="30"></div><div><label for="n_telefon">Telefon (optional)</label><input id="n_telefon" type="tel" maxlength="30"></div></div><button class="los" onclick="personNeu()">Anlegen</button></details><div class="msg" id="m_personen"></div></div></div><div>
<div class="karte"><h2 style="margin-top:0">Ansicht</h2><div class="knoepfe" id="d_ansicht"></div><p class="hint" id="p_app" style="margin-top:12px"></p></div></div></div></div></div>
</main>__FUSS__<script>const $=i=>document.getElementById(i),esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));let D=null,WAHL=null,VORSCHAU=false,GER=null;
const eur=x=>Number(x||0).toLocaleString("de-DE",{style:"currency",currency:"EUR"});
const FARBEN=[["system","◐","System"],["hell","☀","Hell"],["dunkel","☾","Dunkel"]];
function farbe(){try{return localStorage.getItem("sn_mein_farbe")||"system"}catch(e){return "system"}}
function farbeSetzen(f){try{localStorage.setItem("sn_mein_farbe",f)}catch(e){}if(f=="system")delete document.documentElement.dataset.farbe;else document.documentElement.dataset.farbe=f;const x=FARBEN.find(z=>z[0]==f)||FARBEN[0];$("b_farbe").textContent=x[1];$("b_farbe").title="Ansicht: "+x[2]+" (klicken zum Wechseln)";
 $("d_ansicht").innerHTML=FARBEN.map(([k,s,t])=>`<button class="k2${k==f?" akt":""}" onclick="farbeSetzen('${k}')">${s} ${t}</button>`).join("")}
function farbeWeiter(){const i=FARBEN.findIndex(z=>z[0]==farbe());farbeSetzen(FARBEN[(i+1)%3][0])}
function msg(id,t,ok){const m=$(id);m.className="msg "+(t?(ok?"ok":"f"):"");m.textContent=t||""}
async function post(p,b){if(VORSCHAU)throw new Error("Vorschau");const r=await fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b||{})});const d=await r.json().catch(()=>({}));if(r.status==401&&d.anmelden){ansicht(false);throw new Error("Bitte erneut anmelden.")}if(!r.ok)throw new Error(d.fehler||r.status);return d}
function ansicht(an){$("v_login").style.display=an?"none":"block";$("v_daten").style.display=an?"block":"none";$("l_stoerung").style.display=an?"none":"";$("b_ab").hidden=!an;if(!an){$("kopf_hallo").textContent="";if(!$("l_stoerung").innerHTML)stoerungAllgemein()}}
async function codeAnfordern(){try{const d=await post("/mein/code",{email:$("l_email").value.trim()});msg("m_login",d.text,true);$("l_code_box").style.display="block";$("l_code").focus()}catch(e){msg("m_login",e.message)}}
async function anmelden(){try{await post("/mein/anmelden",{email:$("l_email").value.trim(),code:$("l_code").value});msg("m_login","");laden()}catch(e){msg("m_login",e.message)}}
async function abmelden(){await post("/mein/abmelden").catch(()=>{});location.replace("/mein")}
async function laden(){try{D=await post("/mein/daten");ansicht(true)}catch(e){ansicht(false);return}
 datenZeigen()}
async function appLink(){try{const a=(await post("/mein/app",{})).app||{};const t=a.version_name?`📱 <a href="/mein/app.apk">App „SparteNet Mitglied“ ${esc(a.version_name)} für Android herunterladen</a>`:"";$("l_app").innerHTML=t;$("p_app").innerHTML=t}catch(e){}}
function vorschau(x){VORSCHAU=true;D=x;ansicht(true);$("v_login").style.display="block";datenZeigen();$("l_stoerung").style.display="";stoerungZeigen("l_stoerung",(x.parzellen[0]||{}).stoerungen,x.stoerung_text,x.stoerung_farbe);document.querySelectorAll("button:not(.k2)").forEach(b=>b.onclick=null)}
const VL="__VEREINSLOGO__";
function kopf(spSrc,spName){const fl=document.querySelector("header .mk img");let h="";if(VL&&spSrc)h+=`<img src="${esc(spSrc)}" alt="${esc(spName||"Spartenlogo")}" title="${esc(spName||"")}">`;if(fl)h+=`<img src="${esc(fl.getAttribute("src"))}" alt="Firmenlogo">`;$("kopf_logos").innerHTML=h;if(fl)fl.style.display="none"}
function stoerungZeigen(id,liste,text,farbe){const sf=farbe||"#b42318";$(id).innerHTML=(liste||[]).length?`<div role="alert" style="border:2px solid ${sf};background:${sf}1a;color:${sf};border-radius:var(--ecken);padding:14px 16px;margin:0 0 12px;font-weight:600">`
  +liste.map(s=>`<div style="display:flex;gap:10px;align-items:flex-start;margin:4px 0"><span style="font-size:22px;line-height:1">⚠</span><span>${esc(s.text)}</span></div>`).join("")
  +(text?`<div style="font-weight:400;margin-top:8px;color:var(--t);white-space:pre-wrap">${esc(text)}</div>`:"")+"</div>":""}
async function stoerungAllgemein(){try{const d=await post("/mein/stoerung",{});stoerungZeigen("l_stoerung",d.stoerungen,d.stoerung_text,d.stoerung_farbe)}catch(x){}}
let LT=null;function logoNachEmail(){clearTimeout(LT);const e=$("l_email").value.trim();if(!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(e)){kopf("");return}
 LT=setTimeout(async()=>{try{const d=await post("/mein/logo",{email:e});kopf(d.logo,d.name);stoerungZeigen("l_stoerung",d.stoerungen,d.stoerung_text,d.stoerung_farbe)}catch(x){}},500)}
function reiter(r){document.querySelectorAll("#reiter button").forEach(b=>b.classList.toggle("akt",b.dataset.r==r));["start","rechnungen","support","profil"].forEach(t=>$("t_"+t).hidden=t!=r);try{sessionStorage.setItem("sn_mein_reiter",r)}catch(e){}}
function datenZeigen(){
 $("kopf_hallo").textContent=D.mitglied?"Hallo "+D.mitglied:"";$("d_hinweis").textContent=D.hinweis||"";$("d_parz").innerHTML=D.parzellen.map(p=>`<option value="${esc(p.id)}">${esc(p.sparte_name)} · Parzelle ${esc(p.parzelle)}</option>`).join("");
 $("d_parz").style.display=D.parzellen.length>1?"":"none";if(WAHL&&D.parzellen.some(p=>p.id==WAHL))$("d_parz").value=WAHL;$("t_kat").innerHTML=D.kategorien.map(k=>`<option>${esc(k)}</option>`).join("");
 const q=new URLSearchParams(location.search);if(q.get("zahlung")=="abbruch")msg("m_daten","Die Zahlung wurde abgebrochen – es wurde nichts gebucht.");else if(q.get("zahlung"))msg("m_daten","Danke! Sobald der Bezahldienst die Zahlung bestätigt, ist die Buchung erledigt (Referenz "+q.get("zahlung")+").",true);
 if(q.has("zahlung"))history.replaceState(null,"","/mein");let r="start";try{r=sessionStorage.getItem("sn_mein_reiter")||"start"}catch(e){}reiter(r);profilZeigen();zeigen()}
function P(){return D.parzellen.find(p=>p.id==$("d_parz").value)||D.parzellen[0]}
function zeigen(){const p=P();if(!p){kopf("");return}WAHL=p.id;const lz=p.laufzeit;
 kopf(p.sparte_logo,p.sparte_name);
 stoerungZeigen("d_stoerung",p.stoerungen,D.stoerung_text,D.stoerung_farbe);
 $("d_tarif").innerHTML=p.tarif?`<div class="zeile"><div><div class="klein">Tarif</div><div class="wert">${esc(p.tarif)}</div></div>${lz?`<div><div class="klein">Laufzeit</div><div><b>${lz.aktiv?"bis "+esc(lz.ende):"abgelaufen am "+esc(lz.ende)}</b>${lz.aktiv?`<br><span class="klein">noch ${lz.rest_tage} Tag(e)</span>`:""}</div></div>`:`<div><div class="klein">Laufzeit</div><div><b>unbegrenzt</b></div></div>`}<div><div class="klein">Geräte</div><div><b>${p.tarif_geraete?esc(p.geraete_erlaubt):"unbegrenzt"}</b>${p.zusatz?`<br><span class="klein">${esc(p.tarif_geraete)} + ${esc(p.zusatz)} Zusatz</span>`:""}</div></div>${p.guthaben?`<div><div class="klein">Guthaben</div><div class="wert" style="font-size:18px">${eur(p.guthaben)}</div></div>`:""}<div><div class="klein">Offen</div><div class="wert" style="font-size:18px">${eur(p.offen)}</div></div></div>${p.gesperrt?'<div class="gesperrt">Der WLAN-Zugang ist gerade gesperrt (Laufzeit abgelaufen) – mit einer Verlängerung wird er wieder freigegeben.</div>':""}`:'<p class="hint">Für diese Parzelle ist noch kein Tarif gebucht.</p>';
 const e=D.erlaubt,hoeher=(t)=>p.rang&&(t.rang[0]>p.rang[0]||t.rang[0]==p.rang[0]&&(t.rang[1]>p.rang[1]||t.rang[1]==p.rang[1]&&t.rang[2]>p.rang[2]));
 const ups=D.tarife.filter(t=>t.name!=p.tarif&&hoeher(t)),downs=D.tarife.filter(t=>t.name!=p.tarif&&!hoeher(t));let akt=[];
 if(!p.tarif&&e.neubuchung&&D.tarife.length)akt.push(["neu","Tarif buchen"]);if(p.tarif&&e.tarifwechsel&&ups.length)akt.push(["upgrade","⬆ Upgrade"]);const dg=p.downgrade||{ziele:[]};if(p.tarif&&e.downgrade&&dg.ziele.length&&!p.antraege.length&&!dg.ab_text)akt.push(["downgrade","⬇ Kleinerer Tarif"]);
 if(p.tarif&&e.zusatzgeraete&&p.tarif_geraete&&(p.zusatz_platz>0||p.zusatz>0))akt.push(["zusatz","＋ Zusatzgeräte"]);
 if(p.tarif&&e.verlaengern&&p.tarif_laufzeit&&p.tarif_laufzeit!="unbegrenzt"&&!p.antraege.length)akt.push(["verlaengern","Laufzeit verlängern ("+p.tarif_laufzeit+")"]);
 $("d_wechsel").innerHTML=(p.auftrag?`<p class="hint">Offener Zahlungsauftrag ${esc(p.auftrag.referenz)} (${esc(p.auftrag.tarif)}, ${eur(p.auftrag.betrag)}) – wird gebucht, sobald die Zahlung bestätigt ist.</p>`:"")
  +p.antraege.map(a=>`<p class="hint">⏳ Antrag ${esc(a.nr)} vom ${esc(a.erstellt.slice(0,10))}: ${{wechsel:"Wechsel zu",neu:"Buchung",verlaengern:"Verlängerung"}[a.art]||""} ${esc(a.tarif)} – wartet auf Freigabe durch den Verein.</p>`).join("")
  +(p.tarif&&e.downgrade&&dg.ziele.length&&dg.ab_text?`<p class="hint">⬇ Ein kleinerer Tarif (${esc(dg.ziele[0])}) ist ab ${esc(dg.ab_text)} möglich – ${esc(dg.monate)} Monate nach dem letzten Tarifwechsel.</p>`:"")
  +(akt.length?`<div class="knoepfe">${akt.map(([a,t])=>`<button class="k2" onclick="waehlen('${a}')">${esc(t)}</button>`).join("")}</div><div id="d_auswahl"></div>`:"");
 $("s_rechnungen").style.display=e.zeige_rechnungen?"block":"none";$("d_tickets").style.display=$("h_tickets").style.display=e.zeige_anfragen?"":"none";$("s_neu").style.display=e.neue_anfrage?"":"none";$("b_karte").style.display=e.zugangskarte?"":"none";
 $("d_rechnungen").innerHTML=!e.zeige_rechnungen?"":p.rechnungen.length?'<table class="tabelle"><tr><th>Nr.</th><th>Datum</th><th>Betrag</th><th>Status</th><th></th></tr>'+p.rechnungen.map(r=>`<tr><td>${esc(r.nr)}</td><td>${esc(r.datum)}</td><td>${eur(r.brutto)}</td><td>${esc(r.status)}</td><td><a href="/mein/rechnung?id=${encodeURIComponent(r.id)}" target="_blank" rel="noopener">PDF</a></td></tr>`).join("")+"</table>":'<p class="hint">Noch keine Rechnungen.</p>';
 $("d_tickets").innerHTML=p.tickets.length?p.tickets.map(t=>`<div class="antwort"><b>${esc(t.nr)}</b> · ${esc(t.status)} · ${esc(t.erstellt)}<br>${esc(t.betreff)}${t.loesung?"<br><small>Lösung: "+esc(t.loesung)+"</small>":""}</div>`).join(""):'<p class="hint">Noch keine Tickets.</p>';
 personenZeigen(p);$("s_geraete").style.display=e.geraete||e.zugangskarte?"block":"none";$("d_trennen").innerHTML="";if(e.geraete)geraete();else{$("d_geraete").innerHTML="";$("b_trennen").style.display="none"}}
function waehlen(wie){if(wie=="zusatz")return zusatzZeigen();const p=P();const hoeher=(t)=>p.rang&&(t.rang[0]>p.rang[0]||t.rang[0]==p.rang[0]&&(t.rang[1]>p.rang[1]||t.rang[1]==p.rang[1]&&t.rang[2]>p.rang[2]));
 const art=wie=="upgrade"||wie=="downgrade"?"wechsel":wie;
 const liste=wie=="verlaengern"?[{name:p.tarif,laufzeit:p.tarif_laufzeit,preis:p.tarif_preis,down:p.tarif_down,up:p.tarif_up,geraete:p.tarif_geraete}]:wie=="upgrade"?D.tarife.filter(t=>t.name!=p.tarif&&hoeher(t)):wie=="downgrade"?D.tarife.filter(t=>(p.downgrade||{ziele:[]}).ziele.includes(t.name)):D.tarife;
 const knopf=wie=="downgrade"&&D.erlaubt.downgrade_freigabe?"Antrag stellen (Freigabe durch den Verein)":D.modus=="bezahldienst"?"Weiter zur Bezahlung":wie=="upgrade"||wie=="downgrade"?"Jetzt wechseln":"Antrag an den Verein senden";
 const hinweis=wie=="upgrade"?"Ein Upgrade ist jederzeit möglich"+(D.modus=="bezahldienst"?" – nach der Bezahlung sofort gebucht.":" und wird sofort gebucht.")+" Die Laufzeit beginnt mit dem Wechsel neu."+(p.restwert?" Restguthaben von etwa "+eur(p.restwert)+" aus der laufenden Laufzeit wird angerechnet.":""):wie=="downgrade"?"Ein kleinerer Tarif geht nur eine Stufe nach unten; die Laufzeit beginnt neu. Es dürfen nicht mehr Geräte verbunden sein, als der neue Tarif erlaubt."+(p.restwert?" Restguthaben von etwa "+eur(p.restwert)+" wird angerechnet.":"")+(D.erlaubt.downgrade_freigabe?" Der Verein muss den Wechsel freigeben – Sie bekommen per E-Mail Bescheid.":""):"";
 $("d_auswahl").innerHTML=(hinweis?`<p class="hint" style="margin:10px 0 0">${esc(hinweis)}</p>`:"")+`<div class="tarife">${liste.map(t=>`<div class="tarif" data-t="${esc(t.name)}"><b>${esc(t.name)}</b><br><span class="klein">${t.down} / ${t.up} Mbit/s · ${t.geraete?t.geraete+" Geräte":"Geräte unbegrenzt"}<br>Laufzeit: ${esc(t.laufzeit)}</span><br><b>${eur(t.preis)}</b></div>`).join("")}</div>
 <button class="los" id="d_los" disabled>${esc(knopf)}</button>`;
 let wahl=wie=="verlaengern"?p.tarif:null;document.querySelectorAll(".tarif").forEach(x=>{if(x.dataset.t==wahl)x.classList.add("akt");x.onclick=()=>{wahl=x.dataset.t;document.querySelectorAll(".tarif").forEach(y=>y.classList.toggle("akt",y===x));$("d_los").disabled=false;if(wie=="downgrade")zuViele(liste.find(t=>t.name==wahl))}});
 $("d_los").disabled=!wahl;$("d_los").onclick=async()=>{try{$("d_los").disabled=true;const d=await post("/mein/buchen",{id:p.id,art,tarif:wahl});if(d.url){location.href=d.url;return}msg("m_daten",d.text,true);laden()}catch(e){msg("m_daten",e.message);$("d_los").disabled=false}}}
function zuViele(t){const p=P(),erl=t&&t.geraete?t.geraete+(p.zusatz||0):0,n=GER?GER.anzahl:0;const w=$("d_warnung")||$("d_los").insertAdjacentElement("beforebegin",Object.assign(document.createElement("div"),{id:"d_warnung"}));
 if(erl&&n>erl){w.innerHTML=`<div class="gesperrt">⚠ Zu viele Geräte: ${n} sind verbunden, ${esc(t.name)} erlaubt ${erl}. Ein Wechsel ist erst möglich, wenn Sie ${n-erl} Gerät(e) sperren oder ausschalten.${D.erlaubt.geraete_sperren?' <button class="k2" onclick="trennenZeigen(true);$(\'s_geraete\').scrollIntoView({behavior:\'smooth\'})">⛔ Gerät sperren</button>':""}</div>`;$("d_los").disabled=true}else w.innerHTML=""}
function zusatzZeigen(){const p=P(),max=Math.max(p.zusatz_platz||0,p.zusatz||0),preis=D.zusatz_preis||0;let o="";for(let i=0;i<=max;i++)o+=`<option value="${i}"${i==p.zusatz?" selected":""}>${i} Zusatzgerät${i==1?"":"e"} – insgesamt ${p.tarif_geraete+i} Geräte${i?" · "+eur(i*preis)+" im Jahr":""}</option>`;
 $("d_auswahl").innerHTML=`<p class="hint" style="margin:10px 0 0">Mehr Geräte als im Tarif ${esc(p.tarif)} (${esc(p.tarif_geraete)})? Jedes Zusatzgerät kostet ${eur(preis)} im Jahr${D.modus=="bezahldienst"?" und wird gleich bezahlt":" und wird mit der Jahresrechnung abgerechnet"}. Weniger geht, wenn nicht mehr Geräte verbunden sind.</p><select id="z_anzahl" style="max-width:420px">${o}</select><button class="los" id="z_los">${D.modus=="bezahldienst"?"Weiter":"Übernehmen"}</button>`;
 $("z_los").onclick=async()=>{try{$("z_los").disabled=true;const d=await post("/mein/buchen",{id:p.id,art:"zusatz",anzahl:+$("z_anzahl").value});if(d.url){location.href=d.url;return}msg("m_daten",d.text,true);laden()}catch(e){msg("m_daten",e.message);$("z_los").disabled=false}}}
async function geraete(){const p=P();$("d_geraete").textContent="…";try{GER=await post("/mein/geraete",{id:p.id})}catch(e){if(VORSCHAU)GER={tarif:p.tarif,anzahl:2,max:5,geraete:[{nr:1,name:"Handy",art:"WLAN",ref:"a"},{nr:2,name:"Laptop",art:"WLAN",ref:"b"}],gesperrt:[{ref:"c",name:"Tablet",zeit:"18.10.2026 17:05"}]};else{$("d_geraete").textContent=e.message;return}}
 const d=GER,voll=d.max&&d.anzahl>=d.max;$("d_verbrauch").innerHTML=`<div class="wert" style="font-size:18px">${d.tarif?esc(d.tarif)+": ":""}${d.max?d.anzahl+" von "+d.max+" Geräten":d.anzahl+" Geräte (unbegrenzt)"}</div>`+(d.max?`<div class="balken${voll?" voll":""}"><i style="width:${Math.min(100,Math.round(d.anzahl/d.max*100))}%"></i></div>`:"")+(voll?'<p class="hint" style="color:#b42318">Alle Plätze belegt – trennen Sie ein Gerät oder wechseln Sie in einen größeren Tarif.</p>':"");
 $("d_geraete").innerHTML=d.geraete.length?d.geraete.map(g=>`<div class="geraet"><span class="nr">Gerät ${esc(g.nr)}</span><div style="flex:1"><b>${esc(g.name)}</b>${g.art?`<br><span class="klein">${esc(g.art)}</span>`:""}</div></div>`).join(""):`<p class="hint">${esc(d.fehler||"Gerade ist kein Gerät angemeldet.")}</p>`;
 $("d_getrennt").innerHTML=(d.gesperrt||[]).length?'<h3 style="margin:14px 0 4px">Gesperrte Geräte</h3>'+d.gesperrt.map(g=>`<div class="geraet"><span class="nr" style="background:#b42318">gesperrt</span><div style="flex:1">${esc(g.name)}<br><span class="klein">seit ${esc(g.zeit)}</span></div><button class="k2" onclick="zulassen('${esc(g.ref)}')">Wieder zulassen</button></div>`).join(""):"";
 $("b_trennen").style.display=D.erlaubt.geraete_trennen&&d.geraete.some(g=>g.art!="Kabel")?"":"none";$("b_sperren").style.display=D.erlaubt.geraete_sperren&&d.geraete.length?"":"none"}
function trennenZeigen(sp){if(!GER)return;const l=sp?GER.geraete:GER.geraete.filter(g=>g.art!="Kabel");$("d_trennen").innerHTML=`<div class="karte" style="margin:12px 0 0"><b>Welches Gerät ${sp?"sperren":"trennen"}?</b><p class="hint">${sp?"Das Gerät wird gesperrt und kommt nicht mehr ins Netz, bis Sie es unter „Gesperrte Geräte“ wieder zulassen.":"Das Gerät wird vom WLAN getrennt. Es wird nicht gesperrt und kann sich bei Bedarf jederzeit wieder verbinden."}</p><div class="wahl">${l.map(g=>`<label><input type="radio" name="tr" value="${esc(g.ref)}"> Gerät ${esc(g.nr)} · ${esc(g.name)}</label>`).join("")}</div><div class="knoepfe"><button class="k2" onclick="trennen(${sp?"true":"false"})">${sp?"Sperren":"Trennen"}</button><button class="k2" onclick="$('d_trennen').innerHTML=''">Abbrechen</button></div></div>`}
async function trennen(sp){const w=document.querySelector("input[name=tr]:checked");if(!w){msg("m_daten","Bitte ein Gerät auswählen.");return}try{const d=await post("/mein/geraet_trennen",{id:P().id,ref:w.value,bestaetigt:true,sperren:!!sp});msg("m_daten",d.text,true);$("d_trennen").innerHTML="";geraete()}catch(e){msg("m_daten",e.message)}}
async function zulassen(ref){try{const d=await post("/mein/geraet_zulassen",{id:P().id,ref});msg("m_daten",d.text,true);geraete()}catch(e){msg("m_daten",e.message)}}
async function karte(){try{const d=await post("/mein/zugangskarte",{id:P().id});msg("m_daten",d.text,true)}catch(e){msg("m_daten",e.message)}}
async function ticket(){try{const d=await post("/mein/ticket",{id:P().id,kategorie:$("t_kat").value,betreff:$("t_betreff").value,text:$("t_text").value});msg("m_ticket",d.text,true);$("t_betreff").value="";$("t_text").value="";laden()}catch(e){msg("m_ticket",e.message)}}
function profilZeigen(){const pr=D.profil||{},darf=D.erlaubt.profil;$("p_fest").innerHTML=[["Vorname",pr.vorname],["Nachname",pr.nachname],["Parzelle",(pr.parzellen||[]).join(", ")]].map(([l,w])=>`<div class="fest"><div><span>${l}</span><br><b>${esc(w||"–")}</b></div><span title="nur vom Verein änderbar">🔒</span></div>`).join("");
 $("p_mobil").value=pr.mobil||"";$("p_telefon").value=pr.telefon||"";$("p_email").value=pr.email||"";["p_mobil","p_telefon","p_email"].forEach(i=>$(i).disabled=!darf);$("p_los").style.display=darf?"":"none";$("p_code_box").style.display="none"}
async function profilSpeichern(){const b={mobil:$("p_mobil").value.trim(),telefon:$("p_telefon").value.trim()};const em=$("p_email").value.trim();if(em.toLowerCase()!=String((D.profil||{}).email||"").toLowerCase())b.email=em;
 try{const d=await post("/mein/profil",b);msg("m_profil",d.text,true);if(d.bestaetigen){$("p_code_box").style.display="block";$("p_code").focus()}else laden()}catch(e){msg("m_profil",e.message)}}
async function codeBestaetigen(){try{const d=await post("/mein/profil_bestaetigen",{code:$("p_code").value});msg("m_profil",d.text,true);$("p_code").value="";laden()}catch(e){msg("m_profil",e.message)}}
function personenZeigen(p){const darf=D.erlaubt.personen&&p.haupt;$("h_personen").textContent="Personen der Parzelle "+p.parzelle;
 $("d_personen").innerHTML=(p.personen||[]).map(x=>`<div class="geraet"><div style="flex:1"><b>${esc((x.vorname+" "+x.nachname).trim())}</b><br><span class="klein">${x.haupt?"Pächter":"weitere Person"}${x.email?" · "+esc(x.email):""}</span></div>${darf&&!x.haupt?`<button class="k2" onclick="personEntfernen('${esc(x.email)}')">Entfernen</button>`:""}</div>`).join("")
  +(!darf&&D.erlaubt.personen?'<p class="hint">Weitere Personen kann der Pächter der Parzelle anlegen.</p>':"");$("s_person_neu").style.display=darf?"":"none"}
async function personNeu(){const b={id:P().id};["vorname","nachname","email","mobil","telefon"].forEach(k=>b[k]=$("n_"+k).value.trim());try{const d=await post("/mein/person_neu",b);msg("m_personen",d.text,true);["vorname","nachname","email","mobil","telefon"].forEach(k=>$("n_"+k).value="");$("s_person_neu").open=false;laden()}catch(e){msg("m_personen",e.message)}}
async function personEntfernen(email){if(!confirm("Person entfernen? Sie hat danach keinen Zugang mehr zum Mitgliederbereich dieser Parzelle."))return;try{const d=await post("/mein/person_entfernen",{id:P().id,email});msg("m_personen",d.text,true);laden()}catch(e){msg("m_personen",e.message)}}
farbeSetzen(farbe());appLink();
laden();</script></body></html>"""


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

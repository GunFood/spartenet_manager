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
               "zugangskarte": True, "tarife": []}
_MB_SITZ, _MB_CODES = {}, {}
_MB_LOCK = threading.Lock()
_GRENZEN.update({"mb_code": (5, 3600), "mb_code_mail": (3, 900), "mb_anmelden": (10, 900), "mb_aktion": (30, 3600)})
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
                e[k] = bool(roh[k]) if isinstance(s, bool) else (int(roh[k]) if isinstance(s, int) else str(roh[k]))
    e["titel"] = e["titel"] or "Mitgliederbereich"
    e["geheim_gesetzt"] = bool(roh.get("geheim"))
    return e


def _mb_geheim(d):
    return str(((d.get("mitgliederbereich") or {}) if isinstance(d.get("mitgliederbereich"), dict) else {}).get("geheim") or "")


def akt_mitgliederbereich(d, b=None, ich=""):
    """Einstellungen (Administrator). {"geheim_neu": true} erzeugt das Webhook-Geheimnis neu – wird nur einmal angezeigt."""
    roh = d.get("mitgliederbereich") if isinstance(d.get("mitgliederbereich"), dict) else {}
    extra = {}
    if b is not None:
        for k, s in MB_STANDARD.items():
            if k not in b:
                continue
            v = b[k]
            if isinstance(s, bool):
                roh[k] = bool(v)
            elif isinstance(s, int):
                roh[k] = max(5, min(240, int(v or 30)))
            elif k == "tarife":
                namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
                if not isinstance(v, list) or any(x not in namen for x in v):
                    raise Fehler("Buchbare Tarife: nur vorhandene Tarife auswählen.")
                roh[k] = [str(x) for x in v]
            elif k == "titel":
                roh[k] = text_einzeilig(v or "", 80) or "Mitgliederbereich"
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
            "antraege": len(tarif_antraege(d)), "apps": len([x for x in mitglied_apps(d).values() if x.get("ablauf", 0) > time.time()]), "auftraege": [{"referenz": r, **{k: a.get(k) for k in ("sparte", "parzelle", "tarif", "art", "betrag", "status", "erstellt", "bezahlt_am", "name")}}
                                                                for r, a in auf],
            **extra, "log": (["✔ Gespeichert."] + (["Neues Webhook-Geheimnis – jetzt kopieren, es wird nur einmal angezeigt."] if extra else [])) if b is not None else []}


# ---- Anmeldung mit E-Mail-Code ---------------------------------------------------------------------------------------
def _mb_hash(x):
    return hashlib.sha256(("SparteNet-Mitglied|" + str(x)).encode()).hexdigest()


def mb_mitglieder_von(d, email):
    e = name_norm(email)
    return {i: m for i, m in mitglieder(d).items() if e and name_norm(m.get("email")) == e}


def mb_code_anfordern(d, b, quelle):
    email = str(b.get("email") or "").strip()
    antwort = {"ok": True, "text": "Wenn die Adresse bei uns hinterlegt ist, kommt jetzt ein Anmeldecode per E-Mail (10 Minuten gültig)."}
    if not re.fullmatch(r"[^@\s,;<>]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,}", email):
        raise Fehler("Bitte eine gültige E-Mail-Adresse eingeben.")
    _grenze("mb_code", quelle)
    _grenze("mb_code_mail", name_norm(email))
    treffer = mb_mitglieder_von(d, email)
    if not treffer:
        LOG.info("Mitgliederbereich: Code für unbekannte Adresse angefordert")
        return antwort
    email = next(iter(treffer.values()))["email"]          # an die hinterlegte Adresse, nicht an die eingetippte
    code = f"{secrets.randbelow(1000000):06d}"
    with _MB_LOCK:
        _MB_CODES[name_norm(email)] = {"hash": _mb_hash(code), "bis": time.time() + 600, "versuche": 0}
    email_senden(d, email, f"Ihr Anmeldecode: {code}", None,
                 f"<p>Ihr Anmeldecode für den Mitgliederbereich lautet:</p><p style='font-size:28px;letter-spacing:6px;font-weight:bold'>{code}</p>"
                 "<p>Er gilt 10 Minuten. Haben Sie keinen Code angefordert, können Sie diese E-Mail ignorieren.</p>")
    return antwort


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


def mb_geraete(d, kz, p):
    """Geräte im Netz der Parzelle (IP 10.<Sparte>.<Parzelle>.<Gerät>) – aus der Client-Liste des Gateways, 60 s zwischengespeichert"""
    netz = _parzellen_netz_plan(d, kz, p)
    if not netz:
        return {"geraete": [], "fehler": "Für diese Parzelle ist kein Netz geplant."}
    if time.time() - _GERAETE_CACHE["zeit"] > 60:
        try:
            _GERAETE_CACHE.update(liste=Gateway(d).alle("/v1/sites/{site}/clients"), fehler="", zeit=time.time())
        except Exception as e:
            _GERAETE_CACHE.update(fehler="Geräteliste gerade nicht abrufbar.", zeit=time.time() - 30)
            LOG.warning("Mitgliederbereich: Geräte nicht abrufbar: %s", e)
    try:
        n = ipaddress.ip_network(netz, strict=False)
    except ValueError:
        return {"geraete": [], "fehler": "Netz der Parzelle ungültig."}
    aus = []
    for c in _GERAETE_CACHE["liste"]:
        ip = c.get("ipAddress") or ""
        try:
            if ip and ipaddress.ip_address(ip) in n:
                mac = str(c.get("macAddress") or "")
                aus.append({"name": c.get("name") or c.get("hostname") or "Gerät", "ip": ip, "geraet": ip.rsplit(".", 1)[-1],
                            "mac": ("…" + mac[-8:]) if len(mac) > 8 else mac, "art": {"WIRELESS": "WLAN", "WIRED": "Kabel"}.get(str(c.get("type") or "").upper(), c.get("type") or ""),
                            "seit": c.get("connectedAt") or ""})
        except ValueError:
            continue
    aus.sort(key=lambda x: int(x["geraet"]) if x["geraet"].isdigit() else 999)
    return {"geraete": aus, "netz": netz, "fehler": _GERAETE_CACHE["fehler"]}


def _tarif_info(t):
    return {"name": t["name"], "down": t["down"], "up": t["up"], "preis": t.get("preis", 0), "geraete": t.get("geraete", 0),
            "laufzeit": laufzeit_text(t.get("laufzeit", 0), t.get("laufzeit_einheit", "tage"))}


def tarif_rang(t):
    """Reihenfolge für Up-/Downgrade: Preis, dann Download, dann Upload"""
    return (float(t.get("preis") or 0), float(t.get("down") or 0), float(t.get("up") or 0)) if t else (0, 0, 0)


def mb_buchbar(d):
    """im Mitgliederbereich buchbare Tarife (Auswahl in den Einstellungen; leer = alle)"""
    wahl = mb_einstellungen(d)["tarife"]
    return [t for t in tarife_pruefen(d["tarife"]) if not wahl or t["name"] in wahl]


def mb_tickets(d, mid, m):
    """nur die Tickets dieses Mitglieds: fest zugeordnet – oder ohne Zuordnung mit gleicher E-Mail UND gleicher Parzelle"""
    kz, p = m.get("sparte", ""), str(m.get("parzelle") or "")
    aus = []
    for i, t in mitglied_tickets(d, mid):
        k = t.get("kontakt") or {}
        if k.get("mitglied") == mid or (not k.get("mitglied") and str(t.get("sparte") or "") == kz and str(t.get("parzelle") or "") == p):
            aus.append((i, t))
    return aus


def tarif_antraege(d, kz=None, p=None, offen=True):
    """[(ticket_id, ticket)] mit Tarif-Antrag (Downgrade, oder Buchung/Verlängerung im Modus „Anfrage“)"""
    return [(i, t) for i, t in tickets_daten(d)["liste"].items() if isinstance(t.get("antrag"), dict)
            and (kz is None or t["antrag"].get("sparte") == kz) and (p is None or str(t["antrag"].get("parzelle")) == str(p))
            and (not offen or t["antrag"].get("status") == "offen")]


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
                 if x.get("mitglied") == mid and x.get("status") != "storniert"]
        rechn.sort(key=lambda x: x.get("datum") or "", reverse=True)
        akt_t = next((t for t in tarife_pruefen(d["tarife"]) if t["name"] == tarif), None)
        antr = [{"nr": t["nr"], "art": t["antrag"]["art"], "tarif": t["antrag"]["tarif"], "erstellt": t.get("erstellt", "")}
                for _i, t in tarif_antraege(d, kz, p) if kz and p]
        tk = [{"nr": t.get("nr"), "betreff": t.get("betreff", ""), "status": T_STATUS.get(t.get("status"), ""), "erstellt": t.get("erstellt", ""),
               "loesung": t.get("loesung", "")} for _i, t in mb_tickets(d, mid, m)][:20] if e["zeige_anfragen"] else []
        offen_auftrag = next(({"referenz": r, "tarif": a.get("tarif"), "art": a.get("art"), "betrag": a.get("betrag")} for r, a in zahlungsauftraege(d).items()
                              if a.get("mitglied") == mid and a.get("status") == "offen" and a.get("erstellt", "") > time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() - 86400))), None)
        parz.append({"id": mid, "sparte": kz, "sparte_name": _sparten_kz(d).get(kz, kz), "parzelle": p, "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(),
                     "tarif": tarif, "laufzeit": ({"start": time.strftime("%d.%m.%Y %H:%M", time.localtime(lz["start"])), "ende": time.strftime("%d.%m.%Y %H:%M", time.localtime(lz["ende"])),
                                                   "aktiv": lz.get("status") == "aktiv", "rest_tage": max(0, int((lz["ende"] - time.time()) // 86400))} if lz else None),
                     "gesperrt": bool(gesp), "rechnungen": rechn, "offen": round(sum(float(x["brutto"] or 0) - float(x["bezahlt"] or 0) for x in rechn), 2),
                     "tickets": tk, "auftrag": offen_auftrag, "antraege": antr, "rang": list(tarif_rang(akt_t)) if akt_t else None,
                     **({"tarif_laufzeit": laufzeit_text(akt_t.get("laufzeit", 0), akt_t.get("laufzeit_einheit", "tage")) if akt_t.get("laufzeit") else "unbegrenzt",
                         "tarif_preis": akt_t.get("preis", 0), "tarif_down": akt_t["down"], "tarif_up": akt_t["up"], "tarif_geraete": akt_t.get("geraete", 0)} if akt_t else {})})
    return {"mitglied": parz[0]["name"] if parz else "", "parzellen": parz, "tarife": tarife,
            "erlaubt": {k: e[k] for k in ("tarifwechsel", "downgrade", "neubuchung", "verlaengern", "geraete", "zeige_rechnungen", "zeige_anfragen", "neue_anfrage", "zugangskarte")},
            "modus": e["modus"], "hinweis": e["hinweis"], "titel": e["titel"], "kategorien": list(ticket_kategorien(d))}


def _mb_parzelle(d, email, mid):
    m = mb_mitglieder_von(d, email).get(str(mid or ""))
    if not m or not m.get("sparte") or not str(m.get("parzelle") or "").isdigit():
        raise Fehler("Parzelle nicht gefunden.")
    return str(mid), m, m["sparte"], str(m["parzelle"])


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
    if art not in ("neu", "wechsel", "verlaengern"):
        raise Fehler("Unbekannte Aktion.")
    aktuell = ((d.get("buchungen") or {}).get(kz) or {}).get(p, "")
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
    if art == "wechsel" and not upgrade:           # Downgrade: immer Freigabe im Ticketsystem
        _tid, tk = _mb_ticket(d, mid, m, kz, p, f"Antrag: {beschr}", f"Antrag aus dem Mitgliederbereich: Wechsel von {aktuell} zu {tarif} ({preis}). "
                              "Bitte im Ticket freigeben oder ablehnen.", antrag=antrag)
        return {"ok": True, "text": f"Ihr Antrag {tk['nr']} auf Wechsel zu {tarif} ist beim Verein eingegangen. Ein Wechsel in einen kleineren Tarif muss freigegeben werden – Sie bekommen Bescheid."}
    if e["modus"] == "anfrage":
        if upgrade:                                # Upgrade jederzeit: sofort buchen, Vorstand per Ticket informieren
            akt_buchungen_speichern(d, kz, {p: tarif})
            _tid, tk = _mb_ticket(d, mid, m, kz, p, beschr, f"Upgrade im Mitgliederbereich gebucht: {aktuell} → {tarif} ({preis}). Zur Info – bereits umgesetzt.", status="erledigt")
            journal(f"Mitgliederbereich: {beschr} gebucht ({tk['nr']})")
            _mb_mail(d, m, f"Tarif gewechselt: {tarif}", f"<p>Ihr Tarif für Parzelle {p} ist jetzt <b>{html_mod.escape(tarif)}</b> (vorher {html_mod.escape(aktuell)}).</p>")
            return {"ok": True, "text": f"Erledigt – Ihr Tarif ist jetzt {tarif}. Die Änderung wird im WLAN vom Verein übernommen."}
        _tid, tk = _mb_ticket(d, mid, m, kz, p, f"Antrag: {beschr}", f"Antrag aus dem Mitgliederbereich: {beschr} ({preis}). Bitte im Ticket freigeben oder ablehnen.", antrag=antrag)
        return {"ok": True, "text": f"Danke! Ihr Antrag {tk['nr']} ist beim Verein eingegangen. Sie bekommen Bescheid, sobald er freigegeben ist."}
    ref = "SN-" + secrets.token_hex(5).upper()
    a = {"mitglied": mid, "sparte": kz, "parzelle": int(p), "tarif": tarif, "tarif_alt": aktuell, "art": art, "betrag": round(float(t.get("preis") or 0), 2),
         "email": m.get("email", ""), "name": name, "beschreibung": beschr, "status": "offen", "erstellt": time.strftime("%Y-%m-%d %H:%M")}
    if a["betrag"] <= 0:
        raise Fehler("Für diesen Tarif ist kein Preis hinterlegt – bitte beim Verein melden.")
    url = _link_erzeugen(d, e, ref, a, basis)
    z = zahlungsauftraege(d)
    z[ref] = a
    for k in sorted(z, key=lambda r: z[r].get("erstellt", ""))[:-2000]:
        z.pop(k, None)
    speichere(d)
    journal(f"Zahlungsauftrag {ref} angelegt: {beschr}, {geld(a['betrag'])}")
    return {"ok": True, "url": url, "referenz": ref}


def _mb_mail(d, m, betreff, inhalt):
    if not m.get("email"):
        return
    try:
        email_senden(d, m["email"], betreff, None, f"<p>Hallo {html_mod.escape(m.get('vorname') or '')},</p>{inhalt}")
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
    else:
        akt_buchungen_speichern(d, kz, {p: a["tarif"]})
    a.update(status="bezahlt", bezahlt_am=time.strftime("%Y-%m-%d %H:%M"), quelle=text_einzeilig(quelle, 80))
    speichere(d)
    journal(f"Zahlung bestätigt {ref}: {a['beschreibung']} ({geld(a['betrag'])}) – gebucht")
    ereignis("zahlung_mitglied", {"sparte": kz, "parzelle": int(p), "tarif": a["tarif"], "tarif_alt": a.get("tarif_alt", ""), "betrag": f"{a['betrag']:.2f}",
                                  "referenz": ref, "email": a.get("email", ""), "name": a.get("name", ""), "quelle": quelle or "Bezahldienst"}, d)
    try:
        email_senden(d, a["email"], f"Zahlung erhalten: {a['beschreibung']}", None,
                     f"<p>Hallo {html_mod.escape(a.get('name') or '')},</p><p>vielen Dank – Ihre Zahlung über {geld(a['betrag'])} ist eingegangen.</p>"
                     f"<p><b>{html_mod.escape(a['beschreibung'])}</b> ist gebucht (Referenz {ref}). Die Änderung am WLAN wird vom Verein übernommen.</p>")
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
                         anhaenge=[(f"Zugangskarte_Parzelle_{p}.pdf", karte, "application/pdf")])
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
    if not x or x.get("mitglied") not in mb_mitglieder_von(d, email):
        raise Fehler("Rechnung nicht gefunden.")
    return rechnung_pdf(d, x), f"Rechnung_{x['nr']}.pdf"


def mein_seite(d):
    """Seite /mein im Design der Pächter-Seite (Kopf, Farben, Schrift, Hintergrund und Fußzeile von dort)"""
    e = mb_einstellungen(d)
    titel = html_mod.escape(e["titel"])
    seite = portal_seite(d)
    kopf, rest = seite.split("<body", 1)
    kopf = re.sub(r"<title>.*?</title>", f"<title>{titel}</title>", kopf, flags=re.S)
    body_tag, rest = rest.split(">", 1)
    header = rest[:rest.index("</header>")].replace('<div id="titel"></div>', f'<div id="titel">{titel}</div>') + "</header>"
    fuss = re.search(r"<footer>.*?</footer>", seite, re.S)
    text = html_mod.escape(e["text_anmeldung"]) if e["text_anmeldung"] else ("Mit der E-Mail-Adresse, die beim Verein für Ihre Parzelle hinterlegt ist. "
                                                                           "Sie bekommen einen Anmeldecode per E-Mail – ein Passwort ist nicht nötig.")
    return (MEIN_HTML.replace("__KOPF__", kopf + "<body" + body_tag + ">" + header).replace("__FUSS__", fuss.group(0) if fuss else "")
            .replace("__ANMELDETEXT__", text))


MEIN_HTML = r"""__KOPF__<main>
<style>.zeile{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.zeile>*{flex:1}.klein{font-size:13px;color:var(--m)}.tabelle{width:100%;border-collapse:collapse;font-size:14px}
.tabelle td,.tabelle th{padding:7px 6px;border-bottom:1px solid var(--l);text-align:left}.wert{font-size:22px;font-weight:700}.knoepfe{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.k2{border:1px solid var(--l);background:var(--c);color:var(--t);border-radius:calc(var(--ecken) * .7);padding:10px 14px;cursor:pointer;font:inherit}.k2:hover{border-color:var(--a)}
.tarife{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;margin-top:10px}.tarif{border:1.5px solid var(--l);border-radius:var(--ecken);padding:12px;cursor:pointer;background:var(--c)}
.tarif.akt{border-color:var(--a);box-shadow:0 0 0 2px var(--a) inset}.tarif b{font-size:17px}.gesperrt{background:#fde8e6;color:#b42318;border-radius:8px;padding:8px 10px;margin-top:8px}</style>
<section id="v_login" class="karte" style="display:none"><h2 style="margin-top:0">Anmelden</h2><p class="hint">__ANMELDETEXT__</p>
<label for="l_email">E-Mail-Adresse</label><input id="l_email" type="email" autocomplete="email" onkeydown="if(event.key=='Enter')codeAnfordern()"><button class="los" id="l_b1" onclick="codeAnfordern()">Code per E-Mail senden</button>
<div id="l_code_box" style="display:none"><label for="l_code">Anmeldecode aus der E-Mail</label><input id="l_code" onkeydown="if(event.key=='Enter')anmelden()" inputmode="numeric" autocomplete="one-time-code" maxlength="6" style="font-size:22px;letter-spacing:6px;text-align:center"><button class="los" onclick="anmelden()">Anmelden</button></div>
<div class="msg" id="m_login"></div></section>
<div id="v_daten" style="display:none"><div class="zeile" style="margin-bottom:10px"><p class="hint" id="d_hallo" style="margin:0"></p><div style="flex:none"><select id="d_parz" onchange="zeigen()" style="min-width:200px"></select></div><button class="k2" style="flex:none" onclick="abmelden()">Abmelden</button></div>
<p class="hint" id="d_hinweis"></p><div class="msg" id="m_daten"></div>
<section class="karte" style="display:block"><h2 style="margin-top:0">Mein Tarif</h2><div id="d_tarif"></div><div id="d_wechsel"></div></section>
<section class="karte" style="display:block" id="s_geraete"><h2 style="margin-top:0">Meine Geräte im WLAN</h2><p class="hint">Geräte, die gerade im Netz Ihrer Parzelle angemeldet sind. Erkennbar an der IP-Adresse: <span id="d_netz"></span> – die letzte Zahl ist das Gerät.</p><div id="d_geraete">…</div><div class="knoepfe"><button class="k2" onclick="geraete()">Aktualisieren</button><button class="k2" id="b_karte" onclick="karte()">Zugangskarte per E-Mail</button></div></section>
<section class="karte" style="display:block" id="s_rechnungen"><h2 style="margin-top:0">Meine Rechnungen</h2><div id="d_rechnungen"></div></section>
<section class="karte" style="display:block" id="s_anfragen"><h2 style="margin-top:0">Meine Anfragen</h2><div id="d_tickets"></div>
<details style="margin-top:10px" id="s_neu"><summary style="cursor:pointer;font-weight:600">Neue Anfrage</summary><label for="t_kat">Worum geht es?</label><select id="t_kat"></select><label for="t_betreff">Betreff</label><input id="t_betreff" maxlength="160" onkeydown="if(event.key=='Enter'){event.preventDefault();$('t_text').focus()}"><label for="t_text">Nachricht</label><textarea id="t_text" maxlength="5000" onkeydown="if(event.key=='Enter'&&(event.ctrlKey||event.metaKey))ticket()" placeholder="Strg+Enter sendet"></textarea><button class="los" onclick="ticket()">Anfrage senden</button></details><div class="msg" id="m_ticket"></div></section></div>
</main>__FUSS__<script>const $=i=>document.getElementById(i),esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));let D=null,WAHL=null;
const eur=x=>Number(x||0).toLocaleString("de-DE",{style:"currency",currency:"EUR"});
function msg(id,t,ok){const m=$(id);m.className="msg "+(t?(ok?"ok":"f"):"");m.textContent=t||""}
async function post(p,b){const r=await fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b||{})});const d=await r.json().catch(()=>({}));if(r.status==401&&d.anmelden){ansicht(false);throw new Error("Bitte erneut anmelden.")}if(!r.ok)throw new Error(d.fehler||r.status);return d}
function ansicht(an){$("v_login").style.display=an?"none":"block";$("v_daten").style.display=an?"block":"none"}
async function codeAnfordern(){try{const d=await post("/mein/code",{email:$("l_email").value.trim()});msg("m_login",d.text,true);$("l_code_box").style.display="block";$("l_code").focus()}catch(e){msg("m_login",e.message)}}
async function anmelden(){try{await post("/mein/anmelden",{email:$("l_email").value.trim(),code:$("l_code").value});msg("m_login","");laden()}catch(e){msg("m_login",e.message)}}
async function abmelden(){await post("/mein/abmelden").catch(()=>{});location.replace("/mein")}
async function laden(){try{D=await post("/mein/daten");ansicht(true)}catch(e){ansicht(false);return}
 $("d_hallo").textContent="Hallo "+D.mitglied;$("d_hinweis").textContent=D.hinweis||"";$("d_parz").innerHTML=D.parzellen.map(p=>`<option value="${esc(p.id)}">${esc(p.sparte_name)} · Parzelle ${esc(p.parzelle)}</option>`).join("");
 $("d_parz").style.display=D.parzellen.length>1?"":"none";if(WAHL&&D.parzellen.some(p=>p.id==WAHL))$("d_parz").value=WAHL;$("t_kat").innerHTML=D.kategorien.map(k=>`<option>${esc(k)}</option>`).join("");
 const q=new URLSearchParams(location.search);if(q.get("zahlung")=="abbruch")msg("m_daten","Die Zahlung wurde abgebrochen – es wurde nichts gebucht.");else if(q.get("zahlung"))msg("m_daten","Danke! Sobald der Bezahldienst die Zahlung bestätigt, ist die Buchung erledigt (Referenz "+q.get("zahlung")+").",true);
 if(q.has("zahlung"))history.replaceState(null,"","/mein");zeigen()}
function P(){return D.parzellen.find(p=>p.id==$("d_parz").value)||D.parzellen[0]}
function zeigen(){const p=P();if(!p)return;WAHL=p.id;const lz=p.laufzeit;
 $("d_tarif").innerHTML=p.tarif?`<div class="zeile"><div><div class="klein">Tarif</div><div class="wert">${esc(p.tarif)}</div></div>${lz?`<div><div class="klein">Laufzeit</div><div><b>${lz.aktiv?"bis "+esc(lz.ende):"abgelaufen am "+esc(lz.ende)}</b>${lz.aktiv?`<br><span class="klein">noch ${lz.rest_tage} Tag(e)</span>`:""}</div></div>`:`<div><div class="klein">Laufzeit</div><div><b>unbegrenzt</b></div></div>`}<div><div class="klein">Offen</div><div class="wert" style="font-size:18px">${eur(p.offen)}</div></div></div>${p.gesperrt?'<div class="gesperrt">Der WLAN-Zugang ist gerade gesperrt (Laufzeit abgelaufen) – mit einer Verlängerung wird er wieder freigegeben.</div>':""}`:'<p class="hint">Für diese Parzelle ist noch kein Tarif gebucht.</p>';
 const e=D.erlaubt,R=t=>t.rang.join(","),hoeher=(t)=>p.rang&&(t.rang[0]>p.rang[0]||t.rang[0]==p.rang[0]&&(t.rang[1]>p.rang[1]||t.rang[1]==p.rang[1]&&t.rang[2]>p.rang[2]));
 const ups=D.tarife.filter(t=>t.name!=p.tarif&&hoeher(t)),downs=D.tarife.filter(t=>t.name!=p.tarif&&!hoeher(t));let akt=[];
 if(!p.tarif&&e.neubuchung&&D.tarife.length)akt.push(["neu","Tarif buchen"]);if(p.tarif&&e.tarifwechsel&&ups.length)akt.push(["upgrade","⬆ Upgrade"]);if(p.tarif&&e.downgrade&&downs.length&&!p.antraege.length)akt.push(["downgrade","⬇ Kleinerer Tarif"]);
 if(p.tarif&&e.verlaengern&&p.tarif_laufzeit&&p.tarif_laufzeit!="unbegrenzt"&&!p.antraege.length)akt.push(["verlaengern","Laufzeit verlängern ("+p.tarif_laufzeit+")"]);
 $("d_wechsel").innerHTML=(p.auftrag?`<p class="hint">Offener Zahlungsauftrag ${esc(p.auftrag.referenz)} (${esc(p.auftrag.tarif)}, ${eur(p.auftrag.betrag)}) – wird gebucht, sobald die Zahlung bestätigt ist.</p>`:"")
  +p.antraege.map(a=>`<p class="hint">⏳ Antrag ${esc(a.nr)} vom ${esc(a.erstellt.slice(0,10))}: ${{wechsel:"Wechsel zu",neu:"Buchung",verlaengern:"Verlängerung"}[a.art]||""} ${esc(a.tarif)} – wartet auf Freigabe durch den Verein.</p>`).join("")
  +(akt.length?`<div class="knoepfe">${akt.map(([a,t])=>`<button class="k2" onclick="waehlen('${a}')">${esc(t)}</button>`).join("")}</div><div id="d_auswahl"></div>`:"");
 $("s_rechnungen").style.display=e.zeige_rechnungen?"block":"none";$("s_anfragen").style.display=e.zeige_anfragen||e.neue_anfrage?"block":"none";$("d_tickets").style.display=e.zeige_anfragen?"":"none";$("s_neu").style.display=e.neue_anfrage?"":"none";$("b_karte").style.display=e.zugangskarte?"":"none";
 $("d_rechnungen").innerHTML=p.rechnungen.length?'<table class="tabelle"><tr><th>Nr.</th><th>Datum</th><th>Betrag</th><th>Status</th><th></th></tr>'+p.rechnungen.map(r=>`<tr><td>${esc(r.nr)}</td><td>${esc(r.datum)}</td><td>${eur(r.brutto)}</td><td>${esc(r.status)}</td><td><a href="/mein/rechnung?id=${encodeURIComponent(r.id)}" target="_blank" rel="noopener">PDF</a></td></tr>`).join("")+"</table>":'<p class="hint">Noch keine Rechnungen.</p>';
 $("d_tickets").innerHTML=p.tickets.length?p.tickets.map(t=>`<div class="antwort"><b>${esc(t.nr)}</b> · ${esc(t.status)} · ${esc(t.erstellt)}<br>${esc(t.betreff)}${t.loesung?"<br><small>Lösung: "+esc(t.loesung)+"</small>":""}</div>`).join(""):'<p class="hint">Keine Anfragen.</p>';
 $("s_geraete").style.display=e.geraete?"block":"none";if(e.geraete)geraete()}
function waehlen(wie){const p=P();const e=D.erlaubt,hoeher=(t)=>p.rang&&(t.rang[0]>p.rang[0]||t.rang[0]==p.rang[0]&&(t.rang[1]>p.rang[1]||t.rang[1]==p.rang[1]&&t.rang[2]>p.rang[2]));
 const art=wie=="upgrade"||wie=="downgrade"?"wechsel":wie;
 const liste=wie=="verlaengern"?[{name:p.tarif,laufzeit:p.tarif_laufzeit,preis:p.tarif_preis,down:p.tarif_down,up:p.tarif_up,geraete:p.tarif_geraete}]:wie=="upgrade"?D.tarife.filter(t=>t.name!=p.tarif&&hoeher(t)):wie=="downgrade"?D.tarife.filter(t=>t.name!=p.tarif&&!hoeher(t)):D.tarife;
 const knopf=wie=="downgrade"?"Antrag stellen (Freigabe durch den Verein)":D.modus=="bezahldienst"?"Weiter zur Bezahlung":wie=="upgrade"?"Jetzt wechseln":"Antrag an den Verein senden";
 const hinweis=wie=="upgrade"?"Ein Upgrade ist jederzeit möglich"+(D.modus=="bezahldienst"?" – nach der Bezahlung sofort gebucht.":" und wird sofort gebucht."):wie=="downgrade"?"Ein Wechsel in einen kleineren Tarif muss vom Verein freigegeben werden. Sie bekommen per E-Mail Bescheid.":"";
 $("d_auswahl").innerHTML=(hinweis?`<p class="hint" style="margin:10px 0 0">${esc(hinweis)}</p>`:"")+`<div class="tarife">${liste.map(t=>`<div class="tarif" data-t="${esc(t.name)}"><b>${esc(t.name)}</b><br><span class="klein">${t.down} / ${t.up} Mbit/s · ${t.geraete?t.geraete+" Geräte":"Geräte unbegrenzt"}<br>Laufzeit: ${esc(t.laufzeit)}</span><br><b>${eur(t.preis)}</b></div>`).join("")}</div>
 <button class="los" id="d_los" disabled>${esc(knopf)}</button>`;
 let wahl=wie=="verlaengern"?p.tarif:null;document.querySelectorAll(".tarif").forEach(x=>{if(x.dataset.t==wahl)x.classList.add("akt");x.onclick=()=>{wahl=x.dataset.t;document.querySelectorAll(".tarif").forEach(y=>y.classList.toggle("akt",y===x));$("d_los").disabled=false}});
 $("d_los").disabled=!wahl;$("d_los").onclick=async()=>{try{$("d_los").disabled=true;const d=await post("/mein/buchen",{id:p.id,art,tarif:wahl});if(d.url){location.href=d.url;return}msg("m_daten",d.text,true);laden()}catch(e){msg("m_daten",e.message);$("d_los").disabled=false}}}
async function geraete(){const p=P();$("d_geraete").textContent="…";try{const d=await post("/mein/geraete",{id:p.id});$("d_netz").textContent=d.netz||"";
 $("d_geraete").innerHTML=d.geraete.length?'<table class="tabelle"><tr><th>Gerät</th><th>IP-Adresse</th><th>Nr.</th><th>Verbindung</th></tr>'+d.geraete.map(g=>`<tr><td>${esc(g.name)}<br><span class="klein">${esc(g.mac)}</span></td><td>${esc(g.ip)}</td><td>${esc(g.geraet)}</td><td>${esc(g.art)}</td></tr>`).join("")+"</table>":`<p class="hint">${esc(d.fehler||"Gerade ist kein Gerät angemeldet.")}</p>`}catch(e){$("d_geraete").textContent=e.message}}
async function karte(){try{const d=await post("/mein/zugangskarte",{id:P().id});msg("m_daten",d.text,true)}catch(e){msg("m_daten",e.message)}}
async function ticket(){try{const d=await post("/mein/ticket",{id:P().id,kategorie:$("t_kat").value,betreff:$("t_betreff").value,text:$("t_text").value});msg("m_ticket",d.text,true);$("t_betreff").value="";$("t_text").value="";laden()}catch(e){msg("m_ticket",e.message)}}
laden();</script></body></html>"""


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

"""SparteNet Manager – Zeitplan im Hintergrund: Störungsüberwachung, tägliche Vertragsprüfung, Wochenbericht

Läuft jede Minute. Der Stand (letzte Läufe, Gerätezustände, Störungsverlauf) liegt in der Ablage „Zeitplan_Stand.json“,
nicht in den Einstellungen – so entstehen keine Schreibvorgänge im Minutentakt.
Störung: Gerät länger als „Verzögerung“ offline → Ticket (Kategorie Störung, Priorität hoch) und Ereignis „stoerung“;
wieder online → Vermerk im Ticket, Ereignis „stoerung_behoben“ (auf Wunsch Ticket erledigt).
Geprüft wird die eingestellte Konsole (Reiter „Verbindung“).
"""
from .datenschutz import *  # noqa: F401,F403 – alle Namen der vorherigen Module

UEB_STANDARD = {"aktiv": False, "intervall": 10, "verzoegerung": 15, "ticket": True, "zustaendig": "", "auto_erledigen": True}
BER_STANDARD = {"aktiv": False, "tag": 0, "uhrzeit": "07:00", "an": ""}
STAND_NAME = "Zeitplan_Stand.json"
EREIGNIS_LOG = "Ereignis_Protokoll.json"
_STAND_LOCK = threading.Lock()
_AUS = {"OFFLINE", "CONNECTION_INTERRUPTED", "ISOLATED", "DISCONNECTED"}
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def _einst(d, name, std):
    e = dict(std)
    roh = d.get(name) if isinstance(d.get(name), dict) else {}
    for k, s in std.items():
        if k in roh:
            e[k] = bool(roh[k]) if isinstance(s, bool) else (int(roh[k]) if isinstance(s, int) else str(roh[k]))
    return e


def stand_lesen():
    try:
        roh = ablage_lesen(STAND_NAME)
        return json.loads(roh.decode("utf-8")) if roh else {}
    except (ValueError, Fehler):
        return {}


def stand_schreiben(s):
    ablage_schreiben(STAND_NAME, json.dumps(s, ensure_ascii=False))


# ---- Ereignis-Protokoll (für den Wochenbericht) ---------------------------------------------------------------------
_LOG_LOCK = threading.Lock()


def _protokoll(typ, daten, d):
    if typ not in ("buchung", "kuendigung", "zahlung", "mitglied_neu", "ticket_neu", "ticket_erledigt", "ticket_geschlossen", "stoerung", "stoerung_behoben",
                   "vertrag_gekuendigt", "laufzeit_ende", "laufzeit_verlaengert", "zugang_gesperrt", "zugang_freigegeben"):
        return
    with _LOG_LOCK:
        try:
            roh = ablage_lesen(EREIGNIS_LOG)
            liste = json.loads(roh.decode("utf-8")) if roh else []
        except (ValueError, Fehler):
            liste = []
        liste.append({"zeit": time.strftime("%Y-%m-%d %H:%M"), "typ": typ, **{k: daten.get(k) for k in ("sparte", "parzelle", "tarif", "tarif_alt", "betrag", "ticket", "geraet") if daten.get(k) not in (None, "")}})
        ablage_schreiben(EREIGNIS_LOG, json.dumps(liste[-5000:], ensure_ascii=False))


EREIGNIS_EMPFAENGER.append(_protokoll)


# ---- Störungsüberwachung ---------------------------------------------------------------------------------------------
def stoerungen_pruefen(d, jetzt=None):
    """ein Prüflauf; gibt Log-Zeilen zurück"""
    e = _einst(d, "ueberwachung", UEB_STANDARD)
    jetzt = jetzt or time.time()
    with _STAND_LOCK:
        st = stand_lesen()
        geraete = st.setdefault("geraete", {})
        log = []
        try:
            liste = Gateway(d).alle("/v1/sites/{site}/devices")
            aktuell = {(x.get("macAddress") or x.get("id") or x.get("name")): x for x in liste}
            fehler = ""
        except Fehler as f:
            aktuell, fehler = {"_konsole": {"name": f"Konsole {d.get('konsole_name') or ''}".strip(), "state": "OFFLINE", "model": "Cloud"}}, str(f)
            for k in geraete:            # ohne Verbindung keine Aussage über einzelne Geräte
                if k != "_konsole":
                    aktuell[k] = {**geraete[k], "state": geraete[k].get("state", "ONLINE")}
        if not fehler and "_konsole" in geraete:
            aktuell["_konsole"] = {"name": geraete["_konsole"].get("name", "Konsole"), "state": "ONLINE", "model": "Cloud"}
        for k, x in aktuell.items():
            g = geraete.setdefault(k, {})
            aus = str(x.get("state") or "").upper() in _AUS
            g.update(name=x.get("name") or g.get("name") or k, model=x.get("model") or g.get("model", ""), ip=x.get("ipAddress") or g.get("ip", ""), state=x.get("state", ""))
            if aus:
                g.setdefault("offline_seit", jetzt)
                if not g.get("gemeldet") and jetzt - g["offline_seit"] >= e["verzoegerung"] * 60:
                    g["gemeldet"] = jetzt
                    seit = time.strftime("%d.%m.%Y %H:%M", time.localtime(g["offline_seit"]))
                    daten = {"geraet": g["name"], "modell": g.get("model", ""), "ip": g.get("ip", ""), "seit": seit, "betreff": f"Störung: {g['name']} offline",
                             "nachricht": f"{g['name']} ({g.get('model', '')}, {g.get('ip', '')}) ist seit {seit} nicht erreichbar." + (f"\nFehler: {fehler}" if fehler else "")}
                    if e["ticket"]:
                        try:
                            tid, t = ticket_anlegen(d, {"betreff": daten["betreff"], "text": daten["nachricht"], "kategorie": "Störung / WLAN geht nicht",
                                                        "prioritaet": "hoch", "zustaendig": e["zustaendig"]}, "Überwachung", "Überwachung")
                            g["ticket"] = tid
                            daten["ticket"] = t["nr"]
                        except Fehler as f2:
                            log.append(f"Ticket nicht angelegt: {f2}")
                    ereignis("stoerung", daten, d)
                    st.setdefault("verlauf", []).append({"zeit": time.strftime("%Y-%m-%d %H:%M"), "geraet": g["name"], "art": "offline", "seit": seit})
                    log.append(f"⚠ Störung gemeldet: {g['name']}")
            elif g.get("offline_seit"):
                dauer = round((jetzt - g["offline_seit"]) / 60)
                if g.get("gemeldet"):
                    daten = {"geraet": g["name"], "dauer": f"{dauer} Min.", "betreff": f"Behoben: {g['name']} wieder online"}
                    tid = g.get("ticket")
                    t = tickets_daten(d)["liste"].get(tid) if tid else None
                    if t:
                        _verlauf(t, "Überwachung", "kommentar", f"{g['name']} ist wieder online (nach {dauer} Min.).")
                        if e["auto_erledigen"] and ticket_offen(t):
                            t["status"] = "erledigt"
                            _verlauf(t, "Überwachung", "aenderung", "Status: erledigt (automatisch)")
                        daten["ticket"] = t.get("nr")
                        speichere(d)
                    ereignis("stoerung_behoben", daten, d)
                    st.setdefault("verlauf", []).append({"zeit": time.strftime("%Y-%m-%d %H:%M"), "geraet": g["name"], "art": "online", "dauer": dauer})
                    log.append(f"✔ wieder online: {g['name']} (nach {dauer} Min.)")
                for f_ in ("offline_seit", "gemeldet", "ticket"):
                    g.pop(f_, None)
        st["verlauf"] = st.get("verlauf", [])[-500:]
        st["letzte_pruefung"] = jetzt
        st["fehler"] = fehler
        stand_schreiben(st)
    return log


def akt_ueberwachung(d, b=None, ich=""):
    if b is not None:
        e = _einst(d, "ueberwachung", UEB_STANDARD)
        for k, s in UEB_STANDARD.items():
            if k in b:
                try:
                    e[k] = bool(b[k]) if isinstance(s, bool) else (max(5 if k == "intervall" else 0, min(1440, int(b[k]))) if isinstance(s, int) else str(b[k] or ""))
                except (TypeError, ValueError):
                    raise Fehler("Intervall und Verzögerung in Minuten angeben.")
        if e["zustaendig"] and e["zustaendig"] not in _konten(d):
            raise Fehler("Diesen Benutzer gibt es nicht.")
        d["ueberwachung"] = e
        speichere(d)
        journal(f"Störungsüberwachung {'eingeschaltet' if e['aktiv'] else 'ausgeschaltet'} durch {ich}")
    log = []
    if b is not None and b.get("jetzt"):
        log = stoerungen_pruefen(d) or ["✔ Geprüft – keine neue Störung."]
    st = stand_lesen()
    g = [{"name": x.get("name"), "modell": x.get("model", ""), "ip": x.get("ip", ""), "status": x.get("state", ""),
          "offline_seit": time.strftime("%d.%m. %H:%M", time.localtime(x["offline_seit"])) if x.get("offline_seit") else "", "gemeldet": bool(x.get("gemeldet"))}
         for x in (st.get("geraete") or {}).values()]
    g.sort(key=lambda x: (not x["offline_seit"], x["name"] or ""))
    return {"einstellungen": _einst(d, "ueberwachung", UEB_STANDARD), "geraete": g, "verlauf": list(reversed((st.get("verlauf") or [])[-50:])),
            "letzte": time.strftime("%d.%m.%Y %H:%M", time.localtime(st["letzte_pruefung"])) if st.get("letzte_pruefung") else "", "fehler": st.get("fehler", ""),
            "konten": _konten(d), "log": log or ([f"✔ Gespeichert."] if b is not None else [])}


# ---- Wochenbericht ---------------------------------------------------------------------------------------------------
def wochenbericht_html(d, tage=7):
    grenze = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() - tage * 86400))
    try:
        roh = ablage_lesen(EREIGNIS_LOG)
        ev = [x for x in (json.loads(roh.decode("utf-8")) if roh else []) if x.get("zeit", "") >= grenze]
    except (ValueError, Fehler):
        ev = []
    n = lambda t: sum(1 for x in ev if x["typ"] == t)
    buch = d.get("buchungen") or {}
    preise = {t["name"]: float(t.get("preis") or 0) for t in tarife_pruefen(d["tarife"])}
    gebucht = sum(1 for b in buch.values() for t in b.values() if t)
    umsatz = sum(preise.get(t, 0) for b in buch.values() for t in b.values() if t)
    tk = tickets_daten(d)["liste"].values()
    offen = [t for t in tk if ticket_offen(t)]
    neu_t = sum(1 for t in tk if t.get("erstellt", "") >= grenze)
    erl_t = n("ticket_erledigt")
    r = rechnungen_daten(d)["liste"].values()
    bezahlt_woche = sum(float(z["betrag"]) for x in r for z in x.get("zahlungen") or [] if str(z.get("datum", "")) >= grenze[:10])
    offen_r = sum(float(x["brutto"]) - float(x.get("bezahlt") or 0) for x in r if x.get("status") in ("offen", "teilweise"))
    ueberf = sum(1 for x in r if x.get("status") in ("offen", "teilweise") and x.get("faellig", "9999") < time.strftime("%Y-%m-%d"))
    st = stand_lesen()
    stoer = [v for v in st.get("verlauf") or [] if v.get("zeit", "") >= grenze and v.get("art") == "offline"]
    jetzt_aus = [g.get("name") for g in (st.get("geraete") or {}).values() if g.get("offline_seit")]
    vtr = akt_vertraege(d)["zeilen"]
    frist = [z for z in vtr if z["status"] == "Frist läuft ab"]
    e = html_mod.escape
    def zeile(a, b):
        return f"<tr><td style='padding:4px 12px 4px 0'>{e(a)}</td><td style='padding:4px 0;text-align:right'><b>{e(str(b))}</b></td></tr>"
    h = (f"<h2>Wochenbericht</h2><p>Zeitraum: {e(_de(grenze[:10]))} bis {time.strftime('%d.%m.%Y')}</p>"
         "<h3>Buchungen</h3><table>" + zeile("neue Buchungen", n("buchung")) + zeile("Kündigungen", n("kuendigung")) + zeile("gebuchte Parzellen gesamt", gebucht)
         + zeile("Jahresumsatz laut Buchungen", geld(umsatz)) + zeile("neue Mitglieder", n("mitglied_neu")) + "</table>"
         "<h3>Anfragen</h3><table>" + zeile("neue Tickets", neu_t) + zeile("erledigt", erl_t) + zeile("offen", len(offen))
         + zeile("davon dringend/hoch", sum(1 for t in offen if t.get("prioritaet") in ("dringend", "hoch"))) + "</table>"
         "<h3>Einnahmen</h3><table>" + zeile("Zahlungseingänge (Woche)", geld(bezahlt_woche)) + zeile("offene Rechnungen", geld(offen_r))
         + zeile("davon überfällig (Anzahl)", ueberf) + "</table>"
         "<h3>Netz</h3><table>" + zeile("Störungen (Woche)", len(stoer)) + zeile("jetzt offline", ", ".join(jetzt_aus) or "–") + "</table>"
         + (f"<h3>Verträge</h3><p>Kündigungsfrist läuft bald ab: {len(frist)}</p>" if frist else "")
         + "<p style='color:#5d6b75;font-size:12px'>Automatisch erstellt vom SparteNet Manager.</p>")
    return h


def akt_wochenbericht(d, b=None, ich=""):
    if b is not None:
        e = _einst(d, "wochenbericht", BER_STANDARD)
        if "aktiv" in b:
            e["aktiv"] = bool(b["aktiv"])
        if "tag" in b:
            e["tag"] = max(0, min(6, int(b["tag"])))
        if "uhrzeit" in b:
            if not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", str(b["uhrzeit"])):
                raise Fehler("Uhrzeit als HH:MM.")
            e["uhrzeit"] = str(b["uhrzeit"])
        if "an" in b:
            an = [x.strip() for x in re.split(r"[,;\s]+", str(b["an"] or "")) if x.strip()]
            for x in an:
                if not re.fullmatch(r"[^@\s,;<>]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,}", x):
                    raise Fehler(f"E-Mail-Adresse „{x}“ ist ungültig.")
            e["an"] = ", ".join(an)
        if e["aktiv"] and not e["an"]:
            raise Fehler("Bitte mindestens einen Empfänger angeben.")
        d["wochenbericht"] = e
        speichere(d)
        journal(f"Wochenbericht {'eingeschaltet' if e['aktiv'] else 'ausgeschaltet'} durch {ich}")
    log = []
    if b is not None and b.get("jetzt"):
        e = _einst(d, "wochenbericht", BER_STANDARD)
        an = b.get("an_test") or e["an"]
        if not an:
            raise Fehler("Bitte einen Empfänger angeben.")
        email_senden(d, an, f"SparteNet Wochenbericht {time.strftime('%d.%m.%Y')}", None, wochenbericht_html(d))
        log = [f"✔ Wochenbericht an {an} gesendet."]
    return {"einstellungen": _einst(d, "wochenbericht", BER_STANDARD), "wochentage": WOCHENTAGE, "vorschau": wochenbericht_html(d),
            "log": log or (["✔ Gespeichert."] if b is not None else [])}


# ---- Zeitplan -------------------------------------------------------------------------------------------------------
ZEITPLAN_AUFGABEN = []   # weitere Aufgaben späterer Module: f(jetzt) – jede Minute, Fehler brechen den Rest nicht ab


def zeitplan_lauf(jetzt=None):
    jetzt = jetzt or time.time()
    for f in list(ZEITPLAN_AUFGABEN):
        try:
            f(jetzt)
        except Exception:
            LOG.error("Zeitplan-Aufgabe %s:\n%s", getattr(f, "__name__", f), traceback.format_exc())
    lt = time.localtime(jetzt)
    st = stand_lesen()
    d = lade()
    ue = _einst(d, "ueberwachung", UEB_STANDARD)
    if ue["aktiv"] and d.get("cloud_key") and d.get("konsole_id") and jetzt - float(st.get("letzte_pruefung") or 0) >= ue["intervall"] * 60 - 5:
        with SCHREIB_SPERRE:
            stoerungen_pruefen(lade(), jetzt)
    heute = time.strftime("%Y-%m-%d", lt)
    if lt.tm_hour >= 6 and st.get("vertraege_geprueft") != heute:
        with SCHREIB_SPERRE:
            vertraege_pruefen(lade())
        with SCHREIB_SPERRE:
            tickets_auto_schliessen(lade())
        with _STAND_LOCK:
            s2 = stand_lesen(); s2["vertraege_geprueft"] = heute; stand_schreiben(s2)
    wb = _einst(d, "wochenbericht", BER_STANDARD)
    if wb["aktiv"] and wb["an"] and lt.tm_wday == wb["tag"] and time.strftime("%H:%M", lt) >= wb["uhrzeit"] and st.get("bericht_gesendet") != heute:
        with _STAND_LOCK:
            s2 = stand_lesen(); s2["bericht_gesendet"] = heute; stand_schreiben(s2)
        email_senden(d, wb["an"], f"SparteNet Wochenbericht {time.strftime('%d.%m.%Y', lt)}", None, wochenbericht_html(d))
        journal(f"Wochenbericht gesendet an {wb['an']}")


def zeitplan_hintergrund():
    def schleife():
        time.sleep(20)
        while True:
            try:
                zeitplan_lauf()
            except Exception:
                LOG.error("Zeitplan:\n%s", traceback.format_exc())
            time.sleep(60)
    threading.Thread(target=schleife, daemon=True, name="zeitplan").start()


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

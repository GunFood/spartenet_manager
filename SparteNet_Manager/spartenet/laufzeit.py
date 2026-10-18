"""SparteNet Manager – Laufzeit von Tarifen: Zugang nach Ablauf automatisch sperren, nach Verlängerung wieder freigeben

Tarif mit Laufzeit (z. B. 1 Tag, 7 Tage, 1 Monat): bei der Buchung beginnt die Laufzeit, der Zeitplan prüft jede Minute.
• kurz vor Ablauf  → Ereignis „laufzeit_erinnerung“ (z. B. E-Mail an den Pächter über eine Automation)
• bei Ablauf       → Ereignis „laufzeit_ende“; Zugang der Parzelle sperren
• Verlängerung     → neue Laufzeit (ab Ende bzw. ab jetzt, wenn schon abgelaufen); Zugang wieder freigeben

„Zugang sperren“ heißt: der PPSK-Eintrag (Passwort → Parzellen-Netz) der Parzelle wird aus dem Pächter-WLAN entfernt. Netz, VLAN und
Passwort bleiben erhalten (PPSK_<kz>.csv unverändert) – „freigeben“ trägt genau dieses Passwort wieder ein. Andere Einträge bleiben unberührt.

Am Gateway geschieht das nur automatisch, wenn „Am Gateway automatisch sperren und freigeben“ ausdrücklich eingeschaltet ist
(Administrator). Sonst zeigt der Manager nur an, was zu tun ist, und das Sperren/Freigeben geht von Hand mit Vorschau und Bestätigung.
"""
from .zeitplan import *  # noqa: F401,F403 – alle Namen der vorherigen Module
import calendar
import datetime as _dt

LZ_STANDARD = {"gateway_auto": False, "erinnerung_stunden": 24, "buchung_entfernen": False}
_LZ_WIEDERHOLEN = 300          # fehlgeschlagene Gateway-Änderung frühestens nach 5 Minuten erneut versuchen

AUSLOESER.update({
    "laufzeit_erinnerung": "Laufzeit eines Tarifs endet bald (Zeit unter Tarife → Laufzeiten)",
    "laufzeit_ende": "Laufzeit eines Tarifs ist abgelaufen",
    "laufzeit_verlaengert": "Laufzeit verlängert",
    "zugang_gesperrt": "Zugang einer Parzelle am Gateway gesperrt",
    "zugang_freigegeben": "Zugang einer Parzelle am Gateway wieder freigegeben",
})
AKTIONEN["laufzeit_verlaengern"] = "Laufzeit verlängern (Zugang wird wieder freigegeben)"
PLATZHALTER.update({"{laufzeit}": "Laufzeit des Tarifs (z. B. 7 Tage)", "{laufzeit_ende}": "Ende der Laufzeit (Datum und Uhrzeit)",
                    "{laufzeit_start}": "Beginn der Laufzeit"})


# ---- Grundlagen -------------------------------------------------------------------------------------------------------
def lz_einstellungen(d):
    return _einst(d, "laufzeit_einstellungen", LZ_STANDARD)


def laufzeiten(d):
    x = d.get("laufzeiten")
    if not isinstance(x, dict):
        x = {}
        d["laufzeiten"] = x
    return x


def zugang_gesperrt(d):
    x = d.get("zugang_gesperrt")
    if not isinstance(x, dict):
        x = {}
        d["zugang_gesperrt"] = x
    return x


def _k(kz, p):
    return f"{kz}-{int(p)}"


def _tarif(d, name):
    return next((t for t in tarife_pruefen(d["tarife"]) if t["name"] == name), None)


def plus_laufzeit(start, n, einheit):
    """Zeitpunkt (Sekunden) nach n Stunden/Tagen/Wochen/Monaten – Monate kalendergenau (31.01. + 1 Monat = 28./29.02.)"""
    if einheit == "stunden":
        return start + n * 3600
    if einheit == "tage":
        return start + n * 86400
    if einheit == "wochen":
        return start + n * 7 * 86400
    t = _dt.datetime.fromtimestamp(start)
    m = t.month - 1 + n
    j, m = t.year + m // 12, m % 12 + 1
    return t.replace(year=j, month=m, day=min(t.day, calendar.monthrange(j, m)[1])).timestamp()


def _zeit(ts):
    return time.strftime("%d.%m.%Y %H:%M", time.localtime(ts)) if ts else ""


def _lz_ereignis_daten(d, kz, p, e=None):
    e = e or laufzeiten(d).get(_k(kz, p)) or {}
    t = _tarif(d, e.get("tarif")) if e.get("tarif") else None
    try:
        name = (kalk_sparten(d).get(kz) or {}).get("name") or kz
    except Fehler:
        name = kz
    return {"sparte": kz, "sparte_name": name, "parzelle": int(p), "tarif": e.get("tarif", ""),
            "laufzeit": laufzeit_text(t["laufzeit"], t["laufzeit_einheit"]) if t else "", "laufzeit_start": _zeit(e.get("start")),
            "laufzeit_ende": _zeit(e.get("ende"))}


def laufzeit_starten(d, kz, p, tarif, ab=None, quelle=""):
    """neue Laufzeit für eine Parzelle; gibt den Eintrag zurück (oder None bei Tarif ohne Laufzeit)"""
    t = _tarif(d, tarif)
    k = _k(kz, p)
    if not t or not t.get("laufzeit"):
        laufzeiten(d).pop(k, None)
        return None
    start = ab or time.time()
    e = {"sparte": kz, "parzelle": int(p), "tarif": tarif, "start": start, "ende": plus_laufzeit(start, t["laufzeit"], t["laufzeit_einheit"]),
         "status": "aktiv", "erinnert": False, "quelle": text_einzeilig(quelle or "", 80), "seit": time.strftime("%Y-%m-%d %H:%M")}
    laufzeiten(d)[k] = e
    return e


# ---- Gateway: Zugang sperren / freigeben ------------------------------------------------------------------------------
def _parzellen_netz(d, kz, p):
    try:
        plan = plan_aktiv(d)
        n = next((n for n in plan["netze"] if n["sparte"] == kz and str(n.get("parzelle", "")) == str(int(p))), None)
        if n:
            return n["name"]
    except Fehler:
        pass
    return NETZ_PARZELLE.format(kz=kz, p=int(p))


def zugang_am_gateway(d, kz, p, freigeben, ausfuehren=True):
    """PPSK-Eintrag der Parzelle im Pächter-WLAN entfernen (sperren) oder wieder eintragen (freigeben).
    Gibt (geaendert: bool, text) zurück; wirft Fehler, wenn das Gateway nicht passt."""
    ssid = wlan_ssid(d, kz)
    netz = _parzellen_netz(d, kz, p)
    g = Gateway(d)
    nid = next((n.get("_id") for n in g.legacy("GET", "rest/networkconf") if n.get("name") == netz), None)
    if not nid:
        raise Fehler(f"Netz „{netz}“ gibt es am Gateway nicht – Parzelle {p} hat dort noch keinen Zugang.")
    wlan = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("name") == ssid), None)
    if not wlan:
        raise Fehler(f"WLAN „{ssid}“ nicht am Gateway gefunden (Einrichten → Schritt 2).")
    alt = list(wlan.get("private_preshared_keys") or [])
    hat = [x for x in alt if x.get("networkconf_id") == nid]
    if freigeben:
        z = next((z for z in lese_ppsk(kz) if str(z.get("Parzelle")) == str(int(p))), None)
        pw = (z or {}).get("Passwort", "")
        if not pw:
            raise Fehler(f"Für Parzelle {p} ist kein WLAN-Passwort gespeichert (Einrichten → Schritt 3).")
        if [x.get("password") for x in hat] == [pw]:
            return False, f"Parzelle {p} ist am Gateway schon freigegeben."
        neu = [x for x in alt if x.get("networkconf_id") != nid] + [{"password": pw, "networkconf_id": nid}]
        if sum(1 for x in neu if x.get("password") == pw) > 1:
            raise Fehler(f"Das Passwort von Parzelle {p} ist im WLAN schon einer anderen Parzelle zugeordnet – bitte unter Einrichten prüfen.")
        text = f"Parzelle {p}: Zugang im WLAN „{ssid}“ wieder freigegeben"
    else:
        if not hat:
            return False, f"Parzelle {p} ist am Gateway schon gesperrt."
        neu = [x for x in alt if x.get("networkconf_id") != nid]
        text = f"Parzelle {p}: Zugang im WLAN „{ssid}“ gesperrt (Passwort bleibt gespeichert)"
    if not ausfuehren:
        return True, "Vorschau – " + text + ". Alle anderen Einträge bleiben unverändert."
    ok = _ppsk_schreiben_und_pruefen(g, wlan, ssid, neu)
    if not ok:
        raise Fehler(f"{text} – beim Nachlesen nicht bestätigt, bitte in der UniFi-Oberfläche prüfen.")
    return True, text


def _zugang_setzen(d, kz, p, freigeben, grund, wer):
    """führt die Gateway-Änderung aus und merkt sich den Zustand; gibt den Text zurück"""
    k = _k(kz, p)
    geaendert, text = zugang_am_gateway(d, kz, p, freigeben)
    if freigeben:
        zugang_gesperrt(d).pop(k, None)
    else:
        zugang_gesperrt(d)[k] = {"sparte": kz, "parzelle": int(p), "seit": time.time(), "grund": grund, "wer": wer}
    e = laufzeiten(d).get(k)
    if e:
        e.pop("fehler", None)
        e.pop("versuch", None)
    speichere(d)
    if geaendert:
        journal(f"{text} – {('automatisch: ' if wer == 'Zeitplan' else '')}{grund} ({wer})")
        ereignis("zugang_freigegeben" if freigeben else "zugang_gesperrt", {**_lz_ereignis_daten(d, kz, p), "quelle": wer}, d)
    return text


# ---- Ereignisse aus den Buchungen -------------------------------------------------------------------------------------
def _ereignis(typ, daten, d):
    if typ not in ("buchung", "kuendigung") or d is None or not str(daten.get("parzelle") or "").isdigit():
        return
    kz, p = str(daten.get("sparte") or ""), int(daten["parzelle"])
    k = _k(kz, p)
    if typ == "buchung":
        e = laufzeit_starten(d, kz, p, daten.get("tarif"), quelle=str(daten.get("quelle") or ""))
        if e:
            journal(f"Laufzeit gestartet: {kz} Parzelle {p}, {daten.get('tarif')} bis {_zeit(e['ende'])}")
    else:
        laufzeiten(d).pop(k, None)
    speichere(d)
    # neu gebucht und vorher wegen Laufzeit gesperrt → im nächsten Zeitplan-Lauf freigeben (oder als offen anzeigen)


EREIGNIS_EMPFAENGER.insert(0, _ereignis)


def _verlaengern(d, kz, p, anzahl=1, wer=""):
    k = _k(kz, p)
    tarif = ((d.get("buchungen") or {}).get(kz) or {}).get(str(int(p)), "")
    if not tarif:
        raise Fehler(f"{kz} Parzelle {p} hat keinen Tarif gebucht.")
    t = _tarif(d, tarif)
    if not t or not t.get("laufzeit"):
        raise Fehler(f"Tarif „{tarif}“ hat keine Laufzeit.")
    try:
        anzahl = int(anzahl or 1)
    except (TypeError, ValueError):
        raise Fehler("Anzahl muss eine Zahl sein.")
    if not 1 <= anzahl <= 120:
        raise Fehler("Anzahl 1–120.")
    e = laufzeiten(d).get(k)
    jetzt = time.time()
    ab = e["ende"] if e and e.get("status") == "aktiv" and e.get("ende", 0) > jetzt and e.get("tarif") == tarif else jetzt
    ende = ab
    for _ in range(anzahl):
        ende = plus_laufzeit(ende, t["laufzeit"], t["laufzeit_einheit"])
    start = e["start"] if e and ab != jetzt else jetzt
    laufzeiten(d)[k] = {"sparte": kz, "parzelle": int(p), "tarif": tarif, "start": start, "ende": ende, "status": "aktiv", "erinnert": False,
                        "quelle": text_einzeilig(wer, 80), "seit": time.strftime("%Y-%m-%d %H:%M")}
    speichere(d)
    journal(f"Laufzeit verlängert: {kz} Parzelle {p}, {tarif} bis {_zeit(ende)} ({wer})")
    ereignis("laufzeit_verlaengert", {**_lz_ereignis_daten(d, kz, p), "quelle": wer}, d)
    return laufzeiten(d)[k]


def _aktion_verlaengern(d, daten, aktion, werte, probe, regel):
    kz, p = str(daten.get("sparte") or ""), daten.get("parzelle")
    if not kz or not str(p or "").isdigit():
        raise Fehler("Sparte und Parzelle fehlen im Ereignis.")
    if probe:
        return f"(Probe) {kz} Parzelle {p}: Laufzeit würde verlängert"
    e = _verlaengern(d, kz, p, 1, f"Automation „{regel}“")
    return f"{kz} Parzelle {p}: Laufzeit bis {_zeit(e['ende'])}"


AKTION_ERWEITERUNG["laufzeit_verlaengern"] = _aktion_verlaengern


# ---- Zeitplan: jede Minute --------------------------------------------------------------------------------------------
def laufzeiten_pruefen(d, jetzt=None):
    """Erinnerungen, Ablauf und – wenn eingeschaltet – Sperren/Freigeben am Gateway. Gibt Protokollzeilen zurück."""
    jetzt = jetzt or time.time()
    e_ = lz_einstellungen(d)
    log, geaendert = [], False
    lz, gesp = laufzeiten(d), zugang_gesperrt(d)
    buch = d.get("buchungen") or {}
    for k, e in list(lz.items()):
        if not isinstance(e, dict):
            lz.pop(k); geaendert = True
            continue
        if e.get("status") == "aktiv":
            if e_["erinnerung_stunden"] and not e.get("erinnert") and e["ende"] - jetzt <= e_["erinnerung_stunden"] * 3600 and e["ende"] > jetzt:
                e["erinnert"] = True; geaendert = True
                ereignis("laufzeit_erinnerung", {**_lz_ereignis_daten(d, e["sparte"], e["parzelle"], e), "quelle": "Zeitplan"}, d)
            if e["ende"] <= jetzt:
                e["status"] = "abgelaufen"; e["abgelaufen"] = jetzt; geaendert = True
                journal(f"Laufzeit abgelaufen: {e['sparte']} Parzelle {e['parzelle']} ({e.get('tarif')}) am {_zeit(e['ende'])}")
                log.append(f"Laufzeit abgelaufen: {e['sparte']} Parzelle {e['parzelle']}")
                ereignis("laufzeit_ende", {**_lz_ereignis_daten(d, e["sparte"], e["parzelle"], e), "quelle": "Zeitplan"}, d)
    if geaendert:
        speichere(d)
    if not e_["gateway_auto"]:
        return log
    # Soll-Zustand am Gateway herstellen (nur Einträge mit Grund „Laufzeit“ – von Hand gesperrte bleiben gesperrt)
    for k, e in list(lz.items()):
        if e.get("status") == "abgelaufen" and k not in gesp and jetzt - float(e.get("versuch") or 0) >= _LZ_WIEDERHOLEN:
            try:
                log.append("✔ " + _zugang_setzen(d, e["sparte"], e["parzelle"], False, "Laufzeit abgelaufen", "Zeitplan"))
                if e_["buchung_entfernen"]:
                    akt_buchungen_speichern(d, e["sparte"], {str(e["parzelle"]): ""})
            except Exception as x:
                e["versuch"], e["fehler"] = jetzt, text_einzeilig(str(x), 300)
                speichere(d)
                log.append(f"⚠ {e['sparte']} Parzelle {e['parzelle']}: Sperren fehlgeschlagen – {x}")
    for k, g in list(gesp.items()):
        if g.get("grund") != "Laufzeit abgelaufen":
            continue
        e = lz.get(k)
        gebucht = (buch.get(g["sparte"]) or {}).get(str(g["parzelle"]))
        frei = (e and e.get("status") == "aktiv") or (gebucht and not e and not (_tarif(d, gebucht) or {}).get("laufzeit"))
        if frei and jetzt - float(g.get("versuch") or 0) >= _LZ_WIEDERHOLEN:
            try:
                log.append("✔ " + _zugang_setzen(d, g["sparte"], g["parzelle"], True, "Laufzeit verlängert bzw. neu gebucht", "Zeitplan"))
            except Exception as x:
                g["versuch"], g["fehler"] = jetzt, text_einzeilig(str(x), 300)
                speichere(d)
                log.append(f"⚠ {g['sparte']} Parzelle {g['parzelle']}: Freigeben fehlgeschlagen – {x}")
    return log


def _zeitplan_aufgabe(jetzt):
    if os.environ.get("SPARTENET_ZEITPLAN", "1") == "0":
        return
    d = lade()
    if not d.get("laufzeiten") and not d.get("zugang_gesperrt"):
        return
    with SCHREIB_SPERRE:
        laufzeiten_pruefen(lade(), jetzt)


ZEITPLAN_AUFGABEN.append(_zeitplan_aufgabe)


# ---- Oberfläche / API -------------------------------------------------------------------------------------------------
def _zustand(d, k, e, jetzt):
    g = zugang_gesperrt(d).get(k)
    if e and e.get("status") == "aktiv":
        rest = e["ende"] - jetzt
        if g:
            return "offen_frei", "läuft – am Gateway noch gesperrt" + (" (von Hand)" if g.get("grund") != "Laufzeit abgelaufen" else ""), rest
        return "aktiv", "läuft", rest
    if e and e.get("status") == "ausnahme":
        return ("gesperrt", "abgelaufen – gesperrt", 0) if g else ("ausnahme", "abgelaufen – von Hand freigegeben", 0)
    if e:
        return ("gesperrt", "abgelaufen – gesperrt", 0) if g else ("offen_sperren", "abgelaufen – am Gateway noch frei", 0)
    return ("gesperrt", "gesperrt (" + (g.get("grund") or "") + ")", 0) if g else ("", "", 0)


def _rest_text(sek):
    if sek <= 0:
        return ""
    if sek < 3600:
        return f"noch {int(sek // 60)} Min."
    if sek < 2 * 86400:
        return f"noch {int(sek // 3600)} Std."
    return f"noch {int(sek // 86400)} Tage"


def akt_laufzeiten(d, erlaubt=None, log=None):
    jetzt = time.time()
    lz, gesp = laufzeiten(d), zugang_gesperrt(d)
    tarife_lz = {t["name"]: t for t in tarife_pruefen(d["tarife"]) if t.get("laufzeit")}
    zeilen = []
    for k in sorted(set(lz) | set(gesp), key=lambda k: (k.rsplit("-", 1)[0], int(k.rsplit("-", 1)[1]))):
        e, g = lz.get(k), gesp.get(k)
        x = e or g
        if erlaubt is not None and x.get("sparte") not in erlaubt:
            continue
        code, text, rest = _zustand(d, k, e, jetzt)
        zeilen.append({"sparte": x["sparte"], "parzelle": x["parzelle"], "tarif": (e or {}).get("tarif", ""), "start": _zeit((e or {}).get("start")),
                       "ende": _zeit((e or {}).get("ende")), "ende_ts": (e or {}).get("ende", 0), "rest": _rest_text(rest), "zustand": code, "text": text,
                       "gesperrt": bool(g), "grund": (g or {}).get("grund", ""), "fehler": (e or {}).get("fehler") or (g or {}).get("fehler") or ""})
    zeilen.sort(key=lambda z: ({"offen_sperren": 0, "offen_frei": 1, "aktiv": 2, "ausnahme": 3, "gesperrt": 4}.get(z["zustand"], 4), z["ende_ts"] or 9e12))
    ohne = [{"sparte": kz, "parzelle": int(p), "tarif": t} for kz, b in (d.get("buchungen") or {}).items() for p, t in b.items()
            if t in tarife_lz and _k(kz, p) not in lz and (erlaubt is None or kz in erlaubt)]
    zahl = Counter(z["zustand"] for z in zeilen)
    e_ = lz_einstellungen(d)
    return {"zeilen": zeilen, "ohne_laufzeit": ohne[:500], "einstellungen": e_, "tarife": [{"name": t["name"], "laufzeit": laufzeit_text(t["laufzeit"], t["laufzeit_einheit"])}
                                                                                         for t in tarife_lz.values()],
            "log": (log or []) + [f"{zahl['aktiv']} laufend · {zahl['gesperrt']} gesperrt · {zahl['offen_sperren'] + zahl['offen_frei']} am Gateway offen"
                                  + (f" · {len(ohne)} gebuchte Parzelle(n) mit Laufzeit-Tarif ohne Startzeit" if ohne else "")
                                  + (" · Gateway: automatisch" if e_["gateway_auto"] else " · Gateway: nur von Hand")]}


def _parzelle(b, erlaubt):
    kz = str(b.get("sparte") or "").upper()
    if erlaubt is not None and kz not in erlaubt:
        raise Fehler("Ihr Konto darf nur Parzellen der eigenen Sparten bearbeiten.")
    if not kz or not str(b.get("parzelle") or "").isdigit():
        raise Fehler("Sparte und Parzelle angeben.")
    return kz, int(b["parzelle"])


def akt_laufzeit_verlaengern(d, b, ich, erlaubt=None):
    kz, p = _parzelle(b, erlaubt)
    e = _verlaengern(d, kz, p, b.get("anzahl", 1), ich)
    hinweis = ""
    if _k(kz, p) in zugang_gesperrt(d):
        hinweis = (" Der Zugang wird im nächsten Zeitplan-Lauf (innerhalb einer Minute) am Gateway freigegeben." if lz_einstellungen(d)["gateway_auto"]
                   and zugang_gesperrt(d)[_k(kz, p)].get("grund") == "Laufzeit abgelaufen" else " Der Zugang ist am Gateway noch gesperrt – bitte „Freigeben“.")
    return akt_laufzeiten(d, erlaubt, [f"✔ {kz} Parzelle {p}: Laufzeit bis {_zeit(e['ende'])}.{hinweis}"])


def akt_laufzeit_starten(d, b, ich, erlaubt=None):
    """Laufzeit für schon gebuchte Parzellen starten (z. B. nachdem einem Tarif eine Laufzeit gegeben wurde)"""
    r = akt_laufzeiten(d, erlaubt)
    wahl = r["ohne_laufzeit"]
    if b.get("sparte"):
        kz, p = _parzelle(b, erlaubt)
        wahl = [x for x in wahl if x["sparte"] == kz and x["parzelle"] == p]
    for x in wahl:
        laufzeit_starten(d, x["sparte"], x["parzelle"], x["tarif"], quelle=ich)
    speichere(d)
    journal(f"Laufzeit gestartet für {len(wahl)} gebuchte Parzelle(n) durch {ich}")
    return akt_laufzeiten(d, erlaubt, [f"✔ Laufzeit für {len(wahl)} Parzelle(n) ab jetzt gestartet."])


def akt_zugang(d, b, ich, erlaubt=None):
    """Zugang einer Parzelle von Hand sperren oder freigeben – ohne „ausfuehren“ nur Vorschau (fragt das Gateway, ändert nichts)"""
    kz, p = _parzelle(b, erlaubt)
    aktion = b.get("aktion")
    if aktion not in ("sperren", "freigeben"):
        raise Fehler("Aktion: sperren oder freigeben.")
    if not b.get("ausfuehren"):
        _, text = zugang_am_gateway(d, kz, p, aktion == "freigeben", ausfuehren=False)
        return akt_laufzeiten(d, erlaubt, [text])
    e = laufzeiten(d).get(_k(kz, p))
    grund = ("Laufzeit abgelaufen" if e and e.get("status") in ("abgelaufen", "ausnahme") else "von Hand") if aktion == "sperren" else "von Hand"
    text = _zugang_setzen(d, kz, p, aktion == "freigeben", grund, ich)
    if e and aktion == "freigeben" and e.get("status") == "abgelaufen":
        e["status"] = "ausnahme"          # trotz Ablauf von Hand freigegeben – der Zeitplan sperrt nicht erneut (bis zur nächsten Laufzeit)
    elif e and aktion == "sperren" and e.get("status") == "ausnahme":
        e["status"] = "abgelaufen"
    speichere(d)
    return akt_laufzeiten(d, erlaubt, ["✔ " + text])


def akt_laufzeit_einstellungen(d, b, ich):
    e = lz_einstellungen(d)
    if "gateway_auto" in b:
        e["gateway_auto"] = bool(b["gateway_auto"])
    if "buchung_entfernen" in b:
        e["buchung_entfernen"] = bool(b["buchung_entfernen"])
    if "erinnerung_stunden" in b:
        try:
            e["erinnerung_stunden"] = max(0, min(24 * 60, int(b["erinnerung_stunden"] or 0)))
        except (TypeError, ValueError):
            raise Fehler("Erinnerung in Stunden angeben.")
    alt = lz_einstellungen(d)
    d["laufzeit_einstellungen"] = e
    speichere(d)
    if alt["gateway_auto"] != e["gateway_auto"]:
        journal(f"Laufzeit: automatisches Sperren/Freigeben am Gateway {'EINGESCHALTET' if e['gateway_auto'] else 'ausgeschaltet'} durch {ich}")
    log = ["✔ Gespeichert."]
    if b.get("jetzt"):
        log += laufzeiten_pruefen(d) or ["Geprüft – nichts zu tun."]
    return akt_laufzeiten(d, None, log)


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

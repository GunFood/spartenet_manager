"""SparteNet Manager – Anfragen (Tickets): Störungen, Fragen zu Buchung oder Rechnung … mit Zuständigkeit, Status und Verlauf

Tickets kommen von Hand, über die API (z. B. Kontaktformular der Webseite) oder später per E-Mail-Weiterleitung herein.
Jedes Ticket hat eine Nummer (T-0001), Kategorie, Priorität, Status, zuständigen Benutzer und einen Verlauf.
Antworten an den Kontakt gehen per E-Mail (mit Layout). Ereignisse für Automationen: ticket_neu, ticket_zugewiesen, ticket_erledigt.
Konten mit Sparten-Beschränkung sehen nur Tickets ihrer Sparten und Tickets, die ihnen zugewiesen sind.
"""
from .mitglieder import *  # noqa: F401,F403 – alle Namen der vorherigen Module

T_STATUS = {"neu": "neu", "bearbeitung": "in Bearbeitung", "wartet": "wartet auf Rückmeldung", "erledigt": "erledigt"}
T_PRIO = {"niedrig": "niedrig", "normal": "normal", "hoch": "hoch", "dringend": "dringend"}
T_KATEGORIEN = ["Störung / WLAN geht nicht", "Buchung / Tarif", "Rechnung / Zahlung", "Zugangsdaten / Passwort", "Kündigung", "Sonstiges"]


def tickets_daten(d):
    t = d.get("tickets") if isinstance(d.get("tickets"), dict) else {}
    if not isinstance(t.get("liste"), dict):
        t["liste"] = {}
    t.setdefault("zaehler", 0)
    d["tickets"] = t
    return t


def ticket_kategorien(d):
    k = tickets_daten(d).get("kategorien")
    return k if isinstance(k, list) and k else list(T_KATEGORIEN)


def _sichtbar(t, ich, erlaubt):
    return erlaubt is None or t.get("zustaendig") == ich or (t.get("sparte") and t["sparte"] in erlaubt)


def _ereignis_daten(t):
    k = t.get("kontakt") or {}
    return {"ticket": t["nr"], "betreff": t.get("betreff", ""), "nachricht": t.get("text", ""), "status": T_STATUS.get(t.get("status"), ""),
            "kategorie": t.get("kategorie", ""), "prioritaet": T_PRIO.get(t.get("prioritaet"), ""), "zustaendig": t.get("zustaendig", ""),
            "sparte": t.get("sparte", ""), "parzelle": t.get("parzelle", ""), "name": k.get("name", ""), "email": k.get("email", ""), "telefon": k.get("telefon", "")}


def _konten(d):
    namen = [ADMIN_NAME] + sorted(benutzer_liste(d))
    return [n for n in namen if n == ADMIN_NAME or konto_rechte(d, n)["art"] != "gesperrt"]


def _pruefen(d, roh, alt=None):
    t = dict(alt or {})
    if "betreff" in roh:
        t["betreff"] = text_einzeilig(roh.get("betreff") or "", 160).strip()
    if "text" in roh:
        t["text"] = str(roh.get("text") or "").replace("\r\n", "\n")[:10000]
    if not t.get("betreff"):
        raise Fehler("Bitte einen Betreff angeben.")
    if "kategorie" in roh:
        t["kategorie"] = text_einzeilig(roh.get("kategorie") or "", 60) or "Sonstiges"
    if "prioritaet" in roh:
        if roh.get("prioritaet") not in T_PRIO:
            raise Fehler("Priorität: niedrig, normal, hoch oder dringend.")
        t["prioritaet"] = roh["prioritaet"]
    if "status" in roh:
        if roh.get("status") not in T_STATUS:
            raise Fehler("Unbekannter Status.")
        t["status"] = roh["status"]
    if "zustaendig" in roh:
        z = str(roh.get("zustaendig") or "")
        if z and z not in _konten(d):
            raise Fehler(f"Benutzerkonto „{z}“ gibt es nicht (oder es ist gesperrt).")
        t["zustaendig"] = z
    if "sparte" in roh or "parzelle" in roh:
        kz = str(roh.get("sparte", t.get("sparte")) or "").upper()
        p = str(roh.get("parzelle", t.get("parzelle")) or "").strip()
        if kz and kz not in kalk_sparten(d):
            raise Fehler(f"Sparte „{kz}“ gibt es nicht.")
        if p and not p.isdigit():
            raise Fehler("Parzelle muss eine Nummer sein.")
        t["sparte"], t["parzelle"] = kz, (int(p) if p else "")
    k = dict(t.get("kontakt") or {})
    for f in ("name", "email", "telefon"):
        if f in roh:
            k[f] = text_einzeilig(roh.get(f) or "", 120).strip()
    if k.get("email") and not re.fullmatch(r"[^@\s,;<>]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,}", k["email"]):
        raise Fehler(f"E-Mail-Adresse „{k['email']}“ ist ungültig.")
    # Mitglied zuordnen: gleiche E-Mail oder gleiche Parzelle
    if not k.get("mitglied"):
        m = next((i for i, m in mitglieder(d).items() if k.get("email") and m.get("email") == k["email"].lower()), None) or \
            next((i for i, m in mitglieder(d).items() if t.get("parzelle") and m.get("sparte") == t.get("sparte") and str(m.get("parzelle")) == str(t["parzelle"])), None)
        if m:
            mm = mitglieder(d)[m]
            k["mitglied"] = m
            k.setdefault("name", f"{mm.get('vorname', '')} {mm.get('nachname', '')}".strip())
            if not k.get("name"):
                k["name"] = f"{mm.get('vorname', '')} {mm.get('nachname', '')}".strip()
            k["email"] = k.get("email") or mm.get("email", "")
            k["telefon"] = k.get("telefon") or mm.get("telefon", "")
            if not t.get("sparte") and mm.get("sparte"):
                t["sparte"], t["parzelle"] = mm["sparte"], mm.get("parzelle", "")
    t["kontakt"] = k
    return t


def _verlauf(t, wer, art, text):
    t.setdefault("verlauf", []).append({"zeit": time.strftime("%Y-%m-%d %H:%M"), "wer": wer, "art": art, "text": str(text)[:10000]})
    t["verlauf"] = t["verlauf"][-300:]
    t["geaendert"] = time.strftime("%Y-%m-%d %H:%M")


def ticket_anlegen(d, roh, wer, quelle):
    tk = tickets_daten(d)
    if len(tk["liste"]) >= 50000:
        raise Fehler("Zu viele Tickets – bitte erledigte archivieren.")
    t = _pruefen(d, {"kategorie": "Sonstiges", "prioritaet": "normal", "status": "neu", "zustaendig": "", **roh})
    tk["zaehler"] = int(tk["zaehler"]) + 1
    t.update(nr=f"T-{tk['zaehler']:04d}", erstellt=time.strftime("%Y-%m-%d %H:%M"), quelle=quelle, verlauf=[])
    _verlauf(t, wer, "angelegt", f"Ticket angelegt ({quelle})")
    tid = secrets.token_hex(6)
    tk["liste"][tid] = t
    speichere(d)
    journal(f"Ticket {t['nr']} angelegt: {t['betreff'][:60]} ({quelle})")
    ereignis("ticket_neu", _ereignis_daten(t), d)
    if t.get("zustaendig"):
        ereignis("ticket_zugewiesen", _ereignis_daten(t), d)
    return tid, t


def _zeile(t, tid):
    return {"id": tid, **{k: t.get(k, "") for k in ("nr", "betreff", "kategorie", "prioritaet", "status", "zustaendig", "sparte", "parzelle", "erstellt", "geaendert", "quelle")},
            "kontakt": t.get("kontakt") or {}, "antworten": sum(1 for v in t.get("verlauf") or [] if v["art"] in ("kommentar", "antwort"))}


def akt_tickets(d, q, ich, erlaubt=None):
    tk = tickets_daten(d)
    f_status = q.get("status", ["offen"])[0]
    f_wer = q.get("zustaendig", [""])[0]
    such = q.get("q", [""])[0].strip().lower()
    zeilen = []
    for tid, t in tk["liste"].items():
        if not _sichtbar(t, ich, erlaubt):
            continue
        if f_status == "offen" and t.get("status") == "erledigt" or f_status not in ("offen", "alle") and t.get("status") != f_status:
            continue
        if f_wer == "ich" and t.get("zustaendig") != ich or f_wer == "niemand" and t.get("zustaendig"):
            continue
        if such and such not in " ".join([t.get("nr", ""), t.get("betreff", ""), t.get("text", ""), json.dumps(t.get("kontakt") or {}, ensure_ascii=False),
                                           str(t.get("sparte", "")), str(t.get("parzelle", ""))]).lower():
            continue
        zeilen.append(_zeile(t, tid))
    rang = {"dringend": 0, "hoch": 1, "normal": 2, "niedrig": 3}
    zeilen.sort(key=lambda z: (z["status"] == "erledigt", rang.get(z["prioritaet"], 2), z["erstellt"]), reverse=False)
    offen = sum(1 for t in tk["liste"].values() if t.get("status") != "erledigt" and _sichtbar(t, ich, erlaubt))
    meine = sum(1 for t in tk["liste"].values() if t.get("status") != "erledigt" and t.get("zustaendig") == ich)
    return {"zeilen": zeilen, "status": T_STATUS, "prioritaeten": T_PRIO, "kategorien": ticket_kategorien(d), "konten": _konten(d),
            "offen": offen, "meine": meine, "log": [f"{len(zeilen)} Ticket(s) angezeigt · {offen} offen · {meine} davon Ihnen zugewiesen"]}


def _holen(d, tid, ich, erlaubt):
    t = tickets_daten(d)["liste"].get(str(tid or ""))
    if not t or not _sichtbar(t, ich, erlaubt):
        raise Fehler("Ticket nicht gefunden.")
    return t


def akt_ticket(d, q, ich, erlaubt=None):
    tid = q.get("id", [""])[0]
    t = _holen(d, tid, ich, erlaubt)
    return {"ticket": {**_zeile(t, tid), "text": t.get("text", ""), "verlauf": t.get("verlauf") or []}, "log": []}


def akt_ticket_speichern(d, b, ich, erlaubt=None):
    roh = b.get("ticket") or {}
    tid = str(roh.get("id") or "")
    if erlaubt is not None and roh.get("sparte") is not None and str(roh.get("sparte") or "").upper() not in erlaubt:
        raise Fehler("Ihr Konto darf nur Tickets der eigenen Sparten anlegen.")
    if not tid:
        tid, t = ticket_anlegen(d, {k: v for k, v in roh.items() if k != "id"}, ich, ich)
        r = akt_ticket(d, {"id": [tid]}, ich, erlaubt)
        r["log"] = [f"✔ Ticket {t['nr']} angelegt."]
        return r
    t = _holen(d, tid, ich, erlaubt)
    vorher = {k: t.get(k) for k in ("status", "zustaendig", "prioritaet", "kategorie")}
    neu = _pruefen(d, {k: v for k, v in roh.items() if k != "id"}, t)
    t.clear(); t.update(neu)
    aend = []
    if vorher["status"] != t.get("status"):
        aend.append(f"Status: {T_STATUS.get(vorher['status'], vorher['status'])} → {T_STATUS[t['status']]}")
    if vorher["zustaendig"] != t.get("zustaendig"):
        aend.append(f"Zuständig: {vorher['zustaendig'] or 'niemand'} → {t.get('zustaendig') or 'niemand'}")
    if vorher["prioritaet"] != t.get("prioritaet"):
        aend.append(f"Priorität: {vorher['prioritaet']} → {t['prioritaet']}")
    if vorher["kategorie"] != t.get("kategorie"):
        aend.append(f"Kategorie: {t['kategorie']}")
    if aend:
        _verlauf(t, ich, "aenderung", " · ".join(aend))
    else:
        t["geaendert"] = time.strftime("%Y-%m-%d %H:%M")
    speichere(d)
    if vorher["zustaendig"] != t.get("zustaendig") and t.get("zustaendig"):
        ereignis("ticket_zugewiesen", _ereignis_daten(t), d)
    if vorher["status"] != "erledigt" and t.get("status") == "erledigt":
        ereignis("ticket_erledigt", _ereignis_daten(t), d)
    journal(f"Ticket {t['nr']} geändert durch {ich}" + (": " + " · ".join(aend) if aend else ""))
    r = akt_ticket(d, {"id": [tid]}, ich, erlaubt)
    r["log"] = [f"✔ Ticket {t['nr']} gespeichert."]
    return r


def akt_ticket_kommentar(d, b, ich, erlaubt=None):
    """interne Notiz oder Antwort an den Kontakt (per E-Mail mit Layout, optional mit E-Mail-Vorlage)"""
    tid = str(b.get("id") or "")
    t = _holen(d, tid, ich, erlaubt)
    html = html_bereinigen(b.get("html") or "") if b.get("html") else text_zu_html(b.get("text") or "")
    if b.get("vorlage"):
        v = next((x for x in email_vorlagen(d) if x["id"] == b["vorlage"]), None)
        if not v:
            raise Fehler("Vorlage nicht gefunden.")
        html = html or v["html"]
    if not html_zu_text(html).strip():
        raise Fehler("Bitte einen Text eingeben.")
    log = []
    if b.get("an_kontakt"):
        an = (t.get("kontakt") or {}).get("email")
        if not an:
            raise Fehler("Beim Ticket ist keine E-Mail-Adresse des Kontakts hinterlegt.")
        werte = _platzhalter_werte(_ereignis_daten(t), d)
        betreff = f"[{t['nr']}] {t.get('betreff', '')}"
        email_senden(d, an, betreff, None, _ersetzen(html, werte, html=True))
        _verlauf(t, ich, "antwort", f"E-Mail an {an}:\n" + html_zu_text(_ersetzen(html, werte, html=True)))
        log.append(f"✔ Antwort per E-Mail an {an} gesendet.")
        if t.get("status") == "neu":
            t["status"] = "wartet" if b.get("wartet") else "bearbeitung"
    else:
        _verlauf(t, ich, "kommentar", html_zu_text(html))
        log.append("✔ Notiz gespeichert.")
        if t.get("status") == "neu":
            t["status"] = "bearbeitung"
    speichere(d)
    r = akt_ticket(d, {"id": [tid]}, ich, erlaubt)
    r["log"] = log
    return r


def akt_ticket_loeschen(d, b, ich):
    tid = str(b.get("id") or "")
    t = tickets_daten(d)["liste"].pop(tid, None)
    if not t:
        raise Fehler("Ticket nicht gefunden.")
    speichere(d)
    journal(f"Ticket {t['nr']} gelöscht durch {ich}")
    return {"log": [f"✔ Ticket {t['nr']} gelöscht."]}


def akt_ticket_einstellungen(d, b, ich):
    tk = tickets_daten(d)
    k = [text_einzeilig(x, 60).strip() for x in (b.get("kategorien") or []) if str(x).strip()]
    if not k:
        raise Fehler("Mindestens eine Kategorie.")
    tk["kategorien"] = list(dict.fromkeys(k))[:30]
    speichere(d)
    journal(f"Ticket-Kategorien gespeichert durch {ich}")
    return {"kategorien": tk["kategorien"], "log": ["✔ Kategorien gespeichert."]}


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

"""SparteNet Manager – Anfragen (Tickets): Störungen, Fragen zu Buchung oder Rechnung … mit Zuständigkeit, Status und Verlauf

Tickets kommen von Hand, über die API (z. B. Kontaktformular der Webseite) oder später per E-Mail-Weiterleitung herein.
Jedes Ticket hat eine Nummer (T-0001), Kategorie, Priorität, Status, zuständigen Benutzer und einen Verlauf.
Antworten an den Kontakt gehen per E-Mail (mit Layout). Ereignisse für Automationen: ticket_neu, ticket_zugewiesen, ticket_erledigt, ticket_geschlossen.
„Geschlossen“ ist endgültig (mit Lösung, nur noch lesbar, „Wieder öffnen“ möglich); erledigte Tickets schließt der Zeitplan nach
einstellbaren Tagen automatisch. Tickets hängen am Mitglied (Kontakt „mitglied“) – so sieht man frühere Anfragen und die Akte.
Konten mit Sparten-Beschränkung sehen nur Tickets ihrer Sparten und Tickets, die ihnen zugewiesen sind.
"""
from .mitglieder import *  # noqa: F401,F403 – alle Namen der vorherigen Module

T_STATUS = {"neu": "neu", "bearbeitung": "in Bearbeitung", "wartet": "wartet auf Rückmeldung", "erledigt": "erledigt", "geschlossen": "geschlossen"}
T_ZU = ("erledigt", "geschlossen")       # nicht mehr offen
AUSLOESER["ticket_geschlossen"] = "Ticket abgeschlossen (mit Lösung)"


def ticket_offen(t):
    return t.get("status") not in T_ZU
T_PRIO = {"niedrig": "niedrig", "normal": "normal", "hoch": "hoch", "dringend": "dringend"}
T_KATEGORIEN = ["Störung / WLAN geht nicht", "Buchung / Tarif", "Rechnung / Zahlung", "Zugangsdaten / Passwort", "Kündigung", "Interessent", "Sonstiges"]


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


def parzelle_passt(t, m):
    """Ticket ohne Parzelle passt zu jedem Mitglied; mit Parzelle nur zu dem Mitglied genau dieser Sparte/Parzelle"""
    return not t.get("parzelle") or (m.get("sparte") == t.get("sparte") and str(m.get("parzelle") or "") == str(t.get("parzelle")))


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
        em = (k.get("email") or "").lower()
        alle_m = mitglieder(d).items()
        m = (next((i for i, m in alle_m if em and (m.get("email") or "").lower() == em and parzelle_passt(t, m)), None) or
             next((i for i, m in alle_m if t.get("parzelle") and parzelle_passt(t, m)), None))
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
        if f_status == "offen" and not ticket_offen(t) or f_status not in ("offen", "alle") and t.get("status") != f_status:
            continue
        if f_wer == "ich" and t.get("zustaendig") != ich or f_wer == "niemand" and t.get("zustaendig"):
            continue
        if such and such not in " ".join([t.get("nr", ""), t.get("betreff", ""), t.get("text", ""), json.dumps(t.get("kontakt") or {}, ensure_ascii=False),
                                           str(t.get("sparte", "")), str(t.get("parzelle", ""))]).lower():
            continue
        zeilen.append(_zeile(t, tid))
    rang = {"dringend": 0, "hoch": 1, "normal": 2, "niedrig": 3}
    zeilen.sort(key=lambda z: (z["status"] in T_ZU, rang.get(z["prioritaet"], 2), z["erstellt"]), reverse=False)
    offen = sum(1 for t in tk["liste"].values() if ticket_offen(t) and _sichtbar(t, ich, erlaubt))
    meine = sum(1 for t in tk["liste"].values() if ticket_offen(t) and t.get("zustaendig") == ich)
    return {"zeilen": zeilen, "status": T_STATUS, "prioritaeten": T_PRIO, "kategorien": ticket_kategorien(d), "konten": _konten(d),
            "offen": offen, "meine": meine, "einstellungen": ticket_einstellungen(d), "log": [f"{len(zeilen)} Ticket(s) angezeigt · {offen} offen · {meine} davon Ihnen zugewiesen"]}


def _holen(d, tid, ich, erlaubt):
    t = tickets_daten(d)["liste"].get(str(tid or ""))
    if not t or not _sichtbar(t, ich, erlaubt):
        raise Fehler("Ticket nicht gefunden.")
    return t


def ticket_mitglied_id(d, t):
    """Mitglied des Tickets: fest zugeordnet oder (ohne Zuordnung) gleiche E-Mail-Adresse"""
    k = t.get("kontakt") or {}
    if k.get("mitglied") in mitglieder(d):
        return k["mitglied"]
    em = (k.get("email") or "").strip().lower()
    if em and k.get("art", "mitglied") == "mitglied" and not k.get("geloest"):
        return next((i for i, m in mitglieder(d).items() if (m.get("email") or "").lower() == em and parzelle_passt(t, m)), None)
    return None


def mitglied_tickets(d, mid, ohne=None):
    """alle Tickets eines Mitglieds (fest zugeordnet oder gleiche E-Mail ohne andere Zuordnung), neueste zuerst"""
    m = mitglieder(d).get(mid) or {}
    em = (m.get("email") or "").lower()
    aus = []
    for i, t in tickets_daten(d)["liste"].items():
        if i == ohne:
            continue
        k = t.get("kontakt") or {}
        if k.get("mitglied") == mid or (not k.get("mitglied") and not k.get("geloest") and em and (k.get("email") or "").lower() == em and parzelle_passt(t, m)):
            aus.append((i, t))
    aus.sort(key=lambda x: x[1].get("erstellt", ""), reverse=True)
    return aus


def _frueher_zeile(i, t):
    return {"id": i, "nr": t.get("nr"), "betreff": t.get("betreff", ""), "status": t.get("status"), "erstellt": t.get("erstellt", ""),
            "geaendert": t.get("geaendert", ""), "kategorie": t.get("kategorie", ""), "loesung": t.get("loesung", "")}


def akt_ticket(d, q, ich, erlaubt=None):
    tid = q.get("id", [""])[0]
    t = _holen(d, tid, ich, erlaubt)
    mid = ticket_mitglied_id(d, t)
    m = mitglieder(d).get(mid) if mid else None
    if m and not (erlaubt is None or m.get("sparte") in erlaubt):
        m = None
    mitglied = None
    frueher = []
    if m:
        tarif = ((d.get("buchungen") or {}).get(m.get("sparte")) or {}).get(str(m.get("parzelle")), "")
        mitglied = {"id": mid, "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(), "sparte": m.get("sparte", ""), "parzelle": m.get("parzelle", ""),
                    "email": m.get("email", ""), "telefon": m.get("telefon", ""), "tarif": tarif, "fest": (t.get("kontakt") or {}).get("mitglied") == mid}
        frueher = [_frueher_zeile(i, x) for i, x in mitglied_tickets(d, mid, ohne=tid) if _sichtbar(x, ich, erlaubt)]
    elif (t.get("kontakt") or {}).get("email"):     # Nicht-Mitglieder: frühere Anfragen mit derselben E-Mail
        em = t["kontakt"]["email"].lower()
        frueher = [_frueher_zeile(i, x) for i, x in sorted(tickets_daten(d)["liste"].items(), key=lambda y: y[1].get("erstellt", ""), reverse=True)
                   if i != tid and (x.get("kontakt") or {}).get("email", "").lower() == em and _sichtbar(x, ich, erlaubt)]
    return {"ticket": {**_zeile(t, tid), "text": t.get("text", ""), "verlauf": t.get("verlauf") or [], "loesung": t.get("loesung", ""),
                       "geschlossen": t.get("geschlossen", ""), "bezug": t.get("bezug", ""), "antrag": t.get("antrag")},
            "mitglied": mitglied, "frueher": frueher[:50], "log": []}


def akt_ticket_mitglieder(d, q, erlaubt=None):
    """schlanke Mitgliederliste zum Zuordnen (nur Name, Sparte, Parzelle) – auch für Konten ohne Recht „Mitglieder“"""
    such = q.get("q", [""])[0].strip().lower()
    aus = []
    for i, m in mitglieder(d).items():
        if erlaubt is not None and m.get("sparte") not in erlaubt:
            continue
        name = f"{m.get('nachname', '')}, {m.get('vorname', '')}".strip(", ")
        if such and such not in f"{name} {m.get('sparte', '')} {m.get('parzelle', '')} {m.get('email', '')}".lower():
            continue
        aus.append({"id": i, "name": name, "sparte": m.get("sparte", ""), "parzelle": m.get("parzelle", "")})
    aus.sort(key=lambda x: (x["sparte"], int(x["parzelle"] or 0) if str(x["parzelle"]).isdigit() else 0, x["name"].lower()))
    return {"mitglieder": aus[:300], "log": []}


def akt_ticket_zuordnen(d, b, ich, erlaubt=None):
    tid = str(b.get("id") or "")
    t = _holen(d, tid, ich, erlaubt)
    mid = str(b.get("mitglied") or "")
    k = t.setdefault("kontakt", {})
    if mid:
        m = mitglieder(d).get(mid)
        if not m or (erlaubt is not None and m.get("sparte") not in erlaubt):
            raise Fehler("Mitglied nicht gefunden.")
        k.update(mitglied=mid, art="mitglied", zugeordnet=ich)
        k.pop("geloest", None)
        k["name"] = k.get("name") or f"{m.get('vorname', '')} {m.get('nachname', '')}".strip()
        k["email"] = k.get("email") or m.get("email", "")
        if not t.get("sparte") and m.get("sparte"):
            t["sparte"], t["parzelle"] = m["sparte"], m.get("parzelle", "")
        _verlauf(t, ich, "aenderung", f"Mitglied zugeordnet: {m.get('vorname', '')} {m.get('nachname', '')} ({m.get('sparte', '')} {m.get('parzelle', '')})".strip())
    else:
        k.pop("mitglied", None)
        k["geprueft"], k["geloest"] = False, True
        _verlauf(t, ich, "aenderung", "Zuordnung zum Mitglied gelöst")
    speichere(d)
    r = akt_ticket(d, {"id": [tid]}, ich, erlaubt)
    r["log"] = ["✔ Zuordnung gespeichert."]
    return r


def akt_ticket_schliessen(d, b, ich, erlaubt=None):
    """Ticket abschließen (mit Lösung, auf Wunsch E-Mail an den Kontakt) oder wieder öffnen"""
    tid = str(b.get("id") or "")
    t = _holen(d, tid, ich, erlaubt)
    if b.get("wieder_oeffnen"):
        if t.get("status") not in T_ZU:
            raise Fehler("Das Ticket ist schon offen.")
        t["status"] = "bearbeitung"
        t.pop("geschlossen", None)
        _verlauf(t, ich, "aenderung", "Wieder geöffnet" + (f": {text_einzeilig(b.get('grund'), 300)}" if b.get("grund") else ""))
        speichere(d)
        journal(f"Ticket {t['nr']} wieder geöffnet durch {ich}")
        r = akt_ticket(d, {"id": [tid]}, ich, erlaubt)
        r["log"] = [f"✔ Ticket {t['nr']} wieder geöffnet."]
        return r
    if t.get("status") == "geschlossen":
        raise Fehler("Das Ticket ist schon geschlossen.")
    loesung = str(b.get("loesung") or "").replace("\r", "").strip()[:3000]
    if not loesung:
        raise Fehler("Bitte kurz die Lösung bzw. den Abschluss beschreiben – so lässt sich später nachvollziehen, was getan wurde.")
    log = []
    if b.get("an_kontakt"):
        an = (t.get("kontakt") or {}).get("email")
        if not an:
            raise Fehler("Beim Ticket ist keine E-Mail-Adresse des Kontakts hinterlegt.")
        k = t.get("kontakt") or {}
        email_senden(d, an, f"[{t['nr']}] Ihre Anfrage ist abgeschlossen: {t.get('betreff', '')}", None,
                     f"<p>Hallo {html_mod.escape(k.get('vorname') or k.get('name') or '')},</p><p>Ihre Anfrage <b>{html_mod.escape(t['nr'])}</b> "
                     f"(„{html_mod.escape(t.get('betreff', ''))}“) ist abgeschlossen.</p>{text_zu_html(loesung)}"
                     "<p>Wenn noch etwas offen ist, antworten Sie einfach oder stellen Sie auf der Kontakt-Seite eine neue Anfrage.</p>", sparte=t.get("sparte") or None)
        log.append(f"✔ Abschluss per E-Mail an {an} gesendet.")
    war_offen = ticket_offen(t)
    t["status"], t["loesung"], t["geschlossen"] = "geschlossen", loesung, time.strftime("%Y-%m-%d %H:%M")
    _verlauf(t, ich, "abschluss", loesung + (f"\n(Kontakt per E-Mail informiert)" if b.get("an_kontakt") else ""))
    speichere(d)
    journal(f"Ticket {t['nr']} geschlossen durch {ich}")
    if war_offen:
        ereignis("ticket_erledigt", _ereignis_daten(t), d)
    ereignis("ticket_geschlossen", {**_ereignis_daten(t), "loesung": loesung}, d)
    r = akt_ticket(d, {"id": [tid]}, ich, erlaubt)
    r["log"] = [f"✔ Ticket {t['nr']} geschlossen."] + log
    return r


def tickets_auto_schliessen(d):
    """erledigte Tickets nach X Tagen ohne Änderung schließen (Einstellung „auto_schliessen_tage“, 0 = nie); gibt die Anzahl zurück"""
    tage = ticket_einstellungen(d)["auto_schliessen_tage"]
    if not tage:
        return 0
    grenze = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() - tage * 86400))
    n = 0
    for t in tickets_daten(d)["liste"].values():
        if t.get("status") == "erledigt" and (t.get("geaendert") or t.get("erstellt") or "") < grenze:
            t["status"], t["geschlossen"] = "geschlossen", time.strftime("%Y-%m-%d %H:%M")
            t.setdefault("loesung", "")
            _verlauf(t, "Zeitplan", "abschluss", f"Automatisch geschlossen ({tage} Tage nach „erledigt“ ohne Änderung)")
            n += 1
    if n:
        speichere(d)
        journal(f"{n} erledigte(s) Ticket(s) automatisch geschlossen")
    return n


T_EINST_STANDARD = {"auto_schliessen_tage": 14}


def ticket_einstellungen(d):
    tk = tickets_daten(d)
    e = dict(T_EINST_STANDARD)
    try:
        e["auto_schliessen_tage"] = max(0, min(365, int(tk.get("auto_schliessen_tage", e["auto_schliessen_tage"]))))
    except (TypeError, ValueError):
        pass
    return e


def _mitglied_neu(typ, daten, d):
    """neues Mitglied: frühere Tickets mit derselben E-Mail-Adresse (ohne Zuordnung) diesem Mitglied zuordnen"""
    if typ != "mitglied_neu" or d is None or not daten.get("email"):
        return
    em = str(daten["email"]).lower()
    mid = next((i for i, m in mitglieder(d).items() if (m.get("email") or "").lower() == em), None)
    if not mid:
        return
    n = 0
    for t in tickets_daten(d)["liste"].values():
        k = t.get("kontakt") or {}
        if not k.get("mitglied") and (k.get("email") or "").lower() == em and k.get("art", "mitglied") == "mitglied" and parzelle_passt(t, mitglieder(d)[mid]):
            k["mitglied"] = mid
            n += 1
    if n:
        speichere(d)
        journal(f"{n} frühere(s) Ticket(s) dem neuen Mitglied zugeordnet")


EREIGNIS_EMPFAENGER.append(_mitglied_neu)


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
    if t.get("status") == "geschlossen":
        raise Fehler("Das Ticket ist geschlossen – zum Ändern erst „Wieder öffnen“.")
    if roh.get("status") == "geschlossen":
        raise Fehler("Zum Schließen bitte „Abschließen“ verwenden (mit Lösung).")
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
    if t.get("status") == "geschlossen":
        raise Fehler("Das Ticket ist geschlossen – für weitere Antworten erst „Wieder öffnen“ (oder eine neue Anfrage anlegen).")
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
        email_senden(d, an, betreff, None, _ersetzen(html, werte, html=True), sparte=t.get("sparte") or None)
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
    if "kategorien" in b:
        k = [text_einzeilig(x, 60).strip() for x in (b.get("kategorien") or []) if str(x).strip()]
        if not k:
            raise Fehler("Mindestens eine Kategorie.")
        tk["kategorien"] = list(dict.fromkeys(k))[:30]
    if "auto_schliessen_tage" in b:
        try:
            tk["auto_schliessen_tage"] = max(0, min(365, int(b.get("auto_schliessen_tage") or 0)))
        except (TypeError, ValueError):
            raise Fehler("Tage als Zahl angeben (0 = nie).")
    speichere(d)
    journal(f"Ticket-Einstellungen gespeichert durch {ich}")
    return {"kategorien": ticket_kategorien(d), "einstellungen": ticket_einstellungen(d), "log": ["✔ Gespeichert."]}


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

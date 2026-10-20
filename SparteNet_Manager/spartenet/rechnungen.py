"""SparteNet Manager – Rechnungen und Zahlungsabgleich

Rechnungslauf je Jahr: für jede gebuchte Parzelle mit Mitglied eine Rechnung über den Jahrespreis des Tarifs (PDF mit GiroCode).
Versand per E-Mail mit PDF im Anhang. Kontoauszug als CSV: Zahlungen werden über die Rechnungsnummer im Verwendungszweck,
sonst über Betrag und Name zugeordnet – erst Vorschau, dann übernehmen. Jede übernommene Zahlung löst das Ereignis „zahlung“ aus.
Rechnungen werden nie gelöscht, nur storniert (Aufbewahrungspflicht).
"""
import csv

from .pdf import *  # noqa: F401,F403 – alle Namen der vorherigen Module

R_STATUS = {"offen": "offen", "teilweise": "teilweise bezahlt", "bezahlt": "bezahlt", "storniert": "storniert"}
R_EINST_STANDARD = {"firma": "SparteNet.de", "adresse": "", "email": "", "telefon": "", "steuernr": "", "ust_id": "", "kleinunternehmer": True,
                    "ust_satz": 19, "iban": "", "bic": "", "bank": "", "zahlungsziel": 14, "praefix": "RE",
                    "betreff": "WLAN-Nutzung {jahr}", "text_oben": "vielen Dank, dass Sie das SparteNet-WLAN nutzen. Wir berechnen Ihnen:",
                    "text_unten": "Bei Fragen erreichen Sie uns per E-Mail.",
                    "email_betreff": "Ihre Rechnung {rechnung}", "email_text": "<p>Hallo {vorname},</p><p>anbei Ihre Rechnung <b>{rechnung}</b> über {betrag} für Parzelle {parzelle}. Bitte überweisen Sie den Betrag bis {faellig}.</p><p>Viele Grüße<br>Ihr SparteNet-Team</p>"}
_IBAN_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")


def rechnung_einstellungen(d):
    e = dict(R_EINST_STANDARD)
    roh = d.get("rechnung_einstellungen") if isinstance(d.get("rechnung_einstellungen"), dict) else {}
    for k, std in R_EINST_STANDARD.items():
        if k in roh:
            e[k] = bool(roh[k]) if isinstance(std, bool) else (roh[k] if isinstance(std, (int, float)) else str(roh[k]))
    return e


def rechnungen_daten(d):
    r = d.get("rechnungen") if isinstance(d.get("rechnungen"), dict) else {}
    if not isinstance(r.get("liste"), dict):
        r["liste"] = {}
    if not isinstance(r.get("zaehler"), dict):
        r["zaehler"] = {}
    if not isinstance(r.get("importe"), list):
        r["importe"] = []
    d["rechnungen"] = r
    return r


def _mitglied_der_parzelle(d, kz, p):
    return next(((i, m) for i, m in mitglieder(d).items() if m.get("sparte") == kz and str(m.get("parzelle")) == str(p)), (None, None))


def _neue_nummer(d, jahr):
    r = rechnungen_daten(d)
    n = int(r["zaehler"].get(str(jahr), 0)) + 1
    r["zaehler"][str(jahr)] = n
    return f"{rechnung_einstellungen(d)['praefix']}-{jahr}-{n:04d}"


def _summen(e, brutto):
    brutto = round(float(brutto), 2)
    if e["kleinunternehmer"]:
        return brutto, 0.0, brutto
    netto = round(brutto / (1 + float(e["ust_satz"]) / 100), 2)
    return netto, round(brutto - netto, 2), brutto


# ---- Guthaben je Parzelle (Restguthaben aus einem Tarifwechsel) ------------------------------------------------------
def guthaben(d, kz, p):
    try:
        return round(float(((d.get("guthaben") or {}).get(f"{kz}-{int(p)}") or {}).get("betrag", 0)), 2)
    except (TypeError, ValueError):
        return 0.0


def guthaben_buchen(d, kz, p, betrag, text):
    """Guthaben gutschreiben (positiv) oder verbrauchen (negativ) – mit Verlauf; nie unter 0"""
    betrag = round(float(betrag), 2)
    if not betrag:
        return guthaben(d, kz, p)
    k = f"{kz}-{int(p)}"
    g = d.setdefault("guthaben", {}).setdefault(k, {"betrag": 0.0, "verlauf": []})
    g["betrag"] = max(0.0, round(float(g.get("betrag") or 0) + betrag, 2))
    g.setdefault("verlauf", []).append({"zeit": time.strftime("%Y-%m-%d %H:%M"), "betrag": betrag, "text": text_einzeilig(text, 200), "stand": g["betrag"]})
    del g["verlauf"][:-50]
    journal(f"Guthaben {kz} Parzelle {p}: {'+' if betrag > 0 else ''}{geld(betrag)} ({text}) – Stand {geld(g['betrag'])}")
    return g["betrag"]


def restwert(d, kz, p, jetzt=None):
    """Wert der noch nicht genutzten Laufzeit: Tarifpreis × verbleibende Zeit / gesamte Laufzeit (0 ohne aktive Laufzeit)"""
    e = (d.get("laufzeiten") or {}).get(f"{kz}-{int(p)}")
    jetzt = jetzt or time.time()
    if not isinstance(e, dict) or e.get("status") != "aktiv" or not e.get("ende") or e["ende"] <= jetzt or e["ende"] <= e.get("start", 0):
        return 0.0
    t = next((x for x in tarife_pruefen(d["tarife"]) if x["name"] == e.get("tarif")), None)
    if not t or not float(t.get("preis") or 0):
        return 0.0
    return round(float(t["preis"]) * (e["ende"] - jetzt) / (e["ende"] - e["start"]), 2)


def _guthaben_positionen(d, kz, p, summe):
    """negative Position „Restguthaben“ – höchstens bis zum Rechnungsbetrag"""
    g = min(guthaben(d, kz, p), round(summe, 2))
    return ([{"text": f"Abzüglich Guthaben (Restguthaben aus Tarifwechsel), Parzelle {p}", "menge": 1, "einzel": -g, "gesamt": -g}] if g > 0 else []), g


def rechnung_anlegen(d, kz, p, tarif, positionen, ich, jahr=None, notiz=""):
    """einzelne Rechnung für eine Parzelle anlegen (Positionen brutto); Betrag 0 gilt gleich als bezahlt"""
    e = rechnung_einstellungen(d)
    mid, m = _mitglied_der_parzelle(d, kz, p)
    if not m:
        raise Fehler(f"{kz} Parzelle {p} hat kein Mitglied – keine Rechnung möglich.")
    jahr = int(jahr or time.strftime("%Y"))
    summe = round(sum(float(x["gesamt"]) for x in positionen), 2)
    netto, ust, brutto = _summen(e, summe)
    r = rechnungen_daten(d)
    rid = secrets.token_hex(6)
    r["liste"][rid] = {"nr": _neue_nummer(d, jahr), "jahr": jahr, "datum": time.strftime("%Y-%m-%d"),
                       "faellig": time.strftime("%Y-%m-%d", time.localtime(time.time() + int(e["zahlungsziel"]) * 86400)), "mitglied": mid,
                       "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(), "email": m.get("email", ""), "sparte": kz,
                       "sparte_name": _sparten_kz(d).get(kz, kz), "parzelle": int(p), "tarif": tarif, "positionen": positionen,
                       "netto": netto, "ust": ust, "ust_satz": 0 if e["kleinunternehmer"] else e["ust_satz"], "brutto": brutto, "bezahlt": 0.0,
                       "status": "bezahlt" if brutto <= 0 else "offen", "zahlungen": [], "erstellt": time.strftime("%Y-%m-%d %H:%M"), "von": ich,
                       **({"notiz": notiz} if notiz else {})}
    speichere(d)
    journal(f"Rechnung {r['liste'][rid]['nr']} angelegt: {kz} Parzelle {p}, {geld(brutto)} ({ich})")
    return rid, r["liste"][rid]


def akt_rechnung_einstellungen(d, b, ich):
    e = rechnung_einstellungen(d)
    for k, std in R_EINST_STANDARD.items():
        if k not in b:
            continue
        v = b[k]
        if isinstance(std, bool):
            e[k] = bool(v)
        elif k in ("ust_satz", "zahlungsziel"):
            try:
                e[k] = max(0, min(100 if k == "ust_satz" else 365, float(str(v).replace(",", ".")) if k == "ust_satz" else int(v)))
            except (TypeError, ValueError):
                raise Fehler(f"{'Umsatzsteuersatz' if k == 'ust_satz' else 'Zahlungsziel'} muss eine Zahl sein.")
        elif k == "email_text":
            e[k] = html_bereinigen(v)
        elif k in ("adresse", "text_oben", "text_unten"):
            e[k] = str(v or "")[:1000]
        else:
            e[k] = text_einzeilig(v, 200).strip()
    e["iban"] = e["iban"].replace(" ", "").upper()
    if e["iban"] and not _IBAN_RE.match(e["iban"]):
        raise Fehler("IBAN ist ungültig.")
    if not re.fullmatch(r"[A-Za-z0-9-]{1,10}", e["praefix"] or ""):
        raise Fehler("Präfix der Rechnungsnummer: 1–10 Zeichen, Buchstaben, Ziffern, Bindestrich.")
    d["rechnung_einstellungen"] = e
    speichere(d)
    journal(f"Rechnungs-Einstellungen gespeichert durch {ich}")
    return {"einstellungen": e, "log": ["✔ Einstellungen gespeichert."]}


def _zeile(i, x):
    return {"id": i, **{k: x.get(k) for k in ("nr", "jahr", "datum", "faellig", "name", "email", "sparte", "parzelle", "tarif", "brutto", "bezahlt", "status", "versendet", "mitglied")},
            "offen_betrag": round(float(x.get("brutto", 0)) - float(x.get("bezahlt", 0)), 2) if x.get("status") != "storniert" else 0}


def akt_rechnungen(d, q, erlaubt=None):
    r = rechnungen_daten(d)
    jahr = q.get("jahr", [""])[0]
    status = q.get("status", [""])[0]
    zeilen = [_zeile(i, x) for i, x in r["liste"].items() if (not jahr or str(x.get("jahr")) == jahr) and (not status or x.get("status") == status)
              and (erlaubt is None or x.get("sparte") in erlaubt)]
    zeilen.sort(key=lambda z: z["nr"], reverse=True)
    summe = lambda k: round(sum(float(z[k] or 0) for z in zeilen if z["status"] != "storniert"), 2)
    jahre = sorted({str(x.get("jahr")) for x in r["liste"].values()} | {time.strftime("%Y")}, reverse=True)
    return {"zeilen": zeilen, "jahre": jahre, "status": R_STATUS, "einstellungen": rechnung_einstellungen(d),
            "summe": {"brutto": summe("brutto"), "bezahlt": summe("bezahlt"), "offen": summe("offen_betrag")},
            "log": [f"{len(zeilen)} Rechnung(en) · Summe {geld(summe('brutto'))} · bezahlt {geld(summe('bezahlt'))} · offen {geld(summe('offen_betrag'))}"]}


def akt_rechnungslauf(d, b, ich):
    """für alle gebuchten Parzellen mit Mitglied eine Jahresrechnung – ohne „ausfuehren“ nur Vorschau"""
    try:
        jahr = int(b.get("jahr") or time.strftime("%Y"))
    except (TypeError, ValueError):
        raise Fehler("Jahr angeben.")
    if not 2000 <= jahr <= 2100:
        raise Fehler("Jahr 2000–2100.")
    e = rechnung_einstellungen(d)
    r = rechnungen_daten(d)
    preise = {t["name"]: float(t.get("preis") or 0) for t in tarife_pruefen(d["tarife"])}
    schon = {(x.get("sparte"), str(x.get("parzelle"))) for x in r["liste"].values() if x.get("jahr") == jahr and x.get("status") != "storniert"}
    neu, ohne, vorhanden = [], [], 0
    for kz, buch in sorted((d.get("buchungen") or {}).items()):
        for p, tarif in sorted(buch.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0):
            if not tarif:
                continue
            if (kz, str(p)) in schon:
                vorhanden += 1
                continue
            mid, m = _mitglied_der_parzelle(d, kz, p)
            if not m:
                ohne.append(f"{kz} {p}")
                continue
            zg = zusatz_geraete(d, kz, p)
            neu.append({"sparte": kz, "parzelle": int(p), "tarif": tarif, "preis": round(preise.get(tarif, 0) + zg * zusatz_preis(d), 2), "mitglied": mid,
                        "tarif_preis": preise.get(tarif, 0), "zusatz": zg, "zusatz_preis": zusatz_preis(d),
                        "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(), "email": m.get("email", "")})
    for x in neu:                                   # Guthaben (Restguthaben aus Tarifwechsel) abziehen
        x["guthaben"] = min(guthaben(d, x["sparte"], x["parzelle"]), x["preis"])
        x["preis"] = round(x["preis"] - x["guthaben"], 2)
    summe = sum(x["preis"] for x in neu)
    log = [f"{'Vorschau: ' if not b.get('ausfuehren') else ''}{len(neu)} Rechnung(en) für {jahr} über zusammen {geld(summe)}"
           + (f" · {vorhanden} gibt es schon" if vorhanden else "") + (f" · {len(ohne)} gebuchte Parzelle(n) ohne Mitglied: {', '.join(ohne[:15])}{' …' if len(ohne) > 15 else ''}" if ohne else "")]
    if not b.get("ausfuehren"):
        return {"vorschau": neu[:1000], "ohne": ohne, "log": log}
    if not neu:
        raise Fehler("Keine neuen Rechnungen – alle gebuchten Parzellen mit Mitglied haben für dieses Jahr schon eine.")
    heute = time.strftime("%Y-%m-%d")
    faellig = time.strftime("%Y-%m-%d", time.localtime(time.time() + int(e["zahlungsziel"]) * 86400))
    namen = _sparten_kz(d)
    for x in neu:
        netto, ust, brutto = _summen(e, x["preis"])
        rid = secrets.token_hex(6)
        r["liste"][rid] = {"nr": _neue_nummer(d, jahr), "jahr": jahr, "datum": heute, "faellig": faellig, "mitglied": x["mitglied"], "name": x["name"],
                           "email": x["email"], "sparte": x["sparte"], "sparte_name": namen.get(x["sparte"], x["sparte"]), "parzelle": x["parzelle"],
                           "tarif": x["tarif"], "positionen": [{"text": f"WLAN-Tarif „{x['tarif']}“, Parzelle {x['parzelle']}, Jahr {jahr}", "menge": 1,
                                                                "einzel": round(x["tarif_preis"], 2), "gesamt": round(x["tarif_preis"], 2)}]
                           + ([{"text": f"Zusätzliche Endgeräte, Parzelle {x['parzelle']}, Jahr {jahr}", "menge": x["zusatz"], "einzel": x["zusatz_preis"],
                                "gesamt": round(x["zusatz"] * x["zusatz_preis"], 2)}] if x["zusatz"] else [])
                           + ([{"text": f"Abzüglich Guthaben (Restguthaben aus Tarifwechsel), Parzelle {x['parzelle']}", "menge": 1,
                                "einzel": -x["guthaben"], "gesamt": -x["guthaben"]}] if x["guthaben"] else []),
                           "netto": netto, "ust": ust, "ust_satz": 0 if e["kleinunternehmer"] else e["ust_satz"], "brutto": brutto, "bezahlt": 0.0,
                           "status": "bezahlt" if brutto <= 0 else "offen", "zahlungen": [], "erstellt": time.strftime("%Y-%m-%d %H:%M"), "von": ich}
        if x["guthaben"]:
            guthaben_buchen(d, x["sparte"], x["parzelle"], -x["guthaben"], f"verrechnet mit Rechnung {r['liste'][rid]['nr']}")
    speichere(d)
    journal(f"Rechnungslauf {jahr}: {len(neu)} Rechnung(en) über {geld(summe)} durch {ich}")
    x = akt_rechnungen(d, {"jahr": [str(jahr)]})
    x["log"] = ["✔ " + log[0]] + x["log"]
    return x


def rechnung_pdf(d, x):
    e = rechnung_einstellungen(d)
    akz = (d.get("email_layout") or {}).get("farbe_akzent") or "#3a9a1f"
    p = PDF(titel=f"Rechnung {x['nr']}")
    L, R = 22 * MM, p.b - 20 * MM
    verein, sparte = pdf_logos(d, x.get("sparte"))
    rechts = R
    for logo in (sparte, verein):                 # oben rechts: Vereinslogo, daneben das Spartenlogo
        if logo:
            w = p.bild(rechts, 12 * MM, 42 * MM, 18 * MM, logo, "r")
            rechts -= w + 5 * MM if w else 0
    p.text(L, 24 * MM, e["firma"], 18, True, akz)
    y = 30 * MM
    for z in [z for z in e["adresse"].splitlines() if z.strip()] + [t for t in (e["email"], e["telefon"]) if t]:
        p.text(L, y, z, 9, False, (0.36, 0.42, 0.46))
        y += 4.2 * MM
    p.text(L, 58 * MM, f"{e['firma']} · {' · '.join(z.strip() for z in e['adresse'].splitlines() if z.strip())}"[:110], 7, False, (0.45, 0.45, 0.45))
    p.linie(L, 59.5 * MM, L + 85 * MM, 59.5 * MM, 0.3)
    y = 65 * MM
    for z in (x.get("name") or "", f"Kleingartenanlage {x.get('sparte_name') or x.get('sparte')}", f"Parzelle {x.get('parzelle')}"):
        if z:
            p.text(L, y, z, 11)
            y += 5.5 * MM
    info = [("Rechnungsnummer", x["nr"]), ("Rechnungsdatum", _de(x["datum"])), ("Fällig bis", _de(x["faellig"])), ("Kunde", f"{x.get('sparte')}-{x.get('parzelle')}")]
    yi = 65 * MM
    for a, w in info:
        p.text(R - 45 * MM, yi, a, 9, False, (0.36, 0.42, 0.46), "r")
        p.text(R, yi, w, 9, True, (0.11, 0.18, 0.24), "r")
        yi += 5 * MM
    y = 102 * MM
    p.text(L, y, "Rechnung " + _ersetzen(e["betreff"], {"jahr": str(x["jahr"])}), 15, True)
    y = p.absatz(L, y + 10 * MM, R - L, f"Hallo {x.get('name') or ''},\n{e['text_oben']}", 10)
    y += 3 * MM
    p.rechteck(L, y, R - L, 8 * MM, fuellung=(0.94, 0.95, 0.93))
    p.text(L + 2 * MM, y + 5.4 * MM, "Leistung", 9, True)
    p.text(R - 32 * MM, y + 5.4 * MM, "Menge", 9, True, ausrichtung="r")
    p.text(R - 2 * MM, y + 5.4 * MM, "Betrag", 9, True, ausrichtung="r")
    y += 13 * MM
    for pos in x["positionen"]:
        y2 = p.absatz(L + 2 * MM, y, R - L - 50 * MM, pos["text"], 10)
        p.text(R - 32 * MM, y, str(pos["menge"]), 10, ausrichtung="r")
        p.text(R - 2 * MM, y, geld(pos["gesamt"]), 10, ausrichtung="r")
        y = y2 + 2 * MM
    p.linie(L, y, R, y)
    y += 6 * MM
    if not x.get("ust"):
        p.text(R - 2 * MM, y, f"Gesamtbetrag  {geld(x['brutto'])}", 12, True, ausrichtung="r")
        y += 7 * MM
        if e["kleinunternehmer"]:
            p.text(L, y, "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung).", 8.5, False, (0.36, 0.42, 0.46))
            y += 6 * MM
    else:
        for a, w, f in (("Netto", x["netto"], False), (f"Umsatzsteuer {x['ust_satz']:g} %", x["ust"], False), ("Gesamtbetrag", x["brutto"], True)):
            p.text(R - 40 * MM, y, a, 10 if not f else 12, f, ausrichtung="r")
            p.text(R - 2 * MM, y, geld(w), 10 if not f else 12, f, ausrichtung="r")
            y += 6 * MM
    y += 4 * MM
    zahl = f"Bitte überweisen Sie {geld(x['brutto'])} bis {_de(x['faellig'])} unter Angabe der Rechnungsnummer {x['nr']}."
    if e["iban"]:
        zahl += f"\nEmpfänger: {e['firma']} · IBAN: {_iban_lesbar(e['iban'])}" + (f" · BIC: {e['bic']}" if e["bic"] else "") + (f" · {e['bank']}" if e["bank"] else "")
    breite = R - L - (36 * MM if e["iban"] else 0)
    y_qr = y
    y = p.absatz(L, y, breite, zahl, 10)
    if e["iban"]:
        epc = "\n".join(["BCD", "002", "1", "SCT", e["bic"], e["firma"][:70], e["iban"], f"EUR{float(x['brutto']) - float(x.get('bezahlt') or 0):.2f}", "", "", f"{x['nr']}"[:140]])
        p.qr(R - 32 * MM, y_qr - 4 * MM, 32 * MM, epc)
        p.text(R - 16 * MM, y_qr + 30 * MM, "GiroCode", 7, False, (0.45, 0.45, 0.45), "m")
        y = max(y, y_qr + 33 * MM)
    y = p.absatz(L, y + 4 * MM, R - L, e["text_unten"], 10)
    fuss = " · ".join(t for t in (e["firma"], f"Steuernummer {e['steuernr']}" if e["steuernr"] else "", f"USt-IdNr. {e['ust_id']}" if e["ust_id"] else "") if t)
    p.linie(L, p.h - 18 * MM, R, p.h - 18 * MM, 0.3)
    p.text(p.b / 2, p.h - 13 * MM, fuss, 7.5, False, (0.45, 0.45, 0.45), "m")
    if x.get("status") == "storniert":
        p.text(p.b / 2, 140 * MM, "STORNIERT", 48, True, (0.85, 0.2, 0.2), "m")
    return p.ausgabe()


def _de(iso):
    try:
        j, m, t = str(iso)[:10].split("-")
        return f"{t}.{m}.{j}"
    except ValueError:
        return str(iso)


def _iban_lesbar(i):
    return " ".join(i[k:k + 4] for k in range(0, len(i), 4))


def _holen(d, rid, erlaubt=None):
    x = rechnungen_daten(d)["liste"].get(str(rid or ""))
    if not x or (erlaubt is not None and x.get("sparte") not in erlaubt):
        raise Fehler("Rechnung nicht gefunden.")
    return x


def akt_rechnung_pdf(d, q, erlaubt=None):
    x = _holen(d, q.get("id", [""])[0], erlaubt)
    return {"_datei": rechnung_pdf(d, x), "typ": "application/pdf", "name": f"Rechnung_{x['nr']}.pdf"}


def _werte(d, x):
    w = _platzhalter_werte({"sparte": x.get("sparte"), "parzelle": x.get("parzelle"), "tarif": x.get("tarif"), "email": x.get("email"), "name": x.get("name"),
                            "betrag": geld(x["brutto"]), "referenz": x["nr"]}, d)
    w.update(rechnung=x["nr"], betrag=geld(x["brutto"]), faellig=_de(x["faellig"]))
    return w


def akt_rechnung_senden(d, b, ich, erlaubt=None):
    ids = [str(i) for i in (b.get("ids") or [])][:500]
    if not ids:
        raise Fehler("Keine Rechnung ausgewählt.")
    e = rechnung_einstellungen(d)
    ok, log = 0, []
    for rid in ids:
        x = _holen(d, rid, erlaubt)
        if x.get("status") == "storniert" or x.get("gesperrt"):
            log.append(f"– {x['nr']}: {'storniert' if x.get('status') == 'storniert' else 'gesperrt (Datenschutz)'}, nicht gesendet")
            continue
        if not x.get("email"):
            log.append(f"✖ {x['nr']}: keine E-Mail-Adresse beim Mitglied")
            continue
        w = _werte(d, x)
        try:
            email_senden(d, x["email"], _ersetzen(e["email_betreff"], w), None, _ersetzen(e["email_text"], w, html=True),
                         anhaenge=[(f"Rechnung_{x['nr']}.pdf", rechnung_pdf(d, x), "application/pdf")], sparte=x.get("sparte") or None)
            x["versendet"] = time.strftime("%Y-%m-%d %H:%M")
            ok += 1
        except Fehler as f:
            log.append(f"✖ {x['nr']}: {f}")
            break
        except Exception as f:
            log.append(f"✖ {x['nr']}: {text_einzeilig(str(f), 200)}")
    speichere(d)
    journal(f"Rechnungen versendet: {ok} von {len(ids)} durch {ich}")
    r = akt_rechnungen(d, {}, erlaubt)
    r["log"] = [f"✔ {ok} Rechnung(en) per E-Mail versendet."] + log[:50]
    return r


def zahlung_buchen(d, x, betrag, datum, referenz, quelle):
    x.setdefault("zahlungen", []).append({"datum": datum, "betrag": round(float(betrag), 2), "referenz": text_einzeilig(referenz, 200), "quelle": quelle})
    x["bezahlt"] = round(sum(float(z["betrag"]) for z in x["zahlungen"]), 2)
    x["status"] = "bezahlt" if x["bezahlt"] >= float(x["brutto"]) - 0.005 else ("teilweise" if x["bezahlt"] > 0 else "offen")
    ereignis("zahlung", {"sparte": x.get("sparte"), "parzelle": x.get("parzelle"), "betrag": f"{float(betrag):.2f}", "referenz": x["nr"], "email": x.get("email", ""),
                         "name": x.get("name", ""), "tarif": x.get("tarif", ""), "rechnung": x["nr"], "quelle": quelle}, d)


def akt_rechnung_status(d, b, ich, erlaubt=None):
    x = _holen(d, b.get("id"), erlaubt)
    if b.get("stornieren"):
        if x.get("bezahlt"):
            raise Fehler("Bezahlte Rechnungen bitte nicht stornieren – Zahlung erst klären.")
        x["status"] = "storniert"
        text = "storniert"
    elif b.get("zahlung") is not None:
        try:
            betrag = float(str(b["zahlung"]).replace(",", "."))
        except (TypeError, ValueError):
            raise Fehler("Betrag muss eine Zahl sein.")
        if betrag <= 0:
            raise Fehler("Betrag größer als 0.")
        zahlung_buchen(d, x, betrag, str(b.get("datum") or time.strftime("%Y-%m-%d"))[:10], b.get("referenz") or "von Hand", ich)
        text = f"Zahlung {geld(betrag)} erfasst"
    else:
        raise Fehler("Nichts angegeben.")
    speichere(d)
    journal(f"Rechnung {x['nr']}: {text} durch {ich}")
    r = akt_rechnungen(d, {}, erlaubt)
    r["log"] = [f"✔ {x['nr']}: {text}."]
    return r


# ---- Kontoauszug (CSV) ----------------------------------------------------------------------------------------------
_K = {"datum": ("buchungstag", "buchungsdatum", "datum", "valuta", "wertstellung", "booking date"),
      "betrag": ("betrag", "betrag (eur)", "umsatz", "betrag in eur", "amount", "betrag (€)"),
      "haben": ("haben", "gutschrift"),
      "zweck": ("verwendungszweck", "buchungstext", "beschreibung", "vorgang/verwendungszweck", "purpose"),
      "name": ("auftraggeber", "name", "zahlungspflichtige", "auftraggeber/empfänger", "beguenstigter/zahlungspflichtiger", "begünstigter/zahlungspflichtiger",
               "name zahlungsbeteiligter", "empfänger", "zahlungsbeteiligter", "gegenkonto name")}


def _betrag(t):
    t = str(t or "").replace("€", "").replace("EUR", "").replace(" ", "").strip()
    if not t:
        return None
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return round(float(t), 2)
    except ValueError:
        return None


def _datum(t):
    t = str(t or "").strip()
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", t)
    if m:
        j = m.group(3)
        return f"{('20' + j) if len(j) == 2 else j}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", t)
    return m.group(0) if m else t[:10]


def kontoauszug_lesen(roh):
    try:
        text = roh.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = roh.decode("cp1252", errors="replace")
    trenner = ";" if text.count(";") >= text.count(",") else ","
    zeilen = list(csv.reader(io.StringIO(text), delimiter=trenner))
    kopf_i, sp = None, {}
    for i, z in enumerate(zeilen[:40]):
        k = [c.strip().lower().strip('"') for c in z]
        if any(c in _K["betrag"] or c in _K["haben"] for c in k) and any(c in _K["zweck"] for c in k):
            kopf_i = i
            for feld, namen in _K.items():
                for j, c in enumerate(k):
                    if c in namen:
                        sp.setdefault(feld, j)
            break
    if kopf_i is None:
        raise Fehler("Im Kontoauszug keine Kopfzeile mit „Betrag“ und „Verwendungszweck“ gefunden. Bitte den CSV-Export der Bank verwenden.")
    aus = []
    for z in zeilen[kopf_i + 1:]:
        if not any(c.strip() for c in z):
            continue
        g = lambda f: z[sp[f]].strip() if f in sp and sp[f] < len(z) else ""
        betrag = _betrag(g("betrag")) if "betrag" in sp else _betrag(g("haben"))
        if betrag is None or betrag <= 0:
            continue
        x = {"datum": _datum(g("datum")), "betrag": betrag, "zweck": text_einzeilig(g("zweck"), 300), "name": text_einzeilig(g("name"), 120)}
        x["hash"] = hashlib.sha1(f"{x['datum']}|{x['betrag']}|{x['zweck']}|{x['name']}".encode()).hexdigest()[:20]
        aus.append(x)
    return aus


def _vorschlag(d, z, offen):
    zweck = re.sub(r"\s+", "", (z["zweck"] + " " + z["name"]).upper())
    for rid, x in offen.items():
        if x["nr"].upper().replace(" ", "") in zweck:
            return rid, "Rechnungsnummer"
    rest = lambda x: round(float(x["brutto"]) - float(x.get("bezahlt") or 0), 2)
    text = (z["zweck"] + " " + z["name"]).lower()
    kand = [(rid, x) for rid, x in offen.items() if abs(rest(x) - z["betrag"]) < 0.01]
    namen = [(rid, x) for rid, x in kand if x.get("name") and x["name"].split()[-1].lower() in text]
    if len(namen) == 1:
        return namen[0][0], "Betrag und Name"
    parz = [(rid, x) for rid, x in kand if re.search(rf"\b(parzelle|parz\.?|p)\s*{x.get('parzelle')}\b", text)]
    if len(parz) == 1:
        return parz[0][0], "Betrag und Parzelle"
    return None, ""


def akt_zahlungen_import(d, roh, ich, erlaubt=None):
    if not roh:
        raise Fehler("Leere Datei.")
    zeilen = kontoauszug_lesen(roh)
    r = rechnungen_daten(d)
    bekannt = set(r["importe"])
    offen = {rid: x for rid, x in r["liste"].items() if x.get("status") in ("offen", "teilweise") and (erlaubt is None or x.get("sparte") in erlaubt)}
    for z in zeilen:
        z["schon"] = z["hash"] in bekannt
        z["rechnung"], z["grund"] = (None, "") if z["schon"] else _vorschlag(d, z, offen)
        if z["rechnung"]:
            z["nr"] = offen[z["rechnung"]]["nr"]
    iid = secrets.token_hex(6)
    ablage_schreiben(f"Zahlungsimport_{iid}.json", json.dumps({"zeit": time.time(), "zeilen": zeilen}, ensure_ascii=False))
    for alt in ablage_liste("Zahlungsimport_")[:-5]:
        ablage_loeschen(alt)
    zug = sum(1 for z in zeilen if z["rechnung"])
    return {"import": iid, "zeilen": zeilen, "offen": [{"id": rid, "nr": x["nr"], "name": x.get("name"), "rest": round(float(x["brutto"]) - float(x.get("bezahlt") or 0), 2)}
                                                       for rid, x in sorted(offen.items(), key=lambda a: a[1]["nr"])],
            "log": [f"{len(zeilen)} Zahlungseingang/-eingänge gelesen · {zug} automatisch zugeordnet · {sum(1 for z in zeilen if z['schon'])} schon früher übernommen. Bitte prüfen, dann „Übernehmen“."]}


def akt_zahlungen_uebernehmen(d, b, ich, erlaubt=None):
    iid = re.sub(r"[^0-9a-f]", "", str(b.get("import") or ""))
    roh = ablage_lesen(f"Zahlungsimport_{iid}.json") if iid else None
    if not roh:
        raise Fehler("Import nicht gefunden – bitte den Kontoauszug erneut hochladen.")
    zeilen = {z["hash"]: z for z in json.loads(roh.decode("utf-8"))["zeilen"]}
    zuordnung = b.get("zuordnung") or {}
    r = rechnungen_daten(d)
    ok, log = 0, []
    for h, rid in zuordnung.items():
        z = zeilen.get(h)
        if not z or not rid or z.get("schon") or h in r["importe"]:
            continue
        x = _holen(d, rid, erlaubt)
        if x.get("status") == "storniert":
            log.append(f"– {x['nr']}: storniert, Zahlung nicht gebucht")
            continue
        zahlung_buchen(d, x, z["betrag"], z["datum"], f"{z['name']} · {z['zweck']}", f"Kontoauszug ({ich})")
        r["importe"].append(h)
        ok += 1
        log.append(f"✔ {x['nr']}: {geld(z['betrag'])} vom {_de(z['datum'])} – jetzt {R_STATUS[x['status']]}")
    r["importe"] = r["importe"][-20000:]
    speichere(d)
    ablage_loeschen(f"Zahlungsimport_{iid}.json")
    journal(f"Zahlungsabgleich: {ok} Zahlung(en) gebucht durch {ich}")
    x = akt_rechnungen(d, {}, erlaubt)
    x["log"] = [f"✔ {ok} Zahlung(en) gebucht."] + log[:60]
    return x


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

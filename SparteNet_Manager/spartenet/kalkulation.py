"""SparteNet Manager – Kalkulation: Buchungen, Umsatz, Auslastung, Wirtschaftlichkeit"""
from .pwa import *  # noqa: F401,F403 – alle Namen der vorherigen Module


# =============================================================== Kalkulation (Buchungen, Umsatz, Auslastung, Wirtschaftlichkeit)
KALK_STANDARD = {
    "kleinunternehmer": True, "ust": 19.0, "preise_inkl_ust": True,
    "uplink_monat": 75.0, "strom_mast": 50.0, "strom_hv": 80.0, "zahlung_pct": 3.0, "wartung_pct": 3.0,
    "zentral_start_technik": 1200.0, "zentral_start_personal": 0.0, "zentral_start_sonstiges": 1500.0,
    "zentral_voll_technik": 36000.0, "zentral_voll_personal": 60000.0, "zentral_voll_sonstiges": 15000.0,
    "phase": "auto", "abschreibung_jahre": 5.0, "ueberbuchung": 8.0,
    "ku_grenze_vorjahr": 25000.0, "ku_grenze_lfd": 100000.0, "quote_prognose": 60.0,
}
KALK_TEXTE = {
    "kleinunternehmer": "Kleinunternehmer (§ 19 UStG)", "ust": "Umsatzsteuersatz (%)", "preise_inkl_ust": "Regelbesteuerung: Tarifpreise enthalten MwSt.",
    "uplink_monat": "Uplink je Sparte und Monat (€, netto)", "strom_mast": "Strom je Mast mit Technik und Jahr (€)", "strom_hv": "Strom Hauptverteiler je Sparte und Jahr (€)",
    "zahlung_pct": "Zahlungsabwicklung (% vom Umsatz)", "wartung_pct": "Wartung/Ersatzteile (% der Investition je Jahr)",
    "zentral_start_technik": "Startphase: zentrale Technik (€/Jahr)", "zentral_start_personal": "Startphase: Personal (€/Jahr)", "zentral_start_sonstiges": "Startphase: Versicherung, Steuerberatung (€/Jahr)",
    "zentral_voll_technik": "Ausbau: zentrale Technik (€/Jahr)", "zentral_voll_personal": "Ausbau: Personal (€/Jahr)", "zentral_voll_sonstiges": "Ausbau: Versicherung, Steuerberatung, Recht (€/Jahr)",
    "phase": "Zentrale Kosten", "abschreibung_jahre": "Abschreibungsdauer Hardware (Jahre)", "ueberbuchung": "Überbuchungsfaktor (1:x) für den Uplink",
    "ku_grenze_vorjahr": "Umsatzgrenze Kleinunternehmer Vorjahr (€)", "ku_grenze_lfd": "Umsatzgrenze laufendes Jahr (€)", "quote_prognose": "Buchungsquote für Prognose (%)",
}


def kalk_annahmen(d):
    roh = ((d.get("kalk") or {}).get("annahmen")) or {}
    a = dict(KALK_STANDARD)
    for k, std in KALK_STANDARD.items():
        if k not in roh:
            continue
        v = roh[k]
        if isinstance(std, bool):
            a[k] = bool(v)
        elif k == "phase":
            a[k] = v if v in ("auto", "start", "voll") else "auto"
        else:
            try:
                a[k] = max(0.0, float(v))
            except (TypeError, ValueError):
                raise Fehler(f"„{KALK_TEXTE.get(k, k)}“ muss eine Zahl sein.")
    if a["abschreibung_jahre"] < 1 or a["ueberbuchung"] < 1:
        raise Fehler("Abschreibungsdauer und Überbuchungsfaktor müssen mindestens 1 sein.")
    if a["quote_prognose"] > 100:
        raise Fehler("Buchungsquote höchstens 100 %.")
    return a


def kalk_sparten(d):
    """Alle eingetragenen Sparten: aus der Planung (aktives Gateway) und aus dem VLAN-Planer übernommene"""
    k = d.get("kalk") or {}
    extra = k.get("sparten") or {}
    aus = {}
    try:
        plan = plan_berechnen(d["plan"])
        for s in plan["sparten"]:
            aus[s["kz"]] = {"kz": s["kz"], "name": s["name"], "n": s["n"], "gateway": plan["gateway"], "quelle": "Planung"}
    except Fehler:
        pass
    for kz, s in extra.items():
        if kz in aus:
            continue
        try:
            n = int(s.get("n") or 0)
        except (TypeError, ValueError):
            n = 0
        if s.get("name") and n > 0:
            aus[kz] = {"kz": kz, "name": s["name"], "n": n, "gateway": s.get("gateway") or "", "quelle": s.get("quelle", "VLAN-Planer")}
    for kz, s in aus.items():
        w = extra.get(kz) or {}
        s["investition"] = w.get("investition")
        s["masten"] = w.get("masten")
        s["uplink"] = w.get("uplink")
    return aus


def _zahl_oder_none(v, text):
    if v in (None, ""):
        return None
    try:
        x = float(str(v).replace(",", "."))
    except ValueError:
        raise Fehler(f"{text}: bitte eine Zahl eintragen.")
    if x < 0:
        raise Fehler(f"{text}: nicht negativ.")
    return x


def akt_kalkulation(d, prognose=False):
    a = kalk_annahmen(d)
    tarife = tarife_pruefen(d["tarife"])
    preis = {t["name"]: float(t.get("preis") or 0) for t in tarife}
    down = {t["name"]: float(t.get("down") or 0) for t in tarife}
    ku = a["kleinunternehmer"]
    ek = 1 + a["ust"] / 100 if ku else 1.0  # Einkauf ohne Vorsteuerabzug = brutto
    netto = (lambda p: p) if ku else ((lambda p: p / (1 + a["ust"] / 100)) if a["preise_inkl_ust"] else (lambda p: p))
    oe = sum(preis.values()) / len(preis) if preis else 0
    buch = d.get("buchungen") or {}
    zeilen, unbekannt = [], 0
    for kz, s in sorted(kalk_sparten(d).items(), key=lambda x: (str(x[1]["gateway"]), x[1]["name"].lower())):
        b = buch.get(kz) or {}
        je = {t["name"]: 0 for t in tarife}
        for p, t in b.items():
            if p.isdigit() and 1 <= int(p) <= s["n"]:
                if t in je:
                    je[t] += 1
                else:
                    unbekannt += 1
        gebucht = sum(je.values())
        umsatz_b = sum(je[t] * preis[t] for t in je)
        umsatz = sum(je[t] * netto(preis[t]) for t in je)
        uplink_bedarf = sum(je[t] * down[t] for t in je) / a["ueberbuchung"]
        status = "konfiguriert" if gebucht else "eingetragen"
        prog = False
        if not gebucht and prognose and a["quote_prognose"] > 0:
            # Prognose: Buchungsquote × Parzellen, Tarifmix wie im Durchschnitt der Tarifpreise
            gebucht_p = round(s["n"] * a["quote_prognose"] / 100)
            umsatz_b = gebucht_p * oe
            umsatz = gebucht_p * netto(oe)
            uplink_bedarf = gebucht_p * (sum(down.values()) / len(down) if down else 0) / a["ueberbuchung"]
            prog, status = gebucht_p, "Prognose"
        inv = float(s["investition"] or 0)
        masten = float(s["masten"] or 0)
        uplink = s["uplink"] if s["uplink"] is not None else a["uplink_monat"]
        in_betrieb = bool(gebucht or prog or inv)
        kosten = ((uplink * 12 + masten * a["strom_mast"] + a["strom_hv"]) * ek + umsatz * a["zahlung_pct"] / 100 + inv * a["wartung_pct"] / 100) if in_betrieb else 0.0
        db = umsatz - kosten
        zeilen.append({
            "kz": kz, "name": s["name"], "gateway": s["gateway"], "quelle": s["quelle"], "n": s["n"], "gebucht": gebucht, "prognose": prog or 0,
            "rate": gebucht / s["n"] if s["n"] else 0, "je": je, "umsatz_brutto": round(umsatz_b, 2), "umsatz": round(umsatz, 2),
            "erloes_monat": round(umsatz_b / gebucht / 12, 2) if gebucht else (round(oe / 12, 2) if prog else 0),
            "investition": s["investition"], "masten": s["masten"], "uplink": s["uplink"], "kosten": round(kosten, 2), "db": round(db, 2),
            "amortisation": round(inv / db, 1) if inv and db > 0 else ("nie" if inv and db <= 0 else None),
            "uplink_bedarf": round(uplink_bedarf), "uplink_warnung": uplink_bedarf > 900, "status": status})
    konf = [z for z in zeilen if z["status"] == "konfiguriert"]
    summe = lambda liste, k: round(sum(float(z[k] or 0) for z in liste), 2)
    parz_konf, geb = sum(z["n"] for z in konf), sum(z["gebucht"] for z in konf)
    parz_alle = sum(z["n"] for z in zeilen)
    phase = a["phase"] if a["phase"] != "auto" else ("start" if ku else "voll")
    zentral = sum(a[f"zentral_{phase}_{x}"] for x in ("technik", "personal", "sonstiges"))
    zentral_ek = (a[f"zentral_{phase}_technik"] + a[f"zentral_{phase}_sonstiges"]) * ek + a[f"zentral_{phase}_personal"]
    umsatz_ges, db_ges, inv_ges = summe(zeilen, "umsatz"), summe(zeilen, "db"), summe(zeilen, "investition")
    afa = inv_ges / a["abschreibung_jahre"]
    ergebnis_vor = db_ges - zentral_ek
    umsatz_brutto_ges = summe(zeilen, "umsatz_brutto")
    oe_buchung = umsatz_brutto_ges / max(1, geb + sum(z["prognose"] for z in zeilen)) if umsatz_brutto_ges else oe
    gesamt = {
        "sparten": len(zeilen), "sparten_konf": len(konf), "parzellen_alle": parz_alle, "parzellen_konf": parz_konf, "gebucht": geb,
        "auslastung_konf": geb / parz_konf if parz_konf else 0, "auslastung_alle": geb / parz_alle if parz_alle else 0,
        "je": {t["name"]: sum(z["je"][t["name"]] for z in zeilen) for t in tarife},
        "umsatz_brutto": umsatz_brutto_ges, "umsatz": umsatz_ges, "kosten": summe(zeilen, "kosten"), "db": db_ges, "investition": inv_ges,
        "zentral": round(zentral_ek, 2), "phase": phase, "ergebnis_vor_afa": round(ergebnis_vor, 2), "afa": round(afa, 2), "ergebnis": round(ergebnis_vor - afa, 2),
        "amortisation": round(inv_ges / ergebnis_vor, 1) if inv_ges and ergebnis_vor > 0 else ("nicht erreicht" if inv_ges else None),
        "ku": ku, "ku_grenze": a["ku_grenze_vorjahr"], "ku_status": ("unter der Grenze" if umsatz_brutto_ges <= a["ku_grenze_vorjahr"] else "Grenze überschritten → ab Folgejahr Regelbesteuerung") if ku else "Regelbesteuerung",
        "ku_rest_parzellen": int(max(0, a["ku_grenze_vorjahr"] - umsatz_brutto_ges) // oe_buchung) if ku and oe_buchung else None,
    }
    log = [f"{len(zeilen)} Sparten eingetragen, davon {len(konf)} mit Buchungen · {geb} von {parz_konf} Parzellen gebucht ({gesamt['auslastung_konf']:.1%})"]
    if unbekannt:
        log.append(f"⚠ {unbekannt} Buchung(en) mit einem Tarif, den es nicht mehr gibt – im Bereich „Buchungen erfassen“ neu zuordnen.")
    if any(z["uplink_warnung"] for z in zeilen):
        log.append("⚠ Bei mindestens einer Sparte reicht 1 Gbit/s Uplink rechnerisch nicht (Spalte Uplink-Bedarf).")
    return {"zeilen": zeilen, "gesamt": gesamt, "tarife": [{"name": t["name"], "preis": t.get("preis", 0), "down": t["down"]} for t in tarife],
            "annahmen": a, "texte": KALK_TEXTE, "log": log}


def akt_kalk_annahmen(d, b):
    k = d.setdefault("kalk", {})
    alt = k.get("annahmen") or {}
    k["annahmen"] = {**alt, **{x: b[x] for x in KALK_STANDARD if x in b}}
    try:
        kalk_annahmen(d)
    except Fehler:
        k["annahmen"] = alt
        raise
    speichere(d)
    return {"log": ["✔ Annahmen gespeichert."]}


def akt_kalk_sparte(d, b):
    """Investition, Masten mit Technik und Uplink je Sparte speichern"""
    kz = str(b.get("sparte") or "")
    if kz not in kalk_sparten(d):
        raise Fehler("Sparte unbekannt.")
    k = d.setdefault("kalk", {})
    s = k.setdefault("sparten", {}).setdefault(kz, {})
    for feld, text in (("investition", "Investition"), ("masten", "Masten mit Technik"), ("uplink", "Uplink €/Monat")):
        if feld in b:
            s[feld] = _zahl_oder_none(b[feld], text)
    speichere(d)
    return {"log": [f"✔ {kz} gespeichert."]}


def akt_buchungen(d, kz):
    sp = kalk_sparten(d).get(kz)
    if not sp:
        raise Fehler("Sparte unbekannt.")
    b = (d.get("buchungen") or {}).get(kz) or {}
    namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
    return {"sparte": sp["name"], "kz": kz, "n": sp["n"],
            "zeilen": [{"p": p, "netz": NETZ_PARZELLE.format(kz=kz, p=p), "tarif": b.get(str(p), ""), "unbekannt": bool(b.get(str(p))) and b.get(str(p)) not in namen}
                       for p in range(1, sp["n"] + 1)], "log": []}


def akt_buchungen_speichern(d, kz, aenderungen):
    sp = kalk_sparten(d).get(kz)
    if not sp or not isinstance(aenderungen, dict):
        raise Fehler("Sparte unbekannt oder ungültige Angaben.")
    namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
    b = d.setdefault("buchungen", {}).setdefault(kz, {})
    vorher = dict(b)
    for p, t in aenderungen.items():
        if not str(p).isdigit() or not 1 <= int(p) <= sp["n"]:
            raise Fehler(f"Parzelle {p} gibt es in {kz} nicht (1–{sp['n']}).")
        if not t:
            b.pop(str(int(p)), None)
        elif t in namen:
            b[str(int(p))] = t
        else:
            raise Fehler(f"Tarif „{t}“ gibt es nicht.")
    if not b:
        d["buchungen"].pop(kz, None)
    speichere(d)
    journal(f"Buchungen {kz}: {len(aenderungen)} Änderung(en), jetzt {len(b)} gebucht")
    for p in sorted({str(int(x)) for x in aenderungen}, key=int):
        if vorher.get(p) != b.get(p):
            ereignis("buchung" if b.get(p) else "kuendigung", {"sparte": kz, "sparte_name": sp["name"], "parzelle": int(p),
                                                             "tarif": b.get(p, ""), "tarif_alt": vorher.get(p, "")}, d)
    return {"log": [f"✔ {len(aenderungen)} Änderung(en) gespeichert – {len(b)} von {sp['n']} Parzellen gebucht. "
                    "Ans Gateway (Bandbreite/Netzgröße) geht das über den Reiter „Tarife“."]}


def _xlsx_blaetter(roh_bytes):
    return xlsx_lesen(roh_bytes)


def _norm(s):
    s = str(s or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = re.sub(r"\b(kgv|kga|kgs|kleingartenverein|kleingartenanlage|e\.?\s?v\.?|sparte)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def akt_kalk_import(d, roh):
    """Excel: entweder die Kalkulation (Annahmen, Sparten-Blätter) oder der VLAN-Planer (Blatt Sparten)"""
    namen, lies = _xlsx_blaetter(roh)
    log = []
    k = d.setdefault("kalk", {})
    if "Annahmen" in namen and "Zusammenfassung" in namen:
        an = lies("Annahmen") or {}
        def z(c, std=None):
            v = an.get(c)
            return v if isinstance(v, (int, float)) else std
        neu = {"kleinunternehmer": z("B12", 1) == 1, "ust": (z("B20", 0.19) or 0) * 100, "preise_inkl_ust": z("B19", 1) == 1,
               "uplink_monat": z("B24"), "strom_mast": z("B25"), "strom_hv": z("B26"),
               "zahlung_pct": (z("B27", 0.03) or 0) * 100, "wartung_pct": (z("B28", 0.03) or 0) * 100,
               "zentral_voll_technik": z("B31"), "zentral_voll_personal": z("B32"), "zentral_voll_sonstiges": z("B33"),
               "zentral_start_technik": z("B36"), "zentral_start_personal": z("B37"), "zentral_start_sonstiges": z("B38"),
               "abschreibung_jahre": z("B40"), "ueberbuchung": z("B41"), "ku_grenze_vorjahr": z("B14"), "ku_grenze_lfd": z("B15"),
               "quote_prognose": (z("B18", 0.6) or 0) * 100}
        k["annahmen"] = {**(k.get("annahmen") or {}), **{x: v for x, v in neu.items() if v is not None}}
        log.append("✔ Annahmen übernommen (Steuer, Uplink, Strom, Zahlung, Wartung, zentrale Kosten, Abschreibung, Quote).")
        # Tarifpreise der Reihe nach auf die Tarife des Managers
        tarife = tarife_pruefen(d["tarife"])
        preise = [(an.get(f"A{r}"), an.get(f"C{r}")) for r in range(4, 10) if isinstance(an.get(f"C{r}"), (int, float))]
        for t, (n, p) in zip(tarife, preise):
            t["preis"] = _zahl(p)
            log.append(f"✔ Preis {t['name']}: {t['preis']} €/Jahr (aus „{n}“)")
        d["tarife"] = tarife
        # Sparten-Blätter aus der Zusammenfassung
        zus = lies("Zusammenfassung") or {}
        sparten = kalk_sparten(d)
        for r in range(5, 155):
            blatt = zus.get(f"A{r}")
            if not blatt or blatt not in namen:
                continue
            w = lies(blatt) or {}
            name, var = w.get("B3") or blatt, str(w.get("B7") or "A").upper()
            inv = w.get("G49") if isinstance(w.get("G49"), (int, float)) else w.get("F49" if var == "B" else "D49")
            masten = w.get("G52") if isinstance(w.get("G52"), (int, float)) else None
            treffer = next((kz for kz, s in sparten.items() if _norm(s["name"]) and (_norm(s["name"]) in _norm(name) or _norm(name) in _norm(s["name"]))), None)
            if not treffer:
                log.append(f"ℹ Blatt „{blatt}“ ({name}): keine passende Sparte im Manager – erst Sparte eintragen bzw. VLAN-Planer übernehmen.")
                continue
            s = k.setdefault("sparten", {}).setdefault(treffer, {})
            if isinstance(inv, (int, float)):
                s["investition"] = round(float(inv), 2)
            if isinstance(masten, (int, float)):
                s["masten"] = float(masten)
            up = w.get("B6")
            if isinstance(up, (int, float)):
                s["uplink"] = float(up)
            log.append(f"✔ {treffer} ← Blatt „{blatt}“: Investition {s.get('investition', 0):,.2f} € (Variante {var}), {int(s.get('masten') or 0)} Masten mit Technik".replace(",", "X").replace(".", ",").replace("X", "."))
    elif "Sparten" in namen and "Gateways" in namen:
        sp = lies("Sparten") or {}
        n_neu = 0
        for r in range(5, 1000):
            name = sp.get(f"B{r}")
            if name is None and sp.get(f"A{r}") is None:
                break
            gw, kz, n = sp.get(f"F{r}"), sp.get(f"D{r}"), sp.get(f"C{r}")
            if not name or not kz or not isinstance(n, (int, float)) or gw in (None, ""):
                continue
            s = k.setdefault("sparten", {}).setdefault(str(kz), {})
            s.update({"name": str(name), "n": int(n), "gateway": gw, "quelle": "VLAN-Planer"})
            n_neu += 1
        # Sparten, die im VLAN-Planer kein Gateway mehr haben, verlieren den Planer-Eintrag (Werte bleiben)
        log.append(f"✔ {n_neu} Sparten mit Gateway aus dem VLAN-Planer übernommen (Name, Kürzel, Parzellen, Gateway).")
    else:
        raise Fehler("Unbekannte Datei: erwartet wird die Kalkulation (Blätter „Annahmen“ und „Zusammenfassung“) oder der VLAN-Planer (Blätter „Sparten“ und „Gateways“).")
    speichere(d)
    return {"log": log}

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

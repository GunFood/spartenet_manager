"""SparteNet Manager – Netzplanung: Gateway-Standorte, Glasfaser-Kette, Buchungsquote, theoretische Einnahmen"""
from .netzplanung_daten import *  # noqa: F401,F403 – alle Namen der vorherigen Module


GWP_STANDARD = {
    "PG": 55, "Max_GW": 10, "Vorschlag_nutzen": 1, "Umweg": 1.3, "Uplink_Kap": 1000, "Ueberbuchung": 8, "Bandbreite": 30, "Jahre": 5,
    "P_UCG": 250, "P_Agg": 240, "P_DAC": 20, "P_KVz": 1500, "P_USV": 250, "P_SFP": 21.9, "P_Flex": 179, "P_NT": 70, "P_Halter": 8.5,
    "P_Luefter": 45, "P_Spleiss": 32.9, "P_Saeule": 300, "P_Ueber": 80, "P_Surge": 12, "P_AP": 250, "P_Mast": 392, "P_Fund": 120,
    "P_Faser": 1.5, "P_Kupfer": 1.2, "P_Tiefbau": 0, "P_MontStandort": 500, "P_MontMast": 150, "P_MontZul": 150,
    "KU": 1, "USt": 0.19,
    "Parz_je_AP": 3.6, "AP_je_Mast": 2.2, "Anteil_Technik": 0.5, "Leitung_k": 2.806, "Faser_f": 1.66, "Kupfer_f": 1.06, "Kabel_je_AP": 0.42, "Ports_Agg": 8,
    "Uplink_Monat": 75, "Strom_Standort": 80, "Strom_GW": 25, "Strom_Mast": 50, "Wartung": 0.03, "Zahlung": 0.03, "Preis_Jahr": 120,
    "Quote_Modus": 1, "Quote_fest": 0.6, "Szenario": 1,
    "Neig_1": 0.80, "Neig_2": 0.75, "Neig_3": 0.60, "Neig_4": 0.35, "Neig_5": 0.10,
    "Stufe_A": 1.0, "Stufe_B": 1.0, "Stufe_C": 0.9, "Stufe_D": 0.75,
    "Abg_1": 0.05, "Abg_2": 0.05, "Abg_3": 0.10, "Abg_4": 0.30, "Abg_5": 0.60, "Nachbes": 0.7, "Nachbes_Leer": 2,
}
# Gruppen, Texte und Einheit für das Formular („%“ = intern Anteil 0–1, im Formular Prozent)
GWP_FELDER = [
    ("Netz-Regeln", [("PG", "Parzellen je Gateway", ""), ("Max_GW", "Gateways je Standort (Warnung darüber)", ""),
                     ("Vorschlag_nutzen", "Standort-Vorschlag nutzen, wo nichts gewählt (1 = ja, 0 = eigenständig)", ""),
                     ("Umweg", "Umwegfaktor Glasfaser (Trasse statt Luftlinie)", ""), ("Uplink_Kap", "Kapazität Internet-Anschluss (Mbit/s)", ""),
                     ("Ueberbuchung", "Überbuchungsfaktor (1:x)", ""), ("Bandbreite", "Ø Bandbreite je Kunde (Mbit/s)", ""), ("Jahre", "Betrachtungszeitraum (Jahre)", "")]),
    ("Buchungsquote", [("Quote_Modus", "Modus (1 = aus Alter und Leerstand, 2 = feste Quote)", ""), ("Quote_fest", "Feste Quote (Modus 2)", "%"),
                       ("Szenario", "Modus 1 rechnet mit (1 = heute, 2 = in 5 Jahren)", ""),
                       ("Neig_1", "Buchungsneigung Pächter bis 30", "%"), ("Neig_2", "Buchungsneigung 30–50", "%"), ("Neig_3", "Buchungsneigung 50–70", "%"),
                       ("Neig_4", "Buchungsneigung 70–90", "%"), ("Neig_5", "Buchungsneigung ab 90", "%"),
                       ("Stufe_A", "Faktor Entwicklungsstufe A", "%"), ("Stufe_B", "Faktor Stufe B", "%"), ("Stufe_C", "Faktor Stufe C", "%"), ("Stufe_D", "Faktor Stufe D", "%"),
                       ("Abg_1", "Pachtaufgabe in 5 J., bis 30", "%"), ("Abg_2", "Pachtaufgabe 30–50", "%"), ("Abg_3", "Pachtaufgabe 50–70", "%"),
                       ("Abg_4", "Pachtaufgabe 70–90", "%"), ("Abg_5", "Pachtaufgabe ab 90", "%"),
                       ("Nachbes", "Nachbesetzung frei werdender Parzellen", "%"), ("Nachbes_Leer", "Abschlag je Prozentpunkt Leerstand", "")]),
    ("Laufende Kosten und Erlös", [("Preis_Jahr", "Fester Preis je Kunde und Jahr (€) – wenn nicht nach Tarifmix", ""),
                                   ("Uplink_Monat", "Internet-Anschluss je Monat (€ netto)", ""), ("Strom_Standort", "Strom Standort je Jahr (€)", ""),
                                   ("Strom_GW", "Strom je Gateway und Jahr (€)", ""), ("Strom_Mast", "Strom je Mast mit Technik und Jahr (€)", ""),
                                   ("Wartung", "Wartung (Anteil der Investition je Jahr)", "%"), ("Zahlung", "Zahlungsabwicklung (Anteil vom Umsatz)", "%"),
                                   ("KU", "Kleinunternehmer (1 = ja, 0 = nein)", ""), ("USt", "Umsatzsteuersatz", "%")]),
    ("Preise (netto, €)", [("P_UCG", "Gateway (Cloud Gateway Fiber)", ""), ("P_Agg", "Switch Aggregation (8× SFP+)", ""), ("P_DAC", "DAC-Kabel je Gateway", ""),
                           ("P_KVz", "Außenschrank Standort", ""), ("P_USV", "USV + Überspannungsschutz Standort", ""), ("P_SFP", "SFP 1G Singlemode", ""),
                           ("P_Flex", "Switch Flex 2.5G PoE", ""), ("P_NT", "Netzteil Flex", ""), ("P_Halter", "Hutschienen-Halter", ""), ("P_Luefter", "Lüfter mit Thermostat", ""),
                           ("P_Spleiss", "Mini-Spleißbox", ""), ("P_Saeule", "Strom-Säule", ""), ("P_Ueber", "Überspannungsschutz + LS/FI Säule", ""),
                           ("P_Surge", "Ethernet Surge Protection", ""), ("P_AP", "Access Point U7 Pro Outdoor", ""), ("P_Mast", "Mast 5 m", ""), ("P_Fund", "Mastfundament", ""),
                           ("P_Faser", "Glasfaser €/m", ""), ("P_Kupfer", "Erdkabel Cat 7 €/m", ""), ("P_Tiefbau", "Tiefbau €/m (0 = keine)", ""),
                           ("P_MontStandort", "Montage Standort", ""), ("P_MontMast", "Montage je Mast", ""), ("P_MontZul", "Montage je Glasfaser-Zuleitung", "")]),
    ("Mengen in der Sparte (Faustregeln)", [("Parz_je_AP", "Parzellen je Access Point", ""), ("AP_je_Mast", "Access Points je Mast", ""),
                                            ("Anteil_Technik", "Anteil Masten mit Technik", "%"), ("Leitung_k", "Leitungsweg-Faktor (m = k × √Fläche)", ""),
                                            ("Faser_f", "Glasfaser m je m Leitungsweg", ""), ("Kupfer_f", "Kupfer m je m Leitungsweg", ""),
                                            ("Kabel_je_AP", "Kupferkabel je AP", ""), ("Ports_Agg", "Anschlüsse je Aggregation-Switch", "")]),
]
GWP_WAHL = ("standort", "zuleitung", "reihenfolge", "entfernung", "quote", "aps", "masten", "leitung", "parz", "leer")


def _ceil(x):
    return int(-(-x // 1)) if x > 0 else 0


def _rund(x):
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def gwp_anlagen(d):
    g = d.get("gwplan") or {}
    if g.get("anlagen"):
        return g["anlagen"]
    return [{"nr": t[0], "name": t[1], "adresse": t[2], "stufe": t[3], "eigentum": t[4], "parz": t[5], "parz_konzept": t[6], "leer": t[7],
             "flaeche": t[8], "alter": list(t[9]), "x": t[10], "y": t[11], "vs_standort": t[12], "vs_zuleitung": t[13]} for t in GWP_ANLAGEN]


def gwp_annahmen(d):
    roh = ((d.get("gwplan") or {}).get("annahmen")) or {}
    a = dict(GWP_STANDARD)
    for k, v in roh.items():
        if k in a:
            try:
                a[k] = float(v)
            except (TypeError, ValueError):
                pass
    return a


def gwp_preis(d, a):
    """Ø Preis je Kunde und Jahr: nach Tarifmix aus den Tarifen des Managers oder fest"""
    g = d.get("gwplan") or {}
    tarife = [t for t in tarife_pruefen(d["tarife"])]
    mix = g.get("tarifmix") or ({tarife[0]["name"]: 100} if tarife else {})
    quelle = g.get("preis_quelle", "tarife")
    anteile = {t["name"]: max(0.0, float(mix.get(t["name"], 0) or 0)) for t in tarife}
    summe = sum(anteile.values())
    if quelle == "tarife" and summe > 0:
        preis = sum(anteile[t["name"]] * float(t.get("preis") or 0) for t in tarife) / summe
        anteile = {k: v / summe for k, v in anteile.items()}
    else:
        quelle, preis, anteile = "fest", a["Preis_Jahr"], {}
    return quelle, preis, anteile, [{"name": t["name"], "preis": float(t.get("preis") or 0), "down": t.get("down"), "anteil": anteile.get(t["name"], 0),
                                     "mix": float(mix.get(t["name"], 0) or 0)} for t in tarife]


def gwplan_berechnen(d):
    a = gwp_annahmen(d)
    A = [dict(x) for x in gwp_anlagen(d)]
    wahl = ((d.get("gwplan") or {}).get("wahl")) or {}
    EK = 1 + a["USt"] if a["KU"] == 1 else 1.0
    PG = max(1, int(a["PG"]))
    idx = {s["nr"]: s for s in A}
    for i, s in enumerate(A):
        w = wahl.get(str(s["nr"])) or {}
        s["w"] = w
        s["row"] = i + 5
        if w.get("parz") is not None:
            s["parz"] = int(w["parz"])
        if w.get("leer") is not None:
            s["leer"] = int(w["leer"])
    vn = a["Vorschlag_nutzen"] == 1
    # wirksamer Standort und Zuleitung
    for s in A:
        w, nr = s["w"], s["nr"]
        s["C"] = w["standort"] if w.get("standort") is not None else (s["vs_standort"] if vn else nr)
        if s["C"] == nr:
            s["D"] = None
        elif w.get("zuleitung") is not None:
            s["D"] = w["zuleitung"]
        elif w.get("standort") is None and vn and s.get("vs_zuleitung") is not None:
            s["D"] = s["vs_zuleitung"]
        else:
            s["D"] = s["C"]
    zahl_am = {}
    for s in A:
        zahl_am[s["C"]] = zahl_am.get(s["C"], 0) + 1
    uv = (a["P_Saeule"] + a["P_Flex"] + a["P_NT"] + a["P_Halter"] + a["P_Luefter"] + a["P_Spleiss"] + a["P_Ueber"]) * EK
    for s in A:
        w, nr = s["w"], s["nr"]
        eigen = s["C"] == nr
        q = idx.get(s["D"])
        s["rolle"] = ("Gateway-Standort" if zahl_am.get(nr, 0) > 1 else "eigenständig") if eigen else "über " + (q["name"] if q else "?")
        if eigen:
            km = 0.0
        elif w.get("entfernung") is not None:
            km = w["entfernung"] / 1000
        else:
            km = ((s["x"] - q["x"]) ** 2 + (s["y"] - q["y"]) ** 2) ** 0.5 if q else 0.0
        s["km"] = km
        s["faser_zul"] = 0.0 if eigen else (w["entfernung"] if w.get("entfernung") is not None else km * 1000 * a["Umweg"])
        s["zul_eur"] = 0.0 if eigen else (s["faser_zul"] * (a["P_Faser"] + a["P_Tiefbau"]) + 2 * a["P_SFP"] + a["P_MontZul"]) * EK
        s["uv_eur"] = 0.0 if eigen else uv
        s["sort"] = w["reihenfolge"] if w.get("reihenfolge") is not None else (500 if eigen else 1000) + s["row"]
    for s in A:
        vor = sum(t["parz"] for t in A if t["C"] == s["C"] and t["sort"] < s["sort"])
        s["davor"] = vor
        s["gw_von"] = vor // PG + 1
        s["gw_bis"] = max(s["gw_von"], _ceil((vor + s["parz"]) / PG))
        c = idx.get(s["C"])
        s["versorgt"] = f"{c['name'] if c else '?'}: GW {s['gw_von']}" + (f"–{s['gw_bis']}" if s["gw_bis"] > s["gw_von"] else "")
        nr = s["nr"]
        if not c:
            s["pruefung"] = "Fehler: Standort unbekannt"
        elif s["C"] == nr:
            s["pruefung"] = "OK"
        elif c["C"] != s["C"]:
            s["pruefung"] = "Fehler: Standort hängt selbst an anderem Standort"
        elif s["D"] == nr:
            s["pruefung"] = "Fehler: Zuleitung von sich selbst"
        elif s["D"] not in idx:
            s["pruefung"] = "Fehler: Zuleitung unbekannt"
        elif idx[s["D"]]["C"] != s["C"]:
            s["pruefung"] = "Fehler: Zuleitung hängt an anderem Standort"
        else:
            s["pruefung"] = "OK"
    # Ring in der Zuleitung (kommt nie am Standort an)
    for s in A:
        if s["pruefung"] != "OK" or s["C"] == s["nr"]:
            continue
        x, gesehen = s, set()
        while x and x["C"] != x["nr"] and x["nr"] not in gesehen:
            gesehen.add(x["nr"]); x = idx.get(x["D"])
        if not x or x["C"] != x["nr"]:
            s["pruefung"] = "Fehler: Zuleitung im Kreis – führt nicht zum Standort"
    # Buchungsquote
    for s in A:
        w, P, L = s["w"], max(1, s["parz"]), s["leer"]
        sm = max(0.0001, sum(s["alter"]))
        sh = [x / sm for x in s["alter"]]
        neig = sum(sh[i] * a[f"Neig_{i + 1}"] for i in range(5))
        sf = a.get("Stufe_" + str(s["stufe"])[:1].upper(), a["Stufe_D"])
        lq = L / P
        q_heute = neig * (1 - lq) * sf
        abg = sum(sh[i] * a[f"Abg_{i + 1}"] for i in range(5))
        nach = max(0.0, min(1.0, a["Nachbes"] - lq * a["Nachbes_Leer"]))
        leer5 = L + (P - L) * abg * (1 - nach)
        nb5 = sum(sh[i] * (1 - a[f"Abg_{i + 1}"]) * a[f"Neig_{i + 1}"] for i in range(5)) / max(0.0001, 1 - abg)
        q5 = (P - L) * ((1 - abg) * nb5 + abg * nach * a["Neig_2"]) * sf / P
        if w.get("quote") is not None:
            q, herk = w["quote"], "manuell"
        elif a["Quote_Modus"] == 2:
            q, herk = a["Quote_fest"], "fest"
        elif a["Szenario"] == 2:
            q, herk = q5, "Alter, in 5 J."
        else:
            q, herk = q_heute, "Alter, heute"
        s.update(leerq=lq, leer5=leer5, q_heute=q_heute, q5=q5, quote=q, herkunft=herk, kunden=s["parz"] * q)
    # Technik in der Sparte und Vergleich eigenständig
    for s in A:
        w = s["w"]
        aps = w["aps"] if w.get("aps") is not None else max(2, _ceil(s["parz"] / a["Parz_je_AP"]))
        masten = w["masten"] if w.get("masten") is not None else _ceil(aps / a["AP_je_Mast"])
        tech = max(1, _ceil(masten * a["Anteil_Technik"]))
        leitung = w["leitung"] if w.get("leitung") is not None else a["Leitung_k"] * (s["flaeche"] ** 0.5)
        faser, kupfer, kabel = leitung * a["Faser_f"], leitung * a["Kupfer_f"], _rund(aps * a["Kabel_je_AP"])
        J = tech * (2 * a["P_SFP"] + a["P_Flex"] + a["P_NT"] + a["P_Halter"] + a["P_Luefter"] + a["P_Spleiss"] + a["P_Saeule"] + a["P_Ueber"]) * EK
        K = (aps * a["P_AP"] + masten * (a["P_Mast"] + a["P_Fund"] + a["P_MontMast"]) + kabel * 2 * a["P_Surge"]) * EK
        Lt = (faser * a["P_Faser"] + kupfer * a["P_Kupfer"] + leitung * a["P_Tiefbau"]) * EK
        N = J + K + Lt + s["zul_eur"] + s["uv_eur"]
        P_gw = _ceil(s["parz"] / PG)
        Q = J + K + Lt + (a["P_KVz"] + a["P_USV"] + a["P_MontStandort"] + P_gw * (a["P_UCG"] + a["P_DAC"]) + a["P_Agg"] * _ceil((P_gw + tech) / a["Ports_Agg"])) * EK
        R = (a["Uplink_Monat"] * 12 * max(1, _ceil(s["kunden"] * a["Bandbreite"] / a["Ueberbuchung"] / a["Uplink_Kap"])) + a["Strom_Standort"]
             + P_gw * a["Strom_GW"] + tech * a["Strom_Mast"]) * EK + Q * a["Wartung"]
        s.update(aps=aps, masten=masten, tech=tech, leitung=leitung, inv_sparte=N, lfd_sparte=tech * a["Strom_Mast"] * EK + N * a["Wartung"],
                 gw_eigen=P_gw, inv_eigen=Q, lfd_eigen=R)
    # Standorte
    standorte = []
    for s in A:
        if s["C"] != s["nr"]:
            continue
        mit = [t for t in A if t["C"] == s["nr"]]
        parz = sum(t["parz"] for t in mit)
        gw = _ceil(parz / PG)
        straenge = s["tech"] + sum(1 for t in A if t["D"] == s["nr"])
        agg = _ceil((gw + straenge) / a["Ports_Agg"])
        kunden = sum(t["kunden"] for t in mit)
        bedarf = kunden * a["Bandbreite"] / a["Ueberbuchung"]
        ans = max(1, _ceil(bedarf / a["Uplink_Kap"]))
        inv = gw * (a["P_UCG"] + a["P_DAC"]) * EK + (a["P_KVz"] + a["P_USV"] + a["P_MontStandort"] + agg * a["P_Agg"]) * EK
        lfd = (ans * a["Uplink_Monat"] * 12 + a["Strom_Standort"] + gw * a["Strom_GW"]) * EK + inv * a["Wartung"]
        pr = f"Achtung: mehr als {int(a['Max_GW'])} Gateways" if gw > a["Max_GW"] else (f"OK – {ans} Internet-Anschlüsse nötig" if ans > 1 else "OK")
        standorte.append({"nr": s["nr"], "name": s["name"], "sparten": len(mit), "namen": [t["name"] for t in sorted(mit, key=lambda t: t["sort"])],
                          "parz": parz, "gw": gw, "belegung": parz / (gw * PG) if gw else 0, "straenge": straenge, "agg": agg, "kunden": round(kunden, 1),
                          "bedarf": round(bedarf), "anschluesse": ans, "inv": round(inv, 2), "lfd": round(lfd, 2), "pruefung": pr})
    st_idx = {x["nr"]: x for x in standorte}
    # Einnahmen und Ergebnis
    quelle, preis, anteile, tarife = gwp_preis(d, a)
    netto = (lambda v: v) if a["KU"] == 1 else (lambda v: v / (1 + a["USt"]))
    ist = {}
    try:
        for z in akt_kalkulation(d)["zeilen"]:
            if z["gebucht"]:
                ist[_norm(z["name"])] = z
    except Exception:
        pass
    zeilen = []
    for s in A:
        so = st_idx.get(s["C"])
        anteil = s["parz"] / so["parz"] if so and so["parz"] else 0
        einnahme = s["kunden"] * preis
        inv = s["inv_sparte"] + anteil * (so["inv"] if so else 0)
        lfd = s["lfd_sparte"] + anteil * (so["lfd"] if so else 0) + netto(einnahme) * a["Zahlung"]
        db = netto(einnahme) - lfd
        treffer = next((z for k, z in ist.items() if k and (k == _norm(s["name"]) or (len(k) > 4 and (k in _norm(s["name"]) or _norm(s["name"]) in k)))), None)
        zeilen.append({
            "nr": s["nr"], "name": s["name"], "adresse": s["adresse"], "stufe": s["stufe"], "parz": s["parz"], "leer": s["leer"], "parz_konzept": s["parz_konzept"],
            "standort": s["C"], "zuleitung": s["D"], "sort": s["sort"], "rolle": s["rolle"], "versorgt": s["versorgt"], "gw_von": s["gw_von"], "gw_bis": s["gw_bis"],
            "km": round(s["km"], 3), "faser_zul": round(s["faser_zul"]), "pruefung": s["pruefung"],
            "quote": s["quote"], "herkunft": s["herkunft"], "q_heute": s["q_heute"], "q5": s["q5"], "kunden": round(s["kunden"], 1),
            "einnahme": round(einnahme, 2), "einnahme_monat": round(einnahme / 12, 2), "je_tarif": {k: round(s["kunden"] * v, 1) for k, v in anteile.items()},
            "aps": s["aps"], "masten": s["masten"], "investition": round(inv, 2), "laufend": round(lfd, 2), "db": round(db, 2),
            "amortisation": round(inv / db, 1) if db > 0 else None, "inv_kunde": round(inv / s["kunden"]) if s["kunden"] else None,
            "ist_gebucht": treffer["gebucht"] if treffer else None, "ist_einnahme": treffer["umsatz_brutto"] if treffer else None,
            "w": {k: s["w"].get(k) for k in GWP_WAHL if s["w"].get(k) is not None},
            "vs_standort": s["vs_standort"], "vs_zuleitung": s["vs_zuleitung"]})
    S = lambda liste, k: sum(float(x[k] or 0) for x in liste)
    parz = S(A, "parz")
    kunden = S(A, "kunden")
    einnahme = S(zeilen, "einnahme")
    inv_plan = S(A, "inv_sparte") + S(standorte, "inv")
    lfd_plan = S(A, "lfd_sparte") + S(standorte, "lfd") + netto(einnahme) * a["Zahlung"]
    lfd_plan_ohne_zahlung = S(A, "lfd_sparte") + S(standorte, "lfd")
    db = netto(einnahme) - lfd_plan
    fehler = sum(1 for s in A if s["pruefung"].startswith("Fehler"))
    gesamt = {
        "sparten": len(A), "parzellen": int(parz), "leerq": S(A, "leer") / parz if parz else 0, "leerq5": S(A, "leer5") / parz if parz else 0,
        "quote": kunden / parz if parz else 0, "kunden": round(kunden, 1),
        "preis": round(preis, 2), "preis_quelle": quelle, "einnahme": round(einnahme, 2), "einnahme_monat": round(einnahme / 12, 2), "einnahme_netto": round(netto(einnahme), 2),
        "je_tarif": {k: {"kunden": round(kunden * v, 1), "einnahme": round(kunden * v * next(t["preis"] for t in tarife if t["name"] == k), 2)} for k, v in anteile.items()},
        "standorte": len(standorte), "gateways": int(S(standorte, "gw")), "anschluesse": int(S(standorte, "anschluesse")), "faser": round(S(A, "faser_zul")),
        "fehler": fehler, "investition": round(inv_plan, 2), "laufend": round(lfd_plan_ohne_zahlung, 2), "zahlung": round(netto(einnahme) * a["Zahlung"], 2), "db": round(db, 2),
        "amortisation": round(inv_plan / db, 1) if db > 0 else None, "inv_kunde": round(inv_plan / kunden) if kunden else None,
        "eigen": {"standorte": len(A), "gateways": int(S(A, "gw_eigen")), "anschluesse": len(A), "investition": round(S(A, "inv_eigen"), 2), "laufend": round(S(A, "lfd_eigen"), 2)},
        "plan_laufend_ohne_zahlung": round(lfd_plan_ohne_zahlung, 2), "jahre": a["Jahre"],
        "ist_gebucht": sum(z["ist_gebucht"] or 0 for z in zeilen), "ist_einnahme": round(sum(z["ist_einnahme"] or 0 for z in zeilen), 2),
        "modus": "manuell je Sparte / " + ("feste Quote " + f"{a['Quote_fest']:.0%}" if a["Quote_Modus"] == 2 else ("aus Alter und Leerstand, in 5 Jahren" if a["Szenario"] == 2 else "aus Alter und Leerstand, heute")),
    }
    gesamt["eigen"]["zeitraum"] = round(gesamt["eigen"]["investition"] + gesamt["eigen"]["laufend"] * a["Jahre"], 2)
    gesamt["zeitraum"] = round(inv_plan + lfd_plan_ohne_zahlung * a["Jahre"], 2)
    log = [f"{len(A)} Sparten · {len(standorte)} Gateway-Standorte · {gesamt['gateways']} Gateways · {gesamt['kunden']:.0f} Kunden (Quote {gesamt['quote']:.1%})"]
    if fehler:
        log.append(f"⚠ {fehler} Sparte(n) mit Fehler in der Zuordnung – Spalte „Prüfung“.")
    if any(x["pruefung"].startswith("Achtung") for x in standorte):
        log.append(f"⚠ Mindestens ein Standort hat mehr als {int(a['Max_GW'])} Gateways.")
    return {"zeilen": zeilen, "standorte": standorte, "gesamt": gesamt, "tarife": tarife, "annahmen": a, "felder": GWP_FELDER,
            "quelle_daten": "Excel-Import" if (d.get("gwplan") or {}).get("anlagen") else "Kleingartenentwicklungskonzept 2040 (eingebaut)", "log": log}


def _gwp_int(v, text, lo, hi):
    if v in (None, ""):
        return None
    try:
        x = float(str(v).replace(",", "."))
    except ValueError:
        raise Fehler(f"{text}: bitte eine Zahl eintragen.")
    if x != int(x) or not lo <= x <= hi:
        raise Fehler(f"{text}: ganze Zahl von {lo} bis {hi}.")
    return int(x)


def akt_gwplan_sparte(d, b):
    nrs = {s["nr"]: s for s in gwp_anlagen(d)}
    try:
        nr = int(b.get("nr"))
    except (TypeError, ValueError):
        nr = None
    if nr not in nrs:
        raise Fehler("Sparte unbekannt.")
    g = d.setdefault("gwplan", {})
    w = dict((g.setdefault("wahl", {})).get(str(nr)) or {})
    for feld, wert in b.items():
        if feld not in GWP_WAHL:
            continue
        if feld in ("standort", "zuleitung"):
            v = _gwp_int(wert, "Standort" if feld == "standort" else "Zuleitung von", 1, 9999)
            if v is not None and v not in nrs:
                raise Fehler(f"Sparte Nr. {v} gibt es nicht.")
        elif feld == "reihenfolge":
            v = _gwp_int(wert, "Reihenfolge", 1, 999)
        elif feld == "quote":
            v = _zahl_oder_none(wert, "Quote manuell")
            if v is not None:
                if v > 100:
                    raise Fehler("Quote manuell: höchstens 100 %.")
                v = v / 100
        elif feld == "parz":
            v = _gwp_int(wert, "Parzellen", 1, 2000)
        elif feld == "leer":
            v = _gwp_int(wert, "Leerstand", 0, 2000)
        else:
            v = _zahl_oder_none(wert, {"entfernung": "Entfernung (m)", "aps": "Access Points", "masten": "Masten", "leitung": "Leitungsweg (m)"}[feld])
        if v is None:
            w.pop(feld, None)
        else:
            w[feld] = v
    p = w.get("parz", nrs[nr]["parz"])
    if w.get("leer", nrs[nr]["leer"]) > p:
        raise Fehler("Leerstand kann nicht größer sein als die Parzellenzahl.")
    if w:
        g["wahl"][str(nr)] = w
    else:
        g["wahl"].pop(str(nr), None)
    speichere(d)
    return gwplan_berechnen(d)


def akt_gwplan_annahmen(d, b):
    g = d.setdefault("gwplan", {})
    neu = dict(g.get("annahmen") or {})
    prozent = {k for _, gr in GWP_FELDER for k, _, e in gr if e == "%"}
    texte = {k: t for _, gr in GWP_FELDER for k, t, _ in gr}
    for k, v in (b.get("annahmen") or {}).items():
        if k not in GWP_STANDARD:
            continue
        x = _zahl_oder_none(v, texte.get(k, k))
        if x is None:
            neu.pop(k, None)
            continue
        neu[k] = x / 100 if k in prozent else x
    probe = {**GWP_STANDARD, **neu}
    if probe["PG"] < 1 or probe["Ueberbuchung"] < 1 or probe["Uplink_Kap"] <= 0 or probe["Ports_Agg"] < 1 or probe["Parz_je_AP"] <= 0 or probe["AP_je_Mast"] <= 0:
        raise Fehler("Parzellen je Gateway, Überbuchung, Uplink-Kapazität, Ports und Faustregeln müssen größer als 0 sein.")
    if probe["Quote_Modus"] not in (1, 2) or probe["Szenario"] not in (1, 2) or probe["Vorschlag_nutzen"] not in (0, 1) or probe["KU"] not in (0, 1):
        raise Fehler("Modus und Szenario sind 1 oder 2, Vorschlag und Kleinunternehmer 0 oder 1.")
    g["annahmen"] = neu
    if "tarifmix" in b and isinstance(b["tarifmix"], dict):
        namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
        g["tarifmix"] = {k: _zahl_oder_none(v, f"Anteil {k}") or 0 for k, v in b["tarifmix"].items() if k in namen}
    if b.get("preis_quelle") in ("tarife", "fest"):
        g["preis_quelle"] = b["preis_quelle"]
    speichere(d)
    r = gwplan_berechnen(d)
    r["log"] = ["✔ Einstellungen gespeichert."] + r["log"]
    return r


def akt_gwplan_zuruecksetzen(d, was):
    g = d.setdefault("gwplan", {})
    if was == "wahl":
        g["wahl"] = {}
        txt = "✔ Eigene Zuordnungen entfernt – es gilt wieder der Vorschlag."
    elif was == "annahmen":
        g.pop("annahmen", None); g.pop("tarifmix", None); g.pop("preis_quelle", None)
        txt = "✔ Einstellungen auf Standard zurückgesetzt."
    elif was == "daten":
        g.pop("anlagen", None)
        txt = "✔ Wieder mit den eingebauten Daten aus dem Kleingartenentwicklungskonzept."
    else:
        raise Fehler("Unbekannt.")
    speichere(d)
    r = gwplan_berechnen(d)
    r["log"] = [txt] + r["log"]
    return r


def _xlsx_namen(roh_bytes):
    """definierte Namen einer xlsx → {Name: (Blatt, Zelle)}"""
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    z = zipfile.ZipFile(io.BytesIO(roh_bytes))
    aus = {}
    for n in ET.fromstring(z.read("xl/workbook.xml")).iter(M + "definedName"):
        m = re.match(r"^'?(.+?)'?!\$?([A-Z]+)\$?(\d+)$", (n.text or "").strip())
        if m:
            aus[n.get("name")] = (m.group(1), m.group(2) + m.group(3))
    return aus


def akt_gwplan_import(d, roh):
    """Kleingarten_Gateway_Planung.xlsx: Anlagen (Daten + gelbe Spalten) und Annahmen übernehmen"""
    namen, lies = _xlsx_blaetter(roh)
    if not {"Anlagen", "Netz", "Annahmen"} <= set(namen):
        raise Fehler("Das ist nicht die Gateway-Planung (Kleingarten_Gateway_Planung.xlsx) – es fehlen die Blätter „Anlagen“, „Netz“ oder „Annahmen“.")
    an = lies("Anlagen") or {}
    zahl = lambda v: v if isinstance(v, (int, float)) else None
    anlagen, wahl = [], {}
    felder = {"S": "standort", "T": "zuleitung", "U": "reihenfolge", "V": "entfernung", "W": "quote", "X": "aps", "Y": "masten", "Z": "leitung"}
    for r in range(5, 1000):
        nr = zahl(an.get(f"A{r}"))
        if nr is None:
            if an.get(f"B{r}") is None:
                break
            continue
        nr = int(nr)
        parz = zahl(an.get(f"F{r}"))
        if not parz:
            raise Fehler(f"Anlagen Zeile {r}: Parzellenzahl fehlt.")
        vs, vz = zahl(an.get(f"Q{r}")), zahl(an.get(f"R{r}"))
        anlagen.append({"nr": nr, "name": str(an.get(f"B{r}") or f"Sparte {nr}"), "adresse": str(an.get(f"C{r}") or ""), "stufe": str(an.get(f"D{r}") or "D"),
                        "eigentum": str(an.get(f"E{r}") or ""), "parz": int(parz), "parz_konzept": int(zahl(an.get(f"P{r}")) or parz),
                        "leer": int(zahl(an.get(f"G{r}")) or 0), "flaeche": float(zahl(an.get(f"H{r}")) or 0),
                        "alter": [float(zahl(an.get(f"{c}{r}")) or 0) for c in "IJKLM"], "x": float(zahl(an.get(f"N{r}")) or 0), "y": float(zahl(an.get(f"O{r}")) or 0),
                        "vs_standort": int(vs) if vs else nr, "vs_zuleitung": int(vz) if vz else None})
        w = {}
        for c, f in felder.items():
            v = zahl(an.get(f"{c}{r}"))
            if v is not None:
                w[f] = int(v) if f in ("standort", "zuleitung", "reihenfolge") else float(v)
        if w:
            wahl[str(nr)] = w
    if not anlagen:
        raise Fehler("Im Blatt „Anlagen“ stehen keine Sparten.")
    nrs = {s["nr"] for s in anlagen}
    for k, w in wahl.items():
        for f in ("standort", "zuleitung"):
            if w.get(f) is not None and w[f] not in nrs:
                raise Fehler(f"Sparte {k}: {f} Nr. {w[f]} gibt es in der Liste nicht.")
    neu = {}
    try:
        dn = _xlsx_namen(roh)
        cache = {}
        for k in GWP_STANDARD:
            if k in dn:
                blatt, zelle = dn[k]
                if blatt not in cache:
                    cache[blatt] = lies(blatt) or {}
                v = cache[blatt].get(zelle)
                if isinstance(v, (int, float)):
                    neu[k] = float(v)
    except (KeyError, ET.ParseError):
        pass
    g = d.setdefault("gwplan", {})
    g["anlagen"], g["wahl"] = anlagen, wahl
    if neu:
        g["annahmen"] = {k: v for k, v in neu.items() if v != GWP_STANDARD[k]}
    speichere(d)
    r = gwplan_berechnen(d)
    r["log"] = [f"✔ Aus Excel übernommen: {len(anlagen)} Sparten, {len(wahl)} mit eigener Zuordnung, {len(neu)} Annahmen."] + r["log"]
    journal(f"Netzplanung aus Excel übernommen: {len(anlagen)} Sparten")
    return r

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

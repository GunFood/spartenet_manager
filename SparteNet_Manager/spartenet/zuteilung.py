"""SparteNet Manager – Gateway-Zuteilung nach Buchung („dynamisch“)

Eine Parzelle bekommt ihren Platz an einem Gateway erst, wenn sie bucht: am ersten Gateway ihres Standorts, auf dem noch Platz ist
(Netzplanung „Parzellen je Gateway“, Standard 55). Erst wenn Gateway 1 voll ist, kommt Gateway 2 dran. Wird die Buchung gelöscht,
wird der Platz frei, sobald das Netz am Gateway entfernt ist – die nächste Buchung füllt dann zuerst diese Lücke.

Die VLAN-ID bleibt fest an der Parzelle (Schema 4.7: 1000 + 200·(Block−1) + Parzelle, eindeutig je Standort), deshalb dürfen die Parzellen
einer Sparte auf beliebige Gateways desselben Standorts verteilt sein. Eine einmal zugeteilte Parzelle wird nie automatisch umgezogen.
Dienstnetze (Vorstand, Gäste, Technik) liegen in diesem Modus am ersten Gateway des Standorts.

Am Gateway ändert die Zuteilung selbst nichts: Netze anlegen bzw. entfernen geht nur über die Vorschau im Reiter „Einrichten“
und nach Bestätigung.

Status je Parzelle:  anlegen – gebucht, Netz noch nicht am Gateway · aktiv – Netz am Gateway · entfernen – Buchung gelöscht, Netz noch am Gateway
"""
from .netzplanung import *  # noqa: F401,F403 – alle Namen der vorherigen Module

ZT_STATUS = {"anlegen": "gebucht – Netz anlegen", "aktiv": "Netz am Gateway", "entfernen": "Buchung gelöscht – Netz entfernen"}
_PAZ_RE = re.compile(r"^([A-Z0-9]{1,5})-Paz\.(\d{3})$")


def zuteilung_daten(d):
    z = d.get("zuteilung") if isinstance(d.get("zuteilung"), dict) else {}
    if not isinstance(z.get("p"), dict):
        z["p"] = {}
    d["zuteilung"] = z
    return z


def zuteilung_an(d):
    return bool((d.get("zuteilung") or {}).get("an"))


def _schluessel(kz, p):
    return f"{kz}-{int(p)}"


def _sparten_info(r):
    """Kürzel → Zeile der Netzplanung (Standort, Sparten-ID, VLAN-Block, Parzellen)"""
    return {z["kz"]: z for z in r["zeilen"]}


def _belegung(z, standort):
    zahl = {}
    for e in z["p"].values():
        if e.get("standort") == standort:
            zahl[e["gw"]] = zahl.get(e["gw"], 0) + 1
    return zahl


def _gw_waehlen(d, z, r, standort, bevorzugt=None):
    a = gwp_annahmen(d)
    pg = max(1, int(a["PG"]))
    zahl = _belegung(z, standort)
    if bevorzugt and zahl.get(bevorzugt, 0) < pg:
        return bevorzugt, ""
    g = 1
    while zahl.get(g, 0) >= pg:
        g += 1
    st = next((x for x in r["standorte"] if x["nr"] == standort), None)
    geplant = (st or {}).get("gw") or 1
    hinweis = f"Gateway {g} am Standort „{(st or {}).get('name', standort)}“ wird gebraucht – in der Netzplanung sind {geplant} geplant." if g > geplant else ""
    return g, hinweis


def zuteilung_buchung(d, kz, p, tarif, r=None, bevorzugt=None):
    """Buchung bzw. Kündigung einer Parzelle in der Zuteilung vermerken; gibt einen Hinweistext zurück (oder "")"""
    z = zuteilung_daten(d)
    k = _schluessel(kz, p)
    e = z["p"].get(k)
    if tarif:
        if e:
            if e["status"] == "entfernen":
                e["status"], e["seit"] = "aktiv", time.strftime("%Y-%m-%d %H:%M")
            return ""
        r = r or gwplan_berechnen(d)
        info = _sparten_info(r).get(kz)
        if not info:
            return f"{kz}: Sparte nicht in der Netzplanung – Parzelle {p} bekommt kein Gateway."
        if not 1 <= int(p) <= int(info["parz"]):
            return f"{kz}: Parzelle {p} gibt es laut Netzplanung nicht (1–{info['parz']})."
        g, hinweis = _gw_waehlen(d, z, r, info["standort"], bevorzugt)
        z["p"][k] = {"kz": kz, "p": int(p), "standort": info["standort"], "gw": g, "status": "anlegen", "seit": time.strftime("%Y-%m-%d %H:%M"),
                     "vlan": vlan_parz(info["vlanblock"], p)}
        journal(f"Gateway-Zuteilung: {kz} Parzelle {p} → Standort {info['standort']}, Gateway {g}")
        return hinweis
    if e:
        if e["status"] == "anlegen":
            del z["p"][k]
            journal(f"Gateway-Zuteilung: {kz} Parzelle {p} freigegeben (Netz war noch nicht angelegt)")
        else:
            e["status"], e["seit"] = "entfernen", time.strftime("%Y-%m-%d %H:%M")
            journal(f"Gateway-Zuteilung: {kz} Parzelle {p} – Netz am Gateway {e['gw']} kann entfernt werden")
    return ""


def zuteilung_teile(d, r, standort, gw):
    """Sparten-Liste für den Plan eines Gateways im dynamischen Modus (Parzellen = Status anlegen/aktiv)"""
    z = zuteilung_daten(d)
    st = next((x for x in r["standorte"] if x["nr"] == standort), None)
    mit = sorted([t for t in r["zeilen"] if t["standort"] == standort], key=lambda t: t["sort"])
    teile = []
    for t in mit:
        liste = sorted(e["p"] for e in z["p"].values() if e["kz"] == t["kz"] and e.get("standort") == standort and e["gw"] == gw and e["status"] in ("anlegen", "aktiv"))
        if liste or gw == 1:
            teile.append({"name": t["name"], "kz": t["kz"], "sid": t["nr"], "n": t["parz"], "block": t["vlanblock"], "parzellen": liste, "dienst": gw == 1})
    if not teile and st:
        raise Fehler("Diesem Gateway ist noch keine Parzelle zugeteilt.")
    return teile


def _plan_nachziehen(d):
    """aktive Planung neu bilden, wenn sie aus der Zuteilung stammt (Reiter „Planung“ zeigt dann die aktuellen Parzellen)"""
    p = d.get("plan") or {}
    if not (p.get("dynamisch") and p.get("standort") and p.get("standort_gw")):
        return
    try:
        neu = gwplan_gateway(d, p["standort"], p["standort_gw"])
        plan_berechnen(neu)
        neu["praefix"] = p.get("praefix") or neu["praefix"]
        d["plan"] = neu
    except Fehler as e:
        LOG.warning("Planung aus Gateway-Zuteilung nicht aktualisiert: %s", e)


def _ereignis(typ, daten, d):
    if typ not in ("buchung", "kuendigung") or d is None or not zuteilung_an(d):
        return
    hinweis = zuteilung_buchung(d, str(daten.get("sparte") or ""), int(daten.get("parzelle") or 0), daten.get("tarif") if typ == "buchung" else "")
    if hinweis:
        LOG.warning("Gateway-Zuteilung: %s", hinweis)
        journal("⚠ " + hinweis)
    _plan_nachziehen(d)
    speichere(d)


EREIGNIS_EMPFAENGER.append(_ereignis)   # vor den Automationen eingetragen → {gateway} ist dort schon bekannt


def zuteilung_abgleichen(d, bestand=False):
    """alle Buchungen ↔ Zuteilung; bestand=True (beim Einschalten): gebuchte Parzellen bevorzugt dort, wo sie laut Netzplanung schon liegen"""
    z = zuteilung_daten(d)
    r = gwplan_berechnen(d)
    info = _sparten_info(r)
    gebucht = {(kz, int(p)): t for kz, b in (d.get("buchungen") or {}).items() for p, t in b.items() if t and str(p).isdigit()}
    log, neu, frei = [], 0, 0
    for (kz, p), t in sorted(gebucht.items(), key=lambda x: (info.get(x[0][0], {}).get("standort", 9999), info.get(x[0][0], {}).get("sort", 9999), x[0][1])):
        if _schluessel(kz, p) in z["p"] and z["p"][_schluessel(kz, p)]["status"] != "entfernen":
            continue
        bev = None
        if bestand and kz in info:
            bev = next((x["gw"] for x in info[kz]["teile"] if x["p_von"] <= p <= x["p_bis"]), None)
        h = zuteilung_buchung(d, kz, p, t, r, bevorzugt=bev)
        neu += 1
        if h and h not in log:
            log.append("⚠ " + h)
    for k, e in list(z["p"].items()):
        if (e["kz"], e["p"]) not in gebucht and e["status"] != "entfernen":
            zuteilung_buchung(d, e["kz"], e["p"], "")
            frei += 1
    _plan_nachziehen(d)
    return [f"Abgleich mit den Buchungen: {neu} Parzelle(n) zugeteilt, {frei} freigegeben bzw. zum Entfernen markiert."] + log


def akt_zuteilung(d):
    z = zuteilung_daten(d)
    r = gwplan_berechnen(d)
    pg = max(1, int(gwp_annahmen(d)["PG"]))
    namen = {t["kz"]: t["name"] for t in r["zeilen"]}
    standorte = []
    for st in r["standorte"]:
        eintr = [e for e in z["p"].values() if e.get("standort") == st["nr"]]
        n_sp = st["sparten"]
        gws = []
        for g in range(1, max([st["gw"]] + [e["gw"] for e in eintr]) + 1):
            hier = [e for e in eintr if e["gw"] == g]
            je = {}
            for e in sorted(hier, key=lambda e: (e["kz"], e["p"])):
                je.setdefault(e["kz"], []).append({"p": e["p"], "status": e["status"], "vlan": e.get("vlan")})
            dienst = n_sp * DIENST_JE_SPARTE if g == 1 else 0
            gws.append({"gw": g, "belegt": len(hier), "frei": max(0, pg - len(hier)), "anlegen": sum(1 for e in hier if e["status"] == "anlegen"),
                        "entfernen": sum(1 for e in hier if e["status"] == "entfernen"), "dienstnetze": dienst, "vlans": len(hier) + dienst,
                        "geplant": g <= st["gw"], "sparten": [{"kz": k, "name": namen.get(k, k), "parzellen": v} for k, v in je.items()]})
        standorte.append({"nr": st["nr"], "name": st["name"], "gw_geplant": st["gw"], "gebucht": len(eintr), "gateways": gws})
    plan = d.get("plan") or {}
    return {"an": bool(z.get("an")), "seit": z.get("seit"), "pg": pg, "standorte": standorte, "status_text": ZT_STATUS,
            "aktiv_gateway": {"standort": plan.get("standort"), "gw": plan.get("standort_gw"), "name": plan.get("gatewayname"), "dynamisch": bool(plan.get("dynamisch"))},
            "log": [f"Gateway-Zuteilung nach Buchung: {'eingeschaltet' if z.get('an') else 'aus'} · {len(z['p'])} Parzelle(n) zugeteilt"]}


def akt_zuteilung_einstellen(d, b, ich):
    z = zuteilung_daten(d)
    log = []
    if "an" in b:
        an = bool(b["an"])
        if an and not z.get("an"):
            z["an"], z["seit"] = True, time.strftime("%Y-%m-%d %H:%M")
            log += zuteilung_abgleichen(d, bestand=True)
            journal(f"Gateway-Zuteilung nach Buchung eingeschaltet durch {ich}")
        elif not an and z.get("an"):
            z["an"] = False
            p = d.get("plan") or {}
            if p.get("dynamisch"):
                p.pop("dynamisch", None)
                log.append("ℹ Die aktive Planung bleibt mit den zuletzt zugeteilten Parzellen stehen – für die feste Aufteilung „VLAN-Plan je Gateway → Übernehmen“ erneut wählen.")
            journal(f"Gateway-Zuteilung nach Buchung ausgeschaltet durch {ich}")
    if b.get("abgleichen"):
        if not z.get("an"):
            raise Fehler("Erst die Gateway-Zuteilung nach Buchung einschalten.")
        log += zuteilung_abgleichen(d)
    speichere(d)
    x = akt_zuteilung(d)
    x["log"] = ["✔ Gespeichert."] + log + x["log"]
    return x


# ---- am aktiven Gateway: Netze nach Zuteilung anlegen bzw. entfernen (Vorschau → Bestätigung) ------------------
def _aktiv(d):
    p = d.get("plan") or {}
    if not zuteilung_an(d):
        raise Fehler("Die Gateway-Zuteilung nach Buchung ist aus (Reiter „Netzplanung“).")
    if not (p.get("dynamisch") and p.get("standort") and p.get("standort_gw")):
        raise Fehler("Die aktive Planung stammt nicht aus der Gateway-Zuteilung – unter „Netzplanung → VLAN-Plan je Gateway“ den Standort und das Gateway wählen und „Übernehmen“.")
    return int(p["standort"]), int(p["standort_gw"])


def _lage(d):
    standort, gw = _aktiv(d)
    z = zuteilung_daten(d)
    r = gwplan_berechnen(d)
    info = _sparten_info(r)
    am_standort = {t["kz"] for t in r["zeilen"] if t["standort"] == standort}
    g = Gateway(d)
    ist = {n.get("name"): n for n in g.legacy("GET", "rest/networkconf")}
    anlegen, entfernen, ueberzaehlig, korrigiert = [], [], [], 0
    for e in sorted(z["p"].values(), key=lambda e: (e["kz"], e["p"])):
        if e.get("standort") != standort or e["gw"] != gw:
            continue
        name = NETZ_PARZELLE.format(kz=e["kz"], p=e["p"])
        da = name in ist
        if e["status"] in ("anlegen", "aktiv"):
            if da and e["status"] == "anlegen":
                e["status"] = "aktiv"; korrigiert += 1
            elif not da:
                if e["status"] == "aktiv":
                    e["status"] = "anlegen"; korrigiert += 1
                anlegen.append({"kz": e["kz"], "p": e["p"], "netz": name, "vlan": e.get("vlan")})
        elif e["status"] == "entfernen":
            if da:
                entfernen.append({"kz": e["kz"], "p": e["p"], "netz": name, "vlan": ist[name].get("vlan"), "id": ist[name].get("_id"), "grund": "Buchung gelöscht"})
            else:
                del z["p"][_schluessel(e["kz"], e["p"])]; korrigiert += 1    # Netz schon weg → Platz frei
    soll_hier = {NETZ_PARZELLE.format(kz=e["kz"], p=e["p"]) for e in z["p"].values() if e.get("standort") == standort and e["gw"] == gw}
    for name, n in ist.items():
        m = _PAZ_RE.match(str(name or ""))
        if m and m.group(1) in am_standort and name not in soll_hier:
            kz, p = m.group(1), int(m.group(2))
            e = z["p"].get(_schluessel(kz, p))
            grund = f"Parzelle ist Gateway {e['gw']} zugeteilt" if e else "Parzelle hat keine Buchung"
            ueberzaehlig.append({"kz": kz, "p": p, "netz": name, "vlan": n.get("vlan"), "id": n.get("_id"), "grund": grund})
    if korrigiert:
        _plan_nachziehen(d)
        speichere(d)
    return g, standort, gw, info, anlegen, entfernen, ueberzaehlig


def akt_zuteilung_gateway(d, b):
    """Vorschau (ohne „ausfuehren“) bzw. Ausführen der ausgewählten Netze am aktiven Gateway"""
    b = b or {}
    g, standort, gw, info, anlegen, entfernen, ueberzaehlig = _lage(d)
    name = (d.get("plan") or {}).get("gatewayname") or f"Standort {standort}, Gateway {gw}"
    if not b.get("ausfuehren"):
        return {"gateway": name, "anlegen": anlegen, "entfernen": entfernen, "ueberzaehlig": ueberzaehlig,
                "log": [f"{name}: {len(anlegen)} Netz(e) anzulegen, {len(entfernen)} nach gelöschter Buchung zu entfernen"
                        + (f", {len(ueberzaehlig)} weitere Parzellennetze ohne Zuteilung zu diesem Gateway" if ueberzaehlig else "") + "."]}
    wahl_an = set(b.get("anlegen") or [])
    wahl_weg = set(b.get("entfernen") or [])
    ok_an = {x["netz"] for x in anlegen}
    ok_weg = {x["netz"]: x for x in entfernen + ueberzaehlig}
    if not wahl_an <= ok_an or not wahl_weg <= set(ok_weg):
        raise Fehler("Die Auswahl passt nicht mehr zum Stand am Gateway – bitte erneut „Vorschau“ wählen.")
    if not wahl_an and not wahl_weg:
        raise Fehler("Nichts ausgewählt.")
    log = []
    # anlegen: je Sparte Netz anlegen und – wenn vorhanden – gleich das Passwort der Parzelle ins Pächter-WLAN
    for kz in sorted({x["kz"] for x in anlegen if x["netz"] in wahl_an}):
        netze = [x["netz"] for x in anlegen if x["kz"] == kz and x["netz"] in wahl_an]
        parz = [x["p"] for x in anlegen if x["kz"] == kz and x["netz"] in wahl_an]
        log += akt_netze(d, kz, True, False, namen=netze)["log"]
        pw = {str(z.get("Parzelle")) for z in lese_ppsk(kz) if z.get("Passwort")}
        mit_pw = [p for p in parz if str(p) in pw]
        if mit_pw:
            try:
                log += akt_uebertragen(d, kz, mit_pw, [], True)["log"]
            except Fehler as e:
                log.append(f"ℹ Passwörter {kz}: {e} – bitte im Reiter „Übertragen“ nachholen.")
        if len(mit_pw) < len(parz):
            log.append(f"ℹ {kz}: für Parzelle {', '.join(str(p) for p in parz if p not in mit_pw)} gibt es noch kein Passwort – „Einrichten“ Schritt 3.")
    # entfernen: erst die Zugänge (PPSK) im Pächter-WLAN, dann das Netz
    weg = [ok_weg[n] for n in sorted(wahl_weg)]
    if weg:
        plan = plan_berechnen(d["plan"])
        wlans = g.legacy("GET", "rest/wlanconf")
        for kz in sorted({x["kz"] for x in weg}):
            ids = {x["id"] for x in weg if x["kz"] == kz}
            ssid = WLAN_PAECHTER.format(kz=kz, pre=plan["praefix"])
            for w in wlans:
                keys = w.get("private_preshared_keys") or []
                rest = [k for k in keys if k.get("networkconf_id") not in ids]
                if len(rest) != len(keys):
                    _sicherung_schreiben(kz, w, w.get("name") or ssid)
                    if not _ppsk_schreiben_und_pruefen(g, w, w.get("name") or ssid, rest):
                        raise Fehler(f"Zugänge im WLAN „{w.get('name')}“ ließen sich nicht sicher entfernen – Abbruch, kein Netz gelöscht.")
                    log.append(f"✔ {len(keys) - len(rest)} Zugang/Zugänge im WLAN „{w.get('name')}“ entfernt (Sicherung angelegt).")
        z = zuteilung_daten(d)
        for x in weg:
            try:
                g.legacy("DELETE", f"rest/networkconf/{x['id']}")
                log.append(f"✔ entfernt: {x['netz']} (VLAN {x['vlan']})")
                e = z["p"].get(_schluessel(x["kz"], x["p"]))
                if e and e.get("standort") == standort and e["gw"] == gw:
                    del z["p"][_schluessel(x["kz"], x["p"])]
            except Fehler as e:
                log.append(f"✖ {x['netz']}: {e}")
        journal(f"Gateway-Zuteilung {name}: {len(weg)} Netz(e) entfernt ({', '.join(x['netz'] for x in weg[:20])})")
    # Stand nachlesen
    _lage(d)
    _plan_nachziehen(d)
    speichere(d)
    return {"log": log + ["Fertig – mit „Vorschau“ den neuen Stand prüfen."]}


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

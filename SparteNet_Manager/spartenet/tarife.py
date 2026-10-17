"""SparteNet Manager – Tarife: Bandbreite per QoS-Regel, Netzgröße per Subnetz/DHCP"""
from .voucher import *  # noqa: F401,F403 – alle Namen der vorherigen Module


QOS_TARIF, QOS_NETZ = "SparteNet-Tarif-", "SparteNet-Netz-"
NETZ_ZWECK_AUS = {"wan", "remote-user-vpn", "site-vpn", "vpn-client", "vlan-only"}
TARIF_SICHERUNG = "SparteNet_Sicherung_Tarife_"


def _zahl(x):
    return int(x) if float(x) == int(float(x)) else round(float(x), 1)


def dhcp_bereich(router, praefix, geraete=0):
    """Neues Subnetz und DHCP-Bereich. Router-IP bleibt gleich. Wie am Gateway üblich:
    /24 und größer → DHCP ab .6, kleinere Netze → direkt nach dem Router. geraete = Größe des DHCP-Bereichs (0 = alles)."""
    r = ipaddress.ip_address(router)
    netz = ipaddress.ip_network(f"{router}/{praefix}", strict=False)
    erste, letzte = netz.network_address + 1, netz.broadcast_address - 1
    if not erste <= r <= letzte:
        raise Fehler(f"Router-IP {router} ist in einem /{praefix} nicht möglich.")
    start = max(r + 1, netz.network_address + 6) if praefix <= 24 else r + 1
    if start > letzte:
        raise Fehler(f"Router-IP {router}: in einem /{praefix} bleibt kein Platz für Endgeräte.")
    platz = int(letzte) - int(start) + 1
    stop = letzte
    if geraete:
        if geraete > platz:
            raise Fehler(f"/{praefix} mit Router {router}: Platz für {platz} Endgeräte, der Tarif verlangt {geraete}.")
        stop = start + geraete - 1
    return str(netz), f"{r}/{praefix}", str(start), str(stop), platz


def tarife_pruefen(roh):
    if not isinstance(roh, list) or not roh:
        raise Fehler("Mindestens ein Tarif ist nötig.")
    if len(roh) > 12:
        raise Fehler("Höchstens 12 Tarife.")
    aus, namen = [], set()
    for t in roh:
        name = str((t or {}).get("name") or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9ÄÖÜäöüß .\-_+]{1,24}", name):
            raise Fehler(f"Tarifname „{name}“: 1–24 Zeichen (Buchstaben, Ziffern, Leerzeichen, . - _ +).")
        if name.lower() in namen:
            raise Fehler(f"Tarif „{name}“ gibt es doppelt.")
        namen.add(name.lower())
        try:
            down, up, praefix, geraete = float(t.get("down")), float(t.get("up")), int(t.get("praefix")), int(t.get("geraete") or 0)
        except (TypeError, ValueError):
            raise Fehler(f"Tarif „{name}“: Bandbreite, Netzmaske und Endgeräte müssen Zahlen sein.")
        if not (0.1 <= down <= 10000 and 0.1 <= up <= 10000):
            raise Fehler(f"Tarif „{name}“: Bandbreite zwischen 0,1 und 10000 Mbit/s.")
        if not 24 <= praefix <= 30:
            raise Fehler(f"Tarif „{name}“: Netzmaske /24 bis /30.")
        if geraete < 0:
            raise Fehler(f"Tarif „{name}“: Endgeräte nicht negativ.")
        dhcp_bereich("10.0.0.1", praefix, geraete)  # passt die Anzahl ins Netz?
        roh_preis = t.get("preis")
        if roh_preis in (None, ""):
            roh_preis = next((x["preis"] for x in TARIFE_STANDARD if x["name"].lower() == name.lower()), 0)
        try:
            preis = float(str(roh_preis).replace(",", "."))
        except ValueError:
            raise Fehler(f"Tarif „{name}“: Preis muss eine Zahl sein.")
        if not 0 <= preis <= 100000:
            raise Fehler(f"Tarif „{name}“: Preis 0 bis 100000 € pro Jahr.")
        aus.append({"name": name, "down": _zahl(down), "up": _zahl(up), "praefix": praefix, "geraete": geraete, "preis": _zahl(preis)})
    return aus


def _tarif_netze(g):
    return [n for n in g.legacy("GET", "rest/networkconf") if n.get("ip_subnet") and n.get("purpose") not in NETZ_ZWECK_AUS]


def _qos_regeln(g):
    r = g.v2("GET", "qos-rules")
    return r.get("data", []) if isinstance(r, dict) else (r or [])


def _ist_eigene(r):
    return str(r.get("name", "")).startswith((QOS_TARIF, QOS_NETZ))


def _qos_vorlage(r):
    b = copy.deepcopy(r) if r else {}
    for k in ("_id", "site_id", "index", "wan_or_vpn_network", "attr_hidden", "attr_hidden_id", "attr_no_delete", "attr_no_edit"):
        b.pop(k, None)
    return b


def _qos_soll(name, t, ids, basis=None):
    b = copy.deepcopy(basis) if basis else {}
    b.update({"name": name, "enabled": True, "objective": "LIMIT",
              "download_limit_kbps": int(round(t["down"] * 1000)), "upload_limit_kbps": int(round(t["up"] * 1000)),
              "download_burst": b.get("download_burst") or "OFF", "upload_burst": b.get("upload_burst") or "OFF"})
    b["source"] = {"matching_target": "NETWORK", "network_ids": sorted(ids), "port_matching_type": "ANY"}
    b["destination"] = {"matching_target": "ANY", "port_matching_type": "ANY"}
    b["schedule"] = {"mode": "ALWAYS", "time_all_day": False}
    return b


def _qos_passt(r, soll):
    s, z, sch = r.get("source") or {}, r.get("destination") or {}, r.get("schedule") or {}
    try:
        down, up = int(r.get("download_limit_kbps") or 0), int(r.get("upload_limit_kbps") or 0)
    except (TypeError, ValueError):
        return False
    return (r.get("enabled") is True and r.get("objective") == "LIMIT"
            and down == soll["download_limit_kbps"] and up == soll["upload_limit_kbps"]
            and s.get("matching_target") == "NETWORK" and sorted(s.get("network_ids") or []) == soll["source"]["network_ids"]
            and (z.get("matching_target") or "ANY") == "ANY" and (sch.get("mode") or "ALWAYS") == "ALWAYS")


def _mbit(kbps):
    try:
        return _zahl(int(kbps) / 1000)
    except (TypeError, ValueError):
        return "?"


def _kurz(ip):
    return "." + ip.rsplit(".", 1)[-1] if ip else "?"


def tarif_lage(d):
    tarife = {t["name"]: t for t in tarife_pruefen(d["tarife"])}
    zuord = d.get("tarif_zuordnung") or {}
    modus = d.get("tarif_modus", "tarif")
    g = Gateway(d)
    netze = _tarif_netze(g)
    # Netznamen merken; Parzellen-Zuordnungen in die Buchungen übernehmen (eine gemeinsame Quelle mit der Kalkulation)
    netznamen = {n["_id"]: n.get("name") or "" for n in netze}
    geaendert = netznamen != (d.get("tarif_netznamen") or {})
    for nid, t in list(zuord.items()):
        zp = netz_parzelle(netznamen.get(nid))
        if zp:
            b = d.setdefault("buchungen", {}).setdefault(zp[0], {})
            b.setdefault(str(zp[1]), t)
            zuord.pop(nid); geaendert = True
    if geaendert:
        d["tarif_netznamen"], d["tarif_zuordnung"] = netznamen, zuord
        speichere(d)
    regeln = _qos_regeln(g)
    eigene = [r for r in regeln if _ist_eigene(r)]
    fremde = [r for r in regeln if not _ist_eigene(r)]
    ips = {}
    for quelle, feld in (("stat/sta", "ip"), ("rest/user", "fixed_ip")):
        try:
            for c in g.legacy_roh(quelle):
                if quelle == "rest/user" and not c.get("use_fixedip"):
                    continue
                if c.get(feld) and c.get("network_id"):
                    ips.setdefault(c["network_id"], set()).add(c[feld])
        except Fehler:
            pass
    nach_id = {n["_id"]: n for n in netze}
    in_regel = {}
    for r in regeln:
        for nid in (r.get("source") or {}).get("network_ids") or []:
            in_regel.setdefault(nid, []).append(r)

    zeilen, ops = [], []
    for n in sorted(netze, key=lambda n: (n.get("name") or "").lower()):
        tname = tarif_von_netz(d, n["_id"], n.get("name"))
        t = tarife.get(tname)
        z = {"id": n["_id"], "name": n.get("name") or "?", "vlan": n.get("vlan") or "", "subnetz": n["ip_subnet"],
             "dhcp": f"{n.get('dhcpd_start', '')} – {_kurz(n.get('dhcpd_stop'))}" if n.get("dhcpd_enabled") else "aus",
             "tarif": tname if t else "", "tarif_weg": tname if tname and not t else "",
             "qos": " · ".join(f"{'' if _ist_eigene(r) else '(fremd) '}{r.get('name')}: {_mbit(r.get('download_limit_kbps'))}/{_mbit(r.get('upload_limit_kbps'))}"
                               for r in in_regel.get(n["_id"], [])),
             "status": "ohne", "aenderung": "", "warnung": ""}
        if t:
            router = n["ip_subnet"].split("/")[0]
            try:
                netz, ip_subnet, start, stop, platz = dhcp_bereich(router, t["praefix"], t["geraete"])
                neu_netz = ipaddress.ip_network(netz)
                for m in netze:
                    if m is not n and ipaddress.ip_network(m["ip_subnet"], strict=False).overlaps(neu_netz):
                        raise Fehler(f"{netz} überschneidet sich mit „{m.get('name')}“ ({m['ip_subnet']}).")
                felder, text, warn = {}, [], []
                if n["ip_subnet"] != ip_subnet:
                    felder["ip_subnet"] = ip_subnet
                    text.append(f"Subnetz /{n['ip_subnet'].split('/')[-1]} → /{t['praefix']}")
                if n.get("dhcpd_enabled"):
                    if n.get("dhcpd_start") != start or n.get("dhcpd_stop") != stop:
                        felder.update({"dhcpd_start": start, "dhcpd_stop": stop})
                        text.append(f"DHCP {_kurz(n.get('dhcpd_start'))}–{_kurz(n.get('dhcpd_stop'))} → {_kurz(start)}–{_kurz(stop)}")
                elif t["geraete"]:
                    warn.append("DHCP ist aus – die Geräte-Begrenzung wirkt nur mit DHCP")
                aussen = sorted(ip for ip in ips.get(n["_id"], ()) if ipaddress.ip_address(ip) not in neu_netz)
                if aussen and "ip_subnet" in felder:
                    warn.append(f"{len(aussen)} Gerät(e) mit IP außerhalb des neuen Netzes ({', '.join(aussen[:3])}{' …' if len(aussen) > 3 else ''}) – verlieren die Verbindung bis zur neuen IP")
                if felder:
                    ops.append({"art": "netz", "id": n["_id"], "name": z["name"], "felder": felder,
                                "alt": {k: n.get(k) for k in felder}, "text": " · ".join(text)})
                z.update(status="aendern" if felder else "gleich", aenderung=" · ".join(text) or "passt",
                         warnung=" · ".join(warn), ziel=f"{ip_subnet} · DHCP {_kurz(start)}–{_kurz(stop)} ({int(ipaddress.ip_address(stop)) - int(ipaddress.ip_address(start)) + 1} Geräte)")
            except Fehler as e:
                z.update(status="fehler", aenderung="nicht möglich", warnung=str(e))
        elif tname:
            z["warnung"] = f"Tarif „{tname}“ gibt es nicht mehr – bitte neu zuordnen"
        zeilen.append(z)

    # QoS-Sollzustand
    soll = {}
    for z in zeilen:
        if z["tarif"] and z["status"] != "fehler":
            t = tarife[z["tarif"]]
            if modus == "netz":
                soll[QOS_NETZ + z["name"]] = (t, [z["id"]])
            else:
                soll.setdefault(QOS_TARIF + t["name"], (t, []))[1].append(z["id"])
    vorh = {}
    for r in eigene:
        vorh.setdefault(r["name"], []).append(r)
    vorlage = _qos_vorlage(next(iter(fremde or eigene), None))
    for name, (t, ids) in sorted(soll.items()):
        liste = vorh.pop(name, [])
        limit = f"{t['down']}/{t['up']} Mbit/s"
        anz = f"{len(ids)} Netz{'e' if len(ids) != 1 else ''}"
        if liste:
            b = _qos_soll(name, t, ids, liste[0])
            if not _qos_passt(liste[0], b):
                alt_ids = set((liste[0].get("source") or {}).get("network_ids") or [])
                dazu, weg = len(set(ids) - alt_ids), len(alt_ids - set(ids))
                was = [f"Limit {_mbit(liste[0].get('download_limit_kbps'))}/{_mbit(liste[0].get('upload_limit_kbps'))} → {limit}"] \
                    if _mbit(liste[0].get('download_limit_kbps')) != t["down"] or _mbit(liste[0].get('upload_limit_kbps')) != t["up"] else []
                was += [f"+{dazu} Netz(e)"] * bool(dazu) + [f"−{weg} Netz(e)"] * bool(weg)
                if liste[0].get("enabled") is not True:
                    was.append("wieder einschalten")
                ops.append({"art": "qos_aendern", "id": liste[0]["_id"], "name": name, "body": b,
                            "text": f"{limit} · {anz} · " + (", ".join(was) or "Einstellungen angleichen")})
            for dup in liste[1:]:
                ops.append({"art": "qos_loeschen", "id": dup["_id"], "name": name, "text": "doppelte Regel"})
        else:
            ops.append({"art": "qos_neu", "name": name, "body": _qos_soll(name, t, ids, vorlage), "text": f"{limit} · {anz}"})
    for name, liste in sorted(vorh.items()):
        for r in liste:
            ops.append({"art": "qos_loeschen", "id": r["_id"], "name": name,
                        "text": "kein Netz mehr in diesem Tarif" if name.startswith(QOS_TARIF if modus == "tarif" else QOS_NETZ) else "andere Regel-Art (Modus gewechselt)"})

    zahl = lambda a: sum(1 for o in ops if o["art"] == a)
    mit = sum(1 for z in zeilen if z["tarif"])
    log = [f"{len(netze)} Netze am Gateway · {mit} mit Tarif · {zahl('netz')} Netz(e) zu ändern · QoS: {zahl('qos_neu')} neu, "
           f"{zahl('qos_aendern')} ändern, {zahl('qos_loeschen')} löschen · {len(fremde)} weitere QoS-Regel(n) bleiben unberührt"]
    if any(z["status"] == "fehler" for z in zeilen):
        log.append("⚠ Bei einigen Netzen passt der Tarif nicht – siehe Spalte Hinweis.")
    return {"g": g, "netze": nach_id, "eigene": eigene, "zeilen": zeilen, "ops": ops, "fremde": [r.get("name") for r in fremde], "log": log, "modus": modus}


def akt_tarif_vergleich(d):
    lage = tarif_lage(d)
    return {k: lage[k] for k in ("zeilen", "ops", "fremde", "log", "modus")}


def _tarif_sicherung(netze, eigene):
    pfad = f"{TARIF_SICHERUNG}{time.strftime('%Y%m%d_%H%M%S')}.json"
    ablage_schreiben(pfad, json.dumps({"zeit": time.strftime("%Y-%m-%d %H:%M:%S"),
                                       "netze": [{k: n.get(k) for k in ("_id", "name", "ip_subnet", "dhcpd_start", "dhcpd_stop")} for n in netze],
                                       "regeln": eigene}, ensure_ascii=False, indent=1))
    for x in ablage_liste(TARIF_SICHERUNG, ".json")[:-10]:
        ablage_loeschen(x)
    return pfad


def _qos_ausfuehren(g, op):
    if op["art"] == "qos_neu":
        g.v2("POST", "qos-rules", op["body"])
    elif op["art"] == "qos_aendern":
        g.v2("PUT", f"qos-rules/{op['id']}", op["body"])
    elif op["art"] == "qos_loeschen":
        g.v2("DELETE", f"qos-rules/{op['id']}")


def akt_tarif_uebertragen(d, netze_ids, regeln, ausfuehren):
    lage = tarif_lage(d)
    g, wahl_n, wahl_r = lage["g"], set(netze_ids or []), set(regeln or [])
    ops_q = [o for o in lage["ops"] if o["art"] != "netz" and o["name"] in wahl_r]
    ops_n = [o for o in lage["ops"] if o["art"] == "netz" and o["id"] in wahl_n]
    if not ops_q and not ops_n:
        raise Fehler("Nichts zu übertragen – ausgewählte Einträge sind schon aktuell. Erst „Unterschiede ermitteln“.")
    wort = {"qos_neu": "anlegen", "qos_aendern": "ändern", "qos_loeschen": "löschen"}
    zeilen = [f"QoS-Regel „{o['name']}“ {wort[o['art']]}: {o['text']}" for o in ops_q] + [f"Netz „{o['name']}“: {o['text']}" for o in ops_n]
    if not ausfuehren:
        return {"log": [f"Vorschau – {len(ops_q)} QoS-Regel(n), {len(ops_n)} Netz(e). Am Gateway ändert sich noch nichts:"] + ["  • " + z for z in zeilen]
                + (["", "ℹ Bei verkleinerten Netzen bekommen Geräte mit IP außerhalb des neuen Bereichs kurz keine Verbindung, bis sie eine neue IP haben (WLAN aus/an)."] if ops_n else [])}
    sich = _tarif_sicherung([lage["netze"][o["id"]] for o in ops_n], lage["eigene"])
    erledigt, log = [], []
    try:
        for o in ops_q:
            _qos_ausfuehren(g, o)
            erledigt.append(o)
        for o in ops_n:
            g.legacy("PUT", f"rest/networkconf/{o['id']}", {**lage["netze"][o["id"]], **o["felder"]})
            erledigt.append(o)
    except Fehler as e:
        journal(f"Tarife: abgebrochen nach {len(erledigt)} von {len(ops_q) + len(ops_n)} Schritten – {e} · Sicherung {os.path.basename(sich)}")
        return {"log": [f"✖ Abgebrochen nach {len(erledigt)} von {len(ops_q) + len(ops_n)} Schritten: {e}"]
                + ["  ✔ " + (f"QoS „{o['name']}“" if o["art"] != "netz" else f"Netz „{o['name']}“") for o in erledigt]
                + [f"Sicherung: {os.path.basename(sich)} – mit „Letzte Tarif-Übertragung rückgängig“ zurücksetzen."]}
    time.sleep(1)
    neu = tarif_lage(d)
    offen = {(o["art"] == "netz", o.get("id") if o["art"] == "netz" else o["name"]) for o in neu["ops"]}
    nicht = [o for o in erledigt if (o["art"] == "netz", o["id"] if o["art"] == "netz" else o["name"]) in offen]
    for o in erledigt:
        journal(f"Tarife: {'Netz' if o['art'] == 'netz' else 'QoS'} „{o['name']}“ {'' if o['art'] == 'netz' else wort[o['art']] + ' '}– {o['text']}")
    journal(f"Tarife: {len(erledigt)} Änderung(en) · {'am Gateway bestätigt' if not nicht else str(len(nicht)) + ' NICHT bestätigt'} · Sicherung {os.path.basename(sich)}")
    log.append(f"✔ {len(erledigt)} Änderung(en) übertragen:")
    log += ["  • " + z for z in zeilen]
    log.append("✔ Am Gateway nachgelesen und bestätigt." if not nicht else
               "⚠ Beim Nachlesen weichen ab: " + ", ".join(o["name"] for o in nicht) + " – bitte in der UniFi-Oberfläche prüfen (Einstellungen → Netzwerke bzw. QoS).")
    log.append(f"Sicherung des vorherigen Stands: {os.path.basename(sich)} (für „Rückgängig“). Tipp: in einer Parzelle einen Geschwindigkeitstest machen.")
    return {"log": log}


def akt_tarif_rueckgaengig(d):
    dateien = ablage_liste(TARIF_SICHERUNG, ".json")
    if not dateien:
        raise Fehler("Keine Tarif-Sicherung vorhanden.")
    sich = json.loads(ablage_lesen(dateien[-1]).decode("utf-8"))
    g = Gateway(d)
    netze = {n["_id"]: n for n in _tarif_netze(g)}
    jetzt = {r["_id"]: r for r in _qos_regeln(g) if _ist_eigene(r)}
    alt = {r["_id"]: r for r in sich["regeln"]}
    log, n_netz, n_qos = [], 0, 0
    for r in jetzt.values():
        if r["_id"] not in alt:
            g.v2("DELETE", f"qos-rules/{r['_id']}"); n_qos += 1
    for rid, r in alt.items():
        if rid in jetzt:
            if jetzt[rid] != r:
                g.v2("PUT", f"qos-rules/{rid}", r); n_qos += 1
        else:
            g.v2("POST", "qos-rules", _qos_vorlage(r)); n_qos += 1
    for a in sich["netze"]:
        n = netze.get(a["_id"])
        if not n:
            log.append(f"⚠ Netz „{a['name']}“ gibt es nicht mehr – übersprungen."); continue
        felder = {k: a[k] for k in ("ip_subnet", "dhcpd_start", "dhcpd_stop") if a.get(k) is not None and n.get(k) != a[k]}
        if felder:
            g.legacy("PUT", f"rest/networkconf/{a['_id']}", {**n, **felder}); n_netz += 1
    ablage_umbenennen(dateien[-1], dateien[-1][:-5] + ".zurueckgespielt")
    journal(f"Tarife rückgängig: Stand vom {sich['zeit']} · {n_qos} QoS-Regel(n), {n_netz} Netz(e) zurückgesetzt")
    return {"log": [f"✔ Stand vom {sich['zeit']} wiederhergestellt: {n_qos} QoS-Regel(n), {n_netz} Netz(e)."] + log
            + ["ℹ Die Tarif-Zuordnung im Manager bleibt wie sie ist – „Unterschiede ermitteln“ zeigt die Abweichung."]}


def akt_tarife_speichern(d, b):
    tarife = tarife_pruefen(b.get("tarife"))
    modus = b.get("modus", d.get("tarif_modus", "tarif"))
    if modus not in ("tarif", "netz"):
        raise Fehler("Unbekannter Modus.")
    umben = {}
    for roh_t, t in zip(b["tarife"], tarife):
        alt = str((roh_t or {}).get("alt") or "")
        if alt and alt != t["name"]:
            umben[alt] = t["name"]
    zuord = d.get("tarif_zuordnung") or {}
    d["tarif_zuordnung"] = {k: umben.get(v, v) for k, v in zuord.items()}
    d["buchungen"] = {kz: {pz: umben.get(t, t) for pz, t in b.items()} for kz, b in (d.get("buchungen") or {}).items()}
    d["tarife"], d["tarif_modus"] = tarife, modus
    speichere(d)
    return {"tarife": tarife, "modus": modus, "log": [f"✔ {len(tarife)} Tarife gespeichert"
            + (f" · umbenannt: {', '.join(f'{a} → {n}' for a, n in umben.items())}" if umben else "")
            + f" · Modus: {'eine QoS-Regel je Tarif' if modus == 'tarif' else 'eine QoS-Regel je Netz'}"]}


def akt_tarif_zuordnen(d, aenderungen):
    if not isinstance(aenderungen, dict):
        raise Fehler("Ungültige Zuordnung.")
    namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
    zuord = dict(d.get("tarif_zuordnung") or {})
    netznamen = d.get("tarif_netznamen") or {}
    buch = d.setdefault("buchungen", {})
    geaendert = []
    for nid, t in aenderungen.items():
        if not re.fullmatch(r"[A-Za-z0-9\-]{1,64}", str(nid)):
            raise Fehler("Ungültige Netz-ID.")
        if t and t not in namen:
            raise Fehler(f"Tarif „{t}“ gibt es nicht.")
        zp = netz_parzelle(netznamen.get(nid))
        if zp:  # Parzelle → Buchung (gilt auch für die Kalkulation)
            zuord.pop(nid, None)
            b = buch.setdefault(zp[0], {})
            if (b.get(str(zp[1])) or "") != (t or ""):
                geaendert.append({"sparte": zp[0], "parzelle": zp[1], "tarif": t or "", "tarif_alt": b.get(str(zp[1]), "")})
            if t:
                b[str(zp[1])] = t
            else:
                b.pop(str(zp[1]), None)
        elif not t:
            zuord.pop(nid, None)
        else:
            zuord[nid] = t
    d["buchungen"] = {kz: b for kz, b in buch.items() if b}
    d["tarif_zuordnung"] = zuord
    speichere(d)
    n_buch = sum(len(b) for b in d["buchungen"].values())
    for x in geaendert:
        ereignis("buchung" if x["tarif"] else "kuendigung", x, d)
    return {"log": [f"✔ Zuordnung gespeichert ({len(aenderungen)} Änderung(en)) – {n_buch} Parzellen gebucht, {len(zuord)} weitere Netze mit Tarif. Die Parzellen-Tarife gelten auch in der Kalkulation."]}


def akt_tarif_erkennen(d):
    """Vorschlag aus dem Ist-Zustand: Netze in SparteNet-QoS-Regeln → deren Tarif; Parzellen-Netze sonst nach Netzmaske (wenn eindeutig)."""
    tarife = tarife_pruefen(d["tarife"])
    nach_name = {t["name"]: t for t in tarife}
    g = Gateway(d)
    netze, regeln = _tarif_netze(g), _qos_regeln(g)
    zuord, vorschlag = d.get("tarif_zuordnung") or {}, {}
    for r in regeln:
        if r.get("name", "").startswith(QOS_TARIF) and r["name"][len(QOS_TARIF):] in nach_name:
            for nid in (r.get("source") or {}).get("network_ids") or []:
                vorschlag[nid] = r["name"][len(QOS_TARIF):]
        elif r.get("name", "").startswith(QOS_NETZ):
            passend = [t["name"] for t in tarife if int(round(t["down"] * 1000)) == r.get("download_limit_kbps") and int(round(t["up"] * 1000)) == r.get("upload_limit_kbps")]
            if len(passend) == 1:
                for nid in (r.get("source") or {}).get("network_ids") or []:
                    vorschlag[nid] = passend[0]
    for n in netze:
        if n["_id"] in vorschlag or "Paz." not in (n.get("name") or ""):
            continue
        p = int(n["ip_subnet"].split("/")[-1])
        passend = [t["name"] for t in tarife if t["praefix"] == p]
        if len(passend) == 1:
            vorschlag[n["_id"]] = passend[0]
    neu = {k: v for k, v in vorschlag.items() if not tarif_von_netz(d, k, next((n.get("name") for n in netze if n["_id"] == k), ""))}
    return {"vorschlag": neu, "log": [f"Vorschlag für {len(neu)} Netz(e) ohne Tarif (bestehende Zuordnungen bleiben). Übernehmen = in der Tabelle eingetragen, dann „Speichern“."]}
PAZ_RE = re.compile(r"^(.+)-Paz\.(\d{1,3})$")


def netz_parzelle(name):
    m = PAZ_RE.match(str(name or ""))
    return (m.group(1), int(m.group(2))) if m else None


def tarif_von_netz(d, nid, name):
    """Tarif eines Netzes: bei Parzellen-Netzen aus den Buchungen, sonst aus der Netz-Zuordnung"""
    zp = netz_parzelle(name)
    if zp:
        t = ((d.get("buchungen") or {}).get(zp[0]) or {}).get(str(zp[1]))
        if t:
            return t
    return (d.get("tarif_zuordnung") or {}).get(nid, "")

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

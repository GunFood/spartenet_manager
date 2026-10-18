"""SparteNet Manager – Umzugshilfe: vorhandene Netze am Gateway auf das VLAN-Schema der Planung umstellen (z. B. Buchenweg alt → 4.7)

Vergleicht die Netze am Gateway (gleicher Name, z. B. BW-Paz.004) mit der aktiven Planung: VLAN-ID, Subnetz, Router-IP, DHCP-Bereich.
Die Netzmaske (Tarif) und die Lage des DHCP-Bereichs im Netz bleiben erhalten – nur Nummern ändern sich.
Die Netze behalten ihre ID: Passwörter (PPSK), Tarife/QoS und Port-Profile hängen daran und bleiben gültig.

Ablauf wie überall: Vorschau → Auswahl → Ausführen mit Bestätigung; vorher Sicherung, danach Nachlesen; „Rückgängig“ stellt den Stand her.
Reihenfolge automatisch so, dass keine VLAN-ID und kein Subnetz doppelt belegt wird; was sich im Kreis blockiert, wird gemeldet.
"""
from .zuteilung import *  # noqa: F401,F403 – alle Namen der vorherigen Module

UMZUG_SICHERUNG = "SparteNet_Umzug_Sicherung_"


def _vlan(n):
    try:
        return int(n.get("vlan") or 0) if n.get("vlan_enabled", True) else 0
    except (TypeError, ValueError):
        return 0


def _verschieben(alt_netz, neu_netz, ip):
    """IP an derselben Stelle im neuen Netz (gleicher Abstand zum Netzanfang)"""
    if not ip:
        return ip
    try:
        return str(neu_netz.network_address + (int(ipaddress.ip_address(ip)) - int(alt_netz.network_address)))
    except ValueError:
        return ip


def umzug_lage(d):
    plan = plan_aktiv(d)
    if plan["schema"] != "standort":
        raise Fehler("Die aktive Planung nutzt noch das alte Schema. Erst unter „Netzplanung → VLAN-Plan je Gateway“ das Gateway übernehmen – "
                     "die Umzugshilfe stellt dann die vorhandenen Netze auf diese Planung um.")
    g = Gateway(d)
    ist = [n for n in g.legacy("GET", "rest/networkconf") if n.get("purpose") not in NETZ_ZWECK_AUS]
    nach_name = {n.get("name"): n for n in ist}
    zeilen, gleich, fehlt = [], 0, 0
    for s in plan["netze"]:
        n = nach_name.get(s["name"])
        if not n:
            fehlt += 1
            continue
        alt_sub = n.get("ip_subnet") or ""
        try:
            alt_if = ipaddress.ip_interface(alt_sub)
        except ValueError:
            zeilen.append({"id": n["_id"], "netz": s["name"], "status": "fehler", "text": f"Subnetz „{alt_sub}“ unlesbar"})
            continue
        praefix = alt_if.network.prefixlen
        neu_if = ipaddress.ip_interface(f"{s['router']}/{praefix}")
        felder, text = {}, []
        if _vlan(n) != s["vlan"]:
            felder.update(vlan=s["vlan"], vlan_enabled=True)
            text.append(f"VLAN {_vlan(n) or '–'} → {s['vlan']}")
        if alt_if != neu_if:
            felder["ip_subnet"] = str(neu_if)
            text.append(f"Subnetz {alt_sub} → {neu_if}")
            if n.get("dhcpd_enabled"):
                for k in ("dhcpd_start", "dhcpd_stop"):
                    v = _verschieben(alt_if.network, neu_if.network, n.get(k))
                    if v != n.get(k):
                        felder[k] = v
                if "dhcpd_start" in felder:
                    text.append(f"DHCP {n.get('dhcpd_start')}–{n.get('dhcpd_stop')} → {felder['dhcpd_start']}–{felder.get('dhcpd_stop', n.get('dhcpd_stop'))}")
            for k in ("dhcpd_gateway", "dhcpd_dns_1"):
                if n.get(k) and n.get(k) in alt_if.network:
                    felder[k] = _verschieben(alt_if.network, neu_if.network, n[k])
        if not felder:
            gleich += 1
            continue
        zeilen.append({"id": n["_id"], "netz": s["name"], "art": s["art"], "status": "aendern", "felder": felder, "text": " · ".join(text),
                       "vlan_alt": _vlan(n), "vlan_neu": s["vlan"], "subnetz_alt": alt_sub, "subnetz_neu": str(neu_if)})
    return g, ist, zeilen, gleich, fehlt


def _reihenfolge(ist, ops):
    """führt nur aus, was gerade frei ist; wiederholt, bis nichts mehr geht → (Reihenfolge, blockiert)"""
    stand = {n["_id"]: {"vlan": _vlan(n), "netz": ipaddress.ip_interface(n["ip_subnet"]).network if n.get("ip_subnet") else None, "name": n.get("name")} for n in ist}
    offen, folge = list(ops), []
    while offen:
        weiter = False
        for o in list(offen):
            ziel_v = o["felder"].get("vlan", stand[o["id"]]["vlan"])
            ziel_n = ipaddress.ip_interface(o["felder"]["ip_subnet"]).network if "ip_subnet" in o["felder"] else stand[o["id"]]["netz"]
            frei = all(i == o["id"] or ((not ziel_v or x["vlan"] != ziel_v) and not (ziel_n and x["netz"] and x["netz"].overlaps(ziel_n)))
                       for i, x in stand.items())
            if frei:
                stand[o["id"]].update(vlan=ziel_v, netz=ziel_n)
                folge.append(o); offen.remove(o); weiter = True
        if not weiter:
            break
    blockiert = []
    for o in offen:
        ziel_v = o["felder"].get("vlan", stand[o["id"]]["vlan"])
        ziel_n = ipaddress.ip_interface(o["felder"]["ip_subnet"]).network if "ip_subnet" in o["felder"] else stand[o["id"]]["netz"]
        wer = [x["name"] for i, x in stand.items() if i != o["id"] and ((ziel_v and x["vlan"] == ziel_v) or (ziel_n and x["netz"] and x["netz"].overlaps(ziel_n)))]
        blockiert.append({**o, "grund": "belegt durch " + ", ".join(sorted(set(wer))[:3])})
    return folge, blockiert


def akt_umzug(d, b):
    b = b or {}
    g, ist, zeilen, gleich, fehlt = umzug_lage(d)
    ops = [z for z in zeilen if z["status"] == "aendern"]
    fehlerhaft = [z for z in zeilen if z["status"] == "fehler"]
    if not b.get("ausfuehren"):
        folge, blockiert = _reihenfolge(ist, ops)
        bl = {o["id"]: o["grund"] for o in blockiert}
        liste = [{k: z.get(k) for k in ("id", "netz", "art", "text", "vlan_alt", "vlan_neu", "subnetz_alt", "subnetz_neu")} | {"blockiert": bl.get(z["id"], "")} for z in ops]
        return {"zeilen": liste, "fehler": fehlerhaft, "gleich": gleich, "fehlt": fehlt,
                "log": [f"{len(ops)} Netz(e) umzustellen, {gleich} schon passend, {fehlt} fehlen am Gateway (→ „Einrichten“ bzw. „Netze nach Buchungen“)"
                        + (f", {len(blockiert)} blockiert" if blockiert else "") + ". Am Gateway ändert sich noch nichts."]}
    wahl = set(b.get("netze") or [])
    ops = [o for o in ops if o["id"] in wahl]
    if not ops:
        raise Fehler("Nichts ausgewählt – erst „Vorschau“.")
    if b.get("nur_eins"):
        ops = ops[:1]
    folge, blockiert = _reihenfolge(ist, ops)
    if not folge:
        raise Fehler("Alle ausgewählten Netze sind blockiert: " + "; ".join(f"{o['netz']} ({o['grund']})" for o in blockiert[:5]))
    nach_id = {n["_id"]: n for n in ist}
    pfad = f"{UMZUG_SICHERUNG}{time.strftime('%Y%m%d_%H%M%S')}.json"
    ablage_schreiben(pfad, json.dumps({"zeit": time.strftime("%Y-%m-%d %H:%M:%S"), "netze": [nach_id[o["id"]] for o in folge]}, ensure_ascii=False, indent=1))
    log, erledigt = [], []
    for o in folge:
        try:
            g.legacy("PUT", f"rest/networkconf/{o['id']}", {**nach_id[o["id"]], **o["felder"]})
            erledigt.append(o)
            log.append(f"✔ {o['netz']}: {o['text']}")
        except Fehler as e:
            log.append(f"✖ {o['netz']}: {e} – Abbruch, die restlichen bleiben unverändert.")
            break
    time.sleep(1)
    _, _, neu, _, _ = umzug_lage(d)
    offen = {z["id"] for z in neu}
    nicht = [o["netz"] for o in erledigt if o["id"] in offen]
    journal(f"Umzugshilfe: {len(erledigt)} Netz(e) umgestellt ({', '.join(o['netz'] for o in erledigt[:15])}{' …' if len(erledigt) > 15 else ''}) · "
            f"{'bestätigt' if not nicht else str(len(nicht)) + ' NICHT bestätigt'} · Sicherung {pfad}")
    log.append("✔ Am Gateway nachgelesen und bestätigt." if not nicht else "⚠ Beim Nachlesen weichen ab: " + ", ".join(nicht) + " – bitte in der UniFi-Oberfläche prüfen.")
    if blockiert:
        log.append("ℹ Noch blockiert (später erneut versuchen): " + ", ".join(f"{o['netz']} ({o['grund']})" for o in blockiert[:10]))
    log.append(f"Sicherung: {pfad} – „Umzug rückgängig“ stellt den Stand her. Geräte in umgestellten Netzen brauchen eine neue IP (WLAN aus/an).")
    for kz in sorted({o["netz"].split("-")[0] for o in erledigt}):
        log.append(f"ℹ Feste IPs, Firewall-Regeln oder Port-Weiterleitungen mit alten Adressen von {kz} bitte in der UniFi-Oberfläche prüfen.")
    return {"log": log}


def akt_umzug_rueckgaengig(d):
    dateien = ablage_liste(UMZUG_SICHERUNG, ".json")
    if not dateien:
        raise Fehler("Keine Umzugs-Sicherung vorhanden.")
    sich = json.loads(ablage_lesen(dateien[-1]).decode("utf-8"))
    g = Gateway(d)
    jetzt = {n["_id"]: n for n in g.legacy("GET", "rest/networkconf")}
    log, n_ok = [], 0
    for a in reversed(sich["netze"]):
        n = jetzt.get(a["_id"])
        if not n:
            log.append(f"⚠ Netz „{a.get('name')}“ gibt es nicht mehr – übersprungen."); continue
        felder = {k: a[k] for k in ("vlan", "vlan_enabled", "ip_subnet", "dhcpd_start", "dhcpd_stop", "dhcpd_gateway", "dhcpd_dns_1") if k in a and n.get(k) != a[k]}
        if felder:
            try:
                g.legacy("PUT", f"rest/networkconf/{a['_id']}", {**n, **felder}); n_ok += 1
            except Fehler as e:
                log.append(f"✖ {a.get('name')}: {e}")
    ablage_umbenennen(dateien[-1], dateien[-1][:-5] + ".zurueckgespielt")
    journal(f"Umzugshilfe rückgängig: Stand vom {sich['zeit']} · {n_ok} Netz(e) zurückgesetzt")
    return {"log": [f"✔ Stand vom {sich['zeit']} wiederhergestellt: {n_ok} Netz(e)."] + log}


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

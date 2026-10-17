"""SparteNet Manager – Auslesen, Abgleich, Passwörter je Parzelle (PPSK), Übertragen und Rückgängig"""
from .qrcode import *  # noqa: F401,F403 – alle Namen der vorherigen Module


# =============================================================== Aktionen
def akt_test(d):
    log, g = [], Gateway(d)
    info = g.req("GET", "/v1/info")
    log.append(f"✔ Konsole „{d['konsole_name']}“ über die Cloud erreichbar – Network-App {info.get('applicationVersion', '?')}")
    sites = g.req("GET", "/v1/sites").get("data", [])
    log.append(f"✔ {len(sites)} Site(s): " + ", ".join(s.get("name", "") for s in sites))
    netze, geraete = g.alle("/v1/sites/{site}/networks"), g.alle("/v1/sites/{site}/devices")
    log.append(f"✔ {len(netze)} Netze, {len(geraete)} Geräte – Auslesen, Abgleich, Netze anlegen und Voucher nutzbar")
    try:
        w = g.legacy("GET", "rest/wlanconf")
        log.append(f"✔ PPSK-Schnittstelle über die Cloud erreichbar ({len(w)} WLANs) – Passwörter können hochgeladen werden")
    except Fehler as e:
        log.append(f"ℹ {e}")
    return {"log": log}


LESEN = {
    "geraete": ("/v1/sites/{site}/devices", [("name", "Name"), ("model", "Modell"), ("ipAddress", "IP-Adresse"), ("macAddress", "MAC"), ("state", "Status"), ("firmwareVersion", "Firmware")]),
    "clients": ("/v1/sites/{site}/clients", [("name", "Name"), ("type", "Art"), ("ipAddress", "IP-Adresse"), ("macAddress", "MAC"), ("connectedAt", "verbunden seit")]),
    "netze": ("/v1/sites/{site}/networks", [("name", "Name"), ("vlanId", "VLAN"), ("enabled", "aktiv")]),
    "wlans": ("/v1/sites/{site}/wifi/broadcasts", [("name", "Name"), ("type", "Art"), ("enabled", "aktiv")]),
    "voucher": ("/v1/sites/{site}/hotspot/vouchers", [("code", "Code"), ("name", "Bezeichnung"), ("timeLimitMinutes", "Minuten"), ("expired", "abgelaufen"), ("createdAt", "erstellt")]),
}


def akt_lesen(d, was):
    if was not in LESEN:
        raise Fehler("Unbekannte Auswahl.")
    pfad, sp = LESEN[was]
    daten = Gateway(d).alle(pfad)
    return {"spalten": [list(t) for t in sp], "zeilen": [{k: x.get(k, "") for k, _ in sp} for x in daten]}


def akt_abgleich(d, kz):
    plan, g = plan_aktiv(d), Gateway(d)
    soll = [n for n in plan["netze"] if not kz or n["sparte"] == kz]
    ist = g.alle("/v1/sites/{site}/networks")
    nach_vlan, nach_name = {n.get("vlanId"): n for n in ist}, {n.get("name"): n for n in ist}
    fehlen, abweichend, ok = [], [], 0
    for n in soll:
        v, m = nach_vlan.get(n["vlan"]), nach_name.get(n["name"])
        if v and v.get("name") == n["name"]:
            ok += 1
        elif v:
            abweichend.append({"netz": n["name"], "soll": f"VLAN {n['vlan']}", "ist": f"VLAN {n['vlan']} heißt „{v.get('name')}“"})
        elif m:
            abweichend.append({"netz": n["name"], "soll": f"VLAN {n['vlan']}", "ist": f"hat VLAN {m.get('vlanId')}"})
        else:
            fehlen.append({"netz": n["name"], "vlan": n["vlan"], "subnetz": n["netz"]})
    soll_vlans = {n["vlan"] for n in plan["netze"]} | {1}
    extra = [{"netz": n.get("name"), "vlan": n.get("vlanId")} for n in ist if n.get("vlanId") not in soll_vlans]
    hinweise, clients = [], []
    for x in g.alle("/v1/sites/{site}/devices"):
        art, wo = wo_ist(x.get("ipAddress", ""), plan)
        if art in ("parzelle", "vorstand", "gaeste"):
            hinweise.append({"art": "Gerät", "name": x.get("name"), "ip": x.get("ipAddress"), "hinweis": f"Technik im Netz {wo} – Verwaltung gehört ins Gateway-/Technik-Netz"})
        elif art == "ausserhalb":
            hinweise.append({"art": "Gerät", "name": x.get("name"), "ip": x.get("ipAddress"), "hinweis": "außerhalb des Plans (beim Gateway selbst normal)"})
    for x in g.alle("/v1/sites/{site}/clients"):
        art, wo = wo_ist(x.get("ipAddress", ""), plan)
        if art in ("gateway", "technik"):
            hinweise.append({"art": "Client", "name": x.get("name"), "ip": x.get("ipAddress"), "hinweis": "Endgerät im Technik-Netz – WLAN/PPSK prüfen"})
        clients.append({"name": x.get("name"), "ip": x.get("ipAddress"), "netz": wo})
    return {"log": [f"Soll {len(soll)} Netze · korrekt {ok} · fehlen {len(fehlen)} · abweichend {len(abweichend)} · zusätzlich {len(extra)} · Hinweise {len(hinweise)}"],
            "fehlen": fehlen, "abweichend": abweichend, "extra": extra, "hinweise": hinweise, "clients": clients}


def _ersetze(obj, alt, neu):
    if isinstance(obj, str):
        return obj.replace(alt, neu)
    if isinstance(obj, list):
        return [_ersetze(x, alt, neu) for x in obj]
    if isinstance(obj, dict):
        return {k: _ersetze(v, alt, neu) for k, v in obj.items()}
    return obj


def akt_netze(d, kz, ausfuehren, nur_eins, namen=None):
    plan, g = plan_aktiv(d), Gateway(d)
    soll = [n for n in plan["netze"] if n["sparte"] == kz]
    if not soll:
        raise Fehler("Sparte nicht im Plan.")
    ist = g.alle("/v1/sites/{site}/networks")
    auswahl_namen = set(namen) if namen else None
    vlans = {n.get("vlanId") for n in ist}
    namen_am_gw = {n.get("name") for n in ist}
    neu = [n for n in soll if n["name"] not in namen_am_gw and n["vlan"] not in vlans]
    if auswahl_namen is not None:
        neu = [n for n in neu if n["name"] in auswahl_namen]
    log = [f"{len(neu)} ausgewählte(s) Netz(e) für {kz}."] if auswahl_namen is not None else [f"{len(soll)} Netze im Plan, {len(soll) - len(neu)} vorhanden, {len(neu)} fehlen."]
    if not neu:
        return {"log": log + ["Nichts zu tun – alle Netze vorhanden."]}
    muster = re.compile(r"-Paz\.\d{3}$")
    kand = [n for n in ist if str(n.get("name", "")).startswith(kz + "-") and muster.search(str(n.get("name", "")))] or \
           [n for n in ist if muster.search(str(n.get("name", "")))]
    if not kand:
        raise Fehler("Keine Vorlage gefunden. Bitte ein Parzellennetz (z. B. BW-Paz.001) einmal in der UniFi-Oberfläche anlegen – der Manager kopiert dann dessen Einstellungen.")
    vorlage = g.req("GET", f"/v1/sites/{{site}}/networks/{kand[0]['id']}")
    host = (vorlage.get("ipv4Configuration") or {}).get("hostIpAddress") or ""
    if host.count(".") != 3:
        raise Fehler(f"Vorlage „{vorlage.get('name')}“ hat keine IPv4-Gateway-Adresse.")
    alt = host.rsplit(".", 1)[0] + "."
    for k in ("id", "default", "metadata", "_id"):
        vorlage.pop(k, None)
    log.append(f"Vorlage: {kand[0].get('name')} ({alt}0/24) – DHCP, Isolation, Firewall-Zone werden übernommen.")
    def body(n):
        b = _ersetze(copy.deepcopy(vorlage), alt, f"10.{n['sid']}.{n['x']}.")
        b.update({"name": n["name"], "vlanId": n["vlan"], "enabled": True})
        return b
    if nur_eins:
        neu = neu[:1]
    if not ausfuehren:
        log += [f"Vorschau: {n['name']:<16} VLAN {n['vlan']:<5} {n['netz']}" for n in neu]
        log.append("Anfrage für das erste Netz:\n" + json.dumps(body(neu[0]), indent=2, ensure_ascii=False))
        return {"log": log}
    ok = 0
    for n in neu:
        try:
            g.req("POST", "/v1/sites/{site}/networks", body(n)); ok += 1
            log.append(f"✔ angelegt: {n['name']} VLAN {n['vlan']} {n['netz']}")
        except Fehler as e:
            log.append(f"✖ {n['name']}: {e}")
            if ok == 0:
                log.append("Abbruch nach dem ersten Fehler."); break
    journal(f"Netze {kz}: {ok} von {len(neu)} angelegt ({', '.join(n['name'] for n in neu[:ok][:20])}{' …' if ok > 20 else ''})")
    log.append(f"Fertig: {ok} von {len(neu)} angelegt." + (" Bitte in der UniFi-Oberfläche prüfen, dann den Rest anlegen." if nur_eins and ok else ""))
    return {"log": log}


def akt_ppsk(d, kz, art):
    plan = plan_aktiv(d)
    s = next((x for x in plan["sparten"] if x["kz"] == kz), None)
    if not s:
        raise Fehler("Sparte nicht im Plan.")
    soll = [n for n in plan["netze"] if n["sparte"] == kz and n["art"] == "parzelle"]
    bisher = lese_ppsk(kz)
    register_eintragen([z.get("Passwort", "") for z in bisher])   # auch ältere Passwörter nie wieder vergeben
    vorhanden = {} if art == "neu" else {z["Netz"]: z["Passwort"] for z in bisher}
    log = []
    if art == "gateway":
        g = Gateway(d)
        nid = {n["_id"]: n["name"] for n in g.legacy("GET", "rest/networkconf")}
        ssid = wlan_ssid(d, kz)
        wlan = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("name") == ssid), None)
        if not wlan:
            raise Fehler(f"WLAN „{ssid}“ nicht am Gateway gefunden – unter Schritt 2 „WLANs vom Gateway abrufen“ und das richtige Pächter-WLAN wählen.")
        u = 0
        for k in wlan.get("private_preshared_keys") or []:
            name = nid.get(k.get("networkconf_id"))
            if name and k.get("password"):
                vorhanden[name] = k["password"]; u += 1
        log.append(f"✔ {u} vorhandene Passwörter vom Gateway übernommen.")
    zeilen, neu = [], 0
    fehlend = sum(1 for n in soll if not vorhanden.get(n["name"])) if art != "anzeigen" else 0
    andere = alle_belegten() - set(z["Passwort"] for z in lese_ppsk(kz)) if art == "neu" else set()
    vorrat = iter(passwoerter_erzeugen(fehlend, d, zusaetzlich=set(vorhanden.values()) | andere)) if fehlend else iter(())
    for n in soll:
        pw = vorhanden.get(n["name"], "")
        if not pw and art != "anzeigen":
            pw = next(vorrat); neu += 1
        zeilen.append({"Parzelle": n["parzelle"], "Netz": n["name"], "VLAN": n["vlan"], "WLAN": n["ssid"], "Passwort": pw})
    if art != "anzeigen":
        hier = {z["Netz"] for z in zeilen}
        schreibe_ppsk(kz, sorted(zeilen + [z for z in bisher if z.get("Netz") not in hier and z.get("Passwort")],
                                 key=lambda z: int(z.get("Parzelle") or 0)))  # Parzellen an anderen Gateways bleiben erhalten
        register_eintragen([z["Passwort"] for z in zeilen])
        r = pw_regel(d)
        log.append(f"✔ {neu} neue Passwörter ({r['praefix']} + {r['ziffern']} Ziffern, geprüft auf doppelte), {len(zeilen) - neu} beibehalten – gespeichert in PPSK_{kz}.csv")
    else:
        log.append(f"{sum(1 for z in zeilen if z['Passwort'])} von {len(zeilen)} Parzellen haben ein Passwort.")
    return {"log": log, "zeilen": zeilen, "sparte": s}


def akt_wlans(d, kz):
    """WLANs am Gateway auslesen – mit Vorschlag, welches zu dieser Sparte gehört (Pächter = PPSK mit Parzellennetzen der Sparte)"""
    g = Gateway(d)
    netze = {n["_id"]: n.get("name", "") for n in g.legacy("GET", "rest/networkconf")}
    liste = []
    for w in g.legacy("GET", "rest/wlanconf"):
        keys = w.get("private_preshared_keys") or []
        eigene = sum(1 for k in keys if str(netze.get(k.get("networkconf_id"), "")).startswith(f"{kz}-Paz."))
        liste.append({"name": w.get("name", ""), "ppsk": bool(w.get("private_preshared_keys_enabled")), "schluessel": len(keys), "eigene": eigene,
                      "gast": bool(w.get("is_guest")), "aktiv": w.get("enabled", True) is not False, "sicherheit": w.get("security", ""),
                      "netz": netze.get(w.get("networkconf_id"), "")})
    liste.sort(key=lambda w: w["name"].lower())
    zu = (d.get("wlan_namen") or {}).get(kz) or {}
    namen = [w["name"] for w in liste]
    def vorschlag(art):
        if zu.get(art) in namen:
            return zu[art]
        std = wlan_ssid({"plan": d.get("plan")}, kz, art)
        if std in namen:
            return std
        kz_l = kz.lower()
        if art == "paechter":
            k = sorted([w for w in liste if w["eigene"]], key=lambda w: -w["eigene"]) or [w for w in liste if w["ppsk"] and kz_l in w["name"].lower()]
        elif art == "gaeste":
            k = [w for w in liste if w["gast"] and kz_l in w["name"].lower()] or [w for w in liste if w["gast"]]
        else:
            k = [w for w in liste if kz_l in w["name"].lower() and "vorstand" in w["name"].lower()]
        return k[0]["name"] if k else ""
    return {"wlans": liste, "zuordnung": {a: wlan_ssid(d, kz, a) for a in ("paechter", "gaeste", "vorstand")}, "eigen": bool(zu),
            "vorschlag": {a: vorschlag(a) for a in ("paechter", "gaeste", "vorstand")},
            "log": [f"{len(liste)} WLAN(s) am Gateway." + ("" if liste else " Bitte in der UniFi-Oberfläche anlegen.")]}


def akt_wlan_zuordnung(d, b):
    """WLAN-Namen einer Sparte festlegen (leer = nach Schema); die Passwortliste bekommt den neuen Namen"""
    kz = kz_pruefen(b.get("sparte"), (d.get("plan") or {}).get("praefix") or "SparteNet.de")
    if kz not in {s["kz"] for s in plan_aktiv(d)["sparten"]}:
        raise Fehler("Sparte nicht im Plan.")
    neu = {}
    for art in ("paechter", "gaeste", "vorstand"):
        v = str(b.get(art) or "").strip()
        if len(v.encode("utf-8")) > 32 or any(c in v for c in "\r\n\t"):
            raise Fehler(f"WLAN-Name „{v}“: höchstens 32 Zeichen, eine Zeile.")
        if v:
            neu[art] = v
    alle = d.setdefault("wlan_namen", {})
    if neu:
        alle[kz] = neu
    else:
        alle.pop(kz, None)
    ssid = wlan_ssid(d, kz)
    zeilen = lese_ppsk(kz)
    if zeilen and any(z.get("WLAN") != ssid for z in zeilen):
        for z in zeilen:
            z["WLAN"] = ssid
        schreibe_ppsk(kz, zeilen)
    speichere(d)
    journal(f"WLAN-Namen {kz}: Pächter „{ssid}“, Gäste „{wlan_ssid(d, kz, 'gaeste')}“, Vorstand „{wlan_ssid(d, kz, 'vorstand')}“")
    return {"zuordnung": {a: wlan_ssid(d, kz, a) for a in ("paechter", "gaeste", "vorstand")}, "eigen": bool(neu),
            "log": [f"✔ WLAN-Namen für {kz} gespeichert – Pächter-WLAN „{ssid}“." + (f" Passwortliste ({len(zeilen)} Einträge) und Zugangskarten nutzen jetzt diesen Namen." if zeilen else "")]}


def akt_ppsk_speichern(d, kz, aenderungen):
    """aenderungen: {"Parzelle": "neues Passwort" | ""} – wird in PPSK_<kz>.csv geschrieben"""
    if not isinstance(aenderungen, dict) or not aenderungen:
        raise Fehler("Keine Änderungen.")
    basis = akt_ppsk(d, kz, "anzeigen")["zeilen"]
    alt = {str(z["Parzelle"]): z["Passwort"] for z in basis}
    fehler, log = [], []
    for p, pw in aenderungen.items():
        if str(p) not in alt:
            fehler.append(f"Parzelle {p}: nicht im Plan")
            continue
        f = passwort_fehler(str(pw))
        if f:
            fehler.append(f"Parzelle {p}: Passwort {f}")
    for z in basis:
        p = str(z["Parzelle"])
        if p in aenderungen:
            z["Passwort"] = str(aenderungen[p])
    gesehen = {}
    for z in basis:
        if z["Passwort"]:
            if z["Passwort"] in gesehen:
                fehler.append(f"Parzelle {z['Parzelle']}: gleiches Passwort wie Parzelle {gesehen[z['Passwort']]} – jedes Passwort darf im WLAN nur einmal vorkommen")
            gesehen.setdefault(z["Passwort"], z["Parzelle"])
    andere = set()
    for f in ablage_liste("PPSK_", ".csv"):
        if f != f"PPSK_{kz}.csv":
            andere |= {(z.get("Passwort"), f[5:-4], z.get("Parzelle")) for z in lese_ppsk(f[5:-4]) if z.get("Passwort")}
    for p, pw in aenderungen.items():
        for apw, akz, ap in andere:
            if pw and pw == apw:
                fehler.append(f"Parzelle {p}: Passwort ist schon in Sparte {akz} (Parzelle {ap}) vergeben")
    reg = _register_lesen()
    for p, pw in aenderungen.items():
        if pw and pw != alt.get(str(p)) and _hash(pw) in reg and pw not in alt.values():
            fehler.append(f"Parzelle {p}: dieses Passwort wurde früher schon einmal vergeben – bitte ein anderes nehmen")
    if fehler:
        raise Fehler("Nicht gespeichert:\n" + "\n".join(fehler[:15]))
    schreibe_ppsk(kz, basis)
    register_eintragen([pw for pw in aenderungen.values() if pw])
    geaendert = [p for p, pw in aenderungen.items() if alt[str(p)] != pw]
    gesperrt = [p for p in geaendert if aenderungen[p] == ""]
    LOG.info("PPSK geändert: Sparte %s, Parzellen %s (Passwörter nicht protokolliert)", kz, ",".join(map(str, geaendert)))
    log.append(f"✔ {len(geaendert)} Parzelle(n) geändert und in PPSK_{kz}.csv gespeichert: " + ", ".join(map(str, geaendert)))
    if gesperrt:
        log.append(f"ℹ Ohne Passwort (Zugang wird beim Hochladen entfernt): Parzelle " + ", ".join(map(str, gesperrt)))
    log.append("➜ Damit die Änderung im WLAN gilt: Schritt 4 „Ausführen“. Danach die Karten der geänderten Parzellen neu drucken.")
    return {"log": log, "zeilen": basis, "geaendert": geaendert}


def akt_schreibtest(d):
    """Prüft, ob über die Cloud geschrieben werden darf – ohne etwas dauerhaft zu ändern."""
    g, log, ok = Gateway(d), [], {"network": False, "klassisch": False}
    # 1) Network-API: 1 Test-Voucher (1 Minute) anlegen und sofort wieder löschen
    try:
        a = g.req("POST", "/v1/sites/{site}/hotspot/vouchers", {"count": 1, "name": "SparteNet-Schreibtest", "timeLimitMinutes": 1})
        v = ((a or {}).get("vouchers") or [{}])[0] if isinstance(a, dict) else {}
        if v.get("id"):
            g.req("DELETE", f"/v1/sites/{{site}}/hotspot/vouchers/{v['id']}")
            log.append("✔ Network-API: Schreiben erlaubt (Test-Voucher angelegt und wieder gelöscht) – Netze anlegen und Voucher funktionieren.")
        else:
            log.append("✔ Network-API: Schreiben erlaubt. ℹ Test-Voucher „SparteNet-Schreibtest“ (1 Minute) bitte unter Hotspot löschen.")
        ok["network"] = True
    except Fehler as e:
        log.append(f"✖ Network-API: {e}")
    # 2) Klassische Schnittstelle (für Passwörter/PPSK): Notiz eines bekannten Clients unverändert zurückschreiben
    try:
        nutzer = [u for u in g.legacy_roh("rest/user") if u.get("_id")]
        if not nutzer:
            log.append("ℹ Klassische Schnittstelle: kein bekannter Client für den Test vorhanden – Test übersprungen.")
        else:
            u = nutzer[0]
            g.legacy("PUT", f"rest/user/{u['_id']}", {"note": u.get("note", ""), "noted": bool(u.get("noted", False))})
            log.append("✔ Klassische Schnittstelle: Schreiben erlaubt (ohne Änderung getestet) – Passwörter je Parzelle können übertragen werden.")
            ok["klassisch"] = True
    except Fehler as e:
        log.append(f"✖ Klassische Schnittstelle: {e}")
    if not ok["network"] and not ok["klassisch"]:
        log.append("➜ Über die Cloud ist kein Schreiben möglich. Lösung: API-Key als Besitzer/Super-Admin neu erstellen – oder lokal über VPN/Teleport arbeiten.")
    journal(f"Schreibtest: Network-API {'ok' if ok['network'] else 'abgelehnt'}, klassisch {'ok' if ok['klassisch'] else 'abgelehnt/übersprungen'}")
    return {"log": log, "ok": ok}


def _ppsk_lage(d, kz):
    """Soll (PPSK_<kz>.csv) gegen Ist (WLAN am Gateway) – gemeinsame Grundlage für Vergleich und Übertragung"""
    plan = plan_aktiv(d)
    ssid = wlan_ssid(d, kz)
    g = Gateway(d)
    nid = {n["name"]: n["_id"] for n in g.legacy("GET", "rest/networkconf")}
    wlan = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("name") == ssid), None)
    if not wlan:
        raise Fehler(f"WLAN „{ssid}“ nicht am Gateway gefunden – unter „Einrichten“ Schritt 2 „WLANs vom Gateway abrufen“ und das richtige Pächter-WLAN wählen (oder in der UniFi-Oberfläche anlegen: WPA2, Private Pre-Shared Keys).")
    soll = {z["Netz"]: z for z in lese_ppsk(kz)}
    gesperrt = {str(g.get("parzelle")) for g in (d.get("zugang_gesperrt") or {}).values() if isinstance(g, dict) and g.get("sparte") == kz}
    if not soll:
        raise Fehler(f"Noch keine Passwörter für {kz} – erst „Einrichten“ Schritt 3.")
    ist = {}
    for k in wlan.get("private_preshared_keys") or []:
        ist.setdefault(k.get("networkconf_id"), []).append(k.get("password", ""))
    zeilen = []
    for n in [x for x in plan["netze"] if x["sparte"] == kz and x["art"] == "parzelle"]:
        z = soll.get(n["name"], {})
        pw_soll, nid_ = z.get("Passwort", ""), nid.get(n["name"])
        if str(n["parzelle"]) in gesperrt:
            pw_soll = ""          # Zugang gesperrt (Laufzeit abgelaufen oder von Hand) – soll nicht im WLAN stehen
        pw_ist = ist.get(nid_, []) if nid_ else []
        if not nid_:
            status = "netz_fehlt" if pw_soll else "gleich"
        elif pw_soll and not pw_ist:
            status = "neu"
        elif pw_soll and pw_ist != [pw_soll]:
            status = "geaendert"
        elif not pw_soll and pw_ist:
            status = "entfernen"
        else:
            status = "gleich"
        zeilen.append({"Parzelle": n["parzelle"], "Netz": n["name"], "VLAN": n["vlan"], "status": status, "soll": pw_soll, "ist": pw_ist, "nid": nid_})
    return g, wlan, ssid, zeilen


STATUS_TEXT = {"neu": "neu – noch nicht am Gateway", "geaendert": "geändert", "entfernen": "Zugang wird entfernt",
               "netz_fehlt": "Netz fehlt – wird übertragen, sobald das Netz angelegt ist (oben mit auswählen)", "gleich": "aktuell"}


def akt_vergleich(d, kz):
    plan = plan_aktiv(d)
    soll_netze = [n for n in plan["netze"] if n["sparte"] == kz]
    if not soll_netze:
        raise Fehler("Sparte nicht im Plan.")
    g = Gateway(d)
    ist = g.alle("/v1/sites/{site}/networks")
    namen, vlans = {n.get("name") for n in ist}, {n.get("vlanId") for n in ist}
    netze = [{"Netz": n["name"], "VLAN": n["vlan"], "Subnetz": n["netz"]} for n in soll_netze if n["name"] not in namen and n["vlan"] not in vlans]
    ppsk, ppsk_fehler = [], ""
    try:
        _, _, ssid, zeilen = _ppsk_lage(d, kz)
        for z in zeilen:
            if z["status"] != "gleich":
                ppsk.append({"Parzelle": z["Parzelle"], "Netz": z["Netz"], "status": z["status"], "Status": STATUS_TEXT[z["status"]]})
        gleich = sum(1 for z in zeilen if z["status"] == "gleich")
    except Fehler as e:
        ppsk_fehler, gleich = str(e), 0
    reihe = {"geaendert": 0, "entfernen": 1, "neu": 2, "netz_fehlt": 3}
    ppsk.sort(key=lambda p: (reihe.get(p["status"], 9), p["Parzelle"]))
    zahl = lambda st: sum(1 for p in ppsk if p["status"] == st)
    log = [f"Sparte {kz}: {len(netze)} Netze fehlen · Passwörter: {zahl('neu')} neu, {zahl('geaendert')} geändert, {zahl('entfernen')} zu entfernen, {gleich} aktuell"]
    if ppsk_fehler:
        log.append("ℹ Passwörter: " + ppsk_fehler)
    return {"log": log, "netze": netze, "ppsk": ppsk, "gleich": gleich, "ppsk_fehler": ppsk_fehler}


def _sicherung_schreiben(kz, wlan, ssid):
    pfad = f"SparteNet_Sicherung_{kz}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    ablage_schreiben(pfad, json.dumps({"zeit": time.strftime("%Y-%m-%d %H:%M:%S"), "ssid": ssid, "wlan_id": wlan.get("_id"),
                                       "private_preshared_keys_enabled": wlan.get("private_preshared_keys_enabled"),
                                       "private_preshared_keys": wlan.get("private_preshared_keys") or []}, ensure_ascii=False, indent=1))
    for x in ablage_liste(f"SparteNet_Sicherung_{kz}_")[:-10]:
        ablage_loeschen(x)
    return pfad


def _ppsk_schreiben_und_pruefen(g, wlan, ssid, liste):
    g.legacy("PUT", f"rest/wlanconf/{wlan['_id']}", {"private_preshared_keys_enabled": True, "private_preshared_keys": liste})
    time.sleep(1)
    neu = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("_id") == wlan["_id"]), {})
    erwartet = sorted((k["networkconf_id"], k["password"]) for k in liste)
    ist = sorted((k.get("networkconf_id"), k.get("password")) for k in neu.get("private_preshared_keys") or [])
    return erwartet == ist


def akt_uebertragen(d, kz, parzellen, netze, ausfuehren):
    """Überträgt ausgewählte Änderungen: fehlende Netze anlegen, Passwörter je Parzelle setzen/ändern/entfernen."""
    log = []
    if netze:
        r = akt_netze(d, kz, ausfuehren, False, namen=netze)
        log += r["log"]
    if parzellen:
        g, wlan, ssid, zeilen = _ppsk_lage(d, kz)
        wahl = {str(p) for p in parzellen}
        betroffen = [z for z in zeilen if str(z["Parzelle"]) in wahl and z["status"] in ("neu", "geaendert", "entfernen")]
        uebersprungen = [z for z in zeilen if str(z["Parzelle"]) in wahl and z["status"] == "netz_fehlt"]
        if uebersprungen:
            log.append("ℹ Übersprungen, Netz fehlt noch am Gateway: Parzelle " + ", ".join(str(z["Parzelle"]) for z in uebersprungen))
        if not betroffen:
            log.append("Passwörter: nichts zu übertragen.")
        else:
            nids = {z["nid"] for z in betroffen}
            liste = [k for k in (wlan.get("private_preshared_keys") or []) if k.get("networkconf_id") not in nids]
            liste += [{"password": z["soll"], "networkconf_id": z["nid"]} for z in betroffen if z["soll"]]
            pws = [k["password"] for k in liste]
            doppelt = {p for p in pws if pws.count(p) > 1}
            if doppelt:
                raise Fehler("Ein Passwort käme im WLAN doppelt vor (auch Einträge anderer Sparten zählen) – bitte in Schritt 3 ändern.")
            text = ", ".join(f"{z['Parzelle']} ({ {'neu': 'neu', 'geaendert': 'geändert', 'entfernen': 'entfernt'}[z['status']] })" for z in betroffen)
            if not ausfuehren:
                log.append(f"Vorschau WLAN „{ssid}“: {len(betroffen)} Parzelle(n) – {text}. Alle anderen Einträge bleiben unverändert.")
            else:
                sich = _sicherung_schreiben(kz, wlan, ssid)
                bestaetigt = _ppsk_schreiben_und_pruefen(g, wlan, ssid, liste)
                journal(f"Passwörter {kz} → „{ssid}“: {text} · {'am Gateway bestätigt' if bestaetigt else 'NICHT bestätigt'} · Sicherung {os.path.basename(sich)}")
                log.append(f"✔ {len(betroffen)} Parzelle(n) an das Gateway übertragen: {text}")
                log.append("✔ Am Gateway nachgelesen und bestätigt." if bestaetigt else "⚠ Übertragen, aber beim Nachlesen nicht identisch – bitte in der UniFi-Oberfläche prüfen.")
                log.append(f"Sicherung des vorherigen Stands: {os.path.basename(sich)} (für „Rückgängig“). Mit einem Handy testen!")
    if not netze and not parzellen:
        raise Fehler("Nichts ausgewählt.")
    return {"log": log}


def akt_rueckgaengig(d, kz):
    dateien = ablage_liste(f"SparteNet_Sicherung_{kz}_", ".json")
    if not dateien:
        raise Fehler("Keine Sicherung vorhanden.")
    sich = json.loads(ablage_lesen(dateien[-1]).decode("utf-8"))
    g = Gateway(d)
    wlan = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("_id") == sich["wlan_id"]), None)
    if not wlan:
        raise Fehler("Das WLAN aus der Sicherung gibt es am Gateway nicht mehr.")
    bestaetigt = _ppsk_schreiben_und_pruefen(g, wlan, sich["ssid"], sich["private_preshared_keys"])
    ablage_umbenennen(dateien[-1], dateien[-1][:-5] + ".zurueckgespielt")
    journal(f"Rückgängig {kz} → „{sich['ssid']}“: Stand vom {sich['zeit']} wiederhergestellt · {'bestätigt' if bestaetigt else 'NICHT bestätigt'}")
    return {"log": [f"✔ Passwörter im WLAN „{sich['ssid']}“ auf den Stand vom {sich['zeit']} zurückgesetzt ({len(sich['private_preshared_keys'])} Einträge)."
                    + (" Am Gateway bestätigt." if bestaetigt else " ⚠ Nicht bestätigt – bitte prüfen."),
                    "ℹ PPSK_" + kz + ".csv wurde nicht verändert – dort stehen weiter die neuen Passwörter."]}


def akt_journal():
    if DB:
        z = DB.sql("SELECT zeit, text FROM sn_journal ORDER BY id DESC LIMIT 300", alle=True)
        return {"log": [f"{a:%Y-%m-%d %H:%M:%S} | {t}" for a, t in z] or ["(noch keine Änderungen übertragen)"]}
    if not os.path.exists(JOURNAL):
        return {"log": ["(noch keine Änderungen übertragen)"]}
    with open(JOURNAL, encoding="utf-8") as f:
        return {"log": f.read().splitlines()[-300:][::-1]}


def akt_ppsk_hochladen(d, kz, ausfuehren):
    """Schritt 4: alle Unterschiede der Sparte übertragen"""
    _, _, _, zeilen = _ppsk_lage(d, kz)
    return akt_uebertragen(d, kz, [z["Parzelle"] for z in zeilen if z["status"] in ("neu", "geaendert", "entfernen", "netz_fehlt")], [], ausfuehren)


def akt_ppsk_hochladen_alt(d, kz, ausfuehren):
    plan = plan_aktiv(d)
    keys = [k for k in lese_ppsk(kz) if k.get("Passwort")]
    if not keys:
        raise Fehler("Keine Passwörter vorhanden – erst Schritt 3.")
    ssid = wlan_ssid(d, kz)
    if not ausfuehren:
        return {"log": [f"Vorschau: WLAN „{ssid}“ bekommt bzw. behält {len(keys)} Parzellen-Passwörter. Andere Passwörter bleiben erhalten."]}
    if len({k["Passwort"] for k in keys}) != len(keys):
        raise Fehler("Ein Passwort kommt doppelt vor – bitte korrigieren.")
    g = Gateway(d)
    nid = {n["name"]: n["_id"] for n in g.legacy("GET", "rest/networkconf")}
    wlan = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("name") == ssid), None)
    if not wlan:
        raise Fehler(f"WLAN „{ssid}“ nicht gefunden.")
    fehlt = [k["Netz"] for k in keys if k["Netz"] not in nid]
    if fehlt:
        raise Fehler(f"Netze fehlen noch: {', '.join(fehlt[:6])} … – erst Schritt 1.")
    alle_parz = [n["name"] for n in plan["netze"] if n["sparte"] == kz and n["art"] == "parzelle"]
    unsere = {nid[n] for n in alle_parz if n in nid}
    behalten = [k for k in (wlan.get("private_preshared_keys") or []) if k.get("networkconf_id") not in unsere]
    wlan["private_preshared_keys_enabled"] = True
    wlan["private_preshared_keys"] = behalten + [{"password": k["Passwort"], "networkconf_id": nid[k["Netz"]]} for k in keys]
    g.legacy("PUT", f"rest/wlanconf/{wlan['_id']}", wlan)
    ohne = len([n for n in alle_parz if n in nid]) - len(keys)
    return {"log": [f"✔ {len(keys)} Passwörter im WLAN „{ssid}“ gespeichert ({len(behalten)} weitere unverändert"
                    + (f", {ohne} Parzellen ohne Zugang" if ohne > 0 else "") + "). Mit einem Handy testen!"]}

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

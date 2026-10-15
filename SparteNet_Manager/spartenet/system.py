"""SparteNet Manager – Systeminfo, alle Daten, Diagnose, Ansicht"""
from .ppsk import *  # noqa: F401,F403 – alle Namen der vorherigen Module


def _parallel(funktionen, anzahl=6):
    """führt {schluessel: funktion} parallel aus → {schluessel: (ergebnis, fehlertext)}"""
    aus = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=anzahl) as ex:
        zuk = {ex.submit(f): k for k, f in funktionen.items()}
        for z in concurrent.futures.as_completed(zuk):
            try:
                aus[zuk[z]] = (z.result(), "")
            except Exception as e:  # einzelne Quelle darf fehlen
                aus[zuk[z]] = (None, str(e)[:200])
    return aus


def _isp_metrics(g, konsole):
    """ISP-Messwerte (5 Minuten, 24 h) der Konsole aus der Site-Manager-API"""
    letzter = ""
    for pfad in ("/v1/isp-metrics/5m?duration=24h", "/ea/isp-metrics/5m?duration=24h"):
        try:
            a = g.cloud(pfad)
        except Fehler as e:
            letzter = str(e); continue
        for m in (a.get("data") or []):
            if m.get("hostId") == konsole:
                punkte, roh = [], {}
                def wert(w, *namen):
                    for n in namen:
                        if isinstance(w.get(n), (int, float)):
                            return float(w[n])
                    return None
                for p in m.get("periods") or []:
                    w = ((p.get("data") or {}).get("wan") or {})
                    if w:
                        roh = {"metricTime": p.get("metricTime"), **w}
                    punkte.append({"t": p.get("metricTime"), "down": wert(w, "download_kbps", "downloadKbps", "download"),
                                   "up": wert(w, "upload_kbps", "uploadKbps", "upload"),
                                   "lat": wert(w, "avgLatency"), "maxlat": wert(w, "maxLatency"), "verlust": wert(w, "packetLoss"),
                                   "uptime": wert(w, "uptime"), "isp": w.get("ispName")})
                punkte.sort(key=lambda x: x["t"] or "")
                return {"punkte": punkte, "roh": roh, "hinweise": _isp_bereinigen(punkte)}
        return {"punkte": [], "roh": {}, "hinweise": []}
    raise Fehler(letzter)


def _wan_verlauf(g):
    """Datenverkehr am Internet-Anschluss je 5 Minuten (letzte 24 h) aus den Berichten des Gateways"""
    jetzt = int(time.time() * 1000)
    body = {"attrs": ["wan-rx_bytes", "wan-tx_bytes", "wan2-rx_bytes", "wan2-tx_bytes", "num_sta", "time"], "start": jetzt - 86_400_000, "end": jetzt}
    roh = g.legacy_post("stat/report/5minutes.site", body)
    aus = []
    for r in roh:
        if not r.get("time"):
            continue
        rx = (r.get("wan-rx_bytes") or 0) + (r.get("wan2-rx_bytes") or 0)
        tx = (r.get("wan-tx_bytes") or 0) + (r.get("wan2-tx_bytes") or 0)
        aus.append({"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r["time"] / 1000)),
                    "down": rx * 8 / 300 / 1000, "up": tx * 8 / 300 / 1000, "clients": r.get("num_sta")})
    aus.sort(key=lambda x: x["t"])
    return aus


def _isp_bereinigen(punkte):
    """Einheiten prüfen und einzelne Ausreißer markieren. Werte in kbit/s."""
    hinweise = []
    for k, name in (("down", "Download"), ("up", "Upload")):
        werte = sorted(p[k] for p in punkte if p[k])
        if not werte:
            hinweise.append(f"{name}: die UniFi-Cloud liefert für diesen Zeitraum keine Werte (0 oder leer).")
            continue
        if len(werte) > 3 and werte[0] == werte[-1]:   # immer derselbe Wert = keine Messung (z. B. eingestellte Leitungsgeschwindigkeit)
            mbit = werte[0] / 1e6 if werte[0] > 2_000_000 else werte[0] / 1e3
            for p in punkte:
                p[k] = None
            hinweise.append(f"{name}: die UniFi-Cloud meldet immer denselben Wert ({mbit:g} Mbit/s) – das ist keine Messung und wird nicht gezeichnet.")
            continue
        median = werte[len(werte) // 2]
        if median > 2_000_000:   # > 2 Gbit/s als „kbps“ ist unrealistisch → Feld enthält bit/s
            for p in punkte:
                if p[k] is not None:
                    p[k] = p[k] / 1000
            hinweise.append(f"{name}: Werte kamen offenbar in bit/s statt kbit/s und wurden umgerechnet.")
            werte = [w / 1000 for w in werte]; median /= 1000
        grenze = max(median * 20, 1000)
        spitzen = [p for p in punkte if p[k] and p[k] > grenze]
        if spitzen and len(spitzen) <= max(3, len(punkte) // 50):
            for p in spitzen:
                p[k + "_roh"] = p[k]; p[k] = None
            hinweise.append(f"{name}: {len(spitzen)} unplausible Spitze(n) ausgeblendet (z. B. {spitzen[0][k + '_roh'] / 1000:,.0f} Mbit/s).".replace(",", "."))
    return hinweise


def akt_system(d):
    g, plan = Gateway(d), plan_berechnen(d["plan"])
    g.site_id()
    quellen = _parallel({
        "geraete": lambda: g.alle("/v1/sites/{site}/devices"),
        "clients": lambda: g.alle("/v1/sites/{site}/clients"),
        "sites": lambda: g.cloud("/v1/sites"),
        "isp": lambda: _isp_metrics(g, d["konsole_id"]),
        "verlauf": lambda: _wan_verlauf(g),
        "health": lambda: g.legacy_roh("stat/health"),
        "sta": lambda: g.legacy_roh("stat/sta"),
        "legdev": lambda: g.legacy_roh("stat/device"),
    })
    hinweise = []
    geraete = quellen["geraete"][0] or []
    if quellen["geraete"][1]:
        raise Fehler(quellen["geraete"][1])
    stats = _parallel({x["id"]: (lambda i=x["id"]: g.req("GET", f"/v1/sites/{{site}}/devices/{i}/statistics/latest")) for x in geraete if x.get("id")})
    details = _parallel({x["id"]: (lambda i=x["id"]: g.req("GET", f"/v1/sites/{{site}}/devices/{i}")) for x in geraete if x.get("id")})
    legdev = {str(x.get("mac", "")).lower(): x for x in (quellen["legdev"][0] or [])}
    zeilen = []
    for x in geraete:
        st = (stats.get(x.get("id")) or (None,))[0] or {}
        de = (details.get(x.get("id")) or (None,))[0] or {}
        ports = ((de.get("interfaces") or {}).get("ports") or [])
        radios = ((de.get("interfaces") or {}).get("radios") or [])
        st_rad = ((st.get("interfaces") or {}).get("radios") or [])
        up = st.get("uplink") or {}
        lg = legdev.get(str(x.get("macAddress", "")).lower(), {})
        zeilen.append({
            "gw": bool(re.match(r"(UDM|UDR|UCG|UXG|UDW|EFG|UX\b|Dream|Cloud Gateway|Gateway)", str(x.get("model") or ""), re.I)) or x.get("name") == d["konsole_name"],
            "name": x.get("name"), "modell": x.get("model"), "ip": x.get("ipAddress"), "status": x.get("state"),
            "firmware": x.get("firmwareVersion"), "update": bool(de.get("firmwareUpdatable")),
            "cpu": st.get("cpuUtilizationPct"), "ram": st.get("memoryUtilizationPct"),
            "load": st.get("loadAverage1Min"), "uptime": st.get("uptimeSec"),
            "rx_bps": up.get("rxRateBps"), "tx_bps": up.get("txRateBps"),
            "ports_auf": sum(1 for p in ports if p.get("state") == "UP"), "ports": len(ports),
            "poe": sum(1 for p in ports if (p.get("poe") or {}).get("enabled")),
            "funk": " · ".join(f"{r.get('frequencyGHz')} GHz K{r.get('channel', '?')}/{r.get('channelWidthMHz', '?')} MHz" for r in radios),
            "retries": " · ".join(f"{r.get('frequencyGHz')} GHz {r.get('txRetriesPct')} %" for r in st_rad if r.get("txRetriesPct") is not None),
            "clients": lg.get("num_sta"), "temp": next((t.get("value") for t in (lg.get("temperatures") or []) if isinstance(t, dict)), lg.get("general_temperature")),
        })
    fehlende_stats = sum(1 for k, v in stats.items() if v[1])
    if fehlende_stats:
        hinweise.append(f"Für {fehlende_stats} Gerät(e) liefert die Konsole keine Auslastung (offline oder nicht unterstützt).")

    # Clients je Netz
    clients = quellen["clients"][0] or []
    arten, je_netz = {}, {}
    for c in clients:
        arten[c.get("type") or "?"] = arten.get(c.get("type") or "?", 0) + 1
        _, wo = wo_ist(c.get("ipAddress", ""), plan)
        e = je_netz.setdefault(wo or "unbekannt", {"netz": wo or "unbekannt", "clients": 0, "rx": 0, "tx": 0})
        e["clients"] += 1

    # Datenverkehr je Client (nur klassische Schnittstelle)
    sta = quellen["sta"][0]
    top = []
    if sta:
        for c in sta:
            _, wo = wo_ist(c.get("ip", ""), plan)
            e = je_netz.setdefault(wo or "unbekannt", {"netz": wo or "unbekannt", "clients": 0, "rx": 0, "tx": 0})
            e["rx"] += int(c.get("rx_bytes") or 0); e["tx"] += int(c.get("tx_bytes") or 0)
            top.append({"name": c.get("name") or c.get("hostname") or c.get("mac"), "ip": c.get("ip"), "netz": wo,
                        "wlan": c.get("essid") or ("Kabel" if c.get("is_wired") else ""), "signal": c.get("signal"),
                        "rx": int(c.get("rx_bytes") or 0), "tx": int(c.get("tx_bytes") or 0), "seit": c.get("uptime")})
        top.sort(key=lambda c: c["rx"] + c["tx"], reverse=True)
    else:
        hinweise.append("Datenverkehr je Gerät/Parzelle braucht die klassische Schnittstelle – über die Cloud nicht verfügbar. Angezeigt werden Anzahl Clients je Netz.")

    # WAN / Internet
    wan = {}
    for h in quellen["health"][0] or []:
        if h.get("subsystem") == "wan":
            wan.update({"wan_ip": h.get("wan_ip"), "isp": h.get("isp_name"), "rx_bps": (h.get("rx_bytes-r") or 0) * 8,
                        "tx_bps": (h.get("tx_bytes-r") or 0) * 8, "status": h.get("status"), "gw_cpu": (h.get("gw_system-stats") or {}).get("cpu")})
        if h.get("subsystem") == "www":
            wan.update({"latenz": h.get("latency"), "speed_down": h.get("xput_down"), "speed_up": h.get("xput_up"), "speedtest": h.get("speedtest_lastrun")})
    site = {}
    for sx in ((quellen["sites"][0] or {}).get("data") or []):
        if sx.get("hostId") == d["konsole_id"]:
            stt = sx.get("statistics") or {}
            site = {"zaehler": stt.get("counts") or {}, "prozent": stt.get("percentages") or {},
                    "isp": (stt.get("ispInfo") or {}).get("name") or (stt.get("ispInfo") or {}).get("organization"),
                    "wans": stt.get("wans") or {}, "gateway": stt.get("gateway") or {}}
            break
    isp_erg = quellen["isp"][0] or {"punkte": [], "roh": {}, "hinweise": []}
    isp = isp_erg["punkte"]
    if quellen["isp"][1]:
        hinweise.append("Internet-Verlauf (ISP-Messwerte) nicht verfügbar: " + quellen["isp"][1])
    netze = sorted(je_netz.values(), key=lambda e: (-(e["rx"] + e["tx"]), -e["clients"], e["netz"]))
    return {"geraete": zeilen, "clients_arten": arten, "clients_gesamt": len(clients), "je_netz": netze, "top": top[:15],
            "wan": wan, "site": site, "isp": isp, "isp_roh": isp_erg["roh"], "verlauf": quellen["verlauf"][0] or [], "verlauf_fehler": quellen["verlauf"][1], "isp_hinweise": isp_erg["hinweise"], "hinweise": hinweise, "zeit": time.strftime("%H:%M:%S"),
            "log": [f"✔ Aktualisiert {time.strftime('%H:%M:%S')} – {len(zeilen)} Geräte, {len(clients)} Clients"] + [f"ℹ {h}" for h in hinweise]}


# ---------------------------------------------------------------- Alle Daten (nur lesen)
DATEN = {
    # Schlüssel: (Gruppe, Titel, Art, Pfad)   Art: int = Network-API (Liste), int1 = Einzelobjekt, cloud = Site Manager, leg = klassisch
    "info": ("Network-API", "Version / Info", "int1", "/v1/info"),
    "sites": ("Network-API", "Sites", "int", "/v1/sites"),
    "devices": ("Network-API", "Geräte", "int", "/v1/sites/{site}/devices"),
    "pending": ("Network-API", "Geräte zur Übernahme", "int", "/v1/pending-devices"),
    "clients": ("Network-API", "Clients", "int", "/v1/sites/{site}/clients"),
    "networks": ("Network-API", "Netze / VLANs", "int", "/v1/sites/{site}/networks"),
    "wifi": ("Network-API", "WLANs", "int", "/v1/sites/{site}/wifi/broadcasts"),
    "vouchers": ("Network-API", "Hotspot-Voucher", "int", "/v1/sites/{site}/hotspot/vouchers"),
    "wans": ("Network-API", "WAN-Anschlüsse", "int", "/v1/sites/{site}/wans"),
    "zones": ("Network-API", "Firewall-Zonen", "int", "/v1/sites/{site}/firewall/zones"),
    "policies": ("Network-API", "Firewall-Regeln", "int", "/v1/sites/{site}/firewall/policies"),
    "acl": ("Network-API", "ACL-Regeln", "int", "/v1/sites/{site}/acl-rules"),
    "tml": ("Network-API", "Traffic-Listen", "int", "/v1/sites/{site}/traffic-matching-lists"),
    "vpnserver": ("Network-API", "VPN-Server", "int", "/v1/sites/{site}/vpn/servers"),
    "vpntunnel": ("Network-API", "VPN-Tunnel (Site-to-Site)", "int", "/v1/sites/{site}/vpn/site-to-site-tunnels"),
    "radius": ("Network-API", "RADIUS-Profile", "int", "/v1/sites/{site}/radius/profiles"),
    "tags": ("Network-API", "Geräte-Tags", "int", "/v1/sites/{site}/device-tags"),
    "dpicat": ("Network-API", "DPI-Kategorien", "int", "/v1/dpi/categories"),
    "dpiapp": ("Network-API", "DPI-Anwendungen", "int", "/v1/dpi/applications"),
    "countries": ("Network-API", "Länder", "int", "/v1/countries"),
    "c_hosts": ("UniFi-Cloud (Site Manager)", "Konsolen im Konto", "cloud", "/v1/hosts"),
    "c_sites": ("UniFi-Cloud (Site Manager)", "Sites mit Statistik", "cloud", "/v1/sites"),
    "c_devices": ("UniFi-Cloud (Site Manager)", "Geräte aller Konsolen", "cloud", "/v1/devices"),
    "c_isp5": ("UniFi-Cloud (Site Manager)", "Internet-Messwerte 24 h (5 min)", "cloud", "/v1/isp-metrics/5m?duration=24h"),
    "c_isp1": ("UniFi-Cloud (Site Manager)", "Internet-Messwerte 7 Tage (1 h)", "cloud", "/v1/isp-metrics/1h?duration=7d"),
    "c_sdwan": ("UniFi-Cloud (Site Manager)", "SD-WAN-Konfigurationen", "cloud", "/ea/sd-wan-configs"),
    "l_health": ("Klassische Schnittstelle", "Zustand (Health)", "leg", "stat/health"),
    "l_sysinfo": ("Klassische Schnittstelle", "Systeminfo", "leg", "stat/sysinfo"),
    "l_device": ("Klassische Schnittstelle", "Geräte (ausführlich)", "leg", "stat/device"),
    "l_sta": ("Klassische Schnittstelle", "Aktive Clients mit Datenverkehr", "leg", "stat/sta"),
    "l_user": ("Klassische Schnittstelle", "Bekannte Clients", "leg", "rest/user"),
    "l_net": ("Klassische Schnittstelle", "Netzkonfiguration", "leg", "rest/networkconf"),
    "l_wlan": ("Klassische Schnittstelle", "WLAN-Konfiguration", "leg", "rest/wlanconf"),
    "l_pf": ("Klassische Schnittstelle", "Portweiterleitungen", "leg", "rest/portforward"),
    "l_fw": ("Klassische Schnittstelle", "Firewall-Regeln (alt)", "leg", "rest/firewallrule"),
    "l_fwg": ("Klassische Schnittstelle", "Firewall-Gruppen", "leg", "rest/firewallgroup"),
    "l_route": ("Klassische Schnittstelle", "Statische Routen", "leg", "rest/routing"),
    "l_portconf": ("Klassische Schnittstelle", "Port-Profile", "leg", "rest/portconf"),
    "l_setting": ("Klassische Schnittstelle", "Einstellungen", "leg", "rest/setting"),
    "l_alarm": ("Klassische Schnittstelle", "Alarme", "leg", "list/alarm"),
    "l_rogue": ("Klassische Schnittstelle", "Fremde WLANs in der Nähe", "leg", "stat/rogueap"),
    "l_ddns": ("Klassische Schnittstelle", "Dynamisches DNS", "leg", "rest/dynamicdns"),
    "v2_qos": ("Klassische Schnittstelle", "QoS-Regeln (Bandbreite)", "v2", "qos-rules"),
}
GEHEIM = re.compile(r"(pass|secret|psk|preshared|token|private_?key|^x_|cloud_key|api_?key)", re.I)


def _verdecke(obj):
    if isinstance(obj, dict):
        return {k: ("••••••" if GEHEIM.search(k) and v not in (None, "", [], {}, False, True) else _verdecke(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_verdecke(x) for x in obj]
    return obj


def _daten_holen(g, schluessel, maximal=1000):
    gruppe, titel, art, pfad = DATEN[schluessel]
    if art == "int":
        return g.alle(pfad, maximal)
    if art == "int1":
        return g.req("GET", pfad)
    if art == "cloud":
        a = g.cloud(pfad)
        return a.get("data", a) if isinstance(a, dict) else a
    if art == "v2":
        a = g.v2("GET", pfad)
        return a.get("data", a) if isinstance(a, dict) else a
    return g.legacy_roh(pfad)


def akt_daten(d, schluessel, geheim):
    if schluessel not in DATEN:
        raise Fehler("Unbekannte Datenquelle.")
    g = Gateway(d)
    roh = _daten_holen(g, schluessel)
    if not geheim:
        roh = _verdecke(roh)
    gruppe, titel, art, pfad = DATEN[schluessel]
    anzahl = len(roh) if isinstance(roh, list) else 1
    return {"titel": titel, "gruppe": gruppe, "pfad": pfad, "anzahl": anzahl, "roh": roh,
            "log": [f"✔ {titel}: {anzahl} {'Eintrag' if anzahl == 1 else 'Einträge'}" + (" (max. 1000 angezeigt)" if anzahl >= 1000 else "")
                    + ("" if geheim else " · Passwörter/Schlüssel verdeckt")]}


def akt_daten_pruefen(d):
    g = Gateway(d)
    g.site_id()
    def zaehle(k):
        art = DATEN[k][2]
        if art == "int":
            pfad = DATEN[k][3]
            a = g.req("GET", pfad + ("&" if "?" in pfad else "?") + "limit=1")
            return a.get("totalCount", len(a.get("data", []))) if isinstance(a, dict) else len(a)
        r = _daten_holen(g, k, 1)
        return len(r) if isinstance(r, list) else 1
    erg = _parallel({k: (lambda k=k: zaehle(k)) for k in DATEN}, anzahl=6)
    aus = {k: {"ok": not erg[k][1], "anzahl": erg[k][0], "fehler": erg[k][1]} for k in DATEN}
    ok = sum(1 for v in aus.values() if v["ok"])
    return {"quellen": aus, "log": [f"✔ {ok} von {len(DATEN)} Datenquellen über die Cloud lesbar."]}


PERSOENLICH = re.compile(r"^(email|fullName|firstName|lastName|phone|username|owner|ownerEmail)$", re.I)


def akt_diagnose(d, anonym=True):
    """Liest alle relevanten Antworten roh aus (nur GET), verdeckt Geheimnisse, optional anonymisiert – zum Weitergeben an den Support."""
    g = Gateway(d)
    stamm = g.int_base[len(CLOUD):]
    eintraege = []

    def hole(art, pfad):
        url = CLOUD + pfad if art == "cloud" else (g.int_base + pfad if art == "int" else (f"{g.v2_base}/{pfad}" if art == "v2" else f"{g.leg_base}/{pfad}"))
        t0 = time.time()
        try:
            code, a = http("GET", url, g.key)
        except Fehler as e:
            code, a = 0, str(e)
        eintraege.append({"art": art, "pfad": pfad, "code": code, "ms": int((time.time() - t0) * 1000), "antwort": a})
        return a if code == 200 else None

    for p in ("/v1/hosts", "/v1/sites", "/v1/devices", "/v1/isp-metrics/5m?duration=24h", "/v1/isp-metrics/1h?duration=7d", "/ea/isp-metrics/5m?duration=24h"):
        hole("cloud", p)
    hole("int", "/v1/info")
    sites = hole("int", "/v1/sites")
    site = ((sites or {}).get("data") or [{}])[0].get("id") if isinstance(sites, dict) else None
    hole("int", "/v1/pending-devices?limit=200")
    if site:
        b = f"/v1/sites/{site}"
        geraete = hole("int", b + "/devices?limit=200")
        for x in ((geraete or {}).get("data") or []) if isinstance(geraete, dict) else []:
            hole("int", f"{b}/devices/{x.get('id')}")
            hole("int", f"{b}/devices/{x.get('id')}/statistics/latest")
        for t in ("clients", "networks", "wifi/broadcasts", "hotspot/vouchers", "wans", "firewall/zones", "firewall/policies", "acl-rules",
                  "traffic-matching-lists", "vpn/servers", "vpn/site-to-site-tunnels", "radius/profiles", "device-tags"):
            hole("int", f"{b}/{t}?limit=200")
    for p in ("stat/health", "stat/sysinfo", "stat/device", "stat/sta", "rest/networkconf", "rest/wlanconf"):
        hole("leg", p)
    hole("v2", "qos-rules")
    jetzt = int(time.time() * 1000)
    for p in ("stat/report/5minutes.site", "stat/report/5minutes.gw"):
        t0 = time.time()
        body = {"attrs": ["wan-rx_bytes", "wan-tx_bytes", "wan2-rx_bytes", "wan2-tx_bytes", "num_sta", "time"], "start": jetzt - 86_400_000, "end": jetzt}
        try:
            code, a = http("POST", f"{g.leg_base}/{p}", g.key, body)
        except Fehler as e:
            code, a = 0, str(e)
        eintraege.append({"art": "legpost", "pfad": p, "code": code, "ms": int((time.time() - t0) * 1000), "antwort": a})

    # Geheimnisse und persönliche Daten entfernen
    namen, macs = {}, {}
    def anon(obj, client=False):
        if isinstance(obj, dict):
            aus = {}
            for k, v in obj.items():
                if GEHEIM.search(k) and v not in (None, "", [], {}, False, True):
                    aus[k] = "••••••"
                elif PERSOENLICH.match(k) and v:
                    aus[k] = "•"
                elif anonym and client and k in ("name", "hostname", "displayName") and isinstance(v, str) and v:
                    aus[k] = namen.setdefault(v, f"Client-{len(namen) + 1:02d}")
                elif anonym and client and k in ("macAddress", "mac") and isinstance(v, str) and v:
                    aus[k] = macs.setdefault(v.lower(), f"02:00:00:00:{(len(macs) + 1) // 256:02x}:{(len(macs) + 1) % 256:02x}")
                else:
                    aus[k] = anon(v, client)
            return aus
        if isinstance(obj, list):
            return [anon(x, client) for x in obj]
        return obj
    for e in eintraege:
        e["antwort"] = anon(e["antwort"], client=e["pfad"].split("?")[0].endswith(("/clients", "stat/sta")))
    paket = {"programm": f"SparteNet Manager {VERSION}", "erstellt": time.strftime("%Y-%m-%d %H:%M:%S"), "anonymisiert": anonym,
             "cloud_stamm": stamm, "eintraege": eintraege}
    datei = os.path.join(HIER, f"SparteNet_Diagnose_{time.strftime('%Y%m%d_%H%M')}.json")
    with open(datei, "w", encoding="utf-8") as f:
        json.dump(paket, f, ensure_ascii=False, indent=1)
    ok = sum(1 for e in eintraege if e["code"] == 200)
    return {"log": [f"✔ Diagnose-Datei erstellt: {datei}", f"{ok} von {len(eintraege)} Abfragen erfolgreich · Passwörter, Schlüssel und E-Mail-Adressen entfernt"
                    + (" · Clientnamen und MAC-Adressen anonymisiert" if anonym else ""), "Die Datei wird zusätzlich heruntergeladen – im Chat anhängen."],
            "name": os.path.basename(datei), "inhalt": json.dumps(paket, ensure_ascii=False, indent=1)}


ANSICHT_STANDARD = {"breite": 1200, "zoom": 0, "tabh": 520, "spalten": False, "kd": 430, "dl": 270}


def ansicht_pruefen(roh):
    """Bildschirm-Einstellungen der Oberfläche. 0 bei breite/zoom/tabh = automatisch."""
    a = dict(ANSICHT_STANDARD)
    roh = roh if isinstance(roh, dict) else {}
    grenzen = {"breite": (800, 8000, True), "zoom": (0.6, 3, True), "tabh": (200, 4000, True), "kd": (280, 1600, False), "dl": (200, 1000, False)}
    for k, (lo, hi, null_erlaubt) in grenzen.items():
        try:
            v = float(roh.get(k, a[k]))
        except (TypeError, ValueError):
            continue
        a[k] = 0 if (null_erlaubt and v == 0) else round(min(hi, max(lo, v)), 2)
    a["spalten"] = bool(roh.get("spalten", a["spalten"]))
    return a


def daten_liste():
    return [{"schluessel": k, "gruppe": v[0], "titel": v[1], "pfad": v[3]} for k, v in DATEN.items()]

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

"""SparteNet Manager – Handy & Tablet: Heimnetz, Tailscale, Überblick, Parzellen-Ansicht"""
from .auth import *  # noqa: F401,F403 – alle Namen der vorherigen Module


def lan_adressen():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.0.2.1", 9))  # sendet nichts, ermittelt nur die eigene Adresse
        ips.add(s.getsockname()[0]); s.close()
    except OSError:
        pass
    try:
        ips.update(a[4][0] for a in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    except OSError:
        pass
    return sorted(i for i in ips if not i.startswith(("127.", "169.254.")))


def _tailscale_exe():
    exe = shutil.which("tailscale")
    if not exe and os.name == "nt":
        for p in (r"C:\Program Files\Tailscale\tailscale.exe", r"C:\Program Files (x86)\Tailscale\tailscale.exe"):
            if os.path.exists(p):
                return p
    if not exe and sys.platform == "darwin" and os.path.exists("/Applications/Tailscale.app/Contents/MacOS/Tailscale"):
        return "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
    return exe


def tailscale_lage():
    exe = _tailscale_exe()
    if not exe:
        return {"installiert": False}
    try:
        r = subprocess.run([exe, "status", "--json"], capture_output=True, text=True, timeout=8)
        st = json.loads(r.stdout or "{}")
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        return {"installiert": True, "aktiv": False, "fehler": str(e)[:200]}
    dns = ((st.get("Self") or {}).get("DNSName") or "").rstrip(".")
    freigabe = False
    try:
        s = subprocess.run([exe, "serve", "status", "--json"], capture_output=True, text=True, timeout=8)
        freigabe = f"127.0.0.1:{PORT}" in s.stdout or f"localhost:{PORT}" in s.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {"installiert": True, "aktiv": st.get("BackendState") == "Running", "name": dns,
            "url": f"https://{dns}/" if dns else "", "freigabe": freigabe}


def akt_tailscale(an):
    exe = _tailscale_exe()
    if not exe:
        raise Fehler("Tailscale ist auf diesem PC nicht installiert (tailscale.com/download).")
    befehl = [exe, "serve", "--bg", f"http://127.0.0.1:{PORT}"] if an else [exe, "serve", "--https=443", "off"]
    try:
        r = subprocess.run(befehl, capture_output=True, text=True, timeout=25)
    except subprocess.TimeoutExpired:
        raise Fehler("Tailscale antwortet nicht. Evtl. muss HTTPS im Tailscale-Konto erst erlaubt werden: login.tailscale.com → DNS → „HTTPS Certificates“ aktivieren, dann erneut.")
    except OSError as e:
        raise Fehler(f"Tailscale konnte nicht gestartet werden: {e}")
    text = (r.stdout + "\n" + r.stderr).strip()
    journal(f"Tailscale-Freigabe {'eingeschaltet' if an else 'ausgeschaltet'} (Rückgabe {r.returncode})")
    if r.returncode != 0:
        hilfe = ""
        if "denied" in text.lower() or "operator" in text.lower() or "permission" in text.lower():
            hilfe = "\nLinux: einmal im Terminal „sudo tailscale set --operator=$USER“ ausführen, dann erneut."
        raise Fehler(f"Tailscale meldet einen Fehler:\n{text[:600]}{hilfe}")
    lage = tailscale_lage()
    return {"log": [f"✔ Tailscale-Freigabe {'eingeschaltet' if an else 'ausgeschaltet'}."] + ([text[:600]] if text else [])
            + ([f"App-Adresse: {lage['url']}"] if an and lage.get("url") else []), "tailscale": lage}


def akt_fern(d):
    f = fern_daten(d)
    adressen = [f"http://{ip}:{PORT}/" for ip in lan_adressen()] if LAUFZEIT["host"] == "0.0.0.0" else []
    ts = tailscale_lage()
    urls = ([ts["url"]] if ts.get("freigabe") and ts.get("url") else []) + adressen
    jetzt = time.time()
    geraete = [{"geraet": v.get("geraet") or "?", "seit": v.get("seit", "")} for v in f["sitzungen"].values() if isinstance(v, dict) and v.get("bis", 0) > jetzt]
    with _AUTH_SESSIONS_LOCK:
        geraete.extend({"geraet": v["geraet"], "seit": v["seit"]} for v in _AUTH_SESSIONS.values() if v["bis"] > jetzt)
    return {"lan": LAUFZEIT["host"] == "0.0.0.0", "lan_aktiv": LAUFZEIT["host"] == "0.0.0.0", "lan_env": HOST_OVERRIDE is not None, "pin_gesetzt": bool(f["pin"].get("hash")), "geraete": geraete,
            "adressen": adressen, "tailscale": ts, "qr": {u: qr_svg(u, rand=2) for u in urls}}


def akt_fern_speichern(d, b):
    f, log = fern_daten(d), []
    if b.get("pin"):
        pin_setzen(d, b["pin"]); log.append("✔ PIN gespeichert. Bereits angemeldete Handys müssen sich neu anmelden.")
    if b.get("abmelden"):
        f["sitzungen"] = {}
        with _AUTH_SESSIONS_LOCK:
            _AUTH_SESSIONS.clear()
        log.append("✔ Alle Handys, Tablets und Browser abgemeldet.")
    if "lan" in b:
        if HOST_OVERRIDE is not None:
            raise Fehler("Die Server-Bindung wird durch SPARTENET_HOST gesteuert; Heimnetz hier nicht umschaltbar.")
        f["lan"] = bool(b["lan"])
        if f["lan"] != (LAUFZEIT["host"] == "0.0.0.0"):
            log.append(f"✔ Zugriff aus dem Heimnetz {'ein' if f['lan'] else 'aus'}geschaltet – wirkt nach einem Neustart des Managers (Beenden und wieder starten)."
                       + (" Windows fragt dann evtl. nach der Firewall: „Private Netzwerke“ erlauben." if f["lan"] and os.name == "nt" else ""))
        else:
            log.append(f"✔ Zugriff aus dem Heimnetz bleibt {'ein' if f['lan'] else 'aus'}.")
    speichere(d)
    journal("Handy-Zugriff geändert: " + ", ".join(k for k in ("pin", "abmelden", "lan") if k in b))
    return {"log": log or ["Nichts geändert."]}


def akt_start(d):
    from .kalkulation import akt_kalkulation  # erst hier, weil die Kalkulation später geladen wird
    g = Gateway(d)
    erg = _parallel({"geraete": lambda: g.alle("/v1/sites/{site}/devices"), "clients": lambda: g.alle("/v1/sites/{site}/clients"),
                     "health": lambda: g.legacy_roh("stat/health")}, anzahl=3)
    geraete, fehler = erg["geraete"]
    if fehler:
        raise Fehler(fehler)
    clients = erg["clients"][0] or []
    health = {h.get("subsystem"): h for h in (erg["health"][0] or [])}
    online = [x for x in geraete if str(x.get("state", "")).upper() == "ONLINE"]
    offline = [x.get("name") or x.get("model") or "?" for x in geraete if x not in online]
    wan, www = health.get("wan") or {}, health.get("www") or {}
    kacheln = [
        {"t": "Geräte online", "v": f"{len(online)}/{len(geraete)}", "a": "gut" if not offline else "schlecht", "k": ("offline: " + ", ".join(offline)) if offline else "alle erreichbar"},
        {"t": "Endgeräte im WLAN/LAN", "v": len(clients), "a": "gut", "k": f"{sum(1 for c in clients if c.get('type') == 'WIRELESS')} per WLAN"},
    ]
    if wan or www:
        kacheln.append({"t": "Internet", "v": "online" if (wan.get("status") or www.get("status", "ok")) == "ok" else "gestört",
                        "a": "gut" if (wan.get("status") or "ok") == "ok" else "schlecht",
                        "k": " · ".join(x for x in (wan.get("isp_name") or "", f"{www.get('latency')} ms" if www.get("latency") is not None else "") if x)})
    try:
        kg = akt_kalkulation(d)["gesamt"]
        if kg["parzellen_konf"]:
            kacheln.append({"t": "Auslastung", "v": f"{kg['auslastung_konf']:.0%}", "a": "gut" if kg["auslastung_konf"] >= 0.6 else "", "k": f"{kg['gebucht']} von {kg['parzellen_konf']} Parzellen gebucht"})
    except Fehler:
        pass
    return {"kacheln": kacheln, "konsole": d.get("konsole_name", ""), "zeit": time.strftime("%H:%M"), "log": []}


def akt_parzelle(d, kz, p):
    try:
        p = int(p)
    except (TypeError, ValueError):
        raise Fehler("Bitte eine Parzellen-Nummer eingeben.")
    plan = plan_aktiv(d)
    sp = next((s for s in plan["sparten"] if s["kz"] == kz), None)
    if not sp:
        raise Fehler("Sparte nicht im Plan.")
    if not 1 <= p <= sp["n"]:
        raise Fehler(f"Sparte {kz} hat die Parzellen 1 bis {sp['n']}.")
    netz = next((n for n in plan["netze"] if n["sparte"] == kz and str(n.get("parzelle", "")) == str(p)), None) \
        or next((n for n in plan["netze"] if n["sparte"] == kz and n["name"] == NETZ_PARZELLE.format(kz=kz, p=p)), None)
    zeile = next((z for z in lese_ppsk(kz) if str(z.get("Parzelle")) == str(p)), None)
    if not zeile or not zeile.get("Passwort"):
        raise Fehler(f"Für Parzelle {p} ist noch kein WLAN-Passwort vergeben (Einrichten → Schritt 3) oder der Zugang ist gesperrt.")
    ssid = wlan_ssid(d, kz)
    return {"parzelle": p, "sparte": sp["name"], "netz": zeile.get("Netz") or (netz or {}).get("name", ""), "vlan": zeile.get("VLAN") or (netz or {}).get("vlan", ""),
            "subnetz": (netz or {}).get("netz", ""), "wlan": ssid, "passwort": zeile["Passwort"],
            "qr": qr_svg(wlan_qr_text(ssid, zeile["Passwort"]), rand=2), "log": []}

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

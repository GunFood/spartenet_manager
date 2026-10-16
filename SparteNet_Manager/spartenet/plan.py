"""SparteNet Manager – Planung: Sparten, Parzellen, VLANs, Netze, Passwort-Regeln, Excel-Import"""
from .cloud import *  # noqa: F401,F403 – alle Namen der vorherigen Module


# =============================================================== Plan
def _plan_standort(roh, g, pre):
    """Schema „Standort“ (aus der Netzplanung): VLAN Parzelle = 1000 + 200·(Block−1) + Parzelle, Dienstnetze 100/200/300 + Sparten-ID"""
    sparten = []
    for s in roh.get("sparten", []):
        if not s.get("name"):
            continue
        try:
            sid, n, block = int(s.get("sid") or 0), int(s.get("n") or 0), int(s.get("block") or 0)
            p_von, p_bis = int(s.get("p_von") or 1), int(s.get("p_bis") or s.get("n") or 0)
        except (TypeError, ValueError):
            raise Fehler(f"Sparte „{s.get('name')}“: Sparten-ID, Parzellen, Block und Bereich müssen Zahlen sein.")
        kz = str(s.get("kz") or "").strip()
        if not kz or not 1 <= sid <= 254 or not 1 <= block <= 15 or not 1 <= p_von <= p_bis <= 199 or n < p_bis:
            raise Fehler(f"Sparte „{s.get('name')}“: Kürzel, Sparten-ID (1–254), VLAN-Block (1–15) und Parzellen von–bis (1–199) prüfen.")
        sparten.append({"name": str(s["name"]), "kz": kz, "sid": sid, "n": n, "slot": block, "block": block, "p_von": p_von, "p_bis": p_bis,
                        "dienst": bool(s.get("dienst", True))})
    if len({s["sid"] for s in sparten}) != len(sparten) or len({s["kz"] for s in sparten}) != len(sparten) or len({s["block"] for s in sparten}) != len(sparten):
        raise Fehler("Sparten-ID, Kürzel und VLAN-Block müssen je Sparte einmalig sein.")
    parz = sum(s["p_bis"] - s["p_von"] + 1 for s in sparten)
    if parz > 55:
        raise Fehler(f"{parz} Parzellen an einem Gateway – höchstens 55 (Netzplanung: 55 Parzellen je Gateway).")
    return sparten


def plan_berechnen(roh):
    sparten, slot = [], 1
    g, pre = int(roh.get("gateway") or 1), str(roh.get("praefix") or "SparteNet.de")
    schema = "standort" if roh.get("schema") == "standort" else "steckplatz"
    if not 1 <= g <= 254:
        raise Fehler("Gateway-Nummer 1–254.")
    if schema == "standort":
        sparten = _plan_standort(roh, g, pre)
        roh = {**roh, "sparten": []}
    for s in roh.get("sparten", []):
        if not s.get("name") or not s.get("n"):
            continue
        try:
            n, sid = int(s["n"]), int(s.get("sid") or 0)
        except (TypeError, ValueError):
            raise Fehler(f"Sparte „{s.get('name')}“: Sparten-ID und Parzellen müssen Zahlen sein.")
        kz = str(s.get("kz") or "").strip()
        if not kz or not 1 <= sid <= 254 or not 1 <= n <= 199:
            raise Fehler(f"Sparte „{s.get('name')}“: Kürzel, Sparten-ID (1–254) und Parzellen (1–199) prüfen.")
        sparten.append({"name": str(s["name"]), "kz": kz, "sid": sid, "n": n, "slot": slot})
        slot += 2 if n > 99 else 1
    if slot - 1 > 10:
        raise Fehler("Mehr als 10 Steckplätze belegt.")
    for s in sparten:
        s.setdefault("p_von", 1); s.setdefault("p_bis", s["n"]); s.setdefault("dienst", True)
    if len({s["sid"] for s in sparten}) != len(sparten) or len({s["kz"] for s in sparten}) != len(sparten):
        raise Fehler("Sparten-ID und Kürzel müssen je Sparte einmalig sein.")
    netze = []
    for s in sparten:
        f = {"kz": s["kz"], "pre": pre}
        def e(art, name, vlan, x, ssid, parz="", zugang=""):
            return {"sparte": s["kz"], "name": name, "vlan": vlan, "x": x, "sid": s["sid"], "netz": f"10.{s['sid']}.{x}.0/24",
                    "maske": "255.255.255.0", "router": f"10.{s['sid']}.{x}.1", "dhcp_start": f"10.{s['sid']}.{x}.10",
                    "dhcp_ende": f"10.{s['sid']}.{x}.250", "art": art, "ssid": ssid, "parzelle": parz, "zugang": zugang}
        if schema == "standort":
            vp = lambda p: 1000 + 200 * (s["block"] - 1) + p
            vd = {"vorstand": 100 + s["sid"], "gaeste": 200 + s["sid"], "technik": 300 + s["sid"]}
        else:
            vp = lambda p: vlan_parzelle(s["slot"], p)
            vd = {"vorstand": 2000 + s["slot"] * 10 + 1, "gaeste": 2000 + s["slot"] * 10 + 2, "technik": 2000 + s["slot"] * 10 + 9}
        for p in range(s["p_von"], s["p_bis"] + 1):
            netze.append(e("parzelle", NETZ_PARZELLE.format(p=p, **f), vp(p), p, WLAN_PAECHTER.format(**f), p, f"Passwort Parzelle {p}"))
        if s["dienst"]:
            netze.append(e("vorstand", NETZ_VORSTAND.format(**f), vd["vorstand"], 200, WLAN_VORSTAND.format(**f), "", "eigenes WLAN"))
            netze.append(e("gaeste", NETZ_GAESTE.format(**f), vd["gaeste"], 201, WLAN_GAESTE.format(**f), "", "Voucher"))
            netze.append(e("technik", NETZ_TECHNIK.format(**f), vd["technik"], 250, "", "", "Switches, Access Points"))
    if len({n["vlan"] for n in netze}) != len(netze):
        raise Fehler("VLAN-IDs im Plan sind nicht eindeutig.")
    return {"gateway": g, "gatewayname": str(roh.get("gatewayname") or f"Gateway {g}"), "praefix": pre, "sparten": sparten, "netze": netze, "schema": schema,
            "gateway_netz": {"name": "Gateway", "vlan": 1, "netz": f"10.0.{g}.0/24", "router": f"10.0.{g}.1"}}


def excel_import(roh_bytes):
    """liest Blatt „Eingabe“ des VLAN-Planers ohne Zusatzpakete"""
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    try:
        z = zipfile.ZipFile(io.BytesIO(roh_bytes))
    except zipfile.BadZipFile:
        raise Fehler("Das ist keine Excel-Datei (.xlsx).")
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rid = next((s.get(R + "id") for s in wb.iter(M + "sheet") if s.get("name") == "Eingabe"), None)
    if not rid:
        raise Fehler("Blatt „Eingabe“ nicht gefunden – ist das der VLAN-Planer?")
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    ziel = next(r.get("Target") for r in rels if r.get("Id") == rid).lstrip("/")
    ziel = ziel if ziel.startswith("xl/") else "xl/" + ziel
    strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(M + "si"):
            strings.append("".join(t.text or "" for t in si.iter(M + "t")))
    zellen = {}
    for c in ET.fromstring(z.read(ziel)).iter(M + "c"):
        v, t = c.find(M + "v"), c.get("t")
        if t == "inlineStr":
            wert = "".join(x.text or "" for x in c.iter(M + "t"))
        elif v is None or t == "e":
            continue  # leer oder Formel ohne gespeichertes Ergebnis bzw. mit Fehler
        elif t == "s":
            wert = strings[int(v.text)]
        else:
            wert = v.text
        zellen[c.get("r")] = wert
    def zahl(x):
        try:
            return int(float(x))
        except (TypeError, ValueError):
            return 0
    sparten = [{"name": zellen[f"B{r}"], "kz": zellen.get(f"C{r}", ""), "sid": zahl(zellen.get(f"D{r}")), "n": zahl(zellen.get(f"E{r}"))}
               for r in range(9, 19) if zellen.get(f"B{r}") and zellen.get(f"E{r}")]
    if not sparten and any(zellen.get(f"B{r}") is None for r in range(9, 19)) and "Sparten" in [s.get("name") for s in wb.iter(M + "sheet")]:
        raise Fehler("Im VLAN-Planer sind für das gewählte Gateway keine Sparten eingetragen – oder die Datei wurde ohne berechnete Werte gespeichert. "
                     "In Excel/LibreOffice öffnen, unter „Eingabe“ B4 das Gateway wählen, speichern und erneut übernehmen.")
    plan = {"gateway": zahl(zellen.get("B4")) or 1, "gatewayname": zellen.get("B5", ""), "praefix": zellen.get("B6", "SparteNet.de"), "sparten": sparten}
    plan_berechnen(plan)
    return plan


PW_REGEL_STANDARD = {"praefix": "SN", "ziffern": 10}
_PW_SPERRE = threading.Lock()


def pw_regel(d=None):
    r = dict(PW_REGEL_STANDARD)
    roh = (d or lade()).get("pw_regel") or {}
    pre = str(roh.get("praefix", r["praefix"]))
    if re.fullmatch(r"[A-Za-z0-9\-_.]{0,10}", pre):
        r["praefix"] = pre
    try:
        r["ziffern"] = min(30, max(6, int(roh.get("ziffern", r["ziffern"]))))
    except (TypeError, ValueError):
        pass
    if len(r["praefix"]) + r["ziffern"] < 8:          # WPA2 verlangt mindestens 8 Zeichen
        r["ziffern"] = 8 - len(r["praefix"])
    return r


def _hash(pw):
    import hashlib
    return hashlib.sha256(("SparteNet|" + pw).encode("utf-8")).hexdigest()


def _register_lesen():
    if DB:
        return {r[0] for r in DB.sql("SELECT pruefsumme FROM sn_passwort_register", alle=True)}
    try:
        with open(REGISTER, encoding="utf-8") as f:
            return {z.strip() for z in f if z.strip()}
    except OSError:
        return set()


def register_eintragen(passwoerter):
    """Merkt sich jedes jemals vergebene Passwort (nur als Prüfsumme, nicht im Klartext)."""
    vorhanden = _register_lesen()
    neu = [_hash(p) for p in passwoerter if p and _hash(p) not in vorhanden]
    if neu and DB:
        DB.sql("INSERT IGNORE INTO sn_passwort_register (pruefsumme) VALUES (%s)", [(h,) for h in neu], viele=True)
    elif neu:
        with open(REGISTER, "a", encoding="utf-8") as f:
            f.write("\n".join(neu) + "\n")
        try:
            os.chmod(REGISTER, 0o600)
        except OSError:
            pass


def alle_belegten():
    """Klartext aller aktuell vergebenen Passwörter aller Sparten (PPSK_*.csv)"""
    belegt = set()
    for f in ablage_liste("PPSK_", ".csv"):
        try:
            belegt |= {z.get("Passwort", "") for z in lese_ppsk(f[5:-4])}
        except Exception:
            pass
    belegt.discard("")
    return belegt


def passwoerter_erzeugen(anzahl, d=None, zusaetzlich=()):
    """Neue Passwörter nach Regel Präfix + Ziffern, nie doppelt: weder in einer Sparte noch je zuvor vergeben."""
    r = pw_regel(d)
    with _PW_SPERRE:
        belegt, reg = alle_belegten() | set(zusaetzlich), _register_lesen()
        aus = []
        while len(aus) < anzahl:
            pw = r["praefix"] + "".join(secrets.choice("0123456789") for _ in range(r["ziffern"]))
            if pw in belegt or _hash(pw) in reg:
                continue
            belegt.add(pw); aus.append(pw)
        register_eintragen(aus)
    return aus


def passwort(d=None):
    return passwoerter_erzeugen(1, d)[0]


def passwort_fehler(pw):
    """WPA2-Passphrase: 8–63 druckbare ASCII-Zeichen. Leer = Parzelle ohne Zugang."""
    if pw == "":
        return ""
    if not 8 <= len(pw) <= 63:
        return "muss 8 bis 63 Zeichen lang sein"
    if any(not 32 <= ord(c) <= 126 for c in pw):
        return "nur Buchstaben A–Z, Ziffern und einfache Sonderzeichen (keine Umlaute)"
    if pw != pw.strip():
        return "darf nicht mit einem Leerzeichen beginnen oder enden"
    return ""


def ppsk_datei(kz):
    return f"PPSK_{kz}.csv"


def lese_ppsk(kz):
    roh = ablage_lesen(ppsk_datei(kz))
    if roh is None:
        return []
    return list(csv.DictReader(io.StringIO(roh.decode("utf-8-sig")), delimiter=";"))


def schreibe_ppsk(kz, zeilen):
    f = io.StringIO(newline="")
    w = csv.DictWriter(f, fieldnames=["Parzelle", "Netz", "VLAN", "WLAN", "Passwort"], delimiter=";", extrasaction="ignore")
    w.writeheader(); w.writerows(zeilen)
    ablage_schreiben(ppsk_datei(kz), f.getvalue().encode("utf-8-sig"))


def wo_ist(ip, plan):
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return ("unbekannt", "")
    if a in ipaddress.ip_network(plan["gateway_netz"]["netz"]):
        return ("gateway", "Gateway-/Technik-Netz")
    for n in plan["netze"]:
        if a in ipaddress.ip_network(n["netz"]):
            return (n["art"], n["name"])
    return ("ausserhalb", "außerhalb des Plans")

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

"""SparteNet Manager – Aktualisierung von GitHub nach dem Vorbild von Nextcloud

Ablauf: neue Version auf GitHub prüfen → Sicherung → herunterladen → Inhalt prüfen → entpacken → Selbsttest
→ Wartungsmodus → umschalten → Neustart im selben Prozess. Die neue Version liegt im Datenordner unter
updates/<Version>-<Commit>/; SparteNet_Manager.py startet beim nächsten Start die neueste vorhandene Version
(aus dem Datenordner oder die mitgelieferte, je nachdem welche neuer ist). Zurück geht es jederzeit mit
„Vorherige Version“ – auch automatisch, wenn eine neue Version nicht startet.
"""
from .benutzer import *  # noqa: F401,F403 – alle Namen der vorherigen Module

UPDATE_REPO = os.environ.get("SPARTENET_UPDATE_REPO", "GunFood/spartenet_manager").strip()
UPDATE_API = os.environ.get("SPARTENET_UPDATE_API", "https://api.github.com").rstrip("/")
UPDATE_UNTERORDNER = "SparteNet_Manager"          # Ordner im Repository, in dem der Manager liegt
UPDATE_DIR = os.path.join(HIER, "updates")
UPDATE_AKTIV = os.path.join(UPDATE_DIR, "aktiv.json")
UPDATE_MAX_BYTES = 60_000_000
_UPDATE_TOKEN_FILE = os.environ.get("SPARTENET_UPDATE_TOKEN_FILE", "").strip()
CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # Ordner mit SparteNet_Manager.py dieser Version
UPDATE_STANDARD = {"kanal": "main", "automatisch": False, "stunden": 24}
WARTUNG = {"an": False, "text": ""}
_UPDATE = {"lage": None, "geprueft": 0.0, "laeuft": False, "schritte": [], "fehler": "", "fertig": False, "lock": threading.Lock()}
UPDATE_SCHRITTE = ["Neue Version prüfen", "Sicherung der Daten", "Herunterladen", "Inhalt prüfen", "Entpacken", "Selbsttest",
                   "Wartungsmodus", "Umschalten und neu starten"]


def version_tupel(v):
    return tuple(int(x) for x in re.findall(r"\d+", str(v or "0"))[:4]) or (0,)


def update_einstellungen(d):
    u = dict(UPDATE_STANDARD)
    roh = d.get("update") if isinstance(d.get("update"), dict) else {}
    if roh.get("kanal") in ("main", "release") or str(roh.get("kanal", "")).startswith("branch:"):
        u["kanal"] = roh["kanal"]
    u["automatisch"] = bool(roh.get("automatisch", False))
    try:
        u["stunden"] = max(0, min(168, int(roh.get("stunden", 24))))
    except (TypeError, ValueError):
        pass
    return u


def _token():
    if not _UPDATE_TOKEN_FILE:
        return os.environ.get("SPARTENET_UPDATE_TOKEN", "").strip()
    try:
        with open(_UPDATE_TOKEN_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _gh(pfad, roh=False, max_bytes=2_000_000):
    """GitHub-API (öffentlich; mit SPARTENET_UPDATE_TOKEN_FILE auch private Repositories) – Token wird nie protokolliert"""
    url = pfad if pfad.startswith("https://") else f"{UPDATE_API}{pfad}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": f"SparteNet-Manager/{VERSION}",
                                               "X-GitHub-Api-Version": "2022-11-28"})
    t = _token()
    if t:
        req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
            daten = r.read(max_bytes + 1)
    except urllib.error.HTTPError as e:
        hinweis = {401: "Zugangs-Token ungültig", 403: "GitHub verweigert den Zugriff (Abfragegrenze erreicht? später erneut)",
                   404: "Repository, Zweig oder Version nicht gefunden (bei privatem Repository: SPARTENET_UPDATE_TOKEN_FILE setzen)"}.get(e.code, "")
        raise Fehler(f"GitHub antwortet mit {e.code}{' – ' + hinweis if hinweis else ''}.")
    except (urllib.error.URLError, OSError) as e:
        raise Fehler(f"GitHub nicht erreichbar ({getattr(e, 'reason', e)}). Hat der Server Internetzugang?")
    if len(daten) > max_bytes:
        raise Fehler("Antwort von GitHub ist zu groß.")
    return daten if roh else json.loads(daten.decode("utf-8"))


def _version_aus_quelltext(text):
    m = re.search(r'^VERSION\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else None


def update_pruefen(d, still=False):
    """fragt GitHub nach der neuesten Version im gewählten Kanal"""
    e = update_einstellungen(d)
    kanal = e["kanal"]
    if kanal == "release":
        r = _gh(f"/repos/{UPDATE_REPO}/releases/latest")
        ref = r.get("tag_name") or ""
        c = _gh(f"/repos/{UPDATE_REPO}/commits/{urllib.parse.quote(ref)}")
        notiz, datum = (r.get("body") or r.get("name") or "").strip(), r.get("published_at", "")
    else:
        ref = kanal.split(":", 1)[1] if kanal.startswith("branch:") else "main"
        c = _gh(f"/repos/{UPDATE_REPO}/commits/{urllib.parse.quote(ref)}")
        notiz, datum = (c.get("commit", {}).get("message") or "").strip(), c.get("commit", {}).get("committer", {}).get("date", "")
    sha = c.get("sha", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise Fehler("GitHub hat keine gültige Version geliefert.")
    quelle = _gh(f"/repos/{UPDATE_REPO}/contents/{UPDATE_UNTERORDNER}/spartenet/basis.py?ref={sha}")
    try:
        text = base64.b64decode(quelle.get("content", "")).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        text = ""
    neu = _version_aus_quelltext(text)
    if not neu:
        raise Fehler("Auf GitHub ist keine Versionsnummer zu finden (spartenet/basis.py).")
    ist_sha = installierter_commit()
    # neuer: höhere Versionsnummer – oder gleiche Nummer, aber ein anderer Stand auf GitHub (Korrekturen ohne neue Nummer)
    verfuegbar = version_tupel(neu) > version_tupel(VERSION) or (version_tupel(neu) == version_tupel(VERSION) and bool(ist_sha) and ist_sha != sha)
    lage = {"aktuell": VERSION, "neu": neu, "sha": sha,
            "kurz": sha[:7], "kanal": kanal, "ref": ref, "datum": datum[:16].replace("T", " "), "installiert": (ist_sha or "")[:7],
            "notiz": notiz[:3000], "verfuegbar": verfuegbar, "zeit": time.strftime("%Y-%m-%d %H:%M"), "repo": UPDATE_REPO}
    with _UPDATE["lock"]:
        _UPDATE["lage"], _UPDATE["geprueft"] = lage, time.time()
    if not still:
        LOG.info("Update-Prüfung: installiert %s, auf GitHub %s (%s)", VERSION, neu, sha[:7])
    return lage


def installierter_commit():
    """Commit der laufenden Version, wenn sie über die Aktualisierung installiert wurde (sonst leer)"""
    a = update_aktiv_lesen()
    if a.get("ordner") and a.get("sha") and os.path.abspath(CODE_DIR) == os.path.abspath(os.path.join(UPDATE_DIR, a["ordner"])):
        return str(a["sha"])
    return ""


def update_aktiv_lesen():
    try:
        with open(UPDATE_AKTIV, encoding="utf-8") as f:
            a = json.load(f)
        return a if isinstance(a, dict) else {}
    except (OSError, ValueError):
        return {}


def _update_aktiv_schreiben(a):
    os.makedirs(UPDATE_DIR, exist_ok=True)
    tmp = UPDATE_AKTIV + ".neu"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(a, f, ensure_ascii=False, indent=1)
    os.replace(tmp, UPDATE_AKTIV)


def update_versionen():
    """installierte Versionen im Datenordner"""
    aus = []
    if os.path.isdir(UPDATE_DIR):
        for x in sorted(os.listdir(UPDATE_DIR)):
            p = os.path.join(UPDATE_DIR, x)
            if os.path.isfile(os.path.join(p, "SparteNet_Manager.py")) and os.path.isdir(os.path.join(p, "spartenet")):
                try:
                    with open(os.path.join(p, "spartenet", "basis.py"), encoding="utf-8") as f:
                        v = _version_aus_quelltext(f.read())
                except OSError:
                    v = None
                aus.append({"ordner": x, "version": v or "?", "pfad": p})
    return aus


def _schritt(i, status, text=""):
    with _UPDATE["lock"]:
        s = _UPDATE["schritte"]
        while len(s) <= i:
            s.append({"name": UPDATE_SCHRITTE[len(s)], "status": "offen", "text": ""})
        s[i].update(status=status, text=text)
    if text:
        LOG.info("Update – %s: %s %s", UPDATE_SCHRITTE[i], status, text)


UPDATE_SITZUNGEN = os.path.join(UPDATE_DIR, "sitzungen_neustart.json")


def _sitzungen_sichern():
    """angemeldete Browser bleiben über den Neustart angemeldet (nur Prüfsummen der Sitzungen, 5 Minuten gültig)"""
    try:
        with _AUTH_SESSIONS_LOCK:
            daten = {"zeit": time.time(), "sitzungen": dict(_AUTH_SESSIONS)}
        os.makedirs(UPDATE_DIR, exist_ok=True)
        with open(UPDATE_SITZUNGEN, "w", encoding="utf-8") as f:
            json.dump(daten, f)
        os.chmod(UPDATE_SITZUNGEN, 0o600)
    except OSError as e:
        LOG.warning("Sitzungen konnten nicht für den Neustart gesichert werden: %s", e)


def update_sitzungen_uebernehmen():
    try:
        with open(UPDATE_SITZUNGEN, encoding="utf-8") as f:
            daten = json.load(f)
    except (OSError, ValueError):
        return 0
    try:
        os.remove(UPDATE_SITZUNGEN)
    except OSError:
        pass
    if not isinstance(daten, dict) or time.time() - float(daten.get("zeit", 0)) > 300:
        return 0
    jetzt, n = time.time(), 0
    with _AUTH_SESSIONS_LOCK:
        for k, v in (daten.get("sitzungen") or {}).items():
            if isinstance(v, dict) and re.fullmatch(r"[0-9a-f]{64}", k) and float(v.get("bis", 0)) > jetzt:
                _AUTH_SESSIONS[k] = v
                n += 1
    return n


def _neustart(verzoegerung=1.5):
    """Prozess durch sich selbst ersetzen (gleiche PID, z. B. im Docker-Container) – startet dann die neue Version"""
    def los():
        time.sleep(verzoegerung)
        _sitzungen_sichern()
        LOG.info("Neustart für Update")
        try:
            logging.shutdown()
        except Exception:
            pass
        os.execv(sys.executable, [sys.executable] + sys.argv)
    threading.Thread(target=los, daemon=True).start()


def _entpacken(roh, ziel):
    """nur den Ordner SparteNet_Manager/ aus dem GitHub-Archiv, ohne Pfade außerhalb des Ziels"""
    try:
        z = zipfile.ZipFile(io.BytesIO(roh))
    except zipfile.BadZipFile:
        raise Fehler("Das heruntergeladene Archiv ist beschädigt.")
    namen = z.namelist()
    if not namen:
        raise Fehler("Das Archiv ist leer.")
    wurzel = namen[0].split("/")[0] + "/" + UPDATE_UNTERORDNER + "/"
    dateien = [n for n in namen if n.startswith(wurzel) and not n.endswith("/")]
    rel = [n[len(wurzel):] for n in dateien]
    if "SparteNet_Manager.py" not in rel or "spartenet/basis.py" not in rel or "spartenet/webserver.py" not in rel:
        raise Fehler("Im Archiv fehlt der Manager (SparteNet_Manager.py oder spartenet/).")
    if sum(z.getinfo(n).file_size for n in dateien) > UPDATE_MAX_BYTES * 2:
        raise Fehler("Archiv zu groß.")
    os.makedirs(ziel, exist_ok=True)
    basis = os.path.realpath(ziel)
    for n, r in zip(dateien, rel):
        if r.startswith(("/", "\\")) or ".." in r.replace("\\", "/").split("/"):
            raise Fehler(f"Unzulässiger Pfad im Archiv: {r}")
        pfad = os.path.realpath(os.path.join(ziel, r))
        if not pfad.startswith(basis + os.sep):
            raise Fehler(f"Unzulässiger Pfad im Archiv: {r}")
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with z.open(n) as q, open(pfad, "wb") as f:
            shutil.copyfileobj(q, f)
    return len(dateien)


def _selbsttest(ordner, erwartet):
    """neue Version in einem eigenen Prozess laden (ohne Webserver) und Versionsnummer prüfen"""
    pruef = ("import sys; sys.path.insert(0, sys.argv[1]); sys.argv[0] = sys.argv[1] + '/SparteNet_Manager.py'; "
             "import spartenet.webserver as w; assert callable(w.main); print(w.VERSION)")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SPARTENET_KEIN_BROWSER="1")
    try:
        p = subprocess.run([sys.executable, "-c", pruef, ordner], capture_output=True, text=True, timeout=120, env=env, cwd=ordner)
    except subprocess.TimeoutExpired:
        raise Fehler("Selbsttest: die neue Version lädt nicht (Zeitüberschreitung).")
    if p.returncode != 0:
        letzte = (p.stderr or p.stdout or "").strip().splitlines()[-3:]
        raise Fehler("Selbsttest fehlgeschlagen: " + " | ".join(letzte))
    v = (p.stdout or "").strip().splitlines()[-1:] or [""]
    if v[0] != erwartet:
        raise Fehler(f"Selbsttest: neue Version meldet „{v[0]}“ statt „{erwartet}“.")


def _update_lauf(d_start, wer, ziel_sha=None):
    """läuft im Hintergrund; Fortschritt in _UPDATE (die Oberfläche fragt jede Sekunde nach)"""
    i = 0
    try:
        _schritt(0, "läuft")
        lage = update_pruefen(lade(), still=True)
        if ziel_sha and lage["sha"] != ziel_sha:
            raise Fehler("Auf GitHub gibt es inzwischen eine andere Version – bitte erneut prüfen.")
        if not lage["verfuegbar"]:
            raise Fehler(f"Keine neuere Version – installiert ist {VERSION}, auf GitHub {lage['neu']}.")
        _schritt(0, "fertig", f"{VERSION} → {lage['neu']} ({lage['kurz']})")
        i = 1; _schritt(1, "läuft")
        os.makedirs(UPDATE_DIR, exist_ok=True)
        sich = os.path.join(UPDATE_DIR, f"sicherung_vor_{lage['neu']}_{time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(sich, "w", encoding="utf-8") as f:
            json.dump(dict(lade()), f, ensure_ascii=False)
        try:
            os.chmod(sich, 0o600)
        except OSError:
            pass
        alte = sorted(x for x in os.listdir(UPDATE_DIR) if x.startswith("sicherung_vor_"))
        for x in alte[:-5]:
            try:
                os.remove(os.path.join(UPDATE_DIR, x))
            except OSError:
                pass
        _schritt(1, "fertig", os.path.basename(sich) + (" · Datenbank: zusätzlich mysqldump empfohlen" if DB else ""))
        i = 2; _schritt(2, "läuft")
        roh = _gh(f"/repos/{UPDATE_REPO}/zipball/{lage['sha']}", roh=True, max_bytes=UPDATE_MAX_BYTES)
        pruefsumme = hashlib.sha256(roh).hexdigest()
        _schritt(2, "fertig", f"{len(roh) // 1024} KB · SHA-256 {pruefsumme[:16]}…")
        i = 3; _schritt(3, "läuft")
        if not roh.startswith(b"PK"):
            raise Fehler("Download ist kein ZIP-Archiv.")
        _schritt(3, "fertig", f"Commit {lage['sha'][:12]} aus {UPDATE_REPO}")
        i = 4; _schritt(4, "läuft")
        ordner = os.path.join(UPDATE_DIR, f"{lage['neu']}-{lage['kurz']}")
        tmp = ordner + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        n = _entpacken(roh, tmp)
        with open(os.path.join(tmp, "spartenet", "basis.py"), encoding="utf-8") as f:
            if _version_aus_quelltext(f.read()) != lage["neu"]:
                raise Fehler("Versionsnummer im Archiv passt nicht.")
        shutil.rmtree(ordner, ignore_errors=True)
        os.replace(tmp, ordner)
        _schritt(4, "fertig", f"{n} Dateien nach updates/{os.path.basename(ordner)}")
        i = 5; _schritt(5, "läuft")
        _selbsttest(ordner, lage["neu"])
        _schritt(5, "fertig", f"Version {lage['neu']} lädt fehlerfrei")
        i = 6; _schritt(6, "läuft")
        WARTUNG.update(an=True, text=f"Update auf {lage['neu']} – der Manager startet gleich neu.")
        _schritt(6, "fertig", "Anfragen werden kurz angehalten")
        i = 7; _schritt(7, "läuft")
        a = update_aktiv_lesen()
        _schritt(7, "fertig", "Neustart …")
        with _UPDATE["lock"]:
            protokoll = [dict(x) for x in _UPDATE["schritte"]]
        _update_aktiv_schreiben({"ordner": os.path.basename(ordner), "version": lage["neu"], "sha": lage["sha"], "seit": time.strftime("%Y-%m-%d %H:%M:%S"),
                                 "vorher": {"ordner": a.get("ordner"), "version": VERSION}, "von": wer, "fehler": None, "protokoll": protokoll})
        journal(f"Update installiert: {VERSION} → {lage['neu']} (Commit {lage['kurz']}, SHA-256 {pruefsumme[:16]}) durch {wer}")
        with _UPDATE["lock"]:
            _UPDATE["fertig"] = True
        _neustart()
    except Exception as e:
        WARTUNG.update(an=False, text="")
        text = str(e) if isinstance(e, Fehler) else f"{type(e).__name__}: {e}"
        if not isinstance(e, Fehler):
            LOG.error("Update fehlgeschlagen:\n%s", traceback.format_exc())
        _schritt(i, "fehler", text)
        with _UPDATE["lock"]:
            _UPDATE["fehler"] = text
        journal(f"Update fehlgeschlagen ({UPDATE_SCHRITTE[i]}): {text}")
    finally:
        with _UPDATE["lock"]:
            _UPDATE["laeuft"] = False


def akt_update(d):
    a = update_aktiv_lesen()
    with _UPDATE["lock"]:
        zustand = {k: _UPDATE[k] for k in ("lage", "laeuft", "fehler", "fertig")}
        zustand["schritte"] = [dict(s) for s in _UPDATE["schritte"]]
    zustand["abgeschlossen"] = ""
    if not zustand["laeuft"] and not zustand["schritte"] and a.get("protokoll") and a.get("ordner") \
            and os.path.abspath(CODE_DIR) == os.path.abspath(os.path.join(UPDATE_DIR, a["ordner"])):
        zustand["schritte"] = [dict(x) for x in a["protokoll"]]
        zustand["schritte"][-1]["text"] = f"neu gestartet – läuft seit {a.get('seit')}"
        zustand["abgeschlossen"] = f"✔ Update auf {a.get('version')} am {a.get('seit')} erfolgreich abgeschlossen (durch {a.get('von')})."
    return {**zustand, "version": VERSION, "code": CODE_DIR, "aktiv": a, "versionen": update_versionen(), "einstellungen": update_einstellungen(d),
            "repo": UPDATE_REPO, "token": bool(_token()), "wartung": WARTUNG["an"], "log": []}


def akt_update_pruefen(d):
    lage = update_pruefen(d)
    r = akt_update(d)
    r["log"] = [f"✔ Version {lage['neu']} ist verfügbar (installiert: {VERSION})." if lage["verfuegbar"] else f"✔ Aktuell – installiert {VERSION}, auf GitHub {lage['neu']}."]
    return r


def akt_update_installieren(d, b, wer):
    with _UPDATE["lock"]:
        if _UPDATE["laeuft"]:
            raise Fehler("Es läuft bereits ein Update.")
        _UPDATE.update(laeuft=True, fehler="", fertig=False, schritte=[{"name": n, "status": "offen", "text": ""} for n in UPDATE_SCHRITTE])
    threading.Thread(target=_update_lauf, args=(d, wer, (b or {}).get("sha")), daemon=True).start()
    r = akt_update(d)
    r["log"] = ["Update gestartet …"]
    return r


def akt_update_zurueck(d, wer):
    """zur vorherigen Version (bzw. zur mitgelieferten) zurück und neu starten"""
    a = update_aktiv_lesen()
    if not a.get("ordner"):
        raise Fehler("Es läuft bereits die mitgelieferte Version – nichts zurückzusetzen.")
    v = a.get("vorher") or {}
    if v.get("ordner") and os.path.isdir(os.path.join(UPDATE_DIR, v["ordner"])):
        _update_aktiv_schreiben({"ordner": v["ordner"], "version": v.get("version"), "seit": time.strftime("%Y-%m-%d %H:%M:%S"), "vorher": None, "von": wer})
        ziel = v.get("version")
    else:
        _update_aktiv_schreiben({"ordner": None, "version": None, "seit": time.strftime("%Y-%m-%d %H:%M:%S"), "vorher": None, "von": wer, "zurueck": True})
        ziel = "mitgelieferte Version"
    journal(f"Update zurückgenommen: {VERSION} → {ziel} durch {wer}")
    WARTUNG.update(an=True, text="Zurück zur vorherigen Version – der Manager startet gleich neu.")
    _neustart()
    return {"log": [f"✔ Zurück zu {ziel} – der Manager startet neu."], "neustart": True}


def akt_update_einstellungen(d, b):
    e = update_einstellungen(d)
    if "kanal" in b:
        k = str(b["kanal"]).strip()
        if k not in ("main", "release") and not re.fullmatch(r"branch:[A-Za-z0-9._/-]{1,100}", k):
            raise Fehler("Kanal: main, release oder branch:<Name>.")
        e["kanal"] = k
    if "automatisch" in b:
        e["automatisch"] = bool(b["automatisch"])
    if "stunden" in b:
        try:
            e["stunden"] = max(0, min(168, int(b["stunden"])))
        except (TypeError, ValueError):
            raise Fehler("Prüfabstand: ganze Zahl (Stunden, 0 = aus).")
    d["update"] = e
    speichere(d)
    with _UPDATE["lock"]:
        _UPDATE["lage"] = None
    r = akt_update(d)
    r["log"] = ["✔ Update-Einstellungen gespeichert."]
    return r


def update_hintergrund():
    """prüft regelmäßig auf neue Versionen; installiert nur, wenn „automatisch“ an ist – und dann nachts (2–5 Uhr)"""
    def schleife():
        time.sleep(60)
        while True:
            try:
                d = lade()
                e = update_einstellungen(d)
                if e["stunden"] and time.time() - _UPDATE["geprueft"] >= e["stunden"] * 3600:
                    lage = update_pruefen(d, still=True)
                    if lage["verfuegbar"]:
                        LOG.info("Update verfügbar: %s → %s", VERSION, lage["neu"])
                if e["automatisch"] and _UPDATE["lage"] and _UPDATE["lage"]["verfuegbar"] and 2 <= time.localtime().tm_hour < 5 and not _UPDATE["laeuft"]:
                    akt_update_installieren(d, {"sha": _UPDATE["lage"]["sha"]}, "automatisch")
            except Exception as ex:
                LOG.info("Update-Prüfung im Hintergrund: %s", ex)
            time.sleep(600)
    threading.Thread(target=schleife, daemon=True, name="update").start()


def update_kurz():
    """für die Kopfzeile der Administratoren"""
    lage = _UPDATE["lage"]
    return {"neu": lage["neu"], "verfuegbar": lage["verfuegbar"]} if lage else None


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

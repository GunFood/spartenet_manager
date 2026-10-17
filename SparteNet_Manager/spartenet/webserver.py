"""SparteNet Manager – Webserver: Anfragen, Rechteprüfung, Start"""
from .oberflaeche import *  # noqa: F401,F403 – alle Namen der vorherigen Module


# =============================================================== Webserver
PROXY_VERTRAUEN = os.environ.get("SPARTENET_PROXY", "0").strip().lower() in ("1", "ja", "true", "yes")
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
       "connect-src 'self'; frame-src 'self' blob: data:; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'self'")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _lade(self):
        """Einstellungen laden; ist die Datenbank weg, verständliche Antwort statt Verbindungsabbruch"""
        try:
            return lade()
        except Fehler as e:
            if self.path.split("?")[0] == "/":
                self._send(503, ("<!doctype html><meta charset='utf-8'><title>SparteNet Manager</title><body style='font-family:sans-serif;padding:24px'>"
                                 "<h2>Datenspeicher nicht erreichbar</h2><p>" + str(e).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</p>"
                                 "<p>Bitte die Datenbank prüfen und die Seite neu laden.</p>").encode("utf-8"), "text/html")
            else:
                self._send(503, {"fehler": str(e)})
            return None

    def _quelle(self):
        """Absenderadresse; hinter einem vertrauenswürdigen Reverse-Proxy (SPARTENET_PROXY=1) die vom Proxy gemeldete (S3)"""
        ip = self.client_address[0]
        if PROXY_VERTRAUEN:
            xff = [x.strip() for x in (self.headers.get("X-Forwarded-For") or "").split(",") if x.strip()]
            if xff:
                return xff[-1][:64]
            if self.headers.get("X-Real-IP"):
                return self.headers.get("X-Real-IP").strip()[:64]
        return ip

    def _send(self, code, daten, typ="application/json", extra=None):
        roh = daten if isinstance(daten, bytes) else json.dumps(daten, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", typ + ("; charset=utf-8" if typ.startswith(("text/", "application/json", "application/javascript", "application/manifest")) else ""))
        if len(roh) > 1400 and "gzip" in (self.headers.get("Accept-Encoding") or "") and typ.startswith(("text/", "application/json", "application/javascript")):
            roh = gzip.compress(roh, 6)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        if typ.startswith("text/html"):
            self.send_header("Content-Security-Policy", CSP)
        self.send_header("Content-Length", str(len(roh)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff"); self.send_header("Referrer-Policy", "no-referrer"); self.send_header("X-Frame-Options", "SAMEORIGIN")
        for k, v in (extra or {}).items():
            for wert in v if isinstance(v, (list, tuple)) else (v,):
                self.send_header(k, wert)
        self.end_headers(); self.wfile.write(roh)

    def _fern(self):
        """True, wenn die Anfrage nicht direkt von diesem PC kommt (Heimnetz, Tailscale, Weiterleitung, fremder Hostname)."""
        weiter = any(self.headers.get(k) for k in ("X-Forwarded-For", "X-Forwarded-Host", "Forwarded", "X-Real-IP", "Tailscale-User-Login"))
        host = (self.headers.get("Host") or "").lower()
        return weiter or self.client_address[0] not in ("127.0.0.1", "::1", "::ffff:127.0.0.1") or host not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _sitzung(self):
        c = SimpleCookie()
        try:
            c.load(self.headers.get("Cookie") or "")
        except CookieError:
            return ""
        return c["sn_sitzung"].value if "sn_sitzung" in c else ""

    def _auth_sitzung(self):
        c = SimpleCookie()
        try:
            c.load(self.headers.get("Cookie") or "")
        except CookieError:
            return ""
        return c["sn_auth"].value if "sn_auth" in c else ""

    def _wer(self, d):
        """(Kontoname, Recht) der Anfrage oder None, wenn nicht angemeldet; gesperrte oder gelöschte Konten fliegen sofort raus"""
        self._app_zugang = False
        info = auth_sitzung_info(self._auth_sitzung())
        if info:
            rechte = konto_rechte(d, info.get("benutzer", ADMIN_NAME))
            if rechte and rechte["art"] != "gesperrt":
                return info.get("benutzer", ADMIN_NAME), rechte
            auth_sitzung_entfernen(self._auth_sitzung())
            return None
        if self._fern() and sitzung_ok(d, self._sitzung()):
            return HANDY_NAME, konto_rechte(d, HANDY_NAME)
        app = app_token_pruefen(d, self.headers.get("Authorization"))
        if app:
            self._app_zugang = True
            return app
        return None

    def _token_ok(self):
        """Schutz gegen fremde Seiten (X-Token aus der Oberfläche) – Apps mit eigenem Schlüssel brauchen ihn nicht"""
        return self.headers.get("X-Token") == TOKEN or getattr(self, "_app_zugang", False)

    def _portal(self, methode, u):
        if methode == "GET" and u.path in ("/portal", "/portal/"):
            d = self._lade()
            if d is None:
                return
            if not portal_einstellungen(d)["aktiv"]:
                return self._send(404, b"<!doctype html><meta charset='utf-8'><title>Nicht gefunden</title><p style='font-family:sans-serif;padding:24px'>Diese Seite ist nicht eingeschaltet.</p>", "text/html")
            return self._send(200, PORTAL_HTML.encode("utf-8"), "text/html")
        b = None
        if methode == "POST":
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                n = -1
            if n < 0 or n > 12000:
                return self._send(413, {"fehler": "Anfrage zu groß."})
            try:
                b = json.loads(self.rfile.read(n) or b"{}")
            except (ValueError, UnicodeDecodeError):
                return self._send(400, {"fehler": "Ungültige Anfrage."})
        code, antwort = portal_anfrage(u.path.rstrip("/"), b, self._quelle())
        return self._send(code, antwort)

    def _erlaubt(self, d):
        return self._wer(d) is not None

    def _statisch(self, pfad):
        if pfad in PWA_ICONS:
            return self._send(200, PWA_ICONS[pfad][0], "image/png")
        if pfad == "/manifest.webmanifest":
            return self._send(200, json.dumps(MANIFEST, ensure_ascii=False).encode("utf-8"), "application/manifest+json")
        if pfad == "/sw.js":
            return self._send(200, SW_JS.replace("__VERSION__", VERSION).encode("utf-8"), "application/javascript")
        if pfad == "/offline.html":
            return self._send(200, OFFLINE_HTML.encode("utf-8"), "text/html")
        return None

    def _wartung(self):
        """während des Umschaltens beim Update: kurze Hinweisseite statt Anfragen zu bearbeiten"""
        if not WARTUNG["an"]:
            return False
        if self.path.split("?")[0] == "/":
            self._send(503, ("<!doctype html><meta charset='utf-8'><meta http-equiv='refresh' content='5'><title>SparteNet Manager – Update</title>"
                             "<body style='font-family:sans-serif;padding:24px'><h2>Wartungsmodus</h2><p>" + WARTUNG["text"] +
                             "</p><p>Die Seite lädt in wenigen Sekunden neu.</p>").encode("utf-8"), "text/html", extra={"Retry-After": "5"})
        else:
            self._send(503, {"fehler": WARTUNG["text"] or "Wartungsmodus", "wartung": True}, extra={"Retry-After": "5"})
        return True

    def _api_v1(self, methode, u):
        """Schnittstelle für andere Programme: Anmeldung mit API-Schlüssel statt Sitzung (kein Cookie, kein X-Token)"""
        roh = b""
        if methode == "POST":
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return self._send(400, {"ok": False, "fehler": "Ungültige Anfrage."})
            if n < 0 or n > API_MAX_BYTES:
                return self._send(413, {"ok": False, "fehler": "Anfrage zu groß."})
            roh = self.rfile.read(n)
        if u.path.rstrip("/") == "/api/v1/app/anmelden" and methode == "POST":
            try:
                b = json.loads(roh or b"{}")
                d = lade()
                with SCHREIB_SPERRE:
                    antwort = app_anmelden(d, b if isinstance(b, dict) else {}, self._quelle())
                return self._send(200 if antwort.get("ok") else 401, antwort)
            except (ValueError, UnicodeDecodeError):
                return self._send(400, {"ok": False, "fehler": "Ungültiges JSON."})
            except Fehler as e:
                return self._send(401, {"ok": False, "fehler": str(e)})
        if u.path.rstrip("/") in ("/api/v1/app/funktionen", "/api/v1/app/info") and methode == "GET":
            d = lade()
            wer = app_token_pruefen(d, self.headers.get("Authorization"))
            if not wer:
                return self._send(401, {"ok": False, "fehler": "App-Schlüssel fehlt oder ist ungültig (Authorization: Bearer sna_…)."}, extra={"WWW-Authenticate": "Bearer"})
            if u.path.rstrip("/").endswith("info"):
                return self._send(200, {"ok": True, "version": VERSION, "ich": ich_daten(*wer), "uebersicht": akt_app_uebersicht(d, *wer)})
            return self._send(200, {"version": VERSION, "auth": "Authorization: Bearer sna_… (POST /api/v1/app/anmelden)",
                                    "hinweis": "GET-Funktionen mit Parametern in der Adresse, POST mit JSON. Antwort JSON; Fehler mit HTTP 4xx und {\"fehler\": \"…\"}.",
                                    "funktionen": app_funktionen()})
        code, antwort = api_anfrage(methode, u.path.rstrip("/"), urllib.parse.parse_qs(u.query), roh,
                                    {"Authorization": self.headers.get("Authorization"), "X-API-Key": self.headers.get("X-API-Key")})
        return self._send(code, antwort, extra={"WWW-Authenticate": "Bearer"} if code == 401 else None)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in PWA_ICONS or u.path in ("/manifest.webmanifest", "/sw.js", "/offline.html"):
            return self._statisch(u.path)
        if u.path == "/status":  # öffentlich, wie status.php bei Nextcloud: Version und Wartungsmodus
            return self._send(200, {"produkt": "SparteNet Manager", "version": VERSION, "wartung": WARTUNG["an"]})
        if self._wartung():
            return
        if u.path.startswith("/api/v1/"):
            return self._api_v1("GET", u)
        if u.path == "/portal" or u.path.startswith("/portal/"):
            return self._portal("GET", u)
        d = self._lade()
        if d is None:
            return
        wer = self._wer(d)
        if u.path == "/":
            if not wer:
                return self._send(200, LOGIN_HTML.replace("__INHALT__", LOGIN_FORM).encode("utf-8"), "text/html")
            fern_nur = self._fern() and not auth_sitzung_ok(self._auth_sitzung())
            ich = json.dumps(ich_daten(*wer)).replace("<", "\\u003c")
            return self._send(200, HTML.replace("__TOKEN__", TOKEN).replace("__VERSION__", VERSION).replace("__FERN__", "1" if fern_nur else "0")
                              .replace("__SITZUNG_TAGE__", str(SITZUNG_TAGE)).replace("__ICH__", ich).encode("utf-8"), "text/html")
        if not wer:
            return self._send(401, {"fehler": "anmelden"})
        if not self._token_ok():
            return self._send(403, {"fehler": "nicht erlaubt"})
        self._antwort(u.path, urllib.parse.parse_qs(u.query), None, b"", wer, d)

    def _anmelden(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(400, {"fehler": "Ungültige Anfrage."})
        if n < 0 or n > 4096:
            return self._send(413, {"fehler": "Anfrage zu groß."})
        try:
            b = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, UnicodeDecodeError):
            return self._send(400, {"fehler": "Ungültige Anfrage."})
        if not isinstance(b, dict):
            return self._send(400, {"fehler": "Ungültige Anfrage."})
        d = self._lade()
        if d is None:
            return
        geheim = b.get("passwort", b.get("pin"))
        name = str(b.get("benutzer") or "").strip().lower()
        try:
            konto = benutzer_anmelden(d, name, geheim, self._quelle())
            if zweifaktor_aktiv(d, konto):
                if not str(b.get("code") or "").strip():
                    return self._send(400, {"fehler": "Bitte den 6-stelligen Code aus der Authenticator-App eingeben (oder einen Notfall-Code).", "zweiter_faktor": True})
                if not zweifaktor_pruefen(d, konto, b.get("code")):
                    _konto_sperre(konto, False)
                    LOG.warning("Falscher Zwei-Faktor-Code für „%s“", konto)
                    return self._send(400, {"fehler": "Der Code stimmt nicht.", "zweiter_faktor": True})
            t = auth_sitzung_neu(b.get("geraet"), konto)
            cookie = f"sn_auth={t}"
            LOG.info("Anmeldung erfolgreich: %s", konto)
            if konto != ADMIN_NAME:
                journal(f"Angemeldet: {konto} ({rechte_text(konto_rechte(d, konto))})")
        except Fehler as passwort_fehler:
            if name or not self._fern() or not fern_daten(d)["pin"].get("hash"):
                return self._send(400, {"fehler": str(passwort_fehler)})
            try:
                pin_pruefen(d, geheim)
            except Fehler as pin_fehler:
                return self._send(400, {"fehler": str(pin_fehler)})
            t = sitzung_neu(d, b.get("geraet"))
            cookie = f"sn_sitzung={t}"
            LOG.info("Anmeldung vom Handy/Tablet erfolgreich")
            journal("Handy/Tablet angemeldet: " + str(b.get("geraet") or "?")[:80])
        sicher = "; Secure" if (self.headers.get("X-Forwarded-Proto") == "https" or self.headers.get("Tailscale-User-Login")) else ""
        return self._send(200, {"ok": True}, extra={"Set-Cookie": f"{cookie}; Path=/; Max-Age={SITZUNG_TAGE * 86400}; HttpOnly; SameSite=Strict{sicher}"})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if self._wartung():
            return
        if u.path == "/login":
            return self._anmelden()
        if u.path.startswith("/api/v1/"):
            return self._api_v1("POST", u)
        if u.path.startswith("/portal/"):
            return self._portal("POST", u)
        d = self._lade()
        if d is None:
            return
        if u.path == "/abmelden":
            auth_sitzung_entfernen(self._auth_sitzung())
            t = self._sitzung()
            if t and fern_daten(d)["sitzungen"].pop(_sitzung_hash(t), None):
                speichere(d)
            return self._send(200, {"ok": True}, extra={"Set-Cookie": ["sn_auth=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict", "sn_sitzung=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"]})
        wer = self._wer(d)
        if not wer:
            return self._send(401, {"fehler": "anmelden"})
        if not self._token_ok():
            return self._send(403, {"fehler": "nicht erlaubt"})
        roh_pfad = u.path in ROH_PFADE
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(400, {"fehler": "Ungültige Anfrage."})
        if n < 0 or n > (MAX_UPLOAD_BYTES if roh_pfad else MAX_JSON_BYTES):
            return self._send(413, {"fehler": f"Anfrage zu groß (höchstens {(MAX_UPLOAD_BYTES if roh_pfad else MAX_JSON_BYTES) // 1_000_000} MB)."})
        roh = self.rfile.read(n)
        try:
            body = None if roh_pfad else json.loads(roh or b"{}")
        except (ValueError, UnicodeDecodeError):
            return self._send(400, {"fehler": "Ungültige Anfrage (kein JSON)."})
        self._antwort(u.path, urllib.parse.parse_qs(u.query), body, roh, wer, d)

    def _antwort(self, pfad, q, b, roh, wer, d_geladen=None):
        ich, rechte = wer
        if pfad in ("/api/ppsk-speichern", "/api/fern", "/api/benutzer-speichern", "/api/benutzer-ich", "/api/mitglied-speichern", "/api/mitglieder-import",
                    "/api/ticket-speichern", "/api/ticket-kommentar", "/api/email-test", "/api/email-vorschau", "/api/email-vorlage-speichern",
                    "/api/rechnung-einstellungen", "/api/zahlungen-uebernehmen", "/api/rundschreiben-senden", "/api/mitglied-dsgvo-loeschen", "/api/portal-einstellungen"):
            LOG.info("Aktion %s von %s (Inhalt nicht protokolliert)", pfad, ich)
        elif pfad not in ("/api/log", "/api/karten-vorschau"):
            LOG.info("Aktion %s von %s %s", pfad, ich, json.dumps(_maskiere(b), ensure_ascii=False)[:500] if isinstance(b, (dict, list)) else (urllib.parse.urlencode(q, doseq=True) if q else ""))
        noetig = recht_fuer(pfad, q, b)
        if not erlaubt(rechte, noetig):
            LOG.warning("Keine Berechtigung: %s für %s (%s)", ich, pfad, "/".join(noetig))
            return self._send(403, {"fehler": fehlt_text(ich, rechte, noetig), "recht": "fehlt"})
        if pfad not in ZWEIFAKTOR_FREI and zweifaktor_pflicht_offen(d_geladen or lade(), ich, rechte):
            return self._send(403, {"fehler": "Für Administratoren ist die Zwei-Faktor-Anmeldung Pflicht – bitte zuerst unter „Benutzer → Mein Konto“ einrichten.", "recht": "fehlt", "zweiter_faktor_fehlt": True})
        sp_erl = sparten_von(rechte)
        if sp_erl is not None:
            try:
                sparte_pruefen(pfad, q, b, sp_erl, d_geladen or lade())
            except Fehler as e:
                LOG.warning("Keine Berechtigung (Sparte): %s für %s", ich, pfad)
                return self._send(403, {"fehler": str(e), "recht": "fehlt"})
        ANFRAGE.benutzer = None if ich == ADMIN_NAME else ich
        schreibend = noetig[0] == "admin" or (len(noetig) > 1 and noetig[1] == "schreiben")
        if schreibend:
            SCHREIB_SPERRE.acquire()
        try:
            d = lade() if (schreibend or d_geladen is None) else d_geladen
            if self._fern() and not auth_sitzung_ok(self._auth_sitzung()) and (pfad in ("/api/fern", "/api/tailscale", "/api/beenden", "/api/log-loeschen", "/api/konsolen") or (pfad == "/api/einstellungen" and b is not None)):
                raise Fehler("Diese Einstellung lässt sich nur direkt am PC ändern.")
            if pfad == "/api/einstellungen":
                if b is None:
                    return self._send(200, {"konsole_id": d["konsole_id"], "konsole_name": d["konsole_name"], "cloud_key_gesetzt": bool(d["cloud_key"]),
                                            "log_aktiv": d["log_aktiv"], "logdatei": LOGDATEI, "speicher": speicher_text(), "ansicht": ansicht_pruefen(d.get("ansicht"))})
                if "log_aktiv" in b:
                    d["log_aktiv"] = bool(b["log_aktiv"]); speichere(d); log_einrichten(d["log_aktiv"])
                    return self._send(200, {"log": [f"✔ Protokoll {'eingeschaltet – Datei: ' + LOGDATEI if d['log_aktiv'] else 'ausgeschaltet'}"]})
                if b.get("cloud_key"):
                    d["cloud_key"] = b["cloud_key"].strip()
                for k in ("konsole_id", "konsole_name"):
                    if k in b:
                        d[k] = b[k]
                speichere(d); return self._send(200, {"log": ["✔ Verbindung gespeichert."]})
            if pfad == "/api/ansicht":
                d["ansicht"] = ansicht_pruefen(b); speichere(d)
                return self._send(200, {"ansicht": d["ansicht"]})
            if pfad == "/api/log":
                if not os.path.exists(LOGDATEI):
                    return self._send(200, {"log": ["(Protokolldatei ist leer oder noch nicht angelegt)"]})
                with open(LOGDATEI, encoding="utf-8", errors="replace") as f:
                    zeilen = f.read().splitlines()[-400:]
                return self._send(200, {"log": zeilen or ["(leer)"]})
            if pfad == "/api/log-loeschen":
                for i in range(0, 4):
                    pf = LOGDATEI + (f".{i}" if i else "")
                    if os.path.exists(pf):
                        open(pf, "w").close() if i == 0 else os.remove(pf)
                LOG.info("Protokoll geleert")
                return self._send(200, {"log": ["✔ Protokoll geleert."]})
            if pfad == "/api/konsolen":
                return self._send(200, {"konsolen": konsolen((b or {}).get("cloud_key") or d["cloud_key"])})
            if pfad == "/api/plan" and b is None:
                return self._send(200, antwort_filtern(pfad, {"roh": d["plan"], **plan_aktiv(d)}, sp_erl))
            if pfad == "/api/plan":
                plan_berechnen(b); d["plan"] = b; speichere(d)
                return self._send(200, {"log": ["✔ Plan gespeichert."]})
            if pfad == "/api/excel":
                d["plan"] = excel_import(roh); speichere(d)
                return self._send(200, {"log": [f"✔ Aus Excel übernommen: {len(d['plan']['sparten'])} Sparten."]})
            if pfad == "/api/design" and b is None:
                return self._send(200, {"design": d["design"], "standard": DESIGN_STANDARD, "logo_uri": logo_daten_uri(d["design"]),
                                        "schriften": list(SCHRIFTEN)})
            if pfad == "/api/design":
                d["design"] = design_pruefen({**b.get("design", {}), "logo": d["design"]["logo"]}); speichere(d)
                return self._send(200, {"log": ["✔ Kartendesign gespeichert – wird ab jetzt für alle Zugangskarten verwendet."]})
            if pfad == "/api/logo":
                d["design"]["logo"] = logo_speichern(roh); speichere(d)
                return self._send(200, {"log": [f"✔ Logo übernommen ({len(roh) // 1024} KB)."], "logo_uri": logo_daten_uri(d["design"])})
            if pfad == "/api/logo-loeschen":
                logo_entfernen(); d["design"]["logo"] = ""; speichere(d)
                return self._send(200, {"log": ["✔ Logo entfernt."]})
            routen = {
                "/api/test": lambda: akt_test(d),
                "/api/lesen": lambda: akt_lesen(d, q.get("was", [""])[0]),
                "/api/abgleich": lambda: akt_abgleich(d, q.get("sparte", [""])[0]),
                "/api/netze": lambda: akt_netze(d, b["sparte"], bool(b.get("ausfuehren")), bool(b.get("nur_eins"))),
                "/api/ppsk": lambda: akt_ppsk(d, b["sparte"], b.get("art", "anzeigen")),
                "/api/schreibtest": lambda: akt_schreibtest(d),
                "/api/vergleich": lambda: akt_vergleich(d, q.get("sparte", [""])[0]),
                "/api/uebertragen": lambda: akt_uebertragen(d, b["sparte"], b.get("parzellen") or [], b.get("netze") or [], bool(b.get("ausfuehren"))),
                "/api/rueckgaengig": lambda: akt_rueckgaengig(d, b["sparte"]),
                "/api/journal": lambda: akt_journal(),
                "/api/ppsk-speichern": lambda: akt_ppsk_speichern(d, b["sparte"], b.get("aenderungen")),
                "/api/wlans": lambda: akt_wlans(d, q.get("sparte", [""])[0]),
                "/api/wlan-zuordnung": lambda: akt_wlan_zuordnung(d, b or {}),
                "/api/passwort": lambda: {"passwoerter": passwoerter_erzeugen(min(200, int(q.get("n", ["1"])[0])), d)},
                "/api/pw-regel": lambda: ({"regel": pw_regel(d)} if b is None else (d.__setitem__("pw_regel", {"praefix": str(b.get("praefix", "SN")), "ziffern": b.get("ziffern", 10)}) or speichere(d) or {"regel": pw_regel(d), "log": [f"✔ Regel gespeichert: {pw_regel(d)['praefix']} + {pw_regel(d)['ziffern']} Ziffern – gilt für alle neu erzeugten Passwörter."]})),
                "/api/system": lambda: akt_system(d),
                "/api/daten-liste": lambda: {"quellen": daten_liste()},
                "/api/daten": lambda: akt_daten(d, q.get("q", [""])[0], q.get("geheim", ["0"])[0] == "1"),
                "/api/daten-pruefen": lambda: akt_daten_pruefen(d),
                "/api/diagnose": lambda: akt_diagnose(d, bool(b.get("anonym", True))),
                "/api/ppsk-hochladen": lambda: akt_ppsk_hochladen(d, b["sparte"], bool(b.get("ausfuehren"))),
                "/api/karten": lambda: akt_karten(d, b["sparte"], b.get("auswahl", "alle")),
                "/api/karten-vorschau": lambda: akt_karten_vorschau(d, {**b.get("design", {}), "logo": d["design"]["logo"]}, bool(b.get("drucken"))),
                "/api/tarife": lambda: ({"tarife": tarife_pruefen(d["tarife"]), "modus": d.get("tarif_modus", "tarif"), "standard": TARIFE_STANDARD} if b is None else akt_tarife_speichern(d, b)),
                "/api/tarif-zuordnung": lambda: akt_tarif_zuordnen(d, b.get("aenderungen")),
                "/api/tarif-vergleich": lambda: akt_tarif_vergleich(d),
                "/api/tarif-erkennen": lambda: akt_tarif_erkennen(d),
                "/api/tarif-uebertragen": lambda: akt_tarif_uebertragen(d, b.get("netze") or [], b.get("regeln") or [], bool(b.get("ausfuehren"))),
                "/api/tarif-rueckgaengig": lambda: akt_tarif_rueckgaengig(d),
                "/api/kalkulation": lambda: akt_kalkulation(d, q.get("prognose", ["0"])[0] == "1"),
                "/api/kalk-annahmen": lambda: akt_kalk_annahmen(d, b),
                "/api/kalk-sparte": lambda: akt_kalk_sparte(d, b),
                "/api/kalk-import": lambda: akt_kalk_import(d, roh),
                "/api/gwplan": lambda: gwplan_berechnen(d),
                "/api/gwplan-sparte": lambda: akt_gwplan_sparte(d, b),
                "/api/gwplan-annahmen": lambda: akt_gwplan_annahmen(d, b),
                "/api/gwplan-zuruecksetzen": lambda: akt_gwplan_zuruecksetzen(d, (b or {}).get("was")),
                "/api/gwplan-import": lambda: akt_gwplan_import(d, roh),
                "/api/gwplan-vlan": lambda: akt_gwplan_vlan(d, q.get("standort", [""])[0], q.get("gw", [""])[0]),
                "/api/gwplan-vlan-uebernehmen": lambda: akt_gwplan_vlan_uebernehmen(d, b),
                "/api/zuteilung": lambda: akt_zuteilung(d),
                "/api/zuteilung-einstellen": lambda: akt_zuteilung_einstellen(d, b or {}, ich),
                "/api/zuteilung-parzellen": lambda: akt_zuteilung_parzellen(d, q.get("standort", [""])[0]),
                "/api/zuteilung-setzen": lambda: akt_zuteilung_setzen(d, b or {}, ich),
                "/api/zuteilung-verdichten": lambda: akt_zuteilung_verdichten(d, b or {}, ich),
                "/api/zuteilung-gateway": lambda: akt_zuteilung_gateway(d, b or {}),
                "/api/umzug": lambda: akt_umzug(d, b or {}),
                "/api/umzug-rueckgaengig": lambda: akt_umzug_rueckgaengig(d),
                "/api/buchungen": lambda: akt_buchungen(d, q.get("sparte", [""])[0], sp_erl) if b is None else akt_buchungen_speichern(d, b.get("sparte", ""), b.get("aenderungen")),
                "/api/fern": lambda: akt_fern(d) if b is None else akt_fern_speichern(d, b),
                "/api/tailscale": lambda: akt_tailscale(bool(b.get("an"))),
                "/api/start": lambda: akt_start(d),
                "/api/parzelle": lambda: akt_parzelle(d, q.get("sparte", [""])[0], q.get("p", [""])[0]),
                "/api/voucher": lambda: akt_voucher(d, b.get("anzahl", 10), b.get("minuten", 1440), b.get("name", ""), bool(b.get("ausfuehren")), b.get("vorlage")),
                "/api/voucher-vorlagen": lambda: akt_voucher_vorlagen(d, b),
                "/api/voucher-liste": lambda: akt_voucher_liste(d),
                "/api/voucher-druck": lambda: akt_voucher_druck(d, b),
                "/api/voucher-loeschen": lambda: akt_voucher_loeschen(d, b.get("ids"), bool(b.get("ausfuehren"))),
                "/api/benutzer": lambda: akt_benutzer(d, ich),
                "/api/benutzer-speichern": lambda: akt_benutzer_speichern(d, b or {}, ich),
                "/api/benutzer-loeschen": lambda: akt_benutzer_loeschen(d, b or {}, ich),
                "/api/benutzer-ich": lambda: akt_benutzer_ich(d, ich, b),
                "/api/unterlagen": lambda: akt_unterlagen(d, sp_erl),
                "/api/unterlage-hochladen": lambda: akt_unterlage_hochladen(d, q, roh, ich, sp_erl),
                "/api/unterlage-datei": lambda: akt_unterlage_datei(d, q, sp_erl),
                "/api/unterlage-aendern": lambda: akt_unterlage_aendern(d, b or {}, sp_erl),
                "/api/unterlage-loeschen": lambda: akt_unterlage_loeschen(d, b or {}, sp_erl),
                "/api/unterlage-ordner": lambda: akt_unterlage_ordner(d, b or {}, sp_erl),
                "/api/sicherung": lambda: akt_sicherung(d),
                "/api/sicherung-erstellen": lambda: akt_sicherung_erstellen(d, b, ich),
                "/api/sicherung-datei": lambda: akt_sicherung_datei(d, q),
                "/api/sicherung-jetzt": lambda: akt_sicherung_jetzt(d, ich),
                "/api/sicherung-einstellungen": lambda: akt_sicherung_einstellungen(d, b or {}),
                "/api/sicherung-einspielen": lambda: akt_sicherung_einspielen(d, roh, urllib.parse.unquote(self.headers.get("X-Sicherung-Passwort") or ""), ich),
                "/api/2fa-start": lambda: akt_2fa_start(d, ich),
                "/api/2fa-bestaetigen": lambda: akt_2fa_bestaetigen(d, ich, (b or {}).get("code")),
                "/api/2fa-aus": lambda: akt_2fa_aus(d, ich, (b or {}).get("code")),
                "/api/2fa-zuruecksetzen": lambda: akt_2fa_zuruecksetzen(d, (b or {}).get("name"), ich),
                "/api/sicherheit-einstellungen": lambda: akt_sicherheit_einstellungen(d, b or {}, ich),
                "/api/automation": lambda: (lambda a: a if rechte["art"] == "admin" or STUFE_RANG.get(rechte["bereiche"].get("mitglieder", "kein"), 0) >= 1
                                            else {**a, "verlauf": personen_verdecken(a["verlauf"])})(akt_automation(d, mit_smtp=rechte["art"] == "admin")),
                "/api/automation-speichern": lambda: akt_automation_speichern(d, b or {}, ich),
                "/api/automation-loeschen": lambda: akt_automation_loeschen(d, b or {}, ich),
                "/api/automation-probe": lambda: akt_automation_probe(d, b or {}),
                "/api/smtp-speichern": lambda: akt_smtp_speichern(d, b or {}, ich),
                "/api/email-layout": lambda: akt_email_layout(d, b),
                "/api/email-vorschau": lambda: akt_email_vorschau(d, b or {}),
                "/api/email-vorlage-speichern": lambda: akt_email_vorlage_speichern(d, b or {}, ich),
                "/api/email-vorlage-loeschen": lambda: akt_email_vorlage_loeschen(d, b or {}, ich),
                "/api/email-test": lambda: akt_email_test(d, b or {}),
                "/api/admin-email": lambda: (d.__setitem__("admin_email", str((b or {}).get("email") or "").strip().lower()[:200]) or speichere(d) or {"log": ["✔ E-Mail des Kontos „admin“ gespeichert."]}),
                "/api/mitglieder": lambda: akt_mitglieder(d, sp_erl),
                "/api/mitglied-speichern": lambda: akt_mitglied_speichern(d, b or {}, ich, sp_erl),
                "/api/mitglied-loeschen": lambda: akt_mitglied_loeschen(d, b or {}, ich, sp_erl),
                "/api/mitglieder-import": lambda: akt_mitglieder_import(d, q, roh, ich, sp_erl),
                "/api/mitglieder-export": lambda: akt_mitglieder_export(d, sp_erl),
                "/api/tickets": lambda: akt_tickets(d, q, ich, sp_erl),
                "/api/rechnungen": lambda: akt_rechnungen(d, q, sp_erl),
                "/api/rechnung-einstellungen": lambda: akt_rechnung_einstellungen(d, b or {}, ich) if b is not None else {"einstellungen": rechnung_einstellungen(d)},
                "/api/rechnungslauf": lambda: akt_rechnungslauf(d, b or {}, ich),
                "/api/rechnung-pdf": lambda: akt_rechnung_pdf(d, q, sp_erl),
                "/api/rechnung-senden": lambda: akt_rechnung_senden(d, b or {}, ich, sp_erl),
                "/api/rechnung-status": lambda: akt_rechnung_status(d, b or {}, ich, sp_erl),
                "/api/zahlungen-import": lambda: akt_zahlungen_import(d, roh, ich, sp_erl),
                "/api/zahlungen-uebernehmen": lambda: akt_zahlungen_uebernehmen(d, b or {}, ich, sp_erl),
                "/api/vertraege": lambda: akt_vertraege(d, sp_erl),
                "/api/vertrag-speichern": lambda: akt_vertrag_speichern(d, b or {}, ich, sp_erl),
                "/api/vertrag-kuendigen": lambda: akt_vertrag_kuendigen(d, b or {}, ich, sp_erl),
                "/api/vertrag-einstellungen": lambda: akt_vertrag_einstellungen(d, b or {}, ich),
                "/api/rundschreiben": lambda: akt_rundschreiben(d),
                "/api/rundschreiben-empfaenger": lambda: akt_rundschreiben_empfaenger(d, b or {}, sp_erl),
                "/api/rundschreiben-senden": lambda: akt_rundschreiben_senden(d, b or {}, ich, sp_erl),
                "/api/mitglied-auskunft": lambda: akt_mitglied_auskunft(d, q, ich, sp_erl),
                "/api/mitglied-dsgvo-loeschen": lambda: akt_mitglied_dsgvo_loeschen(d, b or {}, ich, sp_erl),
                "/api/ueberwachung": lambda: akt_ueberwachung(d),
                "/api/ueberwachung-speichern": lambda: akt_ueberwachung(d, b or {}, ich),
                "/api/wochenbericht": lambda: akt_wochenbericht(d, b, ich),
                "/api/portal-einstellungen": lambda: akt_portal_einstellungen(d, b, ich),
                "/api/app-uebersicht": lambda: akt_app_uebersicht(d, ich, rechte),
                "/api/app-geraete": lambda: akt_app_geraete(d, ich, rechte["art"] == "admin" and q.get("alle", ["0"])[0] == "1"),
                "/api/app-geraet-entfernen": lambda: akt_app_geraet_entfernen(d, b or {}, ich, rechte["art"] == "admin"),
                "/api/ticket": lambda: akt_ticket(d, q, ich, sp_erl),
                "/api/ticket-speichern": lambda: akt_ticket_speichern(d, b or {}, ich, sp_erl),
                "/api/ticket-kommentar": lambda: akt_ticket_kommentar(d, b or {}, ich, sp_erl),
                "/api/ticket-loeschen": lambda: akt_ticket_loeschen(d, b or {}, ich),
                "/api/ticket-einstellungen": lambda: akt_ticket_einstellungen(d, b or {}, ich),
                "/api/smtp-test": lambda: akt_smtp_test(d, b or {}),
                "/api/api-schluessel": lambda: akt_api(d),
                "/api/api-schluessel-neu": lambda: akt_api_schluessel_neu(d, b or {}, ich),
                "/api/api-schluessel-aendern": lambda: akt_api_schluessel_aendern(d, b or {}, ich),
                "/api/update": lambda: akt_update(d),
                "/api/update-pruefen": lambda: akt_update_pruefen(d),
                "/api/update-installieren": lambda: akt_update_installieren(d, b, ich),
                "/api/update-zurueck": lambda: akt_update_zurueck(d, ich),
                "/api/update-einstellungen": lambda: akt_update_einstellungen(d, b or {}),
            }
            if pfad in routen:
                antwort = routen[pfad]()
                if isinstance(antwort, dict) and "_datei" in antwort:   # Dateiinhalt (Unterlagen, Sicherung): immer als Download, nie als Webseite
                    name = antwort.get("name") or "Datei"
                    ascii_name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:100] or "Datei"
                    return self._send(200, antwort["_datei"], antwort.get("typ") or "application/octet-stream", extra={
                        "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{urllib.parse.quote(name)}",
                        "Content-Security-Policy": "default-src 'none'; sandbox"})
                return self._send(200, antwort_filtern(pfad, antwort, sp_erl))
            if pfad == "/api/beenden":
                self._send(200, {"log": ["Beendet."]})
                threading.Thread(target=lambda: (time.sleep(0.5), os._exit(0)), daemon=True).start(); return
            self._send(404, {"fehler": "unbekannt"})
        except Fehler as e:
            LOG.warning("Meldung an Benutzer: %s", e)
            self._send(400, {"fehler": str(e)})
        except Exception as e:
            ref = secrets.token_hex(3)
            LOG.error("Unerwarteter Fehler %s bei %s:\n%s", ref, pfad, traceback.format_exc())
            self._send(500, {"fehler": f"Unerwarteter Fehler (Nr. {ref}, {type(e).__name__}) – Details im Protokoll unter dieser Nummer."})
        finally:
            ANFRAGE.benutzer = None
            if schreibend:
                SCHREIB_SPERRE.release()


ROH_PFADE = {"/api/zahlungen-import", "/api/mitglieder-import", "/api/excel", "/api/logo", "/api/kalk-import", "/api/gwplan-import", "/api/unterlage-hochladen", "/api/sicherung-einspielen"}


def main():
    if not AUTH_PASSWORD:
        raise SystemExit("Zugriffsschutz fehlt: SPARTENET_PASSWORD oder SPARTENET_PASSWORD_FILE setzen.")
    if len(AUTH_PASSWORD) < 12:
        raise SystemExit("Das Manager-Passwort muss mindestens 12 Zeichen lang sein.")
    datenbank_starten()
    d = lade()
    log_einrichten(d["log_aktiv"])
    a = update_aktiv_lesen()
    if a.get("ordner") and os.path.abspath(CODE_DIR) == os.path.abspath(os.path.join(UPDATE_DIR, a["ordner"])):
        print(f"Aktualisierte Version aus dem Datenordner: {a['ordner']}")
    elif a.get("fehler"):
        print(f"Hinweis: die aktualisierte Version {a.get('version')} startete nicht – es läuft die mitgelieferte {VERSION} ({a['fehler']}).")
    n = update_sitzungen_uebernehmen()
    if n:
        print(f"{n} Anmeldung(en) über den Neustart übernommen.")
    if os.environ.get("SPARTENET_SICHERUNG", "1") != "0":
        sicherung_hintergrund()
    if os.environ.get("SPARTENET_ZEITPLAN", "1") != "0":
        zeitplan_hintergrund()
    if os.environ.get("SPARTENET_UPDATE_PRUEFEN", "1") != "0":
        update_hintergrund()
    f = fern_daten(d)
    if HOST_OVERRIDE not in (None, "0.0.0.0", "127.0.0.1"):
        raise SystemExit("SPARTENET_HOST muss 127.0.0.1 oder 0.0.0.0 sein.")
    LAUFZEIT["host"] = HOST_OVERRIDE or ("0.0.0.0" if f["lan"] else "127.0.0.1")
    try:
        srv = ThreadingHTTPServer((LAUFZEIT["host"], PORT), Handler)
    except OSError:
        print(f"Port {PORT} belegt – läuft der Manager schon? http://127.0.0.1:{PORT}")
        webbrowser.open(f"http://127.0.0.1:{PORT}"); return
    url = f"http://127.0.0.1:{PORT}"
    print(f"Datenspeicher: {speicher_text()}")
    print(f"SparteNet Manager {VERSION} (Cloud) läuft: {url}\nFenster offen lassen. Beenden mit Strg+C oder im Browser „Beenden“.")
    if LAUFZEIT["host"] == "0.0.0.0":
        print("Handy/Tablet im Heimnetz: " + ", ".join(f"http://{ip}:{PORT}" for ip in lan_adressen()) + " (Manager-Passwort oder Handy-PIN)")
    if not os.environ.get("SPARTENET_KEIN_BROWSER"):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("Beendet.")

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

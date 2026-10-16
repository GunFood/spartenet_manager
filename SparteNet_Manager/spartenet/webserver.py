"""SparteNet Manager – Webserver: Anfragen, Rechteprüfung, Start"""
from .oberflaeche import *  # noqa: F401,F403 – alle Namen der vorherigen Module


# =============================================================== Webserver
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

    def _send(self, code, daten, typ="application/json", extra=None):
        roh = daten if isinstance(daten, bytes) else json.dumps(daten, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", typ + ("; charset=utf-8" if typ.startswith(("text/", "application/json", "application/javascript", "application/manifest")) else ""))
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
        info = auth_sitzung_info(self._auth_sitzung())
        if info:
            rechte = konto_rechte(d, info.get("benutzer", ADMIN_NAME))
            if rechte and rechte["art"] != "gesperrt":
                return info.get("benutzer", ADMIN_NAME), rechte
            auth_sitzung_entfernen(self._auth_sitzung())
            return None
        if self._fern() and sitzung_ok(d, self._sitzung()):
            return HANDY_NAME, konto_rechte(d, HANDY_NAME)
        return None

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

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in PWA_ICONS or u.path in ("/manifest.webmanifest", "/sw.js", "/offline.html"):
            return self._statisch(u.path)
        if u.path == "/status":  # öffentlich, wie status.php bei Nextcloud: Version und Wartungsmodus
            return self._send(200, {"produkt": "SparteNet Manager", "version": VERSION, "wartung": WARTUNG["an"]})
        if self._wartung():
            return
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
        if self.headers.get("X-Token") != TOKEN:
            return self._send(403, {"fehler": "nicht erlaubt"})
        self._antwort(u.path, urllib.parse.parse_qs(u.query), None, b"", wer)

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
            konto = benutzer_anmelden(d, name, geheim, self.client_address[0])
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
        if self.headers.get("X-Token") != TOKEN:
            return self._send(403, {"fehler": "nicht erlaubt"})
        roh = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        body = None if u.path in ("/api/excel", "/api/logo", "/api/kalk-import", "/api/gwplan-import") else json.loads(roh or b"{}")
        self._antwort(u.path, {}, body, roh, wer)

    def _antwort(self, pfad, q, b, roh, wer):
        ich, rechte = wer
        if pfad in ("/api/ppsk-speichern", "/api/fern", "/api/benutzer-speichern", "/api/benutzer-ich"):
            LOG.info("Aktion %s von %s (Inhalt nicht protokolliert)", pfad, ich)
        elif pfad not in ("/api/log", "/api/karten-vorschau"):
            LOG.info("Aktion %s von %s %s", pfad, ich, json.dumps(_maskiere(b), ensure_ascii=False)[:500] if isinstance(b, (dict, list)) else (urllib.parse.urlencode(q, doseq=True) if q else ""))
        noetig = recht_fuer(pfad, q, b)
        if not erlaubt(rechte, noetig):
            LOG.warning("Keine Berechtigung: %s für %s (%s)", ich, pfad, "/".join(noetig))
            return self._send(403, {"fehler": fehlt_text(ich, rechte, noetig), "recht": "fehlt"})
        ANFRAGE.benutzer = None if ich == ADMIN_NAME else ich
        try:
            d = lade()
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
                return self._send(200, {"roh": d["plan"], **plan_berechnen(d["plan"])})
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
                "/api/buchungen": lambda: akt_buchungen(d, q.get("sparte", [""])[0]) if b is None else akt_buchungen_speichern(d, b.get("sparte", ""), b.get("aenderungen")),
                "/api/fern": lambda: akt_fern(d) if b is None else akt_fern_speichern(d, b),
                "/api/tailscale": lambda: akt_tailscale(bool(b.get("an"))),
                "/api/start": lambda: akt_start(d),
                "/api/parzelle": lambda: akt_parzelle(d, q.get("sparte", [""])[0], q.get("p", [""])[0]),
                "/api/voucher": lambda: akt_voucher(d, b.get("anzahl", 10), b.get("minuten", 1440), b.get("name", "Gast"), bool(b.get("ausfuehren"))),
                "/api/benutzer": lambda: akt_benutzer(d, ich),
                "/api/benutzer-speichern": lambda: akt_benutzer_speichern(d, b or {}, ich),
                "/api/benutzer-loeschen": lambda: akt_benutzer_loeschen(d, b or {}, ich),
                "/api/benutzer-ich": lambda: akt_benutzer_ich(d, ich, b),
                "/api/update": lambda: akt_update(d),
                "/api/update-pruefen": lambda: akt_update_pruefen(d),
                "/api/update-installieren": lambda: akt_update_installieren(d, b, ich),
                "/api/update-zurueck": lambda: akt_update_zurueck(d, ich),
                "/api/update-einstellungen": lambda: akt_update_einstellungen(d, b or {}),
            }
            if pfad in routen:
                return self._send(200, routen[pfad]())
            if pfad == "/api/beenden":
                self._send(200, {"log": ["Beendet."]})
                threading.Thread(target=lambda: (time.sleep(0.5), os._exit(0)), daemon=True).start(); return
            self._send(404, {"fehler": "unbekannt"})
        except Fehler as e:
            LOG.warning("Meldung an Benutzer: %s", e)
            self._send(400, {"fehler": str(e)})
        except Exception as e:
            LOG.error("Unerwarteter Fehler bei %s:\n%s", pfad, traceback.format_exc())
            self._send(500, {"fehler": f"Unerwarteter Fehler: {type(e).__name__}: {e}" + (" – Details in der Protokolldatei." if lade()["log_aktiv"] else " – Protokoll einschalten (Verbindung) und erneut versuchen.")})
        finally:
            ANFRAGE.benutzer = None


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

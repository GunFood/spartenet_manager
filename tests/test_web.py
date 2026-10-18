"""Tests über HTTP gegen einen echten Testserver (Dateispeicher, ohne Gateway): Anmeldung, Rechte, Automationen + E-Mail,
API-Schnittstelle, Zwei-Faktor, Unterlagen, Datensicherung"""
import io, json, os, sys, time, unittest, urllib.parse, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hilfe import APP_TOKEN, PASSWORT, Sitzung, SmtpEmpfaenger, Testserver, api, totp   # noqa: E402

SRV = SMTP = None


def setUpModule():
    global SRV, SMTP
    SMTP = SmtpEmpfaenger()
    SRV = Testserver()


def tearDownModule():
    SRV.stop()
    SMTP.stop()


def admin():
    s = Sitzung(SRV.basis)
    code, _ = s.anmelden()
    assert code == 200
    return s


def app_token(a):
    """App-Zugangstoken einmal erzeugen (gilt dann für alle App-Aufrufe der Tests)"""
    if not APP_TOKEN["wert"]:
        code, x = a.req("/api/app-zugangstoken", {"neu": True})
        assert code == 200, x
        APP_TOKEN["wert"] = x["token"]
    return APP_TOKEN["wert"]


class Grundlagen(unittest.TestCase):
    def test_status_oeffentlich(self):
        code, a = api(SRV.basis, "GET", "/status")
        self.assertEqual(code, 200)
        self.assertEqual(a["produkt"], "SparteNet Manager")

    def test_ohne_anmeldung_und_ohne_token(self):
        s = Sitzung(SRV.basis)
        self.assertEqual(s.req("/api/plan")[0], 401)
        s = admin()
        s.token = "falsch"
        self.assertEqual(s.req("/api/plan")[0], 403)

    def test_falsches_passwort(self):
        self.assertEqual(Sitzung(SRV.basis).anmelden("admin", "falsch-falsch-falsch")[0], 400)

    def test_sicherheitskopfzeilen(self):
        code, kopf, _ = Sitzung(SRV.basis).roh("/")
        self.assertIn("Content-Security-Policy", kopf)
        self.assertEqual(kopf.get("X-Content-Type-Options"), "nosniff")

    def test_farbschema_auf_der_seite(self):
        _, _, html = admin().roh("/")
        self.assertIn(b'id="farbe_k"', html)
        self.assertIn(b"prefers-color-scheme:dark", html)


class Rechte(unittest.TestCase):
    def test_bereichskonto(self):
        a = admin()
        code, x = a.req("/api/benutzer-speichern", {"neu": True, "name": "leser", "passwort": "Leser-Passwort-123", "passwort2": "Leser-Passwort-123", "art": "bereiche",
                                                    "bereiche": {"automationen": "lesen", "start": "lesen"}})
        self.assertEqual(code, 200, x)
        l = Sitzung(SRV.basis)
        self.assertEqual(l.anmelden("leser", "Leser-Passwort-123")[0], 200)
        code, x = l.req("/api/automation")
        self.assertEqual(code, 200)
        self.assertIsNone(x["smtp"])                                                  # SMTP-Einstellungen nur für Admins
        self.assertEqual(l.req("/api/automation-speichern", {"regel": {}})[0], 403)
        self.assertEqual(l.req("/api/smtp-speichern", {"host": "x"})[0], 403)
        self.assertEqual(l.req("/api/api-schluessel")[0], 403)
        self.assertEqual(l.req("/api/zuteilung-einstellen", {"an": True})[0], 403)
        self.assertEqual(l.req("/api/umzug", {})[0], 403)
        self.assertEqual(l.req("/api/benutzer")[0], 403)


class AutomationenUndApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = admin()
        code, x = cls.a.req("/api/smtp-speichern", {"host": "127.0.0.1", "port": SMTP.port, "sicherheit": "keine", "anmeldung": "keine", "absender": "wlan@verein.example",
                                                    "passwort": "geheim-smtp-pw"})
        assert code == 200, x
        code, x = cls.a.req("/api/automation-speichern", {"regel": {"name": "Mail bei Buchung", "ausloeser": "buchung", "aktionen": [
            {"typ": "email", "an": "vorstand@verein.example", "betreff": "Neu {sparte} P{parzelle} {tarif}", "text": "Preis {preis}, von {quelle}"}]}})
        assert code == 200, x
        code, x = cls.a.req("/api/automation-speichern", {"regel": {"name": "Zahlung bucht", "ausloeser": "zahlung", "bedingung": {"betrag_min": "100"},
                                                                    "aktionen": [{"typ": "buchen", "tarif": "{tarif}"},
                                                                                 {"typ": "email", "an": "kasse@verein.example", "an_kunde": True, "betreff": "Zahlung {betrag} {referenz}", "text": "Danke {name}"}]}})
        assert code == 200, x
        code, x = cls.a.req("/api/api-schluessel-neu", {"name": "Buchhaltung", "rechte": ["ereignis", "buchen", "lesen"], "sparten": ["BW"]})
        assert code == 200, x
        cls.key = x["neu"]
        code, x = cls.a.req("/api/api-schluessel-neu", {"name": "Nur lesen", "rechte": ["lesen"]})
        cls.key_lesen = x["neu"]

    def test_smtp_login(self):
        a = admin()
        a.req("/api/smtp-speichern", {"anmeldung": "login", "benutzer": "postfach@verein.example", "passwort": "falsch"})
        code, x = a.req("/api/smtp-test", {"an": "test@example.org"})
        self.assertEqual(code, 400)
        self.assertIn("lehnt die Anmeldung ab", x["fehler"])
        a.req("/api/smtp-speichern", {"passwort": SMTP.passwort})
        code, x = a.req("/api/smtp-test", {"an": "test@example.org"})
        self.assertEqual(code, 200, x)
        self.assertEqual(SMTP.anmeldungen[-1], ("postfach@verein.example", SMTP.passwort))
        a.req("/api/smtp-speichern", {"anmeldung": "keine"})

    def test_smtp_passwort_nie_sichtbar(self):
        _, x = self.a.req("/api/automation")
        self.assertNotIn("geheim-smtp-pw", json.dumps(x))
        self.assertTrue(x["smtp"]["passwort_gesetzt"])

    def test_ungueltige_regel(self):
        self.assertEqual(self.a.req("/api/automation-speichern", {"regel": {"name": "x", "ausloeser": "buchung", "aktionen": []}})[0], 400)
        self.assertEqual(self.a.req("/api/automation-speichern", {"regel": {"name": "x", "ausloeser": "buchung", "aktionen": [{"typ": "webhook", "url": "file:///etc/passwd"}]}})[0], 400)

    def test_buchung_sendet_mail(self):
        n = len(SMTP.mails)
        code, x = self.a.req("/api/buchungen", {"sparte": "BW", "aenderungen": {"3": "Basic"}})
        self.assertEqual(code, 200, x)
        m = SMTP.warten(n + 1)[n]
        self.assertEqual(m["an"], ["vorstand@verein.example"])
        self.assertIn("Neu BW P3 Basic", m["text"])

    def test_api_schluessel_pruefung(self):
        self.assertEqual(api(SRV.basis, "GET", "/api/v1/status")[0], 401)
        self.assertEqual(api(SRV.basis, "GET", "/api/v1/status", schluessel=self.key[:-3] + "abc")[0], 401)
        code, x = api(SRV.basis, "GET", "/api/v1/status", schluessel=self.key)
        self.assertEqual((code, x["schluessel"]), (200, "Buchhaltung"))
        self.assertEqual(api(SRV.basis, "POST", "/api/v1/buchung", {"sparte": "BW", "parzelle": 1, "tarif": "Basic"}, self.key_lesen)[0], 403)
        self.assertEqual(api(SRV.basis, "GET", "/api/v1/gibtsnicht", schluessel=self.key)[0], 404)

    def test_api_schluessel_nur_als_pruefsumme(self):
        _, x = self.a.req("/api/daten?q=api")
        self.assertNotIn(self.key.split("_", 2)[2], json.dumps(x))

    def test_zahlung_bucht_und_mailt(self):
        n = len(SMTP.mails)
        code, x = api(SRV.basis, "POST", "/api/v1/ereignis", {"ereignis": "zahlung", "sparte": "BW", "parzelle": 7, "betrag": "120,50", "referenz": "RE-1",
                                                              "email": "kunde@example.org", "name": "Max", "tarif": "Basic"}, self.key)
        self.assertEqual(code, 200, x)
        self.assertTrue(all(e["ok"] for e in x["aktionen"]), x)
        mails = SMTP.warten(n + 2)[n:]
        betreffe = sorted(m["text"].split("Subject: ")[1].split("\n")[0].strip() for m in mails)
        self.assertEqual(betreffe, ["Neu BW P7 Basic", "Zahlung 120.50 RE-1"])       # Folge-Buchung löst „Mail bei Buchung“ aus
        _, b = api(SRV.basis, "GET", "/api/v1/buchungen?sparte=BW", schluessel=self.key)
        self.assertEqual(b["buchungen"]["BW"]["7"], "Basic")

    def test_zahlung_unter_mindestbetrag(self):
        code, x = api(SRV.basis, "POST", "/api/v1/ereignis", {"ereignis": "zahlung", "sparte": "BW", "parzelle": 8, "betrag": "50", "tarif": "Basic"}, self.key)
        self.assertEqual((code, x["aktionen"]), (200, []))

    def test_fremde_sparte_abgelehnt(self):
        code, _ = api(SRV.basis, "POST", "/api/v1/ereignis", {"ereignis": "zahlung", "sparte": "XYZ", "parzelle": 1}, self.key)
        self.assertEqual(code, 400)

    def test_probelauf_sendet_nichts(self):
        n = len(SMTP.mails)
        code, x = self.a.req("/api/automation-probe", {"ausloeser": "zahlung", "sparte": "BW", "tarif": "Basic", "betrag": "150"})
        self.assertEqual(code, 200)
        self.assertTrue(x["ergebnisse"])
        time.sleep(1)
        self.assertEqual(len(SMTP.mails), n)


class ZweiFaktor(unittest.TestCase):
    def test_einrichten_anmelden_wiederverwendung(self):
        a = admin()
        a.req("/api/benutzer-speichern", {"neu": True, "name": "zweifa", "passwort": "Zwei-Faktor-Pw-123", "passwort2": "Zwei-Faktor-Pw-123", "art": "admin"})
        s = Sitzung(SRV.basis)
        self.assertEqual(s.anmelden("zweifa", "Zwei-Faktor-Pw-123")[0], 200)
        _, x = s.req("/api/2fa-start", {})
        geheim = x["geheim"].replace(" ", "")
        code, x = s.req("/api/2fa-bestaetigen", {"code": totp(geheim)})
        self.assertEqual(code, 200, x)
        notfall = x["notfall"]
        t = Sitzung(SRV.basis)
        code, x = t.anmelden("zweifa", "Zwei-Faktor-Pw-123")
        self.assertEqual(code, 400)
        self.assertTrue(x.get("zweiter_faktor"))
        self.assertEqual(Sitzung(SRV.basis).anmelden("zweifa", "Zwei-Faktor-Pw-123", code=notfall[0])[0], 200)
        self.assertEqual(Sitzung(SRV.basis).anmelden("zweifa", "Zwei-Faktor-Pw-123", code=notfall[0])[0], 400)   # Notfall-Code nur einmal


class AnmeldungSicherheit(unittest.TestCase):
    def test_login_seite_und_aktiv(self):
        code, _, html = Sitzung(SRV.basis).roh("/")
        html = html.decode()
        self.assertIn('id="bleiben"', html)
        self.assertIn("automatisch abgemeldet", html)                 # Standard: nach 30 Minuten
        a = admin()
        code, x = a.req("/api/aktiv")
        self.assertEqual((code, x["abmelden_minuten"]), (200, 30))
        s = Sitzung(SRV.basis)
        code, kopf, _ = s.roh("/login", json.dumps({"benutzer": "admin", "passwort": PASSWORT, "bleiben": False}).encode(), {"Content-Type": "application/json"})
        self.assertEqual(code, 200)
        self.assertNotIn("Max-Age", kopf["Set-Cookie"])               # ohne „Angemeldet bleiben“: Sitzungs-Cookie

    def test_zwei_faktor_merken(self):
        a = admin()
        a.req("/api/benutzer-speichern", {"neu": True, "name": "merker", "passwort": "Merker-Passwort-1", "passwort2": "Merker-Passwort-1", "art": "admin"})
        s = Sitzung(SRV.basis)
        s.anmelden("merker", "Merker-Passwort-1")
        _, x = s.req("/api/2fa-start", {})
        _, x = s.req("/api/2fa-bestaetigen", {"code": totp(x["geheim"].replace(" ", ""))})
        notfall = x["notfall"]
        code, x = a.req("/api/sicherheit-einstellungen", {"2fa_merken_stunden": 24, "abmelden_minuten": 30})
        self.assertEqual((code, x["sicherheit"]["2fa_merken_stunden"]), (200, 24), x)
        b = Sitzung(SRV.basis)
        self.assertEqual(b.anmelden("merker", "Merker-Passwort-1", code=notfall[0])[0], 200)
        self.assertEqual(b.anmelden("merker", "Merker-Passwort-1")[0], 200)                    # gleicher Browser: ohne Code
        self.assertEqual(Sitzung(SRV.basis).anmelden("merker", "Merker-Passwort-1")[0], 400)   # anderer Browser: Code nötig
        alt, APP_TOKEN["wert"] = APP_TOKEN["wert"], b.req("/api/app-zugangstoken", {"neu": True, "name": "Test"})[1]["token"]   # eigener Token von merker
        try:
            code, x = api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "merker", "passwort": "Merker-Passwort-1", "code": notfall[1], "geraet": "Test"})
            self.assertTrue(x["merken"], x)
            code, y = api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "merker", "passwort": "Merker-Passwort-1", "merken": x["merken"], "geraet": "Test"})
        finally:
            APP_TOKEN["wert"] = alt
        self.assertEqual(code, 200, y)
        b.req("/api/2fa-vergessen", {})
        self.assertEqual(b.anmelden("merker", "Merker-Passwort-1")[0], 400)                    # vergessen → wieder Code
        a.req("/api/sicherheit-einstellungen", {"2fa_merken_stunden": 0})


def _png(farbe=0):
    import struct, zlib
    def chunk(t, x):
        return struct.pack(">I", len(x)) + t + x + struct.pack(">I", zlib.crc32(t + x) & 0xffffffff)
    roh = b"".join(b"\x00" + bytes([farbe, 120, 40]) * 4 for _ in range(4))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(roh)) + chunk(b"IEND", b"")


class Logos(unittest.TestCase):
    def test_logo_ablegen_und_auswaehlen(self):
        a = admin()
        code, _, x = a.roh("/api/logo?name=Vereinslogo.png", _png(10), {"Content-Type": "application/octet-stream"})
        x = json.loads(x)
        self.assertEqual(code, 200, x)
        self.assertTrue(x["karte"])                                       # auch unter Unterlagen abgelegt
        _, u = a.req("/api/unterlagen")
        self.assertIn("Logos", u["ordner"])
        self.assertTrue(any(f["ordner"] == "Logos" and f["name"] == "Vereinslogo.png" for f in u["dateien"]))
        code, _, _ = a.roh("/api/unterlage-hochladen?name=Zweitlogo.png&ordner=Logos", _png(200), {"Content-Type": "application/octet-stream"})
        self.assertEqual(code, 200)
        _, l = a.req("/api/logos")
        zweit = next(x for x in l["logos"] if x["name"] == "Zweitlogo.png")
        code, kopf, bild = a.roh("/api/logo-bild?id=" + zweit["id"])
        self.assertTrue(bild.startswith(b"\x89PNG"))
        code, x = a.req("/api/logo-waehlen", {"id": zweit["id"]})
        self.assertEqual(code, 200, x)
        self.assertTrue(x["logo_uri"].startswith("data:image/png"))
        code, x = a.req("/api/email-layout", {"logo_unterlage": zweit["id"]})
        self.assertEqual((code, x["layout"]["logo_unterlage"]), (200, zweit["id"]), x)
        _, v = a.req("/api/email-vorschau", {"html": "<p>Hallo</p>"})
        self.assertIn("data:image/png;base64", v["html"])
        code, _, pdf = a.roh("/api/unterlage-hochladen?name=Plan.pdf&ordner=Pl%C3%A4ne", b"%PDF-1.4 test", {"Content-Type": "application/octet-stream"})
        _, u = a.req("/api/unterlagen")
        pid = next(f["id"] for f in u["dateien"] if f["name"] == "Plan.pdf")
        self.assertEqual(a.req("/api/logo-waehlen", {"id": pid})[0], 400)    # kein Bild
        a.req("/api/email-layout", {"logo_unterlage": ""})


class TicketsAkte(unittest.TestCase):
    def test_schliessen_frueher_und_akte(self):
        a = admin()
        _, m = a.req("/api/mitglied-speichern", {"mitglied": {"vorname": "Tina", "nachname": "Timeline", "email": "tina@example.org", "sparte": "BW", "parzelle": "61"}})
        mid = m["id"]
        _, t1 = a.req("/api/ticket-speichern", {"ticket": {"betreff": "WLAN langsam", "email": "tina@example.org", "name": "Tina Timeline"}})
        t1 = t1["ticket"]["id"]
        self.assertEqual(a.req("/api/ticket-schliessen", {"id": t1})[0], 400)            # ohne Lösung
        code, x = a.req("/api/ticket-schliessen", {"id": t1, "loesung": "Kanal am Access Point gewechselt."})
        self.assertEqual((code, x["ticket"]["status"]), (200, "geschlossen"), x)
        self.assertEqual(a.req("/api/ticket-kommentar", {"id": t1, "text": "noch was"})[0], 400)   # geschlossen = nur lesen
        self.assertEqual(a.req("/api/ticket-speichern", {"ticket": {"id": t1, "prioritaet": "hoch"}})[0], 400)
        _, t2 = a.req("/api/ticket-speichern", {"ticket": {"betreff": "Wieder langsam", "sparte": "BW", "parzelle": "61"}})
        code, x = a.req("/api/ticket?id=" + t2["ticket"]["id"])
        self.assertEqual(x["mitglied"]["id"], mid)
        self.assertEqual([f["id"] for f in x["frueher"]], [t1])                           # frühere Anfrage sichtbar
        self.assertIn("Kanal", x["frueher"][0]["loesung"])
        _, o = a.req("/api/tickets?status=offen")
        self.assertNotIn(t1, [z["id"] for z in o["zeilen"]])
        code, x = a.req("/api/ticket-schliessen", {"id": t1, "wieder_oeffnen": True})
        self.assertEqual(x["ticket"]["status"], "bearbeitung")
        code, ak = a.req("/api/mitglied-akte?id=" + mid)
        self.assertEqual(code, 200, ak)
        self.assertEqual(sum(1 for e in ak["zeitleiste"] if e["art"] == "ticket"), 2)
        _, lst = a.req("/api/ticket-mitglieder?q=timeline")
        self.assertEqual(lst["mitglieder"][0]["id"], mid)
        code, x = a.req("/api/ticket-zuordnen", {"id": t2["ticket"]["id"], "mitglied": ""})
        self.assertIsNone(x["mitglied"])


class Gestaltung(unittest.TestCase):
    def test_seiten_und_profile(self):
        a = admin()
        code, g = a.req("/api/gestaltung")
        self.assertEqual(code, 200, g)
        _, kd = a.req("/api/design")
        code, x = a.req("/api/design", {"design": {**kd["design"], "farbe_akzent": "#224466"}})   # Kartendesign weiter speicherbar
        self.assertEqual(code, 200, x)
        code, x = a.req("/api/seiten-design", {"art": "login", "design": {"ueberschrift": "Willkommen <b>KGV</b>", "farbe_knopf": "#123456", "layout": "mittig",
                                                                           "impressum": "https://verein.example/impressum"}})
        self.assertEqual(code, 200, x)
        html = Sitzung(SRV.basis).roh("/")[2].decode()
        self.assertIn("Willkommen &lt;b&gt;KGV&lt;/b&gt;", html)          # kein eigenes HTML
        self.assertIn("--knopf:#123456", html)
        self.assertIn('class="mittig"', html)
        self.assertIn("https://verein.example/impressum", html)
        self.assertEqual(a.req("/api/seiten-design", {"art": "login", "design": {"farbe_knopf": "rot"}})[0], 400)
        self.assertEqual(a.req("/api/seiten-design", {"art": "login", "design": {"impressum": "javascript:alert(1)"}})[0], 400)
        code, _, _ = a.roh("/api/unterlage-hochladen?name=Hinter.png&ordner=Logos", _png(90), {"Content-Type": "application/octet-stream"})
        bid = next(x["id"] for x in a.req("/api/logos")[1]["logos"] if x["name"] == "Hinter.png")
        a.req("/api/seiten-design", {"art": "login", "design": {"hintergrund": bid}})
        code, _, bild = Sitzung(SRV.basis).roh("/seitenbild/login/hintergrund")
        self.assertTrue(bild.startswith(b"\x89PNG"))                      # öffentlich: nur das gewählte Bild
        self.assertEqual(Sitzung(SRV.basis).roh("/seitenbild/portal/logo")[0], 404)
        code, v = a.req("/api/seiten-vorschau", {"art": "portal", "design": {"marke": "KGV Test", "t_ticket": "Störung melden"}})
        self.assertIn("Störung melden", v["html"])
        a.req("/api/seiten-design", {"art": "login", "zuruecksetzen": True})
        a.req("/api/benutzer-speichern", {"neu": True, "name": "kassierer", "passwort": "Kassierer-Pw-123", "passwort2": "Kassierer-Pw-123", "art": "bereiche",
                                          "bereiche": {"rechnungen": "schreiben"}})
        code, x = a.req("/api/ansicht-profile", {"profile": {"kasse01": {"name": "Kassierer", "baum": {"tabs": {"benutzer": {"name": "Mein Zugang"}},
                                                    "karten": {"benutzer/apps-und-geraete": {"aus": True}}, "start": "rechnungen"}}}, "zuordnung": {"kassierer": "kasse01"}})
        self.assertEqual(code, 200, x)
        k = Sitzung(SRV.basis)
        k.anmelden("kassierer", "Kassierer-Pw-123")
        html = k.roh("/")[2].decode()
        self.assertIn('"Mein Zugang"', html)
        self.assertIn('"start": "rechnungen"', html)
        self.assertEqual(k.req("/api/ansicht-profile", {"profile": {}})[0], 403)     # ohne Recht „Oberfläche gestalten“


class Unterlagen(unittest.TestCase):
    def test_html_als_pdf_abgelehnt_und_pdf_als_download(self):
        a = admin()
        q = urllib.parse.urlencode({"name": "boese.pdf", "ordner": "Test"})
        code, _, _ = a.roh("/api/unterlage-hochladen?" + q, b"<!DOCTYPE html><script>alert(1)</script>")
        self.assertEqual(code, 400)
        code, _, _ = a.roh("/api/unterlage-hochladen?" + urllib.parse.urlencode({"name": "x.exe"}), b"MZ....")
        self.assertEqual(code, 400)
        code, _, roh = a.roh("/api/unterlage-hochladen?" + urllib.parse.urlencode({"name": "plan.pdf", "ordner": "Test"}), b"%PDF-1.4\n%test\n")
        self.assertEqual(code, 200, roh)
        datei = next(x for x in json.loads(roh)["dateien"] if x["name"] == "plan.pdf")
        code, kopf, inhalt = a.roh("/api/unterlage-datei?id=" + datei["id"])
        self.assertEqual(inhalt, b"%PDF-1.4\n%test\n")
        self.assertTrue(kopf["Content-Disposition"].startswith("attachment"))
        self.assertIn("sandbox", kopf["Content-Security-Policy"])


class UnterlagenOrdner(unittest.TestCase):
    def test_ordner_anlegen_hochladen_entfernen(self):
        a = admin()
        code, x = a.req("/api/unterlage-ordner", {"neu": "Wartung"})
        self.assertEqual(code, 200, x)
        self.assertIn("Wartung", x["ordner"])
        self.assertEqual(a.req("/api/unterlage-ordner", {"neu": "wartung"})[0], 400)          # gibt es schon
        code, _, roh = a.roh("/api/unterlage-hochladen?" + urllib.parse.urlencode({"name": "w.pdf", "ordner": "Wartung"}), b"%PDF-1.4\n%w\n")
        x = json.loads(roh)
        self.assertEqual(next(f for f in x["dateien"] if f["name"] == "w.pdf")["ordner"], "Wartung")
        self.assertEqual(x["anzahl"]["Wartung"], 1)
        self.assertEqual(a.req("/api/unterlage-ordner", {"loeschen": "Wartung"})[0], 400)     # nicht leer
        self.assertEqual(a.req("/api/unterlage-ordner", {"loeschen": "Verträge"})[0], 400)    # Standard bleibt
        i = next(f for f in x["dateien"] if f["name"] == "w.pdf")["id"]
        code, x = a.req("/api/unterlage-aendern", {"id": i, "ordner": "Pläne"})
        self.assertEqual(next(f for f in x["dateien"] if f["id"] == i)["ordner"], "Pläne")
        code, x = a.req("/api/unterlage-ordner", {"loeschen": "Wartung"})
        self.assertEqual(code, 200, x)
        self.assertNotIn("Wartung", x["ordner"])


class MitgliederTicketsEmail(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = admin()
        cls.a.req("/api/smtp-speichern", {"host": "127.0.0.1", "port": SMTP.port, "sicherheit": "keine", "anmeldung": "keine", "absender": "wlan@verein.example"})
        _, x = cls.a.req("/api/api-schluessel-neu", {"name": "Webseite", "rechte": ["mitglieder", "tickets"]})
        cls.key = x["neu"]

    def test_mitglied_von_hand_api_und_import(self):
        a = self.a
        code, x = a.req("/api/mitglied-speichern", {"mitglied": {"vorname": "Erika", "nachname": "Muster", "email": "Erika@Example.org", "telefon": "+49 3381 12345", "sparte": "BW", "parzelle": "5"}})
        self.assertEqual(code, 200, x)
        m = next(z for z in x["zeilen"] if z["nachname"] == "Muster")
        self.assertEqual((m["email"], m["parzelle"]), ("erika@example.org", 5))
        for falsch in ({"vorname": "", "nachname": ""}, {"nachname": "X", "email": "kaputt"}, {"nachname": "X", "sparte": "BW", "parzelle": "999"}, {"nachname": "X", "sparte": "XYZ"}, {"nachname": "X", "telefon": "abc"}):
            self.assertEqual(a.req("/api/mitglied-speichern", {"mitglied": falsch})[0], 400, falsch)
        code, x = api(SRV.basis, "POST", "/api/v1/mitglied", {"vorname": "Hans", "nachname": "Api", "email": "hans@example.org", "sparte": "BW", "parzelle": 6}, self.key)
        self.assertEqual((code, x["neu"]), (200, True), x)
        code, x = api(SRV.basis, "POST", "/api/v1/mitglied", {"email": "hans@example.org", "telefon": "0331 999"}, self.key)   # gleiche E-Mail → aktualisieren
        self.assertEqual((x["neu"], x["mitglied"]["telefon"], x["mitglied"]["nachname"]), (False, "0331 999", "Api"))
        csv_daten = "Vorname;Nachname;E-Mail;Telefon;Parzelle\nAnna;Import;anna@example.org;0331 1;7\nBodo;Fehler;kaputt;;8\nErika;Muster;erika@example.org;;5\n".encode("utf-8")
        code, _, roh = a.roh("/api/mitglieder-import?" + urllib.parse.urlencode({"name": "liste.csv", "sparte": "BW"}), csv_daten)
        x = json.loads(roh)
        self.assertEqual((x["neu"], x["geaendert"], x["fehler"], x["uebernommen"]), (1, 1, 1, False), x)
        code, _, roh = a.roh("/api/mitglieder-import?" + urllib.parse.urlencode({"name": "liste.csv", "sparte": "BW", "uebernehmen": "1"}), csv_daten)
        _, x = a.req("/api/mitglieder")
        self.assertEqual(sum(1 for z in x["zeilen"] if z["nachname"] == "Muster"), 1)                         # nicht doppelt
        self.assertTrue(any(z["nachname"] == "Import" for z in x["zeilen"]))
        code, kopf, roh = a.roh("/api/mitglieder-export")
        self.assertIn(b"Erika;Muster", roh)
        self.assertTrue(kopf["Content-Disposition"].startswith("attachment"))

    def test_mail_mit_layout_vorlage_und_kunde_aus_mitglied(self):
        a = self.a
        a.req("/api/mitglied-speichern", {"mitglied": {"vorname": "Karla", "nachname": "Kunde", "email": "karla@example.org", "sparte": "BW", "parzelle": "33"}})
        code, x = a.req("/api/email-vorlage-speichern", {"vorlage": {"name": "Willkommen", "betreff": "Willkommen {vorname}", "html": "<h2>Hallo {vorname}</h2><p>Tarif <b>{tarif}</b></p><script>alert(1)</script>"}})
        self.assertEqual(code, 200, x)
        vid = x["id"]
        self.assertNotIn("script", json.dumps(x["vorlagen"]))
        code, x = a.req("/api/automation-speichern", {"regel": {"name": "Willkommen", "ausloeser": "buchung", "bedingung": {"sparte": "BW", "tarif": "Max"},
                                                                "aktionen": [{"typ": "email", "an": "", "an_kunde": True, "vorlage": vid}]}})
        self.assertEqual(code, 200, x)
        n = len(SMTP.mails)
        a.req("/api/buchungen", {"sparte": "BW", "aenderungen": {"33": "Max"}})
        m = SMTP.warten(n + 1)
        neu = [x for x in m[n:] if "karla@example.org" in x["an"]]
        self.assertTrue(neu, m[n:])
        t = neu[0]["text"]
        self.assertIn("Willkommen Karla", t)
        self.assertIn("text/html", t)
        self.assertIn("text/plain", t)
        self.assertEqual(a.req("/api/email-vorlage-loeschen", {"id": vid})[0], 400)                           # noch in einer Regel benutzt
        _, v = a.req("/api/email-vorschau", {"betreff": "x", "html": "<p>{vorname}</p>", "layout": {"kopf": "Mein Verein"}})
        self.assertIn("Mein Verein", v["html"])

    def test_ticket_api_zuweisung_antwort(self):
        a = self.a
        a.req("/api/benutzer-speichern", {"neu": True, "name": "technik", "passwort": "Technik-Passwort-1", "passwort2": "Technik-Passwort-1", "art": "bereiche",
                                          "bereiche": {"tickets": "schreiben"}, "email": "technik@verein.example"})
        a.req("/api/automation-speichern", {"regel": {"name": "Zuweisung", "ausloeser": "ticket_zugewiesen", "aktionen": [
            {"typ": "email", "an": "{zustaendig_email}", "betreff": "Ticket {ticket}: {betreff}", "html": "<p>{nachricht}</p>"}]}})
        code, x = api(SRV.basis, "POST", "/api/v1/ticket", {"betreff": "WLAN geht nicht", "text": "Seit gestern kein Netz", "email": "kunde2@example.org", "name": "K. Zwei",
                                                            "sparte": "BW", "parzelle": 9, "prioritaet": "hoch"}, self.key)
        self.assertEqual(code, 400, x)                                   # ohne Vor-/Nachname und passendes Mitglied abgelehnt
        code, x = api(SRV.basis, "POST", "/api/v1/ticket", {"betreff": "WLAN geht nicht", "text": "Seit gestern kein Netz", "email": "kunde2@example.org",
                                                            "vorname": "K.", "nachname": "Zwei", "art": "kein_mitglied", "sparte": "BW", "prioritaet": "hoch"}, self.key)
        self.assertEqual(code, 200, x)
        nr = x["ticket"]
        self.assertEqual(api(SRV.basis, "GET", "/api/v1/ticket?nr=" + nr, schluessel=self.key)[1]["status"], "neu")
        _, liste = a.req("/api/tickets?status=offen")
        tid = next(z["id"] for z in liste["zeilen"] if z["nr"] == nr)
        n = len(SMTP.mails)
        code, x = a.req("/api/ticket-speichern", {"ticket": {"id": tid, "zustaendig": "technik"}})
        self.assertEqual(code, 200, x)
        mails = SMTP.warten(n + 1)
        self.assertTrue(any("technik@verein.example" in m["an"] and nr in m["text"] for m in mails[n:]), mails[n:])
        t = Sitzung(SRV.basis)
        self.assertEqual(t.anmelden("technik", "Technik-Passwort-1")[0], 200)
        _, x = t.req("/api/tickets?zustaendig=ich")
        self.assertEqual([z["nr"] for z in x["zeilen"]], [nr])
        n = len(SMTP.mails)
        code, x = t.req("/api/ticket-kommentar", {"id": tid, "html": "<p>Wir kümmern uns, {name}.</p>", "an_kontakt": True, "wartet": True})
        self.assertEqual(code, 200, x)
        mails = SMTP.warten(n + 1)
        self.assertTrue(any("kunde2@example.org" in m["an"] and f"[{nr}]" in m["text"] for m in mails[n:]))
        self.assertEqual(x["ticket"]["status"], "wartet")
        self.assertEqual(t.req("/api/ticket-loeschen", {"id": tid})[0], 403)                                   # löschen nur Admin
        code, x = t.req("/api/ticket-speichern", {"ticket": {"id": tid, "status": "erledigt"}})
        self.assertIn("Status: wartet auf Rückmeldung → erledigt", json.dumps(x["ticket"]["verlauf"], ensure_ascii=False))
        self.assertEqual(api(SRV.basis, "POST", "/api/v1/ticket", {"text": "ohne Betreff"}, self.key)[0], 400)


class Version50(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = a = admin()
        a.req("/api/smtp-speichern", {"host": "127.0.0.1", "port": SMTP.port, "sicherheit": "keine", "anmeldung": "keine", "absender": "wlan@verein.example"})
        a.req("/api/rechnung-einstellungen", {"firma": "KGV Test e.V.", "adresse": "Weg 1\n14770 Brandenburg", "iban": "DE89 3704 0044 0532 0130 00", "bic": "COBADEFFXXX"})
        a.req("/api/mitglied-speichern", {"mitglied": {"vorname": "Rita", "nachname": "Rechnung", "email": "rita@example.org", "sparte": "BW", "parzelle": "41"}})
        a.req("/api/mitglied-speichern", {"mitglied": {"vorname": "Paul", "nachname": "Portal", "email": "paul@example.org", "sparte": "BW", "parzelle": "42"}})
        a.req("/api/buchungen", {"sparte": "BW", "aenderungen": {"41": "Plus", "42": "Basic"}})

    def _mails_seit(self, n, anzahl=1):
        return SMTP.warten(n + anzahl)[n:]

    def test_rechnungen_pdf_versand_und_zahlungsabgleich(self):
        a = self.a
        code, v = a.req("/api/rechnungslauf", {"jahr": 2031})
        self.assertEqual(code, 200, v)
        self.assertTrue(any(x["parzelle"] == 41 for x in v["vorschau"]))
        code, x = a.req("/api/rechnungslauf", {"jahr": 2031, "ausfuehren": True})
        self.assertEqual(code, 200, x)
        r41 = next(z for z in x["zeilen"] if z["parzelle"] == 41)
        r42 = next(z for z in x["zeilen"] if z["parzelle"] == 42)
        self.assertEqual(a.req("/api/rechnungslauf", {"jahr": 2031, "ausfuehren": True})[0], 400)          # nicht doppelt
        code, kopf, pdf = a.roh("/api/rechnung-pdf?id=" + r41["id"])
        self.assertTrue(pdf.startswith(b"%PDF-1.4"))
        n = len(SMTP.mails)
        code, x = a.req("/api/rechnung-senden", {"ids": [r41["id"]]})
        self.assertEqual(code, 200, x)
        m = self._mails_seit(n)[0]
        self.assertIn("rita@example.org", m["an"])
        self.assertIn("application/pdf", m["text"])
        csvd = f"Buchungstag;Verwendungszweck;Auftraggeber;Betrag\n17.10.2031;{r41['nr']} WLAN;Rita Rechnung;180,00\n18.10.2031;Spende;Jemand;5,00\n".encode()
        code, _, roh = a.roh("/api/zahlungen-import", csvd)
        x = json.loads(roh)
        self.assertEqual(code, 200, x)
        z = next(z for z in x["zeilen"] if z["betrag"] == 180.0)
        self.assertEqual((z["rechnung"], z["grund"]), (r41["id"], "Rechnungsnummer"))
        code, x = a.req("/api/zahlungen-uebernehmen", {"import": x["import"], "zuordnung": {z["hash"]: z["rechnung"]}})
        self.assertEqual(next(y for y in x["zeilen"] if y["id"] == r41["id"])["status"], "bezahlt")
        _, _, roh = a.roh("/api/zahlungen-import", csvd)
        self.assertTrue(next(z for z in json.loads(roh)["zeilen"] if z["betrag"] == 180.0)["schon"])          # nicht doppelt buchen
        _, k = a.req("/api/api-schluessel-neu", {"name": "Bank", "rechte": ["ereignis"]})
        code, x = api(SRV.basis, "POST", "/api/v1/ereignis", {"ereignis": "zahlung", "betrag": "120", "referenz": r42["nr"]}, k["neu"])
        self.assertEqual(x["aktionen"][0]["aktion"], "Zahlung gebucht", x)

    def test_vertrag_und_rundschreiben(self):
        a = self.a
        _, v = a.req("/api/vertraege")
        z = next(z for z in v["zeilen"] if z["id"] == "BW-41")
        self.assertEqual((z["status"] in ("laufend", "Frist läuft ab"), z["laufzeit"]), (True, 12))
        code, v = a.req("/api/vertrag-kuendigen", {"id": "BW-41"})
        self.assertEqual(next(z for z in v["zeilen"] if z["id"] == "BW-41")["status"], "gekündigt")
        a.req("/api/vertrag-kuendigen", {"id": "BW-41", "zuruecknehmen": True})
        code, e = a.req("/api/rundschreiben-empfaenger", {"filter": {"sparten": ["BW"], "tarife": ["Plus"]}})
        self.assertEqual(code, 200, e)
        self.assertIn("rita@example.org", [x["email"] for x in e["beispiele"]])
        self.assertNotIn("paul@example.org", [x["email"] for x in e["beispiele"]])
        n = len(SMTP.mails)
        code, x = a.req("/api/rundschreiben-senden", {"filter": {"sparten": ["BW"], "tarife": ["Plus"]}, "betreff": "Wartung {vorname}", "html": "<p>Hallo {vorname}</p>"})
        self.assertEqual(code, 200, x)
        ende = time.time() + 10
        while time.time() < ende and not any("rita@example.org" in m["an"] and "Wartung Rita" in m["text"] for m in SMTP.mails[n:]):
            time.sleep(0.2)
        self.assertTrue(any("rita@example.org" in m["an"] and "Wartung Rita" in m["text"] for m in SMTP.mails[n:]), SMTP.mails[n:])

    def test_paechter_seite(self):
        a = self.a
        s = Sitzung(SRV.basis)
        self.assertEqual(s.roh("/portal")[0], 404)
        a.req("/api/portal-einstellungen", {"aktiv": True})
        code, _, html = s.roh("/portal")
        self.assertEqual(code, 200)
        self.assertIn(b"Zugangskarte", html)
        a.req("/api/ppsk", {"sparte": "BW", "art": "fehlende"})
        a.req("/api/seiten-design", {"art": "portal", "design": {"spamschutz": False}})     # Rechenaufgabe: eigener Test (Zeit)
        n = len(SMTP.mails)
        paul = {"vorname": "Paul", "nachname": "Portal", "email": "paul@example.org", "sparte": "BW", "parzelle": "42"}
        code, x = s.req("/portal/ticket", {"betreff": "Frage", "text": "Hallo", **paul, "nachname": "Falsch"})
        self.assertEqual(code, 400)                                      # Name passt nicht zum Mitglied
        self.assertNotIn("Portal", x["fehler"])
        code, x = s.req("/portal/ticket", {"betreff": "Frage", "text": "Hallo", **paul, "vorname": "PAUL "})
        self.assertEqual(code, 200, x)                                   # Groß-/Kleinschreibung und Leerzeichen egal
        nr = x["ticket"]
        code, x = s.req("/portal/ticket", {"betreff": "WLAN buchen?", "art": "interessent", "vorname": "Ina", "nachname": "Neu", "email": "ina@example.org", "sparte": "BW", "parzelle": "77"})
        self.assertEqual(code, 200, x)
        _, tl = a.req("/api/tickets?status=alle")
        ina = next(z for z in tl["zeilen"] if z["nr"] == x["ticket"])
        self.assertEqual((ina["kontakt"]["art"], ina["parzelle"]), ("interessent", ""))
        self.assertEqual(s.req("/portal/status", {"nr": nr, "email": "falsch@example.org", "vorname": "Paul", "nachname": "Portal"})[0], 400)
        self.assertEqual(s.req("/portal/status", {"nr": nr, "email": "paul@example.org", "vorname": "Paul", "nachname": "Portal"})[0], 400)  # Mitglied: Sparte/Parzelle fehlen
        code, x = s.req("/portal/status", {"nr": nr, **paul})
        self.assertEqual((code, x["status"]), (200, "neu"))
        code, x = s.req("/portal/status", {**paul})                                       # ohne Nummer: alle eigenen Anfragen
        self.assertEqual((code, x["liste"][0]["ticket"]), (200, nr), x)
        code, x = s.req("/portal/zugang", {**paul, "email": "falsch@example.org"})
        self.assertEqual(code, 200)
        code, x = s.req("/portal/zugang", paul)
        self.assertEqual(code, 200)
        mails = self._mails_seit(n, 2)
        karte = [m for m in mails if "Zugangskarte" in m["text"]]
        self.assertEqual(len(karte), 1, mails)
        self.assertIn("paul@example.org", karte[0]["an"])
        self.assertIn("application/pdf", karte[0]["text"])
        self.assertNotIn("SN", json.dumps(x))                       # kein Passwort in der Antwort
        for _ in range(6):
            code, x = s.req("/portal/zugang", paul)
        self.assertEqual(code, 400)                                  # Grenze

    def test_zz_mitgliederbereich(self):
        """/mein: Anmeldung per E-Mail-Code, eigene Daten, Wechsel als Anfrage, Bezahldienst mit signiertem Webhook (läuft als letzter der Klasse)"""
        import email as em, hashlib, hmac, re
        a = self.a
        s = Sitzung(SRV.basis)
        self.assertEqual(s.roh("/mein")[0], 404)
        code, x = a.req("/api/mitgliederbereich", {"aktiv": True, "modus": "anfrage"})
        self.assertEqual(code, 200, x)
        code, _, html = s.roh("/mein")
        self.assertEqual(code, 200)
        self.assertIn(b"Mitgliederbereich", html)
        self.assertEqual(s.req("/mein/daten", {})[0], 401)
        n = len(SMTP.mails)
        self.assertEqual(s.req("/mein/code", {"email": "unbekannt@example.org"})[0], 200)       # verrät nicht, ob es die Adresse gibt
        code, x = s.req("/mein/code", {"email": "Paul@Example.org"})
        self.assertEqual(code, 200, x)
        mails = self._mails_seit(n)
        self.assertEqual(len(mails), 1, mails)
        self.assertIn("paul@example.org", mails[0]["an"])
        teile = [p.get_payload(decode=True).decode("utf-8", "replace") for p in em.message_from_string(mails[0]["text"]).walk() if not p.is_multipart()]
        anmeldecode = re.search(r">(\d{6})<", " ".join(teile)).group(1)
        self.assertEqual(s.req("/mein/anmelden", {"email": "paul@example.org", "code": "000000" if anmeldecode != "000000" else "111111"})[0], 400)
        code, x = s.req("/mein/anmelden", {"email": "paul@example.org", "code": anmeldecode})
        self.assertEqual(code, 200, x)
        self.assertEqual(s.req("/mein/anmelden", {"email": "paul@example.org", "code": anmeldecode})[0], 400)    # nur einmal
        code, x = s.req("/mein/daten", {})
        self.assertEqual(code, 200, x)
        p = x["parzellen"][0]
        self.assertEqual((p["parzelle"], p["tarif"], x["mitglied"]), ("42", "Basic", "Paul Portal"))
        code, g = s.req("/mein/geraete", {"id": p["id"]})
        self.assertEqual(code, 200, g)
        self.assertRegex(g["netz"], r"^10\.\d+\.42\.0/24$")                          # Parzellen-Netz 10.<Sparte>.<Parzelle>.x
        # fremde Rechnung (Rita) nicht abrufbar
        _, rl = a.req("/api/rechnungen")
        rita = next((r for r in (rl.get("zeilen") or []) if r.get("parzelle") == 41), None)
        if rita:
            self.assertEqual(s.roh("/mein/rechnung?id=" + rita["id"])[0], 404)
        # nur eigene Tickets: gleiche E-Mail, aber andere Parzelle → nicht sichtbar
        a.req("/api/ticket-speichern", {"ticket": {"betreff": "Fremdes Ticket", "email": "paul@example.org", "sparte": "BW", "parzelle": "41"}})
        self.assertNotIn("Fremdes Ticket", json.dumps(s.req("/mein/daten", {})[1]["parzellen"][0]["tickets"]))
        # buchbare Tarife auswählen
        self.assertEqual(a.req("/api/mitgliederbereich", {"tarife": ["Basic", "Max"], "titel": "Mein WLAN"})[0], 200)
        self.assertIn(b"Mein WLAN", s.roh("/mein")[2])
        self.assertEqual([t["name"] for t in s.req("/mein/daten", {})[1]["tarife"]], ["Basic", "Max"])
        self.assertEqual(s.req("/mein/buchen", {"id": p["id"], "art": "wechsel", "tarif": "Plus"})[0], 400)
        # Upgrade jederzeit: sofort gebucht
        code, x = s.req("/mein/buchen", {"id": p["id"], "art": "wechsel", "tarif": "Max"})
        self.assertEqual(code, 200, x)
        self.assertEqual(s.req("/mein/daten", {})[1]["parzellen"][0]["tarif"], "Max")
        # Downgrade nur als Antrag mit Freigabe im Ticketsystem
        code, x = s.req("/mein/buchen", {"id": p["id"], "art": "wechsel", "tarif": "Basic"})
        self.assertEqual(code, 200, x)
        self.assertIn("freigegeben", x["text"])
        dd = s.req("/mein/daten", {})[1]["parzellen"][0]
        self.assertEqual((dd["tarif"], dd["antraege"][0]["tarif"]), ("Max", "Basic"))
        self.assertEqual(s.req("/mein/buchen", {"id": p["id"], "art": "wechsel", "tarif": "Basic"})[0], 400)     # nicht doppelt
        _, tl = a.req("/api/tickets?status=alle")
        tid = next(z["id"] for z in tl["zeilen"] if z["betreff"].startswith("Antrag: Downgrade Max → Basic"))
        self.assertEqual(a.req("/api/tarif-antrag", {"id": tid, "freigeben": False})[0], 400)                # Ablehnen nur mit Grund
        n = len(SMTP.mails)
        code, x = a.req("/api/tarif-antrag", {"id": tid, "freigeben": True})
        self.assertEqual(code, 200, x)
        self.assertEqual((x["ticket"]["status"], x["ticket"]["antrag"]["status"]), ("geschlossen", "freigegeben"))
        self.assertTrue(any("freigegeben" in m["text"] for m in self._mails_seit(n)))
        self.assertEqual(s.req("/mein/daten", {})[1]["parzellen"][0]["tarif"], "Basic")
        self.assertEqual(a.req("/api/tarif-antrag", {"id": tid, "freigeben": True})[0], 400)                  # nur einmal
        # Bezahldienst
        self.assertEqual(a.req("/api/mitgliederbereich", {"modus": "bezahldienst"})[0], 400)       # ohne Link/Schnittstelle
        code, x = a.req("/api/mitgliederbereich", {"modus": "bezahldienst", "checkout_vorlage": "https://bezahlen.example/pay?ref={referenz}&cent={betrag_cent}&zurueck={rueckkehr}", "geheim_neu": True})
        self.assertEqual(code, 200, x)
        geheim = x["geheim"]
        self.assertNotIn("geheim", a.req("/api/mitgliederbereich")[1])                            # nur einmal sichtbar
        code, x = s.req("/mein/buchen", {"id": p["id"], "art": "wechsel", "tarif": "Max"})
        self.assertEqual(code, 200, x)
        self.assertTrue(x["url"].startswith("https://bezahlen.example/pay?ref=SN-") and "cent=24000" in x["url"], x)
        ref = x["referenz"]
        roh = json.dumps({"referenz": ref, "betrag": 240, "status": "paid"}).encode()
        code, _, y = s.roh("/mein/zahlung-webhook", roh, {"Content-Type": "application/json", "X-SparteNet-Signatur": "sha256=falsch"})
        self.assertEqual(code, 400)
        self.assertEqual(s.req("/mein/daten", {})[1]["parzellen"][0]["tarif"], "Basic")            # nichts gebucht
        sig = "sha256=" + hmac.new(geheim.encode(), roh, hashlib.sha256).hexdigest()
        code, _, y = s.roh("/mein/zahlung-webhook", roh, {"Content-Type": "application/json", "X-SparteNet-Signatur": sig})
        self.assertEqual(code, 200, y)
        self.assertEqual(s.req("/mein/daten", {})[1]["parzellen"][0]["tarif"], "Max")
        code, _, y = s.roh("/mein/zahlung-webhook", roh, {"Content-Type": "application/json", "X-SparteNet-Signatur": sig})
        self.assertIn(b"schon bezahlt", y)                                                          # nicht doppelt
        _, x = a.req("/api/mitgliederbereich")
        self.assertEqual(next(z for z in x["auftraege"] if z["referenz"] == ref)["status"], "bezahlt")
        code, x = s.req("/mein/buchen", {"id": p["id"], "art": "wechsel", "tarif": "Basic"})          # Downgrade auch im Bezahlmodus nur als Antrag
        self.assertEqual(code, 200, x)
        _, tl = a.req("/api/tickets?status=offen")
        tid = next(z["id"] for z in tl["zeilen"] if z["betreff"].startswith("Antrag: Downgrade"))
        code, x = a.req("/api/tarif-antrag", {"id": tid, "freigeben": False, "grund": "Vertrag läuft noch"})
        self.assertEqual((code, x["ticket"]["antrag"]["status"]), (200, "abgelehnt"), x)
        self.assertEqual(s.req("/mein/daten", {})[1]["parzellen"][0]["tarif"], "Max")
        s.req("/mein/abmelden", {})
        self.assertEqual(s.req("/mein/daten", {})[0], 401)
        # Mitglieder-App: Anmeldung mit Code, dann dauerhafter Schlüssel im Kopf (kein Cookie)
        self.assertEqual(api(SRV.basis, "POST", "/mein/info", {})[1]["titel"], "Mein WLAN")
        n = len(SMTP.mails)
        api(SRV.basis, "POST", "/mein/code", {"email": "paul@example.org"})
        teile = [x.get_payload(decode=True).decode("utf-8", "replace") for x in em.message_from_string(self._mails_seit(n)[0]["text"]).walk() if not x.is_multipart()]
        code, x = api(SRV.basis, "POST", "/mein/anmelden", {"email": "paul@example.org", "code": re.search(r">(\d{6})<", " ".join(teile)).group(1), "app": True, "geraet": "Pixel"})
        self.assertEqual(code, 200, x)
        snm = x["token"]
        self.assertTrue(snm.startswith("snm_"))
        code, x = api(SRV.basis, "POST", "/mein/daten", {}, snm)
        self.assertEqual((code, x["parzellen"][0]["parzelle"]), (200, "42"), x)
        self.assertEqual(api(SRV.basis, "POST", "/mein/daten", {}, snm[:-2] + "xx")[0], 401)
        self.assertEqual(a.req("/api/mitgliederbereich")[1]["apps"], 1)
        self.assertEqual(api(SRV.basis, "GET", "/api/tickets", None, snm)[0], 401)                  # kein Zugang zum Manager
        api(SRV.basis, "POST", "/mein/abmelden", {}, snm)
        self.assertEqual(api(SRV.basis, "POST", "/mein/daten", {}, snm)[0], 401)
        a.req("/api/mitgliederbereich", {"aktiv": False, "modus": "anfrage", "tarife": [], "titel": ""})

    def test_app_zugang(self):
        a = self.a
        alt, APP_TOKEN["wert"] = APP_TOKEN["wert"], None
        code, x = api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "admin", "passwort": PASSWORT})
        if not alt:
            self.assertTrue(x.get("zugangstoken"), x)                  # ohne eingerichteten Token keine App-Anmeldung
        APP_TOKEN["wert"] = alt
        app_token(a)
        a.req("/api/benutzer-speichern", {"neu": True, "name": "appnutzer", "passwort": "App-Passwort-123", "passwort2": "App-Passwort-123", "art": "bereiche",
                                          "bereiche": {"tickets": "schreiben", "start": "lesen"}})
        code, x = api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "appnutzer", "passwort": "App-Passwort-123"})
        self.assertEqual((code, x.get("zugangstoken")), (401, True), x)          # Token des Administrators gilt nicht für andere Konten
        n = Sitzung(SRV.basis)
        self.assertEqual(n.anmelden("appnutzer", "App-Passwort-123")[0], 200)
        code, t1 = n.req("/api/app-zugangstoken", {"neu": True, "name": "Pixel 9"})
        self.assertEqual(code, 200, t1)
        code, t2 = n.req("/api/app-zugangstoken", {"neu": True, "name": "Tablet"})
        self.assertEqual([t["name"] for t in t2["tokens"]], ["Pixel 9", "Tablet"])             # beliebig viele, nur die eigenen
        self.assertNotIn("token", n.req("/api/app-zugangstoken")[1])                           # nur einmal angezeigt
        _, alle = a.req("/api/app-zugangstoken")
        self.assertTrue({"admin", "appnutzer"} <= {t["konto"] for t in alle["tokens"]})          # Administrator sieht alle
        adm = next(t["id"] for t in alle["tokens"] if t["konto"] == "admin")
        self.assertEqual(n.req("/api/app-zugangstoken", {"entfernen": adm})[0], 400)           # fremden Token nicht entfernen
        self.assertEqual(n.req("/api/app-zugangstoken", {"alle_sperren": True})[0], 400)
        admin_token, APP_TOKEN["wert"] = APP_TOKEN["wert"], t1["token"]
        try:
            self.assertEqual(api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "appnutzer", "passwort": "falsch-falsch"})[0], 401)
            code, x = api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "admin", "passwort": PASSWORT})
            self.assertEqual((code, x.get("zugangstoken")), (401, True), x)      # Token von appnutzer gilt nicht für admin
            code, x = api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "appnutzer", "passwort": "App-Passwort-123", "geraet": "Pixel 9"})
        finally:
            APP_TOKEN["wert"] = admin_token
        self.assertEqual(code, 200, x)
        tok = x["token"]
        zt = t1["token"]
        self.assertTrue(tok.startswith("sna_"))
        def mit_app(pfad, body=None):
            r = urllib.request.Request(SRV.basis + pfad, data=json.dumps(body).encode() if body is not None else None, method="POST" if body is not None else "GET")
            r.add_header("Authorization", "Bearer " + tok)
            r.add_header("X-App-Token", zt)
            r.add_header("Content-Type", "application/json")
            try:
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(r) as o:
                    return o.status, json.loads(o.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())
        code, x = mit_app("/api/app-uebersicht")
        self.assertEqual(code, 200, x)
        self.assertIn("tickets", x)
        self.assertNotIn("rechnungen", x)                          # kein Recht
        self.assertEqual(mit_app("/api/tickets")[0], 200)
        self.assertEqual(mit_app("/api/benutzer")[0], 403)
        self.assertEqual(mit_app("/api/ticket-speichern", {"ticket": {"betreff": "aus der App"}})[0], 200)
        code, x = mit_app("/api/v1/app/funktionen")
        self.assertTrue(any(f["pfad"] == "/api/tickets" for f in x["funktionen"]))
        zt, gueltig = APP_TOKEN["wert"], t1["token"]
        self.assertEqual(mit_app("/api/app-uebersicht")[0], 401)                 # Schlüssel von appnutzer + Token von admin: abgelehnt
        zt = t2["token"]
        self.assertEqual(mit_app("/api/app-uebersicht")[0], 200)                 # zweiter eigener Token geht auch
        n.req("/api/app-zugangstoken", {"entfernen": t2["tokens"][1]["id"]})
        self.assertEqual(mit_app("/api/app-uebersicht")[0], 401)                 # entfernt: kein Zugang mehr
        zt = gueltig
        code, x = mit_app("/api/app-zugangstoken")
        self.assertEqual(x["tokens"][0]["name"], "Pixel 9")
        self.assertTrue(x["tokens"][0]["zuletzt"])
        code, x = mit_app("/api/app-geraete")
        gid = x["geraete"][0]["id"]
        mit_app("/api/app-geraet-entfernen", {"id": gid})
        self.assertEqual(mit_app("/api/app-uebersicht")[0], 401)

    def test_android_app_ablauf(self):
        """genau die Aufrufe, die die Android-App macht"""
        app_token(self.a)
        self.assertEqual(api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "admin", "passwort": PASSWORT, "geraet": "x"})[0], 200)
        t = APP_TOKEN["wert"]; APP_TOKEN["wert"] = "snz_falsch"
        code, x = api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "admin", "passwort": PASSWORT, "geraet": "x"})
        APP_TOKEN["wert"] = t
        self.assertEqual(code, 401)
        self.assertTrue(x["zugangstoken"])
        code, x = api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "admin", "passwort": PASSWORT, "geraet": "Tablet Test"})
        self.assertEqual(code, 200, x)
        tok = x["token"]
        g = lambda pfad: api(SRV.basis, "GET", pfad, None, tok)
        p = lambda pfad, body: api(SRV.basis, "POST", pfad, body, tok)
        code, info = g("/api/v1/app/info")
        self.assertEqual((code, info["ich"]["admin"]), (200, True))
        self.assertIn("bereiche", info["ich"])
        code, sp = g("/api/buchungen")                                   # ohne Sparte: Liste für die Auswahl
        self.assertEqual(code, 200, sp)
        self.assertIn("BW", [x["kz"] for x in sp["sparten"]])
        code, b = g("/api/buchungen?sparte=BW")
        self.assertIn("Plus", b["tarife"])
        code, m = g("/api/mitglieder")
        self.assertIsInstance(m["sparten"], dict)
        code, t = p("/api/ticket-speichern", {"ticket": {"betreff": "WLAN weg", "text": "seit gestern", "prioritaet": "hoch", "zustaendig": "admin",
                                                         "sparte": "BW", "parzelle": "41", "name": "Rita R.", "email": "rita@example.org"}})
        self.assertEqual(code, 200, t)
        tid = t["ticket"]["id"]
        self.assertEqual(t["ticket"]["kontakt"]["email"], "rita@example.org")
        code, t = p("/api/ticket-speichern", {"ticket": {"id": tid, "status": "wartet"}})   # nur ein Feld ändern
        self.assertEqual((code, t["ticket"]["status"], t["ticket"]["betreff"]), (200, "wartet", "WLAN weg"))
        code, t = p("/api/ticket-kommentar", {"id": tid, "text": "Router neu gestartet", "an_kontakt": False})
        self.assertEqual(t["ticket"]["verlauf"][-1]["art"], "kommentar")
        code, lst = g("/api/tickets?status=offen&zustaendig=ich")
        self.assertTrue(any(z["id"] == tid for z in lst["zeilen"]))
        self.assertIn("admin", lst["konten"])
        code, u = g("/api/app-uebersicht")
        self.assertGreaterEqual(u["tickets"]["meine"], 1)
        self.assertEqual(g("/api/ueberwachung")[0], 200)
        self.assertEqual(g("/api/voucher-vorlagen")[0], 200)
        self.assertEqual(g("/api/plan")[0], 200)

    def test_datenschutz_und_wochenbericht(self):
        a = self.a
        _, m = a.req("/api/mitglied-speichern", {"mitglied": {"vorname": "Dora", "nachname": "Daten", "email": "dora@example.org", "sparte": "BW", "parzelle": "43"}})
        mid = m["id"]
        _, t = a.req("/api/ticket-speichern", {"ticket": {"betreff": "Geheim", "text": "meine Daten", "email": "dora@example.org"}})
        code, kopf, roh = a.roh("/api/mitglied-auskunft?id=" + mid)
        aus = json.loads(roh)
        self.assertEqual(aus["mitglied"]["email"], "dora@example.org")
        self.assertEqual(len(aus["tickets"]), 1)
        code, x = a.req("/api/mitglied-dsgvo-loeschen", {"id": mid})
        self.assertEqual(code, 200, x)
        self.assertFalse(any(z["id"] == mid for z in x["zeilen"]))
        _, t2 = a.req("/api/ticket?id=" + t["ticket"]["id"])
        self.assertNotIn("dora", json.dumps(t2).lower())
        n = len(SMTP.mails)
        code, x = a.req("/api/wochenbericht", {"jetzt": True, "an_test": "chef@verein.example"})
        self.assertEqual(code, 200, x)
        self.assertIn("Wochenbericht", self._mails_seit(n)[0]["text"])


class Datensicherung(unittest.TestCase):
    def test_verschluesselt_hin_und_zurueck(self):
        a = admin()
        a.req("/api/zuteilung-einstellen", {"an": False})
        a.req("/api/buchungen", {"sparte": "BW", "aenderungen": {"20": "Max"}})
        code, _, roh = a.roh("/api/sicherung-erstellen", json.dumps({"passwort": "Sicherung-Pw-123"}).encode(), {"Content-Type": "application/json"})
        self.assertEqual(code, 200)
        self.assertTrue(roh.startswith(b"SPARTENET-SICHERUNG-1\n"))
        with self.assertRaises(zipfile.BadZipFile):
            zipfile.ZipFile(io.BytesIO(roh))
        a.req("/api/buchungen", {"sparte": "BW", "aenderungen": {"20": ""}})
        code, _, _ = a.roh("/api/sicherung-einspielen", roh, {"X-Sicherung-Passwort": "falsch-falsch"})
        self.assertEqual(code, 400)
        code, _, x = a.roh("/api/sicherung-einspielen", roh, {"X-Sicherung-Passwort": urllib.parse.quote("Sicherung-Pw-123")})
        self.assertEqual(code, 200, x)
        _, b = a.req("/api/buchungen?sparte=BW")
        self.assertEqual(next(z for z in b["zeilen"] if z["p"] == 20)["tarif"], "Max")


if __name__ == "__main__":
    unittest.main()

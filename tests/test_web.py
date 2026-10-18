"""Tests über HTTP gegen einen echten Testserver (Dateispeicher, ohne Gateway): Anmeldung, Rechte, Automationen + E-Mail,
API-Schnittstelle, Zwei-Faktor, Unterlagen, Datensicherung"""
import io, json, os, sys, time, unittest, urllib.parse, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hilfe import PASSWORT, Sitzung, SmtpEmpfaenger, Testserver, api, totp   # noqa: E402

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
        n = len(SMTP.mails)
        code, x = s.req("/portal/ticket", {"betreff": "Frage", "text": "Hallo", "email": "paul@example.org", "sparte": "BW", "parzelle": "42"})
        self.assertEqual(code, 200, x)
        nr = x["ticket"]
        self.assertEqual(s.req("/portal/status", {"nr": nr, "email": "falsch@example.org"})[0], 400)
        code, x = s.req("/portal/status", {"nr": nr, "email": "paul@example.org"})
        self.assertEqual((code, x["status"]), (200, "neu"))
        code, x = s.req("/portal/zugang", {"sparte": "BW", "parzelle": "42", "email": "falsch@example.org"})
        self.assertEqual(code, 200)
        code, x = s.req("/portal/zugang", {"sparte": "BW", "parzelle": "42", "email": "paul@example.org"})
        self.assertEqual(code, 200)
        mails = self._mails_seit(n, 2)
        karte = [m for m in mails if "Zugangskarte" in m["text"]]
        self.assertEqual(len(karte), 1, mails)
        self.assertIn("paul@example.org", karte[0]["an"])
        self.assertIn("application/pdf", karte[0]["text"])
        self.assertNotIn("SN", json.dumps(x))                       # kein Passwort in der Antwort
        for _ in range(6):
            code, x = s.req("/portal/zugang", {"sparte": "BW", "parzelle": "42", "email": "paul@example.org"})
        self.assertEqual(code, 400)                                  # Grenze

    def test_app_zugang(self):
        a = self.a
        a.req("/api/benutzer-speichern", {"neu": True, "name": "appnutzer", "passwort": "App-Passwort-123", "passwort2": "App-Passwort-123", "art": "bereiche",
                                          "bereiche": {"tickets": "schreiben", "start": "lesen"}})
        self.assertEqual(api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "appnutzer", "passwort": "falsch-falsch"})[0], 401)
        code, x = api(SRV.basis, "POST", "/api/v1/app/anmelden", {"benutzer": "appnutzer", "passwort": "App-Passwort-123", "geraet": "Pixel 9"})
        self.assertEqual(code, 200, x)
        tok = x["token"]
        self.assertTrue(tok.startswith("sna_"))
        def mit_app(pfad, body=None):
            r = urllib.request.Request(SRV.basis + pfad, data=json.dumps(body).encode() if body is not None else None, method="POST" if body is not None else "GET")
            r.add_header("Authorization", "Bearer " + tok)
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
        code, x = mit_app("/api/app-geraete")
        gid = x["geraete"][0]["id"]
        mit_app("/api/app-geraet-entfernen", {"id": gid})
        self.assertEqual(mit_app("/api/app-uebersicht")[0], 401)

    def test_android_app_ablauf(self):
        """genau die Aufrufe, die die Android-App macht"""
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

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
        code, x = cls.a.req("/api/smtp-speichern", {"host": "127.0.0.1", "port": SMTP.port, "sicherheit": "keine", "absender": "wlan@verein.example",
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

"""Tests ohne Webserver: VLAN-Schema, Zuteilung nach Buchung, Umzugshilfe, TOTP, Prüfungen – mit nachgebautem Gateway"""
import json, os, sys, tempfile, time, unittest
from collections import Counter

_ORDNER = tempfile.mkdtemp(prefix="spartenet_logik_")
for k in [k for k in os.environ if k.startswith("SPARTENET_")]:
    del os.environ[k]
os.environ["SPARTENET_DATA_DIR"] = _ORDNER
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SparteNet_Manager"))

import spartenet.webserver as S   # noqa: E402  (lädt alle Module der Kette)
import spartenet.zuteilung as Z   # noqa: E402
import spartenet.umzug as U       # noqa: E402
import spartenet.voucher as V     # noqa: E402
import spartenet.ppsk as P        # noqa: E402
import spartenet.zeitplan as ZP   # noqa: E402
import spartenet.laufzeit as L    # noqa: E402
import datetime as dt             # noqa: E402


class FakeGateway:
    """nachgebaute klassische Schnittstelle: Netze (networkconf) und WLANs (wlanconf)"""
    netze, wlans, aufrufe = [], [], []

    def __init__(self, d=None):
        pass

    def legacy(self, methode, pfad, body=None):
        FakeGateway.aufrufe.append((methode, pfad))
        if methode == "GET" and pfad == "rest/networkconf":
            return [dict(n) for n in FakeGateway.netze]
        if methode == "GET" and pfad == "rest/wlanconf":
            return [dict(w) for w in FakeGateway.wlans]
        nid = pfad.rsplit("/", 1)[-1]
        if pfad.startswith("rest/networkconf/") and methode == "PUT":
            n = next(n for n in FakeGateway.netze if n["_id"] == nid)
            n.update(body)
            return []
        if pfad.startswith("rest/networkconf/") and methode == "DELETE":
            FakeGateway.netze = [n for n in FakeGateway.netze if n["_id"] != nid]
            return []
        if pfad.startswith("rest/wlanconf/") and methode == "PUT":
            w = next(w for w in FakeGateway.wlans if w["_id"] == nid)
            w.update(body)
            return []
        raise AssertionError(f"unerwarteter Aufruf {methode} {pfad}")


def frisch():
    for n in os.listdir(_ORDNER):
        p = os.path.join(_ORDNER, n)
        if os.path.isfile(p):
            os.remove(p)
    return S.lade()


class VlanSchema(unittest.TestCase):
    def test_alle_gateways_eindeutig(self):
        d = frisch()
        r = S.gwplan_berechnen(d)
        self.assertEqual(r["gesamt"]["fehler"], 0)
        for st in r["standorte"]:
            vlans = []
            for g in st["gateways"]:
                p = S.plan_berechnen(S.gwplan_gateway(d, st["nr"], g["gw"]))
                self.assertLessEqual(sum(1 for n in p["netze"] if n["art"] == "parzelle"), 55)
                vlans += [n["vlan"] for n in p["netze"]]
            self.assertEqual(len(vlans), len(set(vlans)), f"VLAN doppelt am Standort {st['name']}")

    def test_formel(self):
        self.assertEqual(S.vlan_parz(1, 1), 1001)
        self.assertEqual(S.vlan_parz(3, 86), 1486)
        self.assertEqual(S.vlan_dienst(20), {"vorstand": 120, "gaeste": 220, "technik": 320})

    def test_parzellenliste(self):
        p = S.plan_berechnen({"schema": "standort", "gateway": 3, "sparten": [{"name": "B", "kz": "BW", "sid": 20, "n": 86, "block": 3, "parzellen": [7, 2, 40], "dienst": False}]})
        self.assertEqual([n["vlan"] for n in p["netze"]], [1402, 1407, 1440])
        with self.assertRaises(S.Fehler):
            S.plan_berechnen({"schema": "standort", "gateway": 3, "sparten": [{"name": "B", "kz": "BW", "sid": 20, "n": 86, "block": 3, "parzellen": [99]}]})


class Pruefungen(unittest.TestCase):
    def test_totp_rfc6238(self):
        import base64
        geheim = base64.b32encode(b"12345678901234567890").decode()
        self.assertEqual(S.totp_code(geheim, 59 // 30), "287082")

    def test_kuerzel(self):
        self.assertEqual(S.kz_pruefen(" BW ", "SparteNet.de"), "BW")
        for falsch in ("../x", "VIELZULANGES", "A B", "Ä", ""):
            with self.assertRaises(S.Fehler):
                S.kz_pruefen(falsch, "SparteNet.de")

    def test_einzeilig(self):
        self.assertNotIn("\n", S.text_einzeilig("a\nb\r\nc", 50))


class Zuteilung(unittest.TestCase):
    def setUp(self):
        self.d = frisch()
        Z.Gateway = FakeGateway
        FakeGateway.netze, FakeGateway.wlans, FakeGateway.aufrufe = [], [], []
        S.akt_zuteilung_einstellen(self.d, {"an": True}, "test")

    def zt(self):
        return self.d["zuteilung"]["p"]

    def test_erst_gateway_1_dann_2(self):
        S.akt_buchungen_speichern(self.d, "BW", {str(p): "Basic" for p in range(1, 61)})
        self.assertEqual(Counter(e["gw"] for e in self.zt().values()), {1: 55, 2: 5})
        self.assertEqual(self.zt()["BW-56"]["gw"], 2)
        block = next(z["vlanblock"] for z in S.gwplan_berechnen(self.d)["zeilen"] if z["kz"] == "BW")
        self.assertEqual(self.zt()["BW-12"]["vlan"], S.vlan_parz(block, 12))          # VLAN fest an der Parzelle

    def test_luecke_wird_zuerst_gefuellt(self):
        S.akt_buchungen_speichern(self.d, "BW", {str(p): "Basic" for p in range(1, 61)})
        S.akt_buchungen_speichern(self.d, "BW", {"10": ""})                 # Netz war noch nicht angelegt → sofort frei
        self.assertNotIn("BW-10", self.zt())
        S.akt_buchungen_speichern(self.d, "BW", {"70": "Plus"})
        self.assertEqual(self.zt()["BW-70"]["gw"], 1)
        self.zt()["BW-5"]["status"] = "aktiv"
        S.akt_buchungen_speichern(self.d, "BW", {"5": ""})                  # Netz am Gateway → Platz bleibt belegt
        self.assertEqual(self.zt()["BW-5"]["status"], "entfernen")
        S.akt_buchungen_speichern(self.d, "BW", {"71": "Basic"})
        self.assertEqual(self.zt()["BW-71"]["gw"], 2)
        S.akt_buchungen_speichern(self.d, "BW", {"5": "Max"})               # wieder gebucht → bleibt, wie es ist
        self.assertEqual(self.zt()["BW-5"]["status"], "aktiv")

    def test_von_hand_vorgabe_und_verdichten(self):
        S.akt_buchungen_speichern(self.d, "BW", {str(p): "Basic" for p in range(1, 61)})
        st = self.zt()["BW-1"]["standort"]
        with self.assertRaises(S.Fehler):                                     # Gateway 1 ist voll
            S.akt_zuteilung_setzen(self.d, {"aenderungen": {"BW-56": 1}}, "test")
        S.akt_buchungen_speichern(self.d, "BW", {str(p): "" for p in range(1, 11)})
        r = S.akt_zuteilung_verdichten(self.d, {"standort": st}, "test")
        self.assertEqual({e["gw"] for e in self.zt().values()}, {1})          # alles auf Gateway 1
        self.assertIn("5 Parzelle(n) verschoben", r["log"][0])
        S.akt_zuteilung_setzen(self.d, {"aenderungen": {"BW-80": 2}}, "test")   # Vorgabe für noch nicht gebuchte Parzelle
        S.akt_buchungen_speichern(self.d, "BW", {"80": "Plus"})
        self.assertEqual((self.zt()["BW-80"]["gw"], self.zt()["BW-80"]["fest"]), (2, True))
        S.akt_zuteilung_verdichten(self.d, {"standort": st}, "test")
        self.assertEqual(self.zt()["BW-80"]["gw"], 2)                         # feste Zuordnung bleibt
        self.zt()["BW-12"]["status"] = "aktiv"
        S.akt_zuteilung_setzen(self.d, {"aenderungen": {"BW-12": 2}}, "test")    # mit Netz am Gateway 1 → Umzug
        self.assertEqual((self.zt()["BW-12"]["gw"], self.zt()["BW-12"]["status"], self.zt()["BW-12"]["alt_gw"]), (2, "anlegen", 1))
        S.akt_gwplan_vlan_uebernehmen(self.d, {"standort": st, "gw": 1})
        FakeGateway.netze = [{"_id": "n12", "name": "BW-Paz.012", "vlan": 1412}]
        v = S.akt_zuteilung_gateway(self.d, {})
        self.assertEqual([(x["netz"], x["grund"]) for x in v["entfernen"]], [("BW-Paz.012", "umgezogen zu Gateway 2")])
        S.akt_zuteilung_setzen(self.d, {"aenderungen": {"BW-12": 1}}, "test")    # zurück, Netz steht noch → aktiv
        self.assertEqual((self.zt()["BW-12"]["status"], "alt_gw" in self.zt()["BW-12"]), ("aktiv", False))

    def test_gateways_nach_buchungen_bemessen(self):
        S.akt_buchungen_speichern(self.d, "BW", {str(p): "Basic" for p in range(1, 21)})
        st = self.zt()["BW-1"]["standort"]
        voll = next(x for x in S.gwplan_berechnen(self.d)["standorte"] if x["nr"] == st)
        S.akt_gwplan_annahmen(self.d, {"annahmen": {"GW_Basis": 3}})
        wenig = next(x for x in S.gwplan_berechnen(self.d)["standorte"] if x["nr"] == st)
        self.assertGreater(voll["gw"], 1)
        self.assertEqual((wenig["gw"], wenig["gw_max"]), (1, voll["gw"]))
        self.assertLess(wenig["inv"], voll["inv"])
        self.assertEqual(len(wenig["gateways"]), voll["gw"])                  # VLAN-Plan behält Platz für alle Parzellen
        with self.assertRaises(S.Fehler):
            S.akt_gwplan_annahmen(self.d, {"annahmen": {"GW_Basis": 4}})

    def test_gateway_anlegen_und_entfernen(self):
        st = self.d["zuteilung"]
        S.akt_buchungen_speichern(self.d, "BW", {"3": "Basic", "4": "Basic", "6": "Basic"})
        standort = self.zt()["BW-3"]["standort"]
        S.akt_gwplan_vlan_uebernehmen(self.d, {"standort": standort, "gw": 1})
        self.assertTrue(self.d["plan"]["dynamisch"])
        FakeGateway.netze = [{"_id": "n3", "name": "BW-Paz.003", "vlan": 1403}, {"_id": "n80", "name": "BW-Paz.080", "vlan": 1480},
                             {"_id": "n6", "name": "BW-Paz.006", "vlan": 1406}]
        FakeGateway.wlans = [{"_id": "w", "name": "SparteNet.de-BW-Pächter", "private_preshared_keys": [{"networkconf_id": "n6", "password": "a"}, {"networkconf_id": "n3", "password": "b"}]}]
        self.zt()["BW-6"]["status"] = "aktiv"
        S.akt_buchungen_speichern(self.d, "BW", {"6": ""})
        v = S.akt_zuteilung_gateway(self.d, {})
        self.assertEqual([x["netz"] for x in v["anlegen"]], ["BW-Paz.004"])
        self.assertEqual([x["netz"] for x in v["entfernen"]], ["BW-Paz.006"])
        self.assertEqual([x["netz"] for x in v["ueberzaehlig"]], ["BW-Paz.080"])
        with self.assertRaises(S.Fehler):
            S.akt_zuteilung_gateway(self.d, {"ausfuehren": True, "entfernen": ["Gateway"]})
        angelegt = []
        Z.akt_netze = lambda d, kz, a, e, namen=None: (angelegt.extend(namen), FakeGateway.netze.extend({"_id": "x" + n, "name": n} for n in namen), {"log": []})[2]
        Z.akt_uebertragen = lambda *a: {"log": []}
        S.akt_zuteilung_gateway(self.d, {"ausfuehren": True, "anlegen": ["BW-Paz.004"], "entfernen": ["BW-Paz.006"]})
        self.assertEqual(angelegt, ["BW-Paz.004"])
        self.assertEqual(FakeGateway.wlans[0]["private_preshared_keys"], [{"networkconf_id": "n3", "password": "b"}])   # erst Zugang weg …
        self.assertNotIn("n6", [n["_id"] for n in FakeGateway.netze])                                                 # … dann Netz
        self.assertIn("n80", [n["_id"] for n in FakeGateway.netze])                                                   # nicht ausgewählt → bleibt
        self.assertNotIn("BW-6", self.zt())
        self.assertEqual(self.zt()["BW-4"]["status"], "aktiv")
        self.assertIs(st, self.d["zuteilung"])


class Umzug(unittest.TestCase):
    def setUp(self):
        self.d = frisch()
        U.Gateway = FakeGateway
        self.d["plan"] = {"schema": "standort", "gateway": 5, "praefix": "SparteNet.de",
                          "sparten": [{"name": "Buchenweg", "kz": "BW", "sid": 20, "n": 86, "block": 3, "p_von": 1, "p_bis": 3, "dienst": True}]}
        FakeGateway.netze = [
            {"_id": "a1", "name": "BW-Paz.001", "vlan": 1101, "vlan_enabled": True, "ip_subnet": "10.1.1.1/24", "dhcpd_enabled": True, "dhcpd_start": "10.1.1.10", "dhcpd_stop": "10.1.1.250"},
            {"_id": "a2", "name": "BW-Paz.002", "vlan": 1102, "vlan_enabled": True, "ip_subnet": "10.1.2.1/28", "dhcpd_enabled": True, "dhcpd_start": "10.1.2.6", "dhcpd_stop": "10.1.2.14"},
            {"_id": "a3", "name": "BW-Paz.003", "vlan": 1403, "vlan_enabled": True, "ip_subnet": "10.20.3.1/24"},
            {"_id": "f", "name": "Fremd", "vlan": 120, "vlan_enabled": True, "ip_subnet": "192.168.5.1/24"},
            {"_id": "v", "name": "BW-Vorstand", "vlan": 2011, "vlan_enabled": True, "ip_subnet": "10.1.200.1/24"},
        ]

    def test_vorschau_und_umstellen(self):
        v = S.akt_umzug(self.d, {})
        z = {x["netz"]: x for x in v["zeilen"]}
        self.assertEqual(set(z), {"BW-Paz.001", "BW-Paz.002", "BW-Vorstand"})
        self.assertEqual(z["BW-Paz.002"]["subnetz_neu"], "10.20.2.1/28")          # Netzmaske (Tarif) bleibt
        self.assertIn("belegt durch Fremd", z["BW-Vorstand"]["blockiert"])         # VLAN 120 ist schon vergeben
        self.assertEqual(v["gleich"], 1)
        S.akt_umzug(self.d, {"ausfuehren": True, "netze": ["a1", "a2", "v"]})
        n = {x["_id"]: x for x in FakeGateway.netze}
        self.assertEqual((n["a1"]["vlan"], n["a1"]["ip_subnet"], n["a1"]["dhcpd_start"], n["a1"]["dhcpd_stop"]), (1401, "10.20.1.1/24", "10.20.1.10", "10.20.1.250"))
        self.assertEqual((n["a2"]["dhcpd_start"], n["a2"]["dhcpd_stop"]), ("10.20.2.6", "10.20.2.14"))
        self.assertEqual(n["v"]["vlan"], 2011)                                      # blockiert → unverändert
        S.akt_umzug_rueckgaengig(self.d)
        n = {x["_id"]: x for x in FakeGateway.netze}
        self.assertEqual((n["a1"]["vlan"], n["a1"]["ip_subnet"]), (1101, "10.1.1.1/24"))

    def test_tausch_reihenfolge(self):
        # BW-Paz.001 soll VLAN 1401 – das hat gerade BW-Paz.002, das selbst umzieht → erst 002, dann 001
        FakeGateway.netze[1].update(vlan=1401)
        folge, blockiert = U._reihenfolge(FakeGateway.netze, [z for z in U.umzug_lage(self.d)[2] if z["netz"] in ("BW-Paz.001", "BW-Paz.002")])
        self.assertEqual([o["netz"] for o in folge], ["BW-Paz.002", "BW-Paz.001"])
        self.assertEqual(blockiert, [])

    def test_altes_schema_abgelehnt(self):
        self.d["plan"] = {"gateway": 1, "sparten": [{"name": "B", "kz": "BW", "sid": 1, "n": 5}]}
        with self.assertRaises(S.Fehler):
            S.akt_umzug(self.d, {})


class FakeVoucherGateway:
    """nachgebaute Integration-API für Hotspot-Voucher"""
    voucher, posts = [], []

    def __init__(self, d=None):
        pass

    def alle(self, pfad):
        assert pfad == V.VOUCHER_PFAD
        return [dict(x) for x in FakeVoucherGateway.voucher]

    def req(self, methode, pfad, body=None):
        if methode == "POST":
            FakeVoucherGateway.posts.append(body)
            neu = [{"id": f"n{len(FakeVoucherGateway.voucher) + i}", "code": f"{5550000000 + len(FakeVoucherGateway.voucher) + i}", "name": body["name"],
                    "timeLimitMinutes": body["timeLimitMinutes"], "authorizedGuestLimit": body.get("authorizedGuestLimit", 1), "authorizedGuestCount": 0,
                    "dataUsageLimitMBytes": body.get("dataUsageLimitMBytes"), "createdAt": "2026-10-17T08:00:00Z", "expired": False} for i in range(body["count"])]
            FakeVoucherGateway.voucher += neu
            return {"vouchers": neu}
        if methode == "DELETE":
            vid = pfad.rsplit("/", 1)[-1]
            FakeVoucherGateway.voucher = [x for x in FakeVoucherGateway.voucher if x["id"] != vid]
            return {}
        raise AssertionError(pfad)


class Voucher(unittest.TestCase):
    def setUp(self):
        self.d = frisch()
        V.Gateway = FakeVoucherGateway
        FakeVoucherGateway.posts = []
        FakeVoucherGateway.voucher = [
            {"id": "a", "code": "1234567890", "name": "Fest", "timeLimitMinutes": 1440, "authorizedGuestLimit": 1, "authorizedGuestCount": 1,
             "activatedAt": "2026-10-17T08:00:00Z", "expiresAt": "2026-10-18T08:00:00Z", "createdAt": "2026-10-16T10:00:00Z", "expired": False},
            {"id": "b", "code": "2222233333", "name": "Sommerfest", "timeLimitMinutes": 360, "authorizedGuestLimit": 3, "authorizedGuestCount": 0,
             "createdAt": "2026-10-16T11:00:00Z", "expired": False},
            {"id": "c", "code": "9999900000", "name": "Alt", "timeLimitMinutes": 60, "authorizedGuestCount": 1, "expired": True, "createdAt": "2026-01-01T10:00:00Z"},
        ]

    def test_vorlagen_pruefen(self):
        r = S.akt_voucher_vorlagen(self.d, {"vorlagen": [{"name": "Fest", "minuten": 360, "geraete": 3, "daten_mb": 500, "down_kbps": 10000, "up_kbps": 2000, "text": "Sommerfest"}]})
        self.assertEqual(r["vorlagen"][0]["minuten"], 360)
        for falsch in ([], [{"name": ""}], [{"name": "x", "minuten": 0}], [{"name": "x", "minuten": 60, "down_kbps": 1}], [{"name": "A"}, {"name": "a"}]):
            with self.assertRaises(S.Fehler):
                S.akt_voucher_vorlagen(self.d, {"vorlagen": falsch})

    def test_auslesen_status_und_vorschlaege(self):
        r = S.akt_voucher_liste(self.d)
        st = {z["code"]: z["status"] for z in r["zeilen"]}
        self.assertEqual(st, {"1234567890": "voll belegt", "2222233333": "unbenutzt", "9999900000": "abgelaufen"})
        self.assertEqual(next(z for z in r["zeilen"] if z["id"] == "a")["vorlage"], "Tagesgast")        # passt zur Standard-Vorlage
        self.assertIn((360, 3), [(v["minuten"], v["geraete"]) for v in r["vorschlaege"]])

    def test_erstellen_nach_vorlage(self):
        S.akt_voucher_vorlagen(self.d, {"vorlagen": [{"id": "fest", "name": "Fest", "minuten": 360, "geraete": 3, "daten_mb": 500, "down_kbps": 10000, "up_kbps": 2000}]})
        v = S.akt_voucher(self.d, 2, None, "", False, "fest")
        self.assertEqual(FakeVoucherGateway.posts, [])                                                    # Vorschau ändert nichts
        r = S.akt_voucher(self.d, 2, None, "", True, "fest")
        self.assertEqual(FakeVoucherGateway.posts[0], {"count": 2, "name": "Fest", "timeLimitMinutes": 360, "authorizedGuestLimit": 3,
                                                       "dataUsageLimitMBytes": 500, "rxRateLimitKbps": 10000, "txRateLimitKbps": 2000})
        self.assertEqual(len(r["codes"]), 2)
        self.assertIn("Vorschau", v["log"][0])

    def test_druck_im_kartendesign(self):
        r = S.akt_voucher_druck(self.d, {"ids": ["a", "b"], "sparte": "BW"})
        h = r["html"]
        self.assertEqual(h.count('class="seite"'), 2)
        self.assertIn("SparteNet.de-BW-Gäste", h)
        self.assertIn("12345-67890", h)
        self.assertIn("18.10.2026, 10:00 Uhr", h)                     # expiresAt in Ortszeit (Sommerzeit)
        self.assertIn("6 Stunden nach der ersten Anmeldung", h)       # noch nicht angemeldet
        self.assertIn("bis 3 Geräte", h)
        r = S.akt_voucher_druck(self.d, {"codes": ["22222-33333"], "ab_jetzt": True})
        self.assertNotIn("nach der ersten Anmeldung", r["html"])
        self.assertIn("Uhr", r["html"])
        with self.assertRaises(S.Fehler):
            S.akt_voucher_druck(self.d, {"ids": ["gibtsnicht"]})

    def test_qr_offenes_wlan(self):
        self.assertEqual(S.wlan_qr_text("Gast;1", ""), "WIFI:T:nopass;S:Gast\\;1;;")

    def test_loeschen(self):
        v = S.akt_voucher_loeschen(self.d, ["a", "c"], False)
        self.assertEqual(len(FakeVoucherGateway.voucher), 3)
        self.assertTrue(any("in Benutzung" in z for z in v["log"]))
        S.akt_voucher_loeschen(self.d, ["a", "c"], True)
        self.assertEqual([x["id"] for x in FakeVoucherGateway.voucher], ["b"])


class WlanZuordnung(unittest.TestCase):
    def setUp(self):
        self.d = frisch()
        P.Gateway = FakeGateway
        FakeGateway.netze = [{"_id": "n1", "name": "BW-Paz.001"}, {"_id": "n2", "name": "BW-Paz.002"}, {"_id": "x", "name": "Fremd"}]
        FakeGateway.wlans = [
            {"_id": "w1", "name": "Buchenweg Pächter", "private_preshared_keys_enabled": True,
             "private_preshared_keys": [{"networkconf_id": "n1", "password": "SN1111111111"}, {"networkconf_id": "n2", "password": "SN2222222222"}]},
            {"_id": "w2", "name": "Buchenweg Gast", "is_guest": True},
            {"_id": "w3", "name": "Anderes", "private_preshared_keys_enabled": True, "private_preshared_keys": [{"networkconf_id": "x", "password": "y"}]},
        ]

    def test_abrufen_zuordnen_und_passwoerter_holen(self):
        with self.assertRaises(S.Fehler) as f:                                   # Name nach Schema gibt es am Gateway nicht
            S.akt_ppsk(self.d, "BW", "gateway")
        self.assertIn("Schritt 2", str(f.exception))
        w = S.akt_wlans(self.d, "BW")
        self.assertEqual(w["vorschlag"]["paechter"], "Buchenweg Pächter")       # PPSK mit Parzellennetzen der Sparte
        self.assertEqual(w["vorschlag"]["gaeste"], "Buchenweg Gast")
        self.assertEqual(next(x for x in w["wlans"] if x["name"] == "Buchenweg Pächter")["eigene"], 2)
        S.akt_wlan_zuordnung(self.d, {"sparte": "BW", "paechter": "Buchenweg Pächter", "gaeste": "Buchenweg Gast"})
        r = S.akt_ppsk(self.d, "BW", "gateway")
        self.assertIn("2 vorhandene Passwörter", r["log"][0])
        self.assertEqual({z["WLAN"] for z in r["zeilen"]}, {"Buchenweg Pächter"})
        self.assertEqual({z["WLAN"] for z in S.lese_ppsk("BW")}, {"Buchenweg Pächter"})
        sp = next(x for x in S.plan_aktiv(self.d)["sparten"] if x["kz"] == "BW")
        self.assertEqual((sp["wlan"]["paechter"], sp["wlan"]["vorstand"], sp["wlan"]["eigen"]), ("Buchenweg Pächter", "SparteNet.de-BW-Vorstand", True))
        self.assertIn("Buchenweg Pächter", S.akt_karten(self.d, "BW", [1])["html"])
        pz = S.akt_parzelle(self.d, "BW", "1")
        self.assertEqual(pz["wlan"], "Buchenweg Pächter")
        self.assertTrue(pz["qr_matrix"] and all(len(z) == len(pz["qr_matrix"]) and set(z) <= {"0", "1"} for z in pz["qr_matrix"]))   # für die Android-App
        S.akt_wlan_zuordnung(self.d, {"sparte": "BW"})                           # zurück zum Schema
        self.assertEqual(S.wlan_ssid(self.d, "BW"), "SparteNet.de-BW-Pächter")
        self.assertEqual({z["WLAN"] for z in S.lese_ppsk("BW")}, {"SparteNet.de-BW-Pächter"})
        with self.assertRaises(S.Fehler):
            S.akt_wlan_zuordnung(self.d, {"sparte": "BW", "paechter": "x" * 33})


class Vertraege(unittest.TestCase):
    def test_perioden_und_frist(self):
        v = {"beginn": "2025-03-15", "laufzeit": 12, "verlaengerung": 12, "frist": 3}
        ende, kuendbar, st = S.vertrag_lage(v, dt.date(2026, 1, 10))
        self.assertEqual((ende, kuendbar, st), (dt.date(2026, 3, 14), dt.date(2025, 12, 14), "laufend"))
        ende, kuendbar, st = S.vertrag_lage(v, dt.date(2026, 6, 1))          # verlängert
        self.assertEqual(ende, dt.date(2027, 3, 14))
        self.assertEqual(S.plus_monate(dt.date(2024, 1, 31), 1), dt.date(2024, 2, 29))
        ende, _, st = S.vertrag_lage({**v, "ende_zum": "2026-03-14"}, dt.date(2026, 4, 1))
        self.assertEqual(st, "beendet")

    def test_buchung_legt_vertrag_an_und_erinnerung(self):
        d = frisch()
        S.akt_buchungen_speichern(d, "BW", {"7": "Basic"})
        v = d["vertraege"]["BW-7"]
        self.assertEqual(v["beginn"], dt.date.today().isoformat())
        v["beginn"] = (dt.date.today() - dt.timedelta(days=300)).isoformat()   # Frist (1 Monat) läuft in ~35 Tagen ab
        d["vertrag_einstellungen"] = {"erinnerung_tage": 60}
        gesehen = []
        S.EREIGNIS_EMPFAENGER.append(lambda t, x, dd: gesehen.append(t))
        try:
            S.vertraege_pruefen(d)
            S.vertraege_pruefen(d)                                           # nur einmal je Periode
        finally:
            S.EREIGNIS_EMPFAENGER.pop()
        self.assertEqual(gesehen.count("vertrag_erinnerung"), 1)
        S.akt_buchungen_speichern(d, "BW", {"7": ""})
        self.assertEqual(d["vertraege"]["BW-7"]["ende_zum"], dt.date.today().isoformat())


class Ueberwachung(unittest.TestCase):
    def test_offline_ticket_und_wieder_online(self):
        d = frisch()
        d["ueberwachung"] = {"aktiv": True, "verzoegerung": 10, "ticket": True, "auto_erledigen": True}
        geraete = [{"macAddress": "aa", "name": "AP Mast 3", "model": "U7", "state": "ONLINE"}, {"macAddress": "bb", "name": "Switch", "state": "ONLINE"}]
        class G:
            def __init__(self, d): pass
            def alle(self, pfad): return [dict(x) for x in geraete]
        ZP.Gateway = G
        t0 = 1_800_000_000
        self.assertEqual(S.stoerungen_pruefen(d, t0), [])
        geraete[0]["state"] = "OFFLINE"
        self.assertEqual(S.stoerungen_pruefen(d, t0 + 60), [])              # noch innerhalb der Verzögerung
        log = S.stoerungen_pruefen(d, t0 + 60 + 601)
        self.assertIn("Störung gemeldet: AP Mast 3", log[0])
        t = list(d["tickets"]["liste"].values())[-1]
        self.assertEqual((t["prioritaet"], t["status"]), ("hoch", "neu"))
        self.assertEqual(S.stoerungen_pruefen(d, t0 + 2000), [])            # nicht doppelt
        geraete[0]["state"] = "ONLINE"
        log = S.stoerungen_pruefen(d, t0 + 3000)
        self.assertIn("wieder online", log[0])
        self.assertEqual(t["status"], "erledigt")


class PdfUndBank(unittest.TestCase):
    def test_pdf_gueltig(self):
        p = S.PDF()
        p.text(50, 50, "Grüße – 12,00 € (Test)", 12, True)
        p.qr(50, 80, 100, "BCD\n002\n1\nSCT\n\nTest\nDE89370400440532013000\nEUR1.00")
        roh = p.ausgabe()
        self.assertTrue(roh.startswith(b"%PDF-1.4") and roh.rstrip().endswith(b"%%EOF"))
        self.assertIn(b"/WinAnsiEncoding", roh)

    def test_kontoauszug_formate(self):
        a = S.kontoauszug_lesen("Buchungstag;Valuta;Auftraggeber/Empfänger;Verwendungszweck;Betrag (EUR)\n01.10.26;01.10.26;Max;RE-2026-0001;1.234,50\n02.10.26;02.10.26;Strom;Abschlag;-50,00\n".encode("cp1252"))
        self.assertEqual([(x["datum"], x["betrag"], x["name"]) for x in a], [("2026-10-01", 1234.5, "Max")])
        c = S.kontoauszug_lesen("Buchungsdatum;Verwendungszweck;Name;Haben\n03.10.2026;Parzelle 12;Erika;120,00\n".encode())
        self.assertEqual(c[0]["betrag"], 120.0)


if __name__ == "__main__":
    unittest.main()


class Laufzeit(unittest.TestCase):
    """Tarif mit Laufzeit: Ablauf → Zugang (PPSK-Eintrag) sperren, Verlängern → wieder freigeben"""
    def setUp(self):
        self.d = frisch()
        P.Gateway = L.Gateway = FakeGateway
        FakeGateway.netze = [{"_id": "n1", "name": "BW-Paz.001"}, {"_id": "n2", "name": "BW-Paz.002"}]
        FakeGateway.wlans = [{"_id": "w1", "name": "SparteNet.de-BW-Pächter", "private_preshared_keys_enabled": True,
                              "private_preshared_keys": [{"networkconf_id": "n1", "password": "SN1111111111"}, {"networkconf_id": "n2", "password": "SN2222222222"}]}]
        S.akt_ppsk(self.d, "BW", "gateway")                          # Passwörter vom Gateway übernehmen
        tarife = S.tarife_pruefen(self.d["tarife"])
        tarife.append({"name": "Tag", "down": 20, "up": 5, "praefix": 29, "geraete": 5, "preis": 3, "laufzeit": 1, "laufzeit_einheit": "tage"})
        S.akt_tarife_speichern(self.d, {"tarife": tarife})

    def keys(self):
        return sorted(k["networkconf_id"] for k in FakeGateway.wlans[0]["private_preshared_keys"])

    def test_monate_kalendergenau(self):
        t = dt.datetime(2027, 1, 31, 10, 0).timestamp()
        self.assertEqual(dt.datetime.fromtimestamp(L.plus_laufzeit(t, 1, "monate")).date(), dt.date(2027, 2, 28))
        self.assertEqual(L.plus_laufzeit(t, 2, "stunden") - t, 7200)
        with self.assertRaises(S.Fehler):
            S.tarife_pruefen([{"name": "X", "down": 1, "up": 1, "praefix": 29, "laufzeit": 5, "laufzeit_einheit": "jahre"}])

    def test_ablauf_sperren_und_verlaengern(self):
        S.akt_buchungen_speichern(self.d, "BW", {"1": "Tag", "2": "Basic"})
        e = self.d["laufzeiten"]["BW-1"]
        self.assertAlmostEqual(e["ende"] - e["start"], 86400, delta=1)
        self.assertNotIn("BW-2", self.d["laufzeiten"])                # Tarif ohne Laufzeit
        e["ende"] = e["start"] - 1                                    # abgelaufen
        S.laufzeiten_pruefen(self.d)
        self.assertEqual(e["status"], "abgelaufen")
        self.assertEqual(self.keys(), ["n1", "n2"])                   # ohne Einschalten nichts am Gateway
        self.assertEqual(S.akt_laufzeiten(self.d)["zeilen"][0]["zustand"], "offen_sperren")
        S.akt_laufzeit_einstellungen(self.d, {"gateway_auto": True}, "admin")
        S.laufzeiten_pruefen(self.d)
        self.assertEqual(self.keys(), ["n2"])                         # nur Parzelle 1 gesperrt
        self.assertIn("BW-1", self.d["zugang_gesperrt"])
        self.assertTrue(any(z["Parzelle"] == 1 and z["status"] == "gleich" for z in P._ppsk_lage(self.d, "BW")[3]))   # Übertragen gibt sie nicht frei
        S.akt_laufzeit_verlaengern(self.d, {"sparte": "BW", "parzelle": 1}, "admin")
        self.assertEqual(self.d["laufzeiten"]["BW-1"]["status"], "aktiv")
        S.laufzeiten_pruefen(self.d)
        self.assertEqual(self.keys(), ["n1", "n2"])
        k1 = next(k for k in FakeGateway.wlans[0]["private_preshared_keys"] if k["networkconf_id"] == "n1")
        self.assertEqual(k1["password"], "SN1111111111")              # gleiches Passwort wie vorher
        self.assertNotIn("BW-1", self.d["zugang_gesperrt"])

    def test_von_hand_mit_vorschau(self):
        S.akt_buchungen_speichern(self.d, "BW", {"2": "Basic"})
        v = S.akt_zugang(self.d, {"sparte": "BW", "parzelle": 2, "aktion": "sperren"}, "admin")
        self.assertIn("Vorschau", v["log"][0])
        self.assertEqual(self.keys(), ["n1", "n2"])
        S.akt_zugang(self.d, {"sparte": "BW", "parzelle": 2, "aktion": "sperren", "ausfuehren": True}, "admin")
        self.assertEqual(self.keys(), ["n1"])
        S.akt_laufzeit_einstellungen(self.d, {"gateway_auto": True}, "admin")
        S.laufzeiten_pruefen(self.d)
        self.assertEqual(self.keys(), ["n1"])                         # von Hand gesperrt bleibt gesperrt
        S.akt_zugang(self.d, {"sparte": "BW", "parzelle": 2, "aktion": "freigeben", "ausfuehren": True}, "admin")
        self.assertEqual(self.keys(), ["n1", "n2"])

    def test_automation_verlaengert_nach_zahlung(self):
        S.akt_buchungen_speichern(self.d, "BW", {"1": "Tag"})
        self.d["laufzeiten"]["BW-1"]["ende"] = 1
        S.laufzeiten_pruefen(self.d)
        S.automation_daten(self.d)["regeln"].append({"id": "r1", "name": "Zahlung verlängert", "aktiv": True, "ausloeser": "zahlung",
                                                       "bedingung": {}, "aktionen": [{"typ": "laufzeit_verlaengern"}]})
        S.automation_verarbeiten("zahlung", {"sparte": "BW", "parzelle": 1, "betrag": 3}, self.d)
        self.assertEqual(self.d["laufzeiten"]["BW-1"]["status"], "aktiv")


class Leerlauf(unittest.TestCase):
    def test_leerlauf_beendet_sitzung(self):
        t = S.auth_sitzung_neu("Test", "admin")
        self.assertTrue(S.auth_sitzung_info(t, 1800))
        S._AUTH_SESSIONS[S._sitzung_hash(t)]["zuletzt"] -= 1800 + 120
        self.assertIsNone(S.auth_sitzung_info(t, 1800))
        t2 = S.auth_sitzung_neu("Test", "admin")
        S._AUTH_SESSIONS[S._sitzung_hash(t2)]["zuletzt"] -= 99999
        self.assertTrue(S.auth_sitzung_info(t2, 0))                    # 0 = nie abmelden


class Spamschutz(unittest.TestCase):
    def test_rechenaufgabe(self):
        import hmac, hashlib, time as zeit, re as rx
        f = S.spam_frage()
        a, b = map(int, rx.findall(r"\d+", f["frage"]))
        with self.assertRaises(S.Fehler):                                 # zu schnell
            S.spam_pruefen({"antwort": str(a + b), "frage_token": f["frage_token"]})
        ts = str(int(zeit.time()) - 10)
        tok = ts + "." + hmac.new(S._SPAM_GEHEIM, f"{a + b}|{ts}".encode(), hashlib.sha256).hexdigest()[:24]
        S.spam_pruefen({"antwort": str(a + b), "frage_token": tok})       # richtig
        with self.assertRaises(S.Fehler):
            S.spam_pruefen({"antwort": str(a + b + 1), "frage_token": tok})
        with self.assertRaises(S.Fehler):
            S.spam_pruefen({"antwort": str(a + b), "frage_token": tok, "text": "http://a http://b http://c"})

    def test_namensvergleich(self):
        self.assertEqual(S.name_norm(" Müller-Lüdenscheidt "), S.name_norm("mueller luedenscheidt"))
        self.assertEqual(S.name_norm("Straß"), S.name_norm("STRASS"))


class Mitgliederbereich(unittest.TestCase):
    def test_geraete_nach_ip(self):
        """Geräte gehören zur Parzelle, wenn die IP im Netz 10.<Sparte>.<Parzelle>.0/24 liegt; MAC nur gekürzt"""
        d = frisch()
        plan = S.plan_aktiv(d)
        sp = plan["sparten"][0]
        sid, kz = sp["sid"], sp["kz"]
        S._GERAETE_CACHE.update(zeit=time.time(), fehler="", liste=[
            {"name": "Handy", "ipAddress": f"10.{sid}.12.121", "macAddress": "aa:bb:cc:dd:ee:ff", "type": "WIRELESS"},
            {"name": "Nachbar", "ipAddress": f"10.{sid}.13.20", "macAddress": "11:22:33:44:55:66"},
            {"name": "Laptop", "ipAddress": f"10.{sid}.12.15", "macAddress": "aa:bb:cc:00:11:22", "type": "WIRED"}])
        d.setdefault("buchungen", {}).setdefault(kz, {})["12"] = "Basic"
        g = S.mb_geraete(d, kz, "12")
        self.assertEqual([x["name"] for x in g["geraete"]], ["Laptop", "Handy"])
        self.assertEqual([(x["nr"], x["art"]) for x in g["geraete"]], [(1, "Kabel"), (2, "WLAN")])      # fortlaufend nummeriert
        roh = json.dumps(g)
        for geheim in ("10.", "aa:bb", "dd:ee:ff", '"ip"', '"mac"'):                                  # keine IP- oder MAC-Adresse
            self.assertNotIn(geheim, roh)
        self.assertEqual((g["anzahl"], g["max"], g["tarif"]), (2, 3, "Basic"))                           # „Basic: 2 von 3“
        self.assertNotEqual(g["geraete"][0]["ref"], S._geraet_ref(kz, "13", "aa:bb:cc:00:11:22"))      # Kennung hängt an der Parzelle
        with self.assertRaises(S.Fehler):                                                               # Trennen nur, wenn eingeschaltet
            S.mb_geraet_trennen(d, kz, "12", {"ref": g["geraete"][0]["ref"], "bestaetigt": True})
        d["mitgliederbereich"] = {"geraete_trennen": True}
        with self.assertRaises(S.Fehler):                                                               # nur mit Bestätigung
            S.mb_geraet_trennen(d, kz, "12", {"ref": g["geraete"][0]["ref"]})
        with self.assertRaises(S.Fehler):                                                               # Sperren hat einen eigenen Schalter
            S.mb_geraet_trennen(d, kz, "12", {"ref": g["geraete"][0]["ref"], "bestaetigt": True, "sperren": True})
        from unittest import mock
        befehle = []
        class GW:                                                                                       # Gateway-Attrappe: merkt sich die Befehle
            def __init__(self, d): pass
            def legacy_cmd(self, pfad, body): befehle.append(body["cmd"]); return {}
        modul = S.mb_geraet_trennen.__globals__
        roh = S._geraete_roh(d, kz, "12")
        d["mitgliederbereich"] = {"geraete_trennen": True, "geraete_sperren": True}
        with mock.patch.dict(modul, {"Gateway": GW, "speichere": lambda d: None, "_geraete_roh": lambda d, kz, p: roh}):
            with self.assertRaises(S.Fehler):                                                           # Kabel lässt sich nur sperren, nicht trennen
                S.mb_geraet_trennen(d, kz, "12", {"ref": g["geraete"][0]["ref"], "bestaetigt": True})
            S.mb_geraet_trennen(d, kz, "12", {"ref": g["geraete"][1]["ref"], "bestaetigt": True})          # WLAN trennen: kick-sta
            S.mb_geraet_trennen(d, kz, "12", {"ref": g["geraete"][0]["ref"], "bestaetigt": True, "sperren": True})
            self.assertEqual(befehle, ["kick-sta", "block-sta"])
            gs = S.mb_geraete(d, kz, "12")["gesperrt"]
            self.assertEqual([x["name"] for x in gs], ["Laptop"])
            self.assertNotIn("aa:bb", json.dumps(gs))                                                    # Liste ohne MAC
            S.mb_geraet_zulassen(d, kz, "12", {"ref": gs[0]["ref"]})
            self.assertEqual(befehle[-1], "unblock-sta")
            self.assertEqual(S.mb_geraete(d, kz, "12")["gesperrt"], [])
            with self.assertRaises(S.Fehler):
                S.mb_geraet_zulassen(d, kz, "12", {"ref": gs[0]["ref"]})
        S._GERAETE_CACHE.update(zeit=0, liste=[])

    def test_webhook_signatur(self):
        import hashlib, hmac
        d = frisch()
        d["mitgliederbereich"] = {"geheim": "g"}
        with self.assertRaises(S.Fehler):
            S.mb_webhook(d, b'{"referenz":"SN-X"}', "sha256=00")
        roh = b'{"referenz":"SN-X"}'
        with self.assertRaises(S.Fehler):                     # Signatur stimmt, Auftrag gibt es nicht
            S.mb_webhook(d, roh, "sha256=" + hmac.new(b"g", roh, hashlib.sha256).hexdigest())


class TarifRegeln(unittest.TestCase):
    def test_downgrade_und_zusatzgeraete(self):
        """Downgrade nur eine Stufe, frühestens nach 3 Monaten, nicht mit zu vielen Geräten; Zusatzgeräte erhöhen die Grenze"""
        from unittest import mock
        d = frisch()
        kz = S.plan_aktiv(d)["sparten"][0]["kz"]
        d.setdefault("buchungen", {}).setdefault(kz, {})["12"] = "Max"
        d["tarif_seit"] = {f"{kz}-12": time.time() - 10 * 86400}                   # vor 10 Tagen auf Max gewechselt
        alle = {t["name"]: t for t in S.tarife_pruefen(d["tarife"])}
        info = S.downgrade_info(d, kz, "12")
        self.assertEqual(info["ziele"], ["Plus"])                                   # nur eine Stufe nach unten
        self.assertTrue(info["ab_text"])
        with self.assertRaises(S.Fehler) as f:
            S.downgrade_pruefen(d, kz, "12", alle["Basic"])
        self.assertIn("eine Stufe", str(f.exception))
        with self.assertRaises(S.Fehler) as f:
            S.downgrade_pruefen(d, kz, "12", alle["Plus"])
        self.assertIn("frühestens", str(f.exception))
        d["tarif_seit"][f"{kz}-12"] = time.time() - 100 * 86400                    # 3 Monate vorbei
        modul = S.downgrade_pruefen.__globals__
        with mock.patch.dict(modul, {"_geraete_roh": lambda d, kz, p: ([{}] * 6, "")}):
            with self.assertRaises(S.Fehler) as f:                                  # 6 Geräte verbunden, Plus erlaubt 5
                S.downgrade_pruefen(d, kz, "12", alle["Plus"])
            self.assertIn("1 Gerät(e) sperren", str(f.exception))
            d["zusatzgeraete"] = {f"{kz}-12": 1}                                    # mit einem Zusatzgerät passt es
            S.downgrade_pruefen(d, kz, "12", alle["Plus"])
            self.assertEqual(S.geraete_im_tarif(d, alle["Plus"], kz, "12"), 6)
        # Tarifwechsel merkt sich den Zeitpunkt, Kündigung entfernt die Zusatzgeräte
        S._tarif_ereignis("buchung", {"sparte": kz, "parzelle": 12, "tarif": "Plus"}, d)
        self.assertGreater(S.tarif_seit(d, kz, "12"), time.time() - 5)
        S._tarif_ereignis("kuendigung", {"sparte": kz, "parzelle": 12}, d)
        self.assertEqual(S.zusatz_geraete(d, kz, "12"), 0)
        self.assertEqual(S.zusatz_platz(alle["Basic"]), 2)                            # /29: 5 Plätze, Basic 3 → 2 Zusatzgeräte

    def test_rechnung_mit_zusatzgeraeten(self):
        d = frisch()
        kz = S.plan_aktiv(d)["sparten"][0]["kz"]
        d.setdefault("buchungen", {}).setdefault(kz, {})["12"] = "Basic"
        d["zusatzgeraete"] = {f"{kz}-12": 2}
        d["mitgliederbereich"] = {"zusatz_preis": 1.5}
        modul = S.akt_rechnungslauf.__globals__
        with mock_patch(modul, "_mitglied_der_parzelle", lambda d, kz, p: ("m1", {"vorname": "A", "nachname": "B"})):
            x = S.akt_rechnungslauf(d, {"jahr": 2027}, "test")
        z = next(v for v in x["vorschau"] if v["parzelle"] == 12)
        self.assertEqual((z["preis"], z["zusatz"]), (123.0, 2))                     # 120 € + 2 × 1,50 €


class Restguthaben(unittest.TestCase):
    def test_restguthaben_beim_wechsel(self):
        """Wechsel mitten in der Laufzeit: Restwert des alten Tarifs wird Guthaben und mit der Rechnung verrechnet"""
        d = frisch()
        kz = S.plan_aktiv(d)["sparten"][0]["kz"]
        for t in d["tarife"]:
            t.update(laufzeit=12, laufzeit_einheit="monate")
        d.setdefault("buchungen", {}).setdefault(kz, {})["12"] = "Basic"
        jetzt = time.time()
        d["laufzeiten"] = {f"{kz}-12": {"sparte": kz, "parzelle": 12, "tarif": "Basic", "start": jetzt - 100 * 86400, "ende": jetzt + 100 * 86400, "status": "aktiv"}}
        self.assertAlmostEqual(S.restwert(d, kz, 12), 60.0, delta=0.05)           # halbe Laufzeit von 120 €
        S._tarif_ereignis("buchung", {"sparte": kz, "parzelle": 12, "tarif": "Max", "tarif_alt": "Basic"}, d)
        self.assertAlmostEqual(S.guthaben(d, kz, 12), 60.0, delta=0.05)
        S._tarif_ereignis("buchung", {"sparte": kz, "parzelle": 12, "tarif": "Max", "tarif_alt": ""}, d)   # Neubuchung: kein Guthaben
        self.assertAlmostEqual(S.guthaben(d, kz, 12), 60.0, delta=0.05)
        d["buchungen"][kz]["12"] = "Max"
        modul = S.akt_rechnungslauf.__globals__
        with mock_patch(modul, "_mitglied_der_parzelle", lambda d, kz, p: ("m1", {"vorname": "A", "nachname": "B"})):
            with mock_patch(modul, "speichere", lambda d: None):
                vor = S.akt_rechnungslauf(d, {"jahr": 2027}, "test")
                z = next(v for v in vor["vorschau"] if v["parzelle"] == 12)
                self.assertAlmostEqual(z["preis"], 180.0, delta=0.05)                # 240 € − 60 € Guthaben
                S.akt_rechnungslauf(d, {"jahr": 2027, "ausfuehren": True}, "test")
        self.assertEqual(S.guthaben(d, kz, 12), 0.0)                                 # verbraucht
        x = next(r for r in S.rechnungen_daten(d)["liste"].values() if r["parzelle"] == 12)
        self.assertLess(x["positionen"][-1]["gesamt"], 0)                           # Position „Abzüglich Guthaben“
        S.guthaben_buchen(d, kz, 12, -5, "zu viel")                                  # nie unter 0
        self.assertEqual(S.guthaben(d, kz, 12), 0.0)


def mock_patch(modul, name, wert):
    from unittest import mock
    return mock.patch.dict(modul, {name: wert})


class AppUpdates(unittest.TestCase):
    def test_apk_hochladen_pruefen_entfernen(self):
        """neue APK für Mitglieder- oder Manager-App: nur echte APK, Versionsnummer muss steigen, Prüfsumme für die App"""
        import hashlib, io, zipfile
        d = frisch()
        q = lambda **k: {x: [str(v)] for x, v in k.items()}
        self.assertEqual(S.app_update_info(d, "mitglied"), {})
        with self.assertRaises(S.Fehler):
            S.akt_app_update_hochladen(d, q(art="mitglied", version_code=3), b"kein apk" * 200, "admin")
        puffer = io.BytesIO()
        with zipfile.ZipFile(puffer, "w") as z:
            z.writestr("AndroidManifest.xml", b"\x03\x00" * 400)
            z.writestr("classes.dex", b"dex\n035" + bytes(2000))
        apk = puffer.getvalue()
        with self.assertRaises(S.Fehler):
            S.akt_app_update_hochladen(d, q(art="unbekannt", version_code=3), apk, "admin")
        r = S.akt_app_update_hochladen(d, q(art="mitglied", version_code=3, version_name="1.2", hinweis="Neu"), apk, "admin")
        info = S.app_update_info(d, "mitglied")
        self.assertEqual((info["version_code"], info["version_name"], info["sha256"]), (3, "1.2", hashlib.sha256(apk).hexdigest()))
        self.assertEqual(r["apps"]["manager"].get("version_code"), None)
        self.assertEqual(S.app_apk_lesen(d, "mitglied"), apk)
        with self.assertRaises(S.Fehler):                                   # Versionsnummer muss steigen
            S.akt_app_update_hochladen(d, q(art="mitglied", version_code=3), apk, "admin")
        S.akt_app_update_hochladen(d, q(art="manager", version_code=7), apk, "admin")
        self.assertEqual(S.app_update_info(d, "manager")["version_code"], 7)
        S.akt_app_update(d, {"art": "mitglied", "entfernen": True}, "admin")
        self.assertEqual(S.app_update_info(d, "mitglied"), {})
        with self.assertRaises(S.Fehler):
            S.app_apk_lesen(d, "mitglied")


def _axml(paket, code, name):
    """kleines binäres AndroidManifest.xml (wie aapt2 es schreibt): String-Pool, Ressourcen-Kennungen, <manifest>"""
    import struct
    strs = ["versionCode", "versionName", "package", "manifest", name, paket]
    pool_daten, offs = b"", []
    for x in strs:
        offs.append(len(pool_daten))
        pool_daten += struct.pack("<H", len(x)) + x.encode("utf-16-le") + b"\0\0"
    while len(pool_daten) % 4:
        pool_daten += b"\0"
    kopf = 28
    start = kopf + 4 * len(strs)
    pool = struct.pack("<HHIIIIII", 0x0001, kopf, start + len(pool_daten), len(strs), 0, 0, start, 0) + b"".join(struct.pack("<I", o) for o in offs) + pool_daten
    resmap = struct.pack("<HHI", 0x0180, 8, 8 + 8) + struct.pack("<II", 0x0101021B, 0x0101021C)
    attrs = [struct.pack("<IIIHBBI", 0xFFFFFFFF, 0, 0xFFFFFFFF, 8, 0, 0x10, code),
             struct.pack("<IIIHBBI", 0xFFFFFFFF, 1, 4, 8, 0, 0x03, 4),
             struct.pack("<IIIHBBI", 0xFFFFFFFF, 2, 5, 8, 0, 0x03, 5)]
    ext = struct.pack("<IIHHHHHH", 0xFFFFFFFF, 3, 20, 20, len(attrs), 0, 0, 0)
    el_inhalt = struct.pack("<II", 1, 0xFFFFFFFF) + ext + b"".join(attrs)
    element = struct.pack("<HHI", 0x0102, 16, 8 + len(el_inhalt)) + el_inhalt
    rumpf = pool + resmap + element
    return struct.pack("<HHI", 0x0003, 8, 8 + len(rumpf)) + rumpf


class ApkVersion(unittest.TestCase):
    def test_version_aus_manifest(self):
        import io, zipfile
        puffer = io.BytesIO()
        with zipfile.ZipFile(puffer, "w") as z:
            z.writestr("AndroidManifest.xml", _axml("de.spartenet.mitglied", 1_500_123, "1.3 (20.10.2026 19:40)"))
            z.writestr("classes.dex", b"dex\n035" + bytes(2000))
        apk = puffer.getvalue()
        self.assertEqual(S.apk_version(apk), (1_500_123, "1.3 (20.10.2026 19:40)", "de.spartenet.mitglied"))
        d = frisch()
        r = S.akt_app_update_hochladen(d, {"art": ["mitglied"]}, apk, "admin")          # ohne Angaben – alles aus der APK
        self.assertEqual((r["apps"]["mitglied"]["version_code"], r["apps"]["mitglied"]["version_name"]), (1_500_123, "1.3 (20.10.2026 19:40)"))
        with self.assertRaises(S.Fehler):                                               # falsche App gewählt
            S.akt_app_update_hochladen(d, {"art": ["manager"]}, apk, "admin")


class AppZugangstokens(unittest.TestCase):
    def test_alter_gemeinsamer_token_bleibt_gueltig(self):
        """der eine Token aus 5.3/5.4 wird übernommen und gilt weiter für alle Konten, bis der Administrator ihn entfernt"""
        d = frisch()
        d["app_zugang"] = {"hash": S._zt_hash("snz_alt"), "erstellt": "2026-10-01 10:00", "von": "admin", "hinweis": "snz_alt…"}
        i = S.zugangstoken_finden(d, "snz_alt", "irgendwer")
        self.assertTrue(i)
        self.assertNotIn("app_zugang", d)
        self.assertEqual(S.zugangstoken_finden(dict(d, app_zugang={"hash": S._zt_hash("snz_alt")}), "snz_alt"), i)   # gleiche Id bei jedem Laden
        x = S.akt_app_zugangstoken(d, {"neu": True, "name": "Handy"}, "peter")
        self.assertEqual(S.zugangstoken_finden(d, x["token"], "peter"), x["neu_id"])
        self.assertIsNone(S.zugangstoken_finden(d, x["token"], "admin"))
        self.assertEqual(len(S.akt_app_zugangstoken(d, {}, "peter")["tokens"]), 1)
        self.assertEqual(len(S.akt_app_zugangstoken(d, {}, "admin", True)["tokens"]), 2)


class MitgliederEinmalcode(unittest.TestCase):
    def test_ohne_email_versand_klare_meldung_ohne_technik(self):
        d = frisch()
        d["mitglieder"] = {"m1": {"vorname": "A", "nachname": "B", "email": "a@example.org", "sparte": "BW", "parzelle": "1"}}
        for adresse in ("a@example.org", "unbekannt@example.org"):         # gleiche Antwort – verrät nicht, ob es die Adresse gibt
            with self.assertRaises(S.Fehler) as f:
                S.mb_code_anfordern(d, {"email": adresse}, "test")
            self.assertIn("E-Mail-Versand des Vereins", str(f.exception))
        self.assertFalse(S.mb_versand_bereit(d))


class Spartenlogos(unittest.TestCase):
    def test_erzeugen_erkennen_pdf(self):
        d = frisch()
        png = S.vereinslogo_png("Buchenweg", "BW")
        b = S.bild_fuer_pdf(png)
        self.assertEqual((b["breite"], b["hoehe"], b["farben"]), (256, 256, 3))
        self.assertTrue(any(v == 0 for v in b["alpha"]) and any(v == 255 for v in b["alpha"]))     # rund: außen durchsichtig
        self.assertEqual([S.logo_motiv(n) for n in ("Buchenweg", "Rosengarten", "Am Mühlenteich", "Sonnenhang", "Eintracht")],
                         ["baum", "bluete", "wellen", "sonne", "blatt"])
        self.assertEqual(S.logo_farbe("Buchenweg"), S.logo_farbe("Buchenweg"))
        d["mitglieder"] = {"a": {"email": "x@example.org", "sparte": "BW"}, "b": {"email": "y@example.org", "sparte": "BW"},
                           "c": {"email": "y@example.org", "sparte": "RG"}}
        self.assertEqual(S.sparte_aus_email(d, "X@example.org"), "BW")
        self.assertEqual(S.sparte_aus_email(d, "y@example.org"), "")          # zwei Sparten → nicht eindeutig
        p = S.PDF()
        self.assertGreater(p.bild(10, 10, 50, 50, png), 0)
        self.assertEqual(p.bild(10, 10, 50, 50, b"kein Bild"), 0)
        roh = p.ausgabe()
        self.assertIn(b"/XObject", roh)
        self.assertIn(b"/SMask", roh)
        h = S.email_html(d, "<p>x</p>", "t", "cid:a", "cid:b")
        self.assertIn('src="cid:a"', h)
        self.assertIn('src="cid:b"', h)


class StoerungImMitgliederbereich(unittest.TestCase):
    def test_meldung_je_sparte(self):
        d = frisch()
        jetzt = time.time()
        S.stand_schreiben({"geraete": {"aa": {"name": "AP Festwiese", "model": "U6", "offline_seit": jetzt - 3600, "gemeldet": jetzt - 2000},
                                       "bb": {"name": "AP Vereinsheim", "offline_seit": jetzt - 60}}})        # bb noch nicht gemeldet
        e = S.mb_einstellungen(d)
        m = S.mb_stoerungen(d, e, "BW")
        self.assertEqual(len(m), 1)
        self.assertIn("AP Festwiese", m[0]["text"])
        self.assertTrue(m[0]["text"].startswith("Achtung"))
        d["geraete_sparten"] = {"aa": "RG"}
        self.assertEqual(S.mb_stoerungen(d, e, "BW"), [])                      # Gerät gehört zu einer anderen Sparte
        self.assertEqual(len(S.mb_stoerungen(d, e, "RG")), 1)
        self.assertEqual(S.mb_stoerungen(d, e, None, nur_alle=True), [])       # Anmeldeseite ohne E-Mail: nur „alle Sparten“
        d["mitgliederbereich"] = {"stoerung_zeigen": False}
        self.assertEqual(S.mb_stoerungen(d, S.mb_einstellungen(d), "RG"), [])
        S.stand_schreiben({})


class Modulkette(unittest.TestCase):
    def test_keine_doppelten_namen(self):
        """jede Datei übernimmt alle Namen der vorherigen – gleiche öffentliche Namen würden frühere Funktionen überdecken"""
        import ast, re as rx
        ordner = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SparteNet_Manager", "spartenet")
        kette = rx.search(r"basis →(.*?)\n\n", open(os.path.join(ordner, "__init__.py"), encoding="utf-8").read(), rx.S).group(1)
        module = ["basis"] + [x.strip() for x in kette.replace("\n", " ").split("→") if x.strip()]
        erlaubt = {"_schluessel", "_sichtbar", "_zeile", "_holen", "_ereignis", "_hash"}   # nur modulintern benutzt
        gesehen, doppelt = {}, []
        for m in module:
            for n in ast.parse(open(os.path.join(ordner, m + ".py"), encoding="utf-8").read()).body:
                namen = [n.name] if isinstance(n, (ast.FunctionDef, ast.ClassDef)) else [x.id for x in n.targets if isinstance(x, ast.Name)] if isinstance(n, ast.Assign) else []
                for x in namen:
                    if x in gesehen and gesehen[x] != m and x not in erlaubt and x != "__all__":
                        doppelt.append(f"{x}: {gesehen[x]} / {m}")
                    gesehen.setdefault(x, m)
        self.assertEqual(doppelt, [])

    def test_oberflaeche_keine_doppelten_namen(self):
        """gleichnamige JS-Funktionen überschreiben sich still, doppelte IDs liefern das falsche Feld (z. B. App-Zugangstoken / Zuteilung)"""
        import re as rx
        from collections import Counter as C
        f = C(rx.findall(r"(?<![\w.])function\s+([A-Za-z_$][\w$]*)\s*\(", S.HTML))
        i = C(rx.findall(r'\sid="([^"$`{]+)"', S.HTML))
        g = C(rx.findall(r"^(?:let|const|var)\s+([A-Za-z_$][\w$]*)", S.HTML, rx.M))
        self.assertEqual({k: v for k, v in g.items() if v > 1}, {}, "globale JS-Variable doppelt")
        import shutil, subprocess, tempfile
        if shutil.which("node"):                     # vollständige Syntaxprüfung aller Skripte (doppelte let/const sind Syntaxfehler)
            for skript in rx.findall(r"<script>(.*?)</script>", S.HTML + S.MEIN_HTML + S.PORTAL_HTML + S.LOGIN_HTML, rx.S):
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as datei:
                    datei.write(skript)
                r = subprocess.run(["node", "--check", datei.name], capture_output=True, text=True)
                os.unlink(datei.name)
                self.assertEqual(r.returncode, 0, r.stderr[:800])
        self.assertEqual({k: v for k, v in f.items() if v > 1}, {})
        self.assertEqual({k: v for k, v in i.items() if v > 1}, {})

    def test_kartendesign_speichern(self):
        d = frisch()
        self.assertTrue(S.design_pruefen({**d["design"], "farbe_akzent": "#123456"})["farbe_akzent"] == "#123456")

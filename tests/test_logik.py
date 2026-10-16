"""Tests ohne Webserver: VLAN-Schema, Zuteilung nach Buchung, Umzugshilfe, TOTP, Prüfungen – mit nachgebautem Gateway"""
import os, sys, tempfile, unittest
from collections import Counter

_ORDNER = tempfile.mkdtemp(prefix="spartenet_logik_")
for k in [k for k in os.environ if k.startswith("SPARTENET_")]:
    del os.environ[k]
os.environ["SPARTENET_DATA_DIR"] = _ORDNER
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SparteNet_Manager"))

import spartenet.webserver as S   # noqa: E402  (lädt alle Module der Kette)
import spartenet.zuteilung as Z   # noqa: E402
import spartenet.umzug as U       # noqa: E402


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


if __name__ == "__main__":
    unittest.main()

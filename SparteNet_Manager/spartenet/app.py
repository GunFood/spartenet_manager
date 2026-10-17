"""SparteNet Manager – Zugang für Apps (z. B. eine eigene Android-App)

Die App meldet sich mit Benutzername, Passwort (und Zwei-Faktor-Code) an:  POST /api/v1/app/anmelden
und bekommt einen Geräte-Schlüssel „sna_<id>_<geheim>“ (nur als Prüfsumme gespeichert, unter „Mein Konto“ sperrbar).
Mit „Authorization: Bearer sna_…“ kann die App danach alle /api/…-Funktionen des Managers aufrufen – mit genau den Rechten
des Benutzerkontos (gleiche Prüfungen wie in der Oberfläche). Für die Startseite der App: GET /api/app-uebersicht.
Beschreibung aller Funktionen: GET /api/v1/app/funktionen (maschinenlesbar).
"""
from .portal import *  # noqa: F401,F403 – alle Namen der vorherigen Module

_APP_RE = re.compile(r"^sna_([0-9a-f]{10})_([A-Za-z0-9_-]{30,80})$")
APP_TAGE = max(1, int(os.environ.get("SPARTENET_APP_TAGE", "365") or 365))


def app_geraete(d):
    g = d.get("app_geraete")
    if not isinstance(g, dict):
        g = {}
        d["app_geraete"] = g
    return g


def _app_hash(geheim):
    return hashlib.sha256(("SparteNet-App|" + geheim).encode()).hexdigest()


def app_anmelden(d, b, quelle):
    name = str(b.get("benutzer") or "").strip().lower()
    konto = benutzer_anmelden(d, name, b.get("passwort"), quelle)
    if zweifaktor_aktiv(d, konto):
        if not str(b.get("code") or "").strip():
            return {"ok": False, "zweiter_faktor": True, "fehler": "Bitte den Code aus der Authenticator-App mitschicken (Feld „code“)."}
        if not zweifaktor_pruefen(d, konto, b.get("code")):
            _konto_sperre(konto, False)
            return {"ok": False, "zweiter_faktor": True, "fehler": "Der Code stimmt nicht."}
    g = app_geraete(d)
    if sum(1 for x in g.values() if x.get("benutzer") == konto) >= 20:
        raise Fehler("Höchstens 20 Geräte je Konto – unter „Mein Konto“ alte Geräte entfernen.")
    i, geheim = secrets.token_hex(5), secrets.token_urlsafe(32)
    g[i] = {"benutzer": konto, "name": text_einzeilig(b.get("geraet") or "App", 60), "hash": _app_hash(geheim), "angelegt": time.strftime("%Y-%m-%d %H:%M"),
            "zuletzt": "", "quelle": quelle, "ablauf": time.time() + APP_TAGE * 86400}
    speichere(d)
    journal(f"App angemeldet: {konto} ({g[i]['name']})")
    rechte = konto_rechte(d, konto)
    return {"ok": True, "token": f"sna_{i}_{geheim}", "gueltig_tage": APP_TAGE, "ich": ich_daten(konto, rechte), "version": VERSION,
            "hinweis": "Token sicher speichern (z. B. Android Keystore). Bei jeder Anfrage: Authorization: Bearer <token>."}


def app_token_pruefen(d, kopf):
    """(Kontoname, Rechte) für einen gültigen App-Schlüssel, sonst None"""
    roh = str(kopf or "")
    if not roh.lower().startswith("bearer sna_"):
        return None
    m = _APP_RE.match(roh[7:].strip())
    if not m:
        return None
    g = app_geraete(d).get(m.group(1))
    if not g or not hmac.compare_digest(g.get("hash", ""), _app_hash(m.group(2))) or g.get("gesperrt") or time.time() > float(g.get("ablauf") or 0):
        return None
    rechte = konto_rechte(d, g["benutzer"])
    if not rechte or rechte["art"] == "gesperrt":
        return None
    jetzt = time.strftime("%Y-%m-%d %H:%M")
    if g.get("zuletzt", "")[:15] != jetzt[:15]:      # höchstens alle 10 Minuten speichern
        with SCHREIB_SPERRE:
            d2 = lade()
            x = app_geraete(d2).get(m.group(1))
            if x:
                x["zuletzt"] = jetzt
                speichere(d2)
    return g["benutzer"], rechte


def akt_app_geraete(d, ich, alle=False):
    liste = [{"id": i, **{k: x.get(k) for k in ("benutzer", "name", "angelegt", "zuletzt", "gesperrt")},
              "ablauf": time.strftime("%Y-%m-%d", time.localtime(float(x.get("ablauf") or 0)))}
             for i, x in app_geraete(d).items() if alle or x.get("benutzer") == ich]
    liste.sort(key=lambda x: (x["benutzer"], x["angelegt"] or ""))
    return {"geraete": liste, "log": []}


def akt_app_geraet_entfernen(d, b, ich, admin=False):
    i = str(b.get("id") or "")
    x = app_geraete(d).get(i)
    if not x or (not admin and x.get("benutzer") != ich):
        raise Fehler("Gerät nicht gefunden.")
    del app_geraete(d)[i]
    speichere(d)
    journal(f"App-Gerät entfernt: {x.get('benutzer')} ({x.get('name')}) durch {ich}")
    r = akt_app_geraete(d, ich, admin)
    r["log"] = [f"✔ Gerät „{x.get('name')}“ entfernt – die App muss sich neu anmelden."]
    return r


def akt_app_uebersicht(d, ich, rechte):
    """Zahlen für den Startbildschirm der App (und die Startseite) – nur, was das Konto sehen darf"""
    b = rechte["bereiche"]
    adm = rechte["art"] == "admin"
    sieht = lambda k, s="lesen": adm or STUFE_RANG.get(b.get(k, "kein"), 0) >= STUFE_RANG[s]
    erl = sparten_von(rechte)
    aus = {"version": VERSION, "konto": ich, "zeit": time.strftime("%Y-%m-%d %H:%M")}
    if sieht("buchungen") or sieht("kalkulation"):
        buch = {k: v for k, v in (d.get("buchungen") or {}).items() if erl is None or k in erl}
        aus["buchungen"] = sum(1 for v in buch.values() for t in v.values() if t)
    if sieht("tickets"):
        t = [x for x in tickets_daten(d)["liste"].values() if x.get("status") != "erledigt" and (erl is None or x.get("sparte") in erl or x.get("zustaendig") == ich)]
        aus["tickets"] = {"offen": len(t), "neu": sum(1 for x in t if x.get("status") == "neu"), "meine": sum(1 for x in t if x.get("zustaendig") == ich),
                          "dringend": sum(1 for x in t if x.get("prioritaet") in ("dringend", "hoch"))}
    if sieht("mitglieder"):
        aus["mitglieder"] = sum(1 for m in mitglieder(d).values() if erl is None or m.get("sparte") in erl)
    if sieht("rechnungen"):
        r = [x for x in rechnungen_daten(d)["liste"].values() if x.get("status") in ("offen", "teilweise") and (erl is None or x.get("sparte") in erl)]
        aus["rechnungen"] = {"offen": len(r), "offen_betrag": round(sum(float(x["brutto"]) - float(x.get("bezahlt") or 0) for x in r), 2),
                             "ueberfaellig": sum(1 for x in r if x.get("faellig", "9999") < time.strftime("%Y-%m-%d"))}
    if sieht("auslesen") or sieht("start"):
        st = stand_lesen()
        aus["stoerungen"] = {"offline": [g.get("name") for g in (st.get("geraete") or {}).values() if g.get("offline_seit")],
                             "letzte_pruefung": time.strftime("%Y-%m-%d %H:%M", time.localtime(st["letzte_pruefung"])) if st.get("letzte_pruefung") else ""}
    return aus


def app_funktionen():
    """Liste der Funktionen mit nötigem Recht – für App-Entwickler"""
    aus = []
    for pfad, bereich in sorted({**_LESEN}.items()):
        aus.append({"pfad": pfad, "methode": "GET", "recht": f"{bereich}:lesen"})
    for pfad, bereich in sorted(_GET_LESEN_SONST_SCHREIBEN.items()):
        aus.append({"pfad": pfad, "methode": "GET", "recht": f"{bereich}:lesen"})
        aus.append({"pfad": pfad, "methode": "POST", "recht": f"{bereich}:schreiben"})
    for pfad, bereich in sorted(_VORSCHAU.items()):
        aus.append({"pfad": pfad, "methode": "POST", "recht": f"{bereich}:lesen (Vorschau) / schreiben (mit \"ausfuehren\": true)"})
    for pfad, bereich in sorted(_SCHREIBEN.items()):
        aus.append({"pfad": pfad, "methode": "POST", "recht": f"{bereich}:schreiben"})
    for pfad in sorted(_IMMER):
        aus.append({"pfad": pfad, "methode": "GET", "recht": "angemeldet"})
    aus.append({"pfad": "/api/app-uebersicht", "methode": "GET", "recht": "angemeldet"})
    return aus


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

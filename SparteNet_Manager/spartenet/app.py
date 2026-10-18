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


# ---- App-Zugangstoken: schützt die App-Schnittstelle zusätzlich (Header „X-App-Token“) --------------------------------
def _zt_hash(t):
    return hashlib.sha256(("SparteNet-App-Zugang|" + str(t or "")).encode()).hexdigest()


ZT_ALLE = "*"            # alter, gemeinsamer Token aus 5.3/5.4: gilt für alle Konten, bis der Administrator ihn entfernt


def app_zugangstokens(d):
    """{id: {hash, konto, name, erstellt, zuletzt, hinweis}} – jeder Benutzer kann beliebig viele eigene Tokens anlegen"""
    z = d.get("app_zugangstokens")
    if not isinstance(z, dict):
        z = {}
        d["app_zugangstokens"] = z
    alt = d.get("app_zugang")
    if isinstance(alt, dict) and alt.get("hash"):          # Übernahme des bisherigen gemeinsamen Tokens
        z["alt" + alt["hash"][:7]] = {"hash": alt["hash"], "konto": ZT_ALLE, "name": "Bisheriger gemeinsamer Token", "erstellt": alt.get("erstellt", ""),
                                   "von": alt.get("von", ""), "hinweis": alt.get("hinweis", ""), "zuletzt": ""}
    d.pop("app_zugang", None)
    return z


def zugangstoken_finden(d, token, konto=None):
    """Id des Zugangstokens, wenn er gültig ist (und – mit konto – zu diesem Konto gehört), sonst None"""
    if not token:
        return None
    h = _zt_hash(str(token).strip())
    for i, x in app_zugangstokens(d).items():
        if hmac.compare_digest(x.get("hash", ""), h):
            return i if konto is None or x.get("konto") in (konto, ZT_ALLE) else None
    return None


def _zt_zeile(i, x):
    return {"id": i, **{k: x.get(k, "") for k in ("konto", "name", "erstellt", "zuletzt", "hinweis")}, "alle": x.get("konto") == ZT_ALLE}


def akt_app_zugangstoken(d, b, ich, admin=False):
    """Eigene App-Zugangstokens anlegen ({"neu": true, "name": …} – wird nur einmal angezeigt), entfernen ({"entfernen": id}).
    Administrator sieht und entfernt die Tokens aller Konten ({"alle_sperren": true} entfernt alle)."""
    z = app_zugangstokens(d)
    extra, log = {}, []
    if b.get("neu"):
        if sum(1 for x in z.values() if x.get("konto") == ich) >= 500:
            raise Fehler("Sehr viele Zugangstokens – bitte alte entfernen.")
        t = "snz_" + secrets.token_urlsafe(24)
        i = secrets.token_hex(5)
        z[i] = {"hash": _zt_hash(t), "konto": ich, "name": text_einzeilig(b.get("name") or "App", 60) or "App", "erstellt": time.strftime("%Y-%m-%d %H:%M"),
                "von": ich, "hinweis": t[:8] + "…", "zuletzt": ""}
        speichere(d)
        journal(f"App-Zugangstoken „{z[i]['name']}“ angelegt für {ich}")
        extra = {"token": t, "neu_id": i}
        log = ["✔ Neuer Zugangstoken erzeugt. Jetzt kopieren und in der App eintragen – er wird nur einmal angezeigt."]
    elif b.get("entfernen"):
        x = z.get(str(b["entfernen"]))
        if not x or (x.get("konto") != ich and not admin):
            raise Fehler("Zugangstoken nicht gefunden.")
        z.pop(str(b["entfernen"]))
        speichere(d)
        journal(f"App-Zugangstoken „{x.get('name')}“ ({x.get('konto')}) entfernt durch {ich}")
        log = ["✔ Zugangstoken entfernt – Apps mit diesem Token können sich nicht mehr anmelden oder Daten abrufen."]
    elif b.get("alle_sperren"):
        if not admin:
            raise Fehler("Nur der Administrator kann alle Zugangstokens sperren.")
        n = len(z)
        z.clear()
        speichere(d)
        journal(f"Alle App-Zugangstokens ({n}) entfernt durch {ich}")
        log = [f"✔ Alle {n} Zugangstokens entfernt – keine App hat mehr Zugang, bis neue erzeugt sind."]
    elif "app_zugang" in d:
        speichere(d)                                         # Übernahme des alten Tokens sichern
    zeilen = [_zt_zeile(i, x) for i, x in z.items() if admin or x.get("konto") == ich]
    zeilen.sort(key=lambda x: (x["konto"] != ich, x["konto"], x["erstellt"]))
    return {"tokens": zeilen, "admin": admin, **extra, "log": log}


def app_anmelden(d, b, quelle, zugangstoken=None):
    if not zugangstoken_finden(d, zugangstoken):
        return {"ok": False, "zugangstoken": True, "fehler": "Zugangstoken fehlt oder ist falsch – im Manager unter Benutzer & Konto → Mein Konto → App-Zugangstokens erzeugen."}
    name = str(b.get("benutzer") or "").strip().lower()
    if not zugangstoken_finden(d, zugangstoken, name):
        return {"ok": False, "zugangstoken": True, "fehler": "Dieser Zugangstoken gehört zu einem anderen Benutzerkonto – bitte einen eigenen erzeugen."}
    konto = benutzer_anmelden(d, name, b.get("passwort"), quelle)
    merken = None
    if zweifaktor_aktiv(d, konto) and zweifaktor_gemerkt(d, konto, b.get("merken")):
        pass                       # Code auf diesem Gerät noch gemerkt
    elif zweifaktor_aktiv(d, konto):
        if not str(b.get("code") or "").strip():
            return {"ok": False, "zweiter_faktor": True, "fehler": "Bitte den Code aus der Authenticator-App mitschicken (Feld „code“)."}
        if not zweifaktor_pruefen(d, konto, b.get("code")):
            _konto_sperre(konto, False)
            return {"ok": False, "zweiter_faktor": True, "fehler": "Der Code stimmt nicht."}
        merken, _ = zweifaktor_merken(d, konto, b.get("geraet") or "App")
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
            "merken": merken, "merken_stunden": sicherheit(d)["2fa_merken_stunden"] if merken else 0,
            "abmelden_minuten": sicherheit(d)["app_abmelden_minuten"],
            "hinweis": "Token sicher speichern (z. B. Android Keystore). Bei jeder Anfrage: Authorization: Bearer <token>."}


def app_token_pruefen(d, kopf, zugangstoken=None):
    """(Kontoname, Rechte) für einen gültigen App-Schlüssel und Zugangstoken, sonst None"""
    roh = str(kopf or "")
    if not roh.lower().startswith("bearer sna_"):
        return None
    m = _APP_RE.match(roh[7:].strip())
    if not m:
        return None
    g = app_geraete(d).get(m.group(1))
    if not g or not hmac.compare_digest(g.get("hash", ""), _app_hash(m.group(2))) or g.get("gesperrt") or time.time() > float(g.get("ablauf") or 0):
        return None
    zt = zugangstoken_finden(d, zugangstoken, g["benutzer"])
    if not zt:
        return None
    rechte = konto_rechte(d, g["benutzer"])
    if not rechte or rechte["art"] == "gesperrt":
        return None
    jetzt = time.strftime("%Y-%m-%d %H:%M")
    if g.get("zuletzt", "")[:15] != jetzt[:15] or app_zugangstokens(d)[zt].get("zuletzt", "")[:15] != jetzt[:15]:      # höchstens alle 10 Minuten speichern
        with SCHREIB_SPERRE:
            d2 = lade()
            x = app_geraete(d2).get(m.group(1))
            if x:
                x["zuletzt"] = jetzt
            y = app_zugangstokens(d2).get(zt)
            if y:
                y["zuletzt"] = jetzt
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
        jetzt = time.time()
        lz = [e for e in laufzeiten(d).values() if isinstance(e, dict) and (erl is None or e.get("sparte") in erl)]
        if lz:
            gesp = zugang_gesperrt(d)
            aus["laufzeiten"] = {"aktiv": sum(1 for e in lz if e.get("status") == "aktiv"),
                                 "bald": sum(1 for e in lz if e.get("status") == "aktiv" and e["ende"] - jetzt < 86400),
                                 "abgelaufen": sum(1 for e in lz if e.get("status") in ("abgelaufen", "ausnahme")),
                                 "offen": sum(1 for e in lz if (e.get("status") == "abgelaufen") != (_k(e["sparte"], e["parzelle"]) in gesp))}
    if sieht("tickets"):
        t = [x for x in tickets_daten(d)["liste"].values() if ticket_offen(x) and (erl is None or x.get("sparte") in erl or x.get("zustaendig") == ich)]
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

"""SparteNet Manager – Rundschreiben: E-Mail mit Layout an Mitglieder, gefiltert nach Sparte, Tarif, gebucht

Jede E-Mail wird persönlich gefüllt ({vorname}, {parzelle}, {tarif} …). Versand im Hintergrund, eine nach der anderen,
mit Pause gegen Spam-Sperren beim Provider. Verlauf mit gesendet / fehlgeschlagen.
"""
from .vertraege import *  # noqa: F401,F403 – alle Namen der vorherigen Module

RS_STAND = {}          # laufende Rundschreiben: id → {"gesendet", "fehler", "gesamt", "fertig"}
RS_PAUSE = float(os.environ.get("SPARTENET_RUNDSCHREIBEN_PAUSE", "1.0") or 1.0)


def _rs_empfaenger(d, f, erlaubt=None):
    sparten = {str(x).upper() for x in (f.get("sparten") or []) if x}
    tarife = {str(x) for x in (f.get("tarife") or []) if x}
    nur = f.get("nur_gebucht", True)
    aus, ohne = [], 0
    for i, m in mitglieder(d).items():
        if erlaubt is not None and m.get("sparte") not in erlaubt:
            continue
        if sparten and m.get("sparte") not in sparten:
            continue
        tarif = ((d.get("buchungen") or {}).get(m.get("sparte")) or {}).get(str(m.get("parzelle")), "") if m.get("parzelle") else ""
        if (nur or tarife) and not tarif:
            continue
        if tarife and tarif not in tarife:
            continue
        if not m.get("email"):
            ohne += 1
            continue
        aus.append({"id": i, "email": m["email"], "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(), "sparte": m.get("sparte"),
                    "parzelle": m.get("parzelle"), "tarif": tarif})
    # jede Adresse nur einmal
    gesehen, eindeutig = set(), []
    for e in aus:
        if e["email"] not in gesehen:
            gesehen.add(e["email"]); eindeutig.append(e)
    return eindeutig, ohne


def akt_rundschreiben_empfaenger(d, b, erlaubt=None):
    liste, ohne = _rs_empfaenger(d, b.get("filter") or {}, erlaubt)
    return {"anzahl": len(liste), "ohne_email": ohne, "beispiele": liste[:30],
            "log": [f"{len(liste)} Empfänger" + (f" · {ohne} Mitglied(er) ohne E-Mail-Adresse werden übersprungen" if ohne else "")]}


def rundschreiben_liste(d):
    r = d.get("rundschreiben")
    return r if isinstance(r, list) else []


def akt_rundschreiben(d):
    liste = rundschreiben_liste(d)
    for r in liste:
        if r.get("id") in RS_STAND:
            r.update({k: RS_STAND[r["id"]][k] for k in ("gesendet", "fehler")}, status="läuft" if not RS_STAND[r["id"]]["fertig"] else r.get("status"))
    return {"liste": list(reversed(liste[-50:])), "log": []}


def _rs_inhalt(d, b):
    betreff, html = text_einzeilig(b.get("betreff") or "", 200), html_bereinigen(b.get("html") or "")
    if b.get("vorlage"):
        v = next((x for x in email_vorlagen(d) if x["id"] == b["vorlage"]), None)
        if not v:
            raise Fehler("Vorlage nicht gefunden.")
        betreff, html = betreff or v["betreff"], html or v["html"]
    if not betreff or not html_zu_text(html).strip():
        raise Fehler("Betreff und Text angeben.")
    return betreff, html


def _rs_werte(d, e):
    return _platzhalter_werte({"sparte": e.get("sparte"), "parzelle": e.get("parzelle"), "tarif": e.get("tarif"), "email": e["email"], "name": e.get("name")}, d)


def _versand(rid, betreff, html, liste):
    st = RS_STAND[rid]
    for e in liste:
        try:
            d = lade()
            w = _rs_werte(d, e)
            email_senden(d, e["email"], _ersetzen(betreff, w), None, _ersetzen(html, w, html=True), sparte=e.get("sparte") or None)
            st["gesendet"] += 1
        except Exception as f:
            st["fehler"] += 1
            st["fehlerliste"].append(f"{e['email']}: {text_einzeilig(str(f), 150)}")
            if isinstance(f, Fehler) and "nicht eingerichtet" in str(f):
                break
        time.sleep(RS_PAUSE)
    st["fertig"] = True
    with SCHREIB_SPERRE:
        d = lade()
        for r in rundschreiben_liste(d):
            if r["id"] == rid:
                r.update(gesendet=st["gesendet"], fehler=st["fehler"], fehlerliste=st["fehlerliste"][:50], status="fertig", ende=time.strftime("%Y-%m-%d %H:%M"))
        speichere(d)
    journal(f"Rundschreiben „{betreff[:60]}“: {st['gesendet']} gesendet, {st['fehler']} fehlgeschlagen")


def akt_rundschreiben_senden(d, b, ich, erlaubt=None):
    betreff, html = _rs_inhalt(d, b)
    liste, ohne = _rs_empfaenger(d, b.get("filter") or {}, erlaubt)
    if b.get("test_an"):
        bsp = liste[0] if liste else {"email": b["test_an"], "name": "Max Mustermann", "sparte": "", "parzelle": "", "tarif": ""}
        w = _rs_werte(d, bsp)
        email_senden(d, b["test_an"], "[Test] " + _ersetzen(betreff, w), None, _ersetzen(html, w, html=True))
        return {"log": [f"✔ Test an {b['test_an']} gesendet (mit den Daten von {bsp.get('name') or 'einem Beispiel'})."]}
    if not liste:
        raise Fehler("Keine Empfänger für diese Auswahl.")
    if len(liste) > 5000:
        raise Fehler("Höchstens 5000 Empfänger je Rundschreiben.")
    rid = secrets.token_hex(5)
    eintrag = {"id": rid, "zeit": time.strftime("%Y-%m-%d %H:%M"), "von": ich, "betreff": betreff, "gesamt": len(liste), "gesendet": 0, "fehler": 0,
               "filter": b.get("filter") or {}, "status": "läuft"}
    d["rundschreiben"] = (rundschreiben_liste(d) + [eintrag])[-200:]
    speichere(d)
    RS_STAND[rid] = {"gesendet": 0, "fehler": 0, "gesamt": len(liste), "fertig": False, "fehlerliste": []}
    threading.Thread(target=_versand, args=(rid, betreff, html, liste), daemon=True, name=f"rundschreiben-{rid}").start()
    journal(f"Rundschreiben gestartet: „{betreff[:60]}“ an {len(liste)} Empfänger durch {ich}")
    r = akt_rundschreiben(d)
    r["log"] = [f"✔ Rundschreiben an {len(liste)} Empfänger gestartet – läuft im Hintergrund (etwa {round(len(liste) * RS_PAUSE / 60) or 1} Min.)."]
    return r


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

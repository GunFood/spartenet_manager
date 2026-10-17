"""SparteNet Manager – Datenschutz: Auskunft über alle gespeicherten Daten eines Mitglieds und Löschung auf Knopfdruck

Auskunft (Art. 15 DSGVO): eine JSON-Datei mit Mitglied, Buchung, Vertrag, Rechnungen, Tickets.
Löschung (Art. 17 DSGVO): Mitglied entfernen, Tickets anonymisieren, Vertrag ohne Personenbezug. Rechnungen bleiben wegen der
gesetzlichen Aufbewahrungspflicht (bis zu 10 Jahre) erhalten, werden aber gesperrt markiert und ohne E-Mail-Adresse geführt.
"""
from .rundschreiben import *  # noqa: F401,F403 – alle Namen der vorherigen Module


def _bezug(d, m):
    em = (m.get("email") or "").lower()
    kz, p = m.get("sparte"), str(m.get("parzelle") or "")
    tickets = {i: t for i, t in tickets_daten(d)["liste"].items()
               if (em and (t.get("kontakt") or {}).get("email", "").lower() == em) or (t.get("kontakt") or {}).get("mitglied") == m.get("_id")}
    rechn = {i: x for i, x in rechnungen_daten(d)["liste"].items() if x.get("mitglied") == m.get("_id") or (em and (x.get("email") or "").lower() == em)}
    vertrag = vertraege(d).get(f"{kz}-{p}") if kz and p else None
    return tickets, rechn, vertrag


def akt_mitglied_auskunft(d, q, ich, erlaubt=None):
    mid = q.get("id", [""])[0]
    m = mitglieder(d).get(mid)
    if not m or (erlaubt is not None and m.get("sparte") not in erlaubt):
        raise Fehler("Mitglied nicht gefunden.")
    tickets, rechn, vertrag = _bezug(d, {**m, "_id": mid})
    kz, p = m.get("sparte"), str(m.get("parzelle") or "")
    aus = {"erstellt": time.strftime("%Y-%m-%d %H:%M"), "hinweis": "Auskunft über die beim Betreiber des SparteNet-WLANs gespeicherten Daten.",
           "mitglied": {k: m.get(k) for k in M_FELDER + ("angelegt", "geaendert", "quelle")},
           "buchung": {"sparte": kz, "parzelle": p, "tarif": ((d.get("buchungen") or {}).get(kz) or {}).get(p, "")} if kz and p else None,
           "vertrag": vertrag, "rechnungen": [{k: x.get(k) for k in ("nr", "datum", "faellig", "brutto", "bezahlt", "status", "tarif", "zahlungen")} for x in rechn.values()],
           "tickets": [{k: t.get(k) for k in ("nr", "betreff", "text", "status", "erstellt", "geaendert")} | {"verlauf": [v for v in t.get("verlauf") or [] if v["art"] == "antwort"]}
                       for t in tickets.values()],
           "wlan": {"netz": NETZ_PARZELLE.format(kz=kz, p=int(p)) if kz and p.isdigit() else "", "hinweis": "Das WLAN-Passwort der Parzelle ist gespeichert, wird hier aber nicht ausgegeben."}}
    journal(f"Datenschutz-Auskunft erstellt: {kz or '–'} Parzelle {p or '–'} durch {ich}")
    return {"_datei": json.dumps(aus, ensure_ascii=False, indent=2).encode("utf-8"), "typ": "application/json",
            "name": f"Auskunft_{(m.get('nachname') or 'Mitglied').replace(' ', '_')}_{time.strftime('%Y%m%d')}.json"}


def akt_mitglied_dsgvo_loeschen(d, b, ich, erlaubt=None):
    mid = str(b.get("id") or "")
    m = mitglieder(d).get(mid)
    if not m or (erlaubt is not None and m.get("sparte") not in erlaubt):
        raise Fehler("Mitglied nicht gefunden.")
    tickets, rechn, vertrag = _bezug(d, {**m, "_id": mid})
    em = (m.get("email") or "").lower()
    for t in tickets.values():
        t["kontakt"] = {"name": "(gelöscht)"}
        t["text"] = "(Inhalt aus Datenschutzgründen gelöscht)"
        for v in t.get("verlauf") or []:
            if v["art"] in ("antwort", "kommentar"):
                v["text"] = "(gelöscht)"
        _verlauf(t, ich, "aenderung", "Personenbezogene Daten gelöscht (Datenschutz)")
    for x in rechn.values():
        x["email"] = ""
        x["gesperrt"] = True          # Aufbewahrungspflicht: nur noch Buchhaltung, kein Versand
    if vertrag:
        vertrag.pop("notiz", None)
    del mitglieder(d)[mid]
    speichere(d)
    journal(f"Datenschutz-Löschung: Mitglied {m.get('sparte') or '–'} Parzelle {m.get('parzelle') or '–'} gelöscht, {len(tickets)} Ticket(s) anonymisiert, "
            f"{len(rechn)} Rechnung(en) gesperrt aufbewahrt – durch {ich}")
    r = akt_mitglieder(d, erlaubt)
    r["log"] = [f"✔ Mitglied gelöscht · {len(tickets)} Ticket(s) anonymisiert · {len(rechn)} Rechnung(en) bleiben wegen der Aufbewahrungspflicht gesperrt erhalten (ohne E-Mail)."]
    return r


def personen_verdecken(obj):
    """E-Mail-Adressen in Texten unkenntlich machen (für Konten ohne Recht „Mitglieder“)"""
    if isinstance(obj, str):
        return re.sub(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", r"\1…@\2", obj)
    if isinstance(obj, list):
        return [personen_verdecken(x) for x in obj]
    if isinstance(obj, dict):
        return {k: personen_verdecken(v) for k, v in obj.items()}
    return obj


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

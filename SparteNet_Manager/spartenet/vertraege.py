"""SparteNet Manager – Verträge je Buchung: Beginn, Laufzeit, Verlängerung, Kündigungsfrist, Kündigung, Erinnerung

Bei einer neuen Buchung entsteht der Vertrag automatisch (Beginn = heute, Werte aus den Einstellungen).
Täglich prüft der Zeitplan: Erinnerung vor Ablauf der Kündigungsfrist (Ereignis „vertrag_erinnerung“) und Vertragsende nach
Kündigung (Ereignis „vertrag_ende“, auf Wunsch wird die Buchung im Manager entfernt – am Gateway ändert sich nichts).
"""
import datetime as _dt

from .rechnungen import *  # noqa: F401,F403 – alle Namen der vorherigen Module

V_STANDARD = {"laufzeit": 12, "verlaengerung": 12, "frist": 1, "erinnerung_tage": 30, "auto_entfernen": False}


def vertrag_einstellungen(d):
    e = dict(V_STANDARD)
    roh = d.get("vertrag_einstellungen") if isinstance(d.get("vertrag_einstellungen"), dict) else {}
    for k, std in V_STANDARD.items():
        if k in roh:
            e[k] = bool(roh[k]) if isinstance(std, bool) else int(roh[k])
    return e


def vertraege(d):
    v = d.get("vertraege")
    if not isinstance(v, dict):
        v = {}
        d["vertraege"] = v
    return v


def plus_monate(datum, n):
    j, m = divmod(datum.month - 1 + int(n), 12)
    jahr, monat = datum.year + j, m + 1
    tage = [31, 29 if jahr % 4 == 0 and (jahr % 100 or jahr % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][monat - 1]
    return _dt.date(jahr, monat, min(datum.day, tage))


def _d(t):
    try:
        return _dt.date.fromisoformat(str(t)[:10])
    except ValueError:
        return None


def vertrag_lage(v, heute=None):
    """(Ende der laufenden Periode, kündbar bis, Status)"""
    heute = heute or _dt.date.today()
    beginn = _d(v.get("beginn")) or heute
    if v.get("ende_zum"):
        ende = _d(v["ende_zum"])
        return ende, None, "beendet" if ende and ende < heute else "gekündigt"
    ende = plus_monate(beginn, v.get("laufzeit") or 12) - _dt.timedelta(days=1)
    while ende < heute and int(v.get("verlaengerung") or 0) > 0:
        ende = plus_monate(ende + _dt.timedelta(days=1), v["verlaengerung"]) - _dt.timedelta(days=1)
    kuendbar = plus_monate(ende + _dt.timedelta(days=1), -int(v.get("frist") or 0)) - _dt.timedelta(days=1)
    if ende < heute:
        return ende, kuendbar, "abgelaufen"
    return ende, kuendbar, "laufend"


def vertrag_anlegen(d, kz, p, beginn=None):
    k = f"{kz}-{int(p)}"
    v = vertraege(d)
    if k in v and not v[k].get("ende_zum"):
        return v[k]
    e = vertrag_einstellungen(d)
    v[k] = {"sparte": kz, "parzelle": int(p), "beginn": beginn or _dt.date.today().isoformat(), "laufzeit": e["laufzeit"],
            "verlaengerung": e["verlaengerung"], "frist": e["frist"], "erinnert": [], "angelegt": time.strftime("%Y-%m-%d %H:%M")}
    return v[k]


def _ereignis(typ, daten, d):
    if typ == "buchung" and d is not None and daten.get("sparte") and str(daten.get("parzelle") or "").isdigit():
        k = f"{daten['sparte']}-{int(daten['parzelle'])}"
        alt = vertraege(d).get(k)
        if not alt or alt.get("ende_zum"):
            if alt:
                vertraege(d).pop(k)
            vertrag_anlegen(d, daten["sparte"], daten["parzelle"])
            speichere(d)
    elif typ == "kuendigung" and d is not None and str(daten.get("parzelle") or "").isdigit():
        v = vertraege(d).get(f"{daten.get('sparte')}-{int(daten['parzelle'])}")
        if v and not v.get("ende_zum"):
            v["ende_zum"] = _dt.date.today().isoformat()
            v["gekuendigt"] = v.get("gekuendigt") or _dt.date.today().isoformat()
            speichere(d)


EREIGNIS_EMPFAENGER.insert(0, _ereignis)


def _daten(d, k, v):
    ende, kuendbar, status = vertrag_lage(v)
    mid, m = _mitglied_der_parzelle(d, v["sparte"], v["parzelle"])
    return {"sparte": v["sparte"], "parzelle": v["parzelle"], "vertrag_beginn": _de(v.get("beginn")), "vertrag_ende": _de(ende.isoformat()) if ende else "",
            "kuendbar_bis": _de(kuendbar.isoformat()) if kuendbar else "", "email": (m or {}).get("email", ""),
            "name": f"{(m or {}).get('vorname', '')} {(m or {}).get('nachname', '')}".strip(),
            "tarif": ((d.get("buchungen") or {}).get(v["sparte"]) or {}).get(str(v["parzelle"]), "")}


def akt_vertraege(d, erlaubt=None):
    e = vertrag_einstellungen(d)
    buch = d.get("buchungen") or {}
    geaendert = False
    for kz, b in buch.items():           # gebuchte Parzellen ohne Vertrag (z. B. aus der Zeit vor 5.0) bekommen einen
        for p, t in b.items():
            if t and str(p).isdigit() and f"{kz}-{int(p)}" not in vertraege(d):
                vertrag_anlegen(d, kz, p)
                geaendert = True
    if geaendert:
        speichere(d)
    zeilen = []
    heute = _dt.date.today()
    for k, v in vertraege(d).items():
        if erlaubt is not None and v.get("sparte") not in erlaubt:
            continue
        ende, kuendbar, status = vertrag_lage(v, heute)
        if status == "laufend" and kuendbar and (kuendbar - heute).days <= e["erinnerung_tage"]:
            status = "Frist läuft ab"
        x = _daten(d, k, v)
        zeilen.append({"id": k, **x, "status": status, "laufzeit": v.get("laufzeit"), "verlaengerung": v.get("verlaengerung"), "frist": v.get("frist"),
                       "beginn": v.get("beginn"), "gekuendigt": _de(v["gekuendigt"]) if v.get("gekuendigt") else "", "notiz": v.get("notiz", ""),
                       "tage_bis_ende": (ende - heute).days if ende else None})
    zeilen.sort(key=lambda z: (z["status"] in ("beendet",), z["sparte"], z["parzelle"]))
    return {"zeilen": zeilen, "einstellungen": e,
            "log": [f"{sum(1 for z in zeilen if z['status'] != 'beendet')} laufende Verträge · {sum(1 for z in zeilen if z['status'] == 'gekündigt')} gekündigt · "
                    f"{sum(1 for z in zeilen if z['status'] == 'Frist läuft ab')} mit bald ablaufender Kündigungsfrist"]}


def _holen_v(d, k, erlaubt):
    v = vertraege(d).get(str(k or ""))
    if not v or (erlaubt is not None and v.get("sparte") not in erlaubt):
        raise Fehler("Vertrag nicht gefunden.")
    return v


def akt_vertrag_speichern(d, b, ich, erlaubt=None):
    v = _holen_v(d, b.get("id"), erlaubt)
    if "beginn" in b:
        if not _d(b["beginn"]):
            raise Fehler("Beginn als Datum angeben.")
        v["beginn"] = _d(b["beginn"]).isoformat()
    for k, (lo, hi) in {"laufzeit": (1, 120), "verlaengerung": (0, 120), "frist": (0, 24)}.items():
        if k in b:
            try:
                v[k] = max(lo, min(hi, int(b[k])))
            except (TypeError, ValueError):
                raise Fehler("Laufzeit, Verlängerung und Frist in Monaten angeben.")
    if "notiz" in b:
        v["notiz"] = text_einzeilig(b["notiz"], 300)
    speichere(d)
    journal(f"Vertrag {v['sparte']} Parzelle {v['parzelle']} geändert durch {ich}")
    r = akt_vertraege(d, erlaubt)
    r["log"] = ["✔ Vertrag gespeichert."]
    return r


def akt_vertrag_kuendigen(d, b, ich, erlaubt=None):
    v = _holen_v(d, b.get("id"), erlaubt)
    if b.get("zuruecknehmen"):
        if not v.get("ende_zum") or _d(v["ende_zum"]) < _dt.date.today():
            raise Fehler("Diese Kündigung lässt sich nicht mehr zurücknehmen.")
        v.pop("ende_zum", None); v.pop("gekuendigt", None)
        text = "Kündigung zurückgenommen"
    else:
        if v.get("ende_zum"):
            raise Fehler("Der Vertrag ist schon gekündigt.")
        heute = _dt.date.today()
        ende, kuendbar, _ = vertrag_lage(v, heute)
        if b.get("zum"):
            z = _d(b["zum"])
            if not z or z < heute:
                raise Fehler("Kündigungsdatum in der Zukunft angeben.")
            ende = z
        elif kuendbar and heute > kuendbar:     # Frist verpasst → zum Ende der nächsten Periode
            ende = plus_monate(ende + _dt.timedelta(days=1), int(v.get("verlaengerung") or v.get("laufzeit") or 12)) - _dt.timedelta(days=1)
        v["ende_zum"], v["gekuendigt"] = ende.isoformat(), heute.isoformat()
        text = f"gekündigt zum {_de(ende.isoformat())}"
        ereignis("vertrag_gekuendigt", _daten(d, b.get("id"), v), d)
    speichere(d)
    journal(f"Vertrag {v['sparte']} Parzelle {v['parzelle']}: {text} durch {ich}")
    r = akt_vertraege(d, erlaubt)
    r["log"] = [f"✔ {v['sparte']} Parzelle {v['parzelle']}: {text}."]
    return r


def akt_vertrag_einstellungen(d, b, ich):
    e = vertrag_einstellungen(d)
    for k, std in V_STANDARD.items():
        if k in b:
            try:
                e[k] = bool(b[k]) if isinstance(std, bool) else max(0, min(365 if k == "erinnerung_tage" else 120, int(b[k])))
            except (TypeError, ValueError):
                raise Fehler("Zahlen angeben.")
    e["laufzeit"] = max(1, e["laufzeit"])
    d["vertrag_einstellungen"] = e
    speichere(d)
    journal(f"Vertrags-Einstellungen gespeichert durch {ich}")
    r = akt_vertraege(d)
    r["log"] = ["✔ Gespeichert – gilt für neue Verträge."]
    return r


def vertraege_pruefen(d):
    """täglich: Erinnerungen vor Fristablauf, Vertragsende nach Kündigung"""
    e = vertrag_einstellungen(d)
    heute = _dt.date.today()
    log, aenderung = [], False
    for k, v in list(vertraege(d).items()):
        ende, kuendbar, status = vertrag_lage(v, heute)
        if status == "laufend" and kuendbar and 0 <= (kuendbar - heute).days <= e["erinnerung_tage"] and kuendbar.isoformat() not in (v.get("erinnert") or []):
            v.setdefault("erinnert", []).append(kuendbar.isoformat())
            v["erinnert"] = v["erinnert"][-5:]
            aenderung = True
            ereignis("vertrag_erinnerung", _daten(d, k, v), d)
            log.append(f"Erinnerung {k}")
        if v.get("ende_zum") and ende and ende < heute and not v.get("ende_gemeldet"):
            v["ende_gemeldet"] = heute.isoformat()
            aenderung = True
            ereignis("vertrag_ende", _daten(d, k, v), d)
            if e["auto_entfernen"] and ((d.get("buchungen") or {}).get(v["sparte"]) or {}).get(str(v["parzelle"])):
                akt_buchungen_speichern(d, v["sparte"], {str(v["parzelle"]): ""})
                journal(f"Vertragsende {k}: Buchung im Manager entfernt (am Gateway über „Netze nach Buchungen“/„Tarife“ übertragen)")
            log.append(f"Ende {k}")
    if aenderung:
        speichere(d)
    return log


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

"""SparteNet Manager – Einstellungen laden und speichern"""
from .speicher import *  # noqa: F401,F403 – alle Namen der vorherigen Module


# =============================================================== Einstellungen (JSON)
def lade():
    if DB:
        stand = {k: v for k, v in DB.sql("SELECT schluessel, wert FROM sn_daten", alle=True)}
        d = Daten()
        for k, v in stand.items():
            try:
                d[k] = json.loads(v)
            except ValueError:
                LOG.error("Datenbank: Wert „%s“ ist kein gültiges JSON – übersprungen", k)
        d._stand = stand
    else:
        try:
            with open(DATEI, encoding="utf-8") as f:
                d = Daten(json.load(f))
        except (OSError, ValueError):
            d = Daten()
    d.setdefault("cloud_key", ""); d.setdefault("konsole_id", ""); d.setdefault("konsole_name", "")
    d.setdefault("plan", copy.deepcopy(STANDARD_PLAN))
    d.setdefault("log_aktiv", False)
    d.setdefault("tarife", copy.deepcopy(TARIFE_STANDARD)); d.setdefault("tarif_modus", "tarif"); d.setdefault("tarif_zuordnung", {})
    d["design"] = design_pruefen(d.get("design"))
    return d


def speichere(d):
    if DB:
        neu = {k: json.dumps(v, ensure_ascii=False) for k, v in d.items()}
        alt = getattr(d, "_stand", None) or {}
        geaendert = [(k, v) for k, v in neu.items() if alt.get(k) != v]
        if geaendert:
            DB.sql("INSERT INTO sn_daten (schluessel, wert) VALUES (%s, %s) ON DUPLICATE KEY UPDATE wert = VALUES(wert)", geaendert, viele=True)
        for k in alt:
            if k not in neu:
                DB.sql("DELETE FROM sn_daten WHERE schluessel = %s", (k,))
        if isinstance(d, Daten):
            d._stand = neu
        return
    datei_atomar(DATEI, json.dumps(d, ensure_ascii=False, indent=2).encode("utf-8"))


# =============================================================== Tarife (Bandbreite per QoS-Regel, Netzgröße per Subnetz/DHCP)
TARIFE_STANDARD = [
    {"name": "Basic", "down": 30, "up": 10, "praefix": 29, "geraete": 5, "preis": 120},
    {"name": "Plus", "down": 60, "up": 20, "praefix": 28, "geraete": 10, "preis": 180},
    {"name": "Max", "down": 100, "up": 40, "praefix": 24, "geraete": 0, "preis": 240},
]

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

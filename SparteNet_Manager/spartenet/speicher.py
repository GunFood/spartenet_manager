"""SparteNet Manager – Datenspeicher: Dateien im Datenordner oder MariaDB/MySQL, Änderungsprotokoll, Kartenlogo"""
from .basis import *  # noqa: F401,F403 – alle Namen der vorherigen Module


def logo_daten_uri(design):
    if not design.get("logo"):
        return ""
    roh = ablage_lesen(design["logo"])
    if not roh:
        return ""
    return f"data:{LOGO_TYPEN[design['logo'].rsplit('.', 1)[1]]};base64," + base64.b64encode(roh).decode()


def logo_speichern(roh):
    if not roh:
        raise Fehler("Keine Datei empfangen.")
    if len(roh) > 2_000_000:
        raise Fehler("Logo zu groß (max. 2 MB). Bitte verkleinern.")
    kopf = roh[:1024].lstrip()
    if roh.startswith(b"\x89PNG"):
        ext = "png"
    elif roh.startswith(b"\xff\xd8"):
        ext = "jpg"
    elif roh[:6] in (b"GIF87a", b"GIF89a"):
        ext = "gif"
    elif roh[:4] == b"RIFF" and roh[8:12] == b"WEBP":
        ext = "webp"
    elif b"<svg" in kopf.lower():
        ext = "svg"
    else:
        raise Fehler("Unbekanntes Bildformat – bitte PNG, JPG, GIF, WEBP oder SVG verwenden.")
    logo_entfernen()
    name = os.path.basename(LOGO_BASIS) + "." + ext
    ablage_schreiben(name, roh)
    return name


def logo_entfernen():
    for e in LOGO_TYPEN:
        ablage_loeschen(os.path.basename(LOGO_BASIS) + "." + e)


# =============================================================== Datenspeicher: Dateien im Datenordner oder MariaDB/MySQL
# Mit SPARTENET_DB_HOST speichert der Manager alles in der Datenbank (Einstellungen, Planung, Buchungen, Passwörter je Parzelle,
# Sicherungen, Änderungsprotokoll, Passwort-Register, Kartenlogo). Ohne: wie bisher Dateien im Datenordner.
DB_HOST = os.environ.get("SPARTENET_DB_HOST", "").strip()
DB_PORT = int(os.environ.get("SPARTENET_DB_PORT", "3306") or 3306)
DB_NAME = os.environ.get("SPARTENET_DB_NAME", "spartenet").strip() or "spartenet"
DB_USER = os.environ.get("SPARTENET_DB_USER", "spartenet").strip() or "spartenet"
DB_SSL = os.environ.get("SPARTENET_DB_SSL", "0").strip().lower() in ("1", "ja", "true", "yes")
DB_SSL_CA = os.environ.get("SPARTENET_DB_SSL_CA", "").strip()
DB_PASSWORD_FILE = os.environ.get("SPARTENET_DB_PASSWORD_FILE", "").strip()
if DB_PASSWORD_FILE:
    try:
        with open(DB_PASSWORD_FILE, encoding="utf-8") as f:
            DB_PASSWORD = f.read().rstrip("\r\n")
    except OSError as e:
        raise SystemExit(f"SPARTENET_DB_PASSWORD_FILE kann nicht gelesen werden: {e}")
else:
    DB_PASSWORD = os.environ.get("SPARTENET_DB_PASSWORD", "")
DB_TABELLEN = [
    """CREATE TABLE IF NOT EXISTS sn_daten (
        schluessel VARCHAR(100) NOT NULL PRIMARY KEY,
        wert LONGTEXT NOT NULL,
        geaendert TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS sn_dateien (
        name VARCHAR(190) NOT NULL PRIMARY KEY,
        inhalt LONGBLOB NOT NULL,
        geaendert TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS sn_journal (
        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        zeit DATETIME NOT NULL,
        text TEXT NOT NULL,
        KEY zeit (zeit)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS sn_passwort_register (
        pruefsumme CHAR(64) NOT NULL PRIMARY KEY,
        angelegt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=ascii""",
    """CREATE TABLE IF NOT EXISTS sn_meta (
        schluessel VARCHAR(100) NOT NULL PRIMARY KEY,
        wert TEXT NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
]
DB_SCHEMA = "1"


class Datenbank:
    """eine Verbindung je Thread, bei Abbruch einmal neu verbinden"""

    def __init__(self):
        self._lokal = threading.local()
        try:
            import pymysql
        except ImportError:
            raise SystemExit("SPARTENET_DB_HOST ist gesetzt, aber das Paket PyMySQL fehlt: pip install PyMySQL (im Docker-Image enthalten).")
        self.pymysql = pymysql

    def _verbinden(self):
        ssl_opt = None
        if DB_SSL:
            ctx = ssl.create_default_context(cafile=DB_SSL_CA or None)
            ssl_opt = ctx
        return self.pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, charset="utf8mb4",
                                    autocommit=True, connect_timeout=10, read_timeout=60, write_timeout=60, ssl=ssl_opt)

    def _verbindung(self):
        c = getattr(self._lokal, "c", None)
        if c is None:
            c = self._lokal.c = self._verbinden()
        return c

    def sql(self, befehl, werte=None, viele=False, alle=False):
        for versuch in (1, 2):
            try:
                with self._verbindung().cursor() as k:
                    if viele:
                        k.executemany(befehl, werte)
                    else:
                        k.execute(befehl, werte)
                    return k.fetchall() if alle else k.rowcount
            except (self.pymysql.err.OperationalError, self.pymysql.err.InterfaceError) as e:
                try:
                    self._lokal.c.close()
                except Exception:
                    pass
                self._lokal.c = None
                if versuch == 2:
                    LOG.error("Datenbank nicht erreichbar: %s", e)
                    raise Fehler(f"Datenbank {DB_HOST}:{DB_PORT}/{DB_NAME} nicht erreichbar ({e.args[0] if e.args else e}).")

    def einrichten(self):
        for t in DB_TABELLEN:
            self.sql(t)
        self.sql("INSERT INTO sn_meta (schluessel, wert) VALUES ('schema', %s) ON DUPLICATE KEY UPDATE wert = VALUES(wert)", (DB_SCHEMA,))


DB = Datenbank() if DB_HOST else None


class Daten(dict):
    """Einstellungen; merkt sich den geladenen Stand je Schlüssel, damit nur Geändertes in die Datenbank geht"""
    _stand = None


def speicher_text():
    return f"MariaDB/MySQL {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}" if DB else f"Dateien im Ordner {HIER}"


def ablage_lesen(name):
    """Datei aus dem Datenspeicher (bytes) oder None"""
    if DB:
        r = DB.sql("SELECT inhalt FROM sn_dateien WHERE name = %s", (name,), alle=True)
        return bytes(r[0][0]) if r else None
    try:
        with open(os.path.join(HIER, name), "rb") as f:
            return f.read()
    except OSError:
        return None


def ablage_schreiben(name, roh):
    if isinstance(roh, str):
        roh = roh.encode("utf-8")
    if DB:
        DB.sql("INSERT INTO sn_dateien (name, inhalt) VALUES (%s, %s) ON DUPLICATE KEY UPDATE inhalt = VALUES(inhalt)", (name, roh))
        return
    pfad = os.path.join(HIER, name)
    with open(pfad, "wb") as f:
        f.write(roh)
    try:
        os.chmod(pfad, 0o600)
    except OSError:
        pass


def ablage_liste(praefix, endung=""):
    if DB:
        namen = [r[0] for r in DB.sql("SELECT name FROM sn_dateien WHERE LEFT(name, %s) = %s", (len(praefix), praefix), alle=True)]
    else:
        namen = [x for x in os.listdir(HIER) if x.startswith(praefix) and os.path.isfile(os.path.join(HIER, x))]
    return sorted(x for x in namen if x.startswith(praefix) and x.endswith(endung))


def ablage_loeschen(name):
    if DB:
        DB.sql("DELETE FROM sn_dateien WHERE name = %s", (name,))
        return
    try:
        os.remove(os.path.join(HIER, name))
    except OSError:
        pass


def ablage_umbenennen(alt, neu):
    if DB:
        DB.sql("DELETE FROM sn_dateien WHERE name = %s", (neu,))
        DB.sql("UPDATE sn_dateien SET name = %s WHERE name = %s", (neu, alt))
        return
    os.replace(os.path.join(HIER, alt), os.path.join(HIER, neu))


def datenbank_starten():
    """Tabellen anlegen; beim ersten Start vorhandene Dateien aus dem Datenordner übernehmen"""
    if not DB:
        return
    try:
        DB.einrichten()
    except Fehler as e:
        raise SystemExit(str(e))
    except Exception as e:
        raise SystemExit(f"Datenbank {DB_HOST}:{DB_PORT}/{DB_NAME}: {e}")
    leer = not DB.sql("SELECT COUNT(*) FROM sn_daten", alle=True)[0][0]
    dateien = sorted(x for x in os.listdir(HIER) if os.path.isfile(os.path.join(HIER, x)) and (
        x == os.path.basename(DATEI) or x in (os.path.basename(JOURNAL), os.path.basename(REGISTER))
        or x.startswith(("PPSK_", "SparteNet_Sicherung_", os.path.basename(LOGO_BASIS) + "."))))
    if not dateien:
        return
    if not leer:
        LOG.warning("Datenbank enthält schon Daten – Dateien im Datenordner werden nicht übernommen: %s", ", ".join(dateien))
        print("Hinweis: Datenbank enthält schon Daten – alte Dateien im Datenordner werden ignoriert.")
        return
    n = {"daten": 0, "journal": 0, "register": 0, "dateien": 0}
    for x in dateien:
        pfad = os.path.join(HIER, x)
        if x == os.path.basename(DATEI):
            with open(pfad, encoding="utf-8") as f:
                alt = json.load(f)
            DB.sql("INSERT INTO sn_daten (schluessel, wert) VALUES (%s, %s) ON DUPLICATE KEY UPDATE wert = VALUES(wert)",
                   [(k, json.dumps(v, ensure_ascii=False)) for k, v in alt.items()], viele=True)
            n["daten"] = len(alt)
        elif x == os.path.basename(JOURNAL):
            zeilen = []
            with open(pfad, encoding="utf-8", errors="replace") as f:
                for z in f:
                    m = re.match(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \| (.*)$", z.rstrip("\n"))
                    if m:
                        zeilen.append((m.group(1), m.group(2)))
            if zeilen:
                DB.sql("INSERT INTO sn_journal (zeit, text) VALUES (%s, %s)", zeilen, viele=True)
            n["journal"] = len(zeilen)
        elif x == os.path.basename(REGISTER):
            with open(pfad, encoding="utf-8") as f:
                h = sorted({z.strip() for z in f if re.fullmatch(r"[0-9a-f]{64}", z.strip())})
            if h:
                DB.sql("INSERT IGNORE INTO sn_passwort_register (pruefsumme) VALUES (%s)", [(x,) for x in h], viele=True)
            n["register"] = len(h)
        else:
            with open(pfad, "rb") as f:
                ablage_schreiben(x, f.read())
            n["dateien"] += 1
    ziel = os.path.join(HIER, "in_Datenbank_uebernommen_" + time.strftime("%Y%m%d_%H%M%S"))
    os.makedirs(ziel, exist_ok=True)
    for x in dateien:
        try:
            os.replace(os.path.join(HIER, x), os.path.join(ziel, x))
        except OSError:
            pass
    text = (f"In die Datenbank übernommen: {n['daten']} Einstellungsbereiche, {n['journal']} Protokollzeilen, {n['register']} Register-Einträge, "
            f"{n['dateien']} Dateien (Passwörter je Parzelle, Sicherungen, Logo). Die alten Dateien liegen in {ziel}.")
    print(text)
    LOG.info(text)
    journal(text)


JOURNAL = os.path.join(HIER, "SparteNet_Aenderungen.log")


ANFRAGE = threading.local()  # wer die laufende Anfrage stellt (setzt der Webserver) – fürs Änderungsprotokoll


def journal(text):
    """Änderungsprotokoll – immer an, ohne Passwörter"""
    wer = getattr(ANFRAGE, "benutzer", None)
    if wer and " durch " not in text:
        text = f"{text} · {wer}"
    try:
        if DB:
            DB.sql("INSERT INTO sn_journal (zeit, text) VALUES (%s, %s)", (time.strftime("%Y-%m-%d %H:%M:%S"), text))
        else:
            with open(JOURNAL, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {text}\n")
    except (OSError, Fehler):
        pass
    LOG.info("ÄNDERUNG: %s", text)
REGISTER = os.path.join(HIER, "SparteNet_Passwort_Register.txt")

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

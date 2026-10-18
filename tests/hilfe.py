"""Hilfen für die Tests: Testserver starten, angemeldete Sitzung, kleiner SMTP-Empfänger, TOTP"""
import base64, hashlib, hmac, http.cookiejar, json, os, re, socket, socketserver, struct, subprocess, sys, tempfile, threading, time
import urllib.error, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(REPO, "SparteNet_Manager")
PASSWORT = "Test-Passwort-123456"


def freier_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Testserver:
    """startet den Manager in einem leeren Datenordner (Dateispeicher) auf einem freien Port"""

    def __init__(self, **umgebung):
        self.ordner = tempfile.mkdtemp(prefix="spartenet_test_")
        self.port = freier_port()
        pwdatei = os.path.join(self.ordner, "pw.txt")
        with open(pwdatei, "w") as f:
            f.write(PASSWORT)
        env = {k: v for k, v in os.environ.items() if not k.startswith("SPARTENET_")}
        db = {k[5:]: v for k, v in os.environ.items() if k.startswith("TEST_SPARTENET_DB_")}   # optional: Test mit MariaDB
        if db.get("SPARTENET_DB_HOST"):
            datenbank_leeren(db)
            env.update(db)
        env.update(SPARTENET_DATA_DIR=self.ordner, SPARTENET_PASSWORD_FILE=pwdatei, SPARTENET_PORT=str(self.port), SPARTENET_HOST="127.0.0.1",
                   SPARTENET_KEIN_BROWSER="1", SPARTENET_UPDATE_PRUEFEN="0", SPARTENET_SICHERUNG="0", SPARTENET_ZEITPLAN="0", SPARTENET_RUNDSCHREIBEN_PAUSE="0", **umgebung)
        self.log = open(os.path.join(self.ordner, "server.log"), "w")
        self.proc = subprocess.Popen([sys.executable, os.path.join(CODE, "SparteNet_Manager.py")], cwd=self.ordner, env=env,
                                     stdout=self.log, stderr=subprocess.STDOUT)
        self.basis = f"http://127.0.0.1:{self.port}"
        for _ in range(100):
            try:
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(self.basis + "/status", timeout=1):
                    return
            except OSError:
                if self.proc.poll() is not None:
                    break
                time.sleep(0.2)
        self.stop()
        raise RuntimeError("Testserver startet nicht:\n" + open(os.path.join(self.ordner, "server.log")).read()[-3000:])

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.log.close()


def _lies(pfad):
    if not pfad:
        return ""
    with open(pfad) as f:
        return f.read().strip()


def datenbank_leeren(db):
    """vor dem Test: Tabellen des Managers in der Testdatenbank entfernen"""
    import pymysql
    c = pymysql.connect(host=db["SPARTENET_DB_HOST"], port=int(db.get("SPARTENET_DB_PORT", "3306")), user=db.get("SPARTENET_DB_USER", "spartenet"),
                        password=db.get("SPARTENET_DB_PASSWORD") or _lies(db.get("SPARTENET_DB_PASSWORD_FILE")), database=db.get("SPARTENET_DB_NAME", "spartenet"))
    with c.cursor() as cur:
        for t in ("sn_daten", "sn_dateien", "sn_journal", "sn_passwort_register", "sn_meta"):
            cur.execute(f"DROP TABLE IF EXISTS {t}")
    c.commit(); c.close()


class Sitzung:
    def __init__(self, basis):
        self.basis = basis
        self.op = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.token = None

    def roh(self, pfad, daten=None, kopf=None, methode=None):
        r = urllib.request.Request(self.basis + pfad, data=daten, method=methode or ("POST" if daten is not None else "GET"))
        for k, v in {**({"X-Token": self.token} if self.token else {}), **(kopf or {})}.items():
            r.add_header(k, v)
        try:
            with self.op.open(r, timeout=30) as a:
                return a.status, dict(a.headers), a.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def req(self, pfad, body=None, kopf=None):
        code, _, x = self.roh(pfad, json.dumps(body).encode() if body is not None else None, {"Content-Type": "application/json", **(kopf or {})})
        try:
            return code, json.loads(x)
        except ValueError:
            return code, x.decode("utf-8", "replace")

    def anmelden(self, name="admin", pw=PASSWORT, code=None):
        c, a = self.req("/login", {"benutzer": name, "passwort": pw, **({"code": code} if code else {})})
        if c != 200:
            return c, a
        _, _, html = self.roh("/")
        html = html.decode()
        self.token = re.search(r'const T="([^"]+)"', html).group(1)
        return 200, json.loads(re.search(r"const ICH=(\{.*?\});", html).group(1))


APP_TOKEN = {"wert": None}   # App-Zugangstoken für Aufrufe der App-Schnittstelle (wird in den Tests erzeugt)


def api(basis, methode, pfad, body=None, schluessel=None):
    r = urllib.request.Request(basis + pfad, data=json.dumps(body).encode() if body is not None else None, method=methode)
    if schluessel:
        r.add_header("Authorization", "Bearer " + schluessel)
    if APP_TOKEN["wert"] and (pfad.startswith("/api/v1/app/") or (schluessel or "").startswith("sna_")):
        r.add_header("X-App-Token", APP_TOKEN["wert"])
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(r, timeout=30) as a:
            return a.status, json.loads(a.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


class SmtpEmpfaenger:
    """minimaler SMTP-Server, der Nachrichten in einer Liste sammelt"""

    def __init__(self):
        self.mails, self.anmeldungen, self.passwort = [], [], "smtp-geheim"
        aussen = self

        class H(socketserver.StreamRequestHandler):
            def handle(self):
                w = lambda s: self.wfile.write((s + "\r\n").encode())
                w("220 test"); an = []
                while True:
                    zeile = self.rfile.readline()
                    if not zeile:
                        return
                    c = zeile.decode().strip(); u = c.upper()
                    if u.startswith("EHLO"):
                        self.wfile.write(b"250-test\r\n250 AUTH LOGIN PLAIN\r\n")
                    elif u == "AUTH LOGIN":
                        import base64 as b64
                        w("334 VXNlcm5hbWU6"); nutzer = b64.b64decode(self.rfile.readline().strip()).decode()
                        w("334 UGFzc3dvcmQ6"); pw = b64.b64decode(self.rfile.readline().strip()).decode()
                        aussen.anmeldungen.append((nutzer, pw))
                        w("235 ok" if pw == aussen.passwort else "535 falsch")
                    elif u.startswith("RCPT"):
                        an.append(c[8:].strip("<>")); w("250 ok")
                    elif u == "DATA":
                        w("354 los"); teile = []
                        while True:
                            x = self.rfile.readline()
                            if x in (b".\r\n", b".\n", b""):
                                break
                            teile.append(x.decode("utf-8", "replace"))
                        aussen.mails.append({"an": an, "text": "".join(teile)}); an = []; w("250 ok")
                    elif u == "QUIT":
                        w("221 tschuess"); return
                    else:
                        w("250 ok")

        socketserver.ThreadingTCPServer.allow_reuse_address = True
        self.server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def warten(self, anzahl, sekunden=10):
        ende = time.time() + sekunden
        while len(self.mails) < anzahl and time.time() < ende:
            time.sleep(0.1)
        return self.mails

    def stop(self):
        self.server.shutdown()


def totp(geheim_b32, zeit=None):
    """unabhängige TOTP-Berechnung (RFC 6238) zum Prüfen des Managers"""
    k = base64.b32decode(geheim_b32.replace(" ", "") + "=" * (-len(geheim_b32.replace(" ", "")) % 8))
    h = hmac.new(k, struct.pack(">Q", int((zeit or time.time()) // 30)), hashlib.sha1).digest()
    o = h[-1] & 15
    return str((struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % 1000000).zfill(6)

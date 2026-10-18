"""SparteNet Manager – Oberfläche gestalten: Anmeldeseite, Pächter-Seite und Ansichtsprofile (Menü, Reiter, Karten)

Anmelde- und Pächter-Seite: Texte, Farben, Schrift, Logo und Hintergrundbild (aus den Unterlagen), Impressum/Datenschutz.
Nur Text und Farbwerte – kein eigenes HTML, damit niemand Schadcode in die öffentlichen Seiten bringen kann.
Bilder der öffentlichen Seiten werden über /seitenbild/<seite>/<logo|hintergrund> ausgeliefert – nur genau die gewählten Bilder.

Ansichtsprofile: je Profil ein eigener Menübaum (Bereiche, Reiter, Karten umbenennen, sortieren, ausblenden, Hinweise ändern).
Jedes Konto bekommt ein Profil. Ausblenden ist nur Ansicht, kein Schutz – was ein Konto darf, regeln weiter die Rechte.
"""
from .laufzeit import *  # noqa: F401,F403 – alle Namen der vorherigen Module

SEITEN_SCHRIFTEN = {
    "system": ("Systemschrift (modern)", "system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif"),
    "klar": ("Verdana (gut lesbar)", "Verdana,Geneva,Tahoma,sans-serif"),
    "freundlich": ("Trebuchet (freundlich)", "'Trebuchet MS','Segoe UI',Arial,sans-serif"),
    "klassisch": ("Georgia (klassisch)", "Georgia,'Times New Roman',serif"),
}
_FARBE_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_ID_RE_SEITE = re.compile(r"^[0-9a-f]{16}$")

LOGIN_STANDARD = {
    "layout": "geteilt", "marke": "SparteNet Manager", "marke_hervor": "Net",
    "ueberschrift": "WLAN für die Kleingarten-Sparte – übersichtlich verwaltet.",
    "untertitel": "Parzellen, Tarife, Pächter und das Gateway an einem Ort.",
    "punkte": ["Eigenes WLAN-Passwort je Parzelle, Zugangskarten mit QR-Code",
               "Tarife mit Laufzeit – Zugang wird pünktlich gesperrt und freigegeben",
               "Mitglieder, Anfragen, Rechnungen und Störungsmeldungen"],
    "titel": "Anmelden",
    "text": "Mit Benutzername und Passwort. Administrator: Benutzername leer lassen oder „admin“. Auf Handys im Fernzugriff geht ohne Benutzername auch die Handy-PIN.",
    "fuss": "", "kontakt": "", "impressum": "", "datenschutz": "", "portal_link": True,
    "logo": "standard", "hintergrund": "", "abdunkeln": 35,
    "farbe_marke1": "#14321f", "farbe_marke2": "#0d2416", "farbe_glanz": "#3f9a26", "farbe_knopf": "#2f8a1c",
    "farbe_grund": "#eef3ec", "farbe_karte": "#ffffff", "farbe_text": "#16261c",
    "schrift": "system", "ecken": 20, "dunkel": True,
}
PORTAL_DESIGN_STANDARD = {
    "marke": "SparteNet", "marke_hervor": "Net", "logo": "", "hintergrund": "", "abdunkeln": 30,
    "farbe_kopf": "#1d2f3e", "farbe_kopf_text": "#ffffff", "farbe_knopf": "#3a9a1f", "farbe_grund": "#f5f7f4", "farbe_karte": "#ffffff", "farbe_text": "#1d2f3e",
    "schrift": "system", "ecken": 12, "dunkel": True, "breite": 640,
    "reihenfolge": ["ticket", "status", "zugang"],
    "t_ticket": "Anfrage stellen", "t_status": "Stand abfragen", "t_zugang": "Zugangskarte",
    "h_ticket": "Bitte geben Sie Ihre Daten genau so an, wie sie beim Verein gespeichert sind – sonst können wir die Anfrage nicht zuordnen.",
    "h_status": "Ticket-Nummer aus der Bestätigung, dazu Ihr Name und Ihre E-Mail-Adresse.",
    "h_zugang": "Die Karte mit WLAN-Name, Passwort und QR-Code kommt per E-Mail an die Adresse, die beim Verein für Ihre Parzelle hinterlegt ist.",
    "danke": "Danke! Ihre Anfrage hat die Nummer {nr}. Bitte notieren Sie die Nummer.",
    "art_kein_mitglied": True, "art_interessent": True, "spamschutz": True,
    "t_mitglied": "Ich bin Mitglied (Pächter einer Parzelle)", "t_kein_mitglied": "Ich bin kein Mitglied einer Sparte",
    "t_interessent": "Ich bin Interessent (möchte WLAN buchen)",
    "kontakt": "", "impressum": "", "datenschutz": "", "fuss": "",
}
_GRENZEN_SEITE = {"abdunkeln": (0, 90), "ecken": (0, 32), "breite": (480, 1100)}
_LANG = {"text": 600, "untertitel": 300, "ueberschrift": 160, "fuss": 600, "kontakt": 300, "danke": 300, "h_ticket": 600, "h_status": 600, "h_zugang": 600,
         "impressum": 300, "datenschutz": 300}


def _bild_ok(d, wert, standard_erlaubt=False):
    if wert in ("",) or (standard_erlaubt and wert == "standard"):
        return wert
    if not _ID_RE_SEITE.match(str(wert)):
        raise Fehler("Ungültiges Bild.")
    logo_bild(d, wert)                      # wirft Fehler, wenn es kein passendes Bild in den Unterlagen ist
    return str(wert)


def _url_ok(u):
    u = text_einzeilig(u or "", 300).strip()
    if u and not re.match(r"^(https?://|mailto:)[^\s<>\"']+$", u):
        raise Fehler("Impressum/Datenschutz: Adresse mit https:// (oder mailto:) angeben.")
    return u


def seite_pruefen(d, roh, std, alt=None):
    aus = dict(std)
    aus.update({k: v for k, v in (alt or {}).items() if k in std})
    for k, s in std.items():
        if k not in (roh or {}):
            continue
        v = roh[k]
        if isinstance(s, bool):
            aus[k] = bool(v)
        elif isinstance(s, int):
            lo, hi = _GRENZEN_SEITE.get(k, (0, 100))
            try:
                aus[k] = max(lo, min(hi, int(v)))
            except (TypeError, ValueError):
                raise Fehler(f"„{k}“ muss eine Zahl sein.")
        elif k.startswith("farbe_"):
            if not _FARBE_RE.match(str(v or "")):
                raise Fehler(f"Farbe „{v}“ ist ungültig (Form #RRGGBB).")
            aus[k] = str(v).lower()
        elif k == "schrift":
            aus[k] = v if v in SEITEN_SCHRIFTEN else "system"
        elif k == "layout":
            aus[k] = v if v in ("geteilt", "mittig") else "geteilt"
        elif k in ("logo", "hintergrund"):
            aus[k] = _bild_ok(d, v, standard_erlaubt=(k == "logo"))
        elif k in ("impressum", "datenschutz"):
            aus[k] = _url_ok(v)
        elif k == "punkte":
            aus[k] = [text_einzeilig(x, 140).strip() for x in (v if isinstance(v, list) else []) if str(x or "").strip()][:6]
        elif k == "reihenfolge":
            r = [x for x in (v if isinstance(v, list) else []) if x in ("ticket", "status", "zugang")]
            aus[k] = list(dict.fromkeys(r + [x for x in ("ticket", "status", "zugang") if x not in r]))
        else:
            aus[k] = text_einzeilig(v, _LANG.get(k, 120)) if k not in ("text", "fuss", "h_ticket", "h_status", "h_zugang") else str(v or "").replace("\r", "")[:_LANG.get(k, 600)]
    return aus


def seiten_design(d, art):
    roh = (d.get("seiten_design") or {}).get(art) if isinstance(d.get("seiten_design"), dict) else None
    std = LOGIN_STANDARD if art == "login" else PORTAL_DESIGN_STANDARD
    aus = dict(std)
    for k, v in (roh or {}).items():
        if k in std:
            aus[k] = v
    if art == "portal":
        p = d.get("portal") if isinstance(d.get("portal"), dict) else {}
        aus["titel"] = str(p.get("titel") or "SparteNet – Service für Pächter")
        aus["text"] = str(p.get("text") or "Hier können Sie eine Anfrage stellen, den Stand Ihrer Anfrage abfragen oder Ihre WLAN-Zugangskarte erneut anfordern.")
    return aus


def seitenbild(d, art, feld):
    """(Bytes, MIME) des für eine öffentliche Seite gewählten Bildes oder None"""
    if art not in ("login", "portal") or feld not in ("logo", "hintergrund"):
        return None
    i = seiten_design(d, art).get(feld)
    if not i or i == "standard":
        return None
    try:
        return logo_bild(d, i)
    except Fehler:
        return None


def _bild_src(d, art, feld, wert, inline):
    if not wert:
        return ""
    if wert == "standard":
        return "/icon-192.png"
    if inline:
        try:
            roh, typ = logo_bild(d, wert)
            return f"data:{typ};base64," + base64.b64encode(roh).decode()
        except Fehler:
            return ""
    return f"/seitenbild/{art}/{feld}?v={wert[:8]}"


def _marke_html(marke, hervor):
    m = html_mod.escape(marke or "")
    h = html_mod.escape(hervor or "")
    return m.replace(h, f"<span>{h}</span>", 1) if h and h in m else m


def _e(t):
    return html_mod.escape(str(t or ""))


def _absaetze(t):
    return "<br>".join(_e(z) for z in str(t or "").split("\n"))


def _links(g, farbe=None):
    teile = []
    st = f' style="color:{farbe}"' if farbe else ""
    if g.get("impressum"):
        teile.append(f'<a href="{_e(g["impressum"])}" rel="noopener"{st}>Impressum</a>')
    if g.get("datenschutz"):
        teile.append(f'<a href="{_e(g["datenschutz"])}" rel="noopener"{st}>Datenschutz</a>')
    return teile


_DUNKEL = ("--grund:#0c1410;--karte:#16211b;--text:#e3ebe5;--leise:#9db0a4;--rand:#2b3a31;--feld:#101914;--fehlerg:#3a1714;--fehler:#ff9b8f;"
           "--info:#12283a;--infot:#9fd0f5;--schatten:0 18px 50px rgba(0,0,0,.5)")


def login_seite(d, design=None, inline=False):
    """Anmeldeseite aus dem gespeicherten (oder übergebenen) Design"""
    g = design or seiten_design(d, "login")
    s = sicherheit(d)
    ab, merken = s["abmelden_minuten"], s["2fa_merken_stunden"]
    portal_an = bool((d.get("portal") or {}).get("aktiv")) if isinstance(d.get("portal"), dict) else False
    vars_ = (f"--knopf:{g['farbe_knopf']};--m1:{g['farbe_marke1']};--m2:{g['farbe_marke2']};--glanz:{g['farbe_glanz']};"
             f"--grund:{g['farbe_grund']};--karte:{g['farbe_karte']};--text:{g['farbe_text']};--ecken:{int(g['ecken'])}px;"
             f"--schrift:{SEITEN_SCHRIFTEN[g['schrift']][1]};--abdunkeln:{int(g['abdunkeln']) / 100:.2f}")
    dunkel = (f"@media (prefers-color-scheme:dark){{:root:not([data-farbe=hell]){{{_DUNKEL}}}}}:root[data-farbe=dunkel]{{{_DUNKEL}}}" if g["dunkel"] else "")
    hg = _bild_src(d, "login", "hintergrund", g["hintergrund"], inline)
    logo = _bild_src(d, "login", "logo", g["logo"], inline)
    fuss = _links(g, "#cfe9c6")
    if g["portal_link"] and portal_an:
        fuss.insert(0, '<a href="/portal" style="color:#cfe9c6">Pächter-Seite</a>')
    klein = []
    if g["fuss"]:
        klein.append(_absaetze(g["fuss"]))
    klein.append((f"Aus Sicherheitsgründen werden Sie nach {ab} Minuten ohne Aktivität automatisch abgemeldet. " if ab else "")
                 + "Ohne „Angemeldet bleiben“ endet die Anmeldung beim Schließen des Browsers.")
    if g["kontakt"]:
        klein.append("Hilfe: " + _e(g["kontakt"]))
    unten = _links(g)
    if unten:
        klein.append(" · ".join(unten))
    return (LOGIN_HTML.replace("__VARS__", vars_).replace("__DUNKEL__", dunkel)
            .replace("__LAYOUT__", "mittig" if g["layout"] == "mittig" else "geteilt")
            .replace("__HG__", f"url('{hg}')" if hg else "none")
            .replace("__LOGO__", f'<img src="{_e(logo)}" alt="">' if logo else "")
            .replace("__MARKE__", _marke_html(g["marke"], g["marke_hervor"]))
            .replace("__UEBERSCHRIFT__", _e(g["ueberschrift"])).replace("__UNTERTITEL__", _e(g["untertitel"]))
            .replace("__PUNKTE__", "".join(f"<li><i>✓</i>{_e(p)}</li>" for p in g["punkte"]))
            .replace("__FUSSLEISTE__", " · ".join([f"Version {VERSION}"] + fuss))
            .replace("__TITEL__", _e(g["titel"])).replace("__TEXT__", _absaetze(g["text"]))
            .replace("__MERKEN__", f"Dieses Gerät fragt danach {dauer_text_kurz(merken)} lang nicht erneut." if merken else "")
            .replace("__KLEIN__", "<br>".join(klein)))


def portal_seite(d, design=None, inline=False):
    from .portal import PORTAL_HTML       # steht in der späteren Datei portal.py
    g = design or seiten_design(d, "portal")
    vars_ = (f"--a:{g['farbe_knopf']};--k:{g['farbe_kopf']};--kt:{g['farbe_kopf_text']};--bg:{g['farbe_grund']};--c:{g['farbe_karte']};--t:{g['farbe_text']};"
             f"--ecken:{int(g['ecken'])}px;--breite:{int(g['breite'])}px;--schrift:{SEITEN_SCHRIFTEN[g['schrift']][1]};--abdunkeln:{int(g['abdunkeln']) / 100:.2f}")
    dunkel = ("@media (prefers-color-scheme:dark){:root{--bg:#0f161c;--c:#18222a;--t:#e2e8ec;--m:#9aa9b3;--l:#2e3c46}}" if g["dunkel"] else "")
    hg = _bild_src(d, "portal", "hintergrund", g["hintergrund"], inline)
    logo = _bild_src(d, "portal", "logo", g["logo"], inline)
    fuss = []
    if g["kontakt"]:
        fuss.append("Kontakt: " + _e(g["kontakt"]))
    if g["fuss"]:
        fuss.append(_absaetze(g["fuss"]))
    links = _links(g)
    if links:
        fuss.append(" · ".join(links))
    return (PORTAL_HTML.replace("__VARS__", vars_).replace("__DUNKEL__", dunkel)
            .replace("__HG__", f"url('{hg}')" if hg else "none").replace("__MITBILD__", "mitbild" if hg else "")
            .replace("__LOGO__", f'<img src="{_e(logo)}" alt="">' if logo else "")
            .replace("__MARKE__", _marke_html(g["marke"], g["marke_hervor"]))
            .replace("__FUSS__", "<br>".join(fuss)))


# ---- Ansichtsprofile -------------------------------------------------------------------------------------------------
_PID_RE = re.compile(r"^[a-z0-9]{6,16}$")
_KEY_RE = re.compile(r"^[A-Za-z0-9_./:-]{1,80}$")


def ansicht_profile(d):
    a = d.get("ansicht_profile")
    if not isinstance(a, dict):
        a = {}
        d["ansicht_profile"] = a
    if not isinstance(a.get("profile"), dict):
        a["profile"] = {}
    return a


def _baum_pruefen(b):
    """nur bekannte Schlüssel, begrenzte Längen – der Menübaum selbst steht in der Oberfläche"""
    b = b if isinstance(b, dict) else {}
    aus = {"bereiche": [], "tabs": {}, "karten": {}, "reihenfolge": {}, "start": ""}
    for x in (b.get("bereiche") or [])[:30]:
        if not isinstance(x, dict) or not _KEY_RE.match(str(x.get("id") or "")):
            continue
        aus["bereiche"].append({"id": str(x["id"]), "name": text_einzeilig(x.get("name") or "", 40), "icon": text_einzeilig(x.get("icon") or "", 8),
                                "aus": bool(x.get("aus")), "tabs": [str(t) for t in (x.get("tabs") or [])[:40] if _KEY_RE.match(str(t))]})
    for k, x in list((b.get("tabs") or {}).items())[:60]:
        if _KEY_RE.match(str(k)) and isinstance(x, dict):
            aus["tabs"][str(k)] = {"name": text_einzeilig(x.get("name") or "", 40), "aus": bool(x.get("aus"))}
    for k, x in list((b.get("karten") or {}).items())[:400]:
        if _KEY_RE.match(str(k)) and isinstance(x, dict):
            e = {"name": text_einzeilig(x.get("name") or "", 80), "aus": bool(x.get("aus")), "zu": bool(x.get("zu"))}
            if x.get("hint") is not None:
                e["hint"] = str(x.get("hint"))[:600]
            aus["karten"][str(k)] = e
    for k, x in list((b.get("reihenfolge") or {}).items())[:60]:
        if _KEY_RE.match(str(k)) and isinstance(x, list):
            aus["reihenfolge"][str(k)] = [str(i) for i in x[:200] if _KEY_RE.match(str(i))]
    if _KEY_RE.match(str(b.get("start") or "")):
        aus["start"] = str(b["start"])
    if len(json.dumps(aus)) > 250_000:
        raise Fehler("Das Profil ist zu groß.")
    return aus


def konto_profil(d, name):
    """Menübaum des Profils, das dem Konto zugewiesen ist (oder des Standardprofils) – {} = Standardansicht"""
    a = ansicht_profile(d)
    if name == ADMIN_NAME:
        pid = d.get("admin_profil") or ""
    else:
        pid = (benutzer_liste(d).get(name) or {}).get("profil") or ""
    pid = pid if pid in a["profile"] else (a.get("standard") if a.get("standard") in a["profile"] else "")
    p = a["profile"].get(pid) if pid else None
    return {"id": pid, "name": p.get("name", ""), **p.get("baum", {})} if p else {}


def akt_gestaltung(d, ich, log=None):
    a = ansicht_profile(d)
    konten = [{"name": ADMIN_NAME, "anzeige": "Administrator", "profil": d.get("admin_profil") or ""}] + [
        {"name": n, "anzeige": x.get("anzeige", ""), "profil": x.get("profil", "")} for n, x in sorted(benutzer_liste(d).items())]
    return {"login": seiten_design(d, "login"), "portal": seiten_design(d, "portal"),
            "standard": {"login": LOGIN_STANDARD, "portal": PORTAL_DESIGN_STANDARD}, "schriften": {k: v[0] for k, v in SEITEN_SCHRIFTEN.items()},
            "logos": logo_unterlagen(d), "profile": a["profile"], "standardprofil": a.get("standard", ""), "konten": konten,
            "portal_aktiv": bool((d.get("portal") or {}).get("aktiv")) if isinstance(d.get("portal"), dict) else False, "log": log or []}


def akt_seiten_design(d, b, ich):
    art = b.get("art")
    if art not in ("login", "portal"):
        raise Fehler("Seite: login oder portal.")
    roh = b.get("design") or {}
    if b.get("zuruecksetzen"):
        (d.setdefault("seiten_design", {})).pop(art, None)
        speichere(d)
        journal(f"{'Anmeldeseite' if art == 'login' else 'Pächter-Seite'}: Standard wiederhergestellt durch {ich}")
        return akt_gestaltung(d, ich, ["✔ Standard wiederhergestellt."])
    std = LOGIN_STANDARD if art == "login" else PORTAL_DESIGN_STANDARD
    alt = (d.get("seiten_design") or {}).get(art) if isinstance(d.get("seiten_design"), dict) else None
    neu = seite_pruefen(d, roh, std, alt)
    d.setdefault("seiten_design", {})[art] = neu
    if art == "portal":
        p = d.get("portal") if isinstance(d.get("portal"), dict) else {}
        if "titel" in roh:
            p["titel"] = text_einzeilig(roh["titel"], 120)
        if "text" in roh:
            p["text"] = text_einzeilig(roh["text"], 1000)
        d["portal"] = p
    speichere(d)
    journal(f"{'Anmeldeseite' if art == 'login' else 'Pächter-Seite'} gestaltet durch {ich}")
    return akt_gestaltung(d, ich, ["✔ Gespeichert – die Seite sieht ab sofort so aus."])


def akt_seiten_vorschau(d, b):
    art = b.get("art")
    if art not in ("login", "portal"):
        raise Fehler("Seite: login oder portal.")
    std = LOGIN_STANDARD if art == "login" else PORTAL_DESIGN_STANDARD
    g = seite_pruefen(d, b.get("design") or {}, std, seiten_design(d, art))
    if art == "portal":
        g["titel"], g["text"] = text_einzeilig((b.get("design") or {}).get("titel") or seiten_design(d, art)["titel"], 120), \
            text_einzeilig((b.get("design") or {}).get("text") or seiten_design(d, art)["text"], 1000)
    html = login_seite(d, g, inline=True) if art == "login" else portal_seite(d, g, inline=True)
    if art == "portal":       # Vorschau ohne Server-Abfrage: Info direkt einsetzen
        html = html.replace("fetch(\"/portal/info\").then(r=>r.json())", "Promise.resolve(" + json.dumps(portal_info_aus(d, g), ensure_ascii=False).replace("</", "<\\/") + ")")
    return {"html": html, "log": []}


def portal_info_aus(d, g):
    """Angaben für die Pächter-Seite (Texte, Reihenfolge, Sparten) – auch für die Vorschau"""
    e = d.get("portal") if isinstance(d.get("portal"), dict) else {}
    an = {k: bool(e.get(k, True)) for k in ("ticket", "status", "zugang")}
    sparten = sorted(({"kz": k, "name": n} for k, n in _sparten_kz(d).items()), key=lambda x: x["name"].lower())
    return {"titel": g["titel"], "text": g["text"], **an, "sparten": sparten, "kategorien": list(ticket_kategorien(d)),
            **{k: g[k] for k in ("reihenfolge", "t_ticket", "t_status", "t_zugang", "h_ticket", "h_status", "h_zugang", "art_kein_mitglied", "art_interessent",
                                 "t_mitglied", "t_kein_mitglied", "t_interessent", "kontakt", "spamschutz")},
            **(spam_frage() if g["spamschutz"] else {})}


# ---- einfacher Spamschutz: kleine Rechenaufgabe (signiert, ohne Speicher) + Mindestzeit + höchstens 2 Links ------------
_SPAM_GEHEIM = secrets.token_bytes(32)


def spam_frage():
    a, b = secrets.randbelow(8) + 2, secrets.randbelow(8) + 1
    ts = str(int(time.time()))
    sig = hmac.new(_SPAM_GEHEIM, f"{a + b}|{ts}".encode(), hashlib.sha256).hexdigest()[:24]
    return {"frage": f"Wie viel ist {a} + {b}?", "frage_token": f"{ts}.{sig}"}


def spam_pruefen(b):
    """wirft Fehler bei Roboter-Verdacht: falsche Rechenaufgabe, zu schnell (unter 3 s) oder abgelaufen, zu viele Links"""
    tok = str(b.get("frage_token") or "")
    antwort = re.sub(r"\D", "", str(b.get("antwort") or ""))
    try:
        ts, sig = tok.split(".", 1)
        alter = time.time() - int(ts)
    except ValueError:
        raise Fehler("Bitte die Rechenaufgabe lösen (Seite neu laden, falls sie fehlt).")
    if not antwort or not hmac.compare_digest(sig, hmac.new(_SPAM_GEHEIM, f"{antwort}|{ts}".encode(), hashlib.sha256).hexdigest()[:24]):
        raise Fehler("Das Ergebnis der Rechenaufgabe stimmt nicht.")
    if alter < 3:
        raise Fehler("Das ging zu schnell – bitte noch einmal absenden.")
    if alter > 7200:
        raise Fehler("Die Rechenaufgabe ist abgelaufen – bitte die Seite neu laden.")
    if len(re.findall(r"https?://|www\.", f"{b.get('betreff', '')} {b.get('text', '')}", re.I)) > 2:
        raise Fehler("Bitte höchstens zwei Links in die Nachricht schreiben.")


def akt_ansicht_profile(d, b, ich):
    a = ansicht_profile(d)
    if "profile" in b:
        roh = b.get("profile") or {}
        if not isinstance(roh, dict) or len(roh) > 30:
            raise Fehler("Höchstens 30 Profile.")
        neu = {}
        for pid, p in roh.items():
            if not _PID_RE.match(str(pid)) or not isinstance(p, dict):
                raise Fehler("Ungültiges Profil.")
            name = text_einzeilig(p.get("name") or "", 40).strip()
            if not name:
                raise Fehler("Jedes Profil braucht einen Namen.")
            if name.lower() in {x["name"].lower() for x in neu.values()}:
                raise Fehler(f"Profil „{name}“ gibt es doppelt.")
            neu[str(pid)] = {"name": name, "baum": _baum_pruefen(p.get("baum")), "geaendert": time.strftime("%Y-%m-%d %H:%M")}
        a["profile"] = neu
    if "standard" in b:
        a["standard"] = str(b.get("standard") or "") if str(b.get("standard") or "") in a["profile"] else ""
    if "zuordnung" in b:
        for name, pid in (b.get("zuordnung") or {}).items():
            pid = str(pid or "")
            if pid and pid not in a["profile"]:
                raise Fehler("Profil nicht gefunden.")
            if name == ADMIN_NAME:
                d["admin_profil"] = pid
            elif name in benutzer_liste(d):
                benutzer_liste(d)[name]["profil"] = pid
    # Profile, die es nicht mehr gibt, bei den Konten entfernen
    for x in benutzer_liste(d).values():
        if x.get("profil") and x["profil"] not in a["profile"]:
            x["profil"] = ""
    if d.get("admin_profil") and d["admin_profil"] not in a["profile"]:
        d["admin_profil"] = ""
    speichere(d)
    journal(f"Ansichtsprofile gespeichert durch {ich} ({len(a['profile'])} Profil(e))")
    return akt_gestaltung(d, ich, ["✔ Ansichtsprofile gespeichert – gilt beim nächsten Laden der Seite."])


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

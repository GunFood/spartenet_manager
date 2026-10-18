"""SparteNet Manager – Automationen: Wenn ein Ereignis eintritt (Buchung, Kündigung, Zahlung, eigenes API-Ereignis, Unterlage),
führt der Manager die hinterlegten Aktionen aus – E-Mail senden, Tarif buchen, Buchung entfernen, Webhook aufrufen, Protokolleintrag.

Am Gateway ändert eine Automation nie etwas: Übertragen (Tarife, Passwörter) bleibt ein Schritt mit Vorschau und Bestätigung.
E-Mails und Webhooks laufen im Hintergrund (Warteschlange), Buchungen sofort. Verlauf: Ablage „Automation_Verlauf.json“.
"""
import email.message
import email.utils
import html as html_mod
import queue
import smtplib
from html.parser import HTMLParser

from .zweifaktor import *  # noqa: F401,F403 – alle Namen der vorherigen Module

AUSLOESER = {
    "buchung": "Parzelle bucht einen Tarif (neu oder Tarifwechsel)",
    "kuendigung": "Buchung einer Parzelle wird entfernt (Kündigung)",
    "zahlung": "Zahlung eingegangen (über die API, z. B. aus der Buchhaltung)",
    "api": "Eigenes Ereignis über die API (Name frei wählbar)",
    "unterlage": "Unterlage hochgeladen",
    "mitglied_neu": "Mitglied angelegt (von Hand, Import oder API)",
    "ticket_neu": "Neue Anfrage (Ticket) eingegangen",
    "ticket_zugewiesen": "Ticket einem Benutzer zugewiesen",
    "ticket_erledigt": "Ticket erledigt",
    "stoerung": "Störung: Gerät offline (Überwachung)",
    "stoerung_behoben": "Störung behoben: Gerät wieder online",
    "vertrag_erinnerung": "Vertrag: Kündigungsfrist läuft bald ab",
    "vertrag_gekuendigt": "Vertrag gekündigt",
    "vertrag_ende": "Vertrag endet (nach Kündigung)",
}
AKTIONEN = {
    "email": "E-Mail senden",
    "buchen": "Tarif buchen (im Manager)",
    "buchung_entfernen": "Buchung entfernen (im Manager)",
    "webhook": "Webhook aufrufen (POST mit JSON)",
    "protokoll": "Eintrag ins Änderungsprotokoll",
}
PLATZHALTER = {
    "{ereignis}": "Art des Ereignisses", "{sparte}": "Kürzel der Sparte", "{sparte_name}": "Name der Sparte", "{parzelle}": "Parzellennummer",
    "{tarif}": "Tarif (neu)", "{tarif_alt}": "bisheriger Tarif", "{preis}": "Jahrespreis des Tarifs", "{betrag}": "Betrag (Zahlung)",
    "{referenz}": "Referenz / Rechnungsnummer", "{email}": "E-Mail des Kunden (aus dem Ereignis)", "{name}": "Name des Kunden",
    "{datum}": "heutiges Datum", "{zeit}": "Uhrzeit", "{wlan}": "WLAN-Name der Sparte", "{passwort}": "WLAN-Passwort der Parzelle (vertraulich!)",
    "{netz}": "Netzname der Parzelle", "{vlan}": "VLAN-ID der Parzelle", "{gateway}": "zugeteiltes Gateway (Gateway-Zuteilung nach Buchung)",
    "{quelle}": "wer das Ereignis ausgelöst hat",
    "{vorname}": "Vorname des Mitglieds", "{nachname}": "Nachname des Mitglieds", "{telefon}": "Telefon des Mitglieds",
    "{ticket}": "Ticket-Nummer", "{betreff}": "Betreff des Tickets", "{nachricht}": "Text des Tickets", "{status}": "Status des Tickets",
    "{kategorie}": "Kategorie des Tickets", "{prioritaet}": "Priorität des Tickets", "{zustaendig}": "zuständiger Benutzer",
    "{zustaendig_email}": "E-Mail des zuständigen Benutzers",
    "{geraet}": "Gerät (Störung)", "{seit}": "offline seit (Störung)", "{dauer}": "Dauer der Störung",
    "{vertrag_beginn}": "Vertragsbeginn", "{vertrag_ende}": "Ende der laufenden Vertragsperiode", "{kuendbar_bis}": "Kündigung möglich bis",
    "{rechnung}": "Rechnungsnummer", "{faellig}": "Fälligkeit der Rechnung",
}
AKTION_ERWEITERUNG = {}   # Aktionen späterer Module: f(d, daten, aktion, werte, probe, regelname) → Text fürs Protokoll
LAYOUT_STANDARD = {"aktiv": True, "logo": True, "farbe_kopf": "#1d2f3e", "farbe_kopf_text": "#ffffff", "farbe_akzent": "#3a9a1f",
                   "farbe_hinter": "#f5f7f4", "farbe_text": "#1d2f3e", "schrift": "Arial, Helvetica, sans-serif", "breite": 600,
                   "kopf": "SparteNet.de", "fuss": "SparteNet.de · WLAN für Kleingärten\nDiese E-Mail wurde automatisch versendet."}
_HTML_ERLAUBT = {"p": (), "br": (), "b": (), "strong": (), "i": (), "em": (), "u": (), "h2": (), "h3": (), "ul": (), "ol": (), "li": (),
                 "a": ("href",), "hr": (), "blockquote": (), "div": (), "span": ()}
SMTP_STANDARD = {"host": "", "port": 587, "sicherheit": "starttls", "anmeldung": "login", "benutzer": "", "absender": "", "absender_name": "SparteNet"}
SMTP_ANMELDUNG = {"login": "SMTP-Login (AUTH LOGIN, Benutzername + Passwort)", "plain": "AUTH PLAIN", "auto": "automatisch (was der Server anbietet)",
                  "keine": "keine Anmeldung (nur eigener Mailserver im Netz)"}
_SMTP_PW_DATEI = os.environ.get("SPARTENET_SMTP_PASSWORD_FILE", "").strip()
_WARTESCHLANGE = queue.Queue(maxsize=500)
_VERLAUF_LOCK = threading.Lock()
VERLAUF_NAME = "Automation_Verlauf.json"
_TIEFE = threading.local()   # Automation löst Automation aus (Buchen → „Buchung“) – höchstens 3 Ebenen, keine Endlosschleife
_EMAIL_RE = re.compile(r"^[^@\s,;<>]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,}$")


def automation_daten(d):
    a = d.get("automation") if isinstance(d.get("automation"), dict) else {}
    if not isinstance(a.get("regeln"), list):
        a["regeln"] = []
    d["automation"] = a
    return a


def smtp_einstellungen(d):
    s = dict(SMTP_STANDARD)
    roh = d.get("smtp") if isinstance(d.get("smtp"), dict) else {}
    for k in SMTP_STANDARD:
        if k in roh:
            s[k] = roh[k]
    return s


def _smtp_passwort(d):
    if _SMTP_PW_DATEI:
        try:
            with open(_SMTP_PW_DATEI, encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            return ""
    return str((d.get("smtp") or {}).get("passwort") or "")


def verlauf_lesen():
    try:
        roh = ablage_lesen(VERLAUF_NAME)
        return json.loads(roh.decode("utf-8")) if roh else []
    except (ValueError, Fehler):
        return []


def verlauf_schreiben(eintrag):
    with _VERLAUF_LOCK:
        v = verlauf_lesen()
        v.insert(0, {"zeit": time.strftime("%Y-%m-%d %H:%M:%S"), **eintrag})
        ablage_schreiben(VERLAUF_NAME, json.dumps(v[:300], ensure_ascii=False))


def _platzhalter_werte(daten, d):
    w = {k.strip("{}"): "" for k in PLATZHALTER}
    w.update({k: ("" if v is None else str(v)) for k, v in daten.items() if isinstance(v, (str, int, float))})
    w["datum"], w["zeit"] = time.strftime("%d.%m.%Y"), time.strftime("%H:%M")
    kz, p = str(daten.get("sparte") or ""), daten.get("parzelle")
    if kz and not w.get("sparte_name"):
        try:
            w["sparte_name"] = (kalk_sparten(d).get(kz) or {}).get("name") or kz
        except Fehler:
            w["sparte_name"] = kz
    if w.get("tarif"):
        t = next((t for t in tarife_pruefen(d["tarife"]) if t["name"] == w["tarif"]), None)
        w["preis"] = f"{float(t.get('preis') or 0):.2f} €".replace(".", ",") if t else ""
    if kz and p:
        try:
            z = next((z for z in lese_ppsk(kz) if str(z.get("Parzelle")) == str(p)), None)
        except Exception:
            z = None
        if z:
            w["wlan"], w["passwort"], w["netz"], w["vlan"] = z.get("WLAN", ""), z.get("Passwort", ""), z.get("Netz", ""), z.get("VLAN", "")
        m = next((m for m in (d.get("mitglieder") or {}).values() if isinstance(m, dict) and m.get("sparte") == kz and str(m.get("parzelle")) == str(p)), None)
        if m:
            w.update(vorname=m.get("vorname", ""), nachname=m.get("nachname", ""), telefon=w.get("telefon") or m.get("telefon", ""))
            w["email"] = w.get("email") or m.get("email", "")
            w["name"] = w.get("name") or f"{m.get('vorname', '')} {m.get('nachname', '')}".strip()
        e = ((d.get("zuteilung") or {}).get("p") or {}).get(f"{kz}-{int(p)}") if str(p).isdigit() else None
        if e:
            w["gateway"] = f"Standort {e.get('standort')}, Gateway {e.get('gw')}"
            w["vlan"] = w["vlan"] or str(e.get("vlan") or "")
    if w.get("zustaendig") and not w.get("zustaendig_email"):
        w["zustaendig_email"] = d.get("admin_email", "") if w["zustaendig"] == ADMIN_NAME else ((benutzer_liste(d).get(w["zustaendig"]) or {}).get("email", ""))
    return w


def _ersetzen(text, werte, html=False):
    f = (lambda v: html_mod.escape(v)) if html else (lambda v: v)
    return re.sub(r"\{([a-z_]+)\}", lambda m: f(werte[m.group(1)]) if m.group(1) in werte else m.group(0), str(text or ""))


# ---- E-Mail mit Layout: HTML aus dem Editor (nur sichere Elemente), Layout mit Logo, Farben, Kopf und Fuß ----------------
class _Bereiniger(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.aus, self.offen, self.weg = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "iframe", "object", "head", "title"):
            self.weg += 1
            return
        if self.weg or tag not in _HTML_ERLAUBT:
            return
        a = ""
        if tag == "a":
            href = dict(attrs).get("href") or ""
            if re.match(r"^(https?://|mailto:|\{[a-z_]+\})", href.strip(), re.I):
                a = f' href="{html_mod.escape(href.strip(), quote=True)}"'
        self.aus.append(f"<{tag}{a}>")
        if tag not in ("br", "hr"):
            self.offen.append(tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "iframe", "object", "head", "title"):
            self.weg = max(0, self.weg - 1)
            return
        if self.weg or tag not in self.offen:
            return
        while self.offen:
            t = self.offen.pop()
            self.aus.append(f"</{t}>")
            if t == tag:
                break

    def handle_data(self, data):
        if not self.weg:
            self.aus.append(html_mod.escape(data, quote=False))


def html_bereinigen(roh, grenze=30000):
    p = _Bereiniger()
    p.feed(str(roh or "")[:grenze * 2])
    p.close()
    return ("".join(p.aus) + "".join(f"</{t}>" for t in reversed(p.offen)))[:grenze]


def html_zu_text(h):
    t = re.sub(r"(?i)<br\s*/?>", "\n", h)
    t = re.sub(r"(?i)</(p|div|h2|h3|blockquote)>", "\n\n", t)
    t = re.sub(r"(?i)<li>", "• ", t)
    t = re.sub(r"(?i)</li>", "\n", t)
    t = re.sub(r'(?i)<a href="([^"]+)">(.*?)</a>', lambda m: m.group(2) + (f" ({html_mod.unescape(m.group(1))})" if m.group(1) not in m.group(2) else ""), t)
    t = html_mod.unescape(re.sub(r"<[^>]+>", "", t))
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def text_zu_html(t):
    return "".join(f"<p>{html_mod.escape(a).replace(chr(10), '<br>')}</p>" for a in str(t or "").split("\n\n") if a.strip())


def email_layout(d):
    l = dict(LAYOUT_STANDARD)
    roh = d.get("email_layout") if isinstance(d.get("email_layout"), dict) else {}
    for k, std in LAYOUT_STANDARD.items():
        if k not in roh:
            continue
        v = roh[k]
        if isinstance(std, bool):
            l[k] = bool(v)
        elif k == "breite":
            try:
                l[k] = max(400, min(900, int(v)))
            except (TypeError, ValueError):
                pass
        elif k.startswith("farbe_"):
            if re.fullmatch(r"#[0-9a-fA-F]{6}", str(v)):
                l[k] = str(v)
        elif k == "schrift":
            if str(v) in ("Arial, Helvetica, sans-serif", "Georgia, serif", "Verdana, sans-serif", "Tahoma, sans-serif", "'Segoe UI', Roboto, sans-serif"):
                l[k] = str(v)
        else:
            l[k] = str(v)[:1000]
    return l


def _logo_teil(d):
    """(Bytes, Untertyp) des Kartenlogos für die E-Mail oder None"""
    uri = logo_daten_uri(d.get("design") or {})
    m = re.match(r"data:image/(png|jpeg|gif|webp);base64,(.+)", uri or "")
    if not m:
        return None
    try:
        return base64.b64decode(m.group(2)), m.group(1)
    except ValueError:
        return None


def email_html(d, inhalt_html, betreff="", logo_src=None):
    l = email_layout(d)
    e = html_mod.escape
    logo = ""
    if l["logo"] and logo_src:
        logo = f'<img src="{logo_src}" alt="" style="max-height:60px;max-width:220px;display:block;margin:0 auto 8px">'
    fuss = "<br>".join(e(z) for z in l["fuss"].splitlines())
    inhalt = (inhalt_html.replace("<a ", f'<a style="color:{l["farbe_akzent"]}" ').replace("<h2>", f'<h2 style="color:{l["farbe_akzent"]};font-size:20px;margin:18px 0 8px">')
              .replace("<h3>", '<h3 style="font-size:16px;margin:16px 0 6px">').replace("<p>", '<p style="margin:0 0 12px">'))
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{e(betreff)}</title></head>'
            f'<body style="margin:0;padding:0;background:{l["farbe_hinter"]}">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{l["farbe_hinter"]}"><tr><td align="center" style="padding:20px 10px">'
            f'<table role="presentation" width="{l["breite"]}" cellpadding="0" cellspacing="0" style="max-width:100%;background:#ffffff;border-radius:8px;overflow:hidden;font-family:{l["schrift"]};color:{l["farbe_text"]};font-size:15px;line-height:1.5">'
            f'<tr><td style="background:{l["farbe_kopf"]};color:{l["farbe_kopf_text"]};padding:18px 24px;text-align:center;font-size:20px;font-weight:bold">{logo}{e(l["kopf"])}</td></tr>'
            f'<tr><td style="height:4px;background:{l["farbe_akzent"]}"></td></tr>'
            f'<tr><td style="padding:24px">{inhalt}</td></tr>'
            f'<tr><td style="padding:14px 24px;background:#f0f2ef;color:#5d6b75;font-size:12px;text-align:center">{fuss}</td></tr>'
            f'</table></td></tr></table></body></html>')


def _passt(regel, typ, daten):
    if not regel.get("aktiv", True) or regel.get("ausloeser") != typ:
        return False
    if typ == "api" and regel.get("ereignis_name") and regel["ereignis_name"] != daten.get("ereignis_name"):
        return False
    b = regel.get("bedingung") or {}
    if b.get("sparte") and b["sparte"] != daten.get("sparte"):
        return False
    if b.get("tarif") and b["tarif"] != daten.get("tarif"):
        return False
    if b.get("betrag_min") not in (None, ""):
        try:
            if float(daten.get("betrag") or 0) < float(b["betrag_min"]):
                return False
        except (TypeError, ValueError):
            return False
    return True


def email_senden(d, an, betreff, text, html=None, anhaenge=None):
    s = smtp_einstellungen(d)
    if not s["host"] or not s["absender"]:
        raise Fehler("E-Mail-Versand ist nicht eingerichtet (Automationen → E-Mail-Versand).")
    empfaenger = [x.strip() for x in re.split(r"[,;\s]+", str(an or "")) if x.strip()]
    if not empfaenger or not all(_EMAIL_RE.match(x) for x in empfaenger):
        raise Fehler(f"Ungültige Empfänger-Adresse: {an!r}")
    m = email.message.EmailMessage()
    m["From"] = email.utils.formataddr((s["absender_name"] or "SparteNet", s["absender"]))
    m["To"] = ", ".join(empfaenger)
    m["Subject"] = text_einzeilig(betreff, 200)
    m["Date"] = email.utils.formatdate(localtime=True)
    m["Message-ID"] = email.utils.make_msgid(domain=s["absender"].split("@")[-1])
    m.set_content(str(text or "") if text else html_zu_text(html or ""))
    if html is not None and email_layout(d)["aktiv"]:
        logo = _logo_teil(d) if email_layout(d)["logo"] else None
        cid = email.utils.make_msgid(domain="spartenet")
        m.add_alternative(email_html(d, html, betreff, f"cid:{cid[1:-1]}" if logo else None), subtype="html")
        if logo:
            m.get_payload()[1].add_related(logo[0], maintype="image", subtype=logo[1], cid=cid)
    for name, daten, typ in anhaenge or []:
        haupt, _, unter = (typ or "application/octet-stream").partition("/")
        m.add_attachment(daten, maintype=haupt, subtype=unter or "octet-stream", filename=name)
    port = int(s["port"] or (465 if s["sicherheit"] == "ssl" else 587))
    ctx = ssl.create_default_context()
    try:
        if s["sicherheit"] == "ssl":
            verb = smtplib.SMTP_SSL(s["host"], port, timeout=20, context=ctx)
        else:
            verb = smtplib.SMTP(s["host"], port, timeout=20)
    except (OSError, smtplib.SMTPException) as e:
        raise Fehler(f"Mailserver {s['host']}:{port} nicht erreichbar ({type(e).__name__}: {e}) – Server, Port und Verschlüsselung prüfen.")
    try:
        verb.ehlo()
        if s["sicherheit"] == "starttls":
            verb.starttls(context=ctx)
            verb.ehlo()
        smtp_anmelden(d, s, verb)
        verb.send_message(m)
    except smtplib.SMTPAuthenticationError as e:
        raise Fehler(f"Der Mailserver lehnt die Anmeldung ab ({e.smtp_code}: {(e.smtp_error or b'').decode('utf-8', 'replace')[:150]}) – Benutzername und Passwort prüfen.")
    except smtplib.SMTPNotSupportedError:
        raise Fehler("Der Mailserver bietet diese Anmeldung nicht an – meist muss die Verschlüsselung „STARTTLS“ (Port 587) oder „SSL/TLS“ (Port 465) gewählt werden.")
    except smtplib.SMTPRecipientsRefused as e:
        raise Fehler("Empfänger abgelehnt: " + ", ".join(e.recipients)[:200])
    except smtplib.SMTPSenderRefused as e:
        raise Fehler(f"Absender {s['absender']} abgelehnt ({e.smtp_code}) – beim Provider muss die Absender-Adresse zum Postfach passen.")
    finally:
        try:
            verb.quit()
        except Exception:
            pass
    return ", ".join(empfaenger)


def smtp_anmelden(d, s, verb):
    """SMTP-Login mit Benutzername (sonst Absender-Adresse) und Passwort"""
    art = s.get("anmeldung") or "login"
    if art == "keine":
        return
    benutzer, pw = s.get("benutzer") or s.get("absender"), _smtp_passwort(d)
    if not pw:
        raise Fehler("Für den SMTP-Login fehlt das Passwort (Automationen → E-Mail-Versand).")
    if art == "auto":
        verb.login(benutzer, pw)
        return
    if not verb.has_extn("auth"):
        raise smtplib.SMTPNotSupportedError("AUTH")
    verb.user, verb.password = benutzer, pw
    if art == "plain":
        verb.auth("PLAIN", verb.auth_plain)
    else:
        verb.auth("LOGIN", verb.auth_login, initial_response_ok=False)


def _webhook(url, nutzlast):
    if not re.match(r"^https?://", str(url or "")):
        raise Fehler("Webhook: Adresse muss mit http:// oder https:// beginnen.")
    req = urllib.request.Request(url, data=json.dumps(nutzlast, ensure_ascii=False).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": f"SparteNet-Manager/{VERSION}"})
    with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as r:
        return r.status


def email_vorlagen(d):
    return [v for v in (d.get("email_vorlagen") or []) if isinstance(v, dict) and v.get("id")]


def email_inhalt(d, aktion):
    """(Betreff, HTML) einer E-Mail-Aktion – aus der gewählten Vorlage oder eigenem Text"""
    v = next((x for x in email_vorlagen(d) if x["id"] == aktion.get("vorlage")), None) if aktion.get("vorlage") else None
    if v:
        return aktion.get("betreff") or v.get("betreff", ""), v.get("html", "")
    return aktion.get("betreff", ""), aktion.get("html") or text_zu_html(aktion.get("text", ""))


def _hintergrund():
    while True:
        auftrag = _WARTESCHLANGE.get()
        art, regel, daten, aktion = auftrag
        try:
            d = lade()
            werte = _platzhalter_werte(daten, d)
            if art == "email":
                an = _ersetzen(aktion.get("an"), werte)
                if aktion.get("an_kunde") and werte.get("email"):
                    an = ", ".join(x for x in (an, werte["email"]) if x)
                betreff, inhalt = email_inhalt(d, aktion)
                gesendet = email_senden(d, an, _ersetzen(betreff, werte), None, _ersetzen(inhalt, werte, html=True))
                verlauf_schreiben({"regel": regel, "aktion": "E-Mail", "ok": True, "text": f"an {gesendet}"})
            elif art == "webhook":
                st = _webhook(aktion.get("url"), {"ereignis": daten.get("ereignis"), "daten": {k: v for k, v in daten.items() if k != "passwort"},
                                                  "regel": regel, "zeit": time.strftime("%Y-%m-%dT%H:%M:%S")})
                verlauf_schreiben({"regel": regel, "aktion": "Webhook", "ok": True, "text": f"{aktion.get('url')} → {st}"})
        except Exception as e:
            verlauf_schreiben({"regel": regel, "aktion": AKTIONEN.get(art, art), "ok": False, "text": text_einzeilig(str(e), 300)})
            LOG.warning("Automation „%s“ (%s) fehlgeschlagen: %s", regel, art, e)
        finally:
            _WARTESCHLANGE.task_done()


def automation_verarbeiten(typ, daten, d, probe=False):
    """führt alle passenden Regeln aus; gibt eine Liste der Ergebnisse zurück"""
    if d is None:
        d = lade()
    daten = {**daten, "ereignis": typ}
    tiefe = getattr(_TIEFE, "n", 0)
    if tiefe >= 3:
        LOG.warning("Automation: Ereignis %s nach 3 Ebenen nicht mehr ausgeführt (Schleife?)", typ)
        return []
    daten.setdefault("quelle", getattr(ANFRAGE, "benutzer", None) or "admin")
    folge = []      # Ereignisse, die eigene Aktionen auslösen (z. B. „Tarif buchen“ → „Buchung“)
    ergebnisse = []
    regeln = [r for r in automation_daten(d)["regeln"] if _passt(r, typ, daten)]
    for r in regeln:
        werte = _platzhalter_werte(daten, d)
        for a in r.get("aktionen") or []:
            art = a.get("typ")
            try:
                if art in ("email", "webhook"):
                    if probe:
                        ergebnisse.append({"regel": r["name"], "aktion": AKTIONEN[art], "ok": True, "text": "(Probe – nicht gesendet) " + (
                            f"an {_ersetzen(a.get('an'), werte)}{' + Kunde (' + (werte.get('email') or 'ohne Adresse') + ')' if a.get('an_kunde') else ''}: {_ersetzen(email_inhalt(d, a)[0], werte)}" if art == "email" else a.get("url", ""))})
                    else:
                        _WARTESCHLANGE.put_nowait((art, r["name"], daten, a))
                        ergebnisse.append({"regel": r["name"], "aktion": AKTIONEN[art], "ok": True, "text": "in Warteschlange"})
                elif art in ("buchen", "buchung_entfernen"):
                    kz, p = str(daten.get("sparte") or ""), daten.get("parzelle")
                    tarif = _ersetzen(a.get("tarif") or "{tarif}", werte) if art == "buchen" else ""
                    if not kz or not str(p or "").isdigit():
                        raise Fehler("Sparte und Parzelle fehlen im Ereignis.")
                    if art == "buchen" and tarif not in {t["name"] for t in tarife_pruefen(d["tarife"])}:
                        raise Fehler(f"Tarif „{tarif}“ gibt es nicht.")
                    if not probe:
                        b = d.setdefault("buchungen", {}).setdefault(kz, {})
                        alt = b.get(str(int(p)), "")
                        if alt != tarif:
                            folge.append(("buchung" if tarif else "kuendigung", {"sparte": kz, "parzelle": int(p), "tarif": tarif, "tarif_alt": alt,
                                                                                 "email": daten.get("email", ""), "name": daten.get("name", ""),
                                                                                 "quelle": f"Automation „{r['name']}“"}))
                        if tarif:
                            b[str(int(p))] = tarif
                        else:
                            b.pop(str(int(p)), None)
                        d["buchungen"] = {k: v for k, v in d["buchungen"].items() if v}
                        speichere(d)
                        journal(f"Automation „{r['name']}“: {kz} Parzelle {p} → {tarif or 'Buchung entfernt'}")
                    ergebnisse.append({"regel": r["name"], "aktion": AKTIONEN[art], "ok": True, "text": f"{kz} Parzelle {p} → {tarif or 'entfernt'}"})
                elif art in AKTION_ERWEITERUNG:
                    text = AKTION_ERWEITERUNG[art](d, daten, a, werte, probe, r["name"])
                    ergebnisse.append({"regel": r["name"], "aktion": AKTIONEN[art], "ok": True, "text": text})
                elif art == "protokoll":
                    t = _ersetzen(a.get("text") or "Automation „{ereignis}“", werte)
                    if not probe:
                        journal(f"Automation „{r['name']}“: {t}")
                    ergebnisse.append({"regel": r["name"], "aktion": AKTIONEN[art], "ok": True, "text": t})
            except queue.Full:
                ergebnisse.append({"regel": r["name"], "aktion": AKTIONEN.get(art, art), "ok": False, "text": "Warteschlange voll"})
            except Exception as e:
                ergebnisse.append({"regel": r["name"], "aktion": AKTIONEN.get(art, art), "ok": False, "text": str(e)})
        if not probe:
            r["zuletzt"] = time.strftime("%Y-%m-%d %H:%M")
    if regeln and not probe:
        speichere(d)
        for e in ergebnisse:
            if e["aktion"] not in (AKTIONEN["email"], AKTIONEN["webhook"]) or not e["ok"]:
                verlauf_schreiben(e)
    if folge:
        _TIEFE.n = tiefe + 1
        try:
            for t, x in folge:
                ereignis(t, x, d)      # Gateway-Zuteilung und Automationen dieser Folge-Buchung
        finally:
            _TIEFE.n = tiefe
    return ergebnisse


def _empfaenger(typ, daten, d):
    automation_verarbeiten(typ, daten, d)


EREIGNIS_EMPFAENGER.append(_empfaenger)
threading.Thread(target=_hintergrund, daemon=True, name="automation").start()


def _regel_pruefen(r, d):
    if not isinstance(r, dict):
        raise Fehler("Ungültige Regel.")
    aus = {"id": str(r.get("id") or secrets.token_hex(6)), "name": text_einzeilig(r.get("name") or "Neue Regel", 80), "aktiv": bool(r.get("aktiv", True))}
    if r.get("ausloeser") not in AUSLOESER:
        raise Fehler("Bitte einen Auslöser wählen.")
    aus["ausloeser"] = r["ausloeser"]
    aus["ereignis_name"] = re.sub(r"[^a-z0-9_.-]", "", str(r.get("ereignis_name") or "").lower())[:40]
    b = r.get("bedingung") or {}
    bm = b.get("betrag_min")
    aus["bedingung"] = {"sparte": str(b.get("sparte") or "").upper()[:10], "tarif": str(b.get("tarif") or "")[:40],
                        "betrag_min": (float(str(bm).replace(",", ".")) if bm not in (None, "") else None)}
    aktionen = []
    for a in (r.get("aktionen") or [])[:10]:
        art = a.get("typ")
        if art not in AKTIONEN:
            raise Fehler("Unbekannte Aktion.")
        x = {"typ": art}
        if art == "email":
            x.update(an=str(a.get("an") or "")[:300], an_kunde=bool(a.get("an_kunde")), betreff=str(a.get("betreff") or "")[:200],
                     vorlage=str(a.get("vorlage") or "")[:24], html=html_bereinigen(a["html"]) if a.get("html") else "", text=str(a.get("text") or "")[:5000])
            if x["vorlage"] and not any(v["id"] == x["vorlage"] for v in email_vorlagen(d)):
                raise Fehler("E-Mail: die gewählte Vorlage gibt es nicht mehr.")
            if not x["an"] and not x["an_kunde"]:
                raise Fehler("E-Mail: Empfänger angeben oder „an den Kunden“ wählen.")
            for adr in re.split(r"[,;\s]+", _ersetzen(x["an"], {})):
                if adr and "{" not in adr and not _EMAIL_RE.match(adr):
                    raise Fehler(f"Ungültige E-Mail-Adresse: {adr}")
        elif art == "buchen":
            x["tarif"] = str(a.get("tarif") or "{tarif}")[:40]
        elif art == "webhook":
            x["url"] = str(a.get("url") or "")[:500]
            if not re.match(r"^https?://[^\s]+$", x["url"]):
                raise Fehler("Webhook: Adresse muss mit http:// oder https:// beginnen.")
        elif art == "protokoll":
            x["text"] = text_einzeilig(a.get("text") or "", 300)
        aktionen.append(x)
    if not aktionen:
        raise Fehler("Bitte mindestens eine Aktion hinzufügen.")
    aus["aktionen"] = aktionen
    return aus


def akt_automation(d, mit_smtp=True):
    a = automation_daten(d)
    s = smtp_einstellungen(d)
    return {"regeln": a["regeln"], "ausloeser": AUSLOESER, "aktionen": AKTIONEN, "platzhalter": PLATZHALTER, "vorlagen": email_vorlagen(d),
            "smtp": {**s, "passwort_gesetzt": bool(_smtp_passwort(d)), "passwort_aus_datei": bool(_SMTP_PW_DATEI)} if mit_smtp else None,
            "tarife": [t["name"] for t in tarife_pruefen(d["tarife"])], "verlauf": verlauf_lesen()[:100], "warteschlange": _WARTESCHLANGE.qsize(), "log": []}


def akt_automation_speichern(d, b, ich):
    a = automation_daten(d)
    r = _regel_pruefen(b.get("regel"), d)
    alt = next((x for x in a["regeln"] if x["id"] == r["id"]), None)
    if alt:
        r["zuletzt"] = alt.get("zuletzt")
        a["regeln"][a["regeln"].index(alt)] = r
    else:
        a["regeln"].append(r)
    speichere(d)
    journal(f"Automation {'geändert' if alt else 'angelegt'}: {r['name']} ({AUSLOESER[r['ausloeser']]}) durch {ich}")
    x = akt_automation(d)
    x["log"] = [f"✔ Regel „{r['name']}“ gespeichert."]
    return x


def akt_automation_loeschen(d, b, ich):
    a = automation_daten(d)
    r = next((x for x in a["regeln"] if x["id"] == str(b.get("id"))), None)
    if not r:
        raise Fehler("Regel nicht gefunden.")
    a["regeln"].remove(r)
    speichere(d)
    journal(f"Automation gelöscht: {r['name']} durch {ich}")
    x = akt_automation(d)
    x["log"] = [f"✔ Regel „{r['name']}“ gelöscht."]
    return x


def akt_automation_probe(d, b):
    """Probelauf mit Beispieldaten: zeigt, was passieren würde – sendet nichts, bucht nichts"""
    typ = b.get("ausloeser") or "buchung"
    daten = {"sparte": str(b.get("sparte") or "BW"), "parzelle": int(b.get("parzelle") or 1), "tarif": b.get("tarif") or "Basic", "tarif_alt": "",
             "betrag": b.get("betrag") or "120.00", "referenz": "TEST-123", "email": "kunde@example.org", "name": "Max Mustermann",
             "ereignis_name": b.get("ereignis_name") or ""}
    e = automation_verarbeiten(typ, daten, d, probe=True)
    return {"ergebnisse": e, "log": [f"Probelauf „{AUSLOESER.get(typ, typ)}“: {len(e)} Aktion(en) – nichts gesendet, nichts gebucht."] if e else ["Keine aktive Regel passt zu diesem Probelauf."]}


def akt_smtp_speichern(d, b, ich):
    s = smtp_einstellungen(d)
    for k in ("host", "benutzer", "absender", "absender_name"):
        if k in b:
            s[k] = text_einzeilig(b[k], 200).strip()
    if "port" in b:
        try:
            s["port"] = max(1, min(65535, int(b["port"])))
        except (TypeError, ValueError):
            raise Fehler("Port: Zahl 1–65535.")
    if b.get("sicherheit") in ("starttls", "ssl", "keine"):
        s["sicherheit"] = b["sicherheit"]
    if b.get("anmeldung") in SMTP_ANMELDUNG:
        s["anmeldung"] = b["anmeldung"]
    if s["absender"] and not _EMAIL_RE.match(s["absender"]):
        raise Fehler("Absender ist keine gültige E-Mail-Adresse.")
    alt = d.get("smtp") if isinstance(d.get("smtp"), dict) else {}
    if b.get("passwort"):
        s["passwort"] = str(b["passwort"])
    elif alt.get("passwort"):
        s["passwort"] = alt["passwort"]
    d["smtp"] = s
    speichere(d)
    journal(f"E-Mail-Versand eingestellt: {s['host']}:{s['port']} ({s['sicherheit']}, Anmeldung {s['anmeldung']}) durch {ich}")
    x = akt_automation(d)
    x["log"] = ["✔ E-Mail-Versand gespeichert."]
    return x


def akt_smtp_test(d, b):
    an = email_senden(d, b.get("an"), "SparteNet: Test-E-Mail", f"Diese Test-E-Mail kommt vom SparteNet Manager {VERSION}.\nDer E-Mail-Versand für Automationen funktioniert.")
    return {"log": [f"✔ Test-E-Mail an {an} gesendet."]}


def akt_email_layout(d, b=None):
    if b is not None:
        roh = dict(d.get("email_layout") or {})
        for k in LAYOUT_STANDARD:
            if k in b:
                roh[k] = b[k]
        d["email_layout"] = roh
        d["email_layout"] = email_layout(d)
        speichere(d)
        journal("E-Mail-Layout gespeichert")
    return {"layout": email_layout(d), "standard": LAYOUT_STANDARD, "logo": bool(_logo_teil(d)), "vorlagen": email_vorlagen(d),
            "log": ["✔ E-Mail-Layout gespeichert."] if b is not None else []}


def akt_email_vorschau(d, b):
    werte = _platzhalter_werte({"sparte": "BW", "parzelle": 12, "tarif": "Basic", "betrag": "120.00", "referenz": "RE-2026-0042", "name": "Max Mustermann",
                                "vorname": "Max", "nachname": "Mustermann", "email": "max@example.org", "ticket": "T-0007", "betreff": "WLAN geht nicht",
                                "status": "in Bearbeitung"}, d)
    werte["wlan"] = werte.get("wlan") or "SparteNet.de-BW-Pächter"
    werte["passwort"] = werte.get("passwort") or "SN1234567890"
    werte["vorname"], werte["nachname"] = werte.get("vorname") or "Max", werte.get("nachname") or "Mustermann"
    inhalt = html_bereinigen(b.get("html") or "") or "<p>Beispieltext</p>"
    logo = _logo_teil(d)
    src = f"data:image/{logo[1]};base64,{base64.b64encode(logo[0]).decode()}" if logo else None
    if b.get("layout"):
        alt = d.get("email_layout")
        d["email_layout"] = {**(alt or {}), **{k: v for k, v in b["layout"].items() if k in LAYOUT_STANDARD}}
        try:
            h = email_html(d, _ersetzen(inhalt, werte, html=True), _ersetzen(b.get("betreff", ""), werte), src)
        finally:
            d["email_layout"] = alt
    else:
        h = email_html(d, _ersetzen(inhalt, werte, html=True), _ersetzen(b.get("betreff", ""), werte), src)
    return {"html": h, "betreff": _ersetzen(b.get("betreff", ""), werte), "log": []}


def akt_email_vorlage_speichern(d, b, ich):
    v = b.get("vorlage") or {}
    name = text_einzeilig(v.get("name") or "", 60).strip()
    if not name:
        raise Fehler("Bitte einen Namen für die Vorlage angeben.")
    liste = email_vorlagen(d)
    vid = re.sub(r"[^a-z0-9]", "", str(v.get("id") or "").lower())[:24] or secrets.token_hex(5)
    neu = {"id": vid, "name": name, "betreff": text_einzeilig(v.get("betreff") or "", 200), "html": html_bereinigen(v.get("html") or "")}
    if not neu["html"]:
        raise Fehler("Die Vorlage hat keinen Text.")
    liste = [x for x in liste if x["id"] != vid] + [neu]
    if len(liste) > 50:
        raise Fehler("Höchstens 50 E-Mail-Vorlagen.")
    d["email_vorlagen"] = sorted(liste, key=lambda x: x["name"].lower())
    speichere(d)
    journal(f"E-Mail-Vorlage gespeichert: {name} durch {ich}")
    return {"vorlagen": d["email_vorlagen"], "id": vid, "log": [f"✔ Vorlage „{name}“ gespeichert."]}


def akt_email_vorlage_loeschen(d, b, ich):
    vid = str(b.get("id") or "")
    benutzt = [r["name"] for r in automation_daten(d)["regeln"] if any(a.get("vorlage") == vid for a in r.get("aktionen") or [])]
    if benutzt:
        raise Fehler("Die Vorlage wird noch in Regeln benutzt: " + ", ".join(benutzt[:5]))
    d["email_vorlagen"] = [x for x in email_vorlagen(d) if x["id"] != vid]
    speichere(d)
    journal(f"E-Mail-Vorlage gelöscht durch {ich}")
    return {"vorlagen": d["email_vorlagen"], "log": ["✔ Vorlage gelöscht."]}


def akt_email_test(d, b):
    an = email_senden(d, b.get("an"), "SparteNet: Test mit Layout",
                      None, _ersetzen(html_bereinigen(b.get("html") or "") or "<h2>Hallo!</h2><p>So sehen E-Mails vom SparteNet Manager aus.</p>",
                                      _platzhalter_werte({"sparte": "BW", "parzelle": 12, "tarif": "Basic"}, d), html=True))
    return {"log": [f"✔ Test-E-Mail mit Layout an {an} gesendet."]}


def akt_automation_ausloesen(typ, daten):
    """für die API: Ereignis auslösen und Ergebnisse zurückgeben"""
    return automation_verarbeiten(typ, daten, lade())


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

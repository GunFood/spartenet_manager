"""SparteNet Manager – Pächter-Seite (/portal): Anfrage stellen, Ticket-Status abfragen, Zugangskarte neu anfordern

Öffentlich ohne Anmeldung – deshalb eingeschaltet erst durch einen Administrator, mit Grenzen je Absender und Parzelle.
Die Zugangskarte geht nur per E-Mail an die beim Mitglied hinterlegte Adresse; die Seite zeigt nie ein Passwort und verrät nicht,
ob Angaben stimmen.
Anfragen von Mitgliedern nur, wenn Vorname, Nachname, E-Mail, Sparte und Parzelle zu einem gespeicherten Mitglied passen
(Groß-/Kleinschreibung egal, ä = ae, ß = ss). Nicht-Mitglieder und Interessenten können – wenn eingeschaltet – mit Name und E-Mail
anfragen; ihre Tickets sind entsprechend gekennzeichnet. Status nur mit Ticket-Nummer, Name und E-Mail (bei Mitgliedern auch Sparte und
Parzelle), Zugangskarte nur mit allen fünf Angaben eines Mitglieds.
"""
from .gestaltung import *  # noqa: F401,F403 – alle Namen der vorherigen Module

PORTAL_STANDARD = {"aktiv": False, "titel": "SparteNet – Service für Pächter", "text": "Hier können Sie eine Anfrage stellen, den Stand Ihrer Anfrage abfragen oder Ihre WLAN-Zugangskarte erneut anfordern.",
                   "ticket": True, "status": True, "zugang": True, "bestaetigung": True}
_GRENZEN = {"ticket": (10, 3600), "status": (30, 3600), "zugang": (5, 3600), "parzelle": (3, 86400), "fehlversuch": (5, 3600)}
KONTAKT_ARTEN = {"mitglied": "Mitglied", "kein_mitglied": "kein Mitglied einer Sparte", "interessent": "Interessent"}
_ZAEHLER = {}
_Z_LOCK = threading.Lock()


def portal_einstellungen(d):
    e = dict(PORTAL_STANDARD)
    roh = d.get("portal") if isinstance(d.get("portal"), dict) else {}
    for k, s in PORTAL_STANDARD.items():
        if k in roh:
            e[k] = bool(roh[k]) if isinstance(s, bool) else str(roh[k])[:1000]
    return e


def _grenze(art, schluessel):
    anzahl, fenster = _GRENZEN[art]
    jetzt = time.time()
    with _Z_LOCK:
        k = (art, schluessel)
        z = [t for t in _ZAEHLER.get(k, []) if jetzt - t < fenster]
        if len(z) >= anzahl:
            raise Fehler("Zu viele Anfragen – bitte später erneut versuchen.")
        z.append(jetzt)
        _ZAEHLER[k] = z
        if len(_ZAEHLER) > 20000:
            for kk in list(_ZAEHLER)[:5000]:
                _ZAEHLER.pop(kk, None)


def name_norm(t):
    """Vergleichsform für Namen/E-Mail: Groß-/Kleinschreibung, ä/ae, ß/ss, Bindestrich/Leerzeichen egal"""
    t = str(t or "").strip().casefold()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("é", "e"), ("è", "e"), ("-", " ")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def mitglied_passt(d, vorname, nachname, email, kz, p):
    """(id, Mitglied) wenn alle fünf Angaben zu einem gespeicherten Mitglied passen, sonst (None, None)"""
    v, n, e = name_norm(vorname), name_norm(nachname), name_norm(email)
    if not (v and n and e and kz and str(p).strip().isdigit()):
        return None, None
    for i, m in mitglieder(d).items():
        if (m.get("sparte") == str(kz).upper() and str(m.get("parzelle")) == str(int(p)) and name_norm(m.get("vorname")) == v
                and name_norm(m.get("nachname")) == n and name_norm(m.get("email")) == e):
            return i, m
    return None, None


def _fehlversuch(kz, p, quelle):
    """nach 5 falschen Versuchen je Parzelle bzw. Absender und Stunde gesperrt (gegen Ausprobieren)"""
    _grenze("fehlversuch", f"{kz}-{p}")
    _grenze("fehlversuch", quelle)


def _fehlversuche_voll(kz, p, quelle):
    jetzt = time.time()
    anzahl, fenster = _GRENZEN["fehlversuch"]
    with _Z_LOCK:
        return any(len([t for t in _ZAEHLER.get(("fehlversuch", k), []) if jetzt - t < fenster]) >= anzahl for k in (f"{kz}-{p}", quelle))


def akt_portal_einstellungen(d, b=None, ich=""):
    if b is not None:
        e = portal_einstellungen(d)
        for k, s in PORTAL_STANDARD.items():
            if k in b:
                e[k] = bool(b[k]) if isinstance(s, bool) else text_einzeilig(b[k], 1000 if k == "text" else 120)
        d["portal"] = e
        speichere(d)
        journal(f"Pächter-Seite {'eingeschaltet' if e['aktiv'] else 'ausgeschaltet'} durch {ich}")
    return {"einstellungen": portal_einstellungen(d), "log": ["✔ Gespeichert."] if b is not None else []}


def portal_info(d):
    return portal_info_aus(d, seiten_design(d, "portal"))


def portal_anfrage(pfad, b, quelle):
    """öffentliche Anfragen; gibt (HTTP-Status, Antwort) zurück"""
    d = lade()
    e = portal_einstellungen(d)
    if not e["aktiv"]:
        return 404, {"fehler": "Die Pächter-Seite ist nicht eingeschaltet."}
    try:
        if pfad == "/portal/info":
            return 200, portal_info(d)
        if not isinstance(b, dict):
            raise Fehler("Ungültige Anfrage.")
        if b.get("website"):                    # Falle für Formular-Roboter
            return 200, {"ok": True, "text": "Danke!"}
        if pfad == "/portal/ticket" and e["ticket"]:
            _grenze("ticket", quelle)
            ds = seiten_design(d, "portal")
            if ds["spamschutz"]:
                spam_pruefen(b)
            art = str(b.get("art") or "mitglied")
            if art not in KONTAKT_ARTEN or (art == "kein_mitglied" and not ds["art_kein_mitglied"]) or (art == "interessent" and not ds["art_interessent"]):
                art = "mitglied"
            vorname, nachname = text_einzeilig(b.get("vorname") or "", 60).strip(), text_einzeilig(b.get("nachname") or "", 60).strip()
            email = str(b.get("email") or "").strip()
            kz, p = str(b.get("sparte") or "").upper(), str(b.get("parzelle") or "").strip()
            if not (vorname and nachname and email):
                raise Fehler("Bitte Vorname, Nachname und E-Mail-Adresse angeben.")
            mid = None
            if art == "mitglied":
                if not (kz and p.isdigit()):
                    raise Fehler("Bitte Ihre Sparte und Parzellennummer angeben.")
                if _fehlversuche_voll(kz, p, quelle):
                    raise Fehler("Zu viele Versuche – bitte später erneut versuchen oder den Vorstand kontaktieren.")
                mid, m = mitglied_passt(d, vorname, nachname, email, kz, p)
                if not mid:
                    _fehlversuch(kz, p, quelle)
                    LOG.info("Pächter-Seite: Anfrage %s-%s abgelehnt – Angaben passen zu keinem Mitglied", kz, p)
                    raise Fehler("Die Angaben passen nicht zu unseren Mitgliedsdaten. Bitte Vorname, Nachname, E-Mail-Adresse, Sparte und Parzelle prüfen"
                                 + (f" – oder wenden Sie sich an: {ds['kontakt']}" if ds["kontakt"] else " oder den Vorstand kontaktieren") + ".")
            roh = {k: b.get(k) for k in ("betreff", "text", "kategorie", "telefon") if b.get(k) not in (None, "")}
            roh.update(name=f"{vorname} {nachname}", email=email)
            if roh.get("kategorie") not in ticket_kategorien(d):
                roh["kategorie"] = "Interessent" if art == "interessent" and "Interessent" in ticket_kategorien(d) else "Sonstiges"
            roh["text"] = str(roh.get("text") or "")[:5000]
            if art == "mitglied":
                roh.update(sparte=kz, parzelle=p)
            else:
                if kz and kz in _sparten_kz(d):
                    roh["sparte"] = kz              # Sparte hilft bei der Zuständigkeit; Parzelle nur als Text (sonst falsche Mitglieds-Zuordnung)
                if kz or p:
                    roh["text"] = f"[{KONTAKT_ARTEN[art]} · Angabe: Sparte {kz or '–'}, Parzelle {p or '–'}]\n" + roh["text"]
                else:
                    roh["text"] = f"[{KONTAKT_ARTEN[art]}]\n" + roh["text"]
            with SCHREIB_SPERRE:
                d = lade()
                tid, t = ticket_anlegen(d, roh, "Pächter-Seite", f"Pächter-Seite ({quelle})")
                k = t.setdefault("kontakt", {})
                k.update(vorname=vorname, nachname=nachname, art=art, geprueft=bool(mid))
                if mid:
                    k["mitglied"] = mid
                elif art != "mitglied":
                    k.pop("mitglied", None)
                speichere(d)
            if e["bestaetigung"]:
                try:
                    email_senden(d, t["kontakt"]["email"], f"[{t['nr']}] Ihre Anfrage: {t['betreff']}", None,
                                 f"<p>Hallo {html_mod.escape(vorname)} {html_mod.escape(nachname)},</p><p>vielen Dank – Ihre Anfrage ist bei uns eingegangen und hat die Nummer <b>{t['nr']}</b>. "
                                 f"Wir melden uns so bald wie möglich.</p><p>Den Stand können Sie jederzeit auf der Pächter-Seite mit Ticket-Nummer, Name und E-Mail-Adresse abfragen.</p>")
                except Exception as f:
                    LOG.warning("Bestätigung zu %s nicht gesendet: %s", t["nr"], f)
            return 200, {"ok": True, "ticket": t["nr"], "text": ds["danke"].replace("{nr}", t["nr"])}
        if pfad == "/portal/status" and e["status"]:
            _grenze("status", quelle)
            nr = str(b.get("nr") or "").strip().upper()
            em, vn, nn = name_norm(b.get("email")), name_norm(b.get("vorname")), name_norm(b.get("nachname"))
            t = next((t for t in tickets_daten(d)["liste"].values() if t.get("nr") == nr), None)
            k = (t or {}).get("kontakt") or {}
            name_t = name_norm(f"{k.get('vorname', '')} {k.get('nachname', '')}") if k.get("nachname") else name_norm(k.get("name"))
            ok = bool(t and em and vn and nn and name_norm(k.get("email")) == em and name_t == f"{vn} {nn}")
            if ok and k.get("art", "mitglied") == "mitglied" and t.get("parzelle"):
                ok = str(b.get("sparte") or "").upper() == t.get("sparte") and str(b.get("parzelle") or "").strip() == str(t.get("parzelle"))
            if not ok:
                raise Fehler("Kein Ticket mit diesen Angaben gefunden. Bitte Ticket-Nummer, Vorname, Nachname und E-Mail-Adresse prüfen"
                             " (bei Anfragen als Mitglied auch Sparte und Parzelle).")
            antworten = [{"zeit": v["zeit"], "text": v["text"].split("\n", 1)[-1]} for v in t.get("verlauf") or [] if v["art"] == "antwort"]
            return 200, {"ticket": t["nr"], "betreff": t.get("betreff", ""), "status": T_STATUS.get(t.get("status"), ""), "erstellt": t.get("erstellt"),
                         "geaendert": t.get("geaendert"), "antworten": antworten[-10:]}
        if pfad == "/portal/zugang" and e["zugang"]:
            _grenze("zugang", quelle)
            kz = str(b.get("sparte") or "").upper()
            p = str(b.get("parzelle") or "").strip()
            em = str(b.get("email") or "").strip().lower()
            antwort = {"ok": True, "text": "Wenn die Angaben zu einem Mitglied passen, ist die Zugangskarte jetzt per E-Mail an die hinterlegte Adresse unterwegs."}
            if not (kz and p.isdigit() and em and str(b.get("vorname") or "").strip() and str(b.get("nachname") or "").strip()):
                raise Fehler("Bitte Vorname, Nachname, E-Mail-Adresse, Sparte und Parzelle angeben.")
            _grenze("parzelle", f"{kz}-{p}")
            mid, m = mitglied_passt(d, b.get("vorname"), b.get("nachname"), em, kz, p)
            if not m:
                LOG.info("Pächter-Seite: Zugangskarte %s-%s angefordert – Angaben passen nicht", kz, p)
                return 200, antwort
            z = next((z for z in lese_ppsk(kz) if str(z.get("Parzelle")) == p and z.get("Passwort")), None)
            if not z or not ((d.get("buchungen") or {}).get(kz) or {}).get(p):
                LOG.info("Pächter-Seite: Zugangskarte %s-%s – kein Passwort oder keine Buchung", kz, p)
                return 200, antwort
            zeile = {**z, "WLAN": wlan_ssid(d, kz)}
            name = _sparten_kz(d).get(kz, kz)
            karte = zugangskarte_pdf(d, kz, zeile, name)
            email_senden(d, m["email"], f"Ihre WLAN-Zugangskarte für Parzelle {p}", None,
                         f"<p>Hallo {html_mod.escape(m.get('vorname') or '')},</p><p>anbei Ihre WLAN-Zugangskarte für Parzelle {p} ({html_mod.escape(name)}).</p>"
                         f"<p>WLAN: <b>{html_mod.escape(zeile['WLAN'])}</b><br>Den QR-Code auf der Karte mit der Handy-Kamera scannen – das Handy verbindet sich automatisch.</p>"
                         "<p>Bitte vertraulich behandeln. Haben Sie die Karte nicht angefordert, melden Sie sich bitte bei uns.</p>",
                         anhaenge=[(f"Zugangskarte_Parzelle_{p}.pdf", karte, "application/pdf")])
            journal(f"Pächter-Seite: Zugangskarte {kz} Parzelle {p} an hinterlegte E-Mail gesendet")
            return 200, antwort
        return 404, {"fehler": "Diese Funktion ist nicht eingeschaltet."}
    except Fehler as f:
        return 400, {"fehler": str(f)}
    except Exception:
        ref = secrets.token_hex(3)
        LOG.error("Pächter-Seite Fehler %s:\n%s", ref, traceback.format_exc())
        return 500, {"fehler": f"Es ist ein Fehler aufgetreten (Nr. {ref}). Bitte später erneut versuchen."}


PORTAL_HTML = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Service für Pächter</title><meta name="robots" content="noindex"><link rel="icon" href="/favicon.png">
<style>:root{--m:#5d6b75;--l:#d9e0d6;__VARS__}
__DUNKEL__
*{box-sizing:border-box}body{margin:0;font-family:var(--schrift);background:var(--bg);color:var(--t)}
body.mitbild{background:linear-gradient(rgba(0,0,0,var(--abdunkeln)),rgba(0,0,0,var(--abdunkeln))),__HG__ center/cover fixed no-repeat,var(--bg)}
header{background:var(--k);color:var(--kt);padding:18px 20px;text-align:center}header .mk{display:inline-flex;align-items:center;gap:12px}header img{height:46px;max-width:140px;object-fit:contain;background:#fff;border-radius:10px;padding:3px}
header b{font-size:22px}header b span{color:var(--a);filter:brightness(1.25)}#titel{opacity:.88;margin-top:4px}
main{max-width:var(--breite);margin:0 auto;padding:18px 16px 30px}.karte{background:var(--c);border:1px solid var(--l);border-radius:var(--ecken);padding:18px;margin-bottom:16px}
#einl{background:var(--c);border-radius:var(--ecken);padding:12px 16px}body:not(.mitbild) #einl{background:none;padding:0}
nav{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0}nav button{flex:1;min-width:150px;border:1px solid var(--l);background:var(--c);color:var(--t);padding:12px;border-radius:calc(var(--ecken) * .8);font-size:15px;cursor:pointer;font-family:inherit}
nav button.aktiv{border-color:var(--a);box-shadow:inset 0 -3px 0 var(--a);font-weight:600}label{display:block;font-size:13px;color:var(--m);margin:12px 0 4px}
input,select,textarea{width:100%;padding:11px;border:1px solid var(--l);border-radius:calc(var(--ecken) * .65);font:inherit;background:var(--c);color:var(--t)}textarea{min-height:120px}
.r{display:grid;grid-template-columns:1fr 1fr;gap:10px}@media(max-width:480px){.r{grid-template-columns:1fr}}
.arten{display:grid;gap:6px;margin:4px 0 6px}.arten label{display:flex;gap:8px;align-items:center;margin:0;color:var(--t);font-size:14.5px;border:1px solid var(--l);border-radius:calc(var(--ecken) * .65);padding:9px 11px;cursor:pointer}
.arten input{width:auto;margin:0;accent-color:var(--a)}
button.los{margin-top:16px;width:100%;background:var(--a);color:#fff;border:0;border-radius:calc(var(--ecken) * .8);padding:14px;font-size:16px;font-weight:600;cursor:pointer;font-family:inherit}button.los:disabled{opacity:.6}
.hint{color:var(--m);font-size:14px;line-height:1.45}.msg{margin-top:14px;padding:12px;border-radius:8px;display:none;white-space:pre-wrap}.msg.ok{display:block;background:#e7f3e1;color:#24661a}.msg.f{display:block;background:#fde8e6;color:#b42318}
.versteckt{position:absolute;left:-9999px}section{display:none}section.aktiv{display:block}.antwort{border-left:3px solid var(--a);padding:6px 10px;margin:8px 0;white-space:pre-wrap}
.pflicht::after{content:" *"}footer{max-width:var(--breite);margin:0 auto;padding:0 16px 30px;font-size:13px;color:var(--m);text-align:center;line-height:1.6}footer a{color:var(--a)}
body.mitbild footer{color:#eee}</style></head>
<body class="__MITBILD__"><header><div class="mk">__LOGO__<b>__MARKE__</b></div><div id="titel"></div></header><main>
<p class="hint" id="einl"></p><nav id="nav"></nav>
<section id="s_ticket" class="karte"><h2 style="margin-top:0" id="h_ticket"></h2><p class="hint" id="x_ticket"></p>
<div class="arten" id="t_arten"></div>
<div class="r"><div><label for="t_vorname" class="pflicht">Vorname</label><input id="t_vorname" autocomplete="given-name"></div><div><label for="t_nachname" class="pflicht">Nachname</label><input id="t_nachname" autocomplete="family-name"></div></div>
<div class="r"><div><label for="t_email" class="pflicht">E-Mail</label><input id="t_email" type="email" autocomplete="email"></div><div><label for="t_tel">Telefon</label><input id="t_tel" type="tel" autocomplete="tel"></div></div>
<div class="r"><div><label for="t_sparte" id="l_sparte" class="pflicht">Sparte</label><select id="t_sparte"></select></div><div><label for="t_parzelle" id="l_parzelle" class="pflicht">Parzelle</label><input id="t_parzelle" inputmode="numeric"></div></div>
<label for="t_kat">Worum geht es?</label><select id="t_kat"></select>
<label for="t_betreff" class="pflicht">Betreff</label><input id="t_betreff" maxlength="160"><label for="t_text">Ihre Nachricht</label><textarea id="t_text" maxlength="5000"></textarea>
<div id="t_spam"><label for="t_antwort" class="pflicht" id="l_frage">Kurze Rechenaufgabe</label><input id="t_antwort" inputmode="numeric" autocomplete="off" style="max-width:160px"></div>
<input class="versteckt" id="t_web" tabindex="-1" autocomplete="off" aria-hidden="true"><button class="los" onclick="senden('ticket')">Anfrage senden</button><div class="msg" id="m_ticket"></div></section>
<section id="s_status" class="karte"><h2 style="margin-top:0" id="h_status"></h2><p class="hint" id="x_status"></p>
<div class="r"><div><label for="s_nr" class="pflicht">Ticket-Nummer</label><input id="s_nr" placeholder="T-0001"></div><div><label for="s_email" class="pflicht">E-Mail aus der Anfrage</label><input id="s_email" type="email"></div></div>
<div class="r"><div><label for="s_vorname" class="pflicht">Vorname</label><input id="s_vorname"></div><div><label for="s_nachname" class="pflicht">Nachname</label><input id="s_nachname"></div></div>
<div class="r"><div><label for="s_sparte">Sparte (bei Anfrage als Mitglied)</label><select id="s_sparte"></select></div><div><label for="s_parzelle">Parzelle (bei Anfrage als Mitglied)</label><input id="s_parzelle" inputmode="numeric"></div></div>
<button class="los" onclick="senden('status')">Abfragen</button><div class="msg" id="m_status"></div><div id="s_aus"></div></section>
<section id="s_zugang" class="karte"><h2 style="margin-top:0" id="h_zugang"></h2><p class="hint" id="x_zugang"></p>
<div class="r"><div><label for="z_vorname" class="pflicht">Vorname</label><input id="z_vorname" autocomplete="given-name"></div><div><label for="z_nachname" class="pflicht">Nachname</label><input id="z_nachname" autocomplete="family-name"></div></div>
<div class="r"><div><label for="z_sparte" class="pflicht">Sparte</label><select id="z_sparte"></select></div><div><label for="z_parzelle" class="pflicht">Parzelle</label><input id="z_parzelle" inputmode="numeric"></div></div>
<label for="z_email" class="pflicht">Ihre hinterlegte E-Mail-Adresse</label><input id="z_email" type="email" autocomplete="email">
<button class="los" onclick="senden('zugang')">Zugangskarte senden</button><div class="msg" id="m_zugang"></div></section></main>
<footer>__FUSS__</footer>
<script>const $=i=>document.getElementById(i),esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));let INFO=null;
function zeige(id){document.querySelectorAll("section").forEach(s=>s.classList.toggle("aktiv",s.id=="s_"+id));document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("aktiv",b.dataset.id==id))}
function art(){const r=document.querySelector("input[name=t_art]:checked");return r?r.value:"mitglied"}
function artGeaendert(){const m=art()=="mitglied";$("l_sparte").className=m?"pflicht":"";$("l_parzelle").className=m?"pflicht":"";
 $("l_sparte").textContent=m?"Sparte":"Sparte (falls vorhanden / gewünscht)";$("l_parzelle").textContent=m?"Parzelle":"Parzelle (falls vorhanden / gewünscht)"}
function frage(d){$("t_spam").style.display=d.frage?"block":"none";$("l_frage").textContent=d.frage||"";$("t_antwort").value="";INFO.frage_token=d.frage_token||""}
fetch("/portal/info").then(r=>r.json()).then(d=>{if(d.fehler){document.querySelector("main").innerHTML='<div class="karte">'+esc(d.fehler)+"</div>";return}INFO=d;
 document.title=d.titel;$("titel").textContent=d.titel;$("einl").textContent=d.text;const sp='<option value="">bitte wählen</option>'+d.sparten.map(s=>`<option value="${esc(s.kz)}">${esc(s.name)}</option>`).join("");
 ["t_sparte","z_sparte","s_sparte"].forEach(i=>$(i).innerHTML=sp);$("t_kat").innerHTML=d.kategorien.map(k=>`<option>${esc(k)}</option>`).join("");
 ["ticket","status","zugang"].forEach(k=>{$("h_"+k).textContent=d["t_"+k];$("x_"+k).textContent=d["h_"+k]||""});
 const arten=[["mitglied",d.t_mitglied]];if(d.art_kein_mitglied)arten.push(["kein_mitglied",d.t_kein_mitglied]);if(d.art_interessent)arten.push(["interessent",d.t_interessent]);
 $("t_arten").innerHTML=arten.length>1?arten.map(([v,t],i)=>`<label><input type="radio" name="t_art" value="${v}"${i?"":" checked"} onchange="artGeaendert()"> ${esc(t)}</label>`).join(""):"";artGeaendert();frage(d);
 const n=(d.reihenfolge||["ticket","status","zugang"]).filter(k=>d[k]).map(k=>[k,d["t_"+k]]);
 $("nav").innerHTML=n.map(([i,t])=>`<button data-id="${i}" onclick="zeige('${i}')">${esc(t)}</button>`).join("");if(n.length)zeige(n[0][0])});
async function senden(a){const m=$("m_"+a);m.className="msg";const b={ticket:{art:art(),vorname:$("t_vorname").value,nachname:$("t_nachname").value,email:$("t_email").value,sparte:$("t_sparte").value,parzelle:$("t_parzelle").value,telefon:$("t_tel").value,kategorie:$("t_kat").value,betreff:$("t_betreff").value,text:$("t_text").value,website:$("t_web").value,antwort:$("t_antwort").value,frage_token:INFO&&INFO.frage_token},
 status:{nr:$("s_nr").value,email:$("s_email").value,vorname:$("s_vorname").value,nachname:$("s_nachname").value,sparte:$("s_sparte").value,parzelle:$("s_parzelle").value},
 zugang:{vorname:$("z_vorname").value,nachname:$("z_nachname").value,sparte:$("z_sparte").value,parzelle:$("z_parzelle").value,email:$("z_email").value}}[a];
 const k=document.querySelector("#s_"+a+" button.los");k.disabled=true;try{const r=await fetch("/portal/"+a,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)});const d=await r.json();
 if(!r.ok)throw new Error(d.fehler||r.status);if(a=="status"){m.className="msg ok";m.textContent="Ticket "+d.ticket+": "+d.status+" (zuletzt geändert "+(d.geaendert||d.erstellt)+")";$("s_aus").innerHTML=d.antworten.map(x=>`<div class="antwort"><small>${esc(x.zeit)}</small><br>${esc(x.text)}</div>`).join("")}
 else{m.className="msg ok";m.textContent=d.text;if(a=="ticket"){$("t_betreff").value="";$("t_text").value=""}}}catch(e){m.className="msg f";m.textContent=e.message}
 finally{k.disabled=false;if(a=="ticket"&&INFO&&INFO.spamschutz)fetch("/portal/info").then(r=>r.json()).then(frage).catch(()=>{})}}</script></body></html>"""


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

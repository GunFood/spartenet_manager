"""SparteNet Manager – Pächter-Seite (/portal): Anfrage stellen, Ticket-Status abfragen, Zugangskarte neu anfordern

Öffentlich ohne Anmeldung – deshalb eingeschaltet erst durch einen Administrator, mit Grenzen je Absender und Parzelle.
Die Zugangskarte geht nur per E-Mail an die beim Mitglied hinterlegte Adresse; die Seite zeigt nie ein Passwort und verrät nicht,
ob Angaben stimmen. Ticket-Status nur mit Ticket-Nummer und der E-Mail-Adresse aus der Anfrage.
"""
from .laufzeit import *  # noqa: F401,F403 – alle Namen der vorherigen Module

PORTAL_STANDARD = {"aktiv": False, "titel": "SparteNet – Service für Pächter", "text": "Hier können Sie eine Anfrage stellen, den Stand Ihrer Anfrage abfragen oder Ihre WLAN-Zugangskarte erneut anfordern.",
                   "ticket": True, "status": True, "zugang": True, "bestaetigung": True}
_GRENZEN = {"ticket": (10, 3600), "status": (30, 3600), "zugang": (5, 3600), "parzelle": (3, 86400)}
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
    e = portal_einstellungen(d)
    sparten = sorted(({"kz": k, "name": n} for k, n in _sparten_kz(d).items()), key=lambda x: x["name"].lower())
    return {"titel": e["titel"], "text": e["text"], "ticket": e["ticket"], "status": e["status"], "zugang": e["zugang"], "sparten": sparten,
            "kategorien": [k for k in ticket_kategorien(d)]}


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
            if not str(b.get("email") or "").strip():
                raise Fehler("Bitte Ihre E-Mail-Adresse angeben – dorthin kommt die Antwort.")
            roh = {k: b.get(k) for k in ("betreff", "text", "kategorie", "sparte", "parzelle", "name", "email", "telefon") if b.get(k) not in (None, "")}
            if roh.get("kategorie") not in ticket_kategorien(d):
                roh["kategorie"] = "Sonstiges"
            roh["text"] = str(roh.get("text") or "")[:5000]
            with SCHREIB_SPERRE:
                d = lade()
                tid, t = ticket_anlegen(d, roh, "Pächter-Seite", f"Pächter-Seite ({quelle})")
            if e["bestaetigung"]:
                try:
                    email_senden(d, t["kontakt"]["email"], f"[{t['nr']}] Ihre Anfrage: {t['betreff']}", None,
                                 f"<p>Hallo {html_mod.escape(t['kontakt'].get('name') or '')},</p><p>vielen Dank – Ihre Anfrage ist bei uns eingegangen und hat die Nummer <b>{t['nr']}</b>. "
                                 f"Wir melden uns so bald wie möglich.</p><p>Den Stand können Sie jederzeit auf der Pächter-Seite mit Ticket-Nummer und E-Mail-Adresse abfragen.</p>")
                except Exception as f:
                    LOG.warning("Bestätigung zu %s nicht gesendet: %s", t["nr"], f)
            return 200, {"ok": True, "ticket": t["nr"], "text": f"Danke! Ihre Anfrage hat die Nummer {t['nr']}. Bitte notieren Sie die Nummer."}
        if pfad == "/portal/status" and e["status"]:
            _grenze("status", quelle)
            nr = str(b.get("nr") or "").strip().upper()
            em = str(b.get("email") or "").strip().lower()
            t = next((t for t in tickets_daten(d)["liste"].values() if t.get("nr") == nr), None)
            if not t or not em or (t.get("kontakt") or {}).get("email", "").lower() != em:
                raise Fehler("Kein Ticket mit dieser Nummer und E-Mail-Adresse gefunden.")
            antworten = [{"zeit": v["zeit"], "text": v["text"].split("\n", 1)[-1]} for v in t.get("verlauf") or [] if v["art"] == "antwort"]
            return 200, {"ticket": t["nr"], "betreff": t.get("betreff", ""), "status": T_STATUS.get(t.get("status"), ""), "erstellt": t.get("erstellt"),
                         "geaendert": t.get("geaendert"), "antworten": antworten[-10:]}
        if pfad == "/portal/zugang" and e["zugang"]:
            _grenze("zugang", quelle)
            kz = str(b.get("sparte") or "").upper()
            p = str(b.get("parzelle") or "").strip()
            em = str(b.get("email") or "").strip().lower()
            antwort = {"ok": True, "text": "Wenn die Angaben zu einem Mitglied passen, ist die Zugangskarte jetzt per E-Mail an die hinterlegte Adresse unterwegs."}
            if not (kz and p.isdigit() and em):
                raise Fehler("Bitte Sparte, Parzelle und E-Mail-Adresse angeben.")
            _grenze("parzelle", f"{kz}-{p}")
            mid, m = _mitglied_der_parzelle(d, kz, p)
            if not m or (m.get("email") or "").lower() != em:
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
<title>SparteNet – Service</title><meta name="robots" content="noindex"><link rel="icon" href="/favicon.png">
<style>:root{--a:#3a9a1f;--k:#1d2f3e;--bg:#f5f7f4;--c:#fff;--t:#1d2f3e;--m:#5d6b75;--l:#d9e0d6}
@media (prefers-color-scheme:dark){:root{--bg:#0f161c;--c:#18222a;--t:#e2e8ec;--m:#9aa9b3;--l:#2e3c46}}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--t)}
header{background:var(--k);color:#fff;padding:18px 20px;text-align:center}header b{font-size:22px}header b span{color:#6cc24a}
main{max-width:640px;margin:0 auto;padding:18px 16px 40px}.karte{background:var(--c);border:1px solid var(--l);border-radius:12px;padding:18px;margin-bottom:16px}
nav{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}nav button{flex:1;min-width:150px;border:1px solid var(--l);background:var(--c);color:var(--t);padding:12px;border-radius:10px;font-size:15px;cursor:pointer}
nav button.aktiv{border-color:var(--a);box-shadow:inset 0 -3px 0 var(--a);font-weight:600}label{display:block;font-size:13px;color:var(--m);margin:12px 0 4px}
input,select,textarea{width:100%;padding:11px;border:1px solid var(--l);border-radius:8px;font:inherit;background:var(--c);color:var(--t)}textarea{min-height:120px}
.r{display:grid;grid-template-columns:1fr 1fr;gap:10px}@media(max-width:480px){.r{grid-template-columns:1fr}}
button.los{margin-top:16px;width:100%;background:var(--a);color:#fff;border:0;border-radius:10px;padding:14px;font-size:16px;font-weight:600;cursor:pointer}button.los:disabled{opacity:.6}
.hint{color:var(--m);font-size:14px;line-height:1.45}.msg{margin-top:14px;padding:12px;border-radius:8px;display:none;white-space:pre-wrap}.msg.ok{display:block;background:#e7f3e1;color:#24661a}.msg.f{display:block;background:#fde8e6;color:#b42318}
.versteckt{position:absolute;left:-9999px}section{display:none}section.aktiv{display:block}.antwort{border-left:3px solid var(--a);padding:6px 10px;margin:8px 0;white-space:pre-wrap}</style></head>
<body><header><b>Sparte<span>Net</span></b><div id="titel" style="opacity:.85;margin-top:4px"></div></header><main>
<p class="hint" id="text"></p><nav id="nav"></nav>
<section id="s_ticket" class="karte"><h2 style="margin-top:0">Anfrage stellen</h2>
<div class="r"><div><label for="t_name">Name</label><input id="t_name" autocomplete="name"></div><div><label for="t_email">E-Mail *</label><input id="t_email" type="email" autocomplete="email"></div></div>
<div class="r"><div><label for="t_sparte">Sparte</label><select id="t_sparte"></select></div><div><label for="t_parzelle">Parzelle</label><input id="t_parzelle" inputmode="numeric"></div></div>
<div class="r"><div><label for="t_tel">Telefon</label><input id="t_tel" type="tel" autocomplete="tel"></div><div><label for="t_kat">Worum geht es?</label><select id="t_kat"></select></div></div>
<label for="t_betreff">Betreff *</label><input id="t_betreff" maxlength="160"><label for="t_text">Ihre Nachricht</label><textarea id="t_text" maxlength="5000"></textarea>
<input class="versteckt" id="t_web" tabindex="-1" autocomplete="off" aria-hidden="true"><button class="los" onclick="senden('ticket')">Anfrage senden</button><div class="msg" id="m_ticket"></div></section>
<section id="s_status" class="karte"><h2 style="margin-top:0">Stand meiner Anfrage</h2><div class="r"><div><label for="s_nr">Ticket-Nummer</label><input id="s_nr" placeholder="T-0001"></div><div><label for="s_email">E-Mail aus der Anfrage</label><input id="s_email" type="email"></div></div>
<button class="los" onclick="senden('status')">Abfragen</button><div class="msg" id="m_status"></div><div id="s_aus"></div></section>
<section id="s_zugang" class="karte"><h2 style="margin-top:0">Zugangskarte erneut anfordern</h2><p class="hint">Die Karte mit WLAN-Name, Passwort und QR-Code kommt per E-Mail an die Adresse, die beim Verein für Ihre Parzelle hinterlegt ist.</p>
<div class="r"><div><label for="z_sparte">Sparte</label><select id="z_sparte"></select></div><div><label for="z_parzelle">Parzelle</label><input id="z_parzelle" inputmode="numeric"></div></div>
<label for="z_email">Ihre hinterlegte E-Mail-Adresse</label><input id="z_email" type="email" autocomplete="email">
<button class="los" onclick="senden('zugang')">Zugangskarte senden</button><div class="msg" id="m_zugang"></div></section></main>
<script>const $=i=>document.getElementById(i),esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function zeige(id){document.querySelectorAll("section").forEach(s=>s.classList.toggle("aktiv",s.id=="s_"+id));document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("aktiv",b.dataset.id==id))}
fetch("/portal/info").then(r=>r.json()).then(d=>{if(d.fehler){document.querySelector("main").innerHTML='<div class="karte">'+esc(d.fehler)+"</div>";return}
 document.title=d.titel;$("titel").textContent=d.titel;$("text").textContent=d.text;const sp='<option value="">bitte wählen</option>'+d.sparten.map(s=>`<option value="${esc(s.kz)}">${esc(s.name)}</option>`).join("");$("t_sparte").innerHTML=sp;$("z_sparte").innerHTML=sp;
 $("t_kat").innerHTML=d.kategorien.map(k=>`<option>${esc(k)}</option>`).join("");const n=[];if(d.ticket)n.push(["ticket","Anfrage stellen"]);if(d.status)n.push(["status","Stand abfragen"]);if(d.zugang)n.push(["zugang","Zugangskarte"]);
 $("nav").innerHTML=n.map(([i,t])=>`<button data-id="${i}" onclick="zeige('${i}')">${t}</button>`).join("");if(n.length)zeige(n[0][0])});
async function senden(art){const m=$("m_"+art);m.className="msg";const b={ticket:{name:$("t_name").value,email:$("t_email").value,sparte:$("t_sparte").value,parzelle:$("t_parzelle").value,telefon:$("t_tel").value,kategorie:$("t_kat").value,betreff:$("t_betreff").value,text:$("t_text").value,website:$("t_web").value},
 status:{nr:$("s_nr").value,email:$("s_email").value},zugang:{sparte:$("z_sparte").value,parzelle:$("z_parzelle").value,email:$("z_email").value}}[art];
 const k=document.querySelector("#s_"+art+" button.los");k.disabled=true;try{const r=await fetch("/portal/"+art,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)});const d=await r.json();
 if(!r.ok)throw new Error(d.fehler||r.status);if(art=="status"){m.className="msg ok";m.textContent="Ticket "+d.ticket+": "+d.status+" (zuletzt geändert "+(d.geaendert||d.erstellt)+")";$("s_aus").innerHTML=d.antworten.map(a=>`<div class="antwort"><small>${esc(a.zeit)}</small><br>${esc(a.text)}</div>`).join("")}
 else{m.className="msg ok";m.textContent=d.text;if(art=="ticket"){$("t_betreff").value="";$("t_text").value=""}}}catch(e){m.className="msg f";m.textContent=e.message}finally{k.disabled=false}}</script></body></html>"""


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

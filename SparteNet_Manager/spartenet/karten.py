"""SparteNet Manager – Zugangskarten und Gast-Voucher"""
from .system import *  # noqa: F401,F403 – alle Namen der vorherigen Module


def karten_html(design, sparte_name, kz, zeilen, drucken=True, vorschau=False):
    """Eine Seite je Eintrag. zeilen: [{"Parzelle", "WLAN", "Passwort"}] – Gast-Voucher zusätzlich mit
    "Titel", "Unter", "Fuss", "Scan" (Texte statt Kartendesign) und "Zugang" [(Bezeichnung, Wert, CSS-Klasse)]"""
    g = design_pruefen(design)
    esc = lambda t: str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    breite, hoehe = PAPIER[g["format"]]
    if g["quer"]:
        breite, hoehe = hoehe, breite
    innen_b, innen_h = breite - 2 * g["rand_mm"], hoehe - 2 * g["rand_mm"]
    qr_mm = min(g["qr_cm"] * 10, (innen_b * 0.45) if g["quer"] else (innen_b - 6), innen_h * 0.75)
    logo = logo_daten_uri(g)
    logo_html = (f'<div class="logo" style="text-align:{g["logo_pos"]}"><img src="{logo}" alt=""></div>' if logo else "")

    def txt(vorlage, z):
        t = vorlage
        for k, v in (("{sparte}", sparte_name), ("{kz}", kz), ("{parzelle}", z["Parzelle"]), ("{wlan}", z["WLAN"])):
            t = t.replace(k, str(v))
        return esc(t).replace("\n", "<br>")

    seiten = []
    for z in zeilen:
        svg = qr_svg(wlan_qr_text(z["WLAN"], z["Passwort"]), farbe=g["farbe_qr"], hintergrund=g["farbe_qr_hinter"])
        eigen = lambda k, std: (esc(z[k]).replace("\n", "<br>") if k in z else std)
        teile, qr_teil = [], []
        if g["logo_ort"] == "oben":
            teile.append(logo_html)
        if g["zeige_kopf"] and g["t_kopf"].strip():
            teile.append(f'<div class="kopf">{txt(g["t_kopf"], z)}</div>')
        if g["t_titel"].strip():
            teile.append(f'<h1>{eigen("Titel", txt(g["t_titel"], z))}</h1>')
        if g["zeige_unter"] and g["t_unter"].strip():
            teile.append(f'<p class="info">{eigen("Unter", txt(g["t_unter"], z))}</p>')
        qr_teil.append(f'<div class="qr">{svg}</div>')
        if g["zeige_scan"] and g["t_scan"].strip():
            qr_teil.append(f'<p class="scan">{eigen("Scan", txt(g["t_scan"], z))}</p>')
        zugang = []
        if g["zeige_zugang"] and z.get("Zugang"):
            zugang.append('<div class="zugang">' + "".join(f'<div class="lbl">{esc(l)}</div><div class="{k}">{esc(w)}</div>' for l, w, k in z["Zugang"]) + "</div>")
        elif g["zeige_zugang"]:
            zugang.append(f'<div class="zugang"><div class="lbl">WLAN</div><div class="ssid">{esc(z["WLAN"])}</div>'
                          f'<div class="lbl">Passwort</div><div class="pw">{esc(z["Passwort"])}</div></div>')
        unten = [logo_html] if g["logo_ort"] == "unten" else []
        fuss = f'<p class="fuss">{eigen("Fuss", txt(g["t_fuss"], z))}</p>' if g["zeige_fuss"] and (g["t_fuss"].strip() or z.get("Fuss")) else ""
        if g["quer"]:   # Querformat: Texte links, QR-Code rechts
            inhalt = (f'<div class="zwei"><div class="sp-text">{"".join(teile + zugang + unten)}</div>'
                      f'<div class="sp-qr">{"".join(qr_teil)}</div></div>{fuss}')
        else:
            inhalt = "".join(teile + qr_teil + zugang + unten) + fuss
        seiten.append(f'<section class="seite"><div class="innen">{inhalt}</div></section>')

    rahmen = (f'border:{g["rahmen_mm"]}mm solid {g["farbe_rahmen"]};border-radius:{g["rahmen_radius"]}mm;padding:5mm;'
              if g["rahmen"] else "padding:1mm;")
    css = f"""@page{{size:{breite}mm {hoehe}mm;margin:0}}
*{{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
html,body{{margin:0;padding:0}}body{{font-family:{SCHRIFTEN[g["schrift"]]};color:{g["farbe_text"]};font-size:{g["gr_text"]}pt}}
.seite{{width:{breite}mm;height:{hoehe}mm;padding:{g["rand_mm"]}mm;background:{g["farbe_seite"]};overflow:hidden;page-break-after:always;break-after:page}}
.seite:last-child{{page-break-after:auto;break-after:auto}}
.innen{{height:100%;display:flex;flex-direction:column;text-align:{g["ausrichtung"]};{rahmen}}}
.kopf{{color:{g["farbe_akzent"]};font-weight:bold;font-size:{g["gr_kopf"]}pt;margin-top:2mm}}
h1{{font-size:{g["gr_titel"]}pt;margin:3mm 0 0;line-height:1.1}}
.info{{margin:1mm 0 3mm;color:{g["farbe_hell"]}}}
.qr{{margin:2mm 0}}.qr svg{{width:{qr_mm:.1f}mm;max-width:100%;height:auto;display:inline-block;vertical-align:top}}
.scan{{font-size:{g["gr_klein"] + 1}pt;color:{g["farbe_hell"]};margin:1mm 0 4mm}}
.zugang{{margin:1mm 0 2mm}}.lbl{{font-size:{g["gr_klein"]}pt;color:{g["farbe_hell"]};text-transform:uppercase;letter-spacing:.5px;margin-top:2mm}}
.wert{{font-weight:bold;font-size:{g["gr_text"] + 1}pt}}
.ssid{{font-weight:bold;font-size:{g["gr_text"] + 1}pt;white-space:nowrap}}
.pw{{display:inline-block;white-space:nowrap;font-family:Consolas,'DejaVu Sans Mono','Courier New',monospace;font-size:{g["gr_pw"]}pt;letter-spacing:1px;background:{g["farbe_pw_hinter"]};padding:1mm 3mm;border-radius:1.5mm;margin-top:.5mm;font-variant-ligatures:none}}
.zwei{{display:flex;gap:6mm;align-items:center;flex:1 0 auto}}.sp-text{{flex:1 1 55%;min-width:0}}.sp-qr{{flex:0 1 45%;text-align:center}}
.logo{{margin:1mm 0 2mm}}.logo img{{width:{g["logo_mm"]}mm;max-width:100%;max-height:{innen_h * 0.3:.0f}mm;object-fit:contain}}
.fuss{{font-size:{g["gr_klein"]}pt;color:{g["farbe_hell"]};margin:{"auto 0 0" if g["fuss_unten"] and not g["quer"] else "4mm 0 0"};padding-top:3mm}}
@media screen{{body{{background:#8a949b;padding:8mm 0}}.seite{{margin:0 auto 8mm;box-shadow:0 2px 12px rgba(0,0,0,.35)}}}}"""
    # Passt der Inhalt nicht auf die Seite, wird der QR-Code schrittweise verkleinert (min. 2,5 cm).
    anpassen = ("function anpassen(){let klein=0,voll=0,cm=0;document.querySelectorAll('.innen').forEach(i=>{const s=i.querySelector('.qr svg');"
                "i.querySelectorAll('.ssid,.pw').forEach(e=>{let f=parseFloat(getComputedStyle(e).fontSize);const b=e.parentElement.clientWidth;while(e.scrollWidth>b&&f>6){f*=0.95;e.style.fontSize=f+'px'}});"
                "const im=i.querySelector('.logo img');if(im){let lw=im.getBoundingClientRect().width/(parseFloat(document.body.style.zoom)||1);while(i.scrollHeight>i.clientHeight+1&&lw>57){lw*=0.94;im.style.width=lw+'px'}}"
                "let w=parseFloat(getComputedStyle(s).width);const w0=w,min=Math.min(w0,94.5);"
                "while(i.scrollHeight>i.clientHeight+1&&w>min){w=Math.max(min,w*0.96);s.style.width=w+'px'}"
                "if(w<w0-0.5){klein++;cm=w/37.795}if(i.scrollHeight>i.clientHeight+1)voll++});"
                "const t=[];if(klein)t.push('ℹ QR-Code automatisch auf '+cm.toFixed(1).replace('.',',')+' cm verkleinert, damit alles auf die Seite passt.');"
                "if(voll)t.push('⚠ Inhalt passt nicht auf die Seite – Schrift oder Logo verkleinern, Texte kürzen oder größeres Format wählen.');"
                "try{if(parent!==window&&parent.kdHinweis)parent.kdHinweis(t.join('\\n'))}catch(e){}return t}")
    if vorschau:
        skript = ("<script>" + anpassen + "function f(){document.body.style.zoom=1;const s=document.querySelector('.seite');const w=s.offsetWidth+40,h=s.offsetHeight+40;"
                  "document.body.style.zoom=Math.min(1,innerWidth/w,innerHeight/h)}addEventListener('resize',f);"
                  "addEventListener('load',()=>{anpassen();f()})</script>")
        css += "\n@media screen{body{padding:20px 0;min-height:100vh;display:flex;align-items:center;justify-content:center}.seite{margin:0}}"
    else:
        skript = "<script>" + anpassen + "addEventListener('load',()=>{const t=anpassen();" + ("setTimeout(()=>print(),300)" if drucken else "") + "})</script>"
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Zugangskarten {esc(sparte_name)}</title>'
            f'<style>{css}</style></head><body>{"".join(seiten)}{skript}</body></html>')


def beispiel_zeile(d):
    plan = plan_aktiv(d)
    s = plan["sparten"][0] if plan["sparten"] else {"name": "Musterverein e.V.", "kz": "MV"}
    pre = plan.get("praefix") or "SparteNet.de"
    return s["name"], s["kz"], {"Parzelle": 1, "WLAN": (s.get("wlan") or {}).get("paechter") or WLAN_PAECHTER.format(pre=pre, kz=s["kz"]), "Passwort": "Gartenzwerg-4711"}


def akt_karten_vorschau(d, design, drucken=False):
    g = design_pruefen(design)
    name, kz, z = beispiel_zeile(d)
    log = []
    if not qr_kontrast_ok(g["farbe_qr"], g["farbe_qr_hinter"]):
        log.append("⚠ QR-Code: zu wenig Kontrast – dunkle Punkte auf hellem Grund verwenden, sonst scannen viele Handys nicht.")
    if g["qr_cm"] < 3:
        log.append("⚠ QR-Code kleiner als 3 cm – aus der Hand schlecht lesbar.")
    return {"html": karten_html(g, name, kz, [z], drucken=drucken, vorschau=not drucken), "log": log or ["✔ Vorschau aktuell."]}


def akt_karten(d, kz, auswahl):
    plan = plan_aktiv(d)
    s = next((x for x in plan["sparten"] if x["kz"] == kz), None)
    if not s:
        raise Fehler("Sparte nicht im Plan.")
    zeilen = [{**z, "WLAN": wlan_ssid(d, kz)} for z in lese_ppsk(kz) if z.get("Passwort")]
    if auswahl != "alle":
        wahl = {str(x) for x in auswahl}
        zeilen = [z for z in zeilen if str(z["Parzelle"]) in wahl]
    if not zeilen:
        raise Fehler("Keine Einträge ausgewählt bzw. keine Passwörter vorhanden.")
    g = d["design"]
    html = karten_html(g, s["name"], kz, zeilen)
    LOG.info("Zugangskarten erzeugt: Sparte %s, %d Seiten, Format %s", kz, len(zeilen), g["format"])
    return {"html": html, "log": [f"✔ {len(zeilen)} Zugangskarten ({g['format']}{' quer' if g['quer'] else ''}, je Parzelle eine Seite, Design aus „Kartendesign“) zum Drucken geöffnet."]}


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

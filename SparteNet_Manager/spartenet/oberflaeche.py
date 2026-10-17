"""SparteNet Manager – Oberfläche (HTML, CSS, JavaScript der Web-App)"""
from .schnittstelle import *  # noqa: F401,F403 – alle Namen der vorherigen Module


# =============================================================== Oberfläche
HTML = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1d2f3e"><link rel="manifest" href="/manifest.webmanifest"><link rel="icon" href="/favicon.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="SparteNet"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>SparteNet Manager</title>
<script>try{const f=localStorage.getItem("sn_farbe");if(f=="hell"||f=="dunkel")document.documentElement.dataset.farbe=f}catch(e){}</script>
<style>
:root{--navy:#1d2f3e;--green:#3a9a1f;--lgreen:#e7f3e1;--bg:#f5f7f4;--line:#d9e0d6;--red:#b42318;--amber:#9a6700;--text:#1d2f3e;--muted:#5d6b75;--card:#fff;--hover:#eef2f5;--line2:#eef1ec;--bg2:#f4f6f2;color-scheme:light}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--text)}
header{background:var(--kopf,var(--navy));color:#fff;padding:14px 22px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
@media (max-width:600px){header{padding:12px 16px;gap:8px 12px}nav{padding:0 8px}nav button{padding:11px 10px}main{padding:16px}}
header b{font-size:22px}header b span{color:#6cc24a}header small{opacity:.7}#verb{font-size:13px;opacity:.85}
nav{display:flex;gap:4px;padding:0 22px;background:var(--card);border-bottom:1px solid var(--line);flex-wrap:wrap}
nav button{border:0;background:none;padding:13px 16px;font-size:15px;cursor:pointer;color:var(--muted);border-bottom:3px solid transparent}
nav button.aktiv{color:var(--navy);border-bottom-color:var(--green);font-weight:600}
main{max-width:var(--main-b,1200px);margin:0 auto;padding:22px;position:relative}
#griff{position:absolute;top:0;right:0;width:12px;height:100%;cursor:ew-resize;z-index:5}#griff::after{content:"";position:absolute;top:calc(var(--vh,100vh) / 2);left:4px;width:4px;height:60px;margin-top:-30px;border-radius:3px;background:#c5cec1;opacity:.6}
#griff:hover::after,#griff.zieht::after{background:var(--green);opacity:1}
.teiler{cursor:col-resize;align-self:stretch;position:relative;min-height:200px}.teiler::after{content:"";position:absolute;top:40px;bottom:40px;left:2px;width:4px;border-radius:3px;background:#dfe5dc}.teiler:hover::after,.teiler.zieht::after{background:var(--green)}
body.zieht{user-select:none;cursor:ew-resize}body.zieht iframe{pointer-events:none}
main.mehrspaltig section.aktiv:not(#kartendesign):not(#daten){display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,760px),1fr));gap:16px;align-items:start}
main.mehrspaltig section.aktiv:not(#kartendesign):not(#daten)>.karte{margin-bottom:0}
#ansicht{position:fixed;top:64px;right:16px;width:min(380px,calc(100vw - 32px));background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,.22);padding:16px 18px;z-index:50;display:none;max-height:calc(var(--vh,100vh) - 90px);overflow:auto}
#ansicht.offen{display:block}#ansicht h3{margin:0 0 4px}#ansicht .feld output{font-size:13px}section{display:none}section.aktiv{display:block}
.karte{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:16px}
h2{margin:0 0 6px;font-size:19px}h3{margin:0 0 8px;font-size:16px}p.hint{color:var(--muted);margin:4px 0 14px;font-size:14px}
label{display:block;font-size:13px;color:var(--muted);margin:10px 0 4px}
input,select{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:7px;font-size:15px;background:var(--card)}
.reihe{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.knoepfe{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
button.k{border:1px solid var(--navy);background:var(--card);color:var(--navy);padding:9px 16px;border-radius:7px;font-size:14px;cursor:pointer}
label.k{display:inline-flex;align-items:center;border:1px solid var(--navy);background:var(--card);color:var(--navy);padding:9px 16px;border-radius:7px;font-size:14px;cursor:pointer}
button.k:hover,label.k:hover{background:var(--hover)}button.p{background:var(--green);border-color:var(--green);color:#fff}button.p:hover{background:#318417}
button.r{background:var(--red);border-color:var(--red);color:#fff}button.r:hover{background:#8f1b13}button:disabled{opacity:.5;cursor:wait}
.log{background:#0f1a22;color:#d6f5c9;font-family:Consolas,monospace;font-size:13px;border-radius:8px;padding:12px;max-height:340px;overflow:auto;white-space:pre-wrap;margin-top:12px}
.log:empty{display:none}.fehler{color:#ffb4ab}
.tab{overflow:auto;max-height:var(--tab-h,520px);border:1px solid var(--line);border-radius:8px;margin-top:12px}.tab:empty{display:none}
table{border-collapse:collapse;width:100%;font-size:14px;background:var(--card);font-variant-ligatures:none;font-feature-settings:"calt" 0,"liga" 0}
th{position:sticky;top:0;background:var(--navy);color:#fff;text-align:left;padding:8px 10px;font-weight:600;z-index:1}
td{padding:6px 10px;border-top:1px solid var(--line2)}tr.kopf td{background:#548235;color:#fff;font-weight:600}tr.dienst td{background:var(--lgreen)}
td input{padding:6px 8px;font-size:14px}.mono{font-family:Consolas,monospace}
.schritt{display:grid;grid-template-columns:44px 1fr;gap:14px;align-items:start}.schritt>div{min-width:0}.nr{width:40px;height:40px;border-radius:50%;background:var(--green);color:#fff;display:grid;place-items:center;font-weight:700}
.status{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;background:#eee;color:#555;margin-left:6px}.status.ok{background:#dcf2d2;color:#24661a}.status:empty{display:none}
.kacheln{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:12px}
.kachel{border:1px solid var(--line);border-radius:8px;padding:10px 12px}.kachel b{font-size:24px;display:block}.kachel.gut b{color:var(--green)}.kachel.warn b{color:var(--amber)}.kachel.schlecht b{color:var(--red)}
.kd{display:grid;grid-template-columns:var(--kd-links,430px) 8px minmax(0,1fr);gap:8px;align-items:start}
.kd .karte{margin-bottom:12px;padding:14px 16px}.kd h3{margin-bottom:2px}
.kd .vorschau{position:sticky;top:12px}.kd iframe{width:100%;height:calc(var(--vh,100vh) - 150px);min-height:480px;border:1px solid var(--line);border-radius:10px;background:#8a949b}
.feld{display:grid;grid-template-columns:1fr auto;gap:4px 10px;align-items:center;margin-top:8px}.feld label{margin:0}
.feld input[type=range]{grid-column:1/3;padding:0}.feld output{font-size:13px;color:var(--text);font-variant-numeric:tabular-nums}
.feld input[type=color]{width:56px;height:32px;padding:2px;grid-column:2;grid-row:1}
.feld.chk{grid-template-columns:auto 1fr}.feld.chk input{width:auto}.feld.chk label{font-size:14px;color:var(--text)}
.feld textarea{grid-column:1/3;width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:7px;font:inherit;font-size:14px;resize:vertical;min-height:38px}
.feld select{grid-column:1/3}.logo-mini{max-width:160px;max-height:70px;border:1px dashed var(--line);border-radius:6px;padding:4px;display:block;margin-top:8px}
#kd_status{font-size:13px;color:var(--muted)}#kd_status.dirty{color:var(--amber);font-weight:600}
@media (max-width:860px){.teiler,#griff{display:none}.kd{grid-template-columns:1fr}.kd .vorschau{position:static}.kd iframe{height:70vh}}
.pwleiste{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:14px}.pwleiste input{max-width:260px}
#pw_st{font-size:13px;color:var(--muted);flex:1}#pw_st.dirty{color:var(--amber);font-weight:600}
td input.pwfeld{font-family:Consolas,'DejaVu Sans Mono',monospace;min-width:190px;font-variant-ligatures:none}
#tz_tab td:nth-child(2),#tz_tab td:nth-child(4),#tq_netz td:nth-child(2),#tq_qos td:nth-child(2){white-space:nowrap}#kk_tab td,#kk_tab th{white-space:nowrap}#kk_tab td:first-child{white-space:normal;min-width:150px}tr.geaendert td{background:#fff6dd}tr.falsch td{background:#fde8e6}tr.gesperrt td{color:var(--muted)}
#gp_tab td,#gp_tab th,#gp_st td,#gp_st th{white-space:nowrap}#gp_tab td:nth-child(2){white-space:normal;min-width:150px}#gp_st td:nth-child(3){white-space:normal;min-width:220px;font-size:12px}
.gp_in{width:64px;background:#fff8d6}.gp_in.w{width:84px}.gp_an h4{margin:14px 0 6px;color:var(--muted);font-size:13px}
.pwst{font-size:12px;white-space:nowrap}.pwst.f{color:var(--red)}.pwst.g{color:var(--amber)}
button.mini{border:1px solid var(--line);background:var(--card);border-radius:6px;padding:4px 8px;font-size:12px;cursor:pointer;color:var(--navy);margin-right:3px}button.mini:hover{background:var(--hover)}
.balken{position:relative;height:16px;min-width:90px;background:#eef1ec;border-radius:8px;overflow:hidden}.balken i{position:absolute;inset:0 auto 0 0;background:var(--green)}
.balken i.w{background:#d4a017}.balken i.s{background:var(--red)}.balken span{position:relative;font-size:11px;padding-left:6px;line-height:16px;color:var(--text);font-weight:600}
.punkt{display:inline-block;width:9px;height:9px;border-radius:50%;background:#bbb;margin-right:6px}.punkt.on{background:var(--green)}.punkt.off{background:var(--red)}
.chart{position:relative;margin-top:8px}.chart svg{width:100%;height:auto;display:block}.chart .tip{position:absolute;pointer-events:none;background:var(--navy);color:#fff;font-size:12px;padding:6px 8px;border-radius:6px;white-space:nowrap;display:none;z-index:2}
.legende{display:flex;gap:16px;font-size:13px;color:var(--muted);margin-top:4px;flex-wrap:wrap}.legende b{display:inline-block;width:14px;height:4px;border-radius:2px;margin-right:6px;vertical-align:middle}
#sys_k .kachel b{font-size:21px;white-space:nowrap}#sys_ger td,#sys_ger th,#sys_top td{white-space:nowrap}
.kachel small{display:block;color:var(--muted);font-size:12px;margin-top:2px}
.dgrid{display:grid;grid-template-columns:var(--d-links,270px) 8px minmax(0,1fr);gap:8px;align-items:start}
.dliste{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px;max-height:calc(var(--vh,100vh) - 140px);overflow:auto;position:sticky;top:12px}
.dliste h4{margin:10px 8px 4px;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
.dliste button{display:flex;width:100%;justify-content:space-between;gap:8px;border:0;background:none;text-align:left;padding:7px 8px;border-radius:6px;font-size:14px;cursor:pointer;color:var(--text)}
.dliste button:hover{background:var(--hover)}.dliste button.aktiv{background:var(--lgreen);font-weight:600}
.dliste button em{font-style:normal;font-size:11px;padding:1px 7px;border-radius:10px;background:#eee;color:#666;align-self:center}.dliste button em.ok{background:#dcf2d2;color:#24661a}.dliste button em.nein{background:#fde8e6;color:var(--red)}
pre.json{background:#0f1a22;color:#d6f5c9;font-size:12.5px;border-radius:8px;padding:12px;max-height:620px;overflow:auto;margin-top:12px}
td.zelle{max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media (max-width:860px){.dgrid{grid-template-columns:1fr}.dliste{position:static;max-height:300px}}

/* ---- Handy, Tablet, Fold */
header{padding-top:max(14px,env(safe-area-inset-top));padding-left:max(22px,env(safe-area-inset-left));padding-right:max(22px,env(safe-area-inset-right))}
nav{position:sticky;top:0;z-index:20}
@media (max-width:760px){
 header{padding:max(10px,env(safe-area-inset-top)) max(14px,env(safe-area-inset-right)) 10px max(14px,env(safe-area-inset-left));gap:6px 10px}
 header b{font-size:19px}header small{display:none}#verb{flex-basis:100%;order:9;font-size:12px}
 header .k{padding:7px 11px;font-size:13px}
 nav{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;padding:0 6px;gap:0;box-shadow:0 2px 6px rgba(0,0,0,.06)}
 nav::-webkit-scrollbar{display:none}nav button{white-space:nowrap;flex:0 0 auto;padding:12px 12px;font-size:14px}
 main{padding:12px max(12px,env(safe-area-inset-right)) calc(16px + env(safe-area-inset-bottom)) max(12px,env(safe-area-inset-left))}
 .karte{padding:14px;border-radius:12px;margin-bottom:12px}h2{font-size:18px}
 .knoepfe .k{flex:1 1 auto}.log{font-size:12px;max-height:260px}
 .kacheln{grid-template-columns:repeat(auto-fit,minmax(130px,1fr))}.kachel b{font-size:21px}
}
@media (max-width:360px){nav button{padding:12px 9px;font-size:13px}.kacheln{grid-template-columns:repeat(2,minmax(0,1fr))}.kachel{padding:8px;overflow-wrap:anywhere}.kachel b,#sys_k .kachel b{font-size:17px;white-space:normal}}
@media (pointer:coarse){#griff,.teiler{display:none}}
#logpfad{overflow-wrap:anywhere}
@media (pointer:coarse){button.k,label.k{min-height:44px}nav button{min-height:46px}input,select{font-size:16px;min-height:44px}td input,td select{min-height:38px}button.mini{padding:8px 10px;font-size:13px}}
@media (display-mode:standalone){#beenden_k{display:none}}
.schnell{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-top:8px}
.schnell button{border:1px solid var(--line);background:var(--card);border-radius:12px;padding:16px 10px;font-size:15px;cursor:pointer;color:var(--navy);text-align:center;min-height:70px}
.schnell button:hover{background:var(--lgreen)}.schnell button b{display:block;font-size:22px;margin-bottom:4px}
.pz{display:grid;grid-template-columns:minmax(0,1fr) minmax(170px,260px);gap:16px;align-items:center;margin-top:14px;border:2px solid var(--green);border-radius:14px;padding:16px}
.pz .qr svg{width:100%;height:auto;display:block;background:#fff}.pz dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:6px 12px;font-size:15px}.pz dt{color:var(--muted)}.pz dd{margin:0;font-weight:600;overflow-wrap:anywhere}
.pz .pw{font-family:Consolas,'DejaVu Sans Mono',monospace;font-size:24px;letter-spacing:1px;background:var(--lgreen);border-radius:8px;padding:8px 10px;margin:10px 0;overflow-wrap:anywhere;font-variant-ligatures:none}
@media (max-width:560px){.pz{grid-template-columns:1fr}.pz .qr{max-width:260px;margin:0 auto;width:100%}}
.code{font-family:Consolas,monospace;font-size:30px;font-weight:700;letter-spacing:3px;text-align:center;background:var(--lgreen);border-radius:10px;padding:14px;margin-top:12px}
.qrs{display:flex;gap:16px;flex-wrap:wrap;margin-top:12px}.qrs figure{margin:0;border:1px solid var(--line);border-radius:10px;padding:10px;text-align:center;width:220px}.qrs svg{width:180px;height:180px}
.qrs figcaption{font-size:13px;overflow-wrap:anywhere;margin-top:6px}.fern-nur{display:none}body.fern .fern-nur{display:block}body.fern .pc-nur{display:none!important}
.hinweis{background:#fff6dd;border:1px solid #f0d58a;border-radius:8px;padding:10px 12px;font-size:14px;margin-top:10px}
.k.ich{background:none;color:#fff;border-color:rgba(255,255,255,.55);font-size:13px;padding:6px 12px}.nurlesen{background:#fff6dd;color:#7a5a00;border-bottom:1px solid #ecd9a0;padding:8px 22px;font-size:14px}
#bn_ich .kachel b{font-size:19px;overflow-wrap:anywhere}#bn_tab td,#bn_tab th{white-space:nowrap}#bn_tab select{min-width:150px}#bn_tab tr.bn_detail td{background:#f7f9f5;white-space:normal}.bn_matrix{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:8px 18px;padding:6px 2px}.bn_matrix label{display:flex;justify-content:space-between;gap:10px;align-items:center;margin:0;font-size:13px;color:var(--text)}.bn_matrix select{min-width:175px!important;max-width:190px}.bn_matrix select.kein{color:var(--muted)}.bn_matrix select.schreiben{border-color:#3a9a1f;font-weight:600}[data-bereich].nurlesen-karte{position:relative}[data-bereich].nurlesen-karte::after{content:"nur lesen";position:absolute;top:-9px;right:18px;font-size:11px;background:#fff6dd;color:#7a5a00;border:1px solid #ecd9a0;border-radius:10px;padding:1px 8px}.recht-gesperrt td{color:var(--muted)}.recht-gesperrt td:first-child{text-decoration:line-through}
.karte{position:relative}.druckknopf{position:absolute;top:-11px;left:16px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1px 9px;font-size:11px;line-height:18px;color:var(--muted);cursor:pointer;z-index:1}
.druckknopf:hover{color:var(--text);border-color:#9fb19a}.druckkopf{display:none}
@media print{header,nav,.nurlesen,.karte:not(.druck),.log{display:none!important}main{padding:0}.druckknopf{display:none!important}
 body.einzeldruck .karte{display:none!important}body.einzeldruck .karte.druck-diese,body.einzeldruck .karte.druck-diese .karte{display:block!important}
 body.einzeldruck .karte.druck-diese{border:0;padding:0;margin:0;box-shadow:none}body.einzeldruck #ansicht,body.einzeldruck #griff{display:none!important}
 body.einzeldruck .druck-diese .tab{max-height:none!important;overflow:visible!important;border:0}
 body.einzeldruck .druck-diese button,body.einzeldruck .druck-diese .knoepfe,body.einzeldruck .druck-diese input[type=file]{display:none!important}
 body.einzeldruck .druck-diese .log{display:none!important}body.einzeldruck .druckkopf{display:block;border-bottom:1px solid #999;margin-bottom:8px;padding-bottom:4px;font-size:10px;color:#444}
 body.einzeldruck .druck-diese table{font-size:9.5px}body.einzeldruck .druck-diese th,body.einzeldruck tr.kopf td{-webkit-print-color-adjust:exact;print-color-adjust:exact}}

/* Farbschema: hell / dunkel / wie das System (Auswahl unter „Ansicht“, je Browser gespeichert) */
@media screen and (prefers-color-scheme:dark){:root:not([data-farbe=hell]){--bg:#0f161c;--card:#18222a;--line:#2e3c46;--line2:#24313a;--text:#e2e8ec;--muted:#9aa9b3;--lgreen:#1d3317;--hover:#24323c;--bg2:#1f2a33;--kopf:#0b1218;--red:#ff8a7a;--amber:#e8b64c;color-scheme:dark}:root:not([data-farbe=hell]) button.k,:root:not([data-farbe=hell]) label.k,:root:not([data-farbe=hell]) button.mini,:root:not([data-farbe=hell]) .schnell button{color:var(--text);border-color:#5d7689}:root:not([data-farbe=hell]) button.p{color:#fff;border-color:var(--green)}:root:not([data-farbe=hell]) nav button.aktiv{color:var(--text)}:root:not([data-farbe=hell]) input,:root:not([data-farbe=hell]) select,:root:not([data-farbe=hell]) textarea{color:var(--text)}:root:not([data-farbe=hell]) th{background:#25394a}:root:not([data-farbe=hell]) .status{background:#2a3741;color:#c9d3da}:root:not([data-farbe=hell]) .status.ok,:root:not([data-farbe=hell]) .dliste button em.ok{background:#1d3a17;color:#9fe08a}:root:not([data-farbe=hell]) tr.geaendert td,:root:not([data-farbe=hell]) .hinweis,:root:not([data-farbe=hell]) .nurlesen,:root:not([data-farbe=hell]) [data-bereich].nurlesen-karte::after{background:#3a3214;color:#f0d58a;border-color:#6b5a22}:root:not([data-farbe=hell]) tr.falsch td,:root:not([data-farbe=hell]) .dliste button em.nein{background:#45211d}:root:not([data-farbe=hell]) .gp_in{background:#3a3518}:root:not([data-farbe=hell]) #bn_tab tr.bn_detail td{background:var(--bg2)}:root:not([data-farbe=hell]) .dliste button em,:root:not([data-farbe=hell]) .balken{background:#2a3741;color:#c9d3da}:root:not([data-farbe=hell]) .teiler::after,:root:not([data-farbe=hell]) #griff::after{background:#3a4955}:root:not([data-farbe=hell]) .druckknopf:hover{border-color:#6f8a6a}:root:not([data-farbe=hell]) a{color:#8cc8ff}}
@media screen{:root[data-farbe=dunkel]{--bg:#0f161c;--card:#18222a;--line:#2e3c46;--line2:#24313a;--text:#e2e8ec;--muted:#9aa9b3;--lgreen:#1d3317;--hover:#24323c;--bg2:#1f2a33;--kopf:#0b1218;--red:#ff8a7a;--amber:#e8b64c;color-scheme:dark}:root[data-farbe=dunkel] button.k,:root[data-farbe=dunkel] label.k,:root[data-farbe=dunkel] button.mini,:root[data-farbe=dunkel] .schnell button{color:var(--text);border-color:#5d7689}:root[data-farbe=dunkel] button.p{color:#fff;border-color:var(--green)}:root[data-farbe=dunkel] nav button.aktiv{color:var(--text)}:root[data-farbe=dunkel] input,:root[data-farbe=dunkel] select,:root[data-farbe=dunkel] textarea{color:var(--text)}:root[data-farbe=dunkel] th{background:#25394a}:root[data-farbe=dunkel] .status{background:#2a3741;color:#c9d3da}:root[data-farbe=dunkel] .status.ok,:root[data-farbe=dunkel] .dliste button em.ok{background:#1d3a17;color:#9fe08a}:root[data-farbe=dunkel] tr.geaendert td,:root[data-farbe=dunkel] .hinweis,:root[data-farbe=dunkel] .nurlesen,:root[data-farbe=dunkel] [data-bereich].nurlesen-karte::after{background:#3a3214;color:#f0d58a;border-color:#6b5a22}:root[data-farbe=dunkel] tr.falsch td,:root[data-farbe=dunkel] .dliste button em.nein{background:#45211d}:root[data-farbe=dunkel] .gp_in{background:#3a3518}:root[data-farbe=dunkel] #bn_tab tr.bn_detail td{background:var(--bg2)}:root[data-farbe=dunkel] .dliste button em,:root[data-farbe=dunkel] .balken{background:#2a3741;color:#c9d3da}:root[data-farbe=dunkel] .teiler::after,:root[data-farbe=dunkel] #griff::after{background:#3a4955}:root[data-farbe=dunkel] .druckknopf:hover{border-color:#6f8a6a}:root[data-farbe=dunkel] a{color:#8cc8ff}}
</style></head><body>
<header><b>Sparte<span>Net</span></b><small>Manager __VERSION__ · Cloud</small><span id="verb"></span><div style="flex:1"></div><button class="k ich" id="up_chip" onclick="zeige('system')" hidden title="Neue Version verfügbar"></button><button class="k ich" id="ich_k" onclick="zeige('benutzer')" title="Mein Konto und Benutzerkonten"></button><button class="k" style="background:none;color:#fff;border-color:#fff" onclick="ansichtPanel()" title="Breite, Größe, Tabellenhöhe und Farbschema (hell/dunkel) anpassen">Ansicht</button><button class="k ich" id="farbe_k" onclick="farbeWechseln()" title="Farbschema: System → Hell → Dunkel"></button><button class="k pc-nur" id="beenden_k" style="background:none;color:#fff;border-color:#fff" onclick="beenden()">Beenden</button></header>
<div id="ansicht"><h3>Ansicht anpassen</h3><p class="hint" style="margin:2px 0 6px">Für FHD bis 8K, normal oder curved. Wird gespeichert. Breite auch direkt am rechten Rand ziehen (Doppelklick = volle Breite).</p>
<div class="feld"><label for="an_breite_sel">Breite des Inhalts</label><output id="an_breite_o"></output><select id="an_breite_sel" onchange="ansSet('breite',+this.value)"><option value="1200">Standard (FHD)</option><option value="1600">Breit (WQHD)</option><option value="2200">Sehr breit (4K)</option><option value="3200">Ultra (5K / Curved)</option><option value="0">Volle Fensterbreite</option><option value="-1">Eigene …</option></select>
<input type="range" id="an_breite" min="800" max="6000" step="50" oninput="ansSet('breite',+this.value)"></div>
<div class="feld"><label for="an_zoom_sel">Größe (Skalierung)</label><output id="an_zoom_o"></output><select id="an_zoom_sel" onchange="ansSet('zoom',+this.value)"><option value="0">Automatisch nach Bildschirm</option><option value="0.8">80 %</option><option value="0.9">90 %</option><option value="1">100 %</option><option value="1.1">110 %</option><option value="1.25">125 %</option><option value="1.5">150 %</option><option value="1.75">175 %</option><option value="2">200 %</option><option value="2.5">250 %</option><option value="3">300 %</option></select></div>
<div class="feld"><label for="an_tabh_sel">Höhe der Tabellen</label><output id="an_tabh_o"></output><select id="an_tabh_sel" onchange="ansSet('tabh',+this.value)"><option value="0">An Fensterhöhe anpassen</option><option value="320">Niedrig</option><option value="520">Standard</option><option value="900">Hoch</option><option value="-1">Eigene …</option></select>
<input type="range" id="an_tabh" min="200" max="3000" step="20" oninput="ansSet('tabh',+this.value)"></div>
<div class="feld"><label for="an_farbe">Farbschema</label><select id="an_farbe" onchange="farbeSetzen(this.value)"><option value="system">Wie das System (hell/dunkel automatisch)</option><option value="hell">Hell</option><option value="dunkel">Dunkel</option></select></div>
<div class="feld chk"><input type="checkbox" id="an_spalten" onchange="ansSet('spalten',this.checked)"><label for="an_spalten">Karten nebeneinander, wenn Platz ist (breite Monitore)</label></div>
<div class="knoepfe"><button class="k" onclick="ansZurueck()">Zurücksetzen</button><button class="k p" onclick="ansichtPanel(false)">Fertig</button></div></div>
<div id="nurlesen" class="nurlesen" hidden></div>
<nav id="nav"></nav>
<main id="main"><div id="griff" title="Ziehen: Breite ändern · Doppelklick: volle Breite / Standard"></div>
<section id="start"><div class="karte"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><h2 style="flex:1;margin:0">Überblick <span id="st_zeit" class="status"></span></h2><button class="k" onclick="startLaden()">Aktualisieren</button></div>
<div class="kacheln" id="st_k"></div><div class="log" id="log_start"></div></div>
<div class="karte"><h3>Parzelle nachschlagen</h3><p class="hint">WLAN-Name, Passwort und QR-Code einer Parzelle – zum Zeigen, Scannen lassen oder Teilen.</p>
<div class="reihe"><div><label for="st_sp">Sparte</label><select id="st_sp"></select></div><div><label for="st_p">Parzelle</label><input id="st_p" type="number" inputmode="numeric" min="1" max="199" placeholder="z. B. 47" onkeydown="if(event.key=='Enter')parzelleZeigen()"></div></div>
<div class="knoepfe"><button class="k p" onclick="parzelleZeigen()">Anzeigen</button></div><div class="log" id="log_pz"></div><div id="pz_karte"></div></div>
<div data-bereich="voucher" class="karte"><h3>Gast-Voucher schnell</h3><p class="hint">Erstellt einen Code für das Gäste-WLAN.</p>
<div class="knoepfe"><button class="k" onclick="schnellVoucher(120)">2 Stunden</button><button class="k" onclick="schnellVoucher(1440)">1 Tag</button><button class="k" onclick="schnellVoucher(10080)">1 Woche</button></div>
<div class="log" id="log_sv"></div><div id="sv_code"></div></div>
<div class="karte"><h3>Schnellzugriff</h3><div class="schnell">
<button onclick="zeige('tarife')"><b>⇅</b>Tarife</button><button onclick="zeige('uebertragen')"><b>⇪</b>Übertragen</button><button onclick="zeige('einrichten')"><b>⚿</b>Passwörter</button>
<button onclick="zeige('voucher')"><b>✉</b>Gast-Voucher</button><button onclick="zeige('system')"><b>▤</b>Systeminfo</button><button onclick="zeige('abgleich')"><b>✓</b>Abgleich</button></div>
<div class="knoepfe" id="install_k" style="display:none"><button class="k p" onclick="installieren()">Als App auf diesem Gerät installieren</button></div></div></section>

<section id="verbindung"><div class="karte fern-nur"><h2>Am Handy angemeldet</h2><p class="hint">Verbindung, API-Key, PIN und Heimnetz-Zugriff lassen sich nur am PC ändern. Alles andere geht hier genauso.</p>
<div class="knoepfe"><button class="k" onclick="abmelden()">Auf diesem Gerät abmelden</button></div></div>
<div class="karte pc-nur" id="fern_karte"><h2>Handy &amp; Tablet (App)</h2>
<p class="hint">Den Manager auf Handy, Tablet oder Fold als App nutzen. Er läuft weiter auf diesem PC – das Handy ist nur die Bedienung. Schutz: Manager-Passwort, optional Handy-PIN; Anmeldung bleibt __SITZUNG_TAGE__ Tage gültig.</p>
<h3>1. Optionale Handy-PIN festlegen</h3><div class="reihe" style="max-width:640px"><div><label for="fern_pin">Neue PIN (6–32 Zeichen) <span id="fern_pin_st" class="status"></span></label><input id="fern_pin" type="password" autocomplete="new-password" placeholder="z. B. 6–8 Ziffern"></div></div>
<div class="knoepfe"><button class="k p" onclick="fernPin()">PIN speichern</button><button class="k" onclick="fernAbmelden()">Alle Geräte abmelden</button></div>
<div id="fern_geraete" class="hint" style="margin-top:8px"></div>
<h3 style="margin-top:18px">2. Zugriff wählen</h3>
<div class="reihe"><div style="border:1px solid var(--line);border-radius:10px;padding:12px"><b>Von überall – mit Tailscale (empfohlen)</b>
<p class="hint">Verschlüsselt, auch aus der Gartensparte über Mobilfunk, und nur hier wird es eine echte App (HTTPS). Tailscale kostenlos auf PC und Handy installieren, mit demselben Konto anmelden, dann hier einschalten.</p>
<div id="ts_st" class="hint"></div><div class="knoepfe"><button class="k p" id="ts_an" onclick="tailscale(true)">Tailscale-Freigabe einschalten</button><button class="k" id="ts_aus" onclick="tailscale(false)">ausschalten</button></div></div>
<div style="border:1px solid var(--line);border-radius:10px;padding:12px"><b>Nur im eigenen WLAN/Heimnetz</b>
<p class="hint">Ohne Zusatzprogramm, aber nur wenn Handy und PC im selben Netz sind. Unverschlüsselt (http) – am Handy als Verknüpfung auf dem Startbildschirm statt echter App.</p>
<div class="feld chk"><input type="checkbox" id="fern_lan" onchange="fernLan()"><label for="fern_lan">Im Heimnetz erreichbar machen</label></div><div id="lan_st" class="hint"></div></div></div>
<h3 style="margin-top:18px">3. Auf dem Handy</h3>
<p class="hint">QR-Code mit der Kamera scannen → Manager-Passwort oder Handy-PIN eingeben → <b>Android (Chrome):</b> Menü ⋮ → „App installieren“ bzw. „Zum Startbildschirm hinzufügen“ · <b>iPhone/iPad (Safari):</b> Teilen □↑ → „Zum Home-Bildschirm“.</p>
<div class="qrs" id="fern_qr"></div><div class="knoepfe"><button class="k" onclick="fernLaden()">Aktualisieren</button></div><div class="log" id="log_fern"></div></div>
<div class="karte"><h2>Verbindung über die UniFi-Cloud</h2>
<p class="hint">Kein lokaler Zugriff nötig – alles läuft über api.ui.com. Die Daten bleiben bei Ihnen (Datenordner oder eigene MariaDB-Datenbank).</p>
<div class="reihe"><div><label>Site-Manager-API-Key (unifi.ui.com → Einstellungen → API Keys) <span id="key_st" class="status"></span></label><input id="cloud_key" type="password" placeholder="leer lassen = unverändert"></div>
<div><label>Konsole</label><select id="konsole"><option value="">– erst „Konsolen laden“ –</option></select></div></div>
<div class="knoepfe"><button class="k" onclick="konsolenLaden()">Konsolen laden</button><button class="k p" onclick="speichern()">Speichern</button><button class="k" onclick="testen()">Verbindung testen</button></div>
<div class="log" id="log_v"></div></div>
<div class="karte"><h2>Datenspeicher</h2><p class="hint">Hier liegen Einstellungen, Planung, Buchungen, Passwörter je Parzelle, Sicherungen und das Änderungsprotokoll: <b id="speicherort">…</b></p></div>
<div class="karte"><h2>Protokoll zur Fehlersuche</h2><p class="hint">Zeichnet alle Anfragen an die Cloud mit Antwort und Fehlern in <span id="logpfad">SparteNet_Manager.log</span> auf (Passwörter und Key werden nicht gespeichert). Nur bei Bedarf einschalten.</p>
<label style="display:flex;align-items:center;gap:10px;font-size:15px;color:var(--text)"><input type="checkbox" id="log_aktiv" style="width:auto" onchange="logSchalten()"> Protokoll einschalten</label>
<div class="knoepfe"><button class="k" onclick="logZeigen()">Protokoll anzeigen</button><button class="k" onclick="logLoeschen()">Protokoll leeren</button></div>
<div class="log" id="log_datei"></div></div>
<div class="karte"><h2>Diagnose-Datei für die Fehlersuche</h2><p class="hint">Liest alle Antworten der Konsole einmal aus (nur lesend) und speichert sie als Datei. Der API-Key steht nicht darin, Passwörter, Schlüssel und E-Mail-Adressen werden entfernt. Diese Datei kannst du zur Fehlersuche weitergeben – den API-Key bitte nie.</p>
<label style="display:flex;align-items:center;gap:10px;font-size:15px;color:var(--text)"><input type="checkbox" id="diag_anon" style="width:auto" checked> Clientnamen und MAC-Adressen der Endgeräte anonymisieren</label>
<div class="knoepfe"><button class="k p" onclick="diagnose()">Diagnose-Datei erstellen</button></div><div class="log" id="log_diag"></div></div></section>

<section id="lesen"><div class="karte"><h2>Auslesen</h2>
<div class="knoepfe"><button class="k" onclick="lesen('geraete')">Geräte</button><button class="k" onclick="lesen('clients')">Clients</button><button class="k" onclick="lesen('netze')">Netze / VLANs</button>
<button class="k" onclick="lesen('wlans')">WLANs</button><button class="k" onclick="lesen('voucher')">Voucher</button><button class="k p" onclick="csvSpeichern(LETZT,'export')">Als CSV</button></div>
<div class="log" id="log_l"></div><div class="tab" id="tab_l"></div></div></section>

<section id="planung"><div class="karte"><h2>Sparten am Gateway</h2><p class="hint">Empfohlen: in der <a href="#" onclick="zeige('netzplanung');return false">Netzplanung</a> unter „VLAN-Plan je Gateway“ das Gateway wählen und „In Planung übernehmen“ (VLAN-Schema je Standort). Alternativ wie bisher hier eintragen oder den alten VLAN-Planer (Excel) übernehmen – dann gilt das alte Steckplatz-Schema.</p>
<div class="reihe"><div><label>Gateway-Nummer</label><input id="p_gw" type="number" min="1" max="254"></div><div><label>Gateway-Bezeichnung</label><input id="p_gwname"></div><div><label>WLAN-Präfix</label><input id="p_pre"></div></div>
<div class="tab" id="p_tab"></div>
<div class="knoepfe"><button class="k p" onclick="planSpeichern()">Speichern</button><label style="margin:0;display:flex;align-items:center;gap:8px" class="k">Aus Excel übernehmen<input type="file" id="xls" accept=".xlsx" onchange="excelHoch()" style="display:none"></label></div>
<div class="log" id="log_p"></div></div>
<div class="karte druck"><h2>IP-Plan</h2><label>Sparte</label><select id="plan_sp" onchange="planZeigen()"></select>
<div class="knoepfe"><button class="k" onclick="csvSpeichern(PLANZ,'ip-plan')">Als CSV</button><button class="k" onclick="window.print()">Drucken</button></div><div class="tab" id="tab_p"></div></div></section>

<section id="abgleich"><div class="karte"><h2>Abgleich: Plan ↔ Gateway</h2><p class="hint">Fehlende und abweichende Netze, Geräte und Endgeräte im falschen Netz. Nur lesend.</p>
<label>Sparte</label><select id="ab_sp"></select>
<div class="knoepfe"><button class="k p" onclick="abgleich()">Abgleich starten</button></div>
<div class="log" id="log_a"></div><div class="kacheln" id="kach_a"></div>
<h3 style="margin-top:18px" id="h_hin"></h3><div class="tab" id="tab_hin"></div>
<h3 style="margin-top:18px" id="h_feh"></h3><div class="tab" id="tab_feh"></div>
<h3 style="margin-top:18px" id="h_abw"></h3><div class="tab" id="tab_abw"></div>
<h3 style="margin-top:18px" id="h_cli"></h3><div class="tab" id="tab_cli"></div></div>
<div class="karte" data-bereich="netze" id="um_karte"><h2>Umzugshilfe: vorhandene Netze auf das neue VLAN-Schema</h2>
<p class="hint">Für Gateways, die schon mit dem alten Schema laufen (z. B. Buchenweg): Netze mit gleichem Namen bekommen die VLAN-ID, das Subnetz, die Router-IP und den DHCP-Bereich aus der aktiven Planung. Netzmaske (Tarif) und Netz-ID bleiben – Passwörter, Tarife und Port-Profile gelten weiter. Die Reihenfolge wählt der Manager so, dass nie zwei Netze dieselbe VLAN-ID oder dasselbe Subnetz haben. <b>Geräte in umgestellten Netzen brauchen danach eine neue IP</b> (WLAN aus/an) – am besten außerhalb der Gartenzeit und erst mit „nur das erste“ testen.</p>
<div class="knoepfe"><button class="k" onclick="umVorschau()">Vorschau</button><button class="k p" id="um_los" onclick="umAusfuehren(false)" disabled>Ausgewählte umstellen</button><button class="k" id="um_eins" onclick="umAusfuehren(true)" disabled>Nur das erste umstellen</button><button class="k" onclick="umZurueck()">Umzug rückgängig</button></div>
<div class="tab" id="um_tab"></div><div class="log" id="log_um"></div></div></section>

<section id="einrichten"><div class="karte"><h2>Sparte einrichten</h2><p class="hint">Immer zuerst „Vorschau“. Vor Änderungen eine Sicherung der Konsole machen.</p>
<label>Sparte</label><select id="ein_sp" onchange="ssid()"></select></div>
<div class="karte" data-bereich="netze" id="zg_karte" hidden><h3>Netze nach Buchungen – dieses Gateway</h3><p class="hint" id="zg_hint"></p>
<div class="knoepfe"><button class="k" onclick="zgVorschau()">Vorschau</button><button class="k p" id="zg_los" onclick="zgAusfuehren()" disabled>Ausgewählte am Gateway ausführen</button></div>
<div class="tab" id="zg_tab"></div><div class="log" id="log_zg"></div></div>
<div data-bereich="netze" class="karte schritt"><div class="nr">1</div><div><h3>Fehlende Netze anlegen</h3><p class="hint">Vorlage ist ein vorhandenes Parzellennetz (z. B. BW-Paz.004): DHCP, Isolation, Firewall-Zone werden übernommen, nur Name, VLAN und Adressen geändert.</p>
<div class="knoepfe"><button class="k" onclick="netze(false,false)">Vorschau</button><button class="k p" onclick="netze(true,true)">Erstes Netz anlegen (Test)</button><button class="k r" onclick="netze(true,false)">Alle fehlenden anlegen</button></div></div></div>
<div data-bereich="netze" class="karte schritt"><div class="nr">2</div><div><h3>WLANs prüfen</h3><p class="hint">Pächter <b id="ssid1"></b> (WPA2, PPSK) · Gäste <b id="ssid2"></b> (Hotspot/Voucher) · Vorstand <b id="ssid3"></b>.</p></div></div>
<div data-bereich="wlan_pw" class="karte schritt"><div class="nr">3</div><div><h3>Passwörter je Parzelle</h3><p class="hint">Bereits verteilte Passwörter erst übernehmen, dann nur fehlende ergänzen. Gespeichert in PPSK_&lt;Kürzel&gt;.csv.</p>
<div class="knoepfe"><button class="k" onclick="ppsk('anzeigen')">Anzeigen</button><button class="k" onclick="ppsk('gateway')">Vom Gateway übernehmen</button><button class="k p" onclick="ppsk('fehlende')">Fehlende erzeugen</button>
<button class="k" onclick="ppsk('neu')">Alle neu erzeugen</button><button class="k" onclick="csvSpeichern(PPSK,'ppsk')">Als CSV</button></div>
<div class="pwleiste"><span style="font-size:14px">Regel für neue Passwörter:</span><input id="pr_pre" style="max-width:90px" maxlength="10"><span>+</span><input id="pr_z" type="number" min="6" max="30" style="max-width:80px"><span style="font-size:14px">Ziffern</span>
<span id="pr_bsp" class="mono" style="font-size:14px;color:var(--muted)"></span><button class="k" onclick="regelSpeichern()">Regel speichern</button></div>
<p class="hint" style="margin-top:6px">Jedes erzeugte Passwort ist einmalig – über alle Sparten und auch gegenüber früher vergebenen (Register nur als Prüfsumme gespeichert).</p>
<div id="pw_bereich" style="display:none"><p class="hint" style="margin-top:14px">Passwort direkt in der Tabelle ändern (8–63 Zeichen, keine Umlaute, jedes nur einmal). „neu“ = zufälliges Passwort, „sperren“ = Parzelle ohne Zugang, „↺“ = zurück. Erst <b>Änderungen speichern</b>, dann <b>Schritt 4</b>, damit es im WLAN gilt.</p>
<div class="pwleiste"><input id="pw_suche" placeholder="Suchen (Parzelle, Netz, Passwort)" oninput="pwFilter()"><span id="pw_st"></span>
<button class="k p" onclick="pwSpeichern()">Änderungen speichern</button><button class="k" onclick="pwVerwerfen()">Verwerfen</button></div>
<div class="tab" id="tab_pw"></div></div>
<div data-bereich="karten"><h3 style="margin-top:16px">Zugangskarten mit WLAN-QR-Code</h3><p class="hint">Je Parzelle eine Seite, im gespeicherten Kartendesign. Erst „Anzeigen“ oder „Fehlende erzeugen“, dann in der Tabelle oben (Spalte „Drucken“) auswählen.</p>
<p class="hint">Format, Farben, Texte, QR-Größe und Logo: Reiter <a href="#" onclick="zeige('kartendesign');return false">Kartendesign</a>.</p>
<div class="knoepfe"><button class="k p" onclick="karten('alle')">Alle drucken</button><button class="k" onclick="karten('auswahl')">Ausgewählte drucken</button>
<button class="k" onclick="markiere(true)">Alle markieren</button><button class="k" onclick="markiere(false)">Keine markieren</button><button class="k" onclick="markiereGeaendert()">Zuletzt geänderte markieren</button></div></div></div></div>
<div data-bereich="wlan_pw" class="karte schritt"><div class="nr">4</div><div><h3>Passwörter ins Pächter-WLAN laden</h3><p class="hint">Überträgt alle Unterschiede dieser Sparte (neu, geändert, gesperrt), mit Sicherung und Kontrolle. Einzelne Parzellen auswählen: Reiter <a href="#" onclick="zeige('uebertragen');return false">Übertragen</a>.</p>
<div class="knoepfe"><button class="k" onclick="schritt('ppsk-hochladen',false)">Vorschau</button><button class="k r" onclick="schritt('ppsk-hochladen',true)">Ausführen</button></div></div></div>
<div class="karte"><h3>Protokoll</h3><div class="log" id="log_e"></div><div class="tab" id="tab_e"></div></div></section>

<section id="uebertragen"><div class="karte"><h2>Änderungen an das Gateway übertragen</h2>
<p class="hint">Hier gehen alle Änderungen aus dem Manager über die UniFi-Cloud an das Gateway: fehlende Netze und Passwörter je Parzelle (neu, geändert, gesperrt). Immer erst „Unterschiede ermitteln“, dann auswählen und übertragen. Vor jeder Passwort-Übertragung wird der alte Stand gesichert.</p>
<div class="knoepfe"><button class="k" onclick="schreibtest()">1. Schreibzugriff prüfen</button></div><div class="log" id="log_st"></div></div>
<div class="karte"><h3>2. Unterschiede zwischen Manager und Gateway</h3><div class="reihe" style="max-width:520px"><div><label>Sparte</label><select id="ue_sp"></select></div></div>
<div class="knoepfe"><button class="k p" onclick="vergleich()">Unterschiede ermitteln</button></div><div class="log" id="log_ue"></div><div class="kacheln" id="ue_k"></div>
<div id="ue_bereich" style="display:none">
<h3 style="margin-top:16px" id="ue_h_netze"></h3><div class="tab" id="ue_netze"></div>
<h3 style="margin-top:16px" id="ue_h_ppsk"></h3><div class="tab" id="ue_ppsk"></div>
<div class="knoepfe"><button class="k" onclick="ueAlle(true)">Alle markieren</button><button class="k" onclick="ueAlle(false)">Keine markieren</button>
<button class="k" onclick="uebertragen(false)">Vorschau</button><button class="k r" onclick="uebertragen(true)">3. Ausgewählte übertragen</button></div></div>
<div class="knoepfe" style="margin-top:18px;border-top:1px solid var(--line);padding-top:14px"><button class="k" onclick="rueckgaengig()">Letzte Passwort-Übertragung rückgängig</button></div></div>
<div class="karte"><h3>Änderungsprotokoll</h3><p class="hint">Jede Übertragung mit Zeit und Ergebnis (ohne Passwörter) – Datei SparteNet_Aenderungen.log.</p>
<div class="knoepfe"><button class="k" onclick="journalZeigen()">Anzeigen</button></div><div class="log" id="log_jn"></div></div></section>

<section id="tarife"><div data-bereich="tarife" class="karte"><h2>Tarife</h2>
<p class="hint">Ein Tarif legt zwei Dinge fest: die <b>Bandbreite</b> (wird am Gateway als QoS-Regel „Geschwindigkeit begrenzen“ angelegt, die Netze des Tarifs werden darin eingetragen) und die <b>Netzgröße</b> (Subnetzmaske unter Netzwerke → Gateway-IP/Subnetz, dazu der passende DHCP-Bereich). „Endgeräte“ = Größe des DHCP-Bereichs, 0 = ganzer Bereich. Die Router-IP (z. B. 10.1.67.1) bleibt immer gleich.</p>
<div class="tab"><table id="tf_tab"></table></div>
<div class="knoepfe"><button class="k" onclick="tfNeu()">+ Tarif</button><button class="k" onclick="tfStandard()">Beispiel-Tarife einsetzen</button></div>
<div class="reihe" style="margin-top:12px"><div><label for="tf_modus">QoS-Regeln anlegen</label><select id="tf_modus" onchange="tfModusHint()"><option value="tarif">Eine Regel je Tarif – alle Netze des Tarifs in einer Regel</option><option value="netz">Eine Regel je Netz – jede Parzelle eine eigene Regel</option></select></div></div>
<p class="hint" id="tf_modus_hint"></p>
<div class="knoepfe"><button class="k p" onclick="tfSpeichern()">Tarife speichern</button></div><div class="log" id="log_tf"></div></div>

<div data-bereich="buchungen" class="karte"><h3>Netze einem Tarif zuordnen</h3>
<p class="hint">Alle Netze vom Gateway (auch Vorstand, Gäste, Technik oder eigene) – jedes kann einen Tarif bekommen. Tarif wählen, „Zuordnung speichern“, dann unten übertragen. „Ist-Zustand erkennen“ schlägt für Parzellen ohne Tarif den passenden Tarif nach der heutigen Netzmaske vor.</p>
<div class="knoepfe"><button class="k p" onclick="tzLaden()">Netze laden &amp; Unterschiede ermitteln</button><button class="k" onclick="tzErkennen()">Ist-Zustand erkennen</button></div>
<div class="log" id="log_tz"></div><div class="kacheln" id="tz_k"></div>
<div id="tz_bereich" style="display:none">
<div class="reihe" style="margin-top:12px"><div><label for="tz_suche">Suchen</label><input id="tz_suche" placeholder="z. B. Paz. oder 10.1.5 oder Basic" oninput="tzFilter()"></div>
<div><label for="tz_massen">Für markierte Netze</label><div style="display:flex;gap:6px"><select id="tz_massen"></select><button class="k" onclick="tzMassen()">setzen</button></div></div></div>
<div class="tab" id="tz_tab"></div>
<div class="knoepfe"><button class="k" onclick="tzMarkAlle(true)">Sichtbare markieren</button><button class="k" onclick="tzMarkAlle(false)">Keine markieren</button><button class="k p" onclick="tzSpeichern()">Zuordnung speichern &amp; neu vergleichen</button><span id="tz_offen" class="status"></span></div>
</div></div>

<div data-bereich="tarife" class="karte"><h3>An das Gateway übertragen</h3>
<p class="hint">Zuerst oben „Unterschiede ermitteln“. QoS-Regeln, die der Manager anlegt, heißen „SparteNet-Tarif-…“ bzw. „SparteNet-Netz-…“ – andere QoS-Regeln am Gateway werden nie verändert. Vor jeder Übertragung wird der alte Stand gesichert.</p>
<h3 id="tq_h_qos" style="margin-top:12px"></h3><div class="tab" id="tq_qos"></div>
<h3 id="tq_h_netz" style="margin-top:12px"></h3><div class="tab" id="tq_netz"></div>
<div class="knoepfe" id="tq_kn" style="display:none"><button class="k" onclick="tqAlle(true)">Alle markieren</button><button class="k" onclick="tqAlle(false)">Keine markieren</button><button class="k" onclick="tqUebertragen(false)">Vorschau</button><button class="k r" onclick="tqUebertragen(true)">Ausgewählte übertragen</button></div>
<div class="log" id="log_tq"></div>
<div class="knoepfe" style="margin-top:18px;border-top:1px solid var(--line);padding-top:14px"><button class="k" onclick="tqRueckgaengig()">Letzte Tarif-Übertragung rückgängig</button></div></div>
</section>

<section id="kalkulation"><div data-bereich="kalkulation" class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Kalkulation &amp; Auslastung</h2>
<label class="feld chk" style="margin:0;display:flex;gap:6px;align-items:center"><input type="checkbox" id="kk_prog" onchange="kkLaden()" style="width:auto"> Prognose für Sparten ohne Buchungen</label>
<button class="k p" onclick="kkLaden()">Berechnen</button></div>
<p class="hint">Gebuchte Parzellen × Tarifpreis je Sparte, Buchungsrate und Gesamtauslastung aller Sparten mit Buchungen. Kosten und Ergebnis nach den Annahmen der Kalkulation. Rechnet nur hier im Manager – am Gateway ändert sich nichts.</p>
<div class="kacheln" id="kk_k"></div><div class="log" id="log_kk"></div></div>
<div data-bereich="kalkulation" class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Je Sparte</h3><button class="k" onclick="kkCsv()">Als CSV speichern</button></div>
<p class="hint">Investition, Masten mit Technik und Uplink je Sparte direkt in der Tabelle ändern (wird sofort gespeichert) oder aus der Kalkulation (Excel) übernehmen. Uplink leer = Standard aus den Annahmen.</p>
<div class="tab" id="kk_tab"></div></div>
<div data-bereich="buchungen" class="karte"><h3>Buchungen erfassen</h3>
<p class="hint">Welche Parzelle welchen Tarif gebucht hat. Was im Reiter „Tarife“ einer Parzelle zugeordnet ist, steht automatisch hier – und umgekehrt. Ans Gateway (Bandbreite, Netzgröße) geht es über „Tarife“ → Übertragen.</p>
<div class="reihe"><div><label for="kb_sp">Sparte</label><select id="kb_sp" onchange="kbLaden()"></select></div>
<div><label for="kb_bereich">Parzellen (z. B. 1-20, 25, 31)</label><input id="kb_bereich" placeholder="1-20, 25"></div>
<div><label for="kb_tarif">Tarif</label><div style="display:flex;gap:6px"><select id="kb_tarif"></select><button class="k" onclick="kbMassen()">setzen</button></div></div></div>
<div class="kacheln" id="kb_k"></div><div class="tab" id="kb_tab"></div>
<div class="knoepfe"><button class="k p" onclick="kbSpeichern()">Buchungen speichern</button><button class="k" onclick="kbLaden(true)">Verwerfen</button><span id="kb_offen" class="status"></span></div><div class="log" id="log_kb"></div></div>
<div data-bereich="kalkulation" class="karte"><h3>Annahmen</h3><p class="hint">Aus der Kalkulation übernommen oder hier ändern. Tarifpreise (€ pro Jahr) stehen im Reiter „Tarife“.</p>
<div class="reihe" id="ka_form"></div><div class="knoepfe"><button class="k p" onclick="kaSpeichern()">Annahmen speichern</button></div><div class="log" id="log_ka"></div></div>
<div data-bereich="kalkulation" class="karte"><h3>Aus Excel übernehmen</h3><p class="hint"><b>Kalkulation</b> (Kalkulation_Sparten_WLAN.xlsx): Annahmen, Tarifpreise und je Sparten-Blatt Investition und Masten. <b>VLAN-Planer</b>: alle Sparten, die dort ein Gateway haben (Name, Kürzel, Parzellen, Gateway).</p>
<div class="knoepfe"><label class="k">Kalkulation oder VLAN-Planer wählen …<input type="file" id="kk_datei" accept=".xlsx" onchange="kkImport()" style="display:none"></label></div><div class="log" id="log_ki"></div></div>
</section>

<section id="netzplanung"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Netzplanung &amp; Einnahmen</h2>
<span id="gp_quelle" class="status"></span><button class="k" onclick="gpCsv()">Als CSV speichern</button><button class="k p" onclick="gpLaden()">Berechnen</button></div>
<p class="hint">Gateway-Standorte, Glasfaser von Sparte zu Sparte, 55 Parzellen je Gateway und einstellbare Buchungsquote – dieselbe Rechnung wie die Excel „Kleingarten_Gateway_Planung“. <b>Theoretische Einnahme</b> = Parzellen × Buchungsquote × Ø Tarifpreis. Rechnet nur hier im Manager – am Gateway ändert sich nichts.</p>
<div class="kacheln" id="gp_k"></div><div class="log" id="log_gp"></div></div>
<div class="karte"><h3>Einnahmen nach Tarif und Buchungsquote</h3>
<p class="hint">Preise aus dem Reiter „Tarife“. Der Tarifmix legt fest, wie sich die Kunden auf die Tarife verteilen (Anteile in %, werden auf 100 % umgerechnet). „Quote manuell“ in der Tabelle gilt immer vorrangig.</p>
<div class="reihe"><div><label for="gp_pq">Preis je Kunde</label><select id="gp_pq"><option value="tarife">nach Tarifmix</option><option value="fest">fester Preis (Einstellungen)</option></select></div>
<div><label for="gp_qm">Buchungsquote</label><select id="gp_qm"><option value="1">aus Alter und Leerstand</option><option value="2">feste Quote für alle</option></select></div>
<div><label for="gp_qf">Feste Quote (%)</label><input id="gp_qf" inputmode="decimal"></div>
<div><label for="gp_sz">Alter und Leerstand</label><select id="gp_sz"><option value="1">heute</option><option value="2">in 5 Jahren</option></select></div></div>
<div class="reihe" id="gp_mix" style="margin-top:10px"></div>
<div class="knoepfe"><button class="k p" onclick="gpSchnell()">Übernehmen</button></div>
<div class="tab" id="gp_tt"></div><div class="log" id="log_gps"></div></div>
<div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Je Sparte</h3>
<input id="gp_such" placeholder="Sparte suchen …" oninput="gpTabelle()" style="max-width:200px"><select id="gp_stf" onchange="gpTabelle()" style="max-width:220px"></select>
<label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="gp_err" onchange="gpTabelle()" style="width:auto"> nur Fehler</label></div>
<p class="hint">Gelbe Felder werden sofort gespeichert. <b>Standort</b> = Nr. der Sparte, in der die Gateways stehen (eigene Nr. = selbst Standort). <b>Zuleitung von</b> = Nr. der Sparte, von der die Glasfaser kommt. <b>Reihenfolge</b> = welche Sparte die Gateways zuerst füllt. Kette A → B → C → D: alle Standort A, B Zuleitung A, C Zuleitung B, D Zuleitung C. Leer = Vorschlag bzw. berechneter Wert (grau).</p>
<div class="tab" id="gp_tab" style="--tab-h:640px"></div></div>
<div class="karte" data-bereich="netzplanung"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">VLAN-Plan je Gateway</h3>
<select id="gv_st" onchange="gvZeigen()" style="max-width:280px"></select><button class="k" onclick="gvCsv()">VLAN-Liste als CSV</button></div>
<p class="hint"><b>Schema</b> (eindeutig je Standort, alle Gateways eines Standorts hängen an derselben Glasfaser): Parzelle = <span class="mono">1000 + 200 × (VLAN-Block − 1) + Parzelle</span> – die letzten beiden Ziffern sind die Parzellennummer (Block 1: 1001–1199, Block 2: 1201–1399 … Block 15: 3801–3999). Dienstnetze je Sparte: Vorstand <span class="mono">100 + Sparten-ID</span>, Gäste <span class="mono">200 + ID</span>, Technik <span class="mono">300 + ID</span> (überall eindeutig). Subnetze <span class="mono">10.&lt;Sparten-ID&gt;.&lt;Parzelle&gt;.0/24</span>. VLAN-Block = Reihenfolge am Standort, in der Tabelle oben fest einstellbar. Je Gateway höchstens 55 Parzellen + Vorstand/Gäste/Technik der Sparten, die dort beginnen.</p>
<div class="tab" id="gv_tab"></div><div class="log" id="log_gv"></div></div>
<div class="karte" data-bereich="netzplanung" id="zt_karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Gateway-Zuteilung nach Buchung</h3><span id="zt_st" class="status"></span><button class="k" onclick="ztLaden()">Aktualisieren</button></div>
<p class="hint">Eingeschaltet bekommt eine Parzelle ihr VLAN-Netz erst, wenn sie <b>bucht</b> – am ersten Gateway ihres Standorts mit freiem Platz (höchstens <span id="zt_pg">55</span> Parzellen je Gateway). Erst wenn Gateway 1 voll ist, kommt Gateway 2 dran. Wird eine Buchung gelöscht, kann das Netz entfernt werden; der Platz wird dann frei und von der nächsten Buchung zuerst wieder belegt. Die VLAN-ID bleibt fest an der Parzelle (Schema oben), Passwort und Zugangskarte bleiben gleich. Zugeteilte Parzellen werden nie automatisch umgezogen. Dienstnetze (Vorstand/Gäste/Technik) liegen am ersten Gateway des Standorts. <b>Am Gateway ändert sich nur etwas über „Einrichten → Netze nach Buchungen“ mit Vorschau und Bestätigung.</b></p>
<div class="knoepfe zt-schreib"><label style="display:flex;gap:8px;align-items:center;margin:0"><input type="checkbox" id="zt_an" style="width:auto" onchange="ztSchalten()"> Gateway-Zuteilung nach Buchung eingeschaltet</label><button class="k" onclick="ztAbgleichen()">Mit Buchungen abgleichen</button></div>
<select id="zt_stf" onchange="ztZeigen()" style="max-width:280px;margin:6px 0"></select><div class="tab" id="zt_tab"></div><div class="log" id="log_zt"></div></div>
<div class="karte"><h3>Gateway-Standorte</h3><p class="hint">Alle Gateways eines Standorts teilen sich einen Internet-Anschluss – ein weiterer erst, wenn der Bedarf größer ist als die Kapazität.</p><div class="tab" id="gp_st"></div></div>
<div class="karte"><h3>Einstellungen</h3><p class="hint">Netz-Regeln, Buchungsquote, Kosten und Preise. Leeres Feld = Standardwert.</p><div id="gp_an"></div>
<div class="knoepfe"><button class="k p" onclick="gpAnSpeichern()">Einstellungen speichern</button><button class="k" onclick="gpReset('annahmen')">Auf Standard zurücksetzen</button></div><div class="log" id="log_gpa"></div></div>
<div class="karte"><h3>Aus Excel übernehmen</h3><p class="hint"><b>Kleingarten_Gateway_Planung.xlsx</b>: Sparten (Parzellen, Leerstand, Alter, Lage), Ihre gelben Spalten (Standort, Zuleitung, Reihenfolge, Quote …) und alle Annahmen. Ohne Import rechnet der Manager mit den eingebauten Daten aus dem Kleingartenentwicklungskonzept 2040.</p>
<div class="knoepfe"><label class="k">Gateway-Planung (Excel) wählen …<input type="file" id="gp_datei" accept=".xlsx" onchange="gpImport()" style="display:none"></label>
<button class="k" onclick="gpReset('wahl')">Eigene Zuordnungen löschen (Vorschlag)</button><button class="k" onclick="gpReset('daten')">Eingebaute Daten verwenden</button></div><div class="log" id="log_gpi"></div></div>
</section>

<section id="kartendesign"><div class="karte" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
<h2 style="margin:0;flex:1;min-width:200px">Zugangskarten gestalten</h2><span id="kd_status"></span>
<button class="k p" onclick="designSpeichern()">Speichern</button><button class="k" onclick="testdruck()">Testseite drucken</button><button class="k" onclick="designStandard()">Standard wiederherstellen</button></div>
<div class="kd" id="kd_box"><div id="kd_form"></div><div class="teiler" data-k="kd" data-box="kd_box" title="Ziehen: Breite der Einstellungen ändern"></div>
<div class="vorschau"><iframe id="kd_vor" title="Vorschau Zugangskarte"></iframe><div class="log" id="log_kd"></div></div></div></section>

<section id="system"><div class="karte bn-admin" id="si_karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Datensicherung</h2><button class="k" onclick="siLaden()">Aktualisieren</button></div>
<p class="hint">Eine Datei mit allem: Einstellungen, Planung, Buchungen, Netzplanung, Benutzer (nur Prüfsummen), Passwörter je Parzelle, WLAN-/Tarif-Sicherungen, Kartenlogo, Unterlagen und Änderungsprotokoll. <b>Mit Passwort</b> wird die Datei verschlüsselt (AES-256) – ohne Passwort enthält sie WLAN-Passwörter und den Cloud-Key im Klartext. Das Passwort gut aufheben: ohne es lässt sich die Sicherung nicht einspielen.</p>
<div class="reihe"><div><label for="si_pw">Passwort für die Sicherung (mind. 10 Zeichen, empfohlen)</label><input id="si_pw" type="password" autocomplete="new-password"></div>
<div><label for="si_pw2">Passwort wiederholen</label><input id="si_pw2" type="password" autocomplete="new-password"></div></div>
<div class="knoepfe"><button class="k p" onclick="siHerunterladen()">Sicherung herunterladen</button><button class="k" onclick="siJetzt()">Jetzt auf dem Server sichern</button></div>
<h3>Automatisch auf dem Server</h3><div class="reihe"><div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="si_auto" style="width:auto"> täglich sichern</label></div>
<div><label for="si_uhr">um … Uhr</label><input id="si_uhr" inputmode="numeric"></div><div><label for="si_anz">Anzahl behalten</label><input id="si_anz" inputmode="numeric"></div></div>
<div class="knoepfe"><button class="k" onclick="siEinstellungen()">Speichern</button></div><div class="tab" id="si_liste"></div>
<details style="margin-top:12px"><summary style="cursor:pointer;font-weight:600">Sicherung einspielen</summary><p class="hint">Ersetzt <b>alle</b> Daten des Managers durch die Sicherung. Der jetzige Stand wird vorher automatisch auf dem Server gesichert. Am Gateway ändert sich nichts.</p>
<div class="reihe"><div><label for="si_ein_pw">Passwort der Sicherung (falls verschlüsselt)</label><input id="si_ein_pw" type="password" autocomplete="off"></div>
<div><label class="k" style="margin-top:22px;display:inline-block">Sicherung wählen und einspielen …<input type="file" id="si_datei" accept=".zip,.sns" onchange="siEinspielen()" style="display:none"></label></div></div></details>
<div class="log" id="log_si"></div></div>
<div class="karte bn-admin" id="up_karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Aktualisierung</h2><span id="up_st" class="status"></span>
<button class="k" onclick="upPruefen()">Nach Updates suchen</button><button class="k p" id="up_los" onclick="upInstallieren()" hidden>Jetzt aktualisieren</button></div>
<p class="hint">Wie bei Nextcloud: Der Manager fragt GitHub nach einer neueren Version, sichert die Daten, lädt die neue Version, prüft sie, testet sie und startet dann neu – ohne Docker-Neubau. Die neue Version liegt im Datenordner unter <span class="mono">updates/</span>; „Vorherige Version“ schaltet jederzeit zurück (startet eine neue Version nicht, geschieht das automatisch).</p>
<div class="kacheln" id="up_k"></div><div id="up_notiz"></div><div id="up_schritte"></div>
<details style="margin-top:10px"><summary style="cursor:pointer;font-weight:600">Einstellungen und installierte Versionen</summary>
<div class="reihe" style="margin-top:10px"><div><label for="up_kanal">Quelle (Kanal)</label><select id="up_kanal"><option value="main">main – jeder Stand auf GitHub main</option><option value="release">release – nur veröffentlichte GitHub-Releases</option><option value="branch">anderer Zweig …</option></select></div>
<div><label for="up_zweig">Zweig (nur bei „anderer Zweig“)</label><input id="up_zweig" placeholder="z. B. manager-4.6"></div>
<div><label for="up_std">Automatisch prüfen alle … Stunden (0 = aus)</label><input id="up_std" inputmode="numeric"></div>
<div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="up_auto" style="width:auto"> automatisch installieren (nachts 2–5 Uhr)</label></div></div>
<div class="knoepfe"><button class="k p" onclick="upEinstellungen()">Speichern</button><button class="k" id="up_zurueck" onclick="upZurueck()">Vorherige Version</button></div>
<div class="tab" id="up_versionen"></div></details><div class="log" id="log_up"></div></div>
<div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Systeminfo</h2>
<label style="display:flex;align-items:center;gap:8px;margin:0;font-size:14px;color:var(--text)"><input type="checkbox" id="sys_auto" style="width:auto" onchange="sysAuto()"> alle 60 s aktualisieren</label>
<button class="k p" onclick="sysLaden()">Aktualisieren</button></div>
<div class="log" id="log_sys"></div><div class="kacheln" id="sys_k"></div></div>
<div class="karte"><h3>Internet – letzte 24 Stunden</h3><p class="hint" id="sys_ch_hint">Messwerte der UniFi-Cloud im 5-Minuten-Raster.</p><div id="sys_ch1" class="chart"></div><div id="sys_ch2" class="chart"></div>
<details style="margin-top:10px"><summary style="cursor:pointer;font-size:13px;color:var(--muted)">Rohwerte der UniFi-Cloud (letzter Messpunkt)</summary><pre class="json" id="sys_isp_roh"></pre></details></div>
<div class="karte"><h3>Geräte – Auslastung</h3><div class="tab" id="sys_ger"></div></div>
<div class="karte"><h3>Clients und Datenverkehr je Netz</h3><p class="hint" id="sys_netz_hint"></p><div class="tab" id="sys_netz"></div></div>
<div class="karte" id="sys_top_k" style="display:none"><h3>Größte Verbraucher (seit Verbindungsbeginn)</h3><div class="tab" id="sys_top"></div></div></section>

<section id="daten"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Alle Daten</h2>
<label style="display:flex;align-items:center;gap:8px;margin:0;font-size:14px;color:var(--text)"><input type="checkbox" id="d_geheim" style="width:auto" onchange="if(DAKT)datenLaden(DAKT)"> Passwörter/Schlüssel anzeigen</label>
<button class="k p" onclick="datenPruefen()">Verfügbarkeit prüfen</button></div>
<p class="hint">Alles, was die Konsole über die Cloud lesen lässt – nur lesend, am Gateway wird nichts geändert. Links eine Quelle wählen.</p><div class="log" id="log_d"></div></div>
<div class="dgrid" id="d_box"><div class="dliste" id="d_liste"></div><div class="teiler" data-k="dl" data-box="d_box" title="Ziehen: Breite der Liste ändern"></div>
<div class="karte" style="min-width:0"><h3 id="d_titel">–</h3><p class="hint mono" id="d_pfad"></p>
<div class="knoepfe" style="margin-top:4px"><input id="d_filter" placeholder="Filtern …" oninput="datenZeigen()" style="max-width:240px"><button class="k" id="d_btn_tab" onclick="DANS='tab';datenZeigen()">Tabelle</button><button class="k" onclick="DANS='json';datenZeigen()">JSON</button>
<button class="k" onclick="datenJson()">Als JSON speichern</button><button class="k" onclick="datenCsv()">Als CSV</button></div>
<div class="tab" id="d_tab"></div><pre class="json" id="d_json" style="display:none"></pre></div></div></section>

<section id="voucher"><div class="karte" data-bereich="voucher"><h2>Gast-Voucher erstellen</h2>
<p class="hint">Vorlage wählen, Anzahl eingeben, „Vorschau“ – dann „Erstellen“: die Voucher werden am Gateway angelegt und können sofort gedruckt werden.</p>
<div class="reihe"><div><label for="v_vorlage">Vorlage</label><select id="v_vorlage" onchange="vVorlageInfo()"></select></div>
<div><label for="v_anz">Anzahl</label><input id="v_anz" type="number" value="10" min="1" max="1000"></div>
<div><label for="v_name">Bezeichnung am Gateway (leer = Name der Vorlage)</label><input id="v_name" maxlength="40"></div></div>
<p class="hint" id="v_info" style="margin-top:8px"></p>
<div class="reihe"><div><label for="v_wlan">Gast-WLAN auf dem Ausdruck</label><select id="v_wlan"></select></div>
<div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="v_jetzt" style="width:auto"> „Gültig bis“ ab jetzt berechnen (Ausgabe sofort)</label></div></div>
<div class="knoepfe"><button class="k" onclick="voucher(false)">Vorschau</button><button class="k p" onclick="voucher(true)">Erstellen und übertragen</button><button class="k" onclick="voucherDruck()">Drucken (Kartendesign)</button><button class="k" onclick="voucherEtiketten()">Kleine Etiketten</button></div>
<div class="log" id="log_vo"></div><div class="tab" id="tab_vo"></div></div>
<div class="karte" data-bereich="voucher"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Vorlagen</h3><button class="k vv-schreib" onclick="vvNeu()">Neue Vorlage</button><button class="k p vv-schreib" onclick="vvSpeichern()">Vorlagen speichern</button></div>
<p class="hint">Gültigkeit ab der ersten Anmeldung, Geräte je Voucher, Datenvolumen und Bandbreite (0 = unbegrenzt), Text für den Ausdruck. Vorlagen liegen im Manager; aus den Vouchern am Gateway werden unten Vorschläge gemacht.</p>
<div class="tab" id="vv_tab"></div><div class="log" id="log_vv"></div></div>
<div class="karte" data-bereich="voucher"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Voucher am Gateway</h3><span id="vl_st" class="status"></span>
<select id="vl_f" onchange="vlZeigen()" style="max-width:200px"><option value="">alle</option><option>unbenutzt</option><option>in Benutzung</option><option>voll belegt</option><option>abgelaufen</option></select><button class="k" onclick="vlLaden()">Auslesen</button></div>
<div class="tab" id="vl_tab" style="--tab-h:520px"></div>
<div class="knoepfe"><button class="k" onclick="vlAuswahl('abgelaufen')">Abgelaufene auswählen</button><button class="k" onclick="vlDrucken()">Ausgewählte drucken (Kartendesign)</button><button class="k r vv-schreib" onclick="vlLoeschen()">Ausgewählte löschen …</button></div>
<div id="vl_vs"></div><div class="log" id="log_vl"></div></div></section>

<section id="unterlagen"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Unterlagen</h2><span id="ul_st" class="status"></span><button class="k" onclick="ulLaden()">Aktualisieren</button></div>
<p class="hint">Verträge, Pläne, Protokolle, Rechnungen … allgemein oder je Sparte hinterlegen. Erlaubt: PDF, Bilder, Office-/OpenOffice-Dateien, CSV, Text, ZIP – keine Webseiten, SVG oder Programme. PDF und Bilder lassen sich direkt ansehen, alles andere wird heruntergeladen.</p>
<div class="reihe"><div><label for="ul_such">Suchen</label><input id="ul_such" placeholder="Name oder Beschreibung …" oninput="ulZeigen()"></div>
<div><label for="ul_f_ordner">Ordner</label><select id="ul_f_ordner" onchange="ulZeigen()"></select></div><div><label for="ul_f_sparte">Sparte</label><select id="ul_f_sparte" onchange="ulZeigen()"></select></div></div>
<div class="tab" id="ul_tab" style="--tab-h:620px"></div><div class="log" id="log_ul"></div></div>
<div class="karte" data-bereich="unterlagen" id="ul_hoch"><h3>Hochladen</h3>
<div id="ul_zone" style="border:2px dashed var(--line);border-radius:10px;padding:22px;text-align:center;color:var(--muted);cursor:pointer" onclick="$('ul_datei').click()">Dateien hierher ziehen oder <u>auswählen</u><input type="file" id="ul_datei" multiple style="display:none" onchange="ulHoch(this.files)"></div>
<div class="reihe" style="margin-top:10px"><div><label for="ul_ordner">Ordner</label><input id="ul_ordner" list="ul_ordnerliste" value="Allgemein"><datalist id="ul_ordnerliste"></datalist></div>
<div><label for="ul_sparte">Sparte</label><select id="ul_sparte"></select></div><div><label for="ul_beschr">Beschreibung (optional)</label><input id="ul_beschr" maxlength="300"></div></div>
<div class="log" id="log_ulh"></div></div></section>

<section id="automationen"><div class="karte" data-bereich="automationen"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Automationen</h2><span id="au_st" class="status"></span><button class="k" onclick="auLaden()">Aktualisieren</button><button class="k p au-schreib" onclick="auNeu()">Neue Regel</button></div>
<p class="hint">Wenn etwas passiert (eine Parzelle bucht, kündigt, eine Zahlung kommt über die API herein …), führt der Manager die hinterlegten Aktionen aus: E-Mail senden, Tarif buchen, Webhook aufrufen, Protokolleintrag. <b>Am Gateway ändert eine Automation nichts</b> – Übertragen bleibt ein Schritt mit Vorschau und Bestätigung (Reiter „Tarife“ bzw. „Übertragen“).</p>
<div class="tab" id="au_tab"></div><div class="log" id="log_au"></div></div>
<div class="karte au-schreib" id="au_edit" hidden><h3 id="au_edit_t">Regel</h3>
<div class="reihe"><div><label for="au_name">Name</label><input id="au_name" maxlength="80" placeholder="z. B. Willkommens-Mail bei Buchung"></div>
<div><label for="au_aus">Wenn …</label><select id="au_aus" onchange="auAusWechsel()"></select></div>
<div id="au_evn_w" hidden><label for="au_evn">Name des Ereignisses (API)</label><input id="au_evn" placeholder="z. B. mahnung" maxlength="40"></div>
<div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="au_aktiv" style="width:auto" checked> aktiv</label></div></div>
<h3>Nur wenn … (leer = immer)</h3><div class="reihe"><div><label for="au_b_sp">Sparte</label><select id="au_b_sp"></select></div><div><label for="au_b_tf">Tarif</label><select id="au_b_tf"></select></div>
<div><label for="au_b_bt">Betrag mindestens (€, nur Zahlung)</label><input id="au_b_bt" inputmode="decimal"></div></div>
<h3>Dann …</h3><div id="au_akt"></div>
<div class="knoepfe"><select id="au_neu_typ" style="max-width:240px"></select><button class="k" onclick="auAktionNeu()">Aktion hinzufügen</button></div>
<details style="margin-top:8px"><summary style="cursor:pointer">Platzhalter für Betreff und Text</summary><div class="tab" id="au_ph"></div></details>
<div class="knoepfe"><button class="k p" onclick="auSpeichern()">Regel speichern</button><button class="k" onclick="auProbe()">Probelauf (sendet und bucht nichts)</button><button class="k" onclick="$('au_edit').hidden=true">Abbrechen</button></div><div class="log" id="log_aue"></div></div>
<div class="karte" data-bereich="automationen"><h3>Verlauf</h3><p class="hint">Die letzten ausgeführten Aktionen (höchstens 300 werden aufbewahrt).</p><div class="tab" id="au_verlauf" style="--tab-h:360px"></div></div>
<div class="karte bn-admin"><h3>E-Mail-Versand (SMTP)</h3><p class="hint">Postfach, über das die Automationen E-Mails senden (z. B. das Vereins-Postfach beim Provider). Das Passwort wird nicht angezeigt; leer lassen = unverändert. Alternativ als Docker-Secret: <span class="mono">SPARTENET_SMTP_PASSWORD_FILE</span>.</p>
<div class="reihe"><div><label for="sm_host">Server</label><input id="sm_host" placeholder="smtp.example.de"></div><div><label for="sm_port">Port</label><input id="sm_port" inputmode="numeric"></div>
<div><label for="sm_sich">Verschlüsselung</label><select id="sm_sich"><option value="starttls">STARTTLS (Port 587)</option><option value="ssl">SSL/TLS (Port 465)</option><option value="keine">keine (nur im eigenen Netz)</option></select></div></div>
<div class="reihe"><div><label for="sm_ben">Benutzername</label><input id="sm_ben" autocomplete="off"></div><div><label for="sm_pw">Passwort</label><input id="sm_pw" type="password" autocomplete="new-password"></div>
<div><label for="sm_abs">Absender-Adresse</label><input id="sm_abs" placeholder="wlan@verein.de"></div><div><label for="sm_absn">Absender-Name</label><input id="sm_absn"></div></div>
<div class="knoepfe"><button class="k p" onclick="smSpeichern()">Speichern</button><input id="sm_test_an" placeholder="Test an …" style="max-width:240px"><button class="k" onclick="smTest()">Test-E-Mail senden</button></div><div class="log" id="log_sm"></div></div>
<div class="karte bn-admin"><h3>API-Schnittstelle für andere Programme</h3><p class="hint">Andere Programme (Buchhaltung, Zahlungseingang, n8n, Zapier, Home Assistant …) melden Ereignisse oder buchen Tarife. Jeder Schlüssel bekommt nur die nötigen Rechte und optional nur bestimmte Sparten. Der Schlüssel wird <b>nur einmal</b> angezeigt und nur als Prüfsumme gespeichert. Höchstens <span id="api_min"></span> Anfragen je Minute und Schlüssel.</p>
<div class="tab" id="api_tab"></div>
<h3>Neuer Schlüssel</h3><div class="reihe"><div><label for="api_name">Name</label><input id="api_name" placeholder="z. B. Buchhaltung"></div><div><label for="api_sp">Nur Sparten (Kürzel, Komma; leer = alle)</label><input id="api_sp"></div></div>
<div id="api_rechte" style="display:flex;gap:16px;flex-wrap:wrap;margin:6px 0"></div>
<div class="knoepfe"><button class="k p" onclick="apiNeu()">Schlüssel erzeugen</button></div><div id="api_neu" hidden class="hinweis" style="margin:8px 0"></div><div class="log" id="log_api"></div>
<details style="margin-top:10px"><summary style="cursor:pointer;font-weight:600">Beispiele</summary><pre class="mono" id="api_bsp" style="white-space:pre-wrap;font-size:12px;background:var(--bg2,#f4f6f2);padding:10px;border-radius:8px"></pre>
<p class="hint">Zahlungsanbieter (Bank, PayPal, Stripe …) senden ihre eigenen Formate – dazwischen übersetzt z. B. n8n, Zapier oder Make die Meldung in einen Aufruf von <span class="mono">/api/v1/ereignis</span>. Der Manager muss dafür von dort erreichbar sein (z. B. über den Reverse-Proxy, nur HTTPS).</p></details></div></section>

<section id="benutzer"><div class="karte"><h2>Mein Konto</h2><div class="kacheln" id="bn_ich"></div>
<div class="tab" id="bn_ich_liste" style="--tab-h:420px"></div>
<div id="bn_ich_pw"><h3>Eigenes Passwort ändern</h3><div class="reihe" style="max-width:820px"><div><label for="bn_alt">Bisheriges Passwort</label><input id="bn_alt" type="password" autocomplete="current-password"></div>
<div><label for="bn_neu1">Neues Passwort (mind. 12 Zeichen)</label><input id="bn_neu1" type="password" autocomplete="new-password"></div><div><label for="bn_neu2">Neues Passwort wiederholen</label><input id="bn_neu2" type="password" autocomplete="new-password"></div></div>
<div class="knoepfe"><button class="k p" onclick="bnEigenesPw()">Passwort ändern</button></div></div>
<div id="bn_2fa"><h3>Zwei-Faktor-Anmeldung</h3><p class="hint" id="bn_2fa_st"></p>
<div class="knoepfe"><button class="k p" id="bn_2fa_ein" onclick="zfStart()">Einrichten</button><button class="k" id="bn_2fa_aus" onclick="zfAus()">Ausschalten</button></div>
<div id="bn_2fa_neu" hidden><div style="display:flex;gap:18px;flex-wrap:wrap;align-items:center"><div id="bn_2fa_qr" style="width:200px;background:#fff;padding:8px;border:1px solid var(--line);border-radius:8px"></div>
<div><p class="hint">1. QR-Code mit der Authenticator-App scannen (z. B. Google/Microsoft Authenticator, Aegis, 2FAS) – oder den Schlüssel eintippen:<br><b class="mono" id="bn_2fa_geheim"></b></p>
<label for="bn_2fa_code">2. Angezeigten Code eingeben</label><div style="display:flex;gap:8px"><input id="bn_2fa_code" inputmode="numeric" maxlength="6" style="max-width:140px"><button class="k p" onclick="zfBestaetigen()">Bestätigen</button></div></div></div></div>
<div id="bn_2fa_notfall" hidden></div></div>
<p class="hint" id="bn_admin_hint" hidden>Das Konto „admin“ meldet sich mit dem Manager-Passwort an. Geändert wird es in der Docker-Konfiguration (Secret spartenet_password) – danach den Manager neu starten.</p>
<div class="knoepfe"><button class="k" onclick="abmelden()">Abmelden</button></div><div class="log" id="log_bni"></div></div>
<div class="karte bn-admin"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Benutzerkonten</h3><button class="k" onclick="bnLaden()">Aktualisieren</button></div>
<p class="hint"><b>Administrator</b>: alles, auch Benutzerkonten. <b>Gesperrt</b>: keine Anmeldung, offene Sitzungen enden sofort. <b>Rechte je Bereich</b>: für jedes Arbeitsblatt bzw. jede Funktion einzeln <i>kein Zugriff</i> (ausgeblendet), <i>lesen</i> (ansehen, Vorschau) oder <i>lesen und schreiben</i> (ändern, ans Gateway übertragen) – z. B. alles nur lesen, aber WLAN-Passwörter schreiben und Tarife buchen. „Rechte“ öffnet die Liste; jede Änderung wird sofort gespeichert.</p>
<label style="display:flex;gap:8px;align-items:center;margin:8px 0"><input type="checkbox" id="bn_2fa_pflicht" style="width:auto" onchange="zfPflicht(this.checked)"> Zwei-Faktor-Anmeldung für alle Administratoren verpflichtend</label>
<div class="tab" id="bn_tab" style="--tab-h:900px"></div><div class="log" id="log_bn"></div></div>
<div class="karte bn-admin"><h3>Neues Benutzerkonto</h3>
<div class="reihe"><div><label for="bn_name">Benutzername</label><input id="bn_name" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="z. B. vorstand.buchenweg"></div>
<div><label for="bn_anz">Name (Anzeige, optional)</label><input id="bn_anz" placeholder="z. B. Maria Muster, Vorstand Buchenweg"></div>
<div><label for="bn_vorlage">Rechte (Vorlage – danach je Bereich anpassbar)</label><select id="bn_vorlage"></select></div>
<div><label for="bn_pw1">Passwort (mind. 12 Zeichen)</label><input id="bn_pw1" type="password" autocomplete="new-password"></div>
<div><label for="bn_pw2">Passwort wiederholen</label><input id="bn_pw2" type="password" autocomplete="new-password"></div></div>
<div class="knoepfe"><button class="k p" onclick="bnAnlegen()">Konto anlegen</button><button class="k" onclick="bnVorschlag()">Passwort vorschlagen</button><span id="bn_vorschlag" class="mono"></span></div><div class="log" id="log_bnn"></div></div>
</section>

<section id="hilfe"><div class="karte"><h2>Hilfe</h2><p class="hint">
<b>Schema:</b> Parzelle p auf Steckplatz n → VLAN 1000 + n·100 + p (Buchenweg: Parzelle 25 = VLAN 1125), Netz 10.&lt;Sparten-ID&gt;.p.0/24, Router .1, Geräte .10–.250. Vorstand 2000+n·10+1, Gäste +2, Technik +9. Namen BW-Paz.025, BW-Vorstand, BW-Gäste, BW-Technik.<br><br>
<b>Neue Sparte:</b> „Planung“ → Zeile anhängen, speichern · „Abgleich“ · „Einrichten“ Schritt 1–4 · Zugangskarten drucken · mit Handy testen.<br><br>
<b>Zugangskarten:</b> Aussehen im Reiter „Kartendesign“ einstellen und speichern – gedruckt wird unter „Einrichten“ Schritt 3. Logo-Datei und Design liegen im Programmordner.<br><br>
<b>Passwörter ändern:</b> „Einrichten“ Schritt 3 → „Anzeigen“, Passwort in der Tabelle ändern, „Änderungen speichern“. Dann Reiter „Übertragen“ → „Unterschiede ermitteln“ → „Ausgewählte übertragen“ und die Karte neu drucken.<br><br>
<b>Handy &amp; Tablet:</b> „Verbindung → Handy &amp; Tablet“: optional eine Handy-PIN festlegen, Tailscale-Freigabe (von überall, echte App) oder Heimnetz einschalten, QR-Code mit dem Handy scannen, Manager-Passwort oder PIN eingeben, „App installieren“. Der PC mit dem Manager muss dabei laufen.<br><br>
<b>Kalkulation:</b> Reiter „Kalkulation“ → „Aus Excel übernehmen“ (Kalkulation und/oder VLAN-Planer) · Buchungen je Parzelle erfassen (oder über „Tarife“) · Tabelle „Je Sparte“ zeigt Umsatz, Buchungsrate, Kosten, Deckungsbeitrag; oben die Gesamtauslastung aller Sparten mit Buchungen.<br><br>
<b>Tarife:</b> Reiter „Tarife“ → Tarife festlegen (Bandbreite Download/Upload, Netzmaske, Endgeräte) und speichern · „Netze laden“ · je Netz einen Tarif wählen (oder markieren und „für markierte setzen“) · „Zuordnung speichern“ · unten „Vorschau“, dann „Ausgewählte übertragen“. Bandbreite → QoS-Regel „SparteNet-Tarif-…“, Netzgröße → Subnetz und DHCP-Bereich des Netzes. Ein /29 mit DHCP .2–.6 lässt genau 5 Geräte zu, ein /28 mit .2–.11 genau 10.<br><br>
<b>Übertragen:</b> Erst „Schreibzugriff prüfen“. Wird das abgelehnt (403), den API-Key auf unifi.ui.com als Besitzer bzw. Super-Admin neu erstellen.<br><br>
<b>Systeminfo / Alle Daten:</b> nur lesend. Datenverkehr je Parzelle und einige Quellen der klassischen Schnittstelle gibt die Konsole über die Cloud nicht immer frei – „Alle Daten → Verfügbarkeit prüfen“ zeigt, was geht.<br><br>
<b>API-Key:</b> unifi.ui.com → Einstellungen → API Keys, angemeldet als Besitzer der Konsole. Der Key aus der Network-App („Integrationen“) funktioniert über die Cloud nicht.</p></div></section>
</main>
<script>
const T="__TOKEN__";let LETZT=null,PLAN=null,PLANZ=null,PPSK=null,PPSKSP=null,CODES=[],VMIN=0,EINST={};
const TABS=[["start","Start"],["verbindung","Verbindung"],["lesen","Auslesen"],["planung","Planung"],["abgleich","Abgleich"],["einrichten","Einrichten"],["uebertragen","Übertragen"],["tarife","Tarife"],["kalkulation","Kalkulation"],["netzplanung","Netzplanung"],["kartendesign","Kartendesign"],["voucher","Gast-Voucher"],["system","Systeminfo"],["daten","Alle Daten"],["unterlagen","Unterlagen"],["automationen","Automationen"],["benutzer","Benutzer"],["hilfe","Hilfe"]];
const $=id=>document.getElementById(id);const nav=$("nav");TABS.forEach(([id,t])=>{const b=document.createElement("button");b.textContent=t;b.onclick=()=>zeige(id);b.id="n_"+id;nav.appendChild(b)});
function zeige(id){if(!reiterErlaubt(id))id=startReiter();rechteHinweis(id);if(id=="start"&&!$("st_k").innerHTML&&typeof EINST!="undefined"&&EINST.konsole_id)startLaden().catch(()=>{});if(id=="verbindung")fernLaden().catch(()=>{});if(location.hash!="#"+id)history.replaceState(null,"","#"+id);setTimeout(()=>{const b=document.querySelector("nav button.aktiv");if(b&&b.scrollIntoView)b.scrollIntoView({inline:"center",block:"nearest"})},0);if(id=="kalkulation"&&!KK)kkLaden().catch(()=>{});if(id=="netzplanung"&&!GP)gpLaden().catch(()=>{});if(id=="netzplanung")ztLaden().catch(()=>{});if(id=="benutzer")bnStart();if(id=="unterlagen")ulLaden().catch(()=>{});if(id=="voucher"&&!VV)vvLaden().catch(()=>{});if(id=="automationen")auLaden().catch(()=>{});if(id=="system"&&ICH.admin){upLaden(true).catch(()=>{});siLaden().catch(()=>{})}if(id=="kartendesign"&&!DESIGN)designLaden();if(id=="tarife"&&!TF)tfLaden();if(id=="system"&&!SYS)sysLaden();if(id=="daten"&&!DLISTE)datenListe();document.querySelectorAll("section").forEach(s=>s.classList.toggle("aktiv",s.id==id));document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("aktiv",b.id=="n_"+id))}
async function api(pfad,body,logid){const el=logid&&$(logid);const kn=[...document.querySelectorAll("button")];kn.forEach(b=>b.disabled=true);if(el)el.textContent="… bitte warten (über die Cloud kann das einige Sekunden dauern)";
 try{const r=await fetch(pfad,{method:body===undefined?"GET":"POST",headers:{"X-Token":T,"Content-Type":"application/json"},body:body===undefined?undefined:(body instanceof Blob?body:JSON.stringify(body))});
 if(r.status==401){location.reload();return new Promise(()=>{})}const d=await r.json().catch(()=>({}));if(d.zweiter_faktor_fehlt&&typeof zeige=="function"&&!document.querySelector("#benutzer.aktiv"))zeige("benutzer");if(r.status==403&&!d.recht){location.reload();return new Promise(()=>{})}if(!r.ok)throw new Error(d.fehler||r.status);if(el)el.textContent=d.log?d.log.join("\n"):"";return d}
 catch(e){if(el)el.innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>';throw e}finally{kn.forEach(b=>b.disabled=false)}}
function esc(s){return String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
const SK=s=>Array.isArray(s)?s[0]:s,SL=s=>Array.isArray(s)?(s[1]||s[0]):s,SC=s=>Array.isArray(s)&&s[2]?" class='"+s[2]+"'":"";
function tabelle(id,sp,z,kl){$(id).innerHTML=z.length?"<table><tr>"+sp.map(s=>"<th>"+esc(SL(s))+"</th>").join("")+"</tr>"+z.map(r=>"<tr class='"+(kl?kl(r):"")+"'>"+sp.map(s=>"<td"+SC(s)+">"+esc(r[SK(s)])+"</td>").join("")+"</tr>").join("")+"</table>":""}
function csvWert(v){let s=String(v??"");if(/^[=+\-@\t\r]/.test(s)&&!/^-?\d+([.,]\d+)?( ?%| ?€)?$/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"'}
function csvSpeichern(d,name){if(!d||!d.zeilen.length)return alert("Keine Daten.");const sp=d.spalten.map(SK);const t="﻿"+[d.spalten.map(SL).join(";")].concat(d.zeilen.map(z=>sp.map(k=>csvWert(z[k])).join(";"))).join("\r\n");
 const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([t],{type:"text/csv"}));a.download=name+".csv";a.click()}
async function logSchalten(){await api("/api/einstellungen",{log_aktiv:$("log_aktiv").checked},"log_datei")}
async function logZeigen(){await api("/api/log",undefined,"log_datei");const el=$("log_datei");el.scrollTop=el.scrollHeight}
async function logLoeschen(){if(confirm("Protokoll leeren?"))await api("/api/log-loeschen",{},"log_datei")}
async function einst(){EINST=await api("/api/einstellungen");if(FERN){try{const a=JSON.parse(localStorage.getItem("sn_ansicht")||"null");if(a){ANS={...ANS_STD,...a};ansAnwenden()}}catch(e){}}else if(EINST.ansicht){ANS={...ANS_STD,...EINST.ansicht};ansAnwenden()}$("log_aktiv").checked=!!EINST.log_aktiv;$("logpfad").textContent=EINST.logdatei;$("speicherort").textContent=EINST.speicher||"";const e=$("key_st");e.textContent=EINST.cloud_key_gesetzt?"hinterlegt":"fehlt";e.className="status"+(EINST.cloud_key_gesetzt?" ok":"");
 if(EINST.konsole_id)$("konsole").innerHTML=`<option value="${esc(EINST.konsole_id)}">${esc(EINST.konsole_name||EINST.konsole_id)}</option>`;$("verb").textContent=EINST.konsole_name?"· "+EINST.konsole_name:"";
 if(!EINST.cloud_key_gesetzt||!EINST.konsole_id)zeige("verbindung");else if(document.querySelector("section.aktiv")?.id=="start"&&!$("st_k").innerHTML)startLaden().catch(()=>{})}
async function konsolenLaden(){const d=await api("/api/konsolen",{cloud_key:$("cloud_key").value},"log_v");$("log_v").textContent="✔ "+d.konsolen.length+" Konsole(n) gefunden – wählen und speichern.";
 $("konsole").innerHTML=d.konsolen.map(k=>`<option value="${esc(k.id)}" ${k.id==EINST.konsole_id?"selected":""}>${esc(k.name)} · ${esc(k.modell)} · ${esc(k.firmware)}</option>`).join("")}
async function speichern(){const k=$("konsole");if(!k.value)return alert("Bitte erst „Konsolen laden“ und eine Konsole wählen.");
 await api("/api/einstellungen",{cloud_key:$("cloud_key").value,konsole_id:k.value,konsole_name:k.selectedOptions[0].text.split(" · ")[0]},"log_v");$("cloud_key").value="";einst()}
async function testen(){await api("/api/test",{},"log_v")}
async function lesen(w){const d=await api("/api/lesen?was="+w,undefined,"log_l");LETZT=d;$("log_l").textContent=d.zeilen.length+" Einträge";tabelle("tab_l",d.spalten,d.zeilen)}
function editor(roh){if(roh.schema=="standort")return editorStandort(roh);$("p_gw").value=roh.gateway;$("p_gwname").value=roh.gatewayname;$("p_pre").value=roh.praefix;const z=[...roh.sparten];while(z.length<10)z.push({name:"",kz:"",sid:"",n:""});
 $("p_tab").innerHTML="<table><tr><th>Steckplatz</th><th>Sparte (Name)</th><th>Kürzel</th><th>Sparten-ID (1–254)</th><th>Parzellen (1–199)</th></tr>"+z.map((s,i)=>`<tr><td>${i+1}</td><td><input data-f="name" value="${esc(s.name)}"></td><td><input data-f="kz" value="${esc(s.kz)}" style="max-width:110px"></td><td><input data-f="sid" type="number" value="${esc(s.sid)}" style="max-width:120px"></td><td><input data-f="n" type="number" value="${esc(s.n)}" style="max-width:120px"></td></tr>`).join("")+"</table>"}
function editorStandort(roh){$("p_gw").value=roh.gateway;$("p_gwname").value=roh.gatewayname;$("p_pre").value=roh.praefix;
 $("p_tab").innerHTML=`<p class="hint" style="padding:10px 12px;margin:0">Diese Planung kommt aus der <b>Netzplanung</b> (Standort ${esc(roh.standort_name||"")}, Gateway ${esc(roh.standort_gw||"")})${roh.dynamisch?" – <b>Gateway-Zuteilung nach Buchung</b>: hier stehen nur die gebuchten Parzellen, die diesem Gateway zugeteilt sind; die Liste aktualisiert sich bei jeder Buchung":""}. VLANs nach dem Standort-Schema. Sparten, Parzellen und VLAN-Blöcke bitte in der Netzplanung ändern und dort neu übernehmen.</p>`+
 "<table><tr><th>VLAN-Block</th><th>Sparte</th><th>Kürzel</th><th>Sparten-ID</th><th>Parzellen an diesem Gateway</th><th>Dienstnetze hier</th></tr>"+roh.sparten.map(s=>`<tr><td>${s.block}</td><td>${esc(s.name)}</td><td class="mono">${esc(s.kz)}</td><td>${s.sid}</td><td>${parzText(s)} von ${s.n}</td><td>${s.dienst?"ja":"–"}</td></tr>`).join("")+"</table>"}
async function planSpeichern(){if(PLAN&&PLAN.roh&&PLAN.roh.schema=="standort"){await api("/api/plan",{...PLAN.roh,gateway:+$("p_gw").value||PLAN.roh.gateway,gatewayname:$("p_gwname").value,praefix:$("p_pre").value||"SparteNet.de"},"log_p");return planLaden(true)}const sp=[...$("p_tab").querySelectorAll("tr")].slice(1).map(tr=>{const o={};tr.querySelectorAll("input").forEach(i=>o[i.dataset.f]=i.type=="number"&&i.value?+i.value:i.value.trim());return o}).filter(s=>s.name);
 await api("/api/plan",{gateway:+$("p_gw").value||1,gatewayname:$("p_gwname").value,praefix:$("p_pre").value||"SparteNet.de",sparten:sp},"log_p");planLaden(true)}
async function excelHoch(){const f=$("xls").files[0];if(f){await api("/api/excel",f,"log_p");planLaden(true)}}
async function planLaden(still){try{PLAN=await api("/api/plan")}catch(e){$("log_p").innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>';return}
 editor(PLAN.roh);zgKarte();const o=PLAN.sparten.map(s=>`<option value="${esc(s.kz)}">${esc(s.name)} (${esc(s.kz)}, ${PLAN.schema=="standort"?"Parzellen "+parzText(s)+", VLAN-Block "+s.block:s.n+" Parzellen, Steckplatz "+s.slot})</option>`).join("");
 $("plan_sp").innerHTML='<option value="">Alle Sparten</option>'+o;$("ein_sp").innerHTML=o;$("ab_sp").innerHTML=o+'<option value="">Alle Sparten</option>';$("ue_sp").innerHTML=o;$("st_sp").innerHTML=o;ssid();planZeigen()}
function ssid(){if(!PLAN)return;const kz=$("ein_sp").value,p=PLAN.praefix;$("ssid1").textContent=p+"-"+kz+"-Pächter";$("ssid2").textContent=p+"-"+kz+"-Gäste";$("ssid3").textContent=p+"-"+kz+"-Vorstand"}
function planZeigen(){if(!PLAN)return;const f=$("plan_sp").value,g=PLAN.gateway_netz;const z=[{bez:"Gateway (Hauptverteiler)",vlan:1,netz:g.netz,maske:"255.255.255.0",router:g.router,geraete:"Technik",zugang:"untagged",t:"kopf"}];
 PLAN.sparten.filter(s=>!f||s.kz==f).forEach(s=>{z.push({bez:(PLAN.schema=="standort"?"VLAN-Block "+s.block+": "+s.name+" ("+s.kz+", ID "+s.sid+", Parzellen "+parzText(s)+")":"Sparte "+s.slot+": "+s.name+" ("+s.kz+", ID "+s.sid+", "+s.n+" Parzellen)"),t:"kopf"});
 PLAN.netze.filter(n=>n.sparte==s.kz).forEach(n=>z.push({bez:n.art=="parzelle"?n.name+"  (Parzelle "+n.parzelle+")":n.name,vlan:n.vlan,netz:n.netz,maske:n.maske,router:n.router,geraete:n.dhcp_start+" – "+n.dhcp_ende,zugang:(n.ssid?n.ssid+" · ":"")+n.zugang,t:n.art=="parzelle"?"":"dienst"}))});
 PLANZ={spalten:[["bez","Netz"],["vlan","VLAN"],["netz","Subnetz"],["maske","Maske"],["router","Router-IP"],["geraete","Geräte-IPs"],["zugang","WLAN / Zugang"]],zeilen:z};tabelle("tab_p",PLANZ.spalten,z,r=>r.t||"")}
function kachel(t,v,a){return `<div class="kachel ${a}"><b>${v}</b>${t}</div>`}
async function abgleich(){const d=await api("/api/abgleich?sparte="+encodeURIComponent($("ab_sp").value),undefined,"log_a");
 $("kach_a").innerHTML=kachel("Netze fehlen",d.fehlen.length,d.fehlen.length?"warn":"gut")+kachel("Netze abweichend",d.abweichend.length,d.abweichend.length?"schlecht":"gut")+kachel("zusätzlich am Gateway",d.extra.length,"")+kachel("Hinweise Geräte/Clients",d.hinweise.length,d.hinweise.length?"schlecht":"gut");
 $("h_hin").textContent=d.hinweise.length?"Hinweise":"";tabelle("tab_hin",[["art","Art"],["name","Name"],["ip","IP"],["hinweis","Hinweis"]],d.hinweise);
 $("h_feh").textContent=d.fehlen.length?"Fehlende Netze ("+d.fehlen.length+")":"";tabelle("tab_feh",[["netz","Netz"],["vlan","VLAN"],["subnetz","Subnetz"]],d.fehlen);
 $("h_abw").textContent=d.abweichend.length?"Abweichungen":"";tabelle("tab_abw",[["netz","Netz laut Plan"],["soll","Soll"],["ist","Ist am Gateway"]],d.abweichend);
 $("h_cli").textContent=d.clients.length?"Verbundene Endgeräte":"";tabelle("tab_cli",[["name","Name"],["ip","IP"],["netz","Netz"]],d.clients)}
async function netze(aus,eins){const kz=$("ein_sp").value;if(!kz)return alert("Erst unter „Planung“ eine Sparte speichern.");
 if(aus&&!confirm((eins?"EIN Netz (das erste fehlende) anlegen?":"ALLE fehlenden Netze anlegen?")+"\nSparte: "+kz))return;await api("/api/netze",{sparte:kz,ausfuehren:aus,nur_eins:eins},"log_e")}
async function schritt(art,aus){const kz=$("ein_sp").value;if(!kz)return alert("Erst den Plan speichern.");if(aus&&!confirm("Wirklich ausführen?\nSparte: "+kz))return;await api("/api/"+art,{sparte:kz,ausfuehren:aus},"log_e")}
async function ppsk(art){const kz=$("ein_sp").value;if(pwOffen()&&!confirm("Es gibt ungespeicherte Passwort-Änderungen. Verwerfen?"))return;
 if(art=="neu"&&!confirm("ALLE Passwörter dieser Sparte neu erzeugen? Bereits verteilte Zugangskarten werden nach dem Hochladen ungültig."))return;
 const d=await api("/api/ppsk",{sparte:kz,art:art},"log_e");PPSKSP=d.sparte;pwSetzen(d.zeilen)}
let PWALT={},PWGEAENDERT=[];
function regelBeispiel(){const p=$("pr_pre").value,z=+$("pr_z").value||10;$("pr_bsp").textContent="Beispiel: "+p+"0123456789".repeat(3).slice(0,z)}
async function regelLaden(){const d=await api("/api/pw-regel");$("pr_pre").value=d.regel.praefix;$("pr_z").value=d.regel.ziffern;regelBeispiel()}
async function regelSpeichern(){const d=await api("/api/pw-regel",{praefix:$("pr_pre").value.trim(),ziffern:+$("pr_z").value},"log_e");$("pr_pre").value=d.regel.praefix;$("pr_z").value=d.regel.ziffern;regelBeispiel()}
function pwSetzen(zeilen){PPSK={spalten:[["Parzelle","Parzelle"],["Netz","Netz"],["WLAN","WLAN"],["Passwort","Passwort","mono"],["VLAN","VLAN"]],zeilen:zeilen};PWALT={};zeilen.forEach(r=>PWALT[r.Parzelle]=r.Passwort||"");
 $("pw_bereich").style.display="block";$("tab_e").innerHTML="";
 $("tab_pw").innerHTML="<table><tr><th>Drucken</th><th>Parzelle</th><th>Netz</th><th>WLAN</th><th>Passwort</th><th></th><th>VLAN</th><th>Status</th></tr>"+zeilen.map(r=>`<tr data-p="${esc(r.Parzelle)}"><td><input type="checkbox" class="kwahl" value="${esc(r.Parzelle)}" style="width:auto" ${r.Passwort?"":"disabled"}></td><td>${esc(r.Parzelle)}</td><td>${esc(r.Netz)}</td><td>${esc(r.WLAN)}</td>
 <td><input class="pwfeld" data-p="${esc(r.Parzelle)}" value="${esc(r.Passwort||"")}" maxlength="63" spellcheck="false" autocomplete="off" oninput="pwPruefen()"></td>
 <td style="white-space:nowrap"><button class="mini" onclick="pwNeu('${esc(r.Parzelle)}')" title="Zufälliges neues Passwort">neu</button><button class="mini" onclick="pwFeld('${esc(r.Parzelle)}','')" title="Zugang entfernen">sperren</button><button class="mini" onclick="pwFeld('${esc(r.Parzelle)}',PWALT['${esc(r.Parzelle)}'])" title="Ursprünglicher Wert">↺</button></td>
 <td>${esc(r.VLAN)}</td><td class="pwst"></td></tr>`).join("")+"</table>";pwPruefen();pwFilter()}
function pwFehler(pw){if(pw==="")return"";if(pw.length<8||pw.length>63)return"8–63 Zeichen";if(/[^\x20-\x7e]/.test(pw))return"keine Umlaute/Sonderzeichen";if(pw!==pw.trim())return"Leerzeichen am Rand";return""}
function pwPruefen(){const felder=[...document.querySelectorAll(".pwfeld")];const zahl={};felder.forEach(f=>{if(f.value)zahl[f.value]=(zahl[f.value]||0)+1});let ge=0,fe=0;
 felder.forEach(f=>{const tr=f.closest("tr"),st=tr.querySelector(".pwst"),alt=PWALT[f.dataset.p];let fehler=pwFehler(f.value);if(!fehler&&f.value&&zahl[f.value]>1)fehler="doppelt";
  const geaendert=f.value!==alt;tr.classList.toggle("geaendert",geaendert&&!fehler);tr.classList.toggle("falsch",!!fehler);tr.classList.toggle("gesperrt",!f.value);
  st.className="pwst"+(fehler?" f":geaendert?" g":"");st.textContent=fehler?"✖ "+fehler:geaendert?(f.value?"geändert":"wird gesperrt"):(f.value?"":"ohne Zugang");if(geaendert)ge++;if(fehler)fe++;
  const cb=tr.querySelector(".kwahl");cb.disabled=!f.value||geaendert;if(cb.disabled)cb.checked=false});
 const e=$("pw_st");e.textContent=fe?`✖ ${fe} ungültig – bitte korrigieren`:ge?`● ${ge} Änderung(en) noch nicht gespeichert`:"Alle Passwörter gespeichert";e.className=ge||fe?"dirty":"";return{ge,fe}}
function pwOffen(){return document.querySelectorAll("tr.geaendert,tr.falsch").length>0}
function pwFeld(p,w){const f=document.querySelector(`.pwfeld[data-p="${CSS.escape(p)}"]`);if(f){f.value=w;pwPruefen()}}
async function pwNeu(p){const d=await api("/api/passwort?n=1");pwFeld(p,d.passwoerter[0])}
function pwFilter(){const t=$("pw_suche").value.trim().toLowerCase();document.querySelectorAll("#tab_pw tr[data-p]").forEach(tr=>{const f=tr.querySelector(".pwfeld");tr.style.display=!t||(tr.textContent+" "+f.value).toLowerCase().includes(t)?"":"none"})}
function pwVerwerfen(){if(!pwOffen()||confirm("Alle ungespeicherten Änderungen verwerfen?"))document.querySelectorAll(".pwfeld").forEach(f=>{f.value=PWALT[f.dataset.p]});pwPruefen()}
async function pwSpeichern(){const{ge,fe}=pwPruefen();if(fe)return alert("Bitte erst die rot markierten Passwörter korrigieren.");if(!ge)return alert("Keine Änderungen.");
 const aend={};document.querySelectorAll(".pwfeld").forEach(f=>{if(f.value!==PWALT[f.dataset.p])aend[f.dataset.p]=f.value});
 if(Object.values(aend).some(v=>v==="")&&!confirm("Bei mindestens einer Parzelle wird der Zugang entfernt (leeres Passwort). Fortfahren?"))return;
 const d=await api("/api/ppsk-speichern",{sparte:$("ein_sp").value,aenderungen:aend},"log_e");PWGEAENDERT=d.geaendert.map(String);pwSetzen(d.zeilen);markiereGeaendert()}
function markiereGeaendert(){if(!PWGEAENDERT.length)return alert("In dieser Sitzung wurde noch nichts geändert.");document.querySelectorAll(".kwahl").forEach(c=>c.checked=!c.disabled&&PWGEAENDERT.includes(c.value))}
addEventListener("beforeunload",e=>{if(typeof pwOffen=="function"&&pwOffen()){e.preventDefault();e.returnValue=""}});
function markiere(an){document.querySelectorAll(".kwahl").forEach(c=>c.checked=an)}
async function karten(art){const kz=$("ein_sp").value;if(!PPSK)return alert("Erst unter Schritt 3 „Anzeigen“ oder „Fehlende erzeugen“.");
 let auswahl="alle";if(art=="auswahl"){auswahl=[...document.querySelectorAll(".kwahl:checked")].map(c=>c.value);if(!auswahl.length)return alert("Bitte in der Tabelle Parzellen markieren.")}
 const w=window.open("","_blank");let d;try{d=await api("/api/karten",{sparte:kz,auswahl:auswahl},"log_e")}catch(e){if(w)w.close();return}
 if(w){w.document.open();w.document.write(d.html);w.document.close()}else alert("Bitte Pop-ups für diese Seite erlauben.")}
let VV=null,VL=null,VDRUCK=null;
const vvDarf=()=>ICH.admin||ICH.bereiche.voucher=="schreiben";
const dauerText=m=>m%1440==0?(m/1440)+(m==1440?" Tag":" Tage"):m%60==0?(m/60)+(m==60?" Stunde":" Stunden"):m+" Minuten";
const vEinst=v=>dauerText(v.minuten)+" · "+v.geraete+" Gerät"+(v.geraete!=1?"e":"")+" · "+(v.daten_mb?v.daten_mb+" MB":"Daten unbegrenzt")+(v.down_kbps||v.up_kbps?" · "+(v.down_kbps/1000||"∞")+"/"+(v.up_kbps/1000||"∞")+" Mbit/s":"");
async function vvLaden(){if(!PLAN)await planLaden(true);vWlanAuswahl();const d=await api("/api/voucher-vorlagen",undefined,"log_vv");VV=d.vorlagen;vvZeigen();vVorlagenAuswahl()}
function vVorlagenAuswahl(){const s=$("v_vorlage"),alt=s.value;s.innerHTML=VV.map(v=>`<option value="${esc(v.id)}">${esc(v.name)} – ${esc(dauerText(v.minuten))}</option>`).join("");if(VV.some(v=>v.id==alt))s.value=alt;vVorlageInfo()}
function vVorlageInfo(){const v=(VV||[]).find(x=>x.id==$("v_vorlage").value);$("v_info").textContent=v?vEinst(v)+(v.text?" · Druck: „"+v.text+"“":""):""}
function vvEinheit(m){return m%1440==0?[m/1440,1440]:m%60==0?[m/60,60]:[m,1]}
function vvZeigen(){const w=vvDarf();document.querySelectorAll(".vv-schreib").forEach(e=>e.hidden=!w);
 $("vv_tab").innerHTML="<table><tr><th>Name</th><th>Gültigkeit</th><th>Geräte</th><th>Daten (MB)</th><th>Download Mbit/s</th><th>Upload Mbit/s</th><th>Text auf dem Ausdruck</th><th></th></tr>"+VV.map((v,i)=>{const [z,e]=vvEinheit(v.minuten);const dis=w?"":" disabled";
  return`<tr><td><input class="vv_in" data-i="${i}" data-f="name" value="${esc(v.name)}" maxlength="40"${dis}></td><td style="white-space:nowrap"><input class="vv_in" data-i="${i}" data-f="zahl" type="number" min="1" value="${z}" style="width:80px"${dis}> <select class="vv_in" data-i="${i}" data-f="einheit" style="width:auto"${dis}><option value="1"${e==1?" selected":""}>Minuten</option><option value="60"${e==60?" selected":""}>Stunden</option><option value="1440"${e==1440?" selected":""}>Tage</option></select></td>
  <td><input class="vv_in" data-i="${i}" data-f="geraete" type="number" min="1" value="${v.geraete}" style="width:70px"${dis}></td><td><input class="vv_in" data-i="${i}" data-f="daten_mb" type="number" min="0" value="${v.daten_mb}" style="width:100px"${dis}></td>
  <td><input class="vv_in" data-i="${i}" data-f="down" type="number" min="0" step="0.5" value="${v.down_kbps/1000}" style="width:90px"${dis}></td><td><input class="vv_in" data-i="${i}" data-f="up" type="number" min="0" step="0.5" value="${v.up_kbps/1000}" style="width:90px"${dis}></td>
  <td><input class="vv_in" data-i="${i}" data-f="text" value="${esc(v.text||"")}" maxlength="120"${dis}></td><td>${w?`<button class="k" onclick="vvWeg(${i})">Entfernen</button>`:""}</td></tr>`}).join("")+"</table>";
 document.querySelectorAll(".vv_in").forEach(el=>el.onchange=()=>{const v=VV[+el.dataset.i],f=el.dataset.f,row=[...document.querySelectorAll(`.vv_in[data-i="${el.dataset.i}"]`)],g=k=>row.find(x=>x.dataset.f==k).value;
  if(f=="zahl"||f=="einheit")v.minuten=Math.round(+g("zahl")*+g("einheit"));else if(f=="down")v.down_kbps=Math.round(+el.value*1000);else if(f=="up")v.up_kbps=Math.round(+el.value*1000);else if(f=="name"||f=="text")v[f]=el.value;else v[f]=+el.value})}
function vvNeu(v){VV.push(v||{id:"",name:"Neue Vorlage",minuten:1440,geraete:1,daten_mb:0,down_kbps:0,up_kbps:0,text:""});vvZeigen();$("log_vv").textContent="Neue Vorlage hinzugefügt – Werte eintragen und „Vorlagen speichern“."}
function vvWeg(i){VV.splice(i,1);vvZeigen()}
async function vvSpeichern(){const d=await api("/api/voucher-vorlagen",{vorlagen:VV},"log_vv");VV=d.vorlagen;vvZeigen();vVorlagenAuswahl()}
async function voucher(aus){const b={vorlage:$("v_vorlage").value,anzahl:+$("v_anz").value,name:$("v_name").value.trim(),ausfuehren:aus};
 if(aus&&!confirm(b.anzahl+" Voucher nach Vorlage „"+$("v_vorlage").selectedOptions[0].textContent+"“ am Gateway erstellen?"))return;
 const d=await api("/api/voucher",b,"log_vo");if(d.codes){VDRUCK={codes:d.codes.map(c=>({code:c,dauer:d.dauer,text:d.text,geraete:d.geraete}))};tabelle("tab_vo",[["code","Voucher-Code","mono"]],d.codes.map(c=>({code:vCode(c)})));if(VL)vlLaden().catch(()=>{})}}
const vZeit=t=>{if(!t)return"";const x=new Date(t);return isNaN(x)?String(t):x.toLocaleString("de-DE",{day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit"})};
const vCode=c=>String(c).length==10?String(c).slice(0,5)+"-"+String(c).slice(5):String(c);
function vDruckFenster(liste){const w=window.open("","_blank");
 w.document.write(`<html><head><title>Voucher</title><style>body{font-family:Arial;margin:10mm}.k{display:inline-block;width:60mm;border:1px dashed #999;margin:2mm;padding:4mm;text-align:center;page-break-inside:avoid;vertical-align:top}.c{font-family:Consolas,monospace;font-size:20px;font-weight:bold;letter-spacing:2px;margin:2mm 0}.t{font-size:11px;color:#444;margin-top:1mm}</style></head><body>`+
 liste.map(v=>`<div class="k"><div style="color:#3a9a1f;font-weight:bold">SparteNet.de · Gast-WLAN</div><div class="c">${esc(vCode(v.code))}</div><div style="font-size:12px">gültig ${esc(v.dauer)} ab Anmeldung${v.geraete>1?" · bis "+v.geraete+" Geräte":""}</div>${v.text?`<div class="t">${esc(v.text)}</div>`:""}</div>`).join("")+"<script>print()<\/script></body></html>");w.document.close()}
function voucherEtiketten(){if(!VDRUCK||!VDRUCK.codes.length)return alert("Erst Voucher erstellen – oder unten „Auslesen“ und vorhandene auswählen.");vDruckFenster(VDRUCK.codes)}
function vWlanAuswahl(){const s=$("v_wlan");if(!s||!PLAN||s.options.length)return;s.innerHTML=PLAN.sparten.map(x=>`<option value="${esc(x.kz)}">${esc(PLAN.praefix+"-"+x.kz+"-Gäste")} (${esc(x.name)})</option>`).join("")}
async function vKartenDruck(b,log){vWlanAuswahl();const w=window.open("","_blank");let d;try{d=await api("/api/voucher-druck",{...b,sparte:$("v_wlan").value,ab_jetzt:$("v_jetzt").checked},log)}catch(e){if(w)w.close();return}
 if(w){w.document.open();w.document.write(d.html);w.document.close()}else alert("Bitte Pop-ups für diese Seite erlauben.")}
function voucherDruck(){if(!VDRUCK||!VDRUCK.codes.length)return alert("Erst Voucher erstellen – oder unten „Auslesen“ und vorhandene auswählen.");vKartenDruck({codes:VDRUCK.codes.map(v=>v.code)},"log_vo")}
async function vlLaden(){const d=await api("/api/voucher-liste",undefined,"log_vl");VL=d;vlZeigen()}
function vlZeigen(){const d=VL;if(!d)return;const f=$("vl_f").value,L=d.zeilen.filter(z=>!f||z.status==f),farbe={"abgelaufen":"var(--muted)","in Benutzung":"var(--green)","voll belegt":"var(--amber)"};
 const n={};d.zeilen.forEach(z=>n[z.status]=(n[z.status]||0)+1);$("vl_st").textContent=d.zeilen.length+" Voucher"+(n.unbenutzt?" · "+n.unbenutzt+" unbenutzt":"");
 $("vl_tab").innerHTML=L.length?'<table><tr><th><input type="checkbox" id="vl_alle" style="width:auto" onchange="document.querySelectorAll(\'.vl_w\').forEach(e=>e.checked=this.checked)"></th><th>Code</th><th>Bezeichnung</th><th>Vorlage</th><th>Gültigkeit</th><th>Geräte</th><th>Daten / Bandbreite</th><th>Status</th><th>erstellt</th><th>läuft ab</th><th></th></tr>'+L.map(z=>`<tr><td><input type="checkbox" class="vl_w" value="${esc(z.id)}" style="width:auto"></td><td class="mono"><b>${esc(vCode(z.code))}</b></td><td>${esc(z.name)}</td><td>${esc(z.vorlage||"–")}</td><td>${esc(z.dauer)}</td><td>${z.genutzt} / ${z.geraete}</td>
  <td>${z.daten_mb?z.daten_mb+" MB":"unbegrenzt"}${z.down_kbps||z.up_kbps?" · "+(z.down_kbps/1000||"∞")+"/"+(z.up_kbps/1000||"∞")+" Mbit/s":""}</td><td style="color:${farbe[z.status]||"inherit"};font-weight:600">${esc(z.status)}</td><td>${esc(vZeit(z.erstellt))}</td><td>${esc(vZeit(z.ablauf)||(z.status=="unbenutzt"?"ab Anmeldung":"–"))}</td><td><button class="k" data-id="${esc(z.id)}" onclick="vKartenDruck({ids:[this.dataset.id]},'log_vl')">Drucken</button></td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Keine Voucher'+(f?" mit Status „"+esc(f)+"“":"")+".</p>";
 $("vl_vs").innerHTML=d.vorschlaege.length&&vvDarf()?"<h3 style='margin-top:14px'>Vorschläge aus den Vouchern am Gateway</h3><p class='hint'>Diese Einstellungen kommen am Gateway vor, haben aber noch keine Vorlage.</p><div class='tab'><table><tr><th>Name</th><th>Einstellungen</th><th>Voucher</th><th></th></tr>"+d.vorschlaege.map((v,i)=>`<tr><td>${esc(v.name)}</td><td>${esc(vEinst(v))}</td><td>${v.anzahl}</td><td><button class="k" onclick="vlAlsVorlage(${i})">Als Vorlage übernehmen</button></td></tr>`).join("")+"</table></div>":""}
function vlGewaehlt(){return[...document.querySelectorAll(".vl_w:checked")].map(e=>e.value)}
function vlAuswahl(st){document.querySelectorAll(".vl_w").forEach(e=>{const z=VL.zeilen.find(x=>x.id==e.value);e.checked=z&&z.status==st})}
function vlDrucken(){const ids=vlGewaehlt();if(!ids.length)return $("log_vl").textContent="Nichts ausgewählt.";vKartenDruck({ids},"log_vl")}
async function vlLoeschen(){const ids=vlGewaehlt();if(!ids.length)return $("log_vl").textContent="Nichts ausgewählt.";const v=await api("/api/voucher-loeschen",{ids,ausfuehren:false},"log_vl");
 if(!confirm(v.log.join("\n")+"\n\nJetzt am Gateway löschen?"))return;await api("/api/voucher-loeschen",{ids,ausfuehren:true},"log_vl");vlLaden().catch(()=>{})}
function vlAlsVorlage(i){const v=VL.vorschlaege[i];vvNeu({id:"",name:v.name,minuten:v.minuten,geraete:v.geraete,daten_mb:v.daten_mb,down_kbps:v.down_kbps,up_kbps:v.up_kbps,text:""});$("vv_tab").scrollIntoView({behavior:"smooth",block:"center"})}
let DESIGN=null,DSTD=null,KDT=null,KDLOG="";
function kdHinweis(t){$("log_kd").textContent=KDLOG+(t?"\n"+t:"")}
const KD=[
 ["Papier & Layout",[["format","Papierformat","sel",[["A4","A4 (210 × 297 mm)"],["A5","A5 (148 × 210 mm)"],["A6","A6 (105 × 148 mm)"]]],["quer","Querformat","chk"],
  ["rand_mm","Seitenrand","rng",3,30,1,"mm"],["ausrichtung","Text ausrichten","sel",[["center","Mittig"],["left","Links"],["right","Rechts"]]],["fuss_unten","Fußzeile ganz unten","chk"]]],
 ["Texte",[["_hint","Platzhalter: {sparte} {kz} {parzelle} {wlan} · Enter = neue Zeile"],
  ["zeige_kopf","Kopfzeile","chk"],["t_kopf","","txt"],["t_titel","Überschrift","txt"],["zeige_unter","Untertitel","chk"],["t_unter","","txt"],
  ["zeige_scan","Hinweis unter dem QR-Code","chk"],["t_scan","","txt"],["zeige_zugang","WLAN-Name und Passwort anzeigen","chk"],["zeige_fuss","Fußzeile","chk"],["t_fuss","","txt"]]],
 ["Schrift",[["schrift","Schriftart","sel",[]],["gr_kopf","Kopfzeile","rng",6,40,1,"pt"],["gr_titel","Überschrift","rng",8,80,1,"pt"],["gr_text","Fließtext","rng",6,30,1,"pt"],
  ["gr_pw","Passwort","rng",8,40,1,"pt"],["gr_klein","Kleingedrucktes","rng",5,20,1,"pt"]]],
 ["Farben",[["farbe_akzent","Kopfzeile (Akzent)","col"],["farbe_text","Text","col"],["farbe_hell","Nebentext","col"],["farbe_seite","Seitenhintergrund","col"],["farbe_pw_hinter","Hintergrund Passwort","col"]]],
 ["QR-Code",[["qr_cm","Größe","rng",2,25,.5,"cm"],["farbe_qr","Farbe der Punkte","col"],["farbe_qr_hinter","Hintergrund","col"],["_hint","Dunkle Punkte auf hellem Grund, mindestens 3 cm – sonst lesen manche Handys den Code nicht. Passt nicht alles auf die Seite, werden QR-Code und Logo automatisch verkleinert. Für A6 empfiehlt sich Querformat."]]],
 ["Logo",[["_logo",""],["logo_ort","Platz","sel",[["oben","Oben"],["unten","Unten (über der Fußzeile)"]]],["logo_pos","Ausrichtung","sel",[["center","Mittig"],["left","Links"],["right","Rechts"]]],["logo_mm","Breite","rng",5,180,1,"mm"]]],
 ["Rahmen",[["rahmen","Rahmen anzeigen","chk"],["rahmen_mm","Stärke","rng",.2,5,.1,"mm"],["rahmen_radius","Ecken-Rundung","rng",0,20,1,"mm"],["farbe_rahmen","Rahmenfarbe","col"]]]];
function kdFeld([k,l,t,a,b,c,e]){const id="kd_"+k;
 if(k=="_hint")return `<p class="hint" style="margin:6px 0 2px">${esc(l)}</p>`;
 if(k=="_logo")return `<div class="feld"><label>Logo (PNG, JPG, SVG, WEBP · max. 2 MB, transparentes PNG empfohlen)</label></div><img id="kd_logo_mini" class="logo-mini" alt="" style="display:none">
  <div class="knoepfe" style="margin-top:8px"><label class="k" style="margin:0;color:var(--navy);cursor:pointer">Logo hochladen …<input type="file" id="kd_logo" accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml,.svg" onchange="logoHoch()" style="display:none"></label><button class="k" onclick="logoWeg()">Logo entfernen</button></div>`;
 if(t=="chk")return `<div class="feld chk"><input type="checkbox" id="${id}" data-k="${k}"><label for="${id}">${esc(l)}</label></div>`;
 if(t=="txt")return `<div class="feld">${l?`<label for="${id}">${esc(l)}</label>`:""}<textarea id="${id}" data-k="${k}" rows="1"></textarea></div>`;
 if(t=="col")return `<div class="feld"><label for="${id}">${esc(l)}</label><input type="color" id="${id}" data-k="${k}"></div>`;
 if(t=="rng")return `<div class="feld"><label for="${id}">${esc(l)}</label><output id="${id}_o"></output><input type="range" id="${id}" data-k="${k}" data-e="${e}" min="${a}" max="${b}" step="${c}"></div>`;
 if(t=="sel")return `<div class="feld"><label for="${id}">${esc(l)}</label><select id="${id}" data-k="${k}">${(k=="schrift"?KDSCHRIFT.map(x=>[x,x]):a).map(([v,n])=>`<option value="${esc(v)}">${esc(n)}</option>`).join("")}</select></div>`}
let KDSCHRIFT=[];
function kdAufbauen(){$("kd_form").innerHTML=KD.map(([h,f])=>`<div class="karte"><h3>${esc(h)}</h3>${f.map(kdFeld).join("")}</div>`).join("");
 $("kd_form").querySelectorAll("[data-k]").forEach(el=>{el.addEventListener("input",()=>{kdAusgabe(el);kdGeaendert()});el.addEventListener("change",()=>{kdAusgabe(el);kdGeaendert()})})}
function kdAusgabe(el){if(el.type=="range")$(el.id+"_o").textContent=String(+el.value).replace(".",",")+" "+el.dataset.e;
 if(el.tagName=="TEXTAREA"){el.style.height="auto";el.style.height=el.scrollHeight+2+"px"}}
function kdFuellen(g){$("kd_form").querySelectorAll("[data-k]").forEach(el=>{const v=g[el.dataset.k];if(el.type=="checkbox")el.checked=!!v;else el.value=v;kdAusgabe(el)})}
function kdLesen(){const g={};$("kd_form").querySelectorAll("[data-k]").forEach(el=>{g[el.dataset.k]=el.type=="checkbox"?el.checked:(el.type=="range"?+el.value:el.value)});return g}
function kdStatus(t,dirty){const e=$("kd_status");e.textContent=t;e.className=dirty?"dirty":""}
function kdGeaendert(){kdStatus("● Änderungen noch nicht gespeichert",true);clearTimeout(KDT);KDT=setTimeout(vorschau,250)}
function logoMini(uri){const i=$("kd_logo_mini");if(uri){i.src=uri;i.style.display="block"}else{i.removeAttribute("src");i.style.display="none"}}
async function designLaden(){const d=await api("/api/design");DESIGN=d.design;DSTD=d.standard;KDSCHRIFT=d.schriften;kdAufbauen();kdFuellen(DESIGN);logoMini(d.logo_uri);kdStatus("Gespeichertes Design",false);vorschau()}
async function vorschau(drucken){try{const r=await fetch("/api/karten-vorschau",{method:"POST",headers:{"X-Token":T,"Content-Type":"application/json"},body:JSON.stringify({design:kdLesen(),drucken:!!drucken})});
 const d=await r.json();if(!r.ok)throw new Error(d.fehler||r.status);KDLOG=(d.log||[]).join("\n");$("log_kd").textContent=KDLOG;return d}
 catch(e){$("log_kd").innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>'}}
const _vorschau=vorschau;vorschau=async function(drucken){const d=await _vorschau(drucken);if(d&&!drucken)$("kd_vor").srcdoc=d.html;return d};
async function designSpeichern(){await api("/api/design",{design:kdLesen()},"log_kd");DESIGN=kdLesen();kdStatus("✔ Gespeichert – gilt für alle Zugangskarten",false)}
function designStandard(){if(!confirm("Alle Einstellungen auf Standard zurücksetzen? (Das Logo bleibt; gespeichert wird erst mit „Speichern“.)"))return;kdFuellen(DSTD);kdGeaendert()}
async function testdruck(){const w=window.open("","_blank");const d=await vorschau(true);if(!d){if(w)w.close();return}if(w){w.document.open();w.document.write(d.html);w.document.close()}else alert("Bitte Pop-ups für diese Seite erlauben.")}
async function logoHoch(){const f=$("kd_logo").files[0];if(!f)return;const d=await api("/api/logo",f,"log_kd");logoMini(d.logo_uri);$("kd_logo").value="";vorschau()}
async function logoWeg(){if(!confirm("Logo entfernen?"))return;await api("/api/logo-loeschen",{},"log_kd");logoMini("");vorschau()}
let SYS=null,SYST=null,DLISTE=null,DAKT=null,DDATEN=null,DANS="tab";
const mbit=b=>b==null||b===""?"–":(b>=1e6?(b/1e6).toFixed(b>=1e8?0:1)+" Mbit/s":(b/1e3).toFixed(0)+" kbit/s");
const kbit=k=>k==null?"–":(k>=1e6?(k/1e6).toLocaleString("de-DE",{maximumFractionDigits:1})+" Gbit/s":k>=1000?(k/1000).toLocaleString("de-DE",{maximumFractionDigits:k>=100000?0:1})+" Mbit/s":Math.round(k)+" kbit/s");
const bytes=b=>!b?"0 B":b>=1e9?(b/1e9).toFixed(2)+" GB":b>=1e6?(b/1e6).toFixed(1)+" MB":(b/1e3).toFixed(0)+" kB";
const dauer=s=>{if(s==null||s==="")return"–";s=+s;const t=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);return t?t+" T "+h+" h":h?h+" h "+m+" min":m+" min"};
const zahl=(v,n=1)=>v==null||v===""?"–":(+v).toFixed(n).replace(".",",");
function balken(p){if(p==null||p==="")return"–";const k=p>=85?"s":p>=60?"w":"";return `<div class="balken"><i class="${k}" style="width:${Math.min(100,p)}%"></i><span>${zahl(p,0)} %</span></div>`}
function htab(id,sp,z){$(id).innerHTML=z.length?"<table><tr>"+sp.map(s=>"<th>"+esc(s[0])+"</th>").join("")+"</tr>"+z.map(r=>"<tr>"+sp.map(s=>"<td>"+s[1](r)+"</td>").join("")+"</tr>").join("")+"</table>":"<p class='hint' style='padding:10px'>Keine Daten.</p>"}
function kach(t,v,u,a){return `<div class="kachel ${a||""}"><b>${v}</b>${esc(t)}${u?`<small>${esc(u)}</small>`:""}</div>`}
function diagramm(id,punkte,serien,einheit,fmt){const el=$(id);const pz=punkte.filter(p=>serien.some(s=>p[s.k]!=null));if(!pz.length){el.innerHTML="";return}
 const W=900,H=200,L=84,R=10,T=10,B=26,max=Math.max(1,...pz.flatMap(p=>serien.map(s=>+p[s.k]||0)))*1.1;const t0=new Date(pz[0].t).getTime(),t1=new Date(pz[pz.length-1].t).getTime()||t0+1;
 const X=t=>L+(W-L-R)*((new Date(t).getTime()-t0)/Math.max(1,t1-t0)),Y=v=>T+(H-T-B)*(1-(+v||0)/max);let g="";
 for(let i=0;i<=4;i++){const v=max*i/4,y=Y(v);g+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" stroke="#e3e8e0"/><text x="${L-6}" y="${y+4}" text-anchor="end" font-size="11" fill="#5d6b75">${esc(fmt(v))}</text>`}
 for(let h=0;h<=6;h++){const t=t0+(t1-t0)*h/6,x=L+(W-L-R)*h/6;g+=`<text x="${x}" y="${H-8}" text-anchor="middle" font-size="11" fill="#5d6b75">${new Date(t).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})}</text>`}
 serien.forEach(s=>{const pts=pz.filter(p=>p[s.k]!=null).map(p=>X(p.t).toFixed(1)+","+Y(p[s.k]).toFixed(1));if(!pts.length)return;
  g+=`<polygon points="${pts[0].split(",")[0]},${Y(0)} ${pts.join(" ")} ${pts[pts.length-1].split(",")[0]},${Y(0)}" fill="${s.f}" opacity=".12"/><polyline points="${pts.join(" ")}" fill="none" stroke="${s.f}" stroke-width="1.8"/>`});
 el.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(einheit)}">${g}<line id="${id}_l" y1="${T}" y2="${H-B}" stroke="#1d2f3e" stroke-dasharray="3 3" style="display:none"/><rect x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="transparent"/></svg><div class="tip"></div>
 <div class="legende">${serien.map(s=>`<span><b style="background:${s.f}"></b>${esc(s.n)}</span>`).join("")}</div>`;
 const svg=el.querySelector("svg"),tip=el.querySelector(".tip"),ln=$(id+"_l");
 svg.onmousemove=e=>{const r=svg.getBoundingClientRect(),x=(e.clientX-r.left)*W/r.width;let b=pz[0],bd=1e9;pz.forEach(p=>{const d=Math.abs(X(p.t)-x);if(d<bd){bd=d;b=p}});
  ln.setAttribute("x1",X(b.t));ln.setAttribute("x2",X(b.t));ln.style.display="";tip.style.display="block";
  tip.innerHTML=new Date(b.t).toLocaleString("de-DE",{hour:"2-digit",minute:"2-digit",day:"2-digit",month:"2-digit"})+"<br>"+serien.map(s=>esc(s.n)+": <b>"+esc(fmt(b[s.k]))+"</b>").join("<br>");
  const px=X(b.t)*r.width/W;tip.style.left=Math.min(r.width-170,px+12)+"px";tip.style.top="10px"};svg.onmouseleave=()=>{tip.style.display="none";ln.style.display="none"}}
async function sysLaden(){let d;try{d=await api("/api/system",undefined,"log_sys")}catch(e){return}SYS=d;
 const gw=d.geraete.find(g=>g.gw)||d.geraete[0]||{},isp=d.isp.length?d.isp[d.isp.length-1]:{},z=d.site.zaehler||{},pr=d.site.prozent||{};
 const down=d.wan.rx_bps??gw.rx_bps,up=d.wan.tx_bps??gw.tx_bps,lat=isp.lat??d.wan.latenz,on=d.geraete.filter(g=>String(g.status).toUpperCase()=="ONLINE").length;
 const ca=d.clients_arten,wlan=ca.WIRELESS||0,lan=ca.WIRED||0;
 $("sys_k").innerHTML=kach("Download jetzt",mbit(down),d.wan.rx_bps!=null?"Internet-Anschluss":"Gateway-Uplink","gut")+kach("Upload jetzt",mbit(up),d.wan.tx_bps!=null?"Internet-Anschluss":"Gateway-Uplink","gut")+
  kach("Latenz",lat!=null?zahl(lat,0)+" ms":"–",isp.maxlat!=null?"max. "+zahl(isp.maxlat,0)+" ms":"",lat>80?"warn":"")+
  kach("Paketverlust",isp.verlust!=null?zahl(isp.verlust,1)+" %":"–","letzte 5 min",isp.verlust>1?"schlecht":"")+
  kach("Internet verfügbar",pr.wanUptime!=null?zahl(pr.wanUptime,1)+" %":(isp.uptime!=null?zahl(isp.uptime,0)+" %":"–"),d.site.isp||d.wan.isp||isp.isp||"",pr.wanUptime<99?"warn":"")+
  kach("Clients",d.clients_gesamt,`WLAN ${wlan} · Kabel ${lan}`+(z.guestClient!=null?` · Gäste ${z.guestClient}`:""))+
  kach("Geräte online",on+" / "+d.geraete.length,d.geraete.length-on?(d.geraete.length-on)+" offline":"alle erreichbar",on<d.geraete.length?"schlecht":"gut")+
  kach("Gateway CPU / RAM",(gw.cpu!=null?zahl(gw.cpu,0):"–")+" / "+(gw.ram!=null?zahl(gw.ram,0):"–")+" %",gw.name||"",(gw.cpu>85||gw.ram>90)?"warn":"");
 $("sys_ch_hint").textContent=(d.isp.length?"Messwerte der UniFi-Cloud im 5-Minuten-Raster ("+d.isp.length+" Werte).":"Keine Verlaufsdaten von der UniFi-Cloud erhalten.")+(d.isp_hinweise.length?" "+d.isp_hinweise.join(" "):"");
 $("sys_isp_roh").textContent=JSON.stringify(d.isp_roh||{},null,2);
 const vl=d.verlauf.length?d.verlauf:d.isp;if(d.verlauf.length)$("sys_ch_hint").textContent+=" Download/Upload: Datenverkehr am Internet-Anschluss laut Gateway (5-Minuten-Mittel, "+d.verlauf.length+" Werte).";
 else if(!d.isp.some(p=>p.down!=null||p.up!=null))$("sys_ch_hint").textContent+=" Download/Upload-Verlauf: vom Gateway nicht erhalten"+(d.verlauf_fehler?" ("+d.verlauf_fehler+")":"")+" – es wird nur die Latenz gezeigt.";
 diagramm("sys_ch1",vl,[{k:"down",n:"Download",f:"#3a9a1f"},{k:"up",n:"Upload",f:"#1f6fb2"}],"Durchsatz",kbit);
 diagramm("sys_ch2",d.isp,[{k:"lat",n:"Latenz Ø",f:"#9a6700"},{k:"maxlat",n:"Latenz max.",f:"#b42318"}],"Latenz",v=>v==null?"–":Math.round(v)+" ms");
 htab("sys_ger",[["Gerät",r=>`<span class="punkt ${String(r.status).toUpperCase()=="ONLINE"?"on":"off"}"></span>${esc(r.name)}${r.gw?" <span class='status ok'>Gateway</span>":""}`],["Modell",r=>esc(r.modell)],["IP",r=>esc(r.ip)],
  ["CPU",r=>balken(r.cpu)],["RAM",r=>balken(r.ram)],["Last",r=>zahl(r.load,2)],["Laufzeit",r=>dauer(r.uptime)],["↓ Uplink",r=>mbit(r.rx_bps)],["↑ Uplink",r=>mbit(r.tx_bps)],
  ["Ports",r=>r.ports?r.ports_auf+" / "+r.ports+(r.poe?` · PoE ${r.poe}`:""):"–"],["Funk",r=>(r.funk||"–").split(" · ").map(esc).join("<br>")],["Wiederholungen",r=>(r.retries||"–").split(" · ").map(esc).join("<br>")],["Clients",r=>r.clients??"–"],["Temp.",r=>r.temp!=null?zahl(r.temp,0)+" °C":"–"],
  ["Firmware",r=>esc(r.firmware||"")+(r.update?" <span class='status' style='background:#fff1c2;color:#7a5200'>Update</span>":"")]],d.geraete);
 const mitTraffic=d.top.length>0;$("sys_netz_hint").textContent=mitTraffic?"Datenverkehr seit Verbindungsbeginn der aktuell verbundenen Geräte.":"Anzahl verbundener Geräte je Netz. Datenverkehr je Parzelle liefert die Konsole über die Cloud nicht.";
 htab("sys_netz",[["Netz",r=>esc(r.netz)],["Clients",r=>r.clients]].concat(mitTraffic?[["↓ empfangen",r=>bytes(r.tx)],["↑ gesendet",r=>bytes(r.rx)],["gesamt",r=>bytes(r.rx+r.tx)]]:[]),d.je_netz);
 $("sys_top_k").style.display=mitTraffic?"":"none";
 if(mitTraffic)htab("sys_top",[["Gerät",r=>esc(r.name)],["IP",r=>esc(r.ip)],["Netz",r=>esc(r.netz)],["WLAN",r=>esc(r.wlan)],["Signal",r=>r.signal!=null?r.signal+" dBm":"–"],["↓ empfangen",r=>bytes(r.tx)],["↑ gesendet",r=>bytes(r.rx)],["verbunden",r=>dauer(r.seit)]],d.top)}
function sysAuto(){clearInterval(SYST);if($("sys_auto").checked)SYST=setInterval(()=>{if($("system").classList.contains("aktiv"))sysLaden()},60000)}
async function datenListe(){const d=await api("/api/daten-liste");DLISTE=d.quellen;let g="",h="";
 DLISTE.forEach(q=>{if(q.gruppe!=g){g=q.gruppe;h+=`<h4>${esc(g)}</h4>`}h+=`<button id="dq_${q.schluessel}" onclick="datenLaden('${q.schluessel}')"><span>${esc(q.titel)}</span><em></em></button>`});$("d_liste").innerHTML=h}
async function datenPruefen(){const d=await api("/api/daten-pruefen",undefined,"log_d");Object.entries(d.quellen).forEach(([k,v])=>{const e=document.querySelector("#dq_"+k+" em");if(!e)return;
 e.textContent=v.ok?v.anzahl:"–";e.className=v.ok?"ok":"nein";e.title=v.fehler||""})}
async function datenLaden(k){DAKT=k;document.querySelectorAll(".dliste button").forEach(b=>b.classList.toggle("aktiv",b.id=="dq_"+k));
 let d;try{d=await api("/api/daten?q="+k+"&geheim="+($("d_geheim").checked?1:0),undefined,"log_d")}catch(e){$("d_tab").innerHTML="";$("d_json").textContent="";return}
 DDATEN=d;$("d_titel").textContent=d.titel+" ("+d.anzahl+")";$("d_pfad").textContent=d.gruppe+" · "+d.pfad;datenZeigen()}
function flach(o,pre,aus,tiefe){if(o===null||typeof o!="object"){aus[pre||"Wert"]=o;return aus}
 if(Array.isArray(o)){aus[pre]=o.every(x=>x===null||typeof x!="object")?o.join(", "):(o.length?JSON.stringify(o):"");return aus}
 Object.entries(o).forEach(([k,v])=>{const n=pre?pre+"."+k:k;if(v&&typeof v=="object"&&!Array.isArray(v)&&tiefe<2)flach(v,n,aus,tiefe+1);else flach(v,n,aus,9)});return aus}
function datenZeilen(){if(!DDATEN)return{sp:[],z:[]};const r=DDATEN.roh;let z;
 if(Array.isArray(r))z=r.map(x=>flach(x,"",{},0));else{const f=flach(r,"",{},0);z=Object.entries(f).map(([k,v])=>({Feld:k,Wert:v}))}
 const t=$("d_filter").value.trim().toLowerCase();if(t)z=z.filter(x=>Object.values(x).join(" ").toLowerCase().includes(t));
 const sp=[];z.forEach(x=>Object.keys(x).forEach(k=>{if(!sp.includes(k))sp.push(k)}));return{sp:sp,z:z}}
function datenZeigen(){if(!DDATEN)return;const json=DANS=="json";$("d_json").style.display=json?"block":"none";$("d_tab").style.display=json?"none":"block";
 if(json){$("d_json").textContent=JSON.stringify(DDATEN.roh,null,2);return}
 const{sp,z}=datenZeilen(),zeig=sp.slice(0,45);
 $("d_tab").innerHTML=z.length?"<table><tr>"+zeig.map(k=>"<th>"+esc(k)+"</th>").join("")+"</tr>"+z.slice(0,1000).map(x=>"<tr>"+zeig.map(k=>{const v=x[k]==null?"":String(x[k]);return `<td class="zelle" title="${esc(v.slice(0,600))}">${esc(v.slice(0,160))}</td>`}).join("")+"</tr>").join("")+"</table>"
  +(sp.length>45?`<p class="hint" style="padding:8px">${sp.length-45} weitere Spalten – vollständig unter „JSON“ oder „Als CSV“.</p>`:""):"<p class='hint' style='padding:10px'>Keine Einträge.</p>"}
function datenJson(){if(!DDATEN)return alert("Erst eine Quelle wählen.");const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify(DDATEN.roh,null,2)],{type:"application/json"}));a.download="spartenet_"+DAKT+".json";a.click()}
function datenCsv(){if(!DDATEN)return alert("Erst eine Quelle wählen.");const{sp,z}=datenZeilen();csvSpeichern({spalten:sp,zeilen:z},"spartenet_"+DAKT)}
async function diagnose(){const d=await api("/api/diagnose",{anonym:$("diag_anon").checked},"log_diag");const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([d.inhalt],{type:"application/json"}));a.download=d.name;a.click()}
const ANS_STD={breite:1200,zoom:0,tabh:520,spalten:false,kd:430,dl:270};let ANS={...ANS_STD},ANST=null;
function autoZoom(){const dpr=window.devicePixelRatio||1,phys=screen.width*dpr;const basis=phys>=7600?2.5:phys>=5000?2:phys>=3800?1.5:phys>=2500?1.25:1;return Math.max(1,Math.round(basis/dpr*4)/4)}
function vhSetzen(){const p=document.createElement("div");p.style.cssText="position:absolute;visibility:hidden;height:100px;width:1px";document.body.appendChild(p);
 const f=p.getBoundingClientRect().height/100||1;p.remove();document.documentElement.style.setProperty("--vh",(innerHeight/f)+"px")}
addEventListener("resize",vhSetzen);
function ansAnwenden(){const r=document.documentElement.style,z=ANS.zoom||autoZoom();document.body.style.zoom=z;vhSetzen();
 r.setProperty("--main-b",ANS.breite?ANS.breite+"px":"100%");r.setProperty("--tab-h",ANS.tabh?ANS.tabh+"px":"calc(var(--vh,100vh) - 240px)");
 r.setProperty("--kd-links",ANS.kd+"px");r.setProperty("--d-links",ANS.dl+"px");$("main").classList.toggle("mehrspaltig",!!ANS.spalten);
 const bs=$("an_breite_sel"),vb=[1200,1600,2200,3200,0];bs.value=vb.includes(ANS.breite)?ANS.breite:-1;$("an_breite").value=ANS.breite||6000;$("an_breite").disabled=!ANS.breite;
 $("an_breite_o").textContent=ANS.breite?ANS.breite+" px":"100 %";$("an_zoom_sel").value=ANS.zoom;$("an_zoom_o").textContent=Math.round(z*100)+" %"+(ANS.zoom?"":" (auto)");
 const ts=$("an_tabh_sel");ts.value=[0,320,520,900].includes(ANS.tabh)?ANS.tabh:-1;$("an_tabh").value=ANS.tabh||800;$("an_tabh").disabled=!ANS.tabh;$("an_tabh_o").textContent=ANS.tabh?ANS.tabh+" px":"Fenster";
 $("an_spalten").checked=!!ANS.spalten;if(typeof SYS!="undefined"&&SYS&&$("system").classList.contains("aktiv"))window.dispatchEvent(new Event("resize"))}
function ansSet(k,v){if(v===-1){v=k=="breite"?(ANS.breite||1800):(ANS.tabh||700)}ANS[k]=v;ansAnwenden();ansSpeichern()}
function ansSpeichern(){if(FERN){try{localStorage.setItem("sn_ansicht",JSON.stringify(ANS))}catch(e){}return}clearTimeout(ANST);ANST=setTimeout(()=>fetch("/api/ansicht",{method:"POST",headers:{"X-Token":T,"Content-Type":"application/json"},body:JSON.stringify(ANS)}).catch(()=>{}),500)}
function ansZurueck(){ANS={...ANS_STD};ansAnwenden();ansSpeichern()}
function ansichtPanel(an){const p=$("ansicht");p.classList.toggle("offen",an===undefined?!p.classList.contains("offen"):an)}
document.addEventListener("click",e=>{const p=$("ansicht");if(p.classList.contains("offen")&&!p.contains(e.target)&&!e.target.closest("header"))p.classList.remove("offen")});
function ziehen(e,bewegen,ende){e.preventDefault();document.body.classList.add("zieht");const mv=ev=>bewegen(ev),up=()=>{document.body.classList.remove("zieht");removeEventListener("pointermove",mv);removeEventListener("pointerup",up);ende&&ende()};addEventListener("pointermove",mv);addEventListener("pointerup",up)}
$("griff").addEventListener("pointerdown",e=>{const g=$("griff"),m=$("main");g.classList.add("zieht");
 ziehen(e,ev=>{const r=m.getBoundingClientRect(),f=m.offsetWidth/r.width,mitte=r.left+r.width/2;ANS.breite=Math.max(800,Math.round(2*Math.abs(ev.clientX-mitte)*f/10)*10);ansAnwenden()},()=>{g.classList.remove("zieht");ansSpeichern()})});
$("griff").addEventListener("dblclick",()=>ansSet("breite",ANS.breite?0:1200));
document.querySelectorAll(".teiler").forEach(t=>t.addEventListener("pointerdown",e=>{const box=$(t.dataset.box),k=t.dataset.k;t.classList.add("zieht");
 ziehen(e,ev=>{const r=box.getBoundingClientRect(),f=box.offsetWidth/r.width,w=(ev.clientX-r.left)*f;ANS[k]=Math.round(Math.min(box.offsetWidth-320,Math.max(k=="kd"?280:200,w)));ansAnwenden()},()=>{t.classList.remove("zieht");ansSpeichern()})}));
let UE=null;
async function schreibtest(){if(!confirm("Schreibzugriff prüfen?\nDabei wird ein Test-Voucher (1 Minute) angelegt und sofort wieder gelöscht. Sonst ändert sich nichts."))return;await api("/api/schreibtest",{},"log_st")}
async function vergleich(){const kz=$("ue_sp").value;if(!kz)return alert("Erst unter „Planung“ eine Sparte speichern.");const d=await api("/api/vergleich?sparte="+encodeURIComponent(kz),undefined,"log_ue");UE=d;
 const z=st=>d.ppsk.filter(p=>p.status==st).length;
 $("ue_k").innerHTML=kachel("Netze fehlen",d.netze.length,d.netze.length?"warn":"gut")+kachel("Passwörter neu",z("neu"),z("neu")?"warn":"gut")+kachel("Passwörter geändert",z("geaendert"),z("geaendert")?"warn":"gut")+kachel("Zugang entfernen",z("entfernen"),z("entfernen")?"schlecht":"gut")+kachel("aktuell",d.gleich,"gut")+(z("netz_fehlt")?kachel("Netz fehlt (Passwort wartet)",z("netz_fehlt"),"warn"):"");
 $("ue_bereich").style.display=(d.netze.length||d.ppsk.length)?"block":"none";
 $("ue_h_netze").textContent=d.netze.length?"Fehlende Netze ("+d.netze.length+")":"";
 $("ue_netze").innerHTML=d.netze.length?"<table><tr><th>Übertragen</th><th>Netz</th><th>VLAN</th><th>Subnetz</th></tr>"+d.netze.map(n=>`<tr><td><input type="checkbox" class="ue_n" value="${esc(n.Netz)}" style="width:auto" checked></td><td>${esc(n.Netz)}</td><td>${esc(n.VLAN)}</td><td>${esc(n.Subnetz)}</td></tr>`).join("")+"</table>":"";
 $("ue_h_ppsk").textContent=d.ppsk.length?"Passwörter je Parzelle ("+d.ppsk.length+" Unterschiede)":"";
 $("ue_ppsk").innerHTML=d.ppsk.length?"<table><tr><th>Übertragen</th><th>Parzelle</th><th>Netz</th><th>Status</th></tr>"+d.ppsk.map(p=>`<tr class="${p.status=="entfernen"?"falsch":p.status=="netz_fehlt"?"gesperrt":"geaendert"}"><td><input type="checkbox" class="ue_p" value="${esc(p.Parzelle)}" style="width:auto" checked></td><td>${esc(p.Parzelle)}</td><td>${esc(p.Netz)}</td><td>${esc(p.Status)}</td></tr>`).join("")+"</table>":""}
function ueAlle(an){document.querySelectorAll(".ue_n,.ue_p").forEach(c=>{if(!c.disabled)c.checked=an})}
async function uebertragen(aus){const kz=$("ue_sp").value,netze=[...document.querySelectorAll(".ue_n:checked")].map(c=>c.value),parz=[...document.querySelectorAll(".ue_p:checked")].map(c=>c.value);
 if(!netze.length&&!parz.length)return alert("Nichts ausgewählt.");
 if(aus&&!confirm(`Jetzt an das Gateway übertragen?\n\nSparte ${kz}\n${netze.length} Netz(e) anlegen\n${parz.length} Parzelle(n) Passwort setzen/ändern/entfernen\n\nVorher wird der alte Passwort-Stand gesichert.`))return;
 await api("/api/uebertragen",{sparte:kz,netze:netze,parzellen:parz,ausfuehren:aus},"log_ue");if(aus){const l=$("log_ue").textContent;await vergleich();$("log_ue").textContent=l+"\n\n"+$("log_ue").textContent}}
async function rueckgaengig(){const kz=$("ue_sp").value;if(!confirm("Die letzte Passwort-Übertragung für "+kz+" rückgängig machen?\nDas WLAN bekommt wieder den gesicherten Stand."))return;await api("/api/rueckgaengig",{sparte:kz},"log_ue")}
async function journalZeigen(){await api("/api/journal",undefined,"log_jn")}
let TF=null,TFL=[],TZ=null,TZAEND={};
function tfBereich(p,n){p=+p;n=+n||0;const start=p<=24?6:2,letzte=Math.pow(2,32-p)-2,platz=letzte-start+1;if(n>platz)return{fehler:"passt nicht – max. "+platz};const stop=n?start+n-1:letzte;return{text:"DHCP ."+start+"–."+stop+" · "+(stop-start+1)+" Geräte"}}
function tfMaske(p){const m=(0xffffffff<<(32-p))>>>0;return[m>>>24,(m>>16)&255,(m>>8)&255,m&255].join(".")}
function tfZeigen(){$("tf_tab").innerHTML="<tr><th>Tarif</th><th>Download Mbit/s</th><th>Upload Mbit/s</th><th>Preis €/Jahr</th><th>Netzmaske</th><th>Endgeräte</th><th>ergibt</th><th></th></tr>"+TFL.map((t,i)=>{const b=tfBereich(t.praefix,t.geraete);
 return `<tr><td><input class="tf_in" data-i="${i}" data-k="name" value="${esc(t.name)}" style="min-width:90px"></td><td><input class="tf_in" type="number" min="0.1" step="any" data-i="${i}" data-k="down" value="${esc(t.down)}" style="width:90px"></td><td><input class="tf_in" type="number" min="0.1" step="any" data-i="${i}" data-k="up" value="${esc(t.up)}" style="width:90px"></td><td><input class="tf_in" type="number" min="0" step="any" data-i="${i}" data-k="preis" value="${esc(t.preis??0)}" style="width:90px" title="${t.preis?(t.preis/12).toLocaleString("de-DE",{maximumFractionDigits:2})+" € im Monat":""}"></td>
 <td><select class="tf_in" data-i="${i}" data-k="praefix">${[24,25,26,27,28,29,30].map(p=>`<option value="${p}"${p==t.praefix?" selected":""}>/${p} · ${tfMaske(p)}</option>`).join("")}</select></td>
 <td><input class="tf_in" type="number" min="0" data-i="${i}" data-k="geraete" value="${esc(t.geraete)}" style="width:80px"></td><td class="tf_erg" data-i="${i}">${b.fehler?'<span class="fehler">'+esc(b.fehler)+"</span>":esc(b.text)}</td>
 <td><button class="k" onclick="tfWeg(${i})" title="Tarif entfernen">✕</button></td></tr>`}).join("");
 document.querySelectorAll(".tf_in").forEach(e=>e.oninput=e.onchange=()=>{const t=TFL[e.dataset.i];t[e.dataset.k]=e.dataset.k=="name"?e.value:e.value===""?"":+e.value;const b=tfBereich(t.praefix,t.geraete);
  document.querySelector(`.tf_erg[data-i="${e.dataset.i}"]`).innerHTML=b.fehler?'<span class="fehler">'+esc(b.fehler)+"</span>":esc(b.text)})}
function tfModusHint(){$("tf_modus_hint").textContent=$("tf_modus").value=="tarif"?"Wie in UniFi unter Einstellungen → QoS: eine Regel „SparteNet-Tarif-Basic“ mit allen Basic-Netzen. Bitte einmal prüfen, ob das Limit dann für jedes Netz einzeln oder für alle zusammen gilt (Geschwindigkeitstest in zwei Basic-Parzellen gleichzeitig). Teilen sich alle die Bandbreite, „eine Regel je Netz“ wählen.":"Jede Parzelle bekommt eine eigene Regel „SparteNet-Netz-BW-Paz.067“ – die Bandbreite ist sicher je Parzelle getrennt, dafür gibt es viele Regeln."}
async function tfLaden(){const d=await api("/api/tarife");TF=d;TFL=d.tarife.map(t=>({...t,alt:t.name}));tfZeigen();$("tf_modus").value=d.modus;tfModusHint();tzMassenFuellen()}
function tfNeu(){TFL.push({name:"Tarif "+(TFL.length+1),down:50,up:10,praefix:29,geraete:5,preis:0});tfZeigen()}
function tfWeg(i){if(!confirm("Tarif „"+TFL[i].name+"“ entfernen? Netze mit diesem Tarif sind danach ohne Tarif (erst nach „Speichern“)."))return;TFL.splice(i,1);tfZeigen()}
function tfStandard(){if(!confirm("Beispiel-Tarife Basic, Plus und Max einsetzen? Gespeichert wird erst mit „Tarife speichern“."))return;TFL=TF.standard.map(t=>({...t,alt:(TFL.find(x=>x.name==t.name)||{}).alt}));tfZeigen()}
async function tfSpeichern(){const d=await api("/api/tarife",{tarife:TFL,modus:$("tf_modus").value},"log_tf");TF.tarife=d.tarife;TF.modus=d.modus;TFL=d.tarife.map(t=>({...t,alt:t.name}));tfZeigen();tzMassenFuellen();if(TZ)tzZeigen()}
function tzOptionen(wert){return `<option value="">– kein Tarif –</option>`+(TF?TF.tarife:[]).map(t=>`<option value="${esc(t.name)}"${t.name==wert?" selected":""}>${esc(t.name)} · ${esc(t.down)}/${esc(t.up)} · /${t.praefix}</option>`).join("")}
function tzMassenFuellen(){$("tz_massen").innerHTML=tzOptionen("")}
async function tzLaden(){if(!TF)await tfLaden();if(Object.keys(TZAEND).length&&!confirm("Es gibt ungespeicherte Zuordnungen. Verwerfen?"))return;TZAEND={};
 const d=await api("/api/tarif-vergleich",undefined,"log_tz");TZ=d;tzZeigen()}
function tzZeigen(){const d=TZ,z=a=>d.ops.filter(o=>o.art==a).length;
 $("tz_k").innerHTML=kachel("Netze mit Tarif",d.zeilen.filter(r=>r.tarif).length,"gut")+kachel("Netze ändern",z("netz"),z("netz")?"warn":"gut")+kachel("QoS neu",z("qos_neu"),z("qos_neu")?"warn":"gut")+kachel("QoS ändern",z("qos_aendern"),z("qos_aendern")?"warn":"gut")+kachel("QoS löschen",z("qos_loeschen"),z("qos_loeschen")?"schlecht":"gut")+kachel("Hinweise",d.zeilen.filter(r=>r.warnung).length,d.zeilen.some(r=>r.warnung)?"warn":"gut");
 $("tz_bereich").style.display="block";
 $("tz_tab").innerHTML="<table><tr><th></th><th>Netz</th><th>VLAN</th><th>Subnetz jetzt</th><th>DHCP jetzt</th><th>QoS jetzt</th><th>Tarif</th><th>Ziel / Änderung</th><th>Hinweis</th></tr>"+d.zeilen.map(r=>{const w=r.id in TZAEND?TZAEND[r.id]:r.tarif;
  return `<tr data-id="${esc(r.id)}" data-such="${esc((r.name+" "+r.subnetz+" "+r.vlan+" "+r.tarif).toLowerCase())}" class="${r.id in TZAEND?"geaendert":r.status=="fehler"?"falsch":r.status=="aendern"?"geaendert":""}"><td><input type="checkbox" class="tz_m" style="width:auto"></td><td>${esc(r.name)}</td><td>${esc(r.vlan)}</td><td>${esc(r.subnetz)}</td><td>${esc(r.dhcp)}</td><td style="font-size:12px">${esc(r.qos||"–")}</td>
  <td><select class="tz_sel" data-id="${esc(r.id)}" style="min-width:170px">${tzOptionen(w)}</select></td><td style="font-size:12px">${r.id in TZAEND?"<i>ungespeichert</i>":esc(r.tarif?(r.status=="aendern"?r.aenderung:r.status=="gleich"?"✔ passt":r.aenderung)+(r.ziel?" → "+r.ziel:""):"")}</td><td style="font-size:12px">${esc(r.warnung)}</td></tr>`}).join("")+"</table>";
 document.querySelectorAll(".tz_sel").forEach(s=>s.onchange=()=>tzSetzen(s.dataset.id,s.value));tzFilter();tzOffen();tqZeigen()}
function tzSetzen(id,wert){const r=TZ.zeilen.find(x=>x.id==id);if(wert===r.tarif)delete TZAEND[id];else TZAEND[id]=wert;const s=document.querySelector(`.tz_sel[data-id="${CSS.escape(id)}"]`);if(s)s.value=wert;
 const tr=document.querySelector(`#tz_tab tr[data-id="${CSS.escape(id)}"]`);if(tr)tr.classList.toggle("geaendert",id in TZAEND||r.status=="aendern");tzOffen()}
function tzOffen(){const n=Object.keys(TZAEND).length;$("tz_offen").textContent=n?n+" ungespeichert":"alles gespeichert";$("tz_offen").classList.toggle("ok",!n)}
function tzFilter(){const q=$("tz_suche").value.trim().toLowerCase();document.querySelectorAll("#tz_tab tr[data-id]").forEach(tr=>tr.style.display=!q||tr.dataset.such.includes(q)?"":"none")}
function tzMarkAlle(an){document.querySelectorAll("#tz_tab tr[data-id]").forEach(tr=>{if(tr.style.display!="none"||!an)tr.querySelector(".tz_m").checked=an})}
function tzMassen(){const w=$("tz_massen").value,m=[...document.querySelectorAll("#tz_tab tr[data-id]")].filter(tr=>tr.style.display!="none"&&tr.querySelector(".tz_m").checked);if(!m.length)return alert("Erst Netze markieren (Häkchen links).");
 m.forEach(tr=>tzSetzen(tr.dataset.id,w));$("log_tz").textContent=m.length+" Netz(e) auf „"+(w||"kein Tarif")+"“ gesetzt – noch „Zuordnung speichern“."}
async function tzSpeichern(){if(Object.keys(TZAEND).length)await api("/api/tarif-zuordnung",{aenderungen:TZAEND},"log_tz");const l=$("log_tz").textContent;TZAEND={};const d=await api("/api/tarif-vergleich",undefined,"log_tz");TZ=d;tzZeigen();$("log_tz").textContent=l+"\n"+$("log_tz").textContent}
async function tzErkennen(){if(!TZ)await tzLaden();if(!TZ)return;const d=await api("/api/tarif-erkennen",{},"log_tz");let n=0;Object.entries(d.vorschlag).forEach(([id,t])=>{if(TZ.zeilen.some(r=>r.id==id)){tzSetzen(id,t);n++}});
 $("log_tz").textContent=n?n+" Netz(e) mit Vorschlag eingetragen (gelb markiert). Prüfen, dann „Zuordnung speichern“.":"Kein Vorschlag – alle Parzellen haben schon einen Tarif oder die Netzmaske passt zu keinem Tarif eindeutig."}
function tqZeigen(){const d=TZ,q=d.ops.filter(o=>o.art!="netz"),n=d.ops.filter(o=>o.art=="netz"),wort={qos_neu:"anlegen",qos_aendern:"ändern",qos_loeschen:"löschen"};
 $("tq_h_qos").textContent=q.length?"QoS-Regeln ("+q.length+")":"";$("tq_h_netz").textContent=n.length?"Netze: Subnetz / DHCP ("+n.length+")":"";
 $("tq_qos").innerHTML=q.length?"<table><tr><th>Übertragen</th><th>Regel</th><th>Aktion</th><th>Inhalt</th></tr>"+q.map(o=>`<tr class="${o.art=="qos_loeschen"?"falsch":"geaendert"}"><td><input type="checkbox" class="tq_r" value="${esc(o.name)}" style="width:auto" checked></td><td>${esc(o.name)}</td><td>${wort[o.art]}</td><td>${esc(o.text)}</td></tr>`).join("")+"</table>":"";
 $("tq_netz").innerHTML=n.length?"<table><tr><th>Übertragen</th><th>Netz</th><th>Änderung</th><th>Hinweis</th></tr>"+n.map(o=>{const r=d.zeilen.find(x=>x.id==o.id)||{};return `<tr class="geaendert"><td><input type="checkbox" class="tq_n" value="${esc(o.id)}" style="width:auto" checked></td><td>${esc(o.name)}</td><td>${esc(o.text)}</td><td style="font-size:12px">${esc(r.warnung||"")}</td></tr>`}).join("")+"</table>":"";
 $("tq_kn").style.display=(q.length||n.length)?"flex":"none";$("log_tq").textContent=(q.length||n.length)?"":"✔ Gateway entspricht den Tarifen – nichts zu übertragen."}
function tqAlle(an){document.querySelectorAll(".tq_r,.tq_n").forEach(c=>c.checked=an)}
async function tqUebertragen(aus){if(!TZ)return alert("Erst „Netze laden & Unterschiede ermitteln“.");if(Object.keys(TZAEND).length)return alert("Es gibt ungespeicherte Zuordnungen – erst „Zuordnung speichern & neu vergleichen“.");
 const regeln=[...document.querySelectorAll(".tq_r:checked")].map(c=>c.value),netze=[...document.querySelectorAll(".tq_n:checked")].map(c=>c.value);if(!regeln.length&&!netze.length)return alert("Nichts ausgewählt.");
 if(aus&&!confirm(`Jetzt an das Gateway übertragen?\n\n${regeln.length} QoS-Regel(n) anlegen/ändern/löschen\n${netze.length} Netz(e): Subnetz/DHCP ändern\n\n`+(netze.length?"Achtung: Geräte in verkleinerten Netzen mit IP außerhalb des neuen Bereichs verlieren kurz die Verbindung (WLAN aus/an hilft).\n\n":"")+"Vorher wird der alte Stand gesichert."))return;
 await api("/api/tarif-uebertragen",{regeln:regeln,netze:netze,ausfuehren:aus},"log_tq");if(aus){const l=$("log_tq").textContent;TZ=await api("/api/tarif-vergleich",undefined,"log_tz");tzZeigen();$("log_tq").textContent=l}}
async function tqRueckgaengig(){if(!confirm("Die letzte Tarif-Übertragung rückgängig machen?\nQoS-Regeln „SparteNet-…“ und geänderte Netze bekommen wieder den gesicherten Stand."))return;await api("/api/tarif-rueckgaengig",{},"log_tq");if(TZ){const l=$("log_tq").textContent;TZ=await api("/api/tarif-vergleich",undefined,"log_tz");tzZeigen();$("log_tq").textContent=l}}

const FERN=__FERN__==1;let INSTALL=null;
if(FERN)document.body.classList.add("fern");
if("serviceWorker" in navigator&&isSecureContext)navigator.serviceWorker.register("/sw.js").catch(()=>{});
addEventListener("beforeinstallprompt",e=>{e.preventDefault();INSTALL=e;$("install_k").style.display="flex"});
addEventListener("appinstalled",()=>{$("install_k").style.display="none"});
async function installieren(){if(!INSTALL)return;INSTALL.prompt();await INSTALL.userChoice;INSTALL=null;$("install_k").style.display="none"}
async function abmelden(){if(!confirm("Auf diesem Gerät abmelden?"))return;await fetch("/abmelden",{method:"POST",headers:{"X-Token":T}});location.reload()}
async function startLaden(){const d=await api("/api/start",undefined,"log_start");$("st_zeit").textContent=d.zeit;
 $("st_k").innerHTML=d.kacheln.map(k=>`<div class="kachel ${k.a}"><b>${esc(k.v)}</b>${esc(k.t)}<small>${esc(k.k||"")}</small></div>`).join("")}
async function parzelleZeigen(){const kz=$("st_sp").value,p=$("st_p").value;if(!kz)return alert("Erst unter „Planung“ eine Sparte speichern.");if(!p)return $("st_p").focus();
 $("pz_karte").innerHTML="";const d=await api("/api/parzelle?sparte="+encodeURIComponent(kz)+"&p="+encodeURIComponent(p),undefined,"log_pz");PZ=d;
 $("pz_karte").innerHTML=`<div class="pz"><div><dl><dt>Parzelle</dt><dd>${esc(d.parzelle)} · ${esc(d.sparte)}</dd><dt>Netz</dt><dd>${esc(d.netz)} (VLAN ${esc(d.vlan)})</dd><dt>WLAN</dt><dd>${esc(d.wlan)}</dd></dl>
 <div class="pw" id="pz_pw">${esc(d.passwort)}</div><div class="knoepfe" style="margin-top:4px"><button class="k" onclick="kopieren(PZ.passwort,'log_pz')">Passwort kopieren</button><button class="k" onclick="pzTeilen()">Teilen</button></div></div>
 <div class="qr" title="Mit der Handy-Kamera scannen – verbindet direkt mit dem WLAN">${d.qr}</div></div>`}
let PZ=null;
function pzTeilen(){teilen('WLAN Parzelle '+PZ.parzelle,'WLAN: '+PZ.wlan+'\nPasswort: '+PZ.passwort,'log_pz')}
async function kopieren(t,logid){try{await navigator.clipboard.writeText(t);$(logid).textContent="✔ In die Zwischenablage kopiert."}catch(e){prompt("Kopieren:",t)}}
async function teilen(titel,text,logid){if(navigator.share){try{await navigator.share({title:titel,text:text})}catch(e){}}else kopieren(text,logid)}
async function schnellVoucher(min){const dauer={120:"2 Stunden",1440:"1 Tag",10080:"1 Woche"}[min];if(!confirm("Einen Gast-Voucher für "+dauer+" erstellen?"))return;
 $("sv_code").innerHTML="";const d=await api("/api/voucher",{anzahl:1,minuten:min,name:"Gast",ausfuehren:true},"log_sv");const c=(d.codes||[])[0];
 if(c){const f=c.length==10?c.slice(0,5)+"-"+c.slice(5):c;$("sv_code").innerHTML=`<div class="code">${esc(f)}</div><p class="hint" style="text-align:center">Gültig ${dauer} ab der ersten Anmeldung im Gäste-WLAN</p><div class="knoepfe"><button class="k" onclick="teilen('Gast-WLAN','Gast-WLAN Zugangscode: ${esc(f)} (gültig ${dauer})','log_sv')">Teilen</button><button class="k" onclick="kopieren('${esc(f)}','log_sv')">Kopieren</button></div>`}}
async function fernLaden(){if(FERN)return;const d=await api("/api/fern",undefined,null);FERNST=d;
 $("fern_pin_st").textContent=d.pin_gesetzt?"festgelegt":"fehlt";$("fern_pin_st").className="status"+(d.pin_gesetzt?" ok":"");$("fern_lan").checked=d.lan;$("fern_lan").disabled=!!d.lan_env;
 $("fern_geraete").textContent=d.geraete.length?"Angemeldet: "+d.geraete.map(g=>(/Android/.test(g.geraet)?"Android":/iPhone|iPad/.test(g.geraet)?"iPhone/iPad":/Windows/.test(g.geraet)?"Windows":"Gerät")+" seit "+g.seit).join(" · "):"Noch kein Handy angemeldet.";
 const ts=d.tailscale;$("ts_st").innerHTML=!ts.installiert?"✖ Tailscale ist auf diesem PC nicht installiert – <b>tailscale.com/download</b>":!ts.aktiv?"⚠ Tailscale ist installiert, aber nicht angemeldet/aktiv.":ts.freigabe?"✔ Freigabe aktiv: <b>"+esc(ts.url)+"</b>":"Tailscale aktiv ("+esc(ts.name)+") – Freigabe noch aus.";
 $("ts_an").disabled=!ts.installiert||!ts.aktiv||ts.freigabe;$("ts_aus").disabled=!ts.freigabe;
 $("lan_st").innerHTML=d.lan_env?"Durch SPARTENET_HOST vorgegeben":d.lan_aktiv?(d.adressen.length?"✔ Erreichbar unter "+d.adressen.map(esc).join(", "):"✔ Eingeschaltet, aber keine Netzwerk-Adresse gefunden."):d.lan?"⚠ Eingeschaltet – wirkt nach Neustart des Managers.":"aus";
 $("fern_qr").innerHTML=Object.entries(d.qr).map(([u,s])=>`<figure>${s}<figcaption>${esc(u)}</figcaption></figure>`).join("")||'<p class="hint">Hier erscheinen QR-Codes, sobald ein Zugriff aktiv ist.</p>'}
let FERNST=null;
async function fernPin(){const p=$("fern_pin").value;if(!p)return $("fern_pin").focus();await api("/api/fern",{pin:p},"log_fern");$("fern_pin").value="";fernLaden()}
async function fernAbmelden(){if(!confirm("Alle Handy-, Tablet- und Browser-Sitzungen abmelden? Sie müssen sich danach erneut mit Manager-Passwort oder Handy-PIN anmelden."))return;await api("/api/fern",{abmelden:true},"log_fern");fernLaden()}
async function fernLan(){const an=$("fern_lan").checked;if(an&&!confirm("Den Manager im Heimnetz erreichbar machen?\nJedes Gerät im selben Netz sieht dann die Anmeldeseite – Zugriff nur mit Manager-Passwort oder optionaler Handy-PIN. Wirkt nach Neustart des Managers."))return $("fern_lan").checked=false;
 try{await api("/api/fern",{lan:an},"log_fern")}catch(e){$("fern_lan").checked=!an}fernLaden()}
async function tailscale(an){if(!confirm(an?"Tailscale-Freigabe einschalten?\nDer Manager ist dann für deine Geräte im Tailscale-Konto per HTTPS erreichbar (mit Manager-Passwort oder optionaler Handy-PIN).":"Tailscale-Freigabe ausschalten?"))return;await api("/api/tailscale",{an:an},"log_fern");fernLaden()}

let KK=null,KB=null,KBAEND={};
const eur=(v,n=0)=>v==null||v===""?"–":Number(v).toLocaleString("de-DE",{minimumFractionDigits:n,maximumFractionDigits:n})+" €";
const pct=v=>(v*100).toLocaleString("de-DE",{minimumFractionDigits:1,maximumFractionDigits:1})+" %";
function balken(v){const w=Math.round(Math.min(1,v)*100);return `<div class="balken" style="min-width:110px"><i class="${v<.3?"s":v<.6?"w":""}" style="width:${w}%"></i><span>${pct(v)}</span></div>`}
async function kkLaden(){const d=await api("/api/kalkulation?prognose="+($("kk_prog").checked?1:0),undefined,"log_kk");KK=d;const g=d.gesamt;
 $("kk_k").innerHTML=kachel("Auslastung (Sparten mit Buchungen)",pct(g.auslastung_konf),g.auslastung_konf>=.6?"gut":g.auslastung_konf>=.3?"warn":"schlecht")+
  kachel("gebuchte Parzellen",g.gebucht+" / "+g.parzellen_konf,"gut")+kachel("Sparten mit Buchungen",g.sparten_konf+" / "+g.sparten,"gut")+
  kachel("Auslastung aller eingetragenen",pct(g.auslastung_alle)+"<small>"+g.parzellen_alle+" Parzellen</small>","")+
  kachel("Umsatz / Jahr",eur(g.umsatz_brutto)+(g.ku?"":"<small>netto "+eur(g.umsatz)+"</small>"),"gut")+
  kachel("Deckungsbeitrag / Jahr",eur(g.db),g.db>=0?"gut":"schlecht")+
  kachel("Ergebnis nach zentralen Kosten",eur(g.ergebnis_vor_afa)+"<small>zentral "+eur(g.zentral)+" ("+(g.phase=="start"?"Startphase":"Ausbau")+")</small>",g.ergebnis_vor_afa>=0?"gut":"schlecht")+
  kachel("Ergebnis nach Abschreibung",eur(g.ergebnis)+"<small>AfA "+eur(g.afa)+"</small>",g.ergebnis>=0?"gut":"schlecht")+
  kachel("Kleinunternehmer-Grenze",g.ku?(g.ku_status.startsWith("unter")?"OK":"über"):"–",g.ku?(g.ku_status.startsWith("unter")?"gut":"schlecht"):"")+
  (g.ku?`<div class="kachel"><b style="font-size:16px">${esc(g.ku_status)}</b>Umsatz ${eur(g.umsatz_brutto)} von ${eur(g.ku_grenze)}<small>${g.ku_rest_parzellen!=null?"noch ca. "+g.ku_rest_parzellen+" Buchungen bis zur Grenze":""}</small></div>`:"");
 const T=d.tarife;let h="<table><tr><th>Sparte</th><th>Gateway</th><th>Parzellen</th><th>gebucht</th><th>Buchungsrate</th>"+T.map(t=>"<th>"+esc(t.name)+"<br><small>"+eur(t.preis)+"/J.</small></th>").join("")+
  "<th>Umsatz / Jahr</th><th>Ø € / Monat</th><th>Investition</th><th>Masten mit Technik</th><th>Uplink €/Monat</th><th>lfd. Kosten / Jahr</th><th>Deckungsbeitrag</th><th>Amortisation</th><th>Uplink-Bedarf</th><th>Status</th></tr>";
 for(const z of d.zeilen){h+=`<tr class="${z.status=="Prognose"?"gesperrt":""}"><td><b>${esc(z.name)}</b> <span class="mono" style="color:var(--muted)">${esc(z.kz)}</span></td><td>${esc(z.gateway)}</td><td>${z.n}</td><td>${z.status=="Prognose"?"≈ "+z.prognose:z.gebucht}</td><td>${balken(z.status=="Prognose"?z.prognose/z.n:z.rate)}</td>`+
  T.map(t=>"<td>"+(z.je[t.name]||"")+"</td>").join("")+`<td>${eur(z.umsatz_brutto)}</td><td>${z.erloes_monat?eur(z.erloes_monat,2):"–"}</td>
  <td><input class="kk_in" data-kz="${esc(z.kz)}" data-f="investition" value="${z.investition??""}" inputmode="decimal" style="width:110px"></td>
  <td><input class="kk_in" data-kz="${esc(z.kz)}" data-f="masten" value="${z.masten??""}" inputmode="numeric" style="width:70px"></td>
  <td><input class="kk_in" data-kz="${esc(z.kz)}" data-f="uplink" value="${z.uplink??""}" placeholder="${d.annahmen.uplink_monat}" inputmode="decimal" style="width:80px"></td>
  <td>${eur(z.kosten)}</td><td style="color:${z.db<0?"var(--red)":"inherit"}">${eur(z.db)}</td><td>${z.amortisation==null?"–":typeof z.amortisation=="number"?z.amortisation.toLocaleString("de-DE")+" J.":esc(z.amortisation)}</td>
  <td style="color:${z.uplink_warnung?"var(--red)":"inherit"}">${z.uplink_bedarf} Mbit/s</td><td>${esc(z.status)}</td></tr>`}
 h+=`<tr class="kopf"><td>Summe</td><td></td><td>${g.parzellen_alle}</td><td>${g.gebucht}</td><td>${balken(g.auslastung_alle)}</td>`+T.map(t=>"<td>"+(g.je[t.name]||"")+"</td>").join("")+
  `<td>${eur(g.umsatz_brutto)}</td><td></td><td>${eur(g.investition)}</td><td></td><td></td><td>${eur(g.kosten)}</td><td>${eur(g.db)}</td><td>${g.amortisation==null?"–":typeof g.amortisation=="number"?g.amortisation.toLocaleString("de-DE")+" J.":esc(g.amortisation)}</td><td></td><td></td></tr></table>`;
 $("kk_tab").innerHTML=d.zeilen.length?h:'<p class="hint" style="padding:12px">Noch keine Sparten – unter „Planung“ eintragen oder unten den VLAN-Planer übernehmen.</p>';
 document.querySelectorAll(".kk_in").forEach(e=>e.onchange=async()=>{await api("/api/kalk-sparte",{sparte:e.dataset.kz,[e.dataset.f]:e.value},"log_kk");kkLaden()});
 const alt=$("kb_sp").value;$("kb_sp").innerHTML=d.zeilen.map(z=>`<option value="${esc(z.kz)}">${esc(z.name)} (${esc(z.kz)})</option>`).join("");if(alt&&d.zeilen.some(z=>z.kz==alt))$("kb_sp").value=alt;
 $("kb_tarif").innerHTML='<option value="">– kein Tarif (nicht gebucht) –</option>'+T.map(t=>`<option value="${esc(t.name)}">${esc(t.name)} · ${eur(t.preis)}/Jahr</option>`).join("");
 kaZeigen(d.annahmen,d.texte);if(!KB&&d.zeilen.length)kbLaden(true)}
window.addEventListener("unhandledrejection",e=>e.preventDefault());  // Fehler zeigt api() bereits im jeweiligen Protokollfeld
// Drucken / PDF je Kasten: jeder Kasten (.karte) bekommt oben links einen Knopf; gedruckt wird nur dieser Kasten
function druckKnoepfe(){document.querySelectorAll(".karte").forEach(k=>{if(k.querySelector(":scope>.druckknopf")||k.closest(".druckkopf"))return;
 const b=document.createElement("button");b.type="button";b.className="druckknopf";b.textContent="🖨 Drucken / PDF";b.title="Nur diesen Kasten drucken – im Druckdialog „Als PDF speichern“ wählen für eine PDF-Datei";
 b.onclick=e=>{e.stopPropagation();kastenDrucken(k)};k.prepend(b)})}
function kastenDrucken(k){const t=(k.querySelector("h2,h3")||{}).textContent||"SparteNet";const kopf=document.createElement("div");kopf.className="druckkopf";
 kopf.textContent="SparteNet Manager · "+t.trim()+" · "+new Date().toLocaleString("de-DE")+" · "+ICH.name;k.prepend(kopf);
 const breit=[...k.querySelectorAll("table")].some(x=>x.scrollWidth>760);const st=document.createElement("style");st.textContent="@page{size:A4 "+(breit?"landscape":"portrait")+";margin:12mm}";document.head.appendChild(st);
 document.body.classList.add("einzeldruck");k.classList.add("druck-diese");
 const fertig=()=>{document.body.classList.remove("einzeldruck");k.classList.remove("druck-diese");kopf.remove();st.remove();window.removeEventListener("afterprint",fertig)};
 window.addEventListener("afterprint",fertig);setTimeout(()=>{window.print();setTimeout(fertig,500)},50)}

const ICH=__ICH__;setTimeout(farbeZeigen,0);
function reiterErlaubt(id){return ICH.admin||!(id in ICH.reiter)||ICH.reiter[id]!="kein"}
function startReiter(){const h=location.hash.slice(1);if(TABS.some(t=>t[0]==h)&&reiterErlaubt(h))return h;const t=TABS.find(t=>reiterErlaubt(t[0]));return t?t[0]:"benutzer"}
function rechteHinweis(id){const e=$("nurlesen");if(!e)return;const st=ICH.admin?"schreiben":ICH.reiter[id];
 if(st=="lesen"){e.textContent="Nur lesen – in diesem Bereich lassen sich mit Ihrem Konto Daten ansehen, aber nichts ändern oder ans Gateway übertragen.";e.hidden=false}else e.hidden=true}
(function(){const k=$("ich_k");if(k)k.textContent="👤 "+ICH.name+" · "+ICH.recht_text+(ICH.sparten&&ICH.sparten.length?" · "+ICH.sparten.join(", "):"");
 TABS.forEach(([id])=>{const b=$("n_"+id);if(b&&!reiterErlaubt(id))b.style.display="none"});
 document.querySelectorAll("[data-bereich]").forEach(e=>{const st=ICH.admin?"schreiben":(ICH.bereiche[e.dataset.bereich]||"kein");if(st=="kein")e.style.display="none";else if(st=="lesen")e.classList.add("nurlesen-karte")});
 document.querySelectorAll(".bn-admin").forEach(e=>e.hidden=!ICH.admin);if(!ICH.admin){const b=$("n_benutzer");if(b)b.textContent="Mein Konto"}})();
let BN=null;const BNOFFEN=new Set();
async function bnStart(){const d=await api("/api/benutzer-ich",undefined,"log_bni");$("log_bni").textContent="";
 $("bn_ich").innerHTML=kachel("Benutzername",esc(d.name),"")+kachel("Rechte",esc(d.recht_text),d.admin?"gut":"")+(d.anzeige?kachel("Name",esc(d.anzeige),""):"")+(d.sparten&&d.sparten.length?kachel("Sparten",esc(d.sparten.join(", ")),"warn"):"");
 $("bn_ich_liste").innerHTML=d.admin?"":"<table><tr><th>Bereich</th><th>Ihr Recht</th></tr>"+d.liste.map(x=>`<tr class="${x.stufe=="kein Zugriff"?"gesperrt":""}"><td>${esc(x.text)}</td><td>${esc(x.stufe)}</td></tr>`).join("")+"</table>";
 zfZeigen(d);$("bn_ich_pw").hidden=!d.eigenes_passwort;$("bn_admin_hint").hidden=d.name!="admin";if(ICH.admin)bnLaden()}
async function bnEigenesPw(){await api("/api/benutzer-ich",{alt:$("bn_alt").value,passwort:$("bn_neu1").value,passwort2:$("bn_neu2").value},"log_bni");["bn_alt","bn_neu1","bn_neu2"].forEach(i=>$(i).value="")}
async function bnLaden(){bnZeigen(await api("/api/benutzer",undefined,"log_bn"))}
async function bnSpeichern(b,logid){bnZeigen(await api("/api/benutzer-speichern",b,logid||"log_bn"))}
function bnZeigen(d){BN=d;const box=$("bn_tab"),y=box.scrollTop;$("bn_2fa_pflicht").checked=!!d.zwei_faktor_pflicht;
 if(!$("bn_vorlage").options.length)$("bn_vorlage").innerHTML=Object.entries(d.vorlagen).map(([k,v])=>`<option value="${k}">${esc(v.text)}</option>`).join("")+'<option value="#admin">Administrator</option><option value="#gesperrt">Gesperrt (noch nicht freigeschaltet)</option>';
 let h="<table><tr><th>Benutzername</th><th>Name</th><th>Kontoart</th><th>Rechte</th><th>angelegt</th><th>zuletzt angemeldet</th><th>Sitzungen</th><th>2FA</th><th></th></tr>";
 for(const z of d.zeilen){const n=esc(z.name),offen=BNOFFEN.has(z.name);
  h+=`<tr class="${z.art=="gesperrt"?"recht-gesperrt":""}"><td><b>${n}</b>${z.name==d.ich?" <small>(Sie)</small>":""}</td>
  <td>${z.fest?esc(z.anzeige):`<input class="bn_anz" data-n="${n}" value="${esc(z.anzeige)}" style="min-width:170px">`}</td>
  <td>${z.fest?"Administrator":`<select class="bn_art" data-n="${n}">${Object.entries(d.arten).map(([k,t])=>`<option value="${k}"${k==z.art?" selected":""}>${esc(t)}</option>`).join("")}</select>`}</td>
  <td>${esc(z.recht_text)}${z.sparten&&z.sparten.length?'<br><small>nur '+esc(z.sparten.join(", "))+'</small>':""}${z.art=="bereiche"?` <button class="k" onclick="bnAuf('${n}')">${offen?"Rechte schließen":"Rechte …"}</button>`:""}</td>
  <td>${esc(z.angelegt)}${z.von?" <small>von "+esc(z.von)+"</small>":""}</td><td>${esc(z.zuletzt)||"–"}</td><td>${z.sitzungen||"–"}</td><td>${z.zwei_faktor?`✔ <button class="k" onclick="zfReset('${n}')">zurücksetzen</button>`:"–"}</td>
  <td>${z.fest?"":`<button class="k" onclick="bnPw('${n}')">Passwort setzen</button> <button class="k" onclick="bnLoeschen('${n}')">Löschen</button>`}</td></tr>`;
  if(offen&&z.art=="bereiche")h+=`<tr class="bn_detail"><td colspan="9"><div class="knoepfe" style="margin:4px 0 6px">Vorlage übernehmen: ${Object.entries(d.vorlagen).map(([k,v])=>`<button class="k" onclick="bnVorlage('${n}','${k}')">${esc(v.text.split(":")[0])}</button>`).join(" ")}</div>
   <div class="reihe" style="margin:4px 0 10px;max-width:760px"><div><label>Nur diese Sparten (Kürzel, z. B. „BW, FEIER“ – leer = alle Sparten)</label><input class="bn_sp" data-n="${n}" value="${esc((z.sparten||[]).join(", "))}" placeholder="alle Sparten" style="text-transform:uppercase"></div></div>
   <div class="bn_matrix">${d.bereiche.map(b=>{const st=z.bereiche[b.k]||"kein";return `<label>${esc(b.text)}<select class="bn_ber ${st}" data-n="${n}" data-k="${b.k}">${b.stufen.map(x=>`<option value="${x}"${x==st?" selected":""}>${esc(d.stufen[x])}</option>`).join("")}</select></label>`}).join("")}</div></td></tr>`}
 box.innerHTML=h+"</table>";box.scrollTop=y;
 box.querySelectorAll(".bn_art").forEach(e=>e.onchange=()=>{if(e.value=="bereiche")BNOFFEN.add(e.dataset.n);bnSpeichern({name:e.dataset.n,art:e.value})});
 box.querySelectorAll(".bn_anz").forEach(e=>e.onchange=()=>bnSpeichern({name:e.dataset.n,anzeige:e.value}));
 box.querySelectorAll(".bn_ber").forEach(e=>e.onchange=()=>bnSpeichern({name:e.dataset.n,bereiche:{[e.dataset.k]:e.value}}));
 box.querySelectorAll(".bn_sp").forEach(e=>e.onchange=()=>bnSpeichern({name:e.dataset.n,sparten:e.value}))}
function bnAuf(n){BNOFFEN.has(n)?BNOFFEN.delete(n):BNOFFEN.add(n);bnZeigen(BN)}
function bnVorlage(n,k){bnSpeichern({name:n,art:"bereiche",vorlage:k})}
async function bnAnlegen(){const v=$("bn_vorlage").value,n=$("bn_name").value.trim();const b={neu:true,name:n,anzeige:$("bn_anz").value.trim(),passwort:$("bn_pw1").value,passwort2:$("bn_pw2").value};
 if(v.startsWith("#"))b.art=v.slice(1);else{b.art="bereiche";b.vorlage=v}
 const r=await api("/api/benutzer-speichern",b,"log_bnn");["bn_name","bn_anz","bn_pw1","bn_pw2"].forEach(i=>$(i).value="");$("bn_vorschlag").textContent="";if(b.art=="bereiche")BNOFFEN.add(n.toLowerCase());bnZeigen(r)}
function bnZufall(){const z="ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";const a=new Uint32Array(16);crypto.getRandomValues(a);return [...a].map(x=>z[x%z.length]).join("").replace(/(.{4})(?!$)/g,"$1-")}
function bnVorschlag(){const p=bnZufall();$("bn_pw1").value=p;$("bn_pw2").value=p;$("bn_vorschlag").textContent=p+"  ← bitte notieren und dem Benutzer sicher mitteilen"}
async function bnPw(n){const p=prompt("Neues Passwort für „"+n+"“ (mind. 12 Zeichen). Leer lassen = Vorschlag erzeugen:");if(p===null)return;const pw=p||bnZufall();
 await bnSpeichern({name:n,passwort:pw,passwort2:pw});if(!p)$("log_bn").textContent+="\nNeues Passwort: "+pw+"  (bitte notieren – wird nicht noch einmal angezeigt)"}
async function bnLoeschen(n){if(!confirm("Konto „"+n+"“ löschen? Offene Sitzungen werden beendet."))return;BNOFFEN.delete(n);bnZeigen(await api("/api/benutzer-loeschen",{name:n},"log_bn"))}

let UP=null,UPT=null;
const UPICON={"offen":"○","läuft":"⏳","fertig":"✔","fehler":"✖"};
async function upLaden(still){const d=await api("/api/update",undefined,still?undefined:"log_up");upZeigen(d);return d}
function upZeigen(d){UP=d;const l=d.lage,a=d.aktiv||{};
 $("up_st").textContent=d.laeuft?"Update läuft":l?(l.verfuegbar?"Update verfügbar":"aktuell"):"";$("up_st").hidden=!$("up_st").textContent;$("up_st").className="status"+(l&&!l.verfuegbar&&!d.laeuft?" ok":"");
 $("up_k").innerHTML=kachel("installiert",esc(d.version)+"<small>"+(a.ordner&&d.code.endsWith(a.ordner)?"aus updates/"+esc(a.ordner):"mitgeliefert")+"</small>","")+
  (l?kachel("auf GitHub ("+esc(l.kanal)+")",esc(l.neu)+"<small>"+esc(l.kurz)+" · "+esc(l.datum)+"</small>",l.verfuegbar?"warn":"gut"):"")+
  kachel("zuletzt geprüft",l?esc(l.zeit):"–","")+(a.fehler?kachel("letztes Update",'<span style="font-size:15px">startete nicht</span><small>'+esc(a.fehler)+"</small>","schlecht"):"");
 $("up_notiz").innerHTML=l&&l.verfuegbar&&l.notiz?'<h3>Was ist neu in '+esc(l.neu)+'</h3><pre class="json" style="white-space:pre-wrap;max-height:260px">'+esc(l.notiz)+"</pre>":"";
 $("up_los").hidden=!(l&&l.verfuegbar)||d.laeuft;if(l)$("up_los").textContent="Jetzt aktualisieren auf "+l.neu;
 $("up_schritte").innerHTML=d.schritte&&d.schritte.length?"<table><tr><th></th><th>Schritt</th><th>Ergebnis</th></tr>"+d.schritte.map(s=>`<tr class="${s.status=="fehler"?"falsch":s.status=="läuft"?"geaendert":""}"><td>${UPICON[s.status]||""}</td><td>${esc(s.name)}</td><td>${esc(s.text)}</td></tr>`).join("")+"</table>":"";
 const e=d.einstellungen;if(document.activeElement==null||!document.activeElement.closest||!document.activeElement.closest("#up_karte details")){
  $("up_kanal").value=e.kanal.startsWith("branch:")?"branch":e.kanal;$("up_zweig").value=e.kanal.startsWith("branch:")?e.kanal.slice(7):"";$("up_std").value=e.stunden;$("up_auto").checked=e.automatisch}
 $("up_zurueck").disabled=!a.ordner;if(d.abgeschlossen&&!$("log_up").textContent)$("log_up").textContent=d.abgeschlossen;
 $("up_versionen").innerHTML=d.versionen.length?"<table><tr><th>Ordner in updates/</th><th>Version</th><th></th></tr>"+d.versionen.map(v=>`<tr><td class="mono">${esc(v.ordner)}</td><td>${esc(v.version)}</td><td>${v.ordner==a.ordner?"aktiv":""}</td></tr>`).join("")+"</table>":"";
 const c=$("up_chip");if(c){c.hidden=!(l&&l.verfuegbar);if(l)c.textContent="⬆ Update "+l.neu}
 clearTimeout(UPT);if(d.laeuft)UPT=setTimeout(()=>upLaden(true).catch(()=>upWarten(l?l.neu:"")),1000);else if(d.fertig)upWarten(l?l.neu:"")}
async function upPruefen(){upZeigen(await api("/api/update-pruefen",{},"log_up"))}
async function upInstallieren(){const l=UP&&UP.lage;if(!l)return;if(!confirm("Auf Version "+l.neu+" aktualisieren? Der Manager sichert die Daten, lädt die neue Version und startet neu (ca. 10–30 Sekunden)."))return;
 upZeigen(await api("/api/update-installieren",{sha:l.sha},"log_up"))}
async function upEinstellungen(){const k=$("up_kanal").value=="branch"?"branch:"+$("up_zweig").value.trim():$("up_kanal").value;upZeigen(await api("/api/update-einstellungen",{kanal:k,stunden:$("up_std").value.trim()||"0",automatisch:$("up_auto").checked},"log_up"))}
async function upZurueck(){if(!confirm("Zur vorherigen Version zurück? Der Manager startet neu."))return;const d=await api("/api/update-zurueck",{},"log_up");if(d.neustart)upWarten("")}
let UPW=false;function upWarten(ziel){if(UPW)return;UPW=true;$("log_up").textContent="Neustart … die Seite lädt automatisch neu, sobald der Manager wieder läuft.";let n=0;
 const t=setInterval(async()=>{n++;try{const r=await fetch("/status",{cache:"no-store"});const s=await r.json();if(!s.wartung&&(s.version!=UP.version||n>20)){clearInterval(t);location.reload()}}catch(e){}if(n>90){clearInterval(t);$("log_up").textContent="Der Manager antwortet nicht – bitte Container-Log prüfen und die Seite neu laden."}},2000)}

function gvZeigen(){const d=GP;if(!d)return;const sel=$("gv_st"),alt=sel.value;
 sel.innerHTML=d.standorte.map(s=>`<option value="${s.nr}">${esc(s.name)} · ${s.gw} Gateway${s.gw!=1?"s":""}</option>`).join("");if(d.standorte.some(s=>String(s.nr)==alt))sel.value=alt;
 const st=d.standorte.find(s=>String(s.nr)==sel.value);if(!st){$("gv_tab").innerHTML="";return}const schreiben=ICH.admin||ICH.bereiche.planung=="schreiben";
 $("gv_tab").innerHTML="<table><tr><th>Gateway</th><th>Sparte (Block)</th><th>Parzellen</th><th>VLANs Parzellen</th><th>Dienstnetze Vorstand / Gäste / Technik</th><th>VLANs am Gateway</th><th></th></tr>"+
  st.gateways.map(g=>g.teile.map((t,i)=>`<tr class="${g.ok?"":"falsch"}">${i==0?`<td rowspan="${g.teile.length}"><b>GW ${g.gw}</b></td>`:""}<td>${esc(t.name)} <span class="mono">${esc(t.kz)}</span> (${t.block})</td><td>${t.p_von}–${t.p_bis}</td><td class="mono">${t.vlan_von}–${t.vlan_bis}</td><td class="mono">${t.dienst?t.vlan_d.vorstand+" / "+t.vlan_d.gaeste+" / "+t.vlan_d.technik:"–"}</td>
  ${i==0?`<td rowspan="${g.teile.length}">${g.vlans} <small>(${g.parzellen} + ${g.dienstnetze})</small></td><td rowspan="${g.teile.length}">${schreiben?`<button class="k" onclick="gvUebernehmen(${st.nr},${g.gw})">In Planung übernehmen</button>`:""}</td>`:""}</tr>`).join("")).join("")+"</table>"}
async function gvUebernehmen(st,gw){const s=GP.standorte.find(x=>x.nr==st);if(!confirm("Gateway "+gw+" am Standort „"+s.name+"“ als Planung übernehmen? Die bisherige Planung (Reiter „Planung“) wird ersetzt und gesichert. Am Gateway ändert sich noch nichts – das geht erst über Abgleich/Einrichten mit Vorschau."))return;
 await api("/api/gwplan-vlan-uebernehmen",{standort:st,gw:gw},"log_gv");PLAN=null;planLaden(true)}
function gvCsv(){if(!GP)return;const st=GP.standorte.find(s=>String(s.nr)==$("gv_st").value);if(!st)return;const z=[];
 for(const g of st.gateways)for(const t of g.teile){for(let p=t.p_von;p<=t.p_bis;p++)z.push({gw:g.gw,kz:t.kz,sparte:t.name,netz:t.kz+"-Paz."+String(p).padStart(3,"0"),vlan:1000+200*(t.block-1)+p,subnetz:"10."+t.nr+"."+p+".0/24",art:"Parzelle "+p});
  if(t.dienst)[["Vorstand","vorstand",200],["Gäste","gaeste",201],["Technik","technik",250]].forEach(([n,k,x])=>z.push({gw:g.gw,kz:t.kz,sparte:t.name,netz:t.kz+"-"+n,vlan:t.vlan_d[k],subnetz:"10."+t.nr+"."+x+".0/24",art:n}))}
 csvSpeichern({spalten:[["gw","Gateway"],["kz","Kürzel"],["sparte","Sparte"],["netz","Netz"],["vlan","VLAN"],["subnetz","Subnetz"],["art","Art"]],zeilen:z},"VLAN_Plan_"+st.name)}

let AU=null,AUE=null;
const auDarf=()=>ICH.admin||ICH.bereiche.automationen=="schreiben";
function auAktText(a){if(a.typ=="email")return"E-Mail an "+(a.an||"")+(a.an_kunde?(a.an?" + ":"")+"Kunde":"")+": „"+a.betreff+"“";if(a.typ=="buchen")return"Tarif buchen: "+a.tarif;if(a.typ=="webhook")return"Webhook "+a.url;if(a.typ=="protokoll")return"Protokoll: "+a.text;return AU.aktionen[a.typ]}
async function auLaden(){const d=await api("/api/automation",undefined,"log_au");AU=d;document.querySelectorAll(".au-schreib").forEach(e=>{if(e.id!="au_edit")e.hidden=!auDarf()});
 $("au_st").textContent=d.regeln.filter(r=>r.aktiv).length+" aktiv"+(d.warteschlange?" · "+d.warteschlange+" in Warteschlange":"");
 $("au_tab").innerHTML=d.regeln.length?"<table><tr><th>Regel</th><th>Wenn</th><th>Nur wenn</th><th>Dann</th><th>zuletzt</th><th></th></tr>"+d.regeln.map(r=>{const b=r.bedingung||{};const bed=[b.sparte&&"Sparte "+b.sparte,b.tarif&&"Tarif "+b.tarif,b.betrag_min!=null&&"Betrag ≥ "+b.betrag_min+" €"].filter(Boolean).join(", ")||"immer";
  return`<tr${r.aktiv?"":' style="opacity:.55"'}><td><b>${esc(r.name)}</b>${r.aktiv?"":" (aus)"}</td><td>${esc(d.ausloeser[r.ausloeser])}${r.ereignis_name?" „"+esc(r.ereignis_name)+"“":""}</td><td>${esc(bed)}</td><td>${r.aktionen.map(a=>esc(auAktText(a))).join("<br>")}</td><td>${esc(r.zuletzt||"–")}</td>
  <td style="white-space:nowrap">${auDarf()?`<button class="k" data-id="${esc(r.id)}" onclick="auBearbeiten(this.dataset.id)">Bearbeiten</button> <button class="k" data-id="${esc(r.id)}" onclick="auLoeschen(this.dataset.id)">Löschen</button>`:""}</td></tr>`}).join("")+"</table>":'<p class="hint" style="padding:12px">Noch keine Regel. Beispiel: „Wenn eine Parzelle bucht → E-Mail an den Vorstand“.</p>';
 $("au_verlauf").innerHTML=d.verlauf.length?"<table><tr><th>Zeit</th><th>Regel</th><th>Aktion</th><th>Ergebnis</th></tr>"+d.verlauf.map(v=>`<tr><td style="white-space:nowrap">${esc(v.zeit)}</td><td>${esc(v.regel)}</td><td>${esc(v.aktion)}</td><td>${v.ok?"✔ ":'<span class="fehler">✖ </span>'}${esc(v.text)}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Noch nichts ausgeführt.</p>';
 if(d.smtp){$("sm_host").value=d.smtp.host;$("sm_port").value=d.smtp.port;$("sm_sich").value=d.smtp.sicherheit;$("sm_ben").value=d.smtp.benutzer;$("sm_abs").value=d.smtp.absender;$("sm_absn").value=d.smtp.absender_name;
  $("sm_pw").placeholder=d.smtp.passwort_aus_datei?"aus Docker-Secret":(d.smtp.passwort_gesetzt?"gespeichert – leer lassen = unverändert":"");$("sm_pw").disabled=d.smtp.passwort_aus_datei}
 if(ICH.admin)apiLaden().catch(()=>{})}
function auSparten(){return[...new Set((GP?GP.zeilen.map(z=>z.kz):[]).concat(PLAN?PLAN.sparten.map(s=>s.kz):[]))].sort()}
function auNeu(){auBearbeiten(null)}
function auBearbeiten(id){const r=id?AU.regeln.find(x=>x.id==id):{name:"",ausloeser:"buchung",aktiv:true,bedingung:{},aktionen:[{typ:"email",an:"",an_kunde:false,betreff:"Neue Buchung: {sparte} Parzelle {parzelle}",text:"Hallo,\n\nin der Sparte {sparte_name} hat Parzelle {parzelle} den Tarif {tarif} gebucht ({preis} im Jahr).\n\nSparteNet Manager, {datum} {zeit}"}]};
 AUE=JSON.parse(JSON.stringify(r));$("au_edit_t").textContent=id?"Regel bearbeiten":"Neue Regel";$("au_name").value=r.name;$("au_aktiv").checked=r.aktiv!==false;
 $("au_aus").innerHTML=Object.entries(AU.ausloeser).map(([k,t])=>`<option value="${k}">${esc(t)}</option>`).join("");$("au_aus").value=r.ausloeser;$("au_evn").value=r.ereignis_name||"";
 const b=r.bedingung||{};$("au_b_sp").innerHTML='<option value="">alle Sparten</option>'+auSparten().map(k=>`<option value="${esc(k)}">${esc(k)}</option>`).join("");$("au_b_sp").value=b.sparte||"";
 $("au_b_tf").innerHTML='<option value="">alle Tarife</option>'+AU.tarife.map(t=>`<option value="${esc(t)}">${esc(t)}</option>`).join("");$("au_b_tf").value=b.tarif||"";$("au_b_bt").value=b.betrag_min??"";
 $("au_neu_typ").innerHTML=Object.entries(AU.aktionen).map(([k,t])=>`<option value="${k}">${esc(t)}</option>`).join("");
 $("au_ph").innerHTML="<table><tr><th>Platzhalter</th><th>wird ersetzt durch</th></tr>"+Object.entries(AU.platzhalter).map(([k,t])=>`<tr><td class="mono">${esc(k)}</td><td>${esc(t)}</td></tr>`).join("")+"</table>";
 auAusWechsel();auAktZeigen();$("log_aue").textContent="";$("au_edit").hidden=false;$("au_edit").scrollIntoView({behavior:"smooth",block:"start"})}
function auAusWechsel(){$("au_evn_w").hidden=$("au_aus").value!="api"}
function auFeld(i,f,wert,label,art){const id="au_a"+i+"_"+f;if(art=="area")return`<div style="grid-column:1/-1"><label for="${id}">${label}</label><textarea id="${id}" data-i="${i}" data-f="${f}" rows="6" class="au_f" style="width:100%;font:inherit">${esc(wert)}</textarea></div>`;
 if(art=="check")return`<div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="${id}" data-i="${i}" data-f="${f}" class="au_f" style="width:auto"${wert?" checked":""}> ${label}</label></div>`;
 if(art=="tarif")return`<div><label for="${id}">${label}</label><select id="${id}" data-i="${i}" data-f="${f}" class="au_f"><option value="{tarif}"${wert=="{tarif}"?" selected":""}>Tarif aus dem Ereignis</option>${AU.tarife.map(t=>`<option${t==wert?" selected":""}>${esc(t)}</option>`).join("")}</select></div>`;
 return`<div><label for="${id}">${label}</label><input id="${id}" data-i="${i}" data-f="${f}" class="au_f" value="${esc(wert)}"></div>`}
function auAktZeigen(){$("au_akt").innerHTML=AUE.aktionen.map((a,i)=>`<div class="karte" style="margin:8px 0;padding:12px;background:var(--bg2,#f7f9f5)"><div style="display:flex;gap:8px;align-items:center"><b style="flex:1">${i+1}. ${esc(AU.aktionen[a.typ])}</b><button class="k" onclick="auAktWeg(${i})">Entfernen</button></div>
 <div class="reihe">${a.typ=="email"?auFeld(i,"an",a.an||"","Empfänger (Komma-getrennt)")+auFeld(i,"an_kunde",a.an_kunde,"zusätzlich an den Kunden ({email} aus dem Ereignis)","check")+auFeld(i,"betreff",a.betreff||"","Betreff")+auFeld(i,"text",a.text||"","Text","area")
  :a.typ=="buchen"?auFeld(i,"tarif",a.tarif||"{tarif}","Tarif","tarif")+'<div class="hint" style="grid-column:1/-1">Bucht im Manager (Kalkulation/Tarife). Ans Gateway geht das erst über „Tarife → An das Gateway übertragen“.</div>'
  :a.typ=="webhook"?auFeld(i,"url",a.url||"","Adresse (https://…)")+'<div class="hint" style="grid-column:1/-1">POST mit JSON: {"ereignis", "daten", "regel", "zeit"} – ohne WLAN-Passwort.</div>'
  :a.typ=="protokoll"?auFeld(i,"text",a.text||"","Text"):'<div class="hint">Entfernt die Buchung der Parzelle aus dem Ereignis (nur im Manager).</div>'}</div></div>`).join("")||'<p class="hint">Noch keine Aktion.</p>';
 document.querySelectorAll(".au_f").forEach(e=>e.oninput=e.onchange=()=>{AUE.aktionen[+e.dataset.i][e.dataset.f]=e.type=="checkbox"?e.checked:e.value})}
function auAktNeu(){}
function auAktionNeu(){const t=$("au_neu_typ").value;AUE.aktionen.push(t=="email"?{typ:t,an:"",an_kunde:false,betreff:"",text:""}:t=="buchen"?{typ:t,tarif:"{tarif}"}:t=="webhook"?{typ:t,url:""}:t=="protokoll"?{typ:t,text:""}:{typ:t});auAktZeigen()}
function auAktWeg(i){AUE.aktionen.splice(i,1);auAktZeigen()}
function auRegel(){return{...AUE,name:$("au_name").value,aktiv:$("au_aktiv").checked,ausloeser:$("au_aus").value,ereignis_name:$("au_evn").value,bedingung:{sparte:$("au_b_sp").value,tarif:$("au_b_tf").value,betrag_min:$("au_b_bt").value}}}
async function auSpeichern(){const r=auRegel();const d=await api("/api/automation-speichern",{regel:r},"log_aue");$("au_edit").hidden=true;await auLaden();$("log_au").textContent=d.log.join("\n")}
async function auProbe(){const r=auRegel();const d=await api("/api/automation-probe",{ausloeser:r.ausloeser,ereignis_name:r.ereignis_name,sparte:r.bedingung.sparte||auSparten()[0]||"BW",tarif:r.bedingung.tarif||AU.tarife[0],betrag:r.bedingung.betrag_min||"120"},"log_aue");
 $("log_aue").textContent=d.log.join("\n")+(d.ergebnisse.length?"\n"+d.ergebnisse.map(e=>(e.ok?"✔ ":"✖ ")+e.regel+" · "+e.aktion+": "+e.text).join("\n"):"")+"\n(Der Probelauf prüft die gespeicherten Regeln – Änderungen vorher speichern.)"}
async function auLoeschen(id){const r=AU.regeln.find(x=>x.id==id);if(!confirm("Regel „"+(r?r.name:id)+"“ löschen?"))return;await api("/api/automation-loeschen",{id},"log_au");auLaden()}
async function smSpeichern(){await api("/api/smtp-speichern",{host:$("sm_host").value,port:$("sm_port").value,sicherheit:$("sm_sich").value,benutzer:$("sm_ben").value,passwort:$("sm_pw").value,absender:$("sm_abs").value,absender_name:$("sm_absn").value},"log_sm");$("sm_pw").value="";auLaden()}
async function smTest(){await api("/api/smtp-test",{an:$("sm_test_an").value},"log_sm")}
let APIK=null;
async function apiLaden(){const d=await api("/api/api-schluessel",undefined,"log_api");APIK=d;$("api_min").textContent=d.pro_minute;
 if(!$("api_rechte").innerHTML)$("api_rechte").innerHTML=Object.entries(d.rechte).map(([k,t])=>`<label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" class="api_r" value="${k}" style="width:auto"${k=="ereignis"?" checked":""}> ${esc(t)}</label>`).join("");
 $("api_tab").innerHTML=d.schluessel.length?"<table><tr><th>Name</th><th>Schlüssel</th><th>Rechte</th><th>Sparten</th><th>angelegt</th><th>zuletzt benutzt</th><th></th></tr>"+d.schluessel.map(s=>`<tr${s.aktiv?"":' style="opacity:.55"'}><td><b>${esc(s.name)}</b>${s.aktiv?"":" (deaktiviert)"}</td><td class="mono">sn_${esc(s.id)}_…</td><td>${esc((s.rechte||[]).join(", "))}</td><td>${esc((s.sparten||[]).join(", ")||"alle")}</td>
  <td>${esc(s.angelegt)}<br><small>${esc(s.von)}</small></td><td>${esc(s.zuletzt||"–")}${s.anfragen?"<br><small>"+s.anfragen+" Anfragen</small>":""}</td><td style="white-space:nowrap"><button class="k" data-id="${esc(s.id)}" data-a="${s.aktiv?0:1}" onclick="apiAendern(this.dataset.id,{aktiv:this.dataset.a=='1'})">${s.aktiv?"Deaktivieren":"Aktivieren"}</button> <button class="k" data-id="${esc(s.id)}" onclick="if(confirm('Schlüssel endgültig löschen? Programme, die ihn benutzen, bekommen dann keinen Zugriff mehr.'))apiAendern(this.dataset.id,{loeschen:true})">Löschen</button></td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Noch kein API-Schlüssel.</p>';
 const o=location.origin;$("api_bsp").textContent=`# Verbindung testen
curl -H "Authorization: Bearer sn_…" ${o}/api/v1/status

# Zahlung eingegangen → startet die Automationen mit Auslöser „Zahlung eingegangen“
curl -X POST -H "Authorization: Bearer sn_…" -H "Content-Type: application/json" \\
  -d '{"ereignis":"zahlung","sparte":"BW","parzelle":12,"betrag":"120.00","referenz":"RE-2026-0042","email":"paechter@example.de","name":"Max Mustermann","tarif":"Basic"}' \\
  ${o}/api/v1/ereignis

# Eigenes Ereignis (Auslöser „Eigenes Ereignis über die API“, Name „mahnung“)
curl -X POST -H "Authorization: Bearer sn_…" -H "Content-Type: application/json" -d '{"ereignis":"mahnung","sparte":"BW","parzelle":12}' ${o}/api/v1/ereignis

# Tarif buchen ("tarif":"" entfernt die Buchung) – löst die Automationen „Buchung“ bzw. „Kündigung“ aus
curl -X POST -H "Authorization: Bearer sn_…" -H "Content-Type: application/json" -d '{"sparte":"BW","parzelle":12,"tarif":"Basic"}' ${o}/api/v1/buchung

# Buchungen und Tarife lesen
curl -H "Authorization: Bearer sn_…" "${o}/api/v1/buchungen?sparte=BW"
curl -H "Authorization: Bearer sn_…" ${o}/api/v1/tarife`}
async function apiNeu(){const rechte=[...document.querySelectorAll(".api_r:checked")].map(e=>e.value);const sparten=$("api_sp").value.split(/[,;\s]+/).filter(Boolean);
 const d=await api("/api/api-schluessel-neu",{name:$("api_name").value,rechte,sparten},"log_api");$("api_name").value="";$("api_sp").value="";
 $("api_neu").hidden=false;$("api_neu").innerHTML='<b>Neuer API-Schlüssel – jetzt kopieren, er wird nicht noch einmal angezeigt:</b><br><span class="mono" id="api_neu_k" style="user-select:all;overflow-wrap:anywhere"></span> <button class="k" onclick="navigator.clipboard&&navigator.clipboard.writeText($(\'api_neu_k\').textContent).then(()=>this.textContent=\'Kopiert ✔\')">Kopieren</button>';
 $("api_neu_k").textContent=d.neu;await apiLaden();$("log_api").textContent=d.log.join("\n")}
async function apiAendern(id,x){await api("/api/api-schluessel-aendern",{id,...x},"log_api");$("api_neu").hidden=true;apiLaden()}

function parzText(s){const l=s.parzellen||(s.p_von?Array.from({length:s.p_bis-s.p_von+1},(_,i)=>s.p_von+i):[]);if(!l.length)return"keine";const r=[];let a=l[0],b=l[0];
 for(const x of l.slice(1).concat([null])){if(x===b+1){b=x;continue}r.push(a==b?String(a):a+"–"+b);a=b=x}return r.join(", ")}
let ZT=null,ZG=null;
async function ztLaden(){const d=await api("/api/zuteilung",undefined,"log_zt");ZT=d;$("zt_an").checked=d.an;$("zt_pg").textContent=d.pg;
 const darf=ICH.admin||(ICH.bereiche.netzplanung=="schreiben"&&!ICH.sparten);document.querySelectorAll(".zt-schreib").forEach(e=>e.hidden=!darf);
 $("zt_st").textContent=d.an?"eingeschaltet"+(d.seit?" seit "+d.seit:""):"aus";$("zt_st").className="status"+(d.an?" ok":"");
 const sel=$("zt_stf"),alt=sel.value;sel.innerHTML=d.standorte.map(s=>`<option value="${s.nr}">${esc(s.name)} · ${s.gebucht} zugeteilt · ${s.gw_geplant} Gateway${s.gw_geplant!=1?"s":""} geplant</option>`).join("");if(d.standorte.some(s=>String(s.nr)==alt))sel.value=alt;ztZeigen()}
function ztZeigen(){const d=ZT;if(!d)return;const st=d.standorte.find(s=>String(s.nr)==$("zt_stf").value);if(!st){$("zt_tab").innerHTML="";return}
 const darf=ICH.admin||ICH.bereiche.planung=="schreiben",farbe={anlegen:"#b26b00",aktiv:"",entfernen:"#b00020"};
 $("zt_tab").innerHTML="<table><tr><th>Gateway</th><th>belegt</th><th>VLANs</th><th>Parzellen (VLAN)</th><th></th></tr>"+st.gateways.map(g=>`<tr><td><b>GW ${g.gw}</b>${g.geplant?"":" <small>(nicht geplant)</small>"}</td><td>${g.belegt} / ${d.pg}${g.anlegen?`<br><small style="color:${farbe.anlegen}">${g.anlegen} anzulegen</small>`:""}${g.entfernen?`<br><small style="color:${farbe.entfernen}">${g.entfernen} zu entfernen</small>`:""}</td>
  <td>${g.vlans}<br><small>${g.belegt} + ${g.dienstnetze} Dienst</small></td><td>${g.sparten.map(s=>`<b class="mono">${esc(s.kz)}</b> ${s.parzellen.map(x=>`<span title="${esc(d.status_text[x.status])} · VLAN ${x.vlan}" style="${farbe[x.status]?"color:"+farbe[x.status]+";font-weight:600":""}${x.status=="entfernen"?";text-decoration:line-through":""}">${x.p}</span>`).join(", ")}`).join("<br>")||'<span class="hint">frei</span>'}</td>
  <td>${darf&&d.an&&(g.belegt||g.gw==1)?`<button class="k" onclick="ztUebernehmen(${st.nr},${g.gw})">${d.aktiv_gateway.standort==st.nr&&d.aktiv_gateway.gw==g.gw&&d.aktiv_gateway.dynamisch?"✔ aktive Planung":"Als Planung übernehmen"}</button>`:""}</td></tr>`).join("")+"</table>"+
  '<p class="hint" style="padding:6px 10px">Orange = gebucht, Netz noch anzulegen · rot durchgestrichen = Buchung gelöscht, Netz noch am Gateway · Maus über die Nummer zeigt die VLAN-ID.</p>'}
async function ztSchalten(){const an=$("zt_an").checked;if(an&&!confirm("Gateway-Zuteilung nach Buchung einschalten?\n\nAlle gebuchten Parzellen werden einem Gateway zugeteilt – vorhandene bevorzugt dort, wo sie laut Netzplanung schon liegen. Neue Buchungen füllen danach immer zuerst das erste Gateway. Am Gateway ändert sich dadurch nichts.")){$("zt_an").checked=false;return}
 try{ZT=await api("/api/zuteilung-einstellen",{an},"log_zt");ztLaden().then(()=>$("log_zt").textContent=ZT.log.join("\n"));PLAN=null;planLaden(true)}catch(e){$("zt_an").checked=!an}}
async function ztAbgleichen(){const d=await api("/api/zuteilung-einstellen",{abgleichen:true},"log_zt");await ztLaden();$("log_zt").textContent=d.log.join("\n");PLAN=null;planLaden(true)}
async function ztUebernehmen(st,gw){const s=ZT.standorte.find(x=>x.nr==st);if(!confirm("Gateway "+gw+" am Standort „"+s.name+"“ als Planung übernehmen? Danach unter „Verbindung“ die Konsole dieses Gateways wählen. Am Gateway ändert sich noch nichts."))return;
 await api("/api/gwplan-vlan-uebernehmen",{standort:st,gw:gw},"log_zt");PLAN=null;await planLaden(true);ztLaden()}
function zgKarte(){const k=$("zg_karte");if(!k||!PLAN)return;const r=PLAN.roh||{};k.hidden=!(r.dynamisch);if(r.dynamisch)$("zg_hint").innerHTML=`Aktive Planung: <b>${esc(r.gatewayname||"")}</b>. „Vorschau“ vergleicht die Zuteilung mit den Netzen am Gateway: gebuchte Parzellen ohne Netz werden angelegt (mit Passwort ins Pächter-WLAN, falls schon vorhanden), Netze gelöschter Buchungen werden entfernt – vorher werden ihre Zugänge im WLAN gelöscht (mit Sicherung). Nur ausgewählte Zeilen werden ausgeführt.`}
async function zgVorschau(){const d=await api("/api/zuteilung-gateway",{},"log_zg");ZG=d;const zeile=(x,art,an)=>`<tr><td><input type="checkbox" class="zg_w" data-art="${art}" value="${esc(x.netz)}" style="width:auto"${an?" checked":""}></td><td>${art=="anlegen"?"anlegen":"entfernen"}</td><td class="mono">${esc(x.netz)}</td><td class="mono">${esc(x.vlan??"")}</td><td>${esc(x.grund||"gebucht")}</td></tr>`;
 const z=d.anlegen.map(x=>zeile(x,"anlegen",true)).concat(d.entfernen.map(x=>zeile(x,"entfernen",true))).concat(d.ueberzaehlig.map(x=>zeile(x,"entfernen",false)));
 $("zg_tab").innerHTML=z.length?"<table><tr><th></th><th>Aktion</th><th>Netz</th><th>VLAN</th><th>Grund</th></tr>"+z.join("")+"</table>"+(d.ueberzaehlig.length?'<p class="hint" style="padding:6px 10px">Nicht vorausgewählt: Parzellennetze am Gateway, die diesem Gateway nicht zugeteilt sind (z. B. noch aus der festen Aufteilung). Nur auswählen, wenn sie wirklich weg sollen.</p>':""):'<p class="hint" style="padding:10px">Alles aktuell – nichts zu tun.</p>';
 $("zg_los").disabled=!z.length}
async function zgAusfuehren(){const w=[...document.querySelectorAll(".zg_w:checked")];const an=w.filter(e=>e.dataset.art=="anlegen").map(e=>e.value),weg=w.filter(e=>e.dataset.art=="entfernen").map(e=>e.value);
 if(!an.length&&!weg.length)return $("log_zg").textContent="Nichts ausgewählt.";
 if(!confirm(`Am Gateway jetzt ausführen?\n\n${an.length} Netz(e) anlegen${an.length?": "+an.slice(0,8).join(", ")+(an.length>8?" …":""):""}\n${weg.length} Netz(e) entfernen${weg.length?": "+weg.slice(0,8).join(", ")+(weg.length>8?" …":""):""}\n\nVorher eine Sicherung der Konsole machen.`))return;
 await api("/api/zuteilung-gateway",{ausfuehren:true,anlegen:an,entfernen:weg},"log_zg");$("zg_los").disabled=true;$("zg_tab").innerHTML="";if(ZT)ztLaden().catch(()=>{})}

const FARBEN={system:["◐","wie das System"],hell:["☀","hell"],dunkel:["☾","dunkel"]};
function farbeLesen(){try{return localStorage.getItem("sn_farbe")||"system"}catch(e){return"system"}}
function farbeSetzen(f){if(!FARBEN[f])f="system";try{localStorage.setItem("sn_farbe",f)}catch(e){}if(f=="system")delete document.documentElement.dataset.farbe;else document.documentElement.dataset.farbe=f;farbeZeigen()}
function farbeZeigen(){const f=farbeLesen(),k=$("farbe_k");if(k){k.textContent=FARBEN[f][0];k.title="Farbschema: "+FARBEN[f][1]+" (klicken zum Wechseln)"}if($("an_farbe"))$("an_farbe").value=f;
 const dunkel=f=="dunkel"||(f=="system"&&matchMedia("(prefers-color-scheme: dark)").matches);const m=document.querySelector('meta[name=theme-color]');if(m)m.content=dunkel?"#0b1218":"#1d2f3e"}
function farbeWechseln(){const r=["system","hell","dunkel"];farbeSetzen(r[(r.indexOf(farbeLesen())+1)%3])}
try{matchMedia("(prefers-color-scheme: dark)").addEventListener("change",farbeZeigen)}catch(e){}

let UM=null;
async function umVorschau(){const d=await api("/api/umzug",{},"log_um");UM=d;
 $("um_tab").innerHTML=d.zeilen.length?'<table><tr><th><input type="checkbox" id="um_alle" checked style="width:auto" onchange="document.querySelectorAll(\'.um_w:not(:disabled)\').forEach(e=>e.checked=this.checked)"></th><th>Netz</th><th>VLAN alt → neu</th><th>Subnetz alt → neu</th><th>Änderung</th></tr>'+d.zeilen.map(z=>`<tr${z.blockiert?' class="falsch"':""}><td><input type="checkbox" class="um_w" value="${esc(z.id)}" style="width:auto"${z.blockiert?"":" checked"}></td><td class="mono">${esc(z.netz)}</td><td class="mono">${esc(z.vlan_alt||"–")} → ${esc(z.vlan_neu)}</td><td class="mono">${esc(z.subnetz_alt)} → ${esc(z.subnetz_neu)}</td><td>${esc(z.text)}${z.blockiert?'<br><small class="fehler" style="color:var(--red)">'+esc(z.blockiert)+"</small>":""}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Nichts umzustellen – alle vorhandenen Netze passen zur Planung.</p>';
 $("um_los").disabled=$("um_eins").disabled=!d.zeilen.length}
async function umAusfuehren(eins){const w=[...document.querySelectorAll(".um_w:checked")].map(e=>e.value);if(!w.length)return $("log_um").textContent="Nichts ausgewählt.";
 if(!confirm((eins?"Nur das erste ausgewählte Netz":w.length+" Netz(e)")+" jetzt am Gateway umstellen?\n\nGeräte in diesen Netzen verlieren kurz die Verbindung und bekommen eine neue IP. Vorher eine Sicherung der Konsole machen. Der Manager sichert den alten Stand für „Umzug rückgängig“."))return;
 await api("/api/umzug",{ausfuehren:true,netze:w,nur_eins:eins},"log_um");$("um_los").disabled=$("um_eins").disabled=true;$("um_tab").innerHTML=""}
async function umZurueck(){if(!confirm("Letzten Umzug rückgängig machen? Die Netze bekommen VLAN, Subnetz und DHCP-Bereich von vorher zurück."))return;await api("/api/umzug-rueckgaengig",{},"log_um")}

let UL=null;
async function ulLaden(){const d=await api("/api/unterlagen",undefined,"log_ul");UL=d;
 const sp=(d.sparten_erlaubt||[...new Set((GP?GP.zeilen.map(z=>z.kz):[]).concat(PLAN?PLAN.sparten.map(s=>s.kz):[]))].sort());
 $("ul_sparte").innerHTML=(d.sparten_erlaubt?"":'<option value="">Allgemein (alle Sparten)</option>')+sp.map(k=>`<option value="${esc(k)}">${esc(k)}</option>`).join("");
 $("ul_ordnerliste").innerHTML=d.ordner.map(o=>`<option value="${esc(o)}">`).join("");
 const fo=$("ul_f_ordner").value,fs=$("ul_f_sparte").value;
 $("ul_f_ordner").innerHTML='<option value="">alle Ordner</option>'+d.ordner.map(o=>`<option value="${esc(o)}">${esc(o)}</option>`).join("");$("ul_f_ordner").value=fo;
 const ds=[...new Set(d.dateien.map(x=>x.sparte||""))].sort();$("ul_f_sparte").innerHTML='<option value="*">alle</option>'+ds.map(k=>`<option value="${esc(k)}">${k?esc(k):"Allgemein"}</option>`).join("");if([...$("ul_f_sparte").options].some(o=>o.value==fs))$("ul_f_sparte").value=fs;
 $("ul_st").textContent=d.belegt_mb+" / "+d.gesamt_mb+" MB";ulZeigen()}
const groesse=b=>b>=1e6?(b/1e6).toLocaleString("de-DE",{maximumFractionDigits:1})+" MB":Math.max(1,Math.round(b/1e3))+" KB";
function ulZeigen(){const d=UL;if(!d)return;const q=$("ul_such").value.trim().toLowerCase(),fo=$("ul_f_ordner").value,fs=$("ul_f_sparte").value;
 const L=d.dateien.filter(x=>(!q||(x.name+" "+(x.beschreibung||"")).toLowerCase().includes(q))&&(!fo||x.ordner==fo)&&(fs=="*"||!fs&&fs!==""||(x.sparte||"")==fs));
 const darf=ICH.admin||ICH.bereiche.unterlagen=="schreiben";
 $("ul_tab").innerHTML=L.length?"<table><tr><th>Name</th><th>Ordner</th><th>Sparte</th><th>Größe</th><th>hochgeladen</th><th>Beschreibung</th><th></th></tr>"+L.map(x=>`<tr><td><b>${esc(x.name)}</b></td>
  <td>${darf&&x.schreiben?`<input class="ul_in" data-id="${x.id}" data-f="ordner" value="${esc(x.ordner)}" list="ul_ordnerliste" style="min-width:120px">`:esc(x.ordner)}</td><td>${x.sparte?esc(x.sparte):"Allgemein"}</td><td>${groesse(x.groesse)}</td>
  <td>${esc(x.zeit)}<br><small>${esc(x.von)}</small></td><td>${darf&&x.schreiben?`<input class="ul_in" data-id="${x.id}" data-f="beschreibung" value="${esc(x.beschreibung||"")}" style="min-width:200px">`:esc(x.beschreibung||"")}</td>
  <td style="white-space:nowrap">${x.ansehen?`<button class="k" onclick="ulDatei('${x.id}',true)">Ansehen</button> `:""}<button class="k" onclick="ulDatei('${x.id}',false)">Herunterladen</button>${darf&&x.schreiben?` <button class="k" onclick="ulLoeschen('${x.id}')">Löschen</button>`:""}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:12px">Keine Unterlagen'+(q||fo?" für diesen Filter":"")+".</p>";
 document.querySelectorAll(".ul_in").forEach(e=>e.onchange=async()=>{UL=await api("/api/unterlage-aendern",{id:e.dataset.id,[e.dataset.f]:e.value},"log_ul");ulZeigen()})}
async function ulHoch(files){const max=UL?UL.max_datei_mb:15;for(const f of files){if(f.size>max*1e6){$("log_ulh").innerHTML='<span class="fehler">✖ '+esc(f.name)+": größer als "+max+" MB</span>";continue}
  const p=new URLSearchParams({name:f.name,ordner:$("ul_ordner").value||"Allgemein",sparte:$("ul_sparte").value||"",beschreibung:$("ul_beschr").value||""});
  try{UL=await api("/api/unterlage-hochladen?"+p.toString(),f,"log_ulh")}catch(e){}}
 $("ul_datei").value="";$("ul_beschr").value="";if(UL)ulLaden()}
async function ulDatei(id,ansehen){const x=UL.dateien.find(y=>y.id==id);const w=ansehen?window.open("","_blank"):null;
 try{const r=await fetch("/api/unterlage-datei?id="+encodeURIComponent(id),{headers:{"X-Token":T}});if(!r.ok){let m=r.status;try{m=(await r.json()).fehler}catch(e){}throw new Error(m)}
  const b=await r.blob();const u=URL.createObjectURL(b);if(ansehen&&w){w.location=u}else{const a=document.createElement("a");a.href=u;a.download=x?x.name:"Datei";document.body.appendChild(a);a.click();a.remove()}setTimeout(()=>URL.revokeObjectURL(u),60000)}
 catch(e){if(w)w.close();$("log_ul").innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>'}}
async function ulLoeschen(id){const x=UL.dateien.find(y=>y.id==id);if(!confirm("„"+(x?x.name:id)+"“ endgültig löschen?"))return;UL=await api("/api/unterlage-loeschen",{id},"log_ul");ulZeigen()}
(function(){const z=$("ul_zone");if(!z)return;["dragenter","dragover"].forEach(t=>z.addEventListener(t,e=>{e.preventDefault();z.style.borderColor="#3a9a1f"}));["dragleave","drop"].forEach(t=>z.addEventListener(t,e=>{e.preventDefault();z.style.borderColor=""}));z.addEventListener("drop",e=>ulHoch(e.dataTransfer.files))})();

async function siLaden(){const d=await api("/api/sicherung",undefined,"log_si");const e=d.einstellungen;$("si_auto").checked=e.automatisch;$("si_uhr").value=e.uhrzeit;$("si_anz").value=e.anzahl;
 $("si_liste").innerHTML=d.liste.length?"<table><tr><th>Sicherung auf dem Server</th><th>Zeit</th><th>Größe</th><th></th></tr>"+d.liste.map(x=>`<tr><td class="mono">${esc(x.name)}</td><td>${esc(x.zeit)}</td><td>${groesse(x.groesse)}${x.verschluesselt?" · verschlüsselt":""}</td><td><button class="k" onclick="siServerDatei('${esc(x.name)}')">Herunterladen</button></td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Noch keine Sicherung auf dem Server.</p>';
 if(!d.krypto)$("log_si").textContent="Hinweis: Verschlüsselung nicht verfügbar (Paket cryptography fehlt) – Sicherungen nur unverschlüsselt."}
async function siBlob(pfad,body,name){const r=await fetch(pfad,{method:body?"POST":"GET",headers:{"X-Token":T,"Content-Type":"application/json"},body:body?JSON.stringify(body):undefined});
 if(!r.ok){let m=r.status;try{m=(await r.json()).fehler}catch(e){}throw new Error(m)}const cd=r.headers.get("Content-Disposition")||"";const m=/filename\*=UTF-8''([^;]+)/.exec(cd);
 const b=await r.blob(),u=URL.createObjectURL(b),a=document.createElement("a");a.href=u;a.download=m?decodeURIComponent(m[1]):name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),60000)}
async function siHerunterladen(){const p=$("si_pw").value;if(p!==$("si_pw2").value)return $("log_si").innerHTML='<span class="fehler">✖ Die Passwörter stimmen nicht überein.</span>';
 if(!p&&!confirm("Ohne Passwort ist die Sicherung NICHT verschlüsselt (WLAN-Passwörter und Cloud-Key lesbar). Trotzdem herunterladen?"))return;
 $("log_si").textContent="… Sicherung wird erstellt";try{await siBlob("/api/sicherung-erstellen",{passwort:p},"SparteNet_Datensicherung");$("log_si").textContent="✔ Sicherung heruntergeladen"+(p?" (verschlüsselt).":".");$("si_pw").value=$("si_pw2").value=""}catch(e){$("log_si").innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>'}}
async function siServerDatei(n){try{await siBlob("/api/sicherung-datei?name="+encodeURIComponent(n),null,n)}catch(e){$("log_si").innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>'}}
async function siJetzt(){await api("/api/sicherung-jetzt",{},"log_si");siLaden()}
async function siEinstellungen(){await api("/api/sicherung-einstellungen",{automatisch:$("si_auto").checked,uhrzeit:$("si_uhr").value,anzahl:$("si_anz").value},"log_si");siLaden()}
async function siEinspielen(){const f=$("si_datei").files[0];$("si_datei").value="";if(!f)return;if(!confirm("ALLE Daten des Managers durch „"+f.name+"“ ersetzen? Der jetzige Stand wird vorher auf dem Server gesichert."))return;
 $("log_si").textContent="… wird eingespielt";try{const r=await fetch("/api/sicherung-einspielen",{method:"POST",headers:{"X-Token":T,"X-Sicherung-Passwort":encodeURIComponent($("si_ein_pw").value)},body:f});const d=await r.json();if(!r.ok)throw new Error(d.fehler||r.status);
  $("log_si").textContent=d.log.join("\n");$("si_ein_pw").value="";if(d.neu_laden)setTimeout(()=>location.reload(),2500)}catch(e){$("log_si").innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>'}}

function zfZeigen(d){const an=!!d.zwei_faktor;$("bn_2fa").hidden=d.name=="Handy (PIN)";
 $("bn_2fa_st").innerHTML=an?"✔ Eingeschaltet seit "+esc(d.zwei_faktor_seit)+" · noch "+d.notfall_rest+" Notfall-Codes":(d.zwei_faktor_pflicht?'<b style="color:var(--red)">Pflicht für Administratoren – bitte jetzt einrichten.</b>':"Aus. Mit Zwei-Faktor braucht die Anmeldung zusätzlich einen 6-stelligen Code aus einer App auf dem Handy.");
 $("bn_2fa_ein").hidden=an;$("bn_2fa_aus").hidden=!an}
async function zfStart(){const d=await api("/api/2fa-start",{},"log_bni");$("bn_2fa_qr").innerHTML=d.svg;$("bn_2fa_geheim").textContent=d.geheim;$("bn_2fa_neu").hidden=false;$("bn_2fa_notfall").hidden=true;$("bn_2fa_code").focus()}
async function zfBestaetigen(){const d=await api("/api/2fa-bestaetigen",{code:$("bn_2fa_code").value.trim()},"log_bni");$("bn_2fa_neu").hidden=true;$("bn_2fa_code").value="";
 $("bn_2fa_notfall").innerHTML='<p class="hint"><b>Notfall-Codes</b> – jeder funktioniert genau einmal, falls das Handy weg ist. Jetzt ausdrucken oder sicher notieren:</p><pre class="json" style="font-size:16px">'+d.notfall.map(esc).join("\n")+"</pre>";$("bn_2fa_notfall").hidden=false;bnStart()}
async function zfAus(){const c=prompt("Zum Ausschalten den aktuellen Code aus der App (oder einen Notfall-Code) eingeben:");if(!c)return;await api("/api/2fa-aus",{code:c},"log_bni");bnStart()}
async function zfReset(n){if(!confirm("Zwei-Faktor-Anmeldung von „"+n+"“ zurücksetzen? Das Konto wird abgemeldet und muss sie neu einrichten."))return;bnZeigen(await api("/api/2fa-zuruecksetzen",{name:n},"log_bn"))}
async function zfPflicht(an){try{bnZeigen(await api("/api/sicherheit-einstellungen",{"2fa_admin":an},"log_bn"))}catch(e){$("bn_2fa_pflicht").checked=!an}}

let GP=null;
const gz=(v,n=0)=>v==null||v===""?"–":Number(v).toLocaleString("de-DE",{minimumFractionDigits:n,maximumFractionDigits:n});
async function gpLaden(){gpZeigen(await api("/api/gwplan",undefined,"log_gp"))}
function gpZeigen(d){if(!d||!d.gesamt)return;GP=d;const g=d.gesamt,e=g.eigen;
 $("gp_quelle").textContent=d.quelle_daten;$("gp_quelle").className="status"+(d.quelle_daten.startsWith("Excel")?" ok":"");
 $("log_gp").textContent=(d.log||[]).join("\n");
 $("gp_k").innerHTML=kachel("theoretische Einnahmen / Jahr",eur(g.einnahme)+"<small>"+eur(g.einnahme_monat)+" im Monat"+(d.annahmen.KU==1?"":" · netto "+eur(g.einnahme_netto))+"</small>","gut")+
  kachel("Kunden (Buchungsquote)",gz(g.kunden)+"<small>"+pct(g.quote)+" von "+gz(g.parzellen)+" Parzellen</small>","gut")+
  kachel("Ø Preis je Kunde",eur(g.preis,2)+"<small>"+(g.preis_quelle=="tarife"?"nach Tarifmix":"fester Preis")+" · "+eur(g.preis/12,2)+" / Monat</small>","")+
  kachel("Standorte · Gateways · Internet",g.standorte+" · "+g.gateways+" · "+g.anschluesse+"<small>eigenständig: "+e.standorte+" · "+e.gateways+" · "+e.anschluesse+"</small>","")+
  kachel("Investition",eur(g.investition)+"<small>eigenständig "+eur(e.investition)+"</small>","")+
  kachel("laufende Kosten / Jahr",eur(g.laufend)+"<small>eigenständig "+eur(e.laufend)+" · zzgl. Zahlung "+eur(g.zahlung)+"</small>","")+
  kachel("Deckungsbeitrag / Jahr",eur(g.db)+"<small>vor zentralen Firmenkosten</small>",g.db>=0?"gut":"schlecht")+
  kachel("Amortisation",g.amortisation==null?"nie":gz(g.amortisation,1)+" J."+"<small>"+eur(g.inv_kunde)+" je Kunde</small>",g.amortisation!=null&&g.amortisation<=6?"gut":"warn")+
  kachel("Glasfaser zwischen Sparten",gz(g.faser)+" m","")+
  kachel("Prüfung",g.fehler?g.fehler+" Fehler":"OK",g.fehler?"schlecht":"gut")+
  (g.ist_gebucht?kachel("tatsächlich gebucht (Kalkulation)",gz(g.ist_gebucht)+"<small>"+eur(g.ist_einnahme)+" / Jahr</small>","gut"):"");
 const a=d.annahmen;if(document.activeElement==null||!document.activeElement.closest||!document.activeElement.closest("#netzplanung .reihe")){
  $("gp_pq").value=g.preis_quelle;$("gp_qm").value=String(a.Quote_Modus);$("gp_qf").value=String(+(a.Quote_fest*100).toFixed(2)).replace(".",",");$("gp_sz").value=String(a.Szenario);
  $("gp_mix").innerHTML=d.tarife.map(t=>`<div><label>Anteil ${esc(t.name)} (${eur(t.preis)}/Jahr) in %</label><input class="gp_mix" data-t="${esc(t.name)}" value="${String(t.mix).replace(".",",")}" inputmode="decimal"></div>`).join("")}
 let tt="<table><tr><th>Tarif</th><th>Preis / Jahr</th><th>Anteil</th><th>Kunden</th><th>Einnahmen / Jahr</th><th>Einnahmen / Monat</th></tr>";
 if(g.preis_quelle=="tarife"){for(const t of d.tarife){const j=g.je_tarif[t.name]||{kunden:0,einnahme:0};tt+=`<tr><td><b>${esc(t.name)}</b></td><td>${eur(t.preis)}</td><td>${pct(t.anteil)}</td><td>${gz(j.kunden)}</td><td>${eur(j.einnahme)}</td><td>${eur(j.einnahme/12)}</td></tr>`}}
 else tt+=`<tr><td>fester Preis</td><td>${eur(g.preis)}</td><td>100,0 %</td><td>${gz(g.kunden)}</td><td>${eur(g.einnahme)}</td><td>${eur(g.einnahme_monat)}</td></tr>`;
 tt+=`<tr class="kopf"><td>Alle Sparten</td><td>Ø ${eur(g.preis,2)}</td><td></td><td>${gz(g.kunden)}</td><td>${eur(g.einnahme)}</td><td>${eur(g.einnahme_monat)}</td></tr></table>`;$("gp_tt").innerHTML=tt;
 const alt=$("gp_stf").value;$("gp_stf").innerHTML='<option value="">alle Standorte</option>'+d.standorte.map(s=>`<option value="${s.nr}">${esc(s.name)} (${s.sparten} Sparten, ${s.gw} GW)</option>`).join("");if(d.standorte.some(s=>String(s.nr)==alt))$("gp_stf").value=alt;
 gpTabelle();
 $("gp_st").innerHTML="<table><tr><th>Nr.</th><th>Standort</th><th>Sparten (Reihenfolge)</th><th>Parzellen</th><th>Gateways</th><th>Belegung</th><th>Glasfaser­strecken</th><th>Aggregation</th><th>Kunden</th><th>Bedarf Mbit/s</th><th>Internet</th><th>Investition</th><th>laufend / Jahr</th><th>Prüfung</th></tr>"+
  d.standorte.map(s=>`<tr class="${s.pruefung.startsWith("Achtung")?"falsch":""}"><td>${s.nr}</td><td><b>${esc(s.name)}</b></td><td>${s.namen.map(esc).join(" → ")}</td><td>${s.parz}</td><td>${s.gw}</td><td>${balken(s.belegung)}</td><td>${s.straenge}</td><td>${s.agg}</td><td>${gz(s.kunden)}</td><td>${gz(s.bedarf)}</td><td>${s.anschluesse}</td><td>${eur(s.inv)}</td><td>${eur(s.lfd)}</td><td>${esc(s.pruefung)}</td></tr>`).join("")+
  `<tr class="kopf"><td></td><td>${d.standorte.length} Standorte</td><td></td><td>${gz(g.parzellen)}</td><td>${g.gateways}</td><td></td><td></td><td></td><td>${gz(g.kunden)}</td><td></td><td>${g.anschluesse}</td><td></td><td></td><td></td></tr></table>`;
 gvZeigen();gpAnZeigen(d)}
function gpTabelle(){const d=GP;if(!d)return;const box=$("gp_tab"),y=box.scrollTop,x=box.scrollLeft;const such=$("gp_such").value.trim().toLowerCase(),stf=$("gp_stf").value,nurF=$("gp_err").checked;
 const inp=(z,f,wert,ph,w)=>`<input class="gp_in${w?" w":""}" data-nr="${z.nr}" data-f="${f}" value="${wert??""}" placeholder="${ph??""}" inputmode="decimal">`;
 const L=d.zeilen.filter(z=>(!such||z.name.toLowerCase().includes(such)||String(z.nr)==such)&&(!stf||String(z.standort)==stf)&&(!nurF||z.pruefung.startsWith("Fehler")));
 const sum=(k)=>L.reduce((s,z)=>s+(+z[k]||0),0);
 let h="<table><tr><th>Nr.</th><th>Sparte</th><th>Kürzel</th><th>Parzellen</th><th>Standort</th><th>Zuleitung von</th><th>Reihen­folge</th><th>Glasfaser m</th><th>versorgt durch</th><th>VLAN-Block</th><th>VLANs</th><th>Quote %</th><th>Kunden</th><th>Einnahme / Jahr</th><th>Einnahme / Monat</th><th>tatsächlich gebucht</th><th>Investition</th><th>Deckungs­beitrag</th><th>Amorti­sation</th><th>Prüfung</th></tr>";
 for(const z of L){const w=z.w||{};const fe=z.pruefung.startsWith("Fehler");
  h+=`<tr class="${fe?"falsch":z.rolle=="Gateway-Standort"?"dienst":""}"><td>${z.nr}</td><td><b>${esc(z.name)}</b><br><small style="color:var(--muted)">${esc(z.stufe)} · ${esc(z.rolle)}</small></td>
  <td><input class="gp_in" data-nr="${z.nr}" data-f="kz" value="${esc(w.kz||"")}" placeholder="${esc(z.kz)}" style="width:70px;text-transform:uppercase" maxlength="5"></td><td>${inp(z,"parz",w.parz,z.parz)}</td><td>${inp(z,"standort",w.standort,z.standort)}</td><td>${inp(z,"zuleitung",w.zuleitung,z.zuleitung??"")}</td><td>${inp(z,"reihenfolge",w.reihenfolge,"")}</td>
  <td>${inp(z,"entfernung",w.entfernung,z.faser_zul||"",1)}</td><td>${esc(z.versorgt)}</td><td>${inp(z,"vlanblock",w.vlanblock,z.vlanblock)}</td>
  <td class="mono" style="font-size:12px">${z.vlan_von}–${z.vlan_bis}<br><small style="color:var(--muted)">Dienst ${z.vlan_d.vorstand}/${z.vlan_d.gaeste}/${z.vlan_d.technik}</small></td>
  <td>${inp(z,"quote",w.quote!=null?String(+(w.quote*100).toFixed(2)).replace(".",","):"",(z.quote*100).toFixed(1).replace(".",","))}<br><small style="color:var(--muted)">${esc(z.herkunft)}</small></td>
  <td>${gz(z.kunden,1)}</td><td><b>${eur(z.einnahme)}</b></td><td>${eur(z.einnahme_monat)}</td><td>${z.ist_gebucht!=null?z.ist_gebucht+" · "+eur(z.ist_einnahme):"–"}</td>
  <td>${eur(z.investition)}</td><td style="color:${z.db<0?"var(--red)":"inherit"}">${eur(z.db)}</td><td>${z.amortisation==null?"nie":gz(z.amortisation,1)+" J."}</td><td>${esc(z.pruefung)}</td></tr>`}
 h+=`<tr class="kopf"><td></td><td>${L.length==d.zeilen.length?"Alle Sparten":L.length+" von "+d.zeilen.length+" Sparten"}</td><td></td><td>${gz(sum("parz"))}</td><td></td><td></td><td></td><td>${gz(sum("faser_zul"))}</td><td></td><td></td><td></td><td>${sum("parz")?pct(sum("kunden")/sum("parz")):"–"}</td><td>${gz(sum("kunden"))}</td><td>${eur(sum("einnahme"))}</td><td>${eur(sum("einnahme_monat"))}</td><td>${gz(sum("ist_gebucht"))}</td><td>${L.length==d.zeilen.length?eur(d.gesamt.investition):"–"}</td><td>${L.length==d.zeilen.length?eur(d.gesamt.db):"–"}</td><td></td><td></td></tr></table>`;
 box.innerHTML=L.length?h:'<p class="hint" style="padding:12px">Keine Sparte passt zum Filter.</p>';box.scrollTop=y;box.scrollLeft=x;
 box.querySelectorAll(".gp_in").forEach(e=>e.onchange=async()=>{const r=await api("/api/gwplan-sparte",{nr:+e.dataset.nr,[e.dataset.f]:e.value.trim()},"log_gp");if(r&&r.gesamt)gpZeigen(r)})}
function gpAnZeigen(d){if($("gp_an").dataset.fertig)return;const a=d.annahmen;
 $("gp_an").innerHTML=d.felder.map(([gr,fs],i)=>`<details class="gp_an"${i==0?" open":""}><summary style="cursor:pointer;font-weight:600;margin-top:8px">${esc(gr)}</summary><div class="reihe" style="margin-top:8px">`+
  fs.map(([k,t,ein])=>`<div><label>${esc(t)}${ein=="%"?" (%)":""}</label><input class="gp_ai" data-k="${k}" data-p="${ein=="%"?1:0}" value="${String(+(ein=="%"?a[k]*100:a[k]).toFixed(4)).replace(".",",")}" inputmode="decimal"></div>`).join("")+"</div></details>").join("");
 $("gp_an").dataset.fertig="1"}
async function gpAnSpeichern(){const an={};document.querySelectorAll(".gp_ai").forEach(e=>an[e.dataset.k]=e.value.trim());const r=await api("/api/gwplan-annahmen",{annahmen:an},"log_gpa");if(r&&r.gesamt){$("gp_an").dataset.fertig="";gpZeigen(r)}}
async function gpSchnell(){const mix={};document.querySelectorAll(".gp_mix").forEach(e=>mix[e.dataset.t]=e.value.trim()||"0");
 const r=await api("/api/gwplan-annahmen",{annahmen:{Quote_Modus:$("gp_qm").value,Quote_fest:$("gp_qf").value.trim(),Szenario:$("gp_sz").value},tarifmix:mix,preis_quelle:$("gp_pq").value},"log_gps");if(r&&r.gesamt){$("gp_an").dataset.fertig="";gpZeigen(r)}}
async function gpReset(was){if(!confirm(was=="wahl"?"Alle eigenen Zuordnungen (Standort, Zuleitung, Reihenfolge, Quote, Mengen) löschen?":was=="daten"?"Importierte Excel-Daten verwerfen und wieder die eingebauten Daten verwenden?":"Alle Einstellungen auf Standard zurücksetzen?"))return;
 const r=await api("/api/gwplan-zuruecksetzen",{was},was=="annahmen"?"log_gpa":"log_gpi");if(r&&r.gesamt){$("gp_an").dataset.fertig="";gpZeigen(r)}}
async function gpImport(){const f=$("gp_datei").files[0];if(!f)return;const r=await api("/api/gwplan-import",f,"log_gpi");$("gp_datei").value="";if(r&&r.gesamt){$("gp_an").dataset.fertig="";gpZeigen(r)}}
function gpCsv(){if(!GP)return;csvSpeichern({spalten:[["nr","Nr."],["name","Sparte"],["kz","Kürzel"],["vlanblock","VLAN-Block"],["vlan_t","VLANs Parzellen"],["dienst_t","VLAN Vorstand/Gäste/Technik"],["parz","Parzellen"],["leer","Leerstand"],["standort","Standort Nr."],["zuleitung","Zuleitung von Nr."],["versorgt","versorgt durch"],["faser_zul","Glasfaser Zuleitung m"],["quote_t","Buchungsquote"],["herkunft","Quote Herkunft"],["kunden_t","Kunden"],["einnahme_t","Einnahme / Jahr"],["monat_t","Einnahme / Monat"],["inv_t","Investition"],["db_t","Deckungsbeitrag / Jahr"],["pruefung","Prüfung"]],
 zeilen:GP.zeilen.map(z=>Object.assign({},z,{vlan_t:z.vlan_von+"–"+z.vlan_bis,dienst_t:z.vlan_d.vorstand+"/"+z.vlan_d.gaeste+"/"+z.vlan_d.technik,quote_t:(z.quote*100).toFixed(1).replace(".",",")+" %",kunden_t:String(z.kunden).replace(".",","),einnahme_t:String(z.einnahme).replace(".",","),monat_t:String(z.einnahme_monat).replace(".",","),inv_t:String(z.investition).replace(".",","),db_t:String(z.db).replace(".",",")}))},"SparteNet_Netzplanung")}
function kkCsv(){if(!KK)return;const T=KK.tarife;csvSpeichern({spalten:[["name","Sparte"],["kz","Kürzel"],["gateway","Gateway"],["n","Parzellen"],["gebucht","gebucht"],["rate_t","Buchungsrate"]].concat(T.map(t=>["t_"+t.name,t.name])).concat([["umsatz_brutto","Umsatz/Jahr"],["investition","Investition"],["kosten","lfd. Kosten/Jahr"],["db","Deckungsbeitrag"],["amortisation","Amortisation (J.)"],["status","Status"]]),
 zeilen:KK.zeilen.map(z=>Object.assign({},z,{rate_t:(z.rate*100).toFixed(1).replace(".",",")+" %"},Object.fromEntries(T.map(t=>["t_"+t.name,z.je[t.name]||0]))))},"SparteNet_Kalkulation")}
function kaZeigen(a,t){$("ka_form").innerHTML=Object.keys(t).map(k=>{const v=a[k];
 if(typeof v=="boolean")return `<div><label><input type="checkbox" class="ka_in" data-k="${k}" ${v?"checked":""} style="width:auto"> ${esc(t[k])}</label></div>`;
 if(k=="phase")return `<div><label>${esc(t[k])}</label><select class="ka_in" data-k="phase"><option value="auto"${v=="auto"?" selected":""}>automatisch (Kleinunternehmer → Startphase)</option><option value="start"${v=="start"?" selected":""}>Startphase</option><option value="voll"${v=="voll"?" selected":""}>Ausbau</option></select></div>`;
 return `<div><label>${esc(t[k])}</label><input class="ka_in" data-k="${k}" value="${String(v).replace(".",",")}" inputmode="decimal"></div>`}).join("")}
async function kaSpeichern(){const b={};document.querySelectorAll(".ka_in").forEach(e=>{b[e.dataset.k]=e.type=="checkbox"?e.checked:e.tagName=="SELECT"?e.value:e.value.replace(",",".")});await api("/api/kalk-annahmen",b,"log_ka");kkLaden()}
async function kkImport(){const f=$("kk_datei").files[0];if(!f)return;await api("/api/kalk-import",f,"log_ki");$("kk_datei").value="";KB=null;kkLaden()}
async function kbLaden(still){const kz=$("kb_sp").value;if(!kz)return;if(!still&&Object.keys(KBAEND).length&&!confirm("Ungespeicherte Buchungen verwerfen?"))return;KBAEND={};
 const d=await api("/api/buchungen?sparte="+encodeURIComponent(kz),undefined,"log_kb");KB=d;kbZeigen()}
function kbTarif(p){return p in KBAEND?KBAEND[p]:KB.zeilen[p-1].tarif}
function kbZeigen(){const T=KK?KK.tarife:[];const opt=w=>'<option value="">–</option>'+T.map(t=>`<option value="${esc(t.name)}"${t.name==w?" selected":""}>${esc(t.name)}</option>`).join("");
 $("kb_tab").innerHTML="<table><tr><th>Parzelle</th><th>Netz</th><th>Tarif</th></tr>"+KB.zeilen.map(z=>{const w=kbTarif(z.p);return `<tr class="${z.p in KBAEND?"geaendert":z.unbekannt?"falsch":""}"><td>${z.p}</td><td class="mono">${esc(z.netz)}</td><td><select class="kb_sel" data-p="${z.p}" style="min-width:140px">${opt(w)}</select>${z.unbekannt&&!(z.p in KBAEND)?" <small>Tarif „"+esc(z.tarif)+"“ fehlt</small>":""}</td></tr>`}).join("")+"</table>";
 document.querySelectorAll(".kb_sel").forEach(s=>s.onchange=()=>kbSetzen(+s.dataset.p,s.value));kbStand()}
function kbSetzen(p,w){if(w===KB.zeilen[p-1].tarif)delete KBAEND[p];else KBAEND[p]=w;const tr=document.querySelector(`.kb_sel[data-p="${p}"]`);if(tr){tr.value=w;tr.closest("tr").classList.toggle("geaendert",p in KBAEND)}kbStand()}
function kbStand(){const n=Object.keys(KBAEND).length,T=KK?KK.tarife:[],z={};let g=0;KB.zeilen.forEach(r=>{const w=kbTarif(r.p);if(w&&T.some(t=>t.name==w)){g++;z[w]=(z[w]||0)+1}});
 $("kb_k").innerHTML=kachel("gebucht",g+" / "+KB.n,"gut")+kachel("Buchungsrate",pct(g/KB.n),g/KB.n>=.6?"gut":"warn")+T.map(t=>kachel(esc(t.name),z[t.name]||0,"")).join("")+kachel("Umsatz / Jahr",eur(T.reduce((s,t)=>s+(z[t.name]||0)*t.preis,0)),"gut");
 $("kb_offen").textContent=n?n+" ungespeichert":"alles gespeichert";$("kb_offen").classList.toggle("ok",!n)}
function kbBereich(txt,max){const s=new Set();for(const teil of txt.split(/[,; ]+/).filter(Boolean)){const m=teil.match(/^(\d+)(?:-(\d+))?$/);if(!m)throw new Error("„"+teil+"“ verstehe ich nicht – Beispiel: 1-20, 25");let a=+m[1],b=+(m[2]||m[1]);if(a>b)[a,b]=[b,a];for(let p=a;p<=b;p++){if(p<1||p>max)throw new Error("Parzelle "+p+" gibt es nicht (1–"+max+")");s.add(p)}}return [...s]}
function kbMassen(){if(!KB)return;try{const ps=kbBereich($("kb_bereich").value,KB.n);if(!ps.length)return $("kb_bereich").focus();ps.forEach(p=>kbSetzen(p,$("kb_tarif").value));$("log_kb").textContent=ps.length+" Parzelle(n) auf „"+($("kb_tarif").value||"nicht gebucht")+"“ gesetzt – noch speichern."}catch(e){$("log_kb").innerHTML='<span class="fehler">✖ '+esc(e.message)+"</span>"}}
async function kbSpeichern(){if(!Object.keys(KBAEND).length)return $("log_kb").textContent="Nichts geändert.";await api("/api/buchungen",{sparte:KB.kz,aenderungen:KBAEND},"log_kb");const l=$("log_kb").textContent;KBAEND={};await kkLaden();await kbLaden(true);$("log_kb").textContent=l}
async function beenden(){if(confirm("SparteNet Manager beenden?")){await api("/api/beenden",{});document.body.innerHTML="<p style='padding:40px;font-family:Arial'>Beendet. Fenster kann geschlossen werden.</p>"}}
ansAnwenden();druckKnoepfe();zeige(startReiter());if(ICH.admin)setTimeout(()=>upLaden(true).catch(()=>{}),1500);einst();planLaden(true);regelLaden();["pr_pre","pr_z"].forEach(i=>$(i).addEventListener("input",regelBeispiel));
</script></body></html>"""

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben

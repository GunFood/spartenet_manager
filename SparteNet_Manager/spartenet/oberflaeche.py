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
.mlogo-kopf{height:36px;width:auto;max-width:120px;object-fit:contain;border-radius:8px;background:#fff;padding:2px;margin-right:-6px}header b{font-size:22px}header b span{color:#6cc24a}header small{opacity:.7}#verb{font-size:13px;opacity:.85}
nav{display:flex;gap:4px;padding:0 22px;background:var(--card);border-bottom:1px solid var(--line);flex-wrap:wrap}
nav button{border:0;background:none;padding:13px 16px;font-size:15px;cursor:pointer;color:var(--muted);border-bottom:3px solid transparent}
nav button.aktiv{color:var(--navy);border-bottom-color:var(--green);font-weight:600}
.burger{width:42px;height:38px;border:1px solid rgba(255,255,255,.55);background:none;border-radius:9px;display:inline-flex;flex-direction:column;justify-content:center;align-items:center;gap:4px;cursor:pointer;padding:0;flex:none}
.burger span{display:block;width:18px;height:2px;border-radius:2px;background:#fff;transition:transform .2s,opacity .2s}
.burger:hover{background:rgba(255,255,255,.12)}
nav .nkat{font-weight:600;color:var(--text);display:flex;align-items:center;gap:8px;border-right:1px solid var(--line);margin-right:6px;padding-right:18px}
nav .nkat i{font-style:normal}
#menue_hg{position:fixed;inset:0;background:rgba(8,16,12,.45);z-index:900}
#menue{position:fixed;top:0;left:0;bottom:0;width:min(360px,88vw);background:var(--card);color:var(--text);z-index:901;transform:translateX(-102%);transition:transform .22s ease;display:flex;flex-direction:column;box-shadow:8px 0 30px rgba(0,0,0,.25)}
#menue.offen{transform:none}
#menue .mk{display:flex;align-items:center;gap:10px;padding:14px 14px 10px 18px;background:var(--kopf,#1d2f3e);color:#fff}#menue .mk b{flex:1;font-size:17px}#menue .mk b span{color:#8fd16f}
#menue .mx{background:none;border:1px solid rgba(255,255,255,.5);color:#fff;border-radius:8px;width:36px;height:34px;cursor:pointer;font-size:16px}
#menue .ms{padding:12px 14px 6px}#menue .ms input{width:100%}
#menue_liste{flex:1;overflow:auto;padding:4px 8px 12px}
#menue .mf{border-top:1px solid var(--line);padding:10px 16px;font-size:13px;color:var(--muted)}#menue .mf label{display:flex;gap:8px;align-items:center;margin:0}#menue .mf input{width:auto;min-height:0}
.mkat{border-radius:10px;margin:2px 0}
.mkat>button{width:100%;display:flex;align-items:center;gap:10px;border:0;background:none;color:var(--text);font-size:15px;font-weight:600;padding:11px 10px;border-radius:10px;cursor:pointer;text-align:left}
.mkat>button:hover,.mpunkt:hover,.munter:hover{background:var(--hover)}
.mkat>button i{font-style:normal;width:24px;text-align:center}.mkat>button em{margin-left:auto;font-style:normal;color:var(--muted);transition:transform .2s}
.mkat.auf>button em{transform:rotate(90deg)}
.mkat .minhalt{display:none;padding:0 0 6px 34px}.mkat.auf .minhalt,.msuche .minhalt{display:block}
.mpunkt,.munter{display:block;width:100%;border:0;background:none;color:var(--text);text-align:left;cursor:pointer;border-radius:8px}
.mpunkt{padding:8px 10px;font-size:14.5px}.mpunkt.aktiv{background:var(--lgreen);font-weight:600}
.munter{padding:5px 10px 5px 22px;font-size:13px;color:var(--muted);position:relative}.munter::before{content:"";position:absolute;left:10px;top:50%;width:5px;height:5px;border-radius:50%;background:var(--line);transform:translateY(-50%)}
.mtreffer{font-size:12px;color:var(--muted);padding:2px 10px 6px}
.karte.blink{animation:kblink 1.8s ease}
.p-zu>*:not(.p-kopf){display:none!important}
.tk-raster{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:16px;align-items:start}@media (max-width:1000px){.tk-raster{grid-template-columns:1fr}}
.tk-seite{border:1px solid var(--line);border-radius:10px;padding:12px;background:var(--bg2)}.tk-seite h4{margin:0 0 8px;font-size:14px}
.tk-frueh{display:block;width:100%;text-align:left;border:1px solid var(--line);background:var(--card);color:var(--text);border-radius:8px;padding:8px 10px;margin:6px 0;cursor:pointer;font:inherit;font-size:13.5px}
.tk-frueh:hover{border-color:var(--green)}.tk-frueh small{color:var(--muted)}.tk-zu{background:var(--lgreen);border-radius:8px;padding:10px 12px;margin:10px 0}
.akte-ev{display:grid;grid-template-columns:110px 26px 1fr;gap:8px;padding:8px 4px;border-bottom:1px solid var(--line2);align-items:start}.akte-ev .z{color:var(--muted);font-size:12.5px;font-variant-numeric:tabular-nums}
.akte-ev.ticket{cursor:pointer}.akte-ev.ticket:hover{background:var(--hover)}
.gs-raster{display:grid;grid-template-columns:minmax(300px,420px) minmax(0,1fr);gap:16px;align-items:start}@media (max-width:980px){.gs-raster{grid-template-columns:1fr}}
.gs-vor{position:sticky;top:60px}.gs-rahmen{border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--bg2);height:620px;position:relative}
.gs-rahmen iframe{border:0;width:1280px;height:900px;transform-origin:0 0;background:#fff}
.gs-gr.aktiv{border-color:var(--green);font-weight:600}
.gs-gruppe{border:1px solid var(--line);border-radius:10px;margin:0 0 10px;padding:0 12px}.gs-gruppe>summary{cursor:pointer;font-weight:600;padding:10px 0}
.gs-gruppe .gs-f{margin:0 0 10px}.gs-gruppe .gs-f label{font-size:13px}.gs-f input[type=color]{width:60px;height:34px;padding:2px}
.gs-zeile2{display:flex;gap:8px;align-items:center}.gs-zeile2 input[type=range]{flex:1}
.ap-baum{margin-top:12px;border:1px solid var(--line);border-radius:10px;padding:6px}
.ap-z{display:grid;grid-template-columns:70px 46px 44px minmax(120px,1fr) 360px;gap:6px;align-items:center;padding:4px 6px;border-radius:8px}
.ap-z:hover{background:var(--hover)}.ap-nr{font-variant-numeric:tabular-nums;font-weight:600}.ap-kn{color:var(--muted);font-size:12px}
.ap-z input[type=text]{min-height:32px;padding:5px 8px}.ap-z .ak{display:flex;gap:4px;align-items:center;flex-wrap:wrap;justify-content:flex-start}
.ap-z button.mini{padding:4px 8px;min-height:30px}.ap-z label{display:flex;gap:4px;align-items:center;margin:0;font-size:12.5px;white-space:nowrap}.ap-z label input{width:auto;min-height:0}
.ap-b{background:var(--bg2);margin-top:6px}.ap-r{margin-left:22px}.ap-k{margin-left:44px}.ap-t{margin-left:66px}.ap-aus{opacity:.5}
.ap-hint{margin:2px 6px 8px 160px}.ap-hint textarea{width:100%;font:inherit;font-size:13px}
@media (max-width:900px){.ap-z{grid-template-columns:62px 1fr}.ap-kn,.ap-z .ic{display:none}.ap-z .ak{grid-column:1/-1}.ap-r,.ap-k,.ap-t{margin-left:8px}.ap-hint{margin-left:8px}}.p-klapp{cursor:pointer}.p-klapp::after{content:" ▾";color:var(--muted);font-size:.8em}.p-zu .p-klapp::after{content:" ▸"}@keyframes kblink{0%,60%{box-shadow:0 0 0 3px var(--green)}100%{box-shadow:none}}
@media (pointer:coarse){.mpunkt{padding:12px 10px}.munter{padding:9px 10px 9px 22px}}
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
.status{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;background:#eee;color:#555;margin-left:6px}.status.ok{background:#dcf2d2;color:#24661a}.status:empty{display:none}input[type=color]{height:40px;padding:3px 4px;cursor:pointer}.re-leiste{display:flex;gap:4px;flex-wrap:wrap;padding:6px;border:1px solid var(--line);border-bottom:0;border-radius:7px 7px 0 0;background:var(--bg2)}.re-leiste button{border:1px solid var(--line);background:var(--card);color:var(--text);border-radius:5px;padding:4px 9px;font-size:13px;cursor:pointer;min-width:30px}.re-leiste button:hover{background:var(--hover)}.re-leiste select{width:auto;padding:4px 6px;font-size:13px}.re-feld{min-height:160px;max-height:460px;overflow:auto;border:1px solid var(--line);border-radius:0 0 7px 7px;padding:10px 12px;background:var(--card);color:var(--text);outline:none;line-height:1.5}.re-feld:focus{border-color:var(--green)}.re-feld h2{font-size:19px;margin:10px 0 6px}.re-feld h3{font-size:16px;margin:8px 0 4px}.re-feld p{margin:0 0 8px}.tk-prio-dringend{color:var(--red);font-weight:700}.tk-prio-hoch{color:var(--amber);font-weight:600}.tk-verlauf{border-left:3px solid var(--line);padding:4px 0 4px 12px;margin:8px 0;white-space:pre-wrap}.tk-verlauf.antwort{border-color:var(--green)}.tk-verlauf.kommentar{border-color:#6c8ebf}.tk-verlauf small{color:var(--muted)}
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
@media (pointer:coarse) and (min-width:861px){.kd{grid-template-columns:minmax(280px,min(var(--kd-links,430px),45%)) minmax(0,1fr)}.dgrid{grid-template-columns:minmax(200px,var(--d-links,270px)) minmax(0,1fr)}}
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
<header><button class="burger" id="burger" onclick="menue()" aria-label="Menü öffnen" aria-controls="menue" aria-expanded="false" title="Menü (Strg+K)"><span></span><span></span><span></span></button>__MANAGERLOGO__<b>Sparte<span>Net</span></b>__KOPFLOGOS__<small>Manager __VERSION__ · Cloud</small><span id="verb"></span><div style="flex:1"></div><button class="k ich" id="up_chip" onclick="zeige('system')" hidden title="Neue Version verfügbar"></button><button class="k ich" id="ich_k" onclick="zeige('benutzer')" title="Mein Konto und Benutzerkonten"></button><button class="k" style="background:none;color:#fff;border-color:#fff" onclick="ansichtPanel()" title="Breite, Größe, Tabellenhöhe und Farbschema (hell/dunkel) anpassen">Ansicht</button><button class="k ich" id="farbe_k" onclick="farbeWechseln()" title="Farbschema: System → Hell → Dunkel"></button><button class="k pc-nur" id="beenden_k" style="background:none;color:#fff;border-color:#fff" onclick="beenden()">Beenden</button></header>
<div id="ansicht"><h3>Ansicht anpassen</h3><p class="hint" style="margin:2px 0 6px">Für FHD bis 8K, normal oder curved. Wird gespeichert. Breite auch direkt am rechten Rand ziehen (Doppelklick = volle Breite).</p>
<div class="feld"><label for="an_breite_sel">Breite des Inhalts</label><output id="an_breite_o"></output><select id="an_breite_sel" onchange="ansSet('breite',+this.value)"><option value="1200">Standard (FHD)</option><option value="1600">Breit (WQHD)</option><option value="2200">Sehr breit (4K)</option><option value="3200">Ultra (5K / Curved)</option><option value="0">Volle Fensterbreite</option><option value="-1">Eigene …</option></select>
<input type="range" id="an_breite" min="800" max="6000" step="50" oninput="ansSet('breite',+this.value)"></div>
<div class="feld"><label for="an_zoom_sel">Größe (Skalierung)</label><output id="an_zoom_o"></output><select id="an_zoom_sel" onchange="ansSet('zoom',+this.value)"><option value="0">Automatisch nach Bildschirm</option><option value="0.8">80 %</option><option value="0.9">90 %</option><option value="1">100 %</option><option value="1.1">110 %</option><option value="1.25">125 %</option><option value="1.5">150 %</option><option value="1.75">175 %</option><option value="2">200 %</option><option value="2.5">250 %</option><option value="3">300 %</option></select></div>
<div class="feld"><label for="an_tabh_sel">Höhe der Tabellen</label><output id="an_tabh_o"></output><select id="an_tabh_sel" onchange="ansSet('tabh',+this.value)"><option value="0">An Fensterhöhe anpassen</option><option value="320">Niedrig</option><option value="520">Standard</option><option value="900">Hoch</option><option value="-1">Eigene …</option></select>
<input type="range" id="an_tabh" min="200" max="3000" step="20" oninput="ansSet('tabh',+this.value)"></div>
<div class="feld"><label for="an_farbe">Farbschema</label><select id="an_farbe" onchange="farbeSetzen(this.value)"><option value="system">Wie das System (hell/dunkel automatisch)</option><option value="hell">Hell</option><option value="dunkel">Dunkel</option></select></div>
<div class="feld chk"><input type="checkbox" id="an_spalten" onchange="ansSet('spalten',this.checked)"><label for="an_spalten">Karten nebeneinander, wenn Platz ist (breite Monitore)</label></div>
<div class="feld chk"><input type="checkbox" id="an_reiter" onchange="ansSet('reiter',this.checked)"><label for="an_reiter">Alle Reiter oben anzeigen (sonst Menü ☰ und die Reiter des jeweiligen Bereichs)</label></div>
<div class="knoepfe"><button class="k" onclick="ansZurueck()">Zurücksetzen</button><button class="k p" onclick="ansichtPanel(false)">Fertig</button></div></div>
<div id="nurlesen" class="nurlesen" hidden></div>
<nav id="nav"></nav>
<div id="menue_hg" hidden onclick="menue(false)"></div>
<aside id="menue" aria-label="Menü" aria-hidden="true"><div class="mk"><b>Sparte<span>Net</span> · Menü</b><button class="mx" onclick="menue(false)" aria-label="Menü schließen">✕</button></div>
<div class="ms"><input id="menue_suche" type="search" placeholder="Funktion suchen … (z. B. Laufzeit, Logo, SMTP)" autocomplete="off" oninput="menueBauen()"></div>
<div id="menue_liste"></div><div class="mf"><label><input type="checkbox" id="menue_reiter" onchange="ansSet('reiter',this.checked)"> Alle Reiter oben anzeigen</label></div></aside>
<main id="main"><div id="griff" title="Ziehen: Breite ändern · Doppelklick: volle Breite / Standard"></div>
<section id="start"><div class="karte" id="ue_karte" hidden><h3>Auf einen Blick</h3><div class="kacheln" id="ue_k"></div></div><div class="karte"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><h2 style="flex:1;margin:0">Überblick <span id="st_zeit" class="status"></span></h2><button class="k" onclick="startLaden()">Aktualisieren</button></div>
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
<div data-bereich="wlan_pw" class="karte schritt"><div class="nr">2</div><div style="flex:1;min-width:0"><h3>WLANs der Sparte</h3><p class="hint">Pächter <b id="ssid1"></b> (WPA2, PPSK) · Gäste <b id="ssid2"></b> (Hotspot/Voucher) · Vorstand <b id="ssid3"></b><span id="ssid_eigen"></span>. Heißen die WLANs am Gateway anders: abrufen, das richtige wählen und speichern – Passwortliste, Übertragen und Zugangskarten nutzen dann diesen Namen.</p>
<div class="knoepfe" style="margin-top:6px"><button class="k" onclick="wlAbrufen()">WLANs vom Gateway abrufen</button></div>
<div id="wl_wahl" hidden><div class="reihe"><div><label for="wl_p">Pächter-WLAN (PPSK, Passwort je Parzelle)</label><select id="wl_p"></select></div><div><label for="wl_g">Gäste-WLAN (Voucher)</label><select id="wl_g"></select></div><div><label for="wl_v">Vorstand-WLAN</label><select id="wl_v"></select></div></div>
<div class="knoepfe"><button class="k p" onclick="wlSpeichern()">Zuordnung speichern</button><button class="k" onclick="wlSchema()">Namen nach Schema</button></div></div><div class="log" id="log_wl"></div></div></div>
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
<div class="knoepfe"><button class="k p" onclick="vergleich()">Unterschiede ermitteln</button></div><div class="log" id="log_ue"></div><div class="kacheln" id="vg_k"></div>
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

<div data-bereich="buchungen" class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Laufzeiten und Zugang</h3><button class="k" onclick="lzLaden()">Aktualisieren</button></div>
<p class="hint">Tarife mit <b>Laufzeit</b> (oben, z. B. 1 Tag oder 1 Monat) beginnen bei der Buchung. Läuft die Zeit ab, wird der <b>Zugang der Parzelle gesperrt</b>: ihr Passwort wird aus dem Pächter-WLAN genommen – Netz, VLAN und Passwort bleiben gespeichert. <b>Verlängern</b> startet eine neue Laufzeit (ab Ende bzw. ab jetzt) und gibt den Zugang wieder frei. Erinnerung, Ablauf, Sperre und Freigabe sind Auslöser für Automationen (z. B. E-Mail an den Pächter, nach Zahlungseingang automatisch verlängern).</p>
<div class="kacheln" id="lz_k"></div>
<div class="reihe" id="lz_einst" style="margin-top:10px"><div><label class="feld chk" style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="lz_auto" style="width:auto"> Am Gateway automatisch sperren und freigeben</label><p class="hint" style="margin:4px 0 0">Nur Administratoren. Aus: der Manager zeigt nur an, was zu tun ist – Sperren/Freigeben dann hier von Hand (mit Vorschau).</p></div>
<div><label for="lz_erin">Erinnerung vor Ablauf</label><select id="lz_erin"><option value="0">keine</option><option value="1">1 Stunde</option><option value="3">3 Stunden</option><option value="12">12 Stunden</option><option value="24">1 Tag</option><option value="72">3 Tage</option><option value="168">7 Tage</option></select></div>
<div><label class="feld chk" style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="lz_entf" style="width:auto"> nach Ablauf zusätzlich die Buchung entfernen</label><p class="hint" style="margin:4px 0 0">Nur mit automatischem Sperren. Sonst bleibt die Parzelle gebucht und kann verlängert werden.</p></div></div>
<div class="knoepfe" id="lz_einst_kn"><button class="k" onclick="lzEinst(false)">Einstellungen speichern</button><button class="k" onclick="lzEinst(true)">Speichern &amp; jetzt prüfen</button></div>
<div class="reihe" style="margin-top:10px"><div><label for="lz_suche">Suchen</label><input id="lz_suche" placeholder="z. B. BW 12 oder abgelaufen" oninput="lzZeigen()"></div></div>
<div id="lz_tab"></div><div id="lz_ohne"></div><div class="log" id="log_lz"></div></div>

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
<div><label for="gp_sz">Alter und Leerstand</label><select id="gp_sz"><option value="1">heute</option><option value="2">in 5 Jahren</option></select></div>
<div><label for="gp_gb">Gateways bemessen nach</label><select id="gp_gb"><option value="1">allen Parzellen (Vollausbau)</option><option value="2">erwarteten Kunden (Buchungsquote)</option><option value="3">tatsächlichen Buchungen</option></select></div></div>
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
<select id="zt_stf" onchange="ztZeigen();zpLaden().catch(()=>{})" style="max-width:280px;margin:6px 0"></select><div class="tab" id="zt_tab"></div><div class="log" id="log_zt"></div>
<details id="zp_box" style="margin-top:12px"><summary style="cursor:pointer;font-weight:600">Parzellen einzeln einem Gateway zuordnen</summary>
<p class="hint">Je Parzelle festlegen, an welchem Gateway sie liegt. <b>Automatisch</b> = erstes Gateway mit freiem Platz. Für noch nicht gebuchte Parzellen ist die Auswahl eine <b>Vorgabe</b> für die spätere Buchung. Gebuchte Parzellen mit Netz werden verschoben: das neue Netz entsteht und das alte wird entfernt über „Einrichten → Netze nach Buchungen“ (je Gateway, mit Vorschau). „Verdichten“ legt alle nicht fest zugeordneten Buchungen auf möglichst wenige Gateways – bei kleiner Buchungsrate z. B. alles auf Gateway 1.</p>
<div class="knoepfe zt-schreib" style="margin-top:0"><select id="zp_sp" onchange="zpZeigen()" style="max-width:260px"></select><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="zp_nur" style="width:auto" onchange="zpZeigen()" checked> nur gebuchte</label>
<select id="zp_alle" style="max-width:220px"></select><button class="k" onclick="zpAlleSetzen()">für alle angezeigten setzen</button></div>
<div class="tab" id="zp_tab" style="--tab-h:480px"></div>
<div class="knoepfe zt-schreib"><button class="k p" onclick="zpSpeichern()">Zuordnung speichern</button><button class="k" onclick="zpVerdichten()">Auf möglichst wenige Gateways verdichten</button></div><div class="log" id="log_zp"></div></details></div>
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

<section id="system"><div class="karte" id="ow_karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Störungsüberwachung</h2><span id="ow_st" class="status"></span><button class="k" onclick="owLaden()">Aktualisieren</button><button class="k bn-admin" onclick="owSpeichern(true)">Jetzt prüfen</button></div>
<p class="hint">Der Manager prüft regelmäßig die Geräte der eingestellten Konsole. Ist ein Gerät länger offline als die Verzögerung, entsteht ein Ticket (Priorität hoch) und die Automation „Störung“ (z. B. E-Mail). Wieder online → Vermerk im Ticket und „Störung behoben“.</p>
<div class="reihe bn-admin"><div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="ow_aktiv" style="width:auto"> Überwachung eingeschaltet</label></div><div><label for="ow_int">alle … Minuten prüfen</label><input id="ow_int" type="number" min="5"></div><div><label for="ow_verz">melden nach … Minuten offline</label><input id="ow_verz" type="number" min="0"></div><div><label for="ow_zu">Ticket zuweisen an</label><select id="ow_zu"></select></div></div>
<div class="bn-admin" style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px"><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="ow_ticket" style="width:auto"> Ticket anlegen</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="ow_auto" style="width:auto"> Ticket automatisch erledigen, wenn wieder online</label><button class="k p" onclick="owSpeichern(false)">Speichern</button></div>
<div class="tab" id="ow_tab" style="--tab-h:320px"></div><div class="log" id="log_ow"></div></div>
<div class="karte bn-admin" id="si_karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Datensicherung</h2><button class="k" onclick="siLaden()">Aktualisieren</button></div>
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
<div class="reihe" style="margin-top:10px"><div><label for="ul_ordner">In Ordner hochladen</label><select id="ul_ordner" onchange="ulOrdnerWahl()"></select><input id="ul_ordner_neu" placeholder="Name des neuen Ordners" maxlength="60" hidden style="margin-top:6px"></div>
<div><label for="ul_sparte">Sparte</label><select id="ul_sparte"></select></div><div><label for="ul_beschr">Beschreibung (optional)</label><input id="ul_beschr" maxlength="300"></div></div>
<div class="log" id="log_ulh"></div>
<details style="margin-top:12px"><summary style="cursor:pointer;font-weight:600">Ordner verwalten</summary>
<div class="knoepfe"><input id="ul_neuer_ordner" placeholder="Neuer Ordner, z. B. Wartung" maxlength="60" style="max-width:300px"><button class="k" onclick="ulOrdnerNeu()">Ordner anlegen</button></div>
<div class="tab" id="ul_ordner_tab"></div><div class="log" id="log_ulo"></div></details></div></section>

<section id="mitglieder"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Mitglieder</h2><span id="mg_st" class="status"></span><button class="k" onclick="mgLaden()">Aktualisieren</button><button class="k" onclick="mgExport()">Als CSV</button><button class="k p mg-schreib" onclick="mgNeu()">Neues Mitglied</button></div>
<p class="hint">Pächter mit Vorname, Nachname, E-Mail und Telefon je Parzelle. Der gebuchte Tarif kommt aus „Tarife“/„Kalkulation“. In E-Mails: {vorname}, {nachname}, {telefon}; „an den Kunden“ geht an die E-Mail des Mitglieds der Parzelle. Neu anlegen auch über die API (POST /api/v1/mitglied) oder per Excel/CSV.</p>
<div class="reihe"><div><label for="mg_such">Suchen</label><input id="mg_such" placeholder="Name, E-Mail, Telefon …" oninput="mgZeigen()"></div><div><label for="mg_f">Sparte</label><select id="mg_f" onchange="mgZeigen()"></select></div><div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="mg_nur" style="width:auto" onchange="mgZeigen()"> nur mit gebuchtem Tarif</label></div></div>
<div class="tab" id="mg_tab" style="--tab-h:560px"></div><div id="mg_ohne"></div><div class="log" id="log_mg"></div></div>
<div class="karte mg-schreib" id="mg_form" hidden><h3 id="mg_form_t">Mitglied</h3><input type="hidden" id="mg_id">
<div class="reihe"><div><label for="mg_vorname">Vorname</label><input id="mg_vorname" maxlength="120" autocomplete="off"></div><div><label for="mg_nachname">Nachname</label><input id="mg_nachname" maxlength="120" autocomplete="off"></div><div><label for="mg_email">E-Mail</label><input id="mg_email" type="email" maxlength="200" autocomplete="off"></div><div><label for="mg_telefon">Telefon</label><input id="mg_telefon" type="tel" maxlength="30" autocomplete="off"></div><div><label for="mg_mobil">Mobil</label><input id="mg_mobil" type="tel" maxlength="30" autocomplete="off"></div></div>
<div class="reihe"><div><label for="mg_sp">Sparte</label><select id="mg_sp"></select></div><div><label for="mg_parzelle">Parzelle</label><input id="mg_parzelle" inputmode="numeric" maxlength="3"></div><div><label for="mg_notiz">Notiz</label><input id="mg_notiz" maxlength="300"></div></div>
<h4 style="margin:14px 0 2px">Weitere Personen dieser Parzelle</h4><p class="hint" style="margin:0 0 6px">Mitpächter, Partner, Familie … Jede Person mit E-Mail-Adresse kann sich selbst im Mitgliederbereich und in der Mitglieder-App anmelden (Einmalcode an ihre eigene Adresse) und sieht dort dieselbe Parzelle. Rechnungen und Verträge laufen weiter auf das Mitglied oben.</p>
<div id="mg_weitere"></div><div class="knoepfe" style="margin-top:4px"><button class="k" type="button" onclick="mgWeitereZeile()">+ Weitere Person</button></div>
<div class="knoepfe"><button class="k p" onclick="mgSpeichern()">Speichern</button><button class="k" onclick="$('mg_form').hidden=true">Abbrechen</button><button class="k r" id="mg_loeschen" onclick="mgLoeschen()">Löschen</button><button class="k" id="mg_auskunft" onclick="mgAuskunft()">Datenschutz-Auskunft (Datei)</button><button class="k r" id="mg_dsgvo" onclick="mgDsgvo()">Datenschutz-Löschung</button></div><div class="log" id="log_mgf"></div></div>
<div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Verträge</h3><span id="vt_st" class="status"></span><button class="k" onclick="vtLaden()">Aktualisieren</button></div>
<p class="hint">Je Buchung ein Vertrag (entsteht bei der Buchung automatisch): Beginn, Laufzeit, automatische Verlängerung, Kündigungsfrist. Vor Ablauf der Frist löst der Manager „Vertrag: Kündigungsfrist läuft bald ab“ aus (Automationen, z. B. E-Mail an das Mitglied); nach einer Kündigung zum Vertragsende „Vertrag endet“.</p>
<div class="reihe"><div><label for="vt_f">Anzeigen</label><select id="vt_f" onchange="vtZeigen()"><option value="">alle laufenden</option><option value="Frist läuft ab">Frist läuft bald ab</option><option value="gekündigt">gekündigt</option><option value="beendet">beendet</option></select></div><div><label for="vt_such">Suchen</label><input id="vt_such" oninput="vtZeigen()" placeholder="Name, Sparte, Parzelle"></div></div>
<div class="tab" id="vt_tab" style="--tab-h:420px"></div><div class="log" id="log_vt"></div>
<details class="bn-admin" style="margin-top:10px"><summary style="cursor:pointer;font-weight:600">Einstellungen für neue Verträge</summary><div class="reihe"><div><label for="vt_lz">Laufzeit (Monate)</label><input id="vt_lz" type="number" min="1"></div><div><label for="vt_vl">Verlängerung (Monate, 0 = keine)</label><input id="vt_vl" type="number" min="0"></div><div><label for="vt_fr">Kündigungsfrist (Monate)</label><input id="vt_fr" type="number" min="0"></div><div><label for="vt_er">Erinnerung (Tage vor Fristende)</label><input id="vt_er" type="number" min="0"></div></div>
<label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="vt_auto" style="width:auto"> Buchung zum Vertragsende im Manager entfernen (am Gateway erst über „Netze nach Buchungen“/„Tarife“)</label><div class="knoepfe"><button class="k p" onclick="vtEinst()">Speichern</button></div></details></div>
<div class="karte mg-schreib"><h3>Rundschreiben</h3><p class="hint">E-Mail mit Layout an Mitglieder – z. B. Wartungsankündigung. Jede E-Mail wird persönlich gefüllt ({vorname}, {parzelle}, {tarif} …). Versand im Hintergrund; jede Adresse nur einmal.</p>
<div class="reihe"><div><label>Sparten (keine Auswahl = alle)</label><div id="rs_sp" class="tab" style="--tab-h:150px;padding:6px 10px"></div></div><div><label>Tarife (keine Auswahl = alle)</label><div id="rs_tf" style="padding:6px 0"></div><label style="display:flex;gap:8px;align-items:center;margin-top:10px"><input type="checkbox" id="rs_nur" style="width:auto" checked> nur Mitglieder mit gebuchtem Tarif</label></div></div>
<div class="reihe"><div><label for="rs_vorlage">Vorlage</label><select id="rs_vorlage" onchange="rsVorlage()"></select></div><div><label for="rs_betreff">Betreff</label><input id="rs_betreff" maxlength="200"></div></div>
<label>Text</label><div id="rs_re"></div>
<div class="knoepfe"><button class="k" onclick="rsPruefen()">Empfänger prüfen</button><input id="rs_test" placeholder="Test an …" style="max-width:220px"><button class="k" onclick="rsSenden(true)">Test senden</button><button class="k p" onclick="rsSenden(false)">An alle senden …</button></div>
<div class="log" id="log_rs"></div><div class="tab" id="rs_verlauf" style="--tab-h:240px"></div></div>
<div class="karte mg-schreib"><h3>Import aus Excel oder CSV</h3><p class="hint">Erste Zeile = Spaltenköpfe. Erkannt werden: <b>Vorname, Nachname</b> (oder Name), <b>E-Mail, Telefon</b> (Tel, Handy), <b>Sparte</b> (Kürzel), <b>Parzelle</b> (Nr), Notiz. Erst „Vorschau“, dann „Übernehmen“. Vorhandene Mitglieder (gleiche E-Mail, oder gleiche Parzelle und gleicher Nachname) werden aktualisiert, nicht doppelt angelegt.</p>
<div class="reihe"><div><label for="mg_datei">Datei (.xlsx oder .csv)</label><input type="file" id="mg_datei" accept=".xlsx,.csv,.txt"></div><div><label for="mg_imp_sp">Sparte, wenn in der Datei keine steht</label><select id="mg_imp_sp"></select></div></div>
<div class="knoepfe"><button class="k" onclick="mgImport(false)">Vorschau</button><button class="k p" id="mg_imp_ok" onclick="mgImport(true)" disabled>Übernehmen</button></div><div class="log" id="log_mgi"></div><div class="tab" id="mg_imp_tab"></div></div></section>

<section id="rechnungen"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Rechnungen</h2><span id="re_st" class="status"></span><button class="k" onclick="reLaden()">Aktualisieren</button></div>
<div class="reihe"><div><label for="re_jahr">Jahr</label><select id="re_jahr" onchange="reLaden()"></select></div><div><label for="re_fs">Status</label><select id="re_fs" onchange="reLaden()"><option value="">alle</option><option value="offen">offen</option><option value="teilweise">teilweise bezahlt</option><option value="bezahlt">bezahlt</option><option value="storniert">storniert</option></select></div><div><label for="re_such">Suchen</label><input id="re_such" oninput="reZeigen()" placeholder="Nr., Name, Parzelle"></div></div>
<div class="kacheln" id="re_k"></div><div class="tab" id="re_tab" style="--tab-h:480px"></div>
<div class="knoepfe re-schreib"><button class="k" onclick="reAlle(true)">alle auswählen</button><button class="k" onclick="reAlle('nicht')">noch nicht versendete</button><button class="k p" onclick="reSenden()">Ausgewählte per E-Mail senden …</button></div><div class="log" id="log_re"></div></div>
<div class="karte re-schreib"><h3>Rechnungslauf</h3><p class="hint">Für jede gebuchte Parzelle mit Mitglied eine Rechnung über den Jahrespreis des Tarifs (Reiter „Tarife“). Parzellen, die für das Jahr schon eine Rechnung haben, werden übersprungen. Rechnungen werden nie gelöscht, nur storniert.</p>
<div class="knoepfe"><input id="rl_jahr" type="number" style="max-width:120px"><button class="k" onclick="reLauf(false)">Vorschau</button><button class="k p" onclick="reLauf(true)">Rechnungen erstellen</button></div><div class="log" id="log_rl"></div><div class="tab" id="rl_tab" style="--tab-h:300px"></div></div>
<div class="karte re-schreib"><h3>Zahlungsabgleich (Kontoauszug)</h3><p class="hint">CSV-Export der Bank hochladen (Spalten wie Buchungstag, Verwendungszweck, Auftraggeber, Betrag). Eingänge werden über die Rechnungsnummer im Verwendungszweck zugeordnet, sonst über Betrag und Name bzw. Parzelle. Bitte prüfen, ggf. anders zuordnen, dann „Übernehmen“ – jede Zahlung löst die Automation „Zahlung eingegangen“ aus. Schon übernommene Buchungen werden erkannt.</p>
<div class="knoepfe"><input type="file" id="za_datei" accept=".csv,.txt" style="max-width:340px"><button class="k" onclick="zaLaden()">Kontoauszug prüfen</button><button class="k p" id="za_ok" onclick="zaUebernehmen()" disabled>Übernehmen</button></div><div class="log" id="log_za"></div><div class="tab" id="za_tab" style="--tab-h:420px"></div></div>
<div class="karte bn-admin"><h3>Einstellungen für Rechnungen</h3>
<div class="reihe"><div><label for="ri_firma">Rechnungssteller</label><input id="ri_firma"></div><div><label for="ri_email">E-Mail</label><input id="ri_email"></div><div><label for="ri_tel">Telefon</label><input id="ri_tel"></div><div><label for="ri_praefix">Präfix Rechnungsnummer</label><input id="ri_praefix" maxlength="10"></div></div>
<div class="reihe"><div><label for="ri_adresse">Anschrift (mehrzeilig)</label><textarea id="ri_adresse" rows="3" style="width:100%;font:inherit"></textarea></div><div><label for="ri_betreff">Rechnungstitel ({jahr})</label><input id="ri_betreff"><label for="ri_ziel">Zahlungsziel (Tage)</label><input id="ri_ziel" type="number" min="0"></div></div>
<div class="reihe"><div><label for="ri_iban">IBAN</label><input id="ri_iban"></div><div><label for="ri_bic">BIC</label><input id="ri_bic"></div><div><label for="ri_bank">Bank</label><input id="ri_bank"></div></div>
<div class="reihe"><div><label for="ri_stnr">Steuernummer</label><input id="ri_stnr"></div><div><label for="ri_ustid">USt-IdNr.</label><input id="ri_ustid"></div><div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="ri_ku" style="width:auto"> Kleinunternehmer (§ 19 UStG)</label></div><div><label for="ri_ust">USt-Satz (%)</label><input id="ri_ust" type="number" min="0" max="100"></div></div>
<label for="ri_oben">Text über der Tabelle</label><input id="ri_oben"><label for="ri_unten">Text unter der Tabelle</label><input id="ri_unten">
<div class="reihe"><div><label for="ri_mb">Betreff der E-Mail</label><input id="ri_mb"></div></div><label>Text der E-Mail ({vorname} {rechnung} {betrag} {faellig} {parzelle} …)</label><div id="ri_re"></div>
<div class="knoepfe"><button class="k p" onclick="riSpeichern()">Speichern</button></div><div class="log" id="log_ri"></div></div></section>

<section id="tickets"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Anfragen (Tickets)</h2><span id="tk_st" class="status"></span><button class="k" onclick="tkLaden()">Aktualisieren</button></div>
<p class="hint">Anfragen von Pächtern – von Hand, über die API (z. B. Kontaktformular: POST /api/v1/ticket) – mit Zuständigkeit, Status und Verlauf. Antworten gehen per E-Mail mit Layout an den Kontakt. Automationen: „Neue Anfrage“, „Ticket zugewiesen“ (z. B. E-Mail an {zustaendig_email}), „Ticket erledigt“.</p>
<div class="reihe"><div><label for="tk_fs">Status</label><select id="tk_fs" onchange="tkLaden()"><option value="offen">offen (nicht erledigt/geschlossen)</option><option value="neu">neu</option><option value="bearbeitung">in Bearbeitung</option><option value="wartet">wartet auf Rückmeldung</option><option value="erledigt">erledigt</option><option value="geschlossen">geschlossen</option><option value="alle">alle</option></select></div>
<div><label for="tk_fz">Zuständig</label><select id="tk_fz" onchange="tkLaden()"><option value="">alle</option><option value="ich">mir zugewiesen</option><option value="niemand">noch niemandem</option></select></div><div><label for="tk_such">Suchen</label><input id="tk_such" placeholder="Nr., Betreff, Name …" onchange="tkLaden()"></div></div>
<div class="tab" id="tk_tab" style="--tab-h:440px"></div><div class="log" id="log_tk"></div>
<div class="reihe bn-admin" style="margin-top:8px"><div><label for="tk_auto">Erledigte Tickets automatisch schließen nach</label><div style="display:flex;gap:6px;align-items:center"><input id="tk_auto" type="number" min="0" max="365" style="max-width:100px"> Tagen <button class="k" onclick="tkAutoSpeichern()">Speichern</button></div><p class="hint" style="margin:4px 0 0">0 = nie. Geschlossene Tickets sind nur noch lesbar und lassen sich wieder öffnen.</p></div></div>
<details id="tkn_box" class="tk-schreib" style="margin-top:12px"><summary style="cursor:pointer;font-weight:600">Neue Anfrage erfassen</summary>
<div class="reihe"><div><label for="tkn_betreff">Betreff</label><input id="tkn_betreff" maxlength="160"></div><div><label for="tkn_kat">Kategorie</label><select id="tkn_kat"></select></div><div><label for="tkn_prio">Priorität</label><select id="tkn_prio"><option value="normal">normal</option><option value="niedrig">niedrig</option><option value="hoch">hoch</option><option value="dringend">dringend</option></select></div><div><label for="tkn_zu">Zuständig</label><select id="tkn_zu"></select></div></div>
<div class="reihe"><div><label for="tkn_name">Name</label><input id="tkn_name" maxlength="120"></div><div><label for="tkn_email">E-Mail</label><input id="tkn_email" type="email"></div><div><label for="tkn_tel">Telefon</label><input id="tkn_tel" type="tel"></div><div><label for="tkn_sp">Sparte</label><select id="tkn_sp"></select></div><div><label for="tkn_p">Parzelle</label><input id="tkn_p" inputmode="numeric"></div></div>
<label for="tkn_text">Anliegen</label><textarea id="tkn_text" rows="4" style="width:100%;font:inherit"></textarea>
<div class="knoepfe"><button class="k p" onclick="tkNeu()">Ticket anlegen</button></div><div class="log" id="log_tkn"></div></details></div>
<div class="karte bn-admin" id="po_karte"><h3>Kontakt-Seite (Selbstauskunft)</h3><p class="hint">Öffentliche Seite <a id="po_link" href="/portal" target="_blank">/portal</a> für Pächter: Anfrage stellen, Stand abfragen, Zugangskarte neu anfordern (geht nur an die beim Mitglied hinterlegte E-Mail). Die Seite ist nur erreichbar, wenn sie hier eingeschaltet ist – für den Zugriff von außen den Manager über einen Reverse-Proxy mit HTTPS freigeben (nur /portal nötig).</p>
<div class="reihe"><div><label style="display:flex;gap:8px;align-items:center;margin-top:8px"><input type="checkbox" id="po_aktiv" style="width:auto"> Kontakt-Seite eingeschaltet</label></div><div><label for="po_titel">Titel</label><input id="po_titel"></div></div>
<label for="po_text">Begrüßungstext</label><input id="po_text"><div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px"><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="po_ticket" style="width:auto"> Anfrage stellen</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="po_status" style="width:auto"> Stand abfragen</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="po_zugang" style="width:auto"> Zugangskarte anfordern</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="po_best" style="width:auto"> Eingangsbestätigung per E-Mail</label></div>
<div class="knoepfe"><button class="k p" onclick="poSpeichern()">Speichern</button></div><div class="log" id="log_po"></div></div>
<div class="karte bn-admin" id="mb_karte"><h3>Mitgliederbereich</h3><p class="hint">Eigene Seite <a id="mb_link" href="/mein" target="_blank">/mein</a> für Mitglieder: Anmeldung mit der hinterlegten E-Mail-Adresse und einem Code per E-Mail (kein Passwort). Mitglieder sehen Tarif mit Laufzeit, Rechnungen (PDF), ihre Geräte im Parzellen-Netz (IP 10.&lt;Sparte&gt;.&lt;Parzelle&gt;.&lt;Gerät&gt;) und ihre Anfragen und können Tarif wechseln, neu buchen oder verlängern. Für den Zugriff von außen /mein über den Reverse-Proxy mit HTTPS freigeben.</p><div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px"><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_aktiv" style="width:auto"> <b>Mitgliederbereich eingeschaltet</b></label></div><p class="hint" style="margin:10px 0 4px"><b>Aussehen, Titel und Texte:</b> ☰ → System &amp; Konto → Oberfläche gestalten → <b>Mitgliederbereich gestalten</b>. Hier: Funktionen, sichtbare Bereiche und buchbare Tarife.</p><label style="margin-top:8px">Sichtbar für Mitglieder</label><div style="display:flex;gap:16px;flex-wrap:wrap"><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_geraete" style="width:auto"> Geräte im WLAN</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_zeige_rechnungen" style="width:auto"> Rechnungen</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_zeige_anfragen" style="width:auto"> Anfragen</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_neue_anfrage" style="width:auto"> Neue Anfrage stellen</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_zugangskarte" style="width:auto"> Zugangskarte anfordern</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_profil" style="width:auto"> Profil: Telefon, Mobil und E-Mail ändern (neue E-Mail mit Code bestätigt)</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_personen" style="width:auto"> Pächter dürfen weitere Personen der Parzelle anlegen</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_geraete_trennen" style="width:auto"> Mitglieder dürfen eigene WLAN-Geräte trennen (mit Bestätigung; keine Sperre – das Gerät kann sich wieder verbinden)</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_geraete_sperren" style="width:auto"> Mitglieder dürfen eigene Geräte sperren und wieder zulassen (Sperre am Gateway, mit Bestätigung)</label></div><div class="knoepfe"><button class="k" onclick="mbTrennenPruefen()" title="Harmloser Test – trennt nichts">Prüfen, ob das Gateway Geräte trennen/sperren zulässt</button></div><div class="log" id="log_mbtr"></div><label style="margin-top:8px">Störungen</label><div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center"><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_stoerung_zeigen" style="width:auto"> Ausfälle (Störungsüberwachung) im Mitgliederbereich, auf seiner Anmeldeseite und in der App hervorgehoben anzeigen</label><label style="display:flex;gap:6px;align-items:center;margin:0">Farbe <input type="color" id="mb_stoerung_farbe" style="width:48px;padding:0;height:30px"></label></div>
<div class="reihe"><div><label for="mb_stoerung_meldung">Meldung je Gerät <small>({geraet} {seit} {ticket} {modell})</small></label><textarea id="mb_stoerung_meldung" rows="2" maxlength="800" style="width:100%;font:inherit"></textarea></div><div><label for="mb_stoerung_text">Eigener Zusatztext <small>(z. B. Ansprechpartner, voraussichtliche Dauer)</small></label><textarea id="mb_stoerung_text" rows="2" maxlength="800" style="width:100%;font:inherit"></textarea></div></div>
<p class="hint" style="margin:2px 0 0">Welche Sparte ein Gerät betrifft, stellst du unter System → Störungsüberwachung ein (Standard: alle Sparten). Angezeigt wird ab dem Zeitpunkt, an dem die Überwachung die Störung meldet (Ticket). Ohne E-Mail-Eingabe zeigt die Anmeldeseite nur Ausfälle, die alle Sparten betreffen.</p>
<label style="margin-top:8px">Tarife</label><div style="display:flex;gap:16px;flex-wrap:wrap"><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_tarifwechsel" style="width:auto"> ⬆ Upgrade jederzeit</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_downgrade" style="width:auto"> ⬇ Kleinerer Tarif als Antrag (Freigabe im Ticket)</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_neubuchung" style="width:auto"> Neu buchen</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="mb_verlaengern" style="width:auto"> Laufzeit verlängern</label></div><label style="margin-top:8px">Im Mitgliederbereich buchbare Tarife <small>(keiner ausgewählt = alle)</small></label><div id="mb_tarife" style="display:flex;gap:16px;flex-wrap:wrap"></div><div class="reihe"><div><label for="mb_modus">Buchen/Wechseln</label><select id="mb_modus" onchange="mbModus()"><option value="anfrage">ohne Bezahlung (Upgrade sofort, Buchen/Verlängern als Antrag)</option><option value="bezahldienst">mit Bezahlung über einen Bezahldienst</option></select></div><div><label for="mb_minuten">Abmelden nach Minuten ohne Aktivität</label><input id="mb_minuten" type="number" min="5" max="240"></div><div><label for="mb_adresse">Öffentliche Adresse (für Rücksprung)</label><input id="mb_adresse" placeholder="https://wlan.meine-sparte.de"></div></div><div id="mb_bezahl" hidden><p class="hint">Der Manager legt einen Zahlungsauftrag (Referenz SN-…) an und leitet das Mitglied zum Bezahldienst. <b>Entweder</b> eine Link-Vorlage mit Platzhaltern {referenz} {betrag} {betrag_cent} {email} {beschreibung} {rueckkehr} {abbruch} (z. B. ein PayPal.me- oder Zahlungslink), <b>oder</b> die Adresse einer eigenen Schnittstelle (z. B. n8n, kleiner Stripe-/Mollie-Dienst): sie bekommt die Daten als JSON (signiert im Kopf X-SparteNet-Signatur) und antwortet mit {"url": "https://…"}. Gebucht wird erst, wenn die Zahlung bestätigt ist: POST <code>/mein/zahlung-webhook</code> mit {"referenz","betrag","status":"bezahlt"} und Kopf <code>X-SparteNet-Signatur: sha256=&lt;HMAC-SHA256 des Inhalts mit dem Geheimnis&gt;</code> – oder über die API: POST /api/v1/ereignis {"ereignis":"zahlung","referenz":"SN-…","betrag":…}.</p><div class="reihe"><div><label for="mb_vorlage">Link-Vorlage</label><input id="mb_vorlage" placeholder="https://…?ref={referenz}&amp;betrag={betrag}"></div><div><label for="mb_api">oder Schnittstelle (Adresse)</label><input id="mb_api" placeholder="https://…"></div></div><p class="hint" id="mb_geheim_info"></p><div class="knoepfe"><button class="k" onclick="mbSpeichern(true)">Webhook-Geheimnis neu erzeugen</button></div><pre id="mb_geheim" hidden style="white-space:pre-wrap;word-break:break-all;background:#fff8e1;padding:8px;border-radius:6px"></pre></div><div class="knoepfe"><button class="k p" onclick="mbSpeichern()">Speichern</button></div><div class="log" id="log_mb"></div><p class="hint" id="mb_versand" style="margin-top:8px"></p><p class="hint" id="mb_apps" style="margin-top:4px"></p><details style="margin-top:8px"><summary>Zahlungsaufträge</summary><div id="mb_auftraege" style="overflow-x:auto"></div></details></div><div class="karte bn-admin" id="apu_karte"><h3>App-Updates</h3><p class="hint">Neue Version der <b>Mitglieder-App</b> oder der <b>Manager-App</b> als APK hochladen. Die Apps melden das Update beim Öffnen, laden die Datei herunter, prüfen die Prüfsumme (SHA-256) und starten die Installation. Android installiert ein Update nur, wenn die APK mit <b>demselben Schlüssel signiert</b> ist wie die installierte App (Release-Build mit dem gleichen Keystore). Versionsnummer und Versionsname liest der Manager selbst aus der APK (jede neu gebaute APK hat automatisch eine höhere Nummer).</p><div id="apu_liste"></div><div class="reihe"><div><label for="apu_art">App</label><select id="apu_art"><option value="mitglied">Mitglieder-App</option><option value="manager">Manager-App</option></select></div><div><label for="apu_vc">versionCode <small>(nur falls nicht lesbar)</small></label><input id="apu_vc" type="number" min="1" placeholder="automatisch"></div><div><label for="apu_vn">Versionsname <small>(optional)</small></label><input id="apu_vn" maxlength="40" placeholder="automatisch"></div></div><label for="apu_hinweis">Hinweis für die Nutzer (optional)</label><input id="apu_hinweis" maxlength="300" placeholder="Was ist neu?"><label for="apu_datei">APK-Datei</label><input id="apu_datei" type="file" accept=".apk,application/vnd.android.package-archive"><div class="knoepfe"><button class="k p" onclick="apuHochladen()">Hochladen</button><button class="k" onclick="apuLaden()">Aktualisieren</button></div><div class="log" id="log_apu"></div></div>
<div class="karte" id="tk_detail" hidden><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1" id="tk_detail_t"></h3><button class="k bn-admin" onclick="tkLoeschen()">Löschen</button><button class="k" onclick="$('tk_detail').hidden=true;TKA=null;tkLaden()">Schließen</button></div>
<div id="tk_felder"></div>
<div id="tk_antwort" style="margin-top:12px"><h3>Antwort oder Notiz</h3><div class="knoepfe" style="margin-top:0"><select id="tk_vorlage" style="max-width:260px" onchange="tkVorlageEinsetzen()"></select></div><div id="tk_re"></div>
<div class="knoepfe"><label id="tk_an_kontakt_l" style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="tk_an_kontakt" style="width:auto"> per E-Mail an den Kontakt senden</label><label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="tk_wartet" style="width:auto"> danach „wartet auf Rückmeldung“</label><button class="k p" onclick="tkAntworten()">Speichern / Senden</button></div></div>
<div class="log" id="log_tkd"></div></div></section>

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
<div class="karte" data-bereich="automationen" id="el_karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">E-Mail-Layout und Vorlagen</h3><button class="k" onclick="elLaden()">Aktualisieren</button></div>
<p class="hint">Alle E-Mails (Automationen, Antworten auf Tickets) bekommen dieses Layout: Kopf mit Logo (aus „Kartendesign“), Farben und Fußzeile. Vorlagen sind fertige Texte mit Platzhaltern – in Regeln und Ticket-Antworten auswählbar.</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;align-items:start"><div>
<h3>Layout</h3><div class="reihe"><div><label for="el_kopf">Kopfzeile</label><input id="el_kopf" maxlength="120"></div><div><label for="el_schrift">Schrift</label><select id="el_schrift"><option>Arial, Helvetica, sans-serif</option><option>Verdana, sans-serif</option><option>Tahoma, sans-serif</option><option>'Segoe UI', Roboto, sans-serif</option><option>Georgia, serif</option></select></div></div>
<div class="reihe"><div><label for="el_fk">Kopf</label><input type="color" id="el_fk"></div><div><label for="el_fkt">Kopf-Schrift</label><input type="color" id="el_fkt"></div><div><label for="el_fa">Akzent</label><input type="color" id="el_fa"></div><div><label for="el_fh">Hintergrund</label><input type="color" id="el_fh"></div><div><label for="el_ft">Text</label><input type="color" id="el_ft"></div></div>
<div class="reihe"><div><label for="el_breite">Breite (px)</label><input id="el_breite" type="number" min="400" max="900"></div><div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="el_logo" style="width:auto"> Logo im Kopf</label><label style="display:flex;gap:8px;align-items:center;margin-top:4px" title="Logo der Sparte des Empfängers (erkannt an der E-Mail-Adresse) neben dem Vereinslogo"><input type="checkbox" id="el_splogo" style="width:auto"> Spartenlogo daneben</label></div><div><label for="el_logoq">Logo</label><div style="display:flex;gap:6px"><select id="el_logoq"></select><button class="k el-schreib" type="button" onclick="elLogoWahl()" title="Aus den Unterlagen wählen">…</button></div></div><div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="el_aktiv" style="width:auto"> HTML-E-Mails mit Layout</label></div></div>
<label for="el_fuss">Fußzeile (Impressum, Kontakt …)</label><textarea id="el_fuss" rows="3" style="width:100%;font:inherit"></textarea>
<div class="knoepfe el-schreib"><button class="k p" onclick="elSpeichern()">Layout speichern</button><input id="el_test_an" placeholder="Test an …" style="max-width:220px"><button class="k bn-admin" onclick="elTest()">Test-E-Mail</button></div>
<h3 style="margin-top:16px">Vorlagen</h3><div class="knoepfe" style="margin-top:0"><select id="ev_wahl" onchange="evWahl()" style="max-width:300px"></select><button class="k el-schreib" onclick="evNeu()">Neue Vorlage</button></div>
<div class="reihe"><div><label for="ev_name">Name der Vorlage</label><input id="ev_name" maxlength="60"></div><div><label for="ev_betreff">Betreff</label><input id="ev_betreff" maxlength="200"></div></div>
<label>Text</label><div id="ev_editor"></div>
<div class="knoepfe el-schreib"><button class="k p" onclick="evSpeichern()">Vorlage speichern</button><button class="k" onclick="evLoeschen()">Vorlage löschen</button></div><div class="log" id="log_el"></div></div>
<div><h3>Vorschau <small style="font-weight:400;color:var(--muted)">(mit Beispieldaten)</small></h3><iframe id="el_vorschau" sandbox="" style="width:100%;height:620px;border:1px solid var(--line);border-radius:8px;background:#fff"></iframe></div></div></div>
<div class="karte bn-admin"><h3>E-Mail-Versand (SMTP)</h3><p class="hint">Postfach, über das die Automationen E-Mails senden (z. B. das Vereins-Postfach beim Provider). Das Passwort wird nicht angezeigt; leer lassen = unverändert. Alternativ als Docker-Secret: <span class="mono">SPARTENET_SMTP_PASSWORD_FILE</span>.</p>
<div class="reihe"><div><label for="sm_host">Server</label><input id="sm_host" placeholder="smtp.example.de"></div><div><label for="sm_port">Port</label><input id="sm_port" inputmode="numeric"></div>
<div><label for="sm_anm">Anmeldung</label><select id="sm_anm"><option value="login">SMTP-Login (Benutzername + Passwort)</option><option value="plain">AUTH PLAIN</option><option value="auto">automatisch</option><option value="keine">keine (nur eigener Mailserver)</option></select></div>
<div><label for="sm_sich">Verschlüsselung</label><select id="sm_sich"><option value="starttls">STARTTLS (Port 587)</option><option value="ssl">SSL/TLS (Port 465)</option><option value="keine">keine (nur im eigenen Netz)</option></select></div></div>
<div class="reihe"><div><label for="sm_ben">Benutzername (leer = Absender-Adresse)</label><input id="sm_ben" autocomplete="off"></div><div><label for="sm_pw">Passwort</label><input id="sm_pw" type="password" autocomplete="new-password"></div>
<div><label for="sm_abs">Absender-Adresse</label><input id="sm_abs" placeholder="wlan@verein.de"></div><div><label for="sm_absn">Absender-Name</label><input id="sm_absn"></div></div>
<div class="knoepfe"><button class="k p" onclick="smSpeichern()">Speichern</button><input id="sm_test_an" placeholder="Test an …" style="max-width:240px"><button class="k" onclick="smTest()">Test-E-Mail senden</button></div><div class="log" id="log_sm"></div></div>
<div class="karte bn-admin" id="wb_karte"><h3>Wochenbericht per E-Mail</h3><p class="hint">Neue Buchungen und Kündigungen, Anfragen, Zahlungseingänge, offene Rechnungen, Störungen und Verträge mit ablaufender Frist – einmal pro Woche.</p>
<div class="reihe"><div><label style="display:flex;gap:8px;align-items:center;margin-top:26px"><input type="checkbox" id="wb_aktiv" style="width:auto"> eingeschaltet</label></div><div><label for="wb_tag">Wochentag</label><select id="wb_tag"></select></div><div><label for="wb_uhr">Uhrzeit</label><input id="wb_uhr" placeholder="07:00"></div><div><label for="wb_an">Empfänger (Komma)</label><input id="wb_an"></div></div>
<div class="knoepfe"><button class="k p" onclick="wbSpeichern(false)">Speichern</button><button class="k" onclick="wbSpeichern(true)">Jetzt senden</button><button class="k" onclick="$('wb_vor').hidden=!$('wb_vor').hidden">Vorschau</button></div><iframe id="wb_vor" sandbox="" hidden style="width:100%;height:520px;border:1px solid var(--line);border-radius:8px;background:#fff;margin-top:10px"></iframe><div class="log" id="log_wb"></div></div>
<div class="karte bn-admin"><h3>API-Schnittstelle für andere Programme</h3><p class="hint">Andere Programme (Buchhaltung, Zahlungseingang, n8n, Zapier, Home Assistant …) melden Ereignisse oder buchen Tarife. Jeder Schlüssel bekommt nur die nötigen Rechte und optional nur bestimmte Sparten. Der Schlüssel wird <b>nur einmal</b> angezeigt und nur als Prüfsumme gespeichert. Höchstens <span id="api_min"></span> Anfragen je Minute und Schlüssel.</p>
<div class="tab" id="api_tab"></div>
<h3>Neuer Schlüssel</h3><div class="reihe"><div><label for="api_name">Name</label><input id="api_name" placeholder="z. B. Buchhaltung"></div><div><label for="api_sp">Nur Sparten (Kürzel, Komma; leer = alle)</label><input id="api_sp"></div></div>
<div id="api_rechte" style="display:flex;gap:16px;flex-wrap:wrap;margin:6px 0"></div>
<div class="knoepfe"><button class="k p" onclick="apiNeu()">Schlüssel erzeugen</button></div><div id="api_neu" hidden class="hinweis" style="margin:8px 0"></div><div class="log" id="log_api"></div>
<details style="margin-top:10px"><summary style="cursor:pointer;font-weight:600">Beispiele</summary><pre class="mono" id="api_bsp" style="white-space:pre-wrap;font-size:12px;background:var(--bg2,#f4f6f2);padding:10px;border-radius:8px"></pre>
<p class="hint">Zahlungsanbieter (Bank, PayPal, Stripe …) senden ihre eigenen Formate – dazwischen übersetzt z. B. n8n, Zapier oder Make die Meldung in einen Aufruf von <span class="mono">/api/v1/ereignis</span>. Der Manager muss dafür von dort erreichbar sein (z. B. über den Reverse-Proxy, nur HTTPS).</p></details></div></section>

<section id="benutzer"><div class="karte"><h2>Mein Konto</h2><div class="kacheln" id="bn_ich"></div>
<div class="tab" id="bn_ich_liste" style="--tab-h:420px"></div>
<div id="bn_ich_pw" data-teil="1"><h3>Eigenes Passwort ändern</h3><div class="reihe" style="max-width:820px"><div><label for="bn_alt">Bisheriges Passwort</label><input id="bn_alt" type="password" autocomplete="current-password"></div>
<div><label for="bn_neu1">Neues Passwort (mind. 12 Zeichen)</label><input id="bn_neu1" type="password" autocomplete="new-password"></div><div><label for="bn_neu2">Neues Passwort wiederholen</label><input id="bn_neu2" type="password" autocomplete="new-password"></div></div>
<div class="knoepfe"><button class="k p" onclick="bnEigenesPw()">Passwort ändern</button></div></div>
<div id="bn_2fa" data-teil="1"><h3>Zwei-Faktor-Anmeldung</h3><p class="hint" id="bn_2fa_st"></p>
<div class="knoepfe"><button class="k p" id="bn_2fa_ein" onclick="zfStart()">Einrichten</button><button class="k" id="bn_2fa_aus" onclick="zfAus()">Ausschalten</button><button class="k" id="bn_2fa_vergessen" onclick="zfVergessen()" title="Alle Browser und Apps, die sich den Code gemerkt haben, fragen beim nächsten Anmelden wieder danach">Gemerkte Geräte vergessen</button></div>
<div id="bn_2fa_neu" hidden><div style="display:flex;gap:18px;flex-wrap:wrap;align-items:center"><div id="bn_2fa_qr" style="width:200px;background:#fff;padding:8px;border:1px solid var(--line);border-radius:8px"></div>
<div><p class="hint">1. QR-Code mit der Authenticator-App scannen (z. B. Google/Microsoft Authenticator, Aegis, 2FAS) – oder den Schlüssel eintippen:<br><b class="mono" id="bn_2fa_geheim"></b></p>
<label for="bn_2fa_code">2. Angezeigten Code eingeben</label><div style="display:flex;gap:8px"><input id="bn_2fa_code" inputmode="numeric" maxlength="6" style="max-width:140px"><button class="k p" onclick="zfBestaetigen()">Bestätigen</button></div></div></div></div>
<div id="bn_2fa_notfall" hidden></div></div>
<div id="bn_app" data-teil="1"><h3>Apps und Geräte</h3><p class="hint">Eine App (z. B. eine eigene Android-App) meldet sich mit Ihrem Benutzernamen und Passwort an (<span class="mono">POST /api/v1/app/anmelden</span>) und bekommt einen eigenen Schlüssel – mit genau Ihren Rechten. Verlorenes Handy? Hier das Gerät entfernen.</p><h4 style="margin:14px 0 4px">App-Zugangstokens</h4><p class="hint">Die App fragt beim Einrichten nach einem Zugangstoken und schickt ihn bei jeder Anfrage mit. Legen Sie beliebig viele an – z. B. einen je Handy oder Tablet – und entfernen Sie einen, wenn ein Gerät verloren geht. Ein Token gilt nur für Ihr Konto, wird nur einmal angezeigt und nur als Prüfsumme gespeichert.</p><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><input id="azt_name" maxlength="60" placeholder="Name, z. B. Handy Peter" style="max-width:260px"><button class="k p" onclick="aztNeu()">Neuen Zugangstoken erzeugen</button><button class="k bn-admin" onclick="aztAlle()">Alle sperren</button></div><div id="azt_neu" hidden style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:8px;background:#fff8e1;padding:8px;border-radius:8px"><input id="azt_wert" readonly class="mono" style="max-width:420px"><button class="k" onclick="navigator.clipboard&&navigator.clipboard.writeText($('azt_wert').value).then(()=>$('log_azt').textContent='✔ Kopiert.')">Kopieren</button></div><div class="tab" id="azt_tab" style="margin-top:8px"></div><div class="log" id="log_azt"></div><h4 style="margin:14px 0 4px">Angemeldete Geräte</h4><div class="tab" id="bn_app_tab"></div><div class="log" id="log_app"></div></div>
<p class="hint" id="bn_admin_hint" hidden>Das Konto „admin“ meldet sich mit dem Manager-Passwort an. Geändert wird es in der Docker-Konfiguration (Secret spartenet_password) – danach den Manager neu starten.</p>
<div class="knoepfe"><button class="k" onclick="abmelden()">Abmelden</button></div><div class="log" id="log_bni"></div></div>
<div class="karte bn-admin"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Benutzerkonten</h3><button class="k" onclick="bnLaden()">Aktualisieren</button></div>
<p class="hint"><b>Administrator</b>: alles, auch Benutzerkonten. <b>Gesperrt</b>: keine Anmeldung, offene Sitzungen enden sofort. <b>Rechte je Bereich</b>: für jedes Arbeitsblatt bzw. jede Funktion einzeln <i>kein Zugriff</i> (ausgeblendet), <i>lesen</i> (ansehen, Vorschau) oder <i>lesen und schreiben</i> (ändern, ans Gateway übertragen) – z. B. alles nur lesen, aber WLAN-Passwörter schreiben und Tarife buchen. „Rechte“ öffnet die Liste; jede Änderung wird sofort gespeichert.</p>
<label style="display:flex;gap:8px;align-items:center;margin:8px 0"><input type="checkbox" id="bn_2fa_pflicht" style="width:auto" onchange="zfPflicht(this.checked)"> Zwei-Faktor-Anmeldung für alle Administratoren verpflichtend</label>
<div class="tab" id="bn_tab" style="--tab-h:900px"></div><div class="log" id="log_bn"></div></div>
<div class="karte bn-admin"><h3>Anmeldung und Sicherheit</h3>
<p class="hint">Gilt für alle Konten. <b>Automatisch abmelden</b>: nach dieser Zeit ohne Aktivität (Maus, Tastatur, Tippen) wird die Sitzung beendet – eine Minute vorher erscheint ein Hinweis. <b>Zwei-Faktor-Code merken</b>: nach richtiger Code-Eingabe fragt dieser Browser bzw. diese App für die gewählte Zeit nicht erneut nach dem Code (Passwort bleibt nötig). Zurücksetzen der Zwei-Faktor-Anmeldung macht gemerkte Geräte ungültig.</p>
<div class="reihe"><div><label for="si_ab">Browser automatisch abmelden</label><select id="si_ab"><option value="0">nie</option><option value="10">nach 10 Minuten</option><option value="15">nach 15 Minuten</option><option value="30">nach 30 Minuten</option><option value="60">nach 1 Stunde</option><option value="120">nach 2 Stunden</option><option value="240">nach 4 Stunden</option><option value="480">nach 8 Stunden</option></select></div>
<div><label for="si_app">Android-App automatisch abmelden</label><select id="si_app"><option value="0">nie</option><option value="15">nach 15 Minuten</option><option value="30">nach 30 Minuten</option><option value="60">nach 1 Stunde</option><option value="240">nach 4 Stunden</option><option value="1440">nach 1 Tag</option><option value="10080">nach 7 Tagen</option></select></div>
<div><label for="si_merk">Zwei-Faktor-Code merken</label><select id="si_merk"><option value="0">nein – immer abfragen</option><option value="8">8 Stunden</option><option value="12">12 Stunden</option><option value="24">1 Tag</option><option value="72">3 Tage</option><option value="168">7 Tage</option><option value="336">14 Tage</option><option value="720">30 Tage</option></select></div></div>
<div class="knoepfe"><button class="k p" onclick="siSpeichernAnmeldung()">Speichern</button></div><div class="log" id="log_sian"></div>
<h3 style="margin-top:18px">App-Zugangstokens</h3><p class="hint">Jeder Benutzer legt seine eigenen Zugangstokens unter <b>Mein Konto → Apps und Geräte</b> an (beliebig viele, z. B. einen je Handy). Dort sehen Sie als Administrator die Tokens aller Konten und können einzelne oder alle sperren.</p></div>
<div class="karte bn-admin"><h3>Neues Benutzerkonto</h3>
<div class="reihe"><div><label for="bn_name">Benutzername</label><input id="bn_name" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="z. B. vorstand.buchenweg"></div>
<div><label for="bn_anz">Name (Anzeige, optional)</label><input id="bn_anz" placeholder="z. B. Maria Muster, Vorstand Buchenweg"></div>
<div><label for="bn_vorlage">Rechte (Vorlage – danach je Bereich anpassbar)</label><select id="bn_vorlage"></select></div>
<div><label for="bn_pw1">Passwort (mind. 12 Zeichen)</label><input id="bn_pw1" type="password" autocomplete="new-password"></div>
<div><label for="bn_pw2">Passwort wiederholen</label><input id="bn_pw2" type="password" autocomplete="new-password"></div></div>
<div class="knoepfe"><button class="k p" onclick="bnAnlegen()">Konto anlegen</button><button class="k" onclick="bnVorschlag()">Passwort vorschlagen</button><span id="bn_vorschlag" class="mono"></span></div><div class="log" id="log_bnn"></div></div>
</section>

<section id="gestaltung">
<div class="karte" data-bereich="gestaltung" id="sl_karte"><h2 style="margin:0 0 6px">Logos</h2><h3 style="margin:10px 0 4px">Manager-Logo</h3><p class="hint">Das Logo des Managers selbst: in der Kopfzeile neben „SparteNet“, auf der Anmeldeseite, der Kontakt-Seite und im Mitgliederbereich (dort beim Logo „Manager-Logo“ wählen) sowie in E-Mails und auf Rechnungen/Zugangskarten, wenn im E-Mail-Layout kein eigenes Logo gewählt ist.</p><div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap"><div style="width:96px;height:96px;display:grid;place-items:center;background:repeating-conic-gradient(#eee 0 25%,#fff 0 50%) 50%/14px 14px;border-radius:10px;overflow:hidden"><img id="ml_bild" alt="" style="max-width:90px;max-height:90px;object-fit:contain" hidden><span class="hint" id="ml_leer">kein Logo</span></div><div><b id="ml_name"></b><div class="knoepfe gs-schreib"><button class="k" onclick="mlWaehlen()">Wählen …</button><button class="k" onclick="mlSetzen('standard')">SparteNet-Symbol</button><button class="k" onclick="mlSetzen('')">Kein Logo</button></div></div></div><div class="log" id="log_ml"></div><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:18px"><h3 style="margin:0;flex:1">Vereinslogos der Sparten</h3><button class="k p gs-schreib" onclick="slErzeugen('',true)">Für alle Sparten ohne Logo erzeugen</button></div><p class="hint">Jede Sparte (jeder Verein) hat ihr eigenes Logo – getrennt vom Manager-Logo. Es erscheint daneben: in E-Mails an Mitglieder (die Sparte wird an der E-Mail-Adresse erkannt), auf Rechnungen und Zugangskarten (PDF), auf gedruckten Zugangskarten und Gast-Vouchern, in der Kopfzeile des Managers, im Mitgliederbereich (sobald die E-Mail eingegeben ist) und in der Mitglieder-App. <b>Automatisch</b> gilt ein Bild aus dem Unterlagen-Ordner „Logos“, das der Sparte zugeordnet ist. <b>Erzeugen</b> zeichnet ein rundes Vereinsabzeichen mit Motiv passend zum Namen und dem Kürzel.</p><div class="tab" id="sl_tab"></div><div class="log" id="log_sl"></div></div>
<div class="karte" data-bereich="gestaltung"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Anmeldeseite gestalten</h2><span class="status" id="gs_login_st"></span></div>
<p class="hint">Texte, Farben, Schrift, Logo und Hintergrundbild der Anmeldeseite. Bilder kommen aus den <b>Unterlagen</b> (am besten Ordner „Logos“). Nur Text – kein eigenes HTML. Rechts die Vorschau.</p>
<div class="gs-raster"><div id="gs_login_form"></div><div class="gs-vor"><div class="knoepfe" style="margin-top:0"><button class="k gs-gr aktiv" data-art="login" data-b="1280">PC</button><button class="k gs-gr" data-art="login" data-b="390">Handy</button></div><div class="gs-rahmen"><iframe id="gs_login_vor" sandbox="allow-scripts" title="Vorschau Anmeldeseite"></iframe></div></div></div>
<div class="knoepfe gs-schreib"><button class="k p" onclick="gsSpeichern('login')">Speichern</button><button class="k" onclick="gsStandard('login')">Standard wiederherstellen</button></div><div class="log" id="log_gs_login"></div></div>
<div class="karte" data-bereich="gestaltung"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Kontakt-Seite gestalten</h2><span class="status" id="gs_portal_st"></span><a class="k" href="/portal" target="_blank" rel="noopener" id="gs_portal_link">Kontakt-Seite öffnen</a></div>
<p class="hint">Aussehen und Texte der öffentlichen Seite <span class="mono">/portal</span>. Einschalten und die einzelnen Funktionen freigeben: <b>Anfragen → Kontakt-Seite</b>. Anfragen als Mitglied gehen nur mit Vorname, Nachname, E-Mail, Sparte und Parzelle, die zu einem gespeicherten Mitglied passen.</p>
<div class="gs-raster"><div id="gs_portal_form"></div><div class="gs-vor"><div class="knoepfe" style="margin-top:0"><button class="k gs-gr aktiv" data-art="portal" data-b="1280">PC</button><button class="k gs-gr" data-art="portal" data-b="390">Handy</button></div><div class="gs-rahmen"><iframe id="gs_portal_vor" sandbox="allow-scripts" title="Vorschau Kontakt-Seite"></iframe></div></div></div>
<div class="knoepfe gs-schreib"><button class="k p" onclick="gsSpeichern('portal')">Speichern</button><button class="k" onclick="gsStandard('portal')">Standard wiederherstellen</button></div><div class="log" id="log_gs_portal"></div></div>
<div class="karte" data-bereich="gestaltung"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Mitgliederbereich gestalten</h2><span class="status" id="gs_mein_st"></span><a class="k" href="/mein" target="_blank" rel="noopener" id="gs_mein_link">Mitgliederbereich öffnen</a></div>
<p class="hint">Aussehen und Texte des Mitgliederbereichs <span class="mono">/mein</span> (Anmeldung mit Einmalcode, Tarif, Geräte, Rechnungen, Anfragen). Solange hier nichts gespeichert ist, sieht er aus wie die Kontakt-Seite. Einschalten und Funktionen (Tarife, Bezahlung, sichtbare Bereiche): <b>Anfragen → Mitgliederbereich</b>. Die Vorschau zeigt Anmeldung und Beispieldaten.</p>
<div class="gs-raster"><div id="gs_mein_form"></div><div class="gs-vor"><div class="knoepfe" style="margin-top:0"><button class="k gs-gr aktiv" data-art="mein" data-b="1280">PC</button><button class="k gs-gr" data-art="mein" data-b="390">Handy</button></div><div class="gs-rahmen"><iframe id="gs_mein_vor" sandbox="allow-scripts" title="Vorschau Mitgliederbereich"></iframe></div></div></div>
<div class="knoepfe gs-schreib"><button class="k p" onclick="gsSpeichern('mein')">Speichern</button><button class="k" onclick="gsStandard('mein')">Standard wiederherstellen</button></div><div class="log" id="log_gs_mein"></div></div>
<div class="karte" data-bereich="gestaltung"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Menü und Ansichtsprofile</h2></div>
<p class="hint">Jedes Profil hat einen eigenen Menübaum: <b>Bereiche</b> (1), <b>Reiter</b> (1.1) und <b>Karten</b> auf der Seite (1.1.1) umbenennen, mit ↑ ↓ sortieren, ausblenden; bei Karten auch den Hinweistext ändern und „eingeklappt“ zeigen. Die Kennnummer (B…, R…, K…) bleibt immer gleich. Unten jedem Konto ein Profil zuweisen. <b>Ausblenden ist nur Ansicht</b> – was ein Konto darf, regeln weiter die Rechte. „Mein Konto“ und „Eigenes Passwort ändern“ bleiben immer sichtbar. Notausgang: Adresse mit <span class="mono">#standardansicht</span> öffnen.</p>
<div class="reihe"><div><label for="ap_wahl">Profil</label><select id="ap_wahl" onchange="apWahl(this.value)"></select></div>
<div><label for="ap_std">Standard für Konten ohne Profil</label><select id="ap_std"></select></div></div>
<div class="knoepfe gs-schreib"><button class="k" onclick="apNeu(false)">+ Neues Profil</button><button class="k" onclick="apNeu(true)">Kopieren</button><button class="k" onclick="apUmbenennen()">Umbenennen</button><button class="k" onclick="apLoeschen()">Löschen</button><button class="k" onclick="apZurueck()">Menübaum auf Standard</button><button class="k" onclick="apExport()">Export</button><label class="k" style="margin:0;cursor:pointer">Import …<input type="file" accept=".json,application/json" style="display:none" onchange="apImport(this)"></label></div>
<div id="ap_baum" class="ap-baum"></div>
<div class="knoepfe gs-schreib"><button class="k" onclick="apBereichNeu()">+ Bereich</button></div>
<h3 style="margin-top:18px">Konten und Profile</h3><div class="tab" id="ap_konten"></div>
<div class="knoepfe gs-schreib"><button class="k p" onclick="apSpeichern()">Profile und Zuordnung speichern</button><button class="k" onclick="apVorschau()">Vorschau in diesem Fenster</button></div><div class="log" id="log_ap"></div></div>
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
const TABS=[["start","Start"],["verbindung","Verbindung"],["lesen","Auslesen"],["planung","Planung"],["abgleich","Abgleich"],["einrichten","Einrichten"],["uebertragen","Übertragen"],["tarife","Tarife"],["kalkulation","Kalkulation"],["netzplanung","Netzplanung"],["kartendesign","Kartendesign"],["voucher","Gast-Voucher"],["system","Systeminfo"],["daten","Alle Daten"],["unterlagen","Unterlagen"],["mitglieder","Mitglieder"],["rechnungen","Rechnungen"],["tickets","Tickets"],["automationen","Automationen"],["benutzer","Benutzer"],["gestaltung","Oberfläche gestalten"],["hilfe","Hilfe"]];
const $=id=>document.getElementById(id);const nav=$("nav");TABS.forEach(([id,t])=>{const b=document.createElement("button");b.textContent=t;b.onclick=()=>zeige(id);b.id="n_"+id;nav.appendChild(b)});
function zeige(id){if(!reiterErlaubt(id))id=startReiter();rechteHinweis(id);if(id=="start"&&!$("st_k").innerHTML&&typeof EINST!="undefined"&&EINST.konsole_id)startLaden().catch(()=>{});if(id=="verbindung")fernLaden().catch(()=>{});if(location.hash!="#"+id)history.replaceState(null,"","#"+id);setTimeout(()=>{const b=document.querySelector("nav button.aktiv");if(b&&b.scrollIntoView)b.scrollIntoView({inline:"center",block:"nearest"})},0);if(id=="kalkulation"&&!KK)kkLaden().catch(()=>{});if(id=="netzplanung"&&!GP)gpLaden().catch(()=>{});if(id=="netzplanung")ztLaden().catch(()=>{});if(id=="benutzer")bnStart();if(id=="unterlagen")ulLaden().catch(()=>{});if(id=="voucher"&&!VV)vvLaden().catch(()=>{});if(id=="automationen")auLaden().catch(()=>{});if(id=="mitglieder"){mgLaden().catch(()=>{});vtLaden().catch(()=>{});rsLaden().catch(()=>{})}if(id=="tickets"){tkLaden().catch(()=>{});if(ICH.admin){poLaden().catch(()=>{});mbLaden().catch(()=>{})}}if(id=="rechnungen")reLaden().catch(()=>{});if(id=="start")ueLaden().catch(()=>{});if(id=="system")owLaden().catch(()=>{});if(id=="system"&&ICH.admin){upLaden(true).catch(()=>{});siLaden().catch(()=>{})}if(id=="kartendesign"&&!DESIGN)designLaden();if(id=="gestaltung")gsLaden().catch(()=>{});if(id=="tarife"&&!TF)tfLaden();if(id=="tarife"&&bereichStufe("buchungen")!="kein")lzLaden().catch(()=>{});if(id=="system"&&!SYS)sysLaden();if(id=="daten"&&!DLISTE)datenListe();document.querySelectorAll("section").forEach(s=>s.classList.toggle("aktiv",s.id==id));document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("aktiv",b.id=="n_"+id));if(typeof navAktualisieren=="function")navAktualisieren(id)}
async function api(pfad,body,logid){const el=logid&&$(logid);const kn=[...document.querySelectorAll("button")].filter(b=>!b.disabled);kn.forEach(b=>b.disabled=true);if(el)el.textContent="… bitte warten (über die Cloud kann das einige Sekunden dauern)";
 try{const r=await fetch(pfad,{method:body===undefined?"GET":"POST",headers:{"X-Token":T,"Content-Type":"application/json"},body:body===undefined?undefined:(body instanceof Blob?body:JSON.stringify(body))});
 if(r.status==401){location.replace(typeof AB_MIN!="undefined"&&AB_MIN>0?"/?abgemeldet=zeit":"/");return new Promise(()=>{})}const d=await r.json().catch(()=>({}));if(d.zweiter_faktor_fehlt&&typeof zeige=="function"&&!document.querySelector("#benutzer.aktiv"))zeige("benutzer");if(r.status==403&&!d.recht){location.reload();return new Promise(()=>{})}if(!r.ok)throw new Error(d.fehler||r.status);if(el)el.textContent=d.log?d.log.join("\n"):"";return d}
 catch(e){if(el)el.innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>';throw e}finally{kn.forEach(b=>b.disabled=false)}}
function esc(s){return String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
// Enter in einem Eingabefeld bestätigt: löst den nächsten Hauptknopf (grün) im selben Block aus – Felder mit eigener Enter-Funktion, Suchfelder und Mehrzeiliges ausgenommen
document.addEventListener("keydown",e=>{if(e.key!=="Enter"||e.isComposing||e.defaultPrevented||e.shiftKey||e.altKey)return;const el=e.target;
 if(!el||el.tagName!=="INPUT"||["checkbox","radio","file","button","submit","reset","color","range","search"].includes(el.type)||el.readOnly)return;
 if(el.hasAttribute("onkeydown")||el.hasAttribute("oninput")||el.closest("form")||el.dataset.keinEnter!==undefined)return;
 const box=el.closest("details,.karte,[data-teil],dialog,.modal");if(!box)return;
 const kn=[...box.querySelectorAll("button.k.p,button.los")].filter(b=>!b.disabled&&b.offsetParent!==null&&b.closest("details,.karte,[data-teil],dialog,.modal")===box);if(!kn.length)return;
 const nach=kn.find(b=>el.compareDocumentPosition(b)&Node.DOCUMENT_POSITION_FOLLOWING);e.preventDefault();(nach||kn[kn.length-1]).click()});
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
function ssid(){if(!PLAN)return;const kz=$("ein_sp").value,s=PLAN.sparten.find(x=>x.kz==kz);if(!s)return;const w=s.wlan||{};$("ssid1").textContent=w.paechter||"";$("ssid2").textContent=w.gaeste||"";$("ssid3").textContent=w.vorstand||"";
 $("ssid_eigen").textContent=w.eigen?" (vom Gateway zugeordnet)":" (Namen nach Schema)";if($("wl_wahl"))$("wl_wahl").hidden=true;if($("log_wl"))$("log_wl").textContent=""}
let WL=null;
async function wlAbrufen(){const kz=$("ein_sp").value;const d=await api("/api/wlans?sparte="+encodeURIComponent(kz),undefined,"log_wl");WL=d;
 const opt=(art,sel)=>'<option value="">– nach Schema –</option>'+d.wlans.map(w=>`<option value="${esc(w.name)}"${w.name==sel?" selected":""}>${esc(w.name)}${w.ppsk?" · PPSK, "+w.schluessel+" Schlüssel"+(w.eigene?" ("+w.eigene+" dieser Sparte)":""):""}${w.gast?" · Gast/Hotspot":""}${w.aktiv?"":" · aus"}</option>`).join("");
 $("wl_p").innerHTML=opt("paechter",d.vorschlag.paechter);$("wl_g").innerHTML=opt("gaeste",d.vorschlag.gaeste);$("wl_v").innerHTML=opt("vorstand",d.vorschlag.vorstand);$("wl_wahl").hidden=false;
 const geaendert=["paechter","gaeste","vorstand"].filter(a=>d.vorschlag[a]&&d.vorschlag[a]!=d.zuordnung[a]);
 $("log_wl").textContent=d.log.join("\n")+(geaendert.length?"\nVorschlag vorausgewählt – bitte prüfen und „Zuordnung speichern“.":"")}
async function wlSpeichern(){const kz=$("ein_sp").value;await api("/api/wlan-zuordnung",{sparte:kz,paechter:$("wl_p").value,gaeste:$("wl_g").value,vorstand:$("wl_v").value},"log_wl");const l=$("log_wl").textContent;PLAN=null;await planLaden(true);$("ein_sp").value=kz;ssid();$("log_wl").textContent=l}
async function wlSchema(){if(!confirm("WLAN-Namen dieser Sparte wieder nach Schema verwenden?"))return;const kz=$("ein_sp").value;await api("/api/wlan-zuordnung",{sparte:kz},"log_wl");const l=$("log_wl").textContent;PLAN=null;await planLaden(true);$("ein_sp").value=kz;ssid();$("log_wl").textContent=l}
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
 ["Logo",[["_logo",""],["logo_ort","Platz","sel",[["oben","Oben"],["unten","Unten (über der Fußzeile)"]]],["logo_pos","Ausrichtung","sel",[["center","Mittig"],["left","Links"],["right","Rechts"]]],["logo_mm","Breite","rng",5,180,1,"mm"],["sparten_logo","Spartenlogo daneben (aus „Oberfläche gestalten → Spartenlogos“)","chk"]]],
 ["Rahmen",[["rahmen","Rahmen anzeigen","chk"],["rahmen_mm","Stärke","rng",.2,5,.1,"mm"],["rahmen_radius","Ecken-Rundung","rng",0,20,1,"mm"],["farbe_rahmen","Rahmenfarbe","col"]]]];
function kdFeld([k,l,t,a,b,c,e]){const id="kd_"+k;
 if(k=="_hint")return `<p class="hint" style="margin:6px 0 2px">${esc(l)}</p>`;
 if(k=="_logo")return `<div class="feld"><label>Logo (PNG, JPG, SVG, WEBP · max. 2 MB, transparentes PNG empfohlen)</label></div><img id="kd_logo_mini" class="logo-mini" alt="" style="display:none">
  <div class="knoepfe" style="margin-top:8px"><label class="k" style="margin:0;color:var(--navy);cursor:pointer">Logo hochladen …<input type="file" id="kd_logo" accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml,.svg" onchange="logoHoch()" style="display:none"></label><button class="k" onclick="logoAusUnterlagen()">Aus Unterlagen wählen …</button><button class="k" onclick="logoWeg()">Logo entfernen</button></div><p class="hint" style="margin:6px 0 0">Hochgeladene Logos (PNG, JPG, GIF, WEBP) werden zusätzlich unter <b>Unterlagen → Logos</b> abgelegt. Dort können Sie weitere Logos ablegen und hier auswählen.</p>`;
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
async function logoHoch(){const f=$("kd_logo").files[0];if(!f)return;const d=await api("/api/logo?name="+encodeURIComponent(f.name),f,"log_kd");logoMini(d.logo_uri);$("kd_logo").value="";vorschau()}
/* Logo-Auswahl aus den Unterlagen: Vorschaubilder werden mit Token geladen (Blob-URLs) */
let LGB={};
async function logoBlob(id){if(LGB[id])return LGB[id];const r=await fetch("/api/logo-bild?id="+encodeURIComponent(id),{headers:{"X-Token":T}});if(!r.ok)throw new Error("Bild nicht ladbar");LGB[id]=URL.createObjectURL(await r.blob());return LGB[id]}
async function logoWahlFenster(titel,aktuell,ohneText){const d=await api("/api/logos");return new Promise(fertig=>{const o=document.createElement("div");
 o.style.cssText="position:fixed;inset:0;z-index:9998;background:rgba(10,20,15,.55);display:grid;place-items:center;padding:16px";
 o.innerHTML=`<div style="background:var(--card,#fff);color:var(--text);border-radius:14px;padding:18px;max-width:760px;width:100%;max-height:86vh;overflow:auto;box-shadow:0 18px 50px rgba(0,0,0,.35)"><div style="display:flex;gap:10px;align-items:center"><h3 style="margin:0;flex:1">${esc(titel)}</h3><button class="k" id="lg_zu">Schließen</button></div>
 <p class="hint">Bilder aus den Unterlagen (PNG, JPG, GIF, WEBP bis 2 MB) – Ordner „${esc(d.ordner)}“ zuerst. Neue Logos unter <b>Unterlagen</b> in den Ordner „${esc(d.ordner)}“ hochladen.</p>
 <div id="lg_raster" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px">${ohneText?`<button class="k" data-id="" style="height:150px;white-space:normal">${esc(ohneText)}</button>`:""}${d.logos.map(x=>`<button class="k" data-id="${esc(x.id)}" title="${esc(x.ordner+" / "+x.name)}" style="height:150px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;padding:8px;${x.id==aktuell?"outline:3px solid var(--green);":""}"><span style="flex:1;display:flex;align-items:center;justify-content:center;width:100%;background:repeating-conic-gradient(#eee 0 25%,#fff 0 50%) 50%/14px 14px;border-radius:6px;overflow:hidden"><img data-lg="${esc(x.id)}" alt="" style="max-width:100%;max-height:96px;object-fit:contain"></span><small style="max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(x.name)}</small></button>`).join("")}</div>
 ${d.logos.length?"":'<p class="hint">Noch keine Bilder in den Unterlagen.</p>'}</div>`;
 document.body.appendChild(o);const zu=w=>{o.remove();fertig(w)};$("lg_zu").onclick=()=>zu(null);o.onclick=e=>{if(e.target===o)zu(null)};
 o.querySelectorAll("#lg_raster button").forEach(b=>b.onclick=()=>zu(b.dataset.id));
 o.querySelectorAll("img[data-lg]").forEach(i=>logoBlob(i.dataset.lg).then(u=>i.src=u).catch(()=>{}))})}
async function logoAusUnterlagen(){const id=await logoWahlFenster("Logo für die Zugangskarten",null);if(!id)return;const d=await api("/api/logo-waehlen",{id},"log_kd");logoMini(d.logo_uri);vorschau()}
async function logoWeg(){if(!confirm("Logo entfernen?"))return;await api("/api/logo-loeschen",{},"log_kd");logoMini("");vorschau()}
let SYS=null,SYST=null,DLISTE=null,DAKT=null,DDATEN=null,DANS="tab";
const mbit=b=>b==null||b===""?"–":(b>=1e6?(b/1e6).toFixed(b>=1e8?0:1)+" Mbit/s":(b/1e3).toFixed(0)+" kbit/s");
const kbit=k=>k==null?"–":(k>=1e6?(k/1e6).toLocaleString("de-DE",{maximumFractionDigits:1})+" Gbit/s":k>=1000?(k/1000).toLocaleString("de-DE",{maximumFractionDigits:k>=100000?0:1})+" Mbit/s":Math.round(k)+" kbit/s");
const bytes=b=>!b?"0 B":b>=1e9?(b/1e9).toFixed(2)+" GB":b>=1e6?(b/1e6).toFixed(1)+" MB":(b/1e3).toFixed(0)+" kB";
const dauer=s=>{if(s==null||s==="")return"–";s=+s;const t=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);return t?t+" T "+h+" h":h?h+" h "+m+" min":m+" min"};
const zahl=(v,n=1)=>v==null||v===""?"–":(+v).toFixed(n).replace(".",",");
function balkenProzent(p){if(p==null||p==="")return"–";const k=p>=85?"s":p>=60?"w":"";return `<div class="balken"><i class="${k}" style="width:${Math.min(100,p)}%"></i><span>${zahl(p,0)} %</span></div>`}
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
  ["CPU",r=>balkenProzent(r.cpu)],["RAM",r=>balkenProzent(r.ram)],["Last",r=>zahl(r.load,2)],["Laufzeit",r=>dauer(r.uptime)],["↓ Uplink",r=>mbit(r.rx_bps)],["↑ Uplink",r=>mbit(r.tx_bps)],
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
const ANS_STD={breite:1200,zoom:0,tabh:520,spalten:false,kd:430,dl:270,reiter:false};let ANS={...ANS_STD},ANST=null;
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
 $("an_spalten").checked=!!ANS.spalten;$("an_reiter").checked=!!ANS.reiter;$("menue_reiter").checked=!!ANS.reiter;if(typeof navAktualisieren=="function")navAktualisieren();if(typeof SYS!="undefined"&&SYS&&$("system").classList.contains("aktiv"))window.dispatchEvent(new Event("resize"))}
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
 $("vg_k").innerHTML=kachel("Netze fehlen",d.netze.length,d.netze.length?"warn":"gut")+kachel("Passwörter neu",z("neu"),z("neu")?"warn":"gut")+kachel("Passwörter geändert",z("geaendert"),z("geaendert")?"warn":"gut")+kachel("Zugang entfernen",z("entfernen"),z("entfernen")?"schlecht":"gut")+kachel("aktuell",d.gleich,"gut")+(z("netz_fehlt")?kachel("Netz fehlt (Passwort wartet)",z("netz_fehlt"),"warn"):"");
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
function tfZeigen(){$("tf_tab").innerHTML="<tr><th>Tarif</th><th>Download Mbit/s</th><th>Upload Mbit/s</th><th>Preis €/Jahr</th><th>Netzmaske</th><th>Endgeräte</th><th title='0 = unbegrenzt. Mit Laufzeit endet der Zugang nach dieser Zeit (Karte „Laufzeiten und Zugang“)'>Laufzeit</th><th>ergibt</th><th></th></tr>"+TFL.map((t,i)=>{const b=tfBereich(t.praefix,t.geraete);
 return `<tr><td><input class="tf_in" data-i="${i}" data-k="name" value="${esc(t.name)}" style="min-width:90px"></td><td><input class="tf_in" type="number" min="0.1" step="any" data-i="${i}" data-k="down" value="${esc(t.down)}" style="width:90px"></td><td><input class="tf_in" type="number" min="0.1" step="any" data-i="${i}" data-k="up" value="${esc(t.up)}" style="width:90px"></td><td><input class="tf_in" type="number" min="0" step="any" data-i="${i}" data-k="preis" value="${esc(t.preis??0)}" style="width:90px" title="${t.preis?(t.preis/12).toLocaleString("de-DE",{maximumFractionDigits:2})+" € im Monat":""}"></td>
 <td><select class="tf_in" data-i="${i}" data-k="praefix">${[24,25,26,27,28,29,30].map(p=>`<option value="${p}"${p==t.praefix?" selected":""}>/${p} · ${tfMaske(p)}</option>`).join("")}</select></td>
 <td><input class="tf_in" type="number" min="0" data-i="${i}" data-k="geraete" value="${esc(t.geraete)}" style="width:80px"></td>
 <td><div style="display:flex;gap:4px;min-width:170px"><input class="tf_in" type="number" min="0" step="1" data-i="${i}" data-k="laufzeit" value="${esc(t.laufzeit||0)}" style="width:64px;flex:none" title="0 = unbegrenzt"><select class="tf_in" data-i="${i}" data-k="laufzeit_einheit" data-text="1" style="width:auto;flex:1;min-width:96px">${[["stunden","Stunden"],["tage","Tage"],["wochen","Wochen"],["monate","Monate"]].map(([k,v])=>`<option value="${k}"${k==(t.laufzeit_einheit||"tage")?" selected":""}>${v}</option>`).join("")}</select></div></td><td class="tf_erg" data-i="${i}">${b.fehler?'<span class="fehler">'+esc(b.fehler)+"</span>":esc(b.text)}</td>
 <td><button class="k" onclick="tfWeg(${i})" title="Tarif entfernen">✕</button></td></tr>`}).join("");
 document.querySelectorAll(".tf_in").forEach(e=>e.oninput=e.onchange=()=>{const t=TFL[e.dataset.i];t[e.dataset.k]=(e.dataset.k=="name"||e.dataset.text)?e.value:e.value===""?"":+e.value;const b=tfBereich(t.praefix,t.geraete);
  document.querySelector(`.tf_erg[data-i="${e.dataset.i}"]`).innerHTML=b.fehler?'<span class="fehler">'+esc(b.fehler)+"</span>":esc(b.text)})}
function tfModusHint(){$("tf_modus_hint").textContent=$("tf_modus").value=="tarif"?"Wie in UniFi unter Einstellungen → QoS: eine Regel „SparteNet-Tarif-Basic“ mit allen Basic-Netzen. Bitte einmal prüfen, ob das Limit dann für jedes Netz einzeln oder für alle zusammen gilt (Geschwindigkeitstest in zwei Basic-Parzellen gleichzeitig). Teilen sich alle die Bandbreite, „eine Regel je Netz“ wählen.":"Jede Parzelle bekommt eine eigene Regel „SparteNet-Netz-BW-Paz.067“ – die Bandbreite ist sicher je Parzelle getrennt, dafür gibt es viele Regeln."}
/* ---- Oberfläche gestalten: Anmeldeseite, Kontakt-Seite, Ansichtsprofile ---- */
let GS=null;const GSD={login:null,portal:null,mein:null},GST={},GSB={login:1280,portal:1280,mein:1280};
const GS_FELDER={
 login:[["Aufbau",[["layout","Aufbau","sel",[["geteilt","Zweigeteilt – Fläche/Bild links, Anmeldung rechts"],["mittig","Anmeldekarte in der Mitte"]]],["schrift","Schrift","schrift"],["ecken","Ecken-Rundung (px)","zahl",0,32],["dunkel","Dunkelmodus erlauben (folgt dem Gerät)","chk"]]],
  ["Marke, Logo und Bild",[["marke","Name (Marke)","txt"],["marke_hervor","Hervorgehobener Teil des Namens","txt"],["logo","Logo","bild",1],["spartenlogos","Vereinslogos der Sparten neben dem Manager-Logo zeigen","chk"],["hintergrund","Hintergrundbild","bild"],["abdunkeln","Bild abdunkeln (%)","zahl",0,90]]],
  ["Farben",[["farbe_marke1","Fläche links – oben","farbe"],["farbe_marke2","Fläche links – unten","farbe"],["farbe_glanz","Lichtschein links unten","farbe"],["farbe_knopf","Knopf und Akzent","farbe"],["farbe_grund","Seitenhintergrund","farbe"],["farbe_karte","Anmeldekarte","farbe"],["farbe_text","Schrift","farbe"]]],
  ["Texte",[["ueberschrift","Überschrift (links)","txt"],["untertitel","Untertitel (links)","area"],["punkte","Punkte links – eine Zeile je Punkt, höchstens 6","liste"],["titel","Titel der Anmeldekarte","txt"],["text","Text der Anmeldekarte","area"],["fuss","Zusätzlicher Hinweis unten","area"],["kontakt","Kontakt bei Problemen","txt"]]],
  ["Links",[["impressum","Impressum (https://…)","txt"],["datenschutz","Datenschutz (https://…)","txt"],["portal_link","Link zur Kontakt-Seite zeigen (wenn eingeschaltet)","chk"]]]],
 portal:[["Aufbau",[["schrift","Schrift","schrift"],["ecken","Ecken-Rundung (px)","zahl",0,32],["breite","Breite des Inhalts (px)","zahl",480,1100],["dunkel","Dunkelmodus erlauben (folgt dem Gerät)","chk"],["reihenfolge","Reihenfolge der Funktionen","reihe"]]],
  ["Marke, Logo und Bild",[["marke","Name im Kopf","txt"],["marke_hervor","Hervorgehobener Teil","txt"],["logo","Logo","bild",0],["spartenlogos","Logos aller Sparten unten zeigen","chk"],["hintergrund","Hintergrundbild","bild"],["abdunkeln","Bild abdunkeln (%)","zahl",0,90]]],
  ["Farben",[["farbe_kopf","Kopfzeile","farbe"],["farbe_kopf_text","Schrift in der Kopfzeile","farbe"],["farbe_knopf","Knöpfe und Akzent","farbe"],["farbe_grund","Seitenhintergrund","farbe"],["farbe_karte","Karten","farbe"],["farbe_text","Schrift","farbe"]]],
  ["Texte",[["titel","Titel","txt"],["text","Einleitung","area"],["t_ticket","Name: Anfrage","txt"],["h_ticket","Hinweis: Anfrage","area"],["t_status","Name: Stand abfragen","txt"],["h_status","Hinweis: Stand abfragen","area"],["t_zugang","Name: Zugangskarte","txt"],["h_zugang","Hinweis: Zugangskarte","area"],["danke","Danke-Text ({nr} = Ticket-Nummer)","txt"]]],
  ["Anfragen",[["t_mitglied","Auswahl: Mitglied","txt"],["art_kein_mitglied","Auch Nicht-Mitglieder dürfen anfragen","chk"],["t_kein_mitglied","Auswahl: kein Mitglied","txt"],["art_interessent","Auch Interessenten dürfen anfragen","chk"],["t_interessent","Auswahl: Interessent","txt"],["spamschutz","Spamschutz: kleine Rechenaufgabe vor dem Absenden","chk"]]],
  ["Kontakt und Links",[["kontakt","Kontakt (z. B. Vorstand, E-Mail, Telefon)","txt"],["fuss","Zusätzlicher Text unten","area"],["impressum","Impressum (https://…)","txt"],["datenschutz","Datenschutz (https://…)","txt"]]]],
 mein:[["Aufbau",[["schrift","Schrift","schrift"],["ecken","Ecken-Rundung (px)","zahl",0,32],["breite","Breite des Inhalts (px)","zahl",480,1100],["dunkel","Dunkelmodus erlauben (folgt dem Gerät)","chk"]]],
  ["Marke, Logo und Bild",[["marke","Name im Kopf","txt"],["marke_hervor","Hervorgehobener Teil","txt"],["logo","Logo (Manager/Verein)","bild",0],["vereinslogo","Vereinslogo der Sparte daneben – erscheint, sobald die E-Mail-Adresse eingegeben ist","chk"],["hintergrund","Hintergrundbild","bild"],["abdunkeln","Bild abdunkeln (%)","zahl",0,90]]],
  ["Farben",[["farbe_kopf","Kopfzeile","farbe"],["farbe_kopf_text","Schrift in der Kopfzeile","farbe"],["farbe_knopf","Knöpfe und Akzent","farbe"],["farbe_grund","Seitenhintergrund","farbe"],["farbe_karte","Karten","farbe"],["farbe_text","Schrift","farbe"]]],
  ["Texte",[["titel","Titel (Kopfzeile, Browser-Tab, App)","txt"],["text_anmeldung","Text auf der Anmeldung (leer = Standardtext)","area"],["hinweis","Hinweis oben nach der Anmeldung","area"]]],
  ["Kontakt und Links",[["kontakt","Kontakt (z. B. Vorstand, E-Mail, Telefon)","txt"],["fuss","Zusätzlicher Text unten","area"],["impressum","Impressum (https://…)","txt"],["datenschutz","Datenschutz (https://…)","txt"]]]]};
const GS_FUNK={ticket:"Anfrage",status:"Stand abfragen",zugang:"Zugangskarte"};
function gsDarf(){return ICH.admin||ICH.bereiche.gestaltung=="schreiben"}
let SPL=null;
async function slLaden(){mlLaden();try{SPL=await api("/api/sparten-logos",undefined,"log_sl");slZeigen(SPL)}catch(e){}}
let ML=null;
async function mlLaden(){try{mlZeigen(await api("/api/manager-logo",undefined,"log_ml"))}catch(e){}}
function mlZeigen(d){ML=d;$("ml_name").textContent=d.logo?d.name:"Kein Logo";$("ml_bild").hidden=!d.src;$("ml_leer").hidden=!!d.src;if(d.src)$("ml_bild").src=d.src;
 const k=document.querySelector(".mlogo-kopf");if(k&&d.src)k.src=d.src;if(k)k.hidden=!d.src}
async function mlWaehlen(){const id=await logoWahlFenster("Manager-Logo wählen",ML&&ML.logo,"");if(id===null||id==="")return;mlSetzen(id)}
async function mlSetzen(logo){mlZeigen(await api("/api/manager-logo",{logo},"log_ml"))}
function slZeigen(d){SPL=d;const w=bereichStufe("gestaltung")=="schreiben";
 $("sl_tab").innerHTML=d.sparten.length?"<table><tr><th>Sparte</th><th>Logo</th><th></th><th></th></tr>"+d.sparten.map(z=>`<tr><td><b>${esc(z.name)}</b><br><small>${esc(z.sparte)}</small></td>
  <td style="width:90px">${z.logo?`<img data-sl="${esc(z.logo)}" alt="" style="height:64px;width:auto;max-width:120px;object-fit:contain">`:'<span class="hint">–</span>'}</td>
  <td>${z.logo?esc(z.logo_name)+"<br><small>"+(z.automatisch?"automatisch (Ordner „Logos“, Sparte "+esc(z.sparte)+")":"ausgewählt")+"</small>":(z.wahl=="-"?"<small>ausgeschaltet</small>":"<small>kein Logo</small>")}</td>
  <td>${w?`<div class="knoepfe" style="margin:0"><button class="k" data-sp="${esc(z.sparte)}" onclick="slWaehlen(this.dataset.sp)">Wählen …</button><button class="k" data-sp="${esc(z.sparte)}" onclick="slErzeugen(this.dataset.sp)">Erzeugen</button>${z.logo?`<button class="k" data-sp="${esc(z.sparte)}" onclick="slSetzen(this.dataset.sp,'-')">Keins</button>`:z.wahl=="-"?`<button class="k" data-sp="${esc(z.sparte)}" onclick="slSetzen(this.dataset.sp,'')">Automatisch</button>`:""}</div>`:""}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Noch keine Sparten angelegt.</p>';
 document.querySelectorAll("img[data-sl]").forEach(i=>logoBlob(i.dataset.sl).then(u=>i.src=u).catch(()=>{}))}
async function slWaehlen(kz){const z=SPL.sparten.find(x=>x.sparte==kz);const id=await logoWahlFenster("Logo für "+(z?z.name:kz),z?z.logo:"","Automatisch (Bild im Ordner „Logos“ mit dieser Sparte)");if(id===null)return;slSetzen(kz,id)}
async function slSetzen(kz,logo){slZeigen(await api("/api/sparten-logos",{sparte:kz,logo},"log_sl"))}
async function slErzeugen(kz,alle){const z=SPL&&SPL.sparten.find(x=>x.sparte==kz);if(!alle&&z&&z.logo&&!confirm("Für "+z.name+" ein neues Logo erzeugen und statt des jetzigen verwenden? (Das alte bleibt in den Unterlagen.)"))return;
 slZeigen(await api("/api/sparten-logo-erzeugen",alle?{alle:true}:{sparte:kz},"log_sl"))}
async function gsLaden(){slLaden();GS=await api("/api/gestaltung");["login","portal","mein"].forEach(a=>{GSD[a]=JSON.parse(JSON.stringify(GS[a]));gsForm(a);gsVorschau(a)});
 document.querySelectorAll(".gs-schreib").forEach(e=>e.hidden=!gsDarf());$("gs_portal_link").hidden=!GS.portal_aktiv;$("gs_mein_link").hidden=!GS.mein_aktiv;apStart()}
function gsBildOpt(art,k,std){return(k=="logo"?'<option value="manager">Manager-Logo (Karte „Logos“)</option>':"")+(std?'<option value="standard">SparteNet-Symbol</option>':"")+'<option value="">– kein Bild –</option>'+GS.logos.map(x=>`<option value="${esc(x.id)}">${esc(x.ordner+" / "+x.name)}</option>`).join("")}
function gsForm(art){const D=GSD[art],id=k=>`gs_${art}_${k}`;
 $("gs_"+art+"_form").innerHTML=GS_FELDER[art].map(([g,fs],gi)=>`<details class="gs-gruppe"${gi<2?" open":""}><summary>${esc(g)}</summary>`+fs.map(([k,l,t,a,b])=>{const v=D[k];
  if(t=="chk")return `<div class="gs-f"><label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="${id(k)}" data-k="${k}" style="width:auto"${v?" checked":""}> ${esc(l)}</label></div>`;
  if(t=="farbe")return `<div class="gs-f gs-zeile2"><input type="color" id="${id(k)}" data-k="${k}" value="${esc(v)}"><label for="${id(k)}" style="margin:0">${esc(l)}</label></div>`;
  if(t=="zahl")return `<div class="gs-f"><label for="${id(k)}">${esc(l)}: <b id="${id(k)}_w">${esc(v)}</b></label><input type="range" id="${id(k)}" data-k="${k}" min="${a}" max="${b}" value="${esc(v)}"></div>`;
  if(t=="sel")return `<div class="gs-f"><label for="${id(k)}">${esc(l)}</label><select id="${id(k)}" data-k="${k}">${a.map(([w,x])=>`<option value="${w}"${w==v?" selected":""}>${esc(x)}</option>`).join("")}</select></div>`;
  if(t=="schrift")return `<div class="gs-f"><label for="${id(k)}">${esc(l)}</label><select id="${id(k)}" data-k="${k}">${Object.entries(GS.schriften).map(([w,x])=>`<option value="${w}"${w==v?" selected":""}>${esc(x)}</option>`).join("")}</select></div>`;
  if(t=="bild")return `<div class="gs-f"><label for="${id(k)}">${esc(l)}</label><div style="display:flex;gap:6px"><select id="${id(k)}" data-k="${k}">${gsBildOpt(art,k,a)}</select><button class="k" type="button" onclick="gsBildWahl('${art}','${k}',${a?1:0})" title="Aus den Unterlagen wählen">…</button></div></div>`;
  if(t=="area")return `<div class="gs-f"><label for="${id(k)}">${esc(l)}</label><textarea id="${id(k)}" data-k="${k}" rows="3" style="width:100%;font:inherit">${esc(v)}</textarea></div>`;
  if(t=="liste")return `<div class="gs-f"><label for="${id(k)}">${esc(l)}</label><textarea id="${id(k)}" data-k="${k}" data-liste="1" rows="4" style="width:100%;font:inherit">${esc((v||[]).join("\n"))}</textarea></div>`;
  if(t=="reihe")return `<div class="gs-f"><label>${esc(l)}</label><div style="display:flex;gap:6px">${[0,1,2].map(i=>`<select data-reihe="${i}" data-k="${k}">${Object.entries(GS_FUNK).map(([w,x])=>`<option value="${w}"${(v||[])[i]==w?" selected":""}>${i+1}. ${esc(x)}</option>`).join("")}</select>`).join("")}</div></div>`;
  return `<div class="gs-f"><label for="${id(k)}">${esc(l)}</label><input type="text" id="${id(k)}" data-k="${k}" value="${esc(v)}"></div>`}).join("")+"</details>").join("");
 const box=$("gs_"+art+"_form");box.querySelectorAll("select[data-k]:not([data-reihe])").forEach(e=>{if(e.querySelector(`option[value="${CSS.escape(String(D[e.dataset.k]??""))}"]`))e.value=D[e.dataset.k]??""});
 box.querySelectorAll("[data-k]").forEach(e=>e.oninput=e.onchange=()=>{const k=e.dataset.k;
  if(e.dataset.reihe!==undefined)D[k]=[...box.querySelectorAll(`[data-reihe][data-k="${k}"]`)].map(x=>x.value);
  else if(e.type=="checkbox")D[k]=e.checked;else if(e.type=="range"){D[k]=+e.value;$(e.id+"_w").textContent=e.value}else if(e.dataset.liste)D[k]=e.value.split("\n").map(x=>x.trim()).filter(Boolean).slice(0,6);else D[k]=e.value;
  $("gs_"+art+"_st").textContent="● nicht gespeichert";clearTimeout(GST[art]);GST[art]=setTimeout(()=>gsVorschau(art),350)});
 if(!gsDarf())box.querySelectorAll("input,select,textarea,button").forEach(e=>e.disabled=true)}
async function gsBildWahl(art,k,std){const w=await logoWahlFenster(k=="logo"?"Logo wählen":"Hintergrundbild wählen",GSD[art][k],"– kein Bild –");if(w===null)return;
 const sel=$(`gs_${art}_${k}`);if(![...sel.options].some(o=>o.value==w)){const d=await api("/api/logos");GS.logos=d.logos;sel.innerHTML=gsBildOpt(art,k,std)}sel.value=w;sel.dispatchEvent(new Event("change"))}
async function gsVorschau(art){try{const r=await fetch("/api/seiten-vorschau",{method:"POST",headers:{"X-Token":T,"Content-Type":"application/json"},body:JSON.stringify({art,design:GSD[art]})});const d=await r.json();
 if(!r.ok){$("log_gs_"+art).textContent="✖ "+(d.fehler||r.status);return}$("gs_"+art+"_vor").srcdoc=d.html;gsSkalieren(art)}catch(e){}}
function gsSkalieren(art){const f=$("gs_"+art+"_vor"),rahmen=f.parentElement,b=GSB[art],sk=Math.min(1,rahmen.clientWidth/b);f.style.width=b+"px";f.style.height=(rahmen.clientHeight/sk)+"px";f.style.transform=`scale(${sk})`}
document.addEventListener("click",e=>{const b=e.target.closest(".gs-gr");if(!b)return;GSB[b.dataset.art]=+b.dataset.b;document.querySelectorAll(`.gs-gr[data-art="${b.dataset.art}"]`).forEach(x=>x.classList.toggle("aktiv",x===b));gsSkalieren(b.dataset.art)});
addEventListener("resize",()=>{if(GS&&$("gestaltung").classList.contains("aktiv")){gsSkalieren("login");gsSkalieren("portal");gsSkalieren("mein")}});
async function gsSpeichern(art){const d=await api("/api/seiten-design",{art,design:GSD[art]},"log_gs_"+art);GS=d;GSD[art]=JSON.parse(JSON.stringify(d[art]));gsForm(art);gsVorschau(art);$("gs_"+art+"_st").textContent="✔ gespeichert"}
async function gsStandard(art){if(!confirm("Alle Einstellungen dieser Seite auf den Standard zurücksetzen?"))return;const d=await api("/api/seiten-design",{art,zuruecksetzen:true},"log_gs_"+art);GS=d;GSD[art]=JSON.parse(JSON.stringify(d[art]));gsForm(art);gsVorschau(art)}

/* Ansichtsprofile */
let APROF={},APA="",AZU={},APHINT=null;
function apId(){const a=new Uint8Array(6);crypto.getRandomValues(a);return [...a].map(x=>x.toString(36).padStart(2,"0")).join("").slice(0,10)}
function apNorm(b){b=b||{};const n={bereiche:(b.bereiche&&b.bereiche.length)?JSON.parse(JSON.stringify(b.bereiche)):MENUE_BASIS.map(c=>({id:c.k,name:"",icon:"",aus:false,tabs:c.tabs.map(t=>t[0])})),
 tabs:JSON.parse(JSON.stringify(b.tabs||{})),karten:JSON.parse(JSON.stringify(b.karten||{})),reihenfolge:JSON.parse(JSON.stringify(b.reihenfolge||{})),start:b.start||""};
 const da=new Set(n.bereiche.flatMap(x=>x.tabs));MENUE_BASIS.forEach(c=>c.tabs.forEach(([t])=>{if(!da.has(t)){(n.bereiche.find(x=>x.id==c.k)||n.bereiche[0]).tabs.push(t)}}));return n}
function apStart(){APROF={};Object.entries(GS.profile||{}).forEach(([i,p])=>APROF[i]={name:p.name,baum:apNorm(p.baum)});AZU={};GS.konten.forEach(k=>AZU[k.name]=k.profil||"");
 if(!APROF[APA])APA=Object.keys(APROF)[0]||"";apListe();$("ap_std").value=GS.standardprofil||"";apZeigen();apKonten()}
function apListe(){const o=Object.entries(APROF).sort((a,b)=>a[1].name.localeCompare(b[1].name)).map(([i,p])=>`<option value="${i}">${esc(p.name)}</option>`).join("");
 $("ap_wahl").innerHTML=o||'<option value="">– noch kein Profil –</option>';$("ap_wahl").value=APA;$("ap_std").innerHTML='<option value="">Standardansicht (ohne Profil)</option>'+o}
function apWahl(i){APA=i;APHINT=null;apZeigen()}
function apEinh(t,B){const ord=(B.reihenfolge||{})[t]||[];return EINH.filter(u=>u.tab==t).sort((a,b)=>{const ia=ord.indexOf(a.id),ib=ord.indexOf(b.id);return(ia<0?1e6+a.pos:ia)-(ib<0?1e6+b.pos:ib)})}
function apTabStd(t){return(MENUE_BASIS.flatMap(c=>c.tabs).find(x=>x[0]==t)||[t,t])[1]}
function apKarteZeile(u,B,nr,kl){const x=B.karten[u.id]||{};return `<div class="ap-z ${kl}${x.aus?" ap-aus":""}"><span class="ap-nr">${nr}</span><span class="ap-kn">${u.nr}</span><span class="ic"></span><input type="text" maxlength="80" value="${esc(x.name||"")}" placeholder="${esc(u.std)}" data-a="k-name" data-u="${esc(u.id)}">`
 +`<span class="ak"><button class="k mini" data-a="k-hoch" data-u="${esc(u.id)}" title="nach oben">↑</button><button class="k mini" data-a="k-runter" data-u="${esc(u.id)}" title="nach unten">↓</button><label title="${u.pflicht?"bleibt immer sichtbar":""}"><input type="checkbox" data-a="k-aus" data-u="${esc(u.id)}"${x.aus?" checked":""}${u.pflicht?" disabled":""}> aus</label><label><input type="checkbox" data-a="k-zu" data-u="${esc(u.id)}"${x.zu?" checked":""}> eingeklappt</label>`
 +(u.hint?`<button class="k mini" data-a="k-hint" data-u="${esc(u.id)}">Hinweis${x.hint!==undefined?" ✎":""}</button>`:"")+"</span></div>"
 +(APHINT==u.id?`<div class="ap-hint"><textarea rows="3" maxlength="600" data-a="k-hinttext" data-u="${esc(u.id)}">${esc(x.hint??u.hintStd)}</textarea><div class="knoepfe" style="margin-top:4px"><button class="k mini" data-a="k-hintstd" data-u="${esc(u.id)}">Original-Hinweis</button><button class="k mini" data-a="k-hintleer" data-u="${esc(u.id)}">Hinweis ausblenden</button></div></div>`:"")}
function apZeigen(){const box=$("ap_baum");if(!APA||!APROF[APA]){box.innerHTML='<p class="hint" style="padding:8px">Noch kein Profil – mit „+ Neues Profil“ anlegen (z. B. „Kassierer“).</p>';return}
 const B=APROF[APA].baum;let h="";
 B.bereiche.forEach((b,bi)=>{const g=MENUE_BASIS.find(c=>c.k==b.id),bnr=bi+1,kn=g?"B"+(MENUE_BASIS.indexOf(g)+1):"B+";
  h+=`<div class="ap-z ap-b${b.aus?" ap-aus":""}"><span class="ap-nr">${bnr}</span><span class="ap-kn">${kn}</span><input type="text" class="ic" maxlength="8" value="${esc(b.icon)}" placeholder="${esc(g?g.i:"📁")}" data-a="b-icon" data-i="${bi}" title="Symbol (z. B. ein Emoji)"><input type="text" maxlength="40" value="${esc(b.name)}" placeholder="${esc(g?g.t:"Neuer Bereich")}" data-a="b-name" data-i="${bi}">`
   +`<span class="ak"><button class="k mini" data-a="b-hoch" data-i="${bi}">↑</button><button class="k mini" data-a="b-runter" data-i="${bi}">↓</button><label><input type="checkbox" data-a="b-aus" data-i="${bi}"${b.aus?" checked":""}> aus</label>${g?"":`<button class="k mini" data-a="b-weg" data-i="${bi}" title="Bereich löschen – seine Reiter wandern in den ersten Bereich">✕</button>`}</span></div>`;
  b.tabs.forEach((t,ti)=>{const tn=TABS.findIndex(x=>x[0]==t),tx=B.tabs[t]||{},pf=PFLICHT_TABS.includes(t)||t=="gestaltung";
   h+=`<div class="ap-z ap-r${tx.aus?" ap-aus":""}"><span class="ap-nr">${bnr}.${ti+1}</span><span class="ap-kn">R${tn+1}</span><span class="ic"></span><input type="text" maxlength="40" value="${esc(tx.name||"")}" placeholder="${esc(apTabStd(t))}" data-a="t-name" data-t="${t}">`
    +`<span class="ak"><button class="k mini" data-a="t-hoch" data-i="${bi}" data-j="${ti}">↑</button><button class="k mini" data-a="t-runter" data-i="${bi}" data-j="${ti}">↓</button><select data-a="t-bereich" data-i="${bi}" data-j="${ti}" style="max-width:160px;min-height:30px;padding:3px 6px" title="in einen anderen Bereich verschieben">${B.bereiche.map((x,xi)=>`<option value="${xi}"${xi==bi?" selected":""}>→ ${esc(x.name||(MENUE_BASIS.find(c=>c.k==x.id)||{}).t||"Bereich "+(xi+1))}</option>`).join("")}</select>`
    +`<label title="${pf?"bleibt immer sichtbar":""}"><input type="checkbox" data-a="t-aus" data-t="${t}"${tx.aus?" checked":""}${pf?" disabled":""}> aus</label><label title="Startseite nach dem Anmelden"><input type="radio" name="ap_start" data-a="t-start" data-t="${t}"${B.start==t?" checked":""}> Start</label></span></div>`;
   let ki=0;const us=apEinh(t,B);us.filter(u=>!u.teil).forEach(u=>{ki++;h+=apKarteZeile(u,B,`${bnr}.${ti+1}.${ki}`,"ap-k");let tj=0;us.filter(x=>x.teil&&x.el.parentElement.closest(".karte")===u.el).forEach(x=>{tj++;h+=apKarteZeile(x,B,`${bnr}.${ti+1}.${ki}.${tj}`,"ap-t")})})})});
 box.innerHTML=h;if(!gsDarf())box.querySelectorAll("input,select,button").forEach(e=>e.disabled=true)}
function apKarte(B,id){return B.karten[id]||(B.karten[id]={})}
function apVerschiebe(B,id,richtung){const u=EINH.find(x=>x.id==id),ord=apEinh(u.tab,B).map(x=>x.id),gleich=ord.filter(i=>EINH.find(x=>x.id==i).parent===u.parent),p=gleich.indexOf(id),q=p+richtung;
 if(q<0||q>=gleich.length)return;const a=ord.indexOf(id),b=ord.indexOf(gleich[q]);[ord[a],ord[b]]=[ord[b],ord[a]];B.reihenfolge[u.tab]=ord}
$("ap_baum").addEventListener("input",e=>{const el=e.target,a=el.dataset.a;if(!a||!APROF[APA])return;const B=APROF[APA].baum;
 if(a=="b-icon")B.bereiche[el.dataset.i].icon=el.value;else if(a=="b-name")B.bereiche[el.dataset.i].name=el.value;
 else if(a=="t-name")(B.tabs[el.dataset.t]=B.tabs[el.dataset.t]||{}).name=el.value;else if(a=="k-name")apKarte(B,el.dataset.u).name=el.value;else if(a=="k-hinttext")apKarte(B,el.dataset.u).hint=el.value});
$("ap_baum").addEventListener("change",e=>{const el=e.target,a=el.dataset.a;if(!a||!APROF[APA])return;const B=APROF[APA].baum;
 if(a=="b-aus")B.bereiche[el.dataset.i].aus=el.checked;else if(a=="t-aus")(B.tabs[el.dataset.t]=B.tabs[el.dataset.t]||{}).aus=el.checked;else if(a=="t-start")B.start=el.dataset.t;
 else if(a=="k-aus")apKarte(B,el.dataset.u).aus=el.checked;else if(a=="k-zu")apKarte(B,el.dataset.u).zu=el.checked;
 else if(a=="t-bereich"){const t=B.bereiche[el.dataset.i].tabs.splice(+el.dataset.j,1)[0];B.bereiche[+el.value].tabs.push(t)}else return;apZeigen()});
$("ap_baum").addEventListener("click",e=>{const el=e.target.closest("button[data-a]");if(!el||!APROF[APA])return;const B=APROF[APA].baum,a=el.dataset.a,i=+el.dataset.i,j=+el.dataset.j;
 const tausch=(arr,x,y)=>{if(y<0||y>=arr.length)return;[arr[x],arr[y]]=[arr[y],arr[x]]};
 if(a=="b-hoch")tausch(B.bereiche,i,i-1);else if(a=="b-runter")tausch(B.bereiche,i,i+1);
 else if(a=="b-weg"){const weg=B.bereiche.splice(i,1)[0];(B.bereiche[0]||{tabs:[]}).tabs.push(...weg.tabs)}
 else if(a=="t-hoch")tausch(B.bereiche[i].tabs,j,j-1);else if(a=="t-runter")tausch(B.bereiche[i].tabs,j,j+1);
 else if(a=="k-hoch")apVerschiebe(B,el.dataset.u,-1);else if(a=="k-runter")apVerschiebe(B,el.dataset.u,1);
 else if(a=="k-hint")APHINT=APHINT==el.dataset.u?null:el.dataset.u;else if(a=="k-hintstd")delete apKarte(B,el.dataset.u).hint;else if(a=="k-hintleer")apKarte(B,el.dataset.u).hint="";else return;apZeigen()});
function apNeu(kopie){const name=prompt(kopie?"Name der Kopie:":"Name des neuen Profils (z. B. Kassierer, Technik, Spartenleitung):",kopie&&APROF[APA]?APROF[APA].name+" (Kopie)":"");if(!name)return;
 const i=apId();APROF[i]={name:name.trim().slice(0,40),baum:kopie&&APROF[APA]?JSON.parse(JSON.stringify(APROF[APA].baum)):apNorm({})};APA=i;apListe();apZeigen();apKonten()}
function apBereichNeu(){if(!APROF[APA])return;const n=prompt("Name des neuen Bereichs:","Neuer Bereich");if(!n)return;APROF[APA].baum.bereiche.push({id:"eigen-"+apId(),name:n.trim().slice(0,40),icon:"📁",aus:false,tabs:[]});apZeigen();
 $("log_ap").textContent="ℹ Reiter über die Auswahl „→ …“ in den neuen Bereich verschieben."}
function apUmbenennen(){if(!APROF[APA])return;const n=prompt("Neuer Name:",APROF[APA].name);if(!n)return;APROF[APA].name=n.trim().slice(0,40);apListe();apKonten()}
function apLoeschen(){if(!APROF[APA]||!confirm("Profil „"+APROF[APA].name+"“ löschen? Konten mit diesem Profil bekommen die Standardansicht (erst nach „Speichern“)."))return;
 Object.keys(AZU).forEach(k=>{if(AZU[k]==APA)AZU[k]=""});delete APROF[APA];APA=Object.keys(APROF)[0]||"";apListe();apZeigen();apKonten()}
function apZurueck(){if(!APROF[APA]||!confirm("Menübaum dieses Profils auf den Standard zurücksetzen (Namen, Reihenfolge, Ausblendungen)?"))return;APROF[APA].baum=apNorm({});apZeigen()}
function apKonten(){const o='<option value="">– Standard –</option>'+Object.entries(APROF).map(([i,p])=>`<option value="${i}">${esc(p.name)}</option>`).join("");
 $("ap_konten").innerHTML="<table><tr><th>Konto</th><th>Name</th><th>Ansichtsprofil</th></tr>"+GS.konten.map(k=>`<tr><td>${esc(k.name)}</td><td>${esc(k.anzeige||"")}</td><td><select data-konto="${esc(k.name)}" style="min-width:200px"${gsDarf()?"":" disabled"}>${o}</select></td></tr>`).join("")+"</table>";
 $("ap_konten").querySelectorAll("select").forEach(s=>{s.value=AZU[s.dataset.konto]||"";s.onchange=()=>AZU[s.dataset.konto]=s.value})}
function apSauber(B){const k={};Object.entries(B.karten).forEach(([i,x])=>{const y={};if(x.name&&x.name.trim())y.name=x.name.trim();if(x.aus)y.aus=true;if(x.zu)y.zu=true;if(x.hint!==undefined)y.hint=x.hint;if(Object.keys(y).length)k[i]=y});
 const t={};Object.entries(B.tabs).forEach(([i,x])=>{if((x.name&&x.name.trim())||x.aus)t[i]={name:(x.name||"").trim(),aus:!!x.aus}});return{...B,karten:k,tabs:t}}
async function apSpeichern(){const profile={};Object.entries(APROF).forEach(([i,p])=>profile[i]={name:p.name,baum:apSauber(p.baum)});
 GS=await api("/api/ansicht-profile",{profile,standard:$("ap_std").value,zuordnung:AZU},"log_ap");apStart()}
function apVorschau(){if(!APROF[APA])return;try{sessionStorage.setItem("sn_profil_vorschau",JSON.stringify({id:APA,name:APROF[APA].name,...apSauber(APROF[APA].baum)}))}catch(e){alert("Vorschau nicht möglich (Browser-Speicher gesperrt).");return}location.reload()}
function apExport(){if(!APROF[APA])return;const b=new Blob([JSON.stringify({sparteNetProfil:1,name:APROF[APA].name,baum:apSauber(APROF[APA].baum)},null,1)],{type:"application/json"}),u=URL.createObjectURL(b),a=document.createElement("a");
 a.href=u;a.download="Ansichtsprofil_"+APROF[APA].name.replace(/[^A-Za-z0-9äöüÄÖÜß_-]+/g,"_")+".json";document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),30000)}
function apImport(inp){const f=inp.files[0];if(!f)return;f.text().then(t=>{const x=JSON.parse(t);if(!x.baum)throw new Error("Keine Profil-Datei.");const i=apId();APROF[i]={name:String(x.name||"Import").slice(0,40),baum:apNorm(x.baum)};APA=i;apListe();apZeigen();apKonten();
 $("log_ap").textContent="✔ Importiert – zum Übernehmen „Profile und Zuordnung speichern“."}).catch(e=>{$("log_ap").textContent="✖ "+e.message}).finally(()=>inp.value="")}
let LZ=null;
async function lzLaden(){LZ=await api("/api/laufzeiten",undefined,"log_lz");lzZeigen()}
function lzZeigen(){const d=LZ;if(!d)return;const e=d.einstellungen,adm=ICH.admin,schr=bereichStufe("buchungen")=="schreiben",gw=ICH.admin||(ICH.bereiche||{}).wlan_pw=="schreiben";
 $("lz_auto").checked=e.gateway_auto;$("lz_erin").value=String(e.erinnerung_stunden);if(![...$("lz_erin").options].some(o=>o.value==String(e.erinnerung_stunden)))$("lz_erin").insertAdjacentHTML("beforeend",`<option value="${e.erinnerung_stunden}">${e.erinnerung_stunden} Stunden</option>`),$("lz_erin").value=String(e.erinnerung_stunden);$("lz_entf").checked=e.buchung_entfernen;
 ["lz_auto","lz_erin","lz_entf"].forEach(i=>$(i).disabled=!adm);$("lz_einst_kn").hidden=!adm;
 const z=c=>d.zeilen.filter(x=>x.zustand==c).length;
 $("lz_k").innerHTML=[["laufend",z("aktiv"),""],["gesperrt",z("gesperrt"),""],["am Gateway offen",z("offen_sperren")+z("offen_frei"),z("offen_sperren")+z("offen_frei")?"warn":""],["Tarife mit Laufzeit",d.tarife.length,""]].map(([t,n,k])=>`<div class="kachel ${k}"><b>${n}</b>${t}</div>`).join("");
 const q=$("lz_suche").value.trim().toLowerCase();const zl=d.zeilen.filter(x=>!q||(x.sparte+" "+x.parzelle+" "+x.tarif+" "+x.text).toLowerCase().includes(q));
 const farbe={aktiv:"",offen_sperren:"geaendert",offen_frei:"geaendert",gesperrt:"gesperrt",ausnahme:""};
 $("lz_tab").className=zl.length?"tab":"";$("lz_tab").innerHTML=zl.length?"<table><tr><th>Sparte</th><th>Parzelle</th><th>Tarif</th><th>Beginn</th><th>Ende</th><th>Zustand</th><th></th></tr>"+zl.map(x=>`<tr class="${farbe[x.zustand]||""}"><td>${esc(x.sparte)}</td><td>${x.parzelle}</td><td>${esc(x.tarif||"–")}</td><td>${esc(x.start)}</td><td>${esc(x.ende)}${x.rest?"<br><small>"+esc(x.rest)+"</small>":""}</td><td>${esc(x.text)}${x.fehler?'<br><small class="fehler">'+esc(x.fehler)+"</small>":""}</td><td style="white-space:nowrap">`
  +(schr&&x.tarif?`<button class="k" onclick="lzVerl('${esc(x.sparte)}',${x.parzelle})">Verlängern</button> `:"")
  +(gw&&!x.gesperrt?`<button class="k" onclick="lzZugang('${esc(x.sparte)}',${x.parzelle},'sperren')">Sperren</button>`:"")
  +(gw&&x.gesperrt?`<button class="k" onclick="lzZugang('${esc(x.sparte)}',${x.parzelle},'freigeben')">Freigeben</button>`:"")+"</td></tr>").join("")+"</table>":'<p class="hint">'+(d.tarife.length?"Noch keine Laufzeiten – sie beginnen mit der nächsten Buchung eines Tarifs mit Laufzeit.":"Kein Tarif hat eine Laufzeit. Oben in der Tarif-Tabelle eine Laufzeit eintragen und speichern.")+"</p>";
 $("lz_ohne").innerHTML=d.ohne_laufzeit.length?`<p class="hint" style="margin-top:10px">${d.ohne_laufzeit.length} gebuchte Parzelle(n) haben einen Tarif mit Laufzeit, aber noch keine Startzeit (gebucht, bevor der Tarif eine Laufzeit hatte): ${d.ohne_laufzeit.slice(0,20).map(x=>esc(x.sparte+" "+x.parzelle)).join(", ")}${d.ohne_laufzeit.length>20?" …":""}</p>`+(schr?'<div class="knoepfe"><button class="k" onclick="lzStarten()">Laufzeit für diese Parzellen ab jetzt starten</button></div>':""):""}
async function lzVerl(kz,p){const n=prompt(`${kz} Parzelle ${p}: um wie viele Laufzeiten verlängern?`,"1");if(!n)return;LZ=await api("/api/laufzeit-verlaengern",{sparte:kz,parzelle:p,anzahl:+n},"log_lz");lzZeigen()}
async function lzZugang(kz,p,aktion){const v=await api("/api/zugang",{sparte:kz,parzelle:p,aktion},"log_lz");LZ=v;lzZeigen();
 if(!confirm(v.log[0]+"\n\nJetzt am Gateway ausführen?"))return;LZ=await api("/api/zugang",{sparte:kz,parzelle:p,aktion,ausfuehren:true},"log_lz");lzZeigen()}
async function lzStarten(){if(!confirm("Laufzeit für alle gebuchten Parzellen mit Laufzeit-Tarif ohne Startzeit ab jetzt starten?"))return;LZ=await api("/api/laufzeit-starten",{},"log_lz");lzZeigen()}
async function lzEinst(jetzt){const an=$("lz_auto").checked;if(an&&!LZ.einstellungen.gateway_auto&&!confirm("Automatisches Sperren und Freigeben einschalten?\n\nDer Manager ändert dann ohne weitere Rückfrage das Pächter-WLAN am Gateway: Parzellen mit abgelaufener Laufzeit verlieren den Zugang, nach Verlängerung bekommen sie ihn zurück. Jede Änderung steht im Änderungsprotokoll."))return;
 LZ=await api("/api/laufzeit-einstellungen",{gateway_auto:an,erinnerung_stunden:+$("lz_erin").value,buchung_entfernen:$("lz_entf").checked,jetzt},"log_lz");lzZeigen()}
async function tfLaden(){const d=await api("/api/tarife");TF=d;TFL=d.tarife.map(t=>({...t,alt:t.name}));tfZeigen();$("tf_modus").value=d.modus;tfModusHint();tzMassenFuellen()}
function tfNeu(){TFL.push({name:"Tarif "+(TFL.length+1),down:50,up:10,praefix:29,geraete:5,preis:0,laufzeit:0,laufzeit_einheit:"tage"});tfZeigen()}
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
async function abmelden(){if(!confirm("Auf diesem Gerät abmelden?"))return;await fetch("/abmelden",{method:"POST",headers:{"X-Token":T}});location.replace("/?abgemeldet=1")}
/* Automatisch abmelden nach X Minuten ohne Aktivität (Einstellung unter Benutzer → Anmeldung und Sicherheit).
   Aktivität aller offenen Tabs zählt (localStorage); dem Server wird sie höchstens jede Minute gemeldet (/api/aktiv). */
const AB_MIN=__ABMELDEN__;let AB_LETZT=Date.now(),AB_GEMELDET=Date.now(),AB_FENSTER=null,AB_AUS=false;
function abJetzt(){let t=AB_LETZT;try{t=Math.max(t,+localStorage.getItem("sn_aktiv")||0)}catch(e){}return t}
function abAktiv(){const j=Date.now();if(j-AB_LETZT<1000)return;AB_LETZT=j;try{localStorage.setItem("sn_aktiv",String(j))}catch(e){}if(AB_FENSTER)abFenster(false)}
function abFenster(an,rest){if(!an){if(AB_FENSTER){AB_FENSTER.remove();AB_FENSTER=null}return}
 if(!AB_FENSTER){AB_FENSTER=document.createElement("div");AB_FENSTER.setAttribute("role","alertdialog");AB_FENSTER.setAttribute("aria-live","assertive");
  AB_FENSTER.style.cssText="position:fixed;inset:0;z-index:9999;background:rgba(10,20,15,.55);display:grid;place-items:center;padding:16px";
  AB_FENSTER.innerHTML='<div style="background:var(--card,#fff);color:var(--text,#1d2f3e);border-radius:16px;padding:24px;max-width:380px;width:100%;box-shadow:0 18px 50px rgba(0,0,0,.35);text-align:center"><div style="font-size:34px">⏳</div><h3 style="margin:6px 0 8px">Noch da?</h3><p style="margin:0 0 16px;color:var(--muted,#5d6b75)">Ohne Aktivität werden Sie in <b id="ab_rest"></b> automatisch abgemeldet.</p><div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap"><button class="k p" id="ab_bleiben">Angemeldet bleiben</button><button class="k" id="ab_raus">Jetzt abmelden</button></div></div>';
  document.body.appendChild(AB_FENSTER);$("ab_bleiben").onclick=()=>{AB_LETZT=0;abAktiv();abMelden(true)};$("ab_raus").onclick=()=>abRaus("1");$("ab_bleiben").focus()}
 $("ab_rest").textContent=rest+" s"}
async function abMelden(sofort){if(!sofort&&Date.now()-AB_GEMELDET<60000)return;AB_GEMELDET=Date.now();try{const r=await fetch("/api/aktiv",{headers:{"X-Token":T},cache:"no-store"});if(r.status==401)abRaus("zeit")}catch(e){}}
async function abRaus(grund){if(AB_AUS)return;AB_AUS=true;try{await fetch("/abmelden",{method:"POST",headers:{"X-Token":T}})}catch(e){}location.replace("/?abgemeldet="+grund)}
function abPruefen(){const ruhe=(Date.now()-abJetzt())/1000,grenze=AB_MIN*60;
 if(ruhe>=grenze)return abRaus("zeit");if(ruhe>=grenze-60)abFenster(true,Math.ceil(grenze-ruhe));else{abFenster(false);if(ruhe<60)abMelden(false)}}
if(AB_MIN>0){["pointerdown","keydown","wheel","touchstart","input"].forEach(e=>addEventListener(e,abAktiv,{passive:true,capture:true}));
 addEventListener("storage",e=>{if(e.key=="sn_aktiv"&&AB_FENSTER&&(Date.now()-abJetzt())/1000<AB_MIN*60-60)abFenster(false)});
 setInterval(abPruefen,1000);document.addEventListener("visibilitychange",()=>{if(!document.hidden)abPruefen()})}
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
function bereichStufe(k){return ICH.admin?"schreiben":(ICH.bereiche||{})[k]||"kein"}
function reiterErlaubt(id){return ICH.admin||!(id in ICH.reiter)||ICH.reiter[id]!="kein"}
/* ---- Menü (☰): Bereiche mit Reitern und Unterpunkten (springen zur Karte im Reiter) ---- */
const MENUE_BASIS=[
 {k:"uebersicht",t:"Übersicht",i:"🏠",tabs:[["start","Start",["Auf einen Blick","Überblick","Parzelle nachschlagen","Gast-Voucher schnell","Schnellzugriff"]]],extra:[["system","Störungsüberwachung","Störungsüberwachung"]]},
 {k:"einrichtung",t:"Einrichtung",i:"🛠️",tabs:[["verbindung","Verbindung",["Verbindung über die UniFi-Cloud","Handy & Tablet","Datenspeicher","Protokoll zur Fehlersuche","Diagnose-Datei"]],["planung","Planung",["Sparten am Gateway","IP-Plan"]],["netzplanung","Netzplanung",["Netzplanung","Einnahmen nach Tarif","Gateway-Zuteilung nach Buchung","VLAN-Plan","Gateway-Standorte","Einstellungen"]],["abgleich","Abgleich",["Abgleich","Umzugshilfe"]]]},
 {k:"wlan",t:"WLAN & Zugang",i:"📶",tabs:[["einrichten","Netze, WLANs & Passwörter",["Sparte einrichten","Netze nach Buchungen","Fehlende Netze anlegen","WLANs der Sparte","Passwörter je Parzelle","Zugangskarten mit WLAN-QR-Code","Passwörter ins Pächter-WLAN laden"]],["uebertragen","Übertragen",["Änderungen an das Gateway übertragen","Unterschiede zwischen Manager und Gateway","Änderungsprotokoll"]],["kartendesign","Zugangskarten-Design",["Zugangskarten gestalten","Logo"]],["voucher","Gast-Voucher",["Gast-Voucher erstellen","Vorlagen","Voucher am Gateway"]]]},
 {k:"tarife",t:"Tarife & Buchungen",i:"💶",tabs:[["tarife","Tarife",["Tarife","Laufzeiten und Zugang","Netze einem Tarif zuordnen","An das Gateway übertragen"]],["kalkulation","Buchungen & Kalkulation",["Buchungen erfassen","Kalkulation","Je Sparte","Annahmen","Aus Excel übernehmen"]]]},
 {k:"verein",t:"Pächter & Verein",i:"👥",tabs:[["mitglieder","Mitglieder",["Mitglieder","Verträge","Rundschreiben","Import aus Excel"]],["tickets","Anfragen",["Anfragen","Kontakt-Seite"]],["rechnungen","Rechnungen",["Rechnungen","Rechnungslauf","Zahlungsabgleich","Einstellungen für Rechnungen"]]]},
 {k:"dokumente",t:"Dokumente & Automatik",i:"📁",tabs:[["unterlagen","Unterlagen",["Unterlagen","Hochladen"]],["automationen","Automationen & E-Mail",["Automationen","Verlauf","E-Mail-Layout und Vorlagen","E-Mail-Versand","Wochenbericht","API-Schnittstelle"]]]},
 {k:"daten",t:"Daten & Auswertung",i:"📊",tabs:[["lesen","Auslesen",["Auslesen"]],["daten","Alle Daten",["Alle Daten"]]],extra:[["uebertragen","Änderungsprotokoll","Änderungsprotokoll"]]},
 {k:"verwaltung",t:"System & Konto",i:"⚙️",tabs:[["system","System",["Störungsüberwachung","Datensicherung","Aktualisierung","Systeminfo","Internet – letzte 24 Stunden","Geräte – Auslastung"]],["benutzer","Benutzer & Konto",["Mein Konto","Zwei-Faktor-Anmeldung","Apps und Geräte","Benutzerkonten","Anmeldung und Sicherheit","Neues Benutzerkonto"]],["gestaltung","Oberfläche gestalten",[]],["hilfe","Hilfe",["Hilfe"]]]}];
/* ---- Ansichtsprofil: Karten (Einheiten) erfassen, Profil anwenden (umbenennen, ausblenden, sortieren, Hinweise, eingeklappt) ---- */
let PROFIL=__PROFIL__;
try{const v=sessionStorage.getItem("sn_profil_vorschau");if(v)PROFIL={...JSON.parse(v),vorschau:true}}catch(e){}
if(location.hash=="#standardansicht")PROFIL={};
const PFLICHT_TABS=["benutzer"],PFLICHT_EINH=["benutzer/mein-konto","benutzer/eigenes-passwort-aendern"];
function slug(t){return String(t).toLowerCase().replace(/ä/g,"ae").replace(/ö/g,"oe").replace(/ü/g,"ue").replace(/ß/g,"ss").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,60)||"karte"}
const EINH=[];
(function(){let nr=0;TABS.forEach(([tab])=>{const sec=$(tab);if(!sec)return;const ids={};
 sec.querySelectorAll(".karte,[data-teil]").forEach(el=>{if(el.closest("#kd_form")||el.parentElement.closest(".karte")&&!el.dataset.teil)return;const h=el.querySelector("h2,h3");if(!h)return;
  const std=h.textContent.replace(/\s+/g," ").trim();let id=tab+"/"+slug(std);if(ids[id])id+="-"+(++ids[id]);else ids[id]=1;
  const hint=[...el.querySelectorAll("p.hint")].find(p=>p.closest(".karte,[data-teil]")===el)||null;nr++;
  EINH.push({id,nr:"K"+nr,tab,el,h,std,hint,hintStd:hint?hint.textContent.trim():"",parent:el.parentElement,teil:!!el.dataset.teil,pflicht:PFLICHT_EINH.includes(id),pos:EINH.length})})})})();
function einhTitel(u,name){const tn=[...u.h.childNodes].find(n=>n.nodeType==3&&n.textContent.trim());if(tn)tn.textContent=name+(tn.textContent.endsWith(" ")?" ":"");else u.h.prepend(document.createTextNode(name+" "))}
function einhZu(u,zu){const kopf=[...u.el.children].find(c=>c.contains(u.h));u.el.classList.toggle("p-zu",zu);if(kopf)kopf.classList.add("p-kopf");u.h.classList.add("p-klapp");u.h.onclick=()=>u.el.classList.toggle("p-zu")}
function sortiereEinh(liste,ordnung){const rang=id=>{const i=ordnung.indexOf(id);return i<0?1e6+liste.findIndex(x=>x.id==id):i};
 const gruppen=new Map();liste.forEach(u=>{if(!gruppen.has(u.parent))gruppen.set(u.parent,[]);gruppen.get(u.parent).push(u)});
 gruppen.forEach(us=>{const marken=us.map(u=>{const c=document.createComment("p");u.el.before(c);return c});[...us].sort((a,b)=>rang(a.id)-rang(b.id)).forEach((u,i)=>marken[i].replaceWith(u.el))})}
function tabVerborgen(t){if(PFLICHT_TABS.includes(t)||(t=="gestaltung"&&(ICH.admin||ICH.bereiche.gestaltung=="schreiben")))return false;return !!(((PROFIL||{}).tabs||{})[t]||{}).aus}
function reiterSichtbar(t){return reiterErlaubt(t)&&!tabVerborgen(t)}
function einhSichtbar(u){if(u.el.dataset.pAus)return false;const c=u.el;return !(c.hidden||getComputedStyle(c).display=="none"||(c.closest("[hidden]")&&c.closest("[hidden]")!==$(u.tab)))}
(function profilAnwenden(){const P=PROFIL||{};if(!P.id&&!P.vorschau)return;const k=P.karten||{};
 EINH.forEach(u=>{const x=k[u.id];if(!x)return;if(x.name)einhTitel(u,x.name);if(x.hint!==undefined&&u.hint){if(x.hint==="")u.hint.style.display="none";else u.hint.textContent=x.hint}
  if(x.aus&&!u.pflicht){u.el.dataset.pAus="1";u.el.style.display="none"}if(x.zu)einhZu(u,true)});
 Object.entries(P.reihenfolge||{}).forEach(([tab,ord])=>sortiereEinh(EINH.filter(u=>u.tab==tab),ord));
 if(P.vorschau){const b=document.createElement("div");b.style.cssText="position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:950;background:#1d2f3e;color:#fff;padding:10px 14px;border-radius:10px;display:flex;gap:10px;align-items:center;box-shadow:0 8px 24px rgba(0,0,0,.3)";
  b.innerHTML='Vorschau des Profils „'+esc(P.name||"")+'“ <button class="k" style="background:#fff">Vorschau beenden</button>';b.querySelector("button").onclick=()=>{try{sessionStorage.removeItem("sn_profil_vorschau")}catch(e){}location.reload()};document.body.appendChild(b)}})();
function menueAusProfil(P){const info={};MENUE_BASIS.forEach(c=>c.tabs.forEach(t=>info[t[0]]=t));
 if(!P||!P.bereiche||!P.bereiche.length)return MENUE_BASIS;
 const kat=P.bereiche.map(b=>{const g=MENUE_BASIS.find(c=>c.k==b.id);return{k:b.id,t:b.name||(g?g.t:"Bereich"),i:b.icon||(g?g.i:"📁"),aus:b.aus,extra:g?g.extra||[]:[],tabs:(b.tabs||[]).filter(t=>info[t]).map(t=>info[t])}});
 Object.keys(info).forEach(t=>{if(!kat.some(c=>c.tabs.some(x=>x[0]==t))){const g=MENUE_BASIS.find(c=>c.tabs.some(x=>x[0]==t));const z=kat.find(c=>c.k==g.k&&!c.aus)||kat.find(c=>!c.aus)||kat[0];if(z)z.tabs.push(info[t])}});
 kat.forEach(c=>{if(c.aus)c.tabs.filter(t=>PFLICHT_TABS.includes(t[0])||t[0]=="gestaltung").forEach(t=>{const z=kat.find(x=>!x.aus);if(z&&z!==c)z.tabs.push(t)})});
 return kat.filter(c=>!c.aus)}
const MENUE=menueAusProfil(PROFIL);
const MKAT={};MENUE.forEach(c=>c.tabs.forEach(([id])=>{if(!MKAT[id])MKAT[id]=c}));
const MWORT={start:"überblick dashboard parzelle passwort qr",verbindung:"cloud api key konsole handy pin tailscale protokoll diagnose datenbank",planung:"ip-plan sparten excel vlan",netzplanung:"vlan gateway standort einnahmen zuteilung",abgleich:"umzug vergleich clients",
 einrichten:"netze wlan ppsk passwort zugangskarten karten drucken qr",uebertragen:"gateway änderungen protokoll rückgängig",kartendesign:"logo karte design farben schrift qr druck",voucher:"gast code gäste",tarife:"laufzeit sperren freigeben qos bandbreite preis zugang ablauf verlängern",
 kalkulation:"buchung buchen excel annahmen",mitglieder:"pächter verträge kündigung rundschreiben import excel datenschutz dsgvo",tickets:"anfragen ticket portal pächter-seite selbstauskunft",rechnungen:"zahlung kontoauszug girocode pdf",
 unterlagen:"dokumente dateien ordner logos hochladen",automationen:"email e-mail smtp layout vorlagen api webhook wochenbericht logo",lesen:"auslesen",daten:"json rohdaten",system:"störung überwachung sicherung backup update version",
 benutzer:"konto passwort zwei-faktor 2fa abmelden sicherheit rechte apps geräte",hilfe:"anleitung"};
function mVerborgen(tab,h){const sec=$(tab);if(!sec)return false;const k=[...sec.querySelectorAll("h2,h3")].find(x=>x.textContent.replace(/\s+/g," ").trim().includes(h));if(!k)return false;return !mKarte(tab,h)}
let MAUF=null;
function mKarte(tab,h){const sec=$(tab);if(!sec||!h)return null;const k=[...sec.querySelectorAll("h2,h3")].find(x=>x.textContent.replace(/\s+/g," ").trim().includes(h));if(!k)return null;const c=k.closest(".karte")||k;
 return(c.hidden||getComputedStyle(c).display=="none"||(c.closest("[hidden]")&&c.closest("[hidden]")!==sec))?null:c}
function springe(tab,h){menue(false);zeige(tab);if(!h)return;let n=0;const ver=()=>{const c=mKarte(tab,h);if(!c){if(++n<15)setTimeout(ver,150);return}   // Inhalte, die erst geladen werden (z. B. Kartendesign)
 c.scrollIntoView({behavior:"smooth",block:"start"});c.classList.remove("blink");void c.offsetWidth;c.classList.add("blink")};setTimeout(ver,80)}
function mName(id){const pn=((((PROFIL||{}).tabs||{})[id])||{}).name;if(pn)return pn;if(id=="benutzer"&&!ICH.admin)return"Mein Konto";for(const c of MENUE)for(const t of c.tabs)if(t[0]==id)return t[1];const x=TABS.find(t=>t[0]==id);return x?x[1]:id}
function einhName(u){return(((PROFIL||{}).karten||{})[u.id]||{}).name||u.std}
function menueBauen(){const q=$("menue_suche").value.trim().toLowerCase(),akt=(location.hash.slice(1)||startReiter()),box=$("menue_liste");
 const einh=tab=>EINH.filter(u=>u.tab==tab&&!u.teil&&einhSichtbar(u)).sort((a,b)=>[...a.parent.children].indexOf(a.el)-[...b.parent.children].indexOf(b.el));
 const unter=(tab,liste)=>liste.map(u=>`<button class="munter" data-tab="${tab}" data-u="${esc(u.id)}">${esc(einhName(u))}</button>`).join("");
 if(q){let h="";MENUE.forEach(c=>{let teil="";c.tabs.concat((c.extra||[]).map(([t,l,z])=>[t,l,[],z])).forEach(([id,l,subs,ziel])=>{if(!reiterSichtbar(id))return;const pt=(mName(id)+" "+c.t+" "+(ziel?"":MWORT[id]||"")).toLowerCase().includes(q);
   const s=ziel?[]:einh(id).filter(u=>einhName(u).toLowerCase().includes(q));if(pt||s.length){teil+=`<button class="mpunkt" data-tab="${id}" data-h="${esc(ziel||"")}">${esc(ziel?l:mName(id))}</button>`+unter(id,s)}});
   if(teil)h+=`<div class="mkat msuche"><div class="mtreffer">${c.i} ${esc(c.t)}</div><div class="minhalt" style="padding-left:6px">${teil}</div></div>`});
  box.innerHTML=h||'<p class="hint" style="padding:10px">Nichts gefunden.</p>'}
 else{const auf=MAUF||(MKAT[akt]||MENUE[0]).k;
  box.innerHTML=MENUE.map(c=>{const tabs=c.tabs.filter(([id])=>reiterSichtbar(id));const ex=(c.extra||[]).filter(([id,,z])=>reiterSichtbar(id)&&mKarte(id,z));if(!tabs.length&&!ex.length)return"";
   return `<div class="mkat${c.k==auf?" auf":""}" data-k="${c.k}"><button class="mkb" aria-expanded="${c.k==auf}"><i>${esc(c.i)}</i>${esc(c.t)}<em>›</em></button><div class="minhalt">`
    +tabs.map(([id])=>`<button class="mpunkt${id==akt?" aktiv":""}" data-tab="${id}">${esc(mName(id))}</button>`+unter(id,einh(id))).join("")
    +ex.map(([id,l,z])=>`<button class="mpunkt" data-tab="${id}" data-h="${esc(z)}">${esc(l)} <small style="color:var(--muted)">→ ${esc(mName(id))}</small></button>`).join("")+"</div></div>"}).join("")}
 box.querySelectorAll(".mkb").forEach(b=>b.onclick=()=>{const k=b.parentElement.dataset.k;MAUF=b.parentElement.classList.contains("auf")?"-":k;menueBauen()});
 box.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>b.dataset.u?springeEinh(b.dataset.tab,b.dataset.u):springe(b.dataset.tab,b.dataset.h||""))}
function springeEinh(tab,id){menue(false);zeige(tab);const u=EINH.find(x=>x.id==id);if(!u)return;setTimeout(()=>{u.el.classList.remove("p-zu");const c=u.el;c.scrollIntoView({behavior:"smooth",block:"start"});c.classList.remove("blink");void c.offsetWidth;c.classList.add("blink")},80)}
function menue(an){const m=$("menue"),offen=an===undefined?!m.classList.contains("offen"):an;m.classList.toggle("offen",offen);m.setAttribute("aria-hidden",String(!offen));$("menue_hg").hidden=!offen;$("burger").setAttribute("aria-expanded",String(offen));
 if(offen){MAUF=null;$("menue_suche").value="";menueBauen();setTimeout(()=>{if(matchMedia("(pointer:fine)").matches)$("menue_suche").focus();else{const a=m.querySelector(".mpunkt.aktiv");if(a)a.scrollIntoView({block:"center"})}},50)}}
addEventListener("keydown",e=>{if(e.key=="Escape"&&$("menue").classList.contains("offen"))menue(false);if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()=="k"){e.preventDefault();menue(true)}});
function navAktualisieren(id){id=id||location.hash.slice(1)||startReiter();const c=MKAT[id],alle=!!ANS.reiter;let kb=$("n_kat");
 if(!kb){kb=document.createElement("button");kb.id="n_kat";kb.className="nkat";kb.onclick=()=>menue(true);$("nav").prepend(kb)}
 kb.hidden=alle||!c;if(c)kb.innerHTML=`<i>${esc(c.i)}</i>${esc(c.t)}`;kb.title="Bereich wechseln (Menü)";
 TABS.forEach(([t])=>{const b=$("n_"+t);if(!b)return;b.hidden=!reiterSichtbar(t)||(!alle&&!!c&&MKAT[t]!==c);if(!alle)b.textContent=mName(t)})
 if(alle)TABS.forEach(([t,l])=>{const b=$("n_"+t);if(b)b.textContent=t=="benutzer"&&!ICH.admin?"Mein Konto":l})}
function startReiter(){const h=location.hash.slice(1);if(TABS.some(t=>t[0]==h)&&reiterErlaubt(h))return h;const ps=(typeof PROFIL!="undefined"&&PROFIL&&PROFIL.start)||"";
 if(ps&&reiterSichtbar(ps))return ps;const t=TABS.find(t=>reiterSichtbar(t[0]))||TABS.find(t=>reiterErlaubt(t[0]));return t?t[0]:"benutzer"}
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
 zfZeigen(d);apLaden().catch(()=>{});$("bn_ich_pw").hidden=!d.eigenes_passwort;$("bn_admin_hint").hidden=d.name!="admin";if(ICH.admin)bnLaden()}
async function bnEigenesPw(){await api("/api/benutzer-ich",{alt:$("bn_alt").value,passwort:$("bn_neu1").value,passwort2:$("bn_neu2").value},"log_bni");["bn_alt","bn_neu1","bn_neu2"].forEach(i=>$(i).value="")}
async function bnLaden(){bnZeigen(await api("/api/benutzer",undefined,"log_bn"))}
async function bnSpeichern(b,logid){bnZeigen(await api("/api/benutzer-speichern",b,logid||"log_bn"))}
function siWahl(id,w){const e=$(id);if(![...e.options].some(o=>o.value==String(w))){const o=document.createElement("option");o.value=w;o.textContent=w+(id=="si_merk"?" Stunden":" Minuten");e.appendChild(o)}e.value=String(w)}
function aztZeigen(d){const ad=d.admin;
 $("azt_tab").innerHTML=d.tokens.length?"<table><tr><th>Name</th>"+(ad?"<th>Konto</th>":"")+"<th>beginnt mit</th><th>erstellt</th><th>zuletzt benutzt</th><th></th></tr>"+d.tokens.map(t=>`<tr${t.id==d.neu_id?' style="background:#eef7e8"':""}><td><b>${esc(t.name)}</b></td>${ad?`<td>${t.alle?"<i>alle Konten (alt)</i>":esc(t.konto)}</td>`:""}<td class="mono">${esc(t.hinweis)}</td><td>${esc(t.erstellt)}</td><td>${esc(t.zuletzt||"–")}</td><td><button class="k" data-id="${esc(t.id)}" onclick="aztWeg(this.dataset.id)">Entfernen</button></td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">⚠ Noch kein Zugangstoken – ohne Token kann sich keine App mit Ihrem Konto anmelden.</p>';
 if(d.token){$("azt_neu").hidden=false;$("azt_wert").value=d.token;$("azt_wert").select()}else{$("azt_neu").hidden=true;$("azt_wert").value=""}}
async function aztLaden(){try{aztZeigen(await api("/api/app-zugangstoken"))}catch(e){}}
async function aztNeu(){aztZeigen(await api("/api/app-zugangstoken",{neu:true,name:$("azt_name").value.trim()||"App"},"log_azt"));$("azt_name").value=""}
async function aztWeg(id){if(!confirm("Zugangstoken entfernen? Apps, die ihn benutzen, haben danach keinen Zugang mehr."))return;aztZeigen(await api("/api/app-zugangstoken",{entfernen:id},"log_azt"))}
async function aztAlle(){if(!confirm("ALLE Zugangstokens aller Konten entfernen? Keine App hat dann mehr Zugang, bis neue erzeugt sind."))return;aztZeigen(await api("/api/app-zugangstoken",{alle_sperren:true},"log_azt"))}
async function siSpeichernAnmeldung(){const d=await api("/api/sicherheit-einstellungen",{abmelden_minuten:+$("si_ab").value,app_abmelden_minuten:+$("si_app").value,"2fa_merken_stunden":+$("si_merk").value},"log_sian");bnZeigen(d);$("log_sian").textContent="✔ Gespeichert. Die neue Abmelde-Zeit gilt nach dem nächsten Neuladen der Seite."}
function bnZeigen(d){BN=d;const box=$("bn_tab"),y=box.scrollTop;$("bn_2fa_pflicht").checked=!!d.zwei_faktor_pflicht;if(d.sicherheit){siWahl("si_ab",d.sicherheit.abmelden_minuten);siWahl("si_app",d.sicherheit.app_abmelden_minuten);siWahl("si_merk",d.sicherheit["2fa_merken_stunden"])}
 if(!$("bn_vorlage").options.length)$("bn_vorlage").innerHTML=Object.entries(d.vorlagen).map(([k,v])=>`<option value="${k}">${esc(v.text)}</option>`).join("")+'<option value="#admin">Administrator</option><option value="#gesperrt">Gesperrt (noch nicht freigeschaltet)</option>';
 let h="<table><tr><th>Benutzername</th><th>Name</th><th>Kontoart</th><th>Rechte</th><th>angelegt</th><th>zuletzt angemeldet</th><th>Sitzungen</th><th>2FA</th><th></th></tr>";
 for(const z of d.zeilen){const n=esc(z.name),offen=BNOFFEN.has(z.name);
  h+=`<tr class="${z.art=="gesperrt"?"recht-gesperrt":""}"><td><b>${n}</b>${z.name==d.ich?" <small>(Sie)</small>":""}</td>
  <td>${z.fest?esc(z.anzeige):`<input class="bn_anz" data-n="${n}" value="${esc(z.anzeige)}" style="min-width:170px">`}<br><input class="bn_mail" data-n="${n}" value="${esc(z.email||"")}" placeholder="E-Mail für Benachrichtigungen" style="min-width:170px;margin-top:4px;font-size:13px"></td>
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
 box.querySelectorAll(".bn_mail").forEach(e=>e.onchange=async()=>{if(e.dataset.n=="admin"){await api("/api/admin-email",{email:e.value},"log_bn")}else bnSpeichern({name:e.dataset.n,email:e.value})});
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
async function auLaden(){const d=await api("/api/automation",undefined,"log_au");AU=d;elLaden().catch(()=>{});if(ICH.admin)wbLaden().catch(()=>{});document.querySelectorAll(".au-schreib").forEach(e=>{if(e.id!="au_edit")e.hidden=!auDarf()});
 $("au_st").textContent=d.regeln.filter(r=>r.aktiv).length+" aktiv"+(d.warteschlange?" · "+d.warteschlange+" in Warteschlange":"");
 $("au_tab").innerHTML=d.regeln.length?"<table><tr><th>Regel</th><th>Wenn</th><th>Nur wenn</th><th>Dann</th><th>zuletzt</th><th></th></tr>"+d.regeln.map(r=>{const b=r.bedingung||{};const bed=[b.sparte&&"Sparte "+b.sparte,b.tarif&&"Tarif "+b.tarif,b.betrag_min!=null&&"Betrag ≥ "+b.betrag_min+" €"].filter(Boolean).join(", ")||"immer";
  return`<tr${r.aktiv?"":' style="opacity:.55"'}><td><b>${esc(r.name)}</b>${r.aktiv?"":" (aus)"}</td><td>${esc(d.ausloeser[r.ausloeser])}${r.ereignis_name?" „"+esc(r.ereignis_name)+"“":""}</td><td>${esc(bed)}</td><td>${r.aktionen.map(a=>esc(auAktText(a))).join("<br>")}</td><td>${esc(r.zuletzt||"–")}</td>
  <td style="white-space:nowrap">${auDarf()?`<button class="k" data-id="${esc(r.id)}" onclick="auBearbeiten(this.dataset.id)">Bearbeiten</button> <button class="k" data-id="${esc(r.id)}" onclick="auLoeschen(this.dataset.id)">Löschen</button>`:""}</td></tr>`}).join("")+"</table>":'<p class="hint" style="padding:12px">Noch keine Regel. Beispiel: „Wenn eine Parzelle bucht → E-Mail an den Vorstand“.</p>';
 $("au_verlauf").innerHTML=d.verlauf.length?"<table><tr><th>Zeit</th><th>Regel</th><th>Aktion</th><th>Ergebnis</th></tr>"+d.verlauf.map(v=>`<tr><td style="white-space:nowrap">${esc(v.zeit)}</td><td>${esc(v.regel)}</td><td>${esc(v.aktion)}</td><td>${v.ok?"✔ ":'<span class="fehler">✖ </span>'}${esc(v.text)}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Noch nichts ausgeführt.</p>';
 if(d.smtp){$("sm_host").value=d.smtp.host;$("sm_port").value=d.smtp.port;$("sm_sich").value=d.smtp.sicherheit;$("sm_anm").value=d.smtp.anmeldung||"login";$("sm_ben").value=d.smtp.benutzer;$("sm_abs").value=d.smtp.absender;$("sm_absn").value=d.smtp.absender_name;
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
 <div class="reihe">${a.typ=="email"?auFeld(i,"an",a.an||"","Empfänger (Komma-getrennt)")+auFeld(i,"an_kunde",a.an_kunde,"zusätzlich an den Kunden ({email} aus dem Ereignis)","check")+`<div><label for="au_a${i}_vorlage">Vorlage</label><select id="au_a${i}_vorlage" data-i="${i}" data-f="vorlage" class="au_f" onchange="setTimeout(auAktZeigen,0)"><option value="">eigener Text</option>${(AU.vorlagen||[]).map(v=>`<option value="${esc(v.id)}"${v.id==a.vorlage?" selected":""}>${esc(v.name)}</option>`).join("")}</select></div>`+auFeld(i,"betreff",a.betreff||"",a.vorlage?"Betreff (leer = aus der Vorlage)":"Betreff")+(a.vorlage?'<div class="hint" style="grid-column:1/-1">Text kommt aus der Vorlage (bearbeiten unter „E-Mail-Layout und Vorlagen“).</div>':`<div style="grid-column:1/-1"><label>Text</label><div id="au_re_${i}"></div></div>`)
  :a.typ=="buchen"?auFeld(i,"tarif",a.tarif||"{tarif}","Tarif","tarif")+'<div class="hint" style="grid-column:1/-1">Bucht im Manager (Kalkulation/Tarife). Ans Gateway geht das erst über „Tarife → An das Gateway übertragen“.</div>'
  :a.typ=="webhook"?auFeld(i,"url",a.url||"","Adresse (https://…)")+'<div class="hint" style="grid-column:1/-1">POST mit JSON: {"ereignis", "daten", "regel", "zeit"} – ohne WLAN-Passwort.</div>'
  :a.typ=="protokoll"?auFeld(i,"text",a.text||"","Text"):'<div class="hint">Entfernt die Buchung der Parzelle aus dem Ereignis (nur im Manager).</div>'}</div></div>`).join("")||'<p class="hint">Noch keine Aktion.</p>';
 document.querySelectorAll(".au_f").forEach(e=>e.oninput=e.onchange=()=>{AUE.aktionen[+e.dataset.i][e.dataset.f]=e.type=="checkbox"?e.checked:e.value});
 AUE.aktionen.forEach((a,i)=>{if(a.typ=="email"&&!a.vorlage&&$("au_re_"+i))reAufbauen("au_re_"+i,a.html||textZuHtml(a.text||""),h=>{a.html=h;a.text=""})})}
function auAktNeu(){}
function auAktionNeu(){const t=$("au_neu_typ").value;AUE.aktionen.push(t=="email"?{typ:t,an:"",an_kunde:false,betreff:"",text:""}:t=="buchen"?{typ:t,tarif:"{tarif}"}:t=="webhook"?{typ:t,url:""}:t=="protokoll"?{typ:t,text:""}:{typ:t});auAktZeigen()}
function auAktWeg(i){AUE.aktionen.splice(i,1);auAktZeigen()}
function auRegel(){return{...AUE,name:$("au_name").value,aktiv:$("au_aktiv").checked,ausloeser:$("au_aus").value,ereignis_name:$("au_evn").value,bedingung:{sparte:$("au_b_sp").value,tarif:$("au_b_tf").value,betrag_min:$("au_b_bt").value}}}
async function auSpeichern(){const r=auRegel();const d=await api("/api/automation-speichern",{regel:r},"log_aue");$("au_edit").hidden=true;await auLaden();$("log_au").textContent=d.log.join("\n")}
async function auProbe(){const r=auRegel();const d=await api("/api/automation-probe",{ausloeser:r.ausloeser,ereignis_name:r.ereignis_name,sparte:r.bedingung.sparte||auSparten()[0]||"BW",tarif:r.bedingung.tarif||AU.tarife[0],betrag:r.bedingung.betrag_min||"120"},"log_aue");
 $("log_aue").textContent=d.log.join("\n")+(d.ergebnisse.length?"\n"+d.ergebnisse.map(e=>(e.ok?"✔ ":"✖ ")+e.regel+" · "+e.aktion+": "+e.text).join("\n"):"")+"\n(Der Probelauf prüft die gespeicherten Regeln – Änderungen vorher speichern.)"}
async function auLoeschen(id){const r=AU.regeln.find(x=>x.id==id);if(!confirm("Regel „"+(r?r.name:id)+"“ löschen?"))return;await api("/api/automation-loeschen",{id},"log_au");auLaden()}
async function smSpeichern(){await api("/api/smtp-speichern",{host:$("sm_host").value,port:$("sm_port").value,sicherheit:$("sm_sich").value,anmeldung:$("sm_anm").value,benutzer:$("sm_ben").value,passwort:$("sm_pw").value,absender:$("sm_abs").value,absender_name:$("sm_absn").value},"log_sm");$("sm_pw").value="";auLaden()}
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

# Mitglied anlegen oder aktualisieren (gleiche E-Mail bzw. Parzelle + Nachname = aktualisieren) – Recht „mitglieder“
curl -X POST -H "Authorization: Bearer sn_…" -H "Content-Type: application/json" \\
  -d '{"vorname":"Erika","nachname":"Muster","email":"erika@example.de","telefon":"03381 12345","sparte":"BW","parzelle":12}' ${o}/api/v1/mitglied

# Anfrage (Ticket) aus dem Kontaktformular – Recht „tickets“; Antwort enthält die Ticket-Nummer
curl -X POST -H "Authorization: Bearer sn_…" -H "Content-Type: application/json" \\
  -d '{"betreff":"WLAN geht nicht","text":"Seit gestern kein Netz","name":"Erika Muster","email":"erika@example.de","sparte":"BW","parzelle":12,"prioritaet":"hoch"}' ${o}/api/v1/ticket
curl -H "Authorization: Bearer sn_…" "${o}/api/v1/ticket?nr=T-0001"

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
 const sel=$("zt_stf"),alt=sel.value;sel.innerHTML=d.standorte.map(s=>`<option value="${s.nr}">${esc(s.name)} · ${s.gebucht} zugeteilt · ${s.gw_geplant} Gateway${s.gw_geplant!=1?"s":""} geplant</option>`).join("");if(d.standorte.some(s=>String(s.nr)==alt))sel.value=alt;ztZeigen();zpLaden().catch(()=>{})}
function ztZeigen(){const d=ZT;if(!d)return;const st=d.standorte.find(s=>String(s.nr)==$("zt_stf").value);if(!st){$("zt_tab").innerHTML="";return}
 const darf=ICH.admin||ICH.bereiche.planung=="schreiben",farbe={anlegen:"#b26b00",aktiv:"",entfernen:"#b00020"};
 $("zt_tab").innerHTML="<table><tr><th>Gateway</th><th>belegt</th><th>VLANs</th><th>Parzellen (VLAN)</th><th></th></tr>"+st.gateways.map(g=>`<tr><td><b>GW ${g.gw}</b>${g.geplant?"":" <small>(nicht geplant)</small>"}</td><td>${g.belegt} / ${d.pg}${g.anlegen?`<br><small style="color:${farbe.anlegen}">${g.anlegen} anzulegen</small>`:""}${g.entfernen?`<br><small style="color:${farbe.entfernen}">${g.entfernen} zu entfernen</small>`:""}</td>
  <td>${g.vlans}<br><small>${g.belegt} + ${g.dienstnetze} Dienst</small></td><td>${g.sparten.map(s=>`<b class="mono">${esc(s.kz)}</b> ${s.parzellen.map(x=>`<span title="${esc(d.status_text[x.status])} · VLAN ${x.vlan}" style="${farbe[x.status]?"color:"+farbe[x.status]+";font-weight:600":""}${x.status=="entfernen"?";text-decoration:line-through":""}">${x.p}</span>`).join(", ")}`).join("<br>")||'<span class="hint">frei</span>'}</td>
  <td>${darf&&d.an&&(g.belegt||g.gw==1)?`<button class="k" onclick="ztUebernehmen(${st.nr},${g.gw})">${d.aktiv_gateway.standort==st.nr&&d.aktiv_gateway.gw==g.gw&&d.aktiv_gateway.dynamisch?"✔ aktive Planung":"Als Planung übernehmen"}</button>`:""}</td></tr>`).join("")+"</table>"+
  '<p class="hint" style="padding:6px 10px">Orange = gebucht, Netz noch anzulegen · rot durchgestrichen = Buchung gelöscht, Netz noch am Gateway · Maus über die Nummer zeigt die VLAN-ID.</p>'}
let ZP=null,ZPA={};
async function zpLaden(){if(!ZT||!ZT.an)return $("zp_box").hidden=true;$("zp_box").hidden=false;const st=$("zt_stf").value;if(!st)return;ZP=await api("/api/zuteilung-parzellen?standort="+encodeURIComponent(st),undefined,"log_zp");ZPA={};
 const alt=$("zp_sp").value;$("zp_sp").innerHTML=ZP.sparten.map(s=>`<option value="${esc(s.kz)}">${esc(s.name)} (${esc(s.kz)}) – ${s.zeilen.filter(z=>z.tarif).length} gebucht</option>`).join("");if(ZP.sparten.some(s=>s.kz==alt))$("zp_sp").value=alt;
 $("zp_alle").innerHTML=zpOptionen(null);zpZeigen()}
function zpOptionen(w){let o=`<option value="0"${!w?" selected":""}>Automatisch</option>`;for(let g=1;g<=ZP.gw_max;g++)o+=`<option value="${g}"${w==g?" selected":""}>Gateway ${g} (${ZP.belegung[g]||0}/${ZP.pg})</option>`;return o}
function zpZeigen(){if(!ZP)return;const s=ZP.sparten.find(x=>x.kz==$("zp_sp").value);if(!s)return $("zp_tab").innerHTML="";const nur=$("zp_nur").checked,darf=ICH.admin||(ICH.bereiche.netzplanung=="schreiben"&&!ICH.sparten);
 const L=s.zeilen.filter(z=>!nur||z.tarif||z.gw);const txt={anlegen:"Netz anlegen",aktiv:"Netz am Gateway",entfernen:"Buchung gelöscht"};
 $("zp_tab").innerHTML=L.length?"<table><tr><th>Parzelle</th><th>Tarif</th><th>jetzt</th><th>Gateway</th><th>Status</th></tr>"+L.map(z=>{const k=s.kz+"-"+z.p,w=k in ZPA?ZPA[k]:(z.gw&&z.fest?z.gw:(z.gw?0:z.vorgabe||0));
  return`<tr><td><b>${z.p}</b></td><td>${esc(z.tarif||"–")}</td><td>${z.gw?"GW "+z.gw+(z.fest?" (fest)":""):(z.vorgabe?"Vorgabe GW "+z.vorgabe:"–")}</td><td>${darf&&z.status!="entfernen"?`<select class="zp_w" data-k="${esc(k)}" style="min-width:200px">${zpOptionen(w)}</select>`:"–"}</td><td>${esc(txt[z.status]||(z.tarif?"":"nicht gebucht"))}${z.alt_gw?" · altes Netz an GW "+z.alt_gw+" entfernen":""}</td></tr>`}).join("")+"</table>":'<p class="hint" style="padding:10px">Keine gebuchten Parzellen in dieser Sparte – Haken „nur gebuchte“ entfernen, um Vorgaben zu setzen.</p>';
 document.querySelectorAll(".zp_w").forEach(e=>e.onchange=()=>{ZPA[e.dataset.k]=+e.value;e.style.borderColor="var(--green)"})}
function zpAlleSetzen(){const w=+$("zp_alle").value;document.querySelectorAll(".zp_w").forEach(e=>{e.value=String(w);ZPA[e.dataset.k]=w;e.style.borderColor="var(--green)"})}
async function zpSpeichern(){if(!Object.keys(ZPA).length)return $("log_zp").textContent="Keine Änderung.";const d=await api("/api/zuteilung-setzen",{standort:+$("zt_stf").value,aenderungen:ZPA},"log_zp");ZT=d;ztZeigen();const l=d.log;await zpLaden();$("log_zp").textContent=l.join("\n");PLAN=null;planLaden(true)}
async function zpVerdichten(){if(!confirm("Alle nicht fest zugeordneten Buchungen dieses Standorts auf möglichst wenige Gateways legen (von Gateway 1 an)? Am Gateway ändert sich dadurch noch nichts."))return;
 const d=await api("/api/zuteilung-verdichten",{standort:+$("zt_stf").value},"log_zp");ZT=d;ztZeigen();const l=d.log;await zpLaden();$("log_zp").textContent=l.join("\n");PLAN=null;planLaden(true)}
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

// ---- kleiner Text-Editor (fett, kursiv, Überschrift, Listen, Link, Platzhalter) – der Server lässt nur sichere Elemente durch
function textZuHtml(t){return String(t||"").split(/\n\n+/).filter(x=>x.trim()).map(x=>"<p>"+esc(x).replace(/\n/g,"<br>")+"</p>").join("")}
const RE_PH=["{vorname}","{nachname}","{name}","{sparte_name}","{parzelle}","{tarif}","{preis}","{wlan}","{passwort}","{betrag}","{referenz}","{datum}","{ticket}","{betreff}","{status}","{zustaendig}"];
function reAufbauen(id,html,aendern){const box=$(id);if(!box)return;
 box.innerHTML=`<div class="re-leiste"><button type="button" data-c="bold" title="fett"><b>F</b></button><button type="button" data-c="italic" title="kursiv"><i>K</i></button><button type="button" data-c="underline" title="unterstrichen"><u>U</u></button>
 <button type="button" data-b="h2" title="Überschrift">Ü1</button><button type="button" data-b="h3" title="Zwischenüberschrift">Ü2</button><button type="button" data-b="p" title="normaler Absatz">¶</button>
 <button type="button" data-c="insertUnorderedList" title="Liste">• Liste</button><button type="button" data-c="insertOrderedList" title="nummerierte Liste">1. Liste</button><button type="button" data-l="1" title="Link">Link</button><button type="button" data-c="removeFormat" title="Formatierung entfernen">⌫</button>
 <select title="Platzhalter einfügen"><option value="">Platzhalter …</option>${RE_PH.map(p=>`<option>${p}</option>`).join("")}</select></div><div class="re-feld" contenteditable="true"></div>`;
 const f=box.querySelector(".re-feld");f.innerHTML=html||"<p><br></p>";const melden=()=>aendern&&aendern(f.innerHTML);
 f.addEventListener("input",melden);f.addEventListener("blur",melden);
 box.querySelectorAll("button").forEach(b=>b.onmousedown=e=>{e.preventDefault();f.focus();if(b.dataset.c)document.execCommand(b.dataset.c);else if(b.dataset.b)document.execCommand("formatBlock",false,b.dataset.b);
  else if(b.dataset.l){const u=prompt("Adresse (https://… oder mailto:…)","https://");if(u&&/^(https?:\/\/|mailto:)/i.test(u))document.execCommand("createLink",false,u)}melden()});
 const sel=box.querySelector("select");sel.onchange=()=>{if(sel.value){f.focus();document.execCommand("insertText",false,sel.value);sel.value="";melden()}}}
function reWert(id){const f=$(id)&&$(id).querySelector(".re-feld");return f?f.innerHTML:""}

let EL=null,EVAKT="";
async function elLaden(){const d=await api("/api/email-layout",undefined,"log_el");EL=d;const l=d.layout;
 $("el_kopf").value=l.kopf;$("el_schrift").value=l.schrift;$("el_fk").value=l.farbe_kopf;$("el_fkt").value=l.farbe_kopf_text;$("el_fa").value=l.farbe_akzent;$("el_fh").value=l.farbe_hinter;$("el_ft").value=l.farbe_text;
 $("el_breite").value=l.breite;$("el_logo").checked=l.logo;$("el_splogo").checked=l.spartenlogo!==false;$("el_aktiv").checked=l.aktiv;$("el_fuss").value=l.fuss;elLogoListe(d.logos||[],l.logo_unterlage||"");
 const darf=ICH.admin||ICH.bereiche.automationen=="schreiben";document.querySelectorAll(".el-schreib").forEach(e=>e.hidden=!darf);
 ["el_kopf","el_schrift","el_fk","el_fkt","el_fa","el_fh","el_ft","el_breite","el_logo","el_splogo","el_logoq","el_fuss"].forEach(i=>$(i).oninput=$(i).onchange=elVorschauBald);
 evListe(d.vorlagen);if(!d.logo)$("log_el").textContent="ℹ Kein Logo hinterlegt – unter „Kartendesign“ hochladen oder hier eines aus den Unterlagen wählen."}
function elWerte(){return{kopf:$("el_kopf").value,schrift:$("el_schrift").value,farbe_kopf:$("el_fk").value,farbe_kopf_text:$("el_fkt").value,farbe_akzent:$("el_fa").value,farbe_hinter:$("el_fh").value,farbe_text:$("el_ft").value,breite:+$("el_breite").value||600,logo:$("el_logo").checked,spartenlogo:$("el_splogo").checked,logo_unterlage:$("el_logoq").value,aktiv:$("el_aktiv").checked,fuss:$("el_fuss").value}}
function elLogoListe(logos,wahl){$("el_logoq").innerHTML='<option value="">wie Zugangskarten (Kartendesign)</option>'+logos.map(x=>`<option value="${esc(x.id)}">${esc(x.ordner+" / "+x.name)}</option>`).join("");$("el_logoq").value=wahl;if($("el_logoq").value!==wahl)$("el_logoq").value=""}
async function elLogoWahl(){const id=await logoWahlFenster("Logo für die E-Mails",$("el_logoq").value,"wie Zugangskarten (Kartendesign)");if(id===null)return;if(![...$("el_logoq").options].some(o=>o.value==id)){const d=await api("/api/email-layout");elLogoListe(d.logos||[],id)}$("el_logoq").value=id;elVorschau()}
let ELT=null;function elVorschauBald(){clearTimeout(ELT);ELT=setTimeout(elVorschau,350)}
async function elVorschau(){try{const r=await fetch("/api/email-vorschau",{method:"POST",headers:{"X-Token":T,"Content-Type":"application/json"},body:JSON.stringify({layout:elWerte(),betreff:$("ev_betreff").value,html:reWert("ev_editor")})});const d=await r.json();if(r.ok)$("el_vorschau").srcdoc=d.html}catch(e){}}
async function elSpeichern(){const d=await api("/api/email-layout",elWerte(),"log_el");EL=d;elVorschau()}
async function elTest(){await api("/api/email-test",{an:$("el_test_an").value,html:reWert("ev_editor")},"log_el")}
function evListe(v){EL.vorlagen=v;$("ev_wahl").innerHTML=v.length?v.map(x=>`<option value="${esc(x.id)}">${esc(x.name)}</option>`).join(""):'<option value="">– noch keine Vorlage –</option>';
 if(v.some(x=>x.id==EVAKT))$("ev_wahl").value=EVAKT;evWahl()}
function evWahl(){const v=(EL.vorlagen||[]).find(x=>x.id==$("ev_wahl").value);EVAKT=v?v.id:"";$("ev_name").value=v?v.name:"Neue Vorlage";$("ev_betreff").value=v?v.betreff:"";
 reAufbauen("ev_editor",v?v.html:"<h2>Hallo {vorname},</h2><p>vielen Dank für Ihre Buchung des Tarifs <b>{tarif}</b> für Parzelle {parzelle}.</p><p>Ihr WLAN: <b>{wlan}</b><br>Passwort: <b>{passwort}</b></p><p>Viele Grüße<br>Ihr SparteNet-Team</p>",elVorschauBald);
 $("ev_betreff").oninput=elVorschauBald;elVorschau()}
function evNeu(){EVAKT="";$("ev_wahl").value="";$("ev_name").value="Neue Vorlage";$("ev_betreff").value="";reAufbauen("ev_editor","<p>Hallo {vorname},</p><p><br></p>",elVorschauBald);$("ev_name").focus();elVorschau()}
async function evSpeichern(){const d=await api("/api/email-vorlage-speichern",{vorlage:{id:EVAKT,name:$("ev_name").value,betreff:$("ev_betreff").value,html:reWert("ev_editor")}},"log_el");EVAKT=d.id;evListe(d.vorlagen);if(AU)AU.vorlagen=d.vorlagen}
async function evLoeschen(){if(!EVAKT)return;if(!confirm("Vorlage „"+$("ev_name").value+"“ löschen?"))return;const d=await api("/api/email-vorlage-loeschen",{id:EVAKT},"log_el");EVAKT="";evListe(d.vorlagen);if(AU)AU.vorlagen=d.vorlagen}

// ---- Mitglieder
let MG=null,MGIMP=null;
const mgDarf=()=>ICH.admin||ICH.bereiche.mitglieder=="schreiben";
async function mgLaden(){const d=await api("/api/mitglieder",undefined,"log_mg");MG=d;document.querySelectorAll(".mg-schreib").forEach(e=>e.hidden=!mgDarf());
 const sp=Object.entries(d.sparten).sort((a,b)=>a[0].localeCompare(b[0]));const f=$("mg_f").value;
 $("mg_f").innerHTML='<option value="">alle Sparten</option>'+sp.map(([k,n])=>`<option value="${esc(k)}">${esc(k)} – ${esc(n)}</option>`).join("");$("mg_f").value=f;
 $("mg_sp").innerHTML='<option value="">–</option>'+sp.map(([k,n])=>`<option value="${esc(k)}">${esc(k)} – ${esc(n)}</option>`).join("");$("mg_imp_sp").innerHTML='<option value="">aus der Datei</option>'+sp.map(([k])=>`<option>${esc(k)}</option>`).join("");
 $("mg_st").textContent=d.zeilen.length+" Mitglieder";mgZeigen()}
function mgZeigen(){const d=MG;if(!d)return;const f=$("mg_f").value,q=$("mg_such").value.trim().toLowerCase(),nur=$("mg_nur").checked;
 const L=d.zeilen.filter(z=>(!f||z.sparte==f)&&(!nur||z.tarif)&&(!q||[z.vorname,z.nachname,z.email,z.telefon,z.notiz,String(z.parzelle),z.mobil,...(z.weitere||[]).flatMap(w=>[w.vorname,w.nachname,w.email,w.telefon,w.mobil])].join(" ").toLowerCase().includes(q)));
 $("mg_tab").innerHTML=L.length?"<table><tr><th>Name</th><th>Sparte</th><th>Parzelle</th><th>Tarif</th><th>E-Mail</th><th>Telefon</th><th>Notiz</th><th></th></tr>"+L.map(z=>`<tr><td><b>${esc(z.nachname)}</b>${z.vorname?", "+esc(z.vorname):""}${(z.weitere||[]).length?` <span class="status" title="${esc(z.weitere.map(w=>(w.vorname+" "+w.nachname).trim()+(w.email?" <"+w.email+">":"")).join("\n"))}">+${z.weitere.length} Person${z.weitere.length>1?"en":""}</span>`:""}</td><td>${esc(z.sparte||"–")}</td><td>${esc(z.parzelle||"–")}</td><td>${z.tarif?'<span class="status ok">'+esc(z.tarif)+"</span>":"–"}</td>
  <td>${z.email?`<a href="mailto:${esc(z.email)}">${esc(z.email)}</a>`:"–"}</td><td>${[z.telefon,z.mobil].filter(Boolean).map(t=>`<a href="tel:${esc(t.replace(/[^0-9+]/g,""))}">${esc(t)}</a>`).join("<br>")||"–"}</td><td>${esc(z.notiz||"")}</td>
  <td style="white-space:nowrap"><button class="k" data-id="${esc(z.id)}" onclick="akteZeigen(this.dataset.id)" title="Zeitleiste: Anfragen, Rechnungen, Vertrag, Buchungen">Akte</button> ${mgDarf()?`<button class="k" data-id="${esc(z.id)}" onclick="mgBearbeiten(this.dataset.id)">Bearbeiten</button>`:""}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Keine Mitglieder'+(f||q?" für diesen Filter":"")+".</p>";
 const o=d.ohne_mitglied.filter(x=>!f||x.sparte==f);$("mg_ohne").innerHTML=o.length?`<p class="hint">Gebuchte Parzellen ohne Mitglied (${o.length}): `+o.slice(0,60).map(x=>`<a href="#" data-s="${esc(x.sparte)}" data-p="${x.parzelle}" onclick="mgNeu(this.dataset.s,this.dataset.p);return false">${esc(x.sparte)} ${x.parzelle}</a>`).join(", ")+(o.length>60?" …":"")+"</p>":""}
function mgNeu(sp,p){mgFormular({id:"",vorname:"",nachname:"",email:"",telefon:"",mobil:"",sparte:sp||$("mg_f").value||"",parzelle:p||"",notiz:""})}
function mgBearbeiten(id){mgFormular(MG.zeilen.find(z=>z.id==id))}
function mgWeitereZeile(w){w=w||{};const z=document.createElement("div");z.className="mg-w";z.style.cssText="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr)) 46px;gap:10px;align-items:end;margin-bottom:6px";
 z.innerHTML=[["vorname","Vorname"],["nachname","Nachname"],["email","E-Mail"],["telefon","Telefon"],["mobil","Mobil"]].map(([k,l])=>`<div><label>${l}</label><input data-w="${k}" maxlength="120" autocomplete="off"${k=="email"?' type="email"':k=="telefon"||k=="mobil"?' type="tel"':""} value="${esc(w[k]||"")}"></div>`).join("")+'<div style="flex:0 0 auto"><button class="k r" type="button" title="Person entfernen" onclick="this.closest(\'.mg-w\').remove()">✕</button></div>';
 $("mg_weitere").appendChild(z)}
function mgFormular(m){$("mg_form").hidden=false;$("mg_form_t").textContent=m.id?"Mitglied bearbeiten":"Neues Mitglied";$("mg_id").value=m.id;["vorname","nachname","email","telefon","mobil","parzelle","notiz"].forEach(k=>$("mg_"+k).value=m[k]||"");$("mg_sp").value=m.sparte||"";
 $("mg_weitere").innerHTML="";(m.weitere||[]).forEach(w=>mgWeitereZeile(w));
 $("mg_loeschen").hidden=!m.id;$("mg_auskunft").hidden=!m.id;$("mg_dsgvo").hidden=!m.id;$("mg_form").scrollIntoView({behavior:"smooth",block:"center"});$("mg_vorname").focus()}
async function mgSpeichern(){const m={id:$("mg_id").value,sparte:$("mg_sp").value};["vorname","nachname","email","telefon","mobil","parzelle","notiz"].forEach(k=>m[k]=$("mg_"+k).value.trim());
 m.weitere=[...document.querySelectorAll("#mg_weitere .mg-w")].map(z=>{const w={};z.querySelectorAll("[data-w]").forEach(i=>w[i.dataset.w]=i.value.trim());return w}).filter(w=>w.vorname||w.nachname||w.email||w.telefon||w.mobil);
 const d=await api("/api/mitglied-speichern",{mitglied:m},"log_mgf");MG=d;mgZeigen();$("mg_form").hidden=true;$("log_mg").textContent=d.log.join("\n")}
async function mgLoeschen(){if(!confirm("Mitglied „"+$("mg_vorname").value+" "+$("mg_nachname").value+"“ löschen?"))return;const d=await api("/api/mitglied-loeschen",{id:$("mg_id").value},"log_mgf");MG=d;mgZeigen();$("mg_form").hidden=true;$("log_mg").textContent=d.log.join("\n")}
async function mgImport(uebernehmen){const f=$("mg_datei").files[0];if(!f)return $("log_mgi").textContent="Bitte eine Datei wählen (.xlsx oder .csv).";
 const p=new URLSearchParams({name:f.name,sparte:$("mg_imp_sp").value,uebernehmen:uebernehmen?"1":"0"});if(uebernehmen&&!confirm("Liste jetzt übernehmen? Vorhandene Mitglieder (gleiche E-Mail oder gleiche Parzelle und Name) werden aktualisiert."))return;
 const d=await api("/api/mitglieder-import?"+p.toString(),f,"log_mgi");MGIMP=d;
 $("mg_imp_tab").innerHTML="<table><tr><th>Zeile</th><th>Ergebnis</th><th>Name</th><th>Sparte</th><th>Parzelle</th><th>E-Mail</th><th>Hinweis</th></tr>"+d.zeilen.map(z=>`<tr class="${z.status=="Fehler"?"falsch":z.status=="aktualisieren"?"geaendert":""}"><td>${z.zeile}</td><td>${esc(z.status)}</td><td>${esc(z.name||"")}</td><td>${esc(z.sparte||"")}</td><td>${esc(z.parzelle||"")}</td><td>${esc(z.email||"")}</td><td>${esc(z.fehler||"")}</td></tr>`).join("")+"</table>";
 $("mg_imp_ok").disabled=uebernehmen||!(d.neu+d.geaendert);if(uebernehmen){$("mg_datei").value="";mgLaden()}}
async function mgExport(){try{await siBlob("/api/mitglieder-export",null,"SparteNet_Mitglieder.csv")}catch(e){$("log_mg").innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>'}}

// ---- Tickets
let TK=null,TKA=null;
const tkDarf=()=>ICH.admin||ICH.bereiche.tickets=="schreiben";
async function tkLaden(){const p=new URLSearchParams({status:$("tk_fs").value||"offen",zustaendig:$("tk_fz").value,q:$("tk_such").value.trim()});const d=await api("/api/tickets?"+p.toString(),undefined,"log_tk");TK=d;if(d.einstellungen&&document.activeElement!==$("tk_auto"))$("tk_auto").value=d.einstellungen.auto_schliessen_tage;
 document.querySelectorAll(".tk-schreib").forEach(e=>e.hidden=!tkDarf());$("tk_st").textContent=d.offen+" offen"+(d.meine?" · "+d.meine+" für Sie":"");
 const nb=$("n_tickets");if(nb)nb.textContent="Tickets"+(d.meine?" ("+d.meine+")":"");
 $("tk_tab").innerHTML=d.zeilen.length?"<table><tr><th>Nr.</th><th>Betreff</th><th>Kontakt</th><th>Sparte</th><th>Kategorie</th><th>Priorität</th><th>Status</th><th>Zuständig</th><th>eingegangen</th></tr>"+d.zeilen.map(z=>`<tr style="cursor:pointer${z.id==TKA?";outline:2px solid var(--green)":""}" data-id="${esc(z.id)}" onclick="tkOeffnen(this.dataset.id)"><td class="mono"><b>${esc(z.nr)}</b></td><td>${esc(z.betreff)}${z.antworten?` <small>(${z.antworten})</small>`:""}</td><td>${esc(z.kontakt.name||z.kontakt.email||"–")}${tkArt(z.kontakt)}</td><td>${esc(z.sparte||"")}${z.parzelle?" "+esc(z.parzelle):""}</td><td>${esc(z.kategorie)}</td><td class="tk-prio-${esc(z.prioritaet)}">${esc(d.prioritaeten[z.prioritaet]||z.prioritaet)}</td><td>${z.status=="neu"?'<span class="status">neu</span>':esc(d.status[z.status]||z.status)}</td><td>${esc(z.zustaendig||"–")}</td><td>${esc(z.erstellt)}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Keine Tickets für diesen Filter.</p>';
 const opt=(o,w)=>o.map(([k,t])=>`<option value="${esc(k)}"${k==w?" selected":""}>${esc(t)}</option>`).join("");
 $("tkn_kat").innerHTML=opt(d.kategorien.map(k=>[k,k]));$("tkn_zu").innerHTML='<option value="">niemand</option>'+opt(d.konten.map(k=>[k,k]));
 if(!$("tkn_sp").options.length){const sp=Object.keys((PLAN&&PLAN.sparten?Object.fromEntries(PLAN.sparten.map(s=>[s.kz,1])):{}));$("tkn_sp").innerHTML='<option value="">–</option>'+sp.map(k=>`<option>${esc(k)}</option>`).join("")}
 if(TKA&&d.zeilen.some(z=>z.id==TKA))tkOeffnen(TKA,true)}
function tkArt(k){if(k.geprueft)return ' <small style="color:var(--green)" title="Vorname, Nachname, E-Mail, Sparte und Parzelle passen zu einem Mitglied">✔ Mitglied geprüft</small>';
 if(k.art=="interessent")return ' <small class="status">Interessent</small>';if(k.art=="kein_mitglied")return ' <small class="status">kein Mitglied</small>';return""}
async function tkOeffnen(id,still){TKA=id;const r=await api("/api/ticket?id="+encodeURIComponent(id),undefined,still?null:"log_tkd");const t=r.ticket,d=TK,zu=t.status=="geschlossen",w=tkDarf()&&!zu;const k=t.kontakt||{},m=r.mitglied;
 const opt=(o,v)=>o.map(([a,b])=>`<option value="${esc(a)}"${a==v?" selected":""}>${esc(b)}</option>`).join("");
 $("tk_detail").hidden=false;$("tk_detail_t").textContent=t.nr+" · "+t.betreff;
 const stat=Object.entries(d.status).filter(([a])=>a!="geschlossen"||zu);
 const sp=(zu?`<div class="tk-zu"><b>✔ Geschlossen</b> am ${esc(t.geschlossen||"")}${t.loesung?`<br><b>Lösung:</b> ${esc(t.loesung)}`:""}${tkDarf()?`<div class="knoepfe" style="margin-top:8px"><button class="k" onclick="tkWiederOeffnen()">Wieder öffnen</button></div>`:""}</div>`
   :(tkDarf()?`<details class="tk-zu" id="tk_abschluss"><summary style="cursor:pointer;font-weight:600">Abschließen …</summary><label for="tk_loesung">Lösung / was wurde getan? (sieht der Pächter auch auf der Kontakt-Seite)</label><textarea id="tk_loesung" rows="3" style="width:100%;font:inherit" maxlength="3000"></textarea>
   <label style="display:flex;gap:6px;align-items:center;margin:6px 0"><input type="checkbox" id="tk_ab_mail" style="width:auto"${k.email?" checked":" disabled"}> Kontakt per E-Mail informieren</label><button class="k p" onclick="tkAbschliessen()">Ticket abschließen</button></details>`:""));
 const seite=`<aside class="tk-seite"><h4>👤 Mitglied</h4>`+(m?`<div><b>${esc(m.name)}</b><br><small>${esc(m.sparte)} · Parzelle ${esc(m.parzelle)}${m.tarif?" · Tarif "+esc(m.tarif):""}${m.fest?"":" · über die E-Mail-Adresse erkannt"}</small></div>
   <div class="knoepfe" style="margin-top:6px">${(ICH.admin||(ICH.bereiche.mitglieder||"kein")!="kein")?`<button class="k" onclick="akteZeigen('${esc(m.id)}')">Akte öffnen</button>`:""}${tkDarf()?`<button class="k" onclick="tkZuordnen()">Ändern</button>`:""}</div>`
   :`<p class="hint" style="margin:0">${k.art=="interessent"?"Interessent – noch kein Mitglied.":k.art=="kein_mitglied"?"Kein Mitglied einer Sparte.":"Kein Mitglied zugeordnet."}</p>${tkDarf()?`<div class="knoepfe" style="margin-top:6px"><button class="k" onclick="tkZuordnen()">Mitglied zuordnen …</button></div>`:""}`)
   +`<div id="tk_zuordnen"></div><h4 style="margin-top:14px">🕘 Frühere Anfragen (${r.frueher.length})</h4>`
   +(r.frueher.length?r.frueher.map(x=>`<button class="tk-frueh" onclick="tkOeffnen('${esc(x.id)}')"><b>${esc(x.nr)}</b> · <small>${esc((x.erstellt||"").slice(0,10))}</small> <span class="status${x.status=="geschlossen"||x.status=="erledigt"?" ok":""}">${esc(d.status[x.status]||x.status)}</span><br>${esc(x.betreff)}${x.loesung?`<br><small>Lösung: ${esc(x.loesung.slice(0,140))}</small>`:""}</button>`).join(""):'<p class="hint" style="margin:0">Keine.</p>')+"</aside>";
 $("tk_felder").innerHTML=`<div class="tk-raster"><div><div class="reihe"><div><label>Status</label><select id="tkd_status"${w?"":" disabled"}>${opt(stat,t.status)}</select></div><div><label>Zuständig</label><select id="tkd_zu"${w?"":" disabled"}><option value="">niemand</option>${opt(d.konten.map(x=>[x,x]),t.zustaendig)}</select></div>
  <div><label>Priorität</label><select id="tkd_prio"${w?"":" disabled"}>${opt(Object.entries(d.prioritaeten),t.prioritaet)}</select></div><div><label>Kategorie</label><select id="tkd_kat"${w?"":" disabled"}>${opt([...new Set(d.kategorien.concat([t.kategorie]))].map(x=>[x,x]),t.kategorie)}</select></div></div>
  <p class="hint" style="margin-top:10px"><b>Kontakt:</b> ${esc(k.name||"–")}${tkArt(k)}${k.email?` · <a href="mailto:${esc(k.email)}">${esc(k.email)}</a>`:""}${k.telefon?` · <a href="tel:${esc(k.telefon)}">${esc(k.telefon)}</a>`:""}${t.sparte?" · Sparte "+esc(t.sparte):""}${t.parzelle?" Parzelle "+esc(t.parzelle):""} · eingegangen ${esc(t.erstellt)} (${esc(t.quelle)})</p>${tkAntrag(t.antrag)}${sp}
  <div class="tk-verlauf" style="border-color:var(--navy)"><small>Anfrage</small><br>${esc(t.text||"(ohne Text)")}</div>`+t.verlauf.filter(v=>v.art!="angelegt").map(v=>`<div class="tk-verlauf ${esc(v.art)}"><small>${esc(v.zeit)} · ${esc(v.wer)} · ${{kommentar:"Notiz",antwort:"Antwort",aenderung:"Änderung",abschluss:"Abschluss"}[v.art]||esc(v.art)}</small><br>${esc(v.text)}</div>`).join("")+`</div>${seite}</div>`;
 ["tkd_status","tkd_zu","tkd_prio","tkd_kat"].forEach(i=>{const e=$(i);if(e)e.onchange=tkFelderSpeichern});
 $("tk_antwort").hidden=!w;$("tk_an_kontakt").disabled=!k.email;$("tk_an_kontakt_l").title=k.email?"":"keine E-Mail-Adresse beim Kontakt";
 $("tk_vorlage").innerHTML='<option value="">ohne Vorlage</option>'+((EL&&EL.vorlagen)||[]).map(v=>`<option value="${esc(v.id)}">${esc(v.name)}</option>`).join("");
 if(!$("tk_re").innerHTML)reAufbauen("tk_re","<p><br></p>",null);if(!still)$("tk_detail").scrollIntoView({behavior:"smooth",block:"start"})}
async function tkAutoSpeichern(){const d=await api("/api/ticket-einstellungen",{auto_schliessen_tage:+$("tk_auto").value},"log_tk");$("tk_auto").value=d.einstellungen.auto_schliessen_tage}
function tkAntrag(a){if(!a)return"";const was={wechsel:(a.tarif_alt?"Wechsel "+a.tarif_alt+" → ":"Wechsel zu ")+a.tarif,neu:"Buchung "+a.tarif,verlaengern:"Verlängerung "+a.tarif}[a.art]||a.tarif;
 const kopf=`<b>📝 Tarif-Antrag:</b> ${esc(was)} · ${esc(a.sparte)} Parzelle ${esc(a.parzelle)}`;
 if(a.status!="offen")return `<div class="tk-zu">${kopf}<br>${a.status=="freigegeben"?"✔ Freigegeben":"✖ Abgelehnt"} am ${esc(a.entschieden||"")} von ${esc(a.von||"")}${a.grund?" – "+esc(a.grund):""}</div>`;
 return `<div class="tk-zu" style="border-color:#c9a227;background:#fff8e1">${kopf}<br><small>Wartet auf Freigabe. Freigeben bucht den Tarif sofort und informiert das Mitglied per E-Mail; danach wird das Ticket geschlossen.</small>`+
  (bereichStufe("buchungen")=="schreiben"?`<div class="knoepfe" style="margin-top:8px"><button class="k p" onclick="tkAntragEntscheiden(true)">Freigeben und buchen</button><button class="k" onclick="tkAntragEntscheiden(false)">Ablehnen …</button></div>`:'<br><small>Freigeben darf, wer Buchungen bearbeiten kann.</small>')+"</div>"}
async function tkAntragEntscheiden(ja){let grund="";if(ja){if(!confirm("Antrag freigeben und den Tarif jetzt buchen?"))return}else{grund=prompt("Grund der Ablehnung (geht per E-Mail an das Mitglied):","");if(!grund)return}
 await api("/api/tarif-antrag",{id:TKA,freigeben:ja,grund},"log_tkd");await tkOeffnen(TKA,true);tkLaden()}
async function tkAbschliessen(){const l=$("tk_loesung").value.trim();if(!l){$("log_tkd").textContent="✖ Bitte kurz die Lösung beschreiben.";$("tk_loesung").focus();return}
 const mail=$("tk_ab_mail").checked;if(mail&&!confirm("Ticket abschließen und den Kontakt per E-Mail informieren?"))return;await api("/api/ticket-schliessen",{id:TKA,loesung:l,an_kontakt:mail},"log_tkd");await tkOeffnen(TKA,true);tkLaden()}
async function tkWiederOeffnen(){const g=prompt("Ticket wieder öffnen – Grund (optional):","");if(g===null)return;await api("/api/ticket-schliessen",{id:TKA,wieder_oeffnen:true,grund:g},"log_tkd");await tkOeffnen(TKA,true);tkLaden()}
async function tkZuordnen(){const box=$("tk_zuordnen");box.innerHTML=`<input id="tk_zs" placeholder="Name, Parzelle, E-Mail …" style="margin-top:8px"><div id="tk_zl" style="max-height:220px;overflow:auto"></div><div class="knoepfe" style="margin-top:4px"><button class="k" onclick="tkZuordnungSetzen('')">Zuordnung lösen</button></div>`;
 const laden=async()=>{const d=await api("/api/ticket-mitglieder?q="+encodeURIComponent($("tk_zs").value));$("tk_zl").innerHTML=d.mitglieder.map(m=>`<button class="tk-frueh" onclick="tkZuordnungSetzen('${esc(m.id)}')">${esc(m.name)} <small>${esc(m.sparte)} ${esc(m.parzelle)}</small></button>`).join("")||'<p class="hint">Niemand gefunden.</p>'};
 $("tk_zs").oninput=()=>{clearTimeout(window.TKZT);window.TKZT=setTimeout(laden,250)};$("tk_zs").focus();laden()}
async function tkZuordnungSetzen(mid){await api("/api/ticket-zuordnen",{id:TKA,mitglied:mid},"log_tkd");await tkOeffnen(TKA,true);tkLaden()}
const AKTE_SYM={ticket:"💬",rechnung:"🧾",zahlung:"💶",vertrag:"📄",laufzeit:"⏱️",buchung:"✅",kuendigung:"⛔",laufzeit_ende:"⌛",laufzeit_verlaengert:"🔁",zugang_gesperrt:"🔒",zugang_freigegeben:"🔓",mitglied:"👤"};
async function akteZeigen(mid){const a=await api("/api/mitglied-akte?id="+encodeURIComponent(mid));const m=a.mitglied,o=document.createElement("div");
 o.style.cssText="position:fixed;inset:0;z-index:9998;background:rgba(10,20,15,.55);display:grid;place-items:center;padding:16px";
 o.innerHTML=`<div style="background:var(--card);color:var(--text);border-radius:14px;padding:18px;max-width:820px;width:100%;max-height:88vh;overflow:auto;box-shadow:0 18px 50px rgba(0,0,0,.35)">
 <div style="display:flex;gap:10px;align-items:center"><h3 style="margin:0;flex:1">Akte: ${esc(m.name)}</h3><button class="k" id="ak_zu">Schließen</button></div>
 <p class="hint">${esc(m.sparte)} · Parzelle ${esc(m.parzelle)}${m.tarif?" · Tarif "+esc(m.tarif):""}${m.email?" · "+esc(m.email):""}${m.telefon?" · "+esc(m.telefon):""} · ${esc(a.log[0])}</p>
 ${a.zeitleiste.map(e=>`<div class="akte-ev ${e.art=="ticket"?"ticket":""}" ${e.art=="ticket"?`data-id="${esc(e.id)}"`:""}><span class="z">${esc(e.zeit||"")}</span><span>${AKTE_SYM[e.art]||"•"}</span><span><b>${esc(e.titel)}</b>${e.text?"<br><small>"+esc(e.text)+"</small>":""}</span></div>`).join("")||'<p class="hint">Noch keine Einträge.</p>'}</div>`;
 document.body.appendChild(o);const zu=()=>o.remove();$("ak_zu").onclick=zu;o.onclick=e=>{if(e.target===o)zu()};
 o.querySelectorAll(".akte-ev.ticket").forEach(x=>x.onclick=()=>{zu();zeige("tickets");setTimeout(()=>tkOeffnen(x.dataset.id),300)})}
async function tkFelderSpeichern(){const r=await api("/api/ticket-speichern",{ticket:{id:TKA,status:$("tkd_status").value,zustaendig:$("tkd_zu").value,prioritaet:$("tkd_prio").value,kategorie:$("tkd_kat").value}},"log_tkd");tkLaden()}
async function tkAntworten(){const an=$("tk_an_kontakt").checked;if(an&&!confirm("Antwort per E-Mail an den Kontakt senden?"))return;
 await api("/api/ticket-kommentar",{id:TKA,html:reWert("tk_re"),an_kontakt:an,vorlage:$("tk_vorlage").value,wartet:$("tk_wartet").checked},"log_tkd");reAufbauen("tk_re","<p><br></p>",null);tkLaden()}
function tkVorlageEinsetzen(){const v=((EL&&EL.vorlagen)||[]).find(x=>x.id==$("tk_vorlage").value);if(v)reAufbauen("tk_re",v.html,null)}
async function tkNeu(){const t={betreff:$("tkn_betreff").value,text:$("tkn_text").value,kategorie:$("tkn_kat").value,prioritaet:$("tkn_prio").value,zustaendig:$("tkn_zu").value,sparte:$("tkn_sp").value,parzelle:$("tkn_p").value,name:$("tkn_name").value,email:$("tkn_email").value,telefon:$("tkn_tel").value};
 const r=await api("/api/ticket-speichern",{ticket:t},"log_tkn");["tkn_betreff","tkn_text","tkn_p","tkn_name","tkn_email","tkn_tel"].forEach(i=>$(i).value="");$("tkn_box").open=false;TKA=r.ticket.id;tkLaden()}
async function tkLoeschen(){if(!confirm("Ticket endgültig löschen?"))return;await api("/api/ticket-loeschen",{id:TKA},"log_tkd");TKA=null;$("tk_detail").hidden=true;tkLaden()}

// ---- Start: Auf einen Blick
async function ueLaden(){let d;try{const r=await fetch("/api/app-uebersicht",{headers:{"X-Token":T}});d=await r.json();if(!r.ok)return}catch(e){return}const k=[];
 if(d.tickets)k.push(kachel("offene Anfragen",d.tickets.offen+(d.tickets.meine?` <small>(${d.tickets.meine} für Sie)</small>`:""),d.tickets.dringend?"warn":""));
 if(d.stoerungen)k.push(kachel("Geräte offline",d.stoerungen.offline.length?esc(d.stoerungen.offline.join(", ")):"0",d.stoerungen.offline.length?"schlecht":"gut"));
 if(d.rechnungen)k.push(kachel("offene Rechnungen",(d.rechnungen.offen_betrag||0).toLocaleString("de-DE",{style:"currency",currency:"EUR"})+(d.rechnungen.ueberfaellig?` <small>(${d.rechnungen.ueberfaellig} überfällig)</small>`:""),d.rechnungen.ueberfaellig?"warn":""));
 if(d.buchungen!=null)k.push(kachel("gebuchte Parzellen",d.buchungen,""));if(d.mitglieder!=null)k.push(kachel("Mitglieder",d.mitglieder,""));
 $("ue_k").innerHTML=k.join("");$("ue_karte").hidden=!k.length}
const geldF=v=>(+v||0).toLocaleString("de-DE",{style:"currency",currency:"EUR"});

// ---- Rechnungen
let RE=null,ZA=null;const reDarf=()=>ICH.admin||ICH.bereiche.rechnungen=="schreiben";
async function reLaden(){const p=new URLSearchParams({jahr:$("re_jahr").value||"",status:$("re_fs").value});const d=await api("/api/rechnungen?"+p.toString(),undefined,"log_re");RE=d;
 document.querySelectorAll(".re-schreib").forEach(e=>e.hidden=!reDarf());const j=$("re_jahr").value;$("re_jahr").innerHTML='<option value="">alle Jahre</option>'+d.jahre.map(x=>`<option${x==j?" selected":""}>${esc(x)}</option>`).join("");
 if(!$("rl_jahr").value)$("rl_jahr").value=new Date().getFullYear();$("re_k").innerHTML=kachel("Summe",geldF(d.summe.brutto),"")+kachel("bezahlt",geldF(d.summe.bezahlt),"gut")+kachel("offen",geldF(d.summe.offen),d.summe.offen?"warn":"");
 $("re_st").textContent=d.zeilen.length+" Rechnungen";reZeigen();if(ICH.admin)riZeigen(d.einstellungen)}
function reZeigen(){const d=RE;if(!d)return;const q=$("re_such").value.trim().toLowerCase(),heute=new Date().toISOString().slice(0,10);
 const L=d.zeilen.filter(z=>!q||[z.nr,z.name,z.sparte,String(z.parzelle)].join(" ").toLowerCase().includes(q));
 $("re_tab").innerHTML=L.length?"<table><tr><th></th><th>Nr.</th><th>Name</th><th>Parzelle</th><th>Tarif</th><th>Betrag</th><th>bezahlt</th><th>Status</th><th>fällig</th><th>versendet</th><th></th></tr>"+L.map(z=>`<tr${z.status=="storniert"?' style="opacity:.5"':""}><td><input type="checkbox" class="re_w" value="${esc(z.id)}" data-v="${z.versendet?1:0}" style="width:auto"></td><td class="mono"><b>${esc(z.nr)}</b></td><td>${esc(z.name)}</td><td>${esc(z.sparte)} ${esc(z.parzelle)}</td><td>${esc(z.tarif)}</td><td>${geldF(z.brutto)}</td><td>${geldF(z.bezahlt)}</td>
  <td>${z.status=="bezahlt"?'<span class="status ok">bezahlt</span>':z.status=="offen"&&z.faellig<heute?'<span class="status" style="background:#fde8e6;color:#b42318">überfällig</span>':esc(d.status[z.status])}</td><td>${esc(z.faellig)}</td><td>${esc(z.versendet||"–")}</td>
  <td style="white-space:nowrap"><button class="k" data-id="${esc(z.id)}" onclick="rePdf(this.dataset.id)">PDF</button>${reDarf()&&["offen","teilweise"].includes(z.status)?` <button class="k" data-id="${esc(z.id)}" data-r="${z.offen_betrag}" onclick="reZahlung(this.dataset.id,this.dataset.r)">Zahlung …</button> <button class="k" data-id="${esc(z.id)}" onclick="reStorno(this.dataset.id)">Storno</button>`:""}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Keine Rechnungen.</p>'}
function reAlle(art){document.querySelectorAll(".re_w").forEach(e=>e.checked=art=="nicht"?e.dataset.v=="0":true)}
async function rePdf(id){const z=RE.zeilen.find(x=>x.id==id);try{await siBlob("/api/rechnung-pdf?id="+encodeURIComponent(id),null,"Rechnung_"+(z?z.nr:id)+".pdf")}catch(e){$("log_re").innerHTML='<span class="fehler">✖ '+esc(e.message)+"</span>"}}
async function reSenden(){const ids=[...document.querySelectorAll(".re_w:checked")].map(e=>e.value);if(!ids.length)return $("log_re").textContent="Nichts ausgewählt.";if(!confirm(ids.length+" Rechnung(en) per E-Mail mit PDF an die Mitglieder senden?"))return;RE=await api("/api/rechnung-senden",{ids},"log_re");reZeigen()}
async function reZahlung(id,rest){const b=prompt("Zahlungseingang in € (z. B. bar oder Überweisung):",String(rest).replace(".",","));if(!b)return;RE=await api("/api/rechnung-status",{id,zahlung:b},"log_re");reLaden()}
async function reStorno(id){if(!confirm("Rechnung stornieren? (Sie bleibt erhalten, gilt aber nicht mehr.)"))return;await api("/api/rechnung-status",{id,stornieren:true},"log_re");reLaden()}
async function reLauf(aus){const j=+$("rl_jahr").value;if(aus&&!confirm("Rechnungen für "+j+" jetzt erstellen?"))return;const d=await api("/api/rechnungslauf",{jahr:j,ausfuehren:aus},"log_rl");
 $("rl_tab").innerHTML=d.vorschau&&d.vorschau.length?"<table><tr><th>Sparte</th><th>Parzelle</th><th>Name</th><th>E-Mail</th><th>Tarif</th><th>Betrag</th></tr>"+d.vorschau.map(x=>`<tr><td>${esc(x.sparte)}</td><td>${x.parzelle}</td><td>${esc(x.name)}</td><td>${esc(x.email||"– (kein Versand möglich)")}</td><td>${esc(x.tarif)}</td><td>${geldF(x.preis)}</td></tr>`).join("")+"</table>":"";if(aus){$("re_jahr").value=String(j);reLaden()}}
async function zaLaden(){const f=$("za_datei").files[0];if(!f)return $("log_za").textContent="Bitte den CSV-Kontoauszug wählen.";const d=await api("/api/zahlungen-import",f,"log_za");ZA=d;
 const opt=w=>'<option value="">nicht zuordnen</option>'+d.offen.map(o=>`<option value="${esc(o.id)}"${o.id==w?" selected":""}>${esc(o.nr)} · ${esc(o.name||"")} · ${geldF(o.rest)}</option>`).join("");
 $("za_tab").innerHTML="<table><tr><th>Datum</th><th>Betrag</th><th>Auftraggeber</th><th>Verwendungszweck</th><th>Rechnung</th><th>erkannt über</th></tr>"+d.zeilen.map(z=>`<tr${z.schon?' style="opacity:.5"':z.rechnung?' class="geaendert"':""}><td>${esc(z.datum)}</td><td>${geldF(z.betrag)}</td><td>${esc(z.name)}</td><td>${esc(z.zweck)}</td><td>${z.schon?"schon übernommen":`<select class="za_w" data-h="${esc(z.hash)}" style="min-width:240px">${opt(z.rechnung)}</select>`}</td><td>${esc(z.grund||"")}</td></tr>`).join("")+"</table>";$("za_ok").disabled=false}
async function zaUebernehmen(){const zu={};document.querySelectorAll(".za_w").forEach(e=>{if(e.value)zu[e.dataset.h]=e.value});if(!Object.keys(zu).length)return $("log_za").textContent="Keine Zuordnung ausgewählt.";
 if(!confirm(Object.keys(zu).length+" Zahlung(en) buchen?"))return;await api("/api/zahlungen-uebernehmen",{import:ZA.import,zuordnung:zu},"log_za");$("za_ok").disabled=true;$("za_tab").innerHTML="";$("za_datei").value="";reLaden()}
let RIF=false;function riZeigen(e){if(RIF)return;RIF=true;const f={firma:"ri_firma",email:"ri_email",telefon:"ri_tel",praefix:"ri_praefix",adresse:"ri_adresse",betreff:"ri_betreff",zahlungsziel:"ri_ziel",iban:"ri_iban",bic:"ri_bic",bank:"ri_bank",steuernr:"ri_stnr",ust_id:"ri_ustid",ust_satz:"ri_ust",text_oben:"ri_oben",text_unten:"ri_unten",email_betreff:"ri_mb"};
 for(const[k,i]of Object.entries(f))$(i).value=e[k]??"";$("ri_ku").checked=!!e.kleinunternehmer;reAufbauen("ri_re",e.email_text,null)}
async function riSpeichern(){const b={firma:$("ri_firma").value,email:$("ri_email").value,telefon:$("ri_tel").value,praefix:$("ri_praefix").value,adresse:$("ri_adresse").value,betreff:$("ri_betreff").value,zahlungsziel:$("ri_ziel").value,iban:$("ri_iban").value,bic:$("ri_bic").value,bank:$("ri_bank").value,steuernr:$("ri_stnr").value,ust_id:$("ri_ustid").value,ust_satz:$("ri_ust").value,text_oben:$("ri_oben").value,text_unten:$("ri_unten").value,email_betreff:$("ri_mb").value,email_text:reWert("ri_re"),kleinunternehmer:$("ri_ku").checked};
 await api("/api/rechnung-einstellungen",b,"log_ri")}

// ---- Verträge
let VT=null;
async function vtLaden(){const d=await api("/api/vertraege",undefined,"log_vt");VT=d;const e=d.einstellungen;$("vt_lz").value=e.laufzeit;$("vt_vl").value=e.verlaengerung;$("vt_fr").value=e.frist;$("vt_er").value=e.erinnerung_tage;$("vt_auto").checked=e.auto_entfernen;vtZeigen()}
function vtZeigen(){const d=VT;if(!d)return;const f=$("vt_f").value,q=$("vt_such").value.trim().toLowerCase(),w=mgDarf();
 const L=d.zeilen.filter(z=>(f?z.status==f:z.status!="beendet")&&(!q||[z.name,z.sparte,String(z.parzelle)].join(" ").toLowerCase().includes(q)));
 $("vt_st").textContent=d.zeilen.filter(z=>z.status=="Frist läuft ab").length+" mit bald ablaufender Frist";
 $("vt_tab").innerHTML=L.length?"<table><tr><th>Parzelle</th><th>Mitglied</th><th>Tarif</th><th>Beginn</th><th>Laufzeit / Verl. / Frist (Monate)</th><th>Periode endet</th><th>kündbar bis</th><th>Status</th><th></th></tr>"+L.map(z=>`<tr><td><b>${esc(z.sparte)} ${z.parzelle}</b></td><td>${esc(z.name||"–")}</td><td>${esc(z.tarif||"–")}</td>
  <td>${w&&!z.gekuendigt?`<input type="date" class="vt_in" data-id="${esc(z.id)}" data-f="beginn" value="${esc(z.beginn)}" style="max-width:150px">`:esc(z.vertrag_beginn)}</td>
  <td style="white-space:nowrap">${w&&!z.gekuendigt?["laufzeit","verlaengerung","frist"].map(k=>`<input type="number" class="vt_in" data-id="${esc(z.id)}" data-f="${k}" value="${z[k]}" style="width:62px">`).join(" "):`${z.laufzeit} / ${z.verlaengerung} / ${z.frist}`}</td>
  <td>${esc(z.vertrag_ende)}</td><td>${esc(z.kuendbar_bis||"–")}</td><td>${z.status=="Frist läuft ab"?'<span class="status" style="background:#fff6dd;color:#7a5a00">Frist läuft ab</span>':z.status=="gekündigt"?'<span class="status">gekündigt am '+esc(z.gekuendigt)+"</span>":esc(z.status)}</td>
  <td style="white-space:nowrap">${w?(z.status=="gekündigt"?`<button class="k" data-id="${esc(z.id)}" onclick="vtKuendigen(this.dataset.id,true)">Kündigung zurücknehmen</button>`:z.status!="beendet"?`<button class="k" data-id="${esc(z.id)}" onclick="vtKuendigen(this.dataset.id,false)">Kündigen …</button>`:""):""}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Keine Verträge für diesen Filter.</p>';
 document.querySelectorAll(".vt_in").forEach(e=>e.onchange=async()=>{VT=await api("/api/vertrag-speichern",{id:e.dataset.id,[e.dataset.f]:e.value},"log_vt");vtZeigen()})}
async function vtKuendigen(id,zurueck){if(zurueck){VT=await api("/api/vertrag-kuendigen",{id,zuruecknehmen:true},"log_vt");return vtZeigen()}
 const z=prompt("Kündigen zum nächstmöglichen Termin – oder ein Datum eingeben (JJJJ-MM-TT):","");if(z===null)return;VT=await api("/api/vertrag-kuendigen",{id,zum:z.trim()},"log_vt");vtZeigen()}
async function vtEinst(){VT=await api("/api/vertrag-einstellungen",{laufzeit:$("vt_lz").value,verlaengerung:$("vt_vl").value,frist:$("vt_fr").value,erinnerung_tage:$("vt_er").value,auto_entfernen:$("vt_auto").checked},"log_vt");vtZeigen()}

// ---- Rundschreiben
let RSINIT=false;
async function rsLaden(){if(!mgDarf())return;if(!RSINIT){RSINIT=true;const sp=Object.entries((MG&&MG.sparten)||{}).sort((a,b)=>a[0].localeCompare(b[0]));
  $("rs_sp").innerHTML=sp.map(([k,n])=>`<label style="display:flex;gap:6px;align-items:center;margin:2px 0"><input type="checkbox" class="rs_s" value="${esc(k)}" style="width:auto"> ${esc(k)} – ${esc(n)}</label>`).join("")||'<span class="hint">erst Mitglieder laden</span>';
  const t=await api("/api/tarife").catch(()=>({tarife:[]}));$("rs_tf").innerHTML=t.tarife.map(x=>`<label style="display:flex;gap:6px;align-items:center;margin:2px 0"><input type="checkbox" class="rs_t" value="${esc(x.name)}" style="width:auto"> ${esc(x.name)}</label>`).join("");
  const v=(EL&&EL.vorlagen)||(await api("/api/email-layout").catch(()=>({vorlagen:[]}))).vorlagen||[];$("rs_vorlage").innerHTML='<option value="">eigener Text</option>'+v.map(x=>`<option value="${esc(x.id)}">${esc(x.name)}</option>`).join("");RSV=v;
  reAufbauen("rs_re","<p>Hallo {vorname},</p><p><br></p><p>Viele Grüße<br>Ihr SparteNet-Team</p>",null)}
 const d=await api("/api/rundschreiben");$("rs_verlauf").innerHTML=d.liste.length?"<table><tr><th>Zeit</th><th>Betreff</th><th>Empfänger</th><th>gesendet</th><th>Fehler</th><th>Status</th></tr>"+d.liste.map(r=>`<tr><td>${esc(r.zeit)}</td><td>${esc(r.betreff)}</td><td>${r.gesamt}</td><td>${r.gesendet}</td><td>${r.fehler||0}</td><td>${esc(r.status)}</td></tr>`).join("")+"</table>":""}
let RSV=[];function rsVorlage(){const v=RSV.find(x=>x.id==$("rs_vorlage").value);if(v){$("rs_betreff").value=v.betreff;reAufbauen("rs_re",v.html,null)}}
function rsFilter(){return{sparten:[...document.querySelectorAll(".rs_s:checked")].map(e=>e.value),tarife:[...document.querySelectorAll(".rs_t:checked")].map(e=>e.value),nur_gebucht:$("rs_nur").checked}}
async function rsPruefen(){const d=await api("/api/rundschreiben-empfaenger",{filter:rsFilter()},"log_rs");$("log_rs").textContent=d.log.join("\n")+(d.beispiele.length?"\nz. B.: "+d.beispiele.slice(0,8).map(x=>x.name+" ("+x.sparte+" "+x.parzelle+")").join(", "):"")}
async function rsSenden(test){const b={filter:rsFilter(),betreff:$("rs_betreff").value,html:reWert("rs_re")};if(test){b.test_an=$("rs_test").value.trim();if(!b.test_an)return $("log_rs").textContent="Bitte eine Test-Adresse eingeben."}
 else{const e=await api("/api/rundschreiben-empfaenger",{filter:b.filter},"log_rs");if(!confirm("Rundschreiben „"+b.betreff+"“ jetzt an "+e.anzahl+" Empfänger senden?"))return}
 await api("/api/rundschreiben-senden",b,"log_rs");if(!test)setTimeout(()=>rsLaden().catch(()=>{}),3000)}

// ---- Datenschutz
async function mgAuskunft(){try{await siBlob("/api/mitglied-auskunft?id="+encodeURIComponent($("mg_id").value),null,"Auskunft.json")}catch(e){$("log_mgf").innerHTML='<span class="fehler">✖ '+esc(e.message)+"</span>"}}
async function mgDsgvo(){if(!confirm("Datenschutz-Löschung: Mitglied endgültig löschen und seine Tickets anonymisieren? Rechnungen bleiben wegen der Aufbewahrungspflicht gesperrt erhalten."))return;
 const d=await api("/api/mitglied-dsgvo-loeschen",{id:$("mg_id").value},"log_mgf");MG=d;mgZeigen();$("mg_form").hidden=true;$("log_mg").textContent=d.log.join("\n")}

// ---- Kontakt-Seite
async function poLaden(){const d=await api("/api/portal-einstellungen",undefined,"log_po");const e=d.einstellungen;$("po_aktiv").checked=e.aktiv;$("po_titel").value=e.titel;$("po_text").value=e.text;$("po_ticket").checked=e.ticket;$("po_status").checked=e.status;$("po_zugang").checked=e.zugang;$("po_best").checked=e.bestaetigung;$("po_link").href=location.origin+"/portal";$("po_link").textContent=location.origin+"/portal"}
async function mbLaden(){const d=await api("/api/mitgliederbereich",undefined,"log_mb");mbZeigen(d);apuLaden()}
async function mbTrennenPruefen(){try{await api("/api/mitglied-trennen-pruefen",{},"log_mbtr")}catch(e){}}
async function apuLaden(){try{apuZeigen(await api("/api/app-update"))}catch(e){}}
function apuZeigen(d){$("apu_liste").innerHTML='<table><tr><th>App</th><th>Version</th><th>Größe</th><th>hochgeladen</th><th></th></tr>'+Object.entries(d.apps||{}).map(([k,a])=>`<tr><td>${esc(a.titel)}</td><td>${a.version_code?esc(a.version_name)+" ("+esc(a.version_code)+")":"–"}</td><td>${a.groesse?(a.groesse/1048576).toFixed(1)+" MB":"–"}</td><td>${esc(a.hochgeladen||"–")}</td><td>${a.version_code?`<button class="k r" onclick="apuEntfernen('${k}')">Entfernen</button>`:""}</td></tr>`).join("")+"</table>"}
async function apuHochladen(){const f=$("apu_datei").files[0];if(!f){$("log_apu").textContent="Bitte eine APK-Datei wählen.";return}const p=new URLSearchParams({art:$("apu_art").value,version_code:$("apu_vc").value,version_name:$("apu_vn").value,hinweis:$("apu_hinweis").value});
 try{apuZeigen(await api("/api/app-update-hochladen?"+p.toString(),f,"log_apu"));$("apu_datei").value=""}catch(e){}}
async function apuEntfernen(art){if(!confirm("Update-Datei entfernen? Die App meldet dann kein Update mehr."))return;try{apuZeigen(await api("/api/app-update",{art,entfernen:true},"log_apu"))}catch(e){}}
const MB_SCHALTER=["aktiv","tarifwechsel","downgrade","neubuchung","verlaengern","geraete","zeige_rechnungen","zeige_anfragen","neue_anfrage","zugangskarte","profil","personen","geraete_trennen","geraete_sperren","stoerung_zeigen"];
function mbZeigen(d){const e=d.einstellungen;for(const k of MB_SCHALTER)$("mb_"+k).checked=e[k];$("mb_stoerung_farbe").value=e.stoerung_farbe;$("mb_stoerung_meldung").value=e.stoerung_meldung;$("mb_stoerung_text").value=e.stoerung_text;$("mb_versand").innerHTML=d.versand?"✉ Einmalcodes werden über den E-Mail-Versand des Managers verschickt (Automationen → E-Mail-Versand).":'<span style="color:#b42318">⚠ E-Mail-Versand ist nicht eingerichtet – ohne ihn bekommen Mitglieder keinen Einmalcode und können sich weder auf /mein noch in der App anmelden. Einrichten unter Automationen → E-Mail-Versand.</span>';$("mb_apps").innerHTML=`📱 Mitglieder-App (Android): ${d.apps} Gerät(e) angemeldet – Anmeldung in der App mit Server-Adresse, E-Mail und Code.`+(d.apps?' <button class="k" onclick="mbAppsAbmelden()">Alle abmelden</button>':"");
 $("mb_tarife").innerHTML=d.alle_tarife.map(t=>`<label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" class="mb_tf" value="${esc(t.name)}" style="width:auto"${e.tarife.includes(t.name)?" checked":""}> ${esc(t.name)} <small>(${Number(t.preis||0).toFixed(2)} €)</small></label>`).join("");$("mb_modus").value=e.modus;$("mb_minuten").value=e.minuten;$("mb_adresse").value=e.adresse||"";$("mb_vorlage").value=e.checkout_vorlage||"";$("mb_api").value=e.link_api||"";
 $("mb_geheim_info").textContent=e.geheim_gesetzt?"Webhook-Geheimnis ist eingerichtet (wird nicht wieder angezeigt).":"Noch kein Webhook-Geheimnis – bitte erzeugen und beim Bezahldienst/Dienst eintragen.";if(d.geheim){$("mb_geheim").hidden=false;$("mb_geheim").textContent=d.geheim}
 $("mb_link").href=location.origin+"/mein";$("mb_link").textContent=location.origin+"/mein";mbModus();
 $("mb_auftraege").innerHTML=d.auftraege.length?'<table><tr><th>Referenz</th><th>Erstellt</th><th>Mitglied</th><th>Parzelle</th><th>Art</th><th>Tarif</th><th>Betrag</th><th>Status</th></tr>'+d.auftraege.map(a=>`<tr><td>${esc(a.referenz)}</td><td>${esc(a.erstellt)}</td><td>${esc(a.name)}</td><td>${esc(a.sparte)} ${esc(a.parzelle)}</td><td>${esc({neu:"Neu",wechsel:"Wechsel",verlaengern:"Verlängerung"}[a.art]||a.art)}</td><td>${esc(a.tarif)}</td><td>${Number(a.betrag||0).toFixed(2)} €</td><td>${esc(a.status)}${a.bezahlt_am?" "+esc(a.bezahlt_am):""}</td></tr>`).join("")+"</table>":'<p class="hint">Noch keine Zahlungsaufträge.</p>'}
async function mbAppsAbmelden(){if(!confirm("Alle Mitglieder-Apps abmelden? Jedes Mitglied muss sich in der App neu mit E-Mail-Code anmelden."))return;mbZeigen(await api("/api/mitgliederbereich",{apps_abmelden:true},"log_mb"))}
function mbModus(){$("mb_bezahl").hidden=$("mb_modus").value!="bezahldienst"}
async function mbSpeichern(neu){const b={modus:$("mb_modus").value,minuten:+$("mb_minuten").value||30,adresse:$("mb_adresse").value,checkout_vorlage:$("mb_vorlage").value,link_api:$("mb_api").value};for(const k of MB_SCHALTER)b[k]=$("mb_"+k).checked;b.stoerung_farbe=$("mb_stoerung_farbe").value;b.stoerung_meldung=$("mb_stoerung_meldung").value;b.stoerung_text=$("mb_stoerung_text").value;b.tarife=[...document.querySelectorAll(".mb_tf:checked")].map(x=>x.value);if(neu===true){if(!confirm("Neues Geheimnis erzeugen? Das alte gilt dann nicht mehr."))return;b.geheim_neu=true}
 const d=await api("/api/mitgliederbereich",b,"log_mb");mbZeigen(d)}
async function poSpeichern(){await api("/api/portal-einstellungen",{aktiv:$("po_aktiv").checked,titel:$("po_titel").value,text:$("po_text").value,ticket:$("po_ticket").checked,status:$("po_status").checked,zugang:$("po_zugang").checked,bestaetigung:$("po_best").checked},"log_po")}

// ---- Störungsüberwachung
async function owLaden(){const d=await api("/api/ueberwachung",undefined,"log_ow");owZeigen(d)}
function owZeigen(d){const e=d.einstellungen;$("ow_aktiv").checked=e.aktiv;$("ow_int").value=e.intervall;$("ow_verz").value=e.verzoegerung;$("ow_ticket").checked=e.ticket;$("ow_auto").checked=e.auto_erledigen;
 $("ow_zu").innerHTML='<option value="">niemand</option>'+d.konten.map(k=>`<option${k==e.zustaendig?" selected":""}>${esc(k)}</option>`).join("");
 const aus=d.geraete.filter(g=>g.offline_seit).length;$("ow_st").textContent=(e.aktiv?"aktiv":"aus")+(d.letzte?" · zuletzt "+d.letzte:"")+(aus?" · "+aus+" offline":"");$("ow_st").className="status"+(e.aktiv&&!aus?" ok":"");
 $("ow_tab").innerHTML=(d.geraete.length?"<table><tr><th>Gerät</th><th>Modell</th><th>IP</th><th>Status</th><th>offline seit</th><th title=\"Bei einem Ausfall sehen Mitglieder dieser Sparte die Störung im Mitgliederbereich\">betrifft Sparte</th></tr>"+d.geraete.map(g=>`<tr${g.offline_seit?' class="falsch"':""}><td><b>${esc(g.name)}</b></td><td>${esc(g.modell)}</td><td class="mono">${esc(g.ip)}</td><td>${esc(g.status)}</td><td>${esc(g.offline_seit||"")}${g.gemeldet?" · gemeldet":""}</td>
  <td><select data-g="${esc(g.key)}" onchange="owSparte(this.dataset.g,this.value)" style="min-width:130px"${ICH.admin?"":" disabled"}><option value="">alle Sparten</option>${Object.entries(d.sparten||{}).map(([k,n])=>`<option value="${esc(k)}"${g.sparte==k?" selected":""}>${esc(n)}</option>`).join("")}</select></td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Noch nicht geprüft.</p>')
  +(d.verlauf.length?"<table><tr><th>Zeit</th><th>Gerät</th><th>Ereignis</th></tr>"+d.verlauf.map(v=>`<tr><td>${esc(v.zeit)}</td><td>${esc(v.geraet)}</td><td>${v.art=="offline"?"offline seit "+esc(v.seit):"wieder online nach "+v.dauer+" Min."}</td></tr>`).join("")+"</table>":"");if(d.fehler)$("log_ow").textContent="⚠ "+d.fehler}
async function owSparte(geraet,sparte){owZeigen(await api("/api/ueberwachung-speichern",{geraet_sparte:{geraet,sparte}},"log_ow"))}
async function owSpeichern(jetzt){const d=await api("/api/ueberwachung-speichern",{aktiv:$("ow_aktiv").checked,intervall:$("ow_int").value,verzoegerung:$("ow_verz").value,ticket:$("ow_ticket").checked,auto_erledigen:$("ow_auto").checked,zustaendig:$("ow_zu").value,jetzt},"log_ow");owZeigen(d);$("log_ow").textContent=d.log.join("\n")}

// ---- Wochenbericht
async function wbLaden(){const d=await api("/api/wochenbericht",undefined,"log_wb");wbZeigen(d)}
function wbZeigen(d){const e=d.einstellungen;$("wb_aktiv").checked=e.aktiv;$("wb_tag").innerHTML=d.wochentage.map((t,i)=>`<option value="${i}"${i==e.tag?" selected":""}>${t}</option>`).join("");$("wb_uhr").value=e.uhrzeit;$("wb_an").value=e.an;
 $("wb_vor").srcdoc='<!doctype html><meta charset="utf-8"><body style="font-family:Arial,sans-serif;padding:16px;color:#1d2f3e">'+d.vorschau}
async function wbSpeichern(jetzt){const b={aktiv:$("wb_aktiv").checked,tag:$("wb_tag").value,uhrzeit:$("wb_uhr").value,an:$("wb_an").value};if(jetzt)Object.assign(b,{jetzt:true,an_test:$("wb_an").value});const d=await api("/api/wochenbericht",b,"log_wb");wbZeigen(d);$("log_wb").textContent=d.log.join("\n")}

// ---- Apps und Geräte
async function apLaden(){aztLaden();const d=await api("/api/app-geraete"+(ICH.admin?"?alle=1":""),undefined,"log_app");
 $("bn_app_tab").innerHTML=d.geraete.length?"<table><tr><th>Gerät</th><th>Konto</th><th>angemeldet</th><th>zuletzt</th><th>gültig bis</th><th></th></tr>"+d.geraete.map(g=>`<tr><td><b>${esc(g.name)}</b></td><td>${esc(g.benutzer)}</td><td>${esc(g.angelegt)}</td><td>${esc(g.zuletzt||"–")}</td><td>${esc(g.ablauf)}</td><td><button class="k" data-id="${esc(g.id)}" onclick="apWeg(this.dataset.id)">Entfernen</button></td></tr>`).join("")+"</table>":'<p class="hint" style="padding:10px">Noch keine App angemeldet.</p>'}
async function apWeg(id){if(!confirm("Gerät entfernen? Die App muss sich danach neu anmelden."))return;await api("/api/app-geraet-entfernen",{id},"log_app");apLaden()}

let UL=null,ULNEU="";
function ulOrdnerWahl(){const neu=$("ul_ordner").value=="__neu";$("ul_ordner_neu").hidden=!neu;if(neu)$("ul_ordner_neu").focus()}
function ulZielordner(){if($("ul_ordner").value!="__neu")return $("ul_ordner").value||"Allgemein";const n=$("ul_ordner_neu").value.trim()||"Allgemein";ULNEU=n;return n}
function ulOrdnerListe(){const d=UL;if(!d||!$("ul_ordner_tab"))return;const darf=ICH.admin||ICH.bereiche.unterlagen=="schreiben";
 $("ul_ordner_tab").innerHTML="<table><tr><th>Ordner</th><th>Dateien</th><th></th></tr>"+d.ordner.map(o=>`<tr><td><a href="#" data-o="${esc(o)}" onclick="$('ul_f_ordner').value=this.dataset.o;ulZeigen();return false">${esc(o)}</a></td><td>${d.anzahl[o]||0}</td><td>${darf&&!d.standard.includes(o)&&!(d.anzahl[o])?`<button class="k" data-o="${esc(o)}" onclick="ulOrdnerWeg(this.dataset.o)">Entfernen</button>`:""}</td></tr>`).join("")+"</table>"}
async function ulOrdnerNeu(){const n=$("ul_neuer_ordner").value.trim();if(!n)return;UL=await api("/api/unterlage-ordner",{neu:n},"log_ulo");$("ul_neuer_ordner").value="";ULNEU=n;await ulLaden();$("log_ulo").textContent="✔ Ordner „"+n+"“ angelegt – beim Hochladen auswählbar."}
async function ulOrdnerWeg(n){if(!confirm("Leeren Ordner „"+n+"“ entfernen?"))return;UL=await api("/api/unterlage-ordner",{loeschen:n},"log_ulo");ulLaden()}
async function ulLaden(){const d=await api("/api/unterlagen",undefined,"log_ul");UL=d;
 const sp=(d.sparten_erlaubt||[...new Set((GP?GP.zeilen.map(z=>z.kz):[]).concat(PLAN?PLAN.sparten.map(s=>s.kz):[]))].sort());
 $("ul_sparte").innerHTML=(d.sparten_erlaubt?"":'<option value="">Allgemein (alle Sparten)</option>')+sp.map(k=>`<option value="${esc(k)}">${esc(k)}</option>`).join("");
 const uo=$("ul_ordner").value;$("ul_ordner").innerHTML=d.ordner.map(o=>`<option value="${esc(o)}">${esc(o)}${d.anzahl&&d.anzahl[o]?" ("+d.anzahl[o]+")":""}</option>`).join("")+'<option value="__neu">+ Neuer Ordner …</option>';
 $("ul_ordner").value=ULNEU&&d.ordner.includes(ULNEU)?ULNEU:(d.ordner.includes(uo)&&uo!="__neu"?uo:"Allgemein");$("ul_ordner_neu").value="";ULNEU="";ulOrdnerWahl();ulOrdnerListe();
 const fo=$("ul_f_ordner").value,fs=$("ul_f_sparte").value;
 $("ul_f_ordner").innerHTML='<option value="">alle Ordner</option>'+d.ordner.map(o=>`<option value="${esc(o)}">${esc(o)}</option>`).join("");$("ul_f_ordner").value=fo;
 const ds=[...new Set(d.dateien.map(x=>x.sparte||""))].sort();$("ul_f_sparte").innerHTML='<option value="*">alle</option>'+ds.map(k=>`<option value="${esc(k)}">${k?esc(k):"Allgemein"}</option>`).join("");if([...$("ul_f_sparte").options].some(o=>o.value==fs))$("ul_f_sparte").value=fs;
 $("ul_st").textContent=d.belegt_mb+" / "+d.gesamt_mb+" MB";ulZeigen()}
const groesse=b=>b>=1e6?(b/1e6).toLocaleString("de-DE",{maximumFractionDigits:1})+" MB":Math.max(1,Math.round(b/1e3))+" KB";
function ulZeigen(){const d=UL;if(!d)return;const q=$("ul_such").value.trim().toLowerCase(),fo=$("ul_f_ordner").value,fs=$("ul_f_sparte").value;
 const L=d.dateien.filter(x=>(!q||(x.name+" "+(x.beschreibung||"")).toLowerCase().includes(q))&&(!fo||x.ordner==fo)&&(fs=="*"||!fs&&fs!==""||(x.sparte||"")==fs));
 const darf=ICH.admin||ICH.bereiche.unterlagen=="schreiben";
 $("ul_tab").innerHTML=L.length?"<table><tr><th>Name</th><th>Ordner</th><th>Sparte</th><th>Größe</th><th>hochgeladen</th><th>Beschreibung</th><th></th></tr>"+L.map(x=>`<tr><td><b>${esc(x.name)}</b></td>
  <td>${darf&&x.schreiben?`<select class="ul_in" data-id="${x.id}" data-f="ordner" style="min-width:140px">${d.ordner.map(o=>`<option value="${esc(o)}"${o==x.ordner?" selected":""}>${esc(o)}</option>`).join("")}</select>`:esc(x.ordner)}</td><td>${x.sparte?esc(x.sparte):"Allgemein"}</td><td>${groesse(x.groesse)}</td>
  <td>${esc(x.zeit)}<br><small>${esc(x.von)}</small></td><td>${darf&&x.schreiben?`<input class="ul_in" data-id="${x.id}" data-f="beschreibung" value="${esc(x.beschreibung||"")}" style="min-width:200px">`:esc(x.beschreibung||"")}</td>
  <td style="white-space:nowrap">${x.ansehen?`<button class="k" onclick="ulDatei('${x.id}',true)">Ansehen</button> `:""}<button class="k" onclick="ulDatei('${x.id}',false)">Herunterladen</button>${darf&&x.schreiben?` <button class="k" onclick="ulLoeschen('${x.id}')">Löschen</button>`:""}</td></tr>`).join("")+"</table>":'<p class="hint" style="padding:12px">Keine Unterlagen'+(q||fo?" für diesen Filter":"")+".</p>";
 document.querySelectorAll(".ul_in").forEach(e=>e.onchange=async()=>{UL=await api("/api/unterlage-aendern",{id:e.dataset.id,[e.dataset.f]:e.value},"log_ul");ulZeigen()})}
async function ulHoch(files){const max=UL?UL.max_datei_mb:15;for(const f of files){if(f.size>max*1e6){$("log_ulh").innerHTML='<span class="fehler">✖ '+esc(f.name)+": größer als "+max+" MB</span>";continue}
  const p=new URLSearchParams({name:f.name,ordner:ulZielordner(),sparte:$("ul_sparte").value||"",beschreibung:$("ul_beschr").value||""});
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
 $("bn_2fa_ein").hidden=an;$("bn_2fa_aus").hidden=!an;$("bn_2fa_vergessen").hidden=!an}
async function zfVergessen(){if(!confirm("Alle gemerkten Browser und Apps vergessen? Beim nächsten Anmelden wird der Code wieder abgefragt."))return;await api("/api/2fa-vergessen",{},"log_bni")}
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
  $("gp_pq").value=g.preis_quelle;$("gp_qm").value=String(a.Quote_Modus);$("gp_qf").value=String(+(a.Quote_fest*100).toFixed(2)).replace(".",",");$("gp_sz").value=String(a.Szenario);$("gp_gb").value=String(a.GW_Basis||1);
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
 const r=await api("/api/gwplan-annahmen",{annahmen:{Quote_Modus:$("gp_qm").value,Quote_fest:$("gp_qf").value.trim(),Szenario:$("gp_sz").value,GW_Basis:$("gp_gb").value},tarifmix:mix,preis_quelle:$("gp_pq").value},"log_gps");if(r&&r.gesamt){$("gp_an").dataset.fertig="";gpZeigen(r)}}
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

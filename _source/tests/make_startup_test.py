import re,sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(a[:60],s.count(a));s=s.replace(a,b)
D='(function(){try{return sessionStorage.getItem("rhbc-demo")||""}catch(e){return""}})()'
rep('function renderAgenda(){','function renderAgenda(){if('+D+'==="agenda"&&calMode==="agenda")throw new Error("Demo: the Agenda view bug");')
rep('function renderSpecials(){','function renderSpecials(){if(/^section/.test('+D+'))throw new Error("Demo: broken Special Events code");')
rep('var STAFF_VIEW=()=>{try{return canEditFlag===true}catch(x){return false}};','var STAFF_VIEW=()=>{if('+D+'==="section-staff")return true;try{return canEditFlag===true}catch(x){return false}};')
rep('const load=async()=>{','const load=async()=>{if('+D+'==="data"){LOG.push("Data download first try failed: Demo: blocked","Data download second try failed: Demo: blocked");return null}')
s=s.replace('<title>','<title>TEST · Self-Correcting Start-Up · ',1)
if 'name="robots"' not in s: s=s.replace('</title>','</title><meta name="robots" content="noindex,nofollow">',1)
bar=r'''<div id="testBanner" style="background:#D4A017;color:#1d1b1f;font:14px/1.4 system-ui,sans-serif;padding:10px 14px;display:grid;gap:8px">
<div style="font-weight:800;text-align:center">TEST SITE · Self-Correcting Start-Up · Saving here changes the real site data</div>
<div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center">
<button type="button" data-demo="agenda">1. Tonight’s Bug (Agenda View)</button>
<button type="button" data-demo="section">2. One Section Broken</button>
<button type="button" data-demo="section-staff">2b. Same, as Staff See It</button>
<button type="button" data-demo="data">3. Data Can’t Load</button>
<button type="button" data-demo="">Turn Off Demo</button></div>
<div id="demoNow" style="text-align:center;font-weight:700"></div>
<ol id="demoLog" style="margin:0 auto;padding-left:22px;max-width:760px"></ol></div>
<style>#testBanner button{background:#1d1b1f;color:#fff;border:0;border-radius:6px;padding:7px 12px;font:600 13px system-ui,sans-serif;cursor:pointer}#testBanner button.on{outline:3px solid #8C1007;outline-offset:1px}@media print{#testBanner{display:none!important}}</style>
<script>(function(){
var N={agenda:"Demo 1 is on: a visitor who chose Agenda view, with tonight’s bug put back on purpose.",section:"Demo 2 is on: the Special Events code is broken on purpose (visitor view).","section-staff":"Demo 2b is on: the same broken section, shown the way signed-in staff see it.",data:"Demo 3 is on: the site’s data is blocked on purpose.","":"No demo is on. This is the normal site."};
var cur="";try{cur=sessionStorage.getItem("rhbc-demo")||""}catch(e){}
document.querySelectorAll("#testBanner [data-demo]").forEach(function(b){if(b.dataset.demo===cur)b.classList.add("on");b.onclick=function(){var d=b.dataset.demo;try{if(d)sessionStorage.setItem("rhbc-demo",d);else sessionStorage.removeItem("rhbc-demo");if(d==="agenda")localStorage.setItem("rhbc-calview","agenda")}catch(e){}
  if(d==="agenda")location.hash="#calendar";else if(d)location.hash="#special-events";location.reload()}});
document.getElementById("demoNow").textContent=N[cur]+" What happened as the page loaded:";
function show(){var ol=document.getElementById("demoLog");ol.replaceChildren();(window.__RHBC_LOG||[]).forEach(function(t){var li=document.createElement("li");li.textContent=t;ol.append(li)})}
addEventListener("rhbc-loaded",function(){setTimeout(show,50)});setTimeout(show,2500);
})();</script>'''
assert s.count('<header class="top">')==1;s=s.replace('<header class="top">',bar+'\n<header class="top">',1)
open(dst,'w',encoding='utf-8').write(s)

#!/usr/bin/env python3
"""Build the GitHub Pages version of the RHBC site from rhbc/src2.html.
usage: build_gh.py OWNER REPO OUTDIR LIVE_DATA_JSON [--noindex]
"""
import json, os, re, sys, shutil, posixpath, urllib.parse

D = os.path.dirname(os.path.abspath(__file__))
owner, repo, out, live = sys.argv[1:5]
noindex = '--noindex' in sys.argv
src = open(os.path.join(D, 'rhbc/src2.html'), encoding='utf-8').read()


def rep(a, b, n=1):
    global src
    c = src.count(a)
    assert c == n, (c, a[:100])
    src = src.replace(a, b)


# ---- document skeleton + logo ----
head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        + ('<meta name="robots" content="noindex">\n' if noindex else '')
        + '<link rel="icon" href="images/logo.png">\n')
src = src.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
src = head + src
rep('@@LOGO_SRC@@', 'images/logo.png', src.count('@@LOGO_SRC@@'))
rep('@@LOGO_WIDE@@', 'images/logo-wide.png')
rep('@@LOGO_WIDE_DARK@@', 'images/logo-wide-dark.png')
rep('@@LOGO_HERO@@', 'images/logo-text.png', 0)

# ---- data now comes from data/site.json ----
rep('<script type="application/json" id="rhbc-data">@@RHBC_DATA@@</script>\n', '')
rep('<script type="application/json" id="rhbc-tpl">@@RHBC_TPL@@</script>\n', '')
rep('(function(){\n"use strict";', 'window.__rhbcMain=function(){\n"use strict";')
assert src.rstrip().endswith('})();\n})();\n</script>') or src.rstrip().endswith('})();\n</script>')
i = src.rstrip().rfind('})();')
src = src[:i] + '};' + src[i + 5:]
rep('const SAVED=readJSON("rhbc-data")||{events:[],notice:null};',
    'let SAVED=window.__RHBC_DATA||{events:[]};\n'
    'const GH=window.__RHBC_GH;\n'
    'const fileUrl=id=>!id?"":(GH&&GH.local[id])?GH.local[id]:id.indexOf("/")>=0?id.split("/").map(encodeURIComponent).join("/"):"/_blob/"+id;')

# legacy asset links -> repository file paths
src, n = re.subn(r'\("/_blob/"\+([A-Za-z_.]+)\)', r'fileUrl(\1)', src)
src, n2 = re.subn(r'"/_blob/"\+([A-Za-z_.]+)', r'fileUrl(\1)', src)
assert n + n2 >= 6, (n, n2)

# uploads go into named folders
rep('try{const r=await assetsApi.upload(file,{type:"application/pdf"});rec.a=r.id}\n      catch(e){jobBusy',
    'try{const r=await assetsApi.upload(file,{type:"application/pdf",folder:"files"});rec.a=r.id}\n      catch(e){jobBusy')
rep('try{const r=await assetsApi.upload(file,{type:"application/pdf"});rec.a=r.id}',
    'try{const r=await assetsApi.upload(file,{type:"application/pdf",...(isB?{folder:"bulletins/"+d.slice(0,4),name:d.replace(/-/g,"")+" RHBC Bulletin.pdf",raw:true}:{folder:"newsletters/"+d.slice(0,4),name:d.replace(/-/g,"")+" RHBC Newsletter.pdf",raw:true})});rec.a=r.id}')
rep('try{const r=await assetsApi.upload(file,{type:file.type});rec.photo=r.id}',
    'try{const r=await assetsApi.upload(file,{type:file.type,folder:"staff"});rec.photo=r.id}')
rep('try{const up=await assetsApi.upload(file,{type:"application/pdf"});links.push({text,a:up.id})}',
    'try{const up=await assetsApi.upload(file,{type:"application/pdf",folder:"files"});links.push({text,a:up.id})}')
rep('try{const r=await assetsApi.upload(f,{type:f.type});state.photos.push(',
    'try{const r=await assetsApi.upload(f,{type:f.type,folder:"photos"});state.photos.push(')

# ---- replace the Claude save/publish machinery with GitHub ----
a = src.index('const SKEL=')
b = src.index('$("saveBtn").onclick=async()=>{')
c = src.index('(function(){let p=null;try{p=sessionStorage.getItem(PENDING)}')
src = src[:a] + src[c:]
save_js = r'''$("saveBtn").onclick=async()=>{
  if(!GH.ok||!dirty)return;
  $("saveBtn").disabled=true;$("saveMsg").textContent="Saving…";
  const body=JSON.stringify(state,null,1)+"\n";
  try{
    await GH.commit(body);
    SAVED=JSON.parse(JSON.stringify(state));dirty=false;
    $("saveMsg").textContent="Saved";renderAll();
    toast("Saved. The public site updates in about a minute.");
  }catch(e){
    if(e.status===409||e.status===422){
      try{sessionStorage.setItem(PENDING,JSON.stringify(state))}catch(x){}
      toast("Someone else saved a moment ago. Reloading their version; you can restore your changes after.");
      setTimeout(()=>location.reload(),1800);return;
    }
    if(e.status===401||e.status===403){toast("Your staff sign-in key has expired or can’t edit. Sign in again.");}
    else toast("Couldn’t save just now. Check your connection and try again.");
    $("saveBtn").disabled=false;$("saveMsg").textContent="You have unsaved changes";
  }
};
'''
src = src.replace('(function(){let p=null;try{p=sessionStorage.getItem(PENDING)}', save_js + '(function(){let p=null;try{p=sessionStorage.getItem(PENDING)}', 1)

a = src.index('(async()=>{\n  try{\n    if(!window.claude||!claude.use)return;')
b = src.index('})();\n', a) + len('})();\n')
init_js = r'''/* staff sign-in (GitHub key) */
if(GH.ok){toggles.forEach(t=>t.hidden=false);document.querySelectorAll(".ms-edit,.hero-add,.doc-add,.ls-edit").forEach(b=>b.hidden=false);canEditFlag=true;assetsApi=GH.assets;renderNotice();renderPhotos();renderAll();}
$("staffLink").textContent=GH.ok?"Staff Sign Out":"Staff Sign In";
$("staffLink").onclick=e=>{e.preventDefault();
  if(GH.ok){if(dirty&&!confirm("You have unsaved changes. Sign Out anyway?"))return;GH.forget();location.reload();return}
  $("gh-key").value="";$("gh-err").hidden=true;$("overlay10").hidden=false;setTimeout(()=>$("gh-key").focus(),30)};
$("gh-cancel").onclick=closeDlg;
$("ghForm").addEventListener("submit",async ev=>{ev.preventDefault();
  const k=$("gh-key").value.trim(),err=m=>{$("gh-err").textContent=m;$("gh-err").hidden=false};
  if(!k)return err("Paste your staff sign-in key.");
  $("gh-go").disabled=true;$("gh-go").textContent="Checking…";
  const r=await GH.check(k);
  $("gh-go").disabled=false;$("gh-go").textContent="Sign in";
  if(r!=="ok")return err(r==="readonly"?"That key can view but not edit the site. Create a key with “Contents: Read and write.”":r==="net"?"Couldn’t reach GitHub. Check your connection and try again.":"That key didn’t work. Check that you copied all of it, and that it hasn’t expired.");
  GH.remember(k);location.reload();
});
if(GH.notice)setTimeout(()=>toast(GH.notice),400);
'''
src = src[:a] + init_js + src[b:]
rep('"overlay8","overlay9","overlay11","overlay12","overlay13","overlay14","overlay15","overlay16"]', '"overlay8","overlay9","overlay11","overlay12","overlay13","overlay14","overlay15","overlay16","overlay10"]')
rep('$("overlay8"),$("overlay9"),$("overlay11"),$("overlay12"),$("overlay13"),$("overlay14"),$("overlay15"),$("overlay16")].forEach(', '$("overlay8"),$("overlay9"),$("overlay11"),$("overlay12"),$("overlay13"),$("overlay14"),$("overlay15"),$("overlay16"),$("overlay10")].forEach(')

# sign-in dialog + footer link
dlg = '''<div id="overlay10" class="overlay" hidden>
  <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dlg10Title">
    <h3 id="dlg10Title">Staff Sign In</h3>
    <p class="meta">Paste your staff sign-in key (a GitHub access token for this website). You only need to do this once on each device.</p>
    <form id="ghForm" class="form" novalidate>
      <label class="full">Sign-in key<input id="gh-key" type="password" autocomplete="off" spellcheck="false" placeholder="github_pat_…"></label>
      <p class="err full" id="gh-err" hidden></p>
      <div class="dialog-actions full">
        <button class="btn ghost" type="button" id="gh-cancel">Cancel</button>
        <button class="btn primary" type="submit" id="gh-go">Sign in</button>
      </div>
    </form>
  </div>
</div>

<div id="overlay3" class="overlay" hidden>'''
rep('<div id="overlay3" class="overlay" hidden>', dlg)
rep('Matthew 7:24</p>\n  </div>\n</footer>',
    'Matthew 7:24</p>\n    <p class="staffline"><a href="#" id="staffLink">Staff Sign In</a></p>\n  </div>\n</footer>')
rep('footer .faddr{', 'footer .staffline{grid-column:1/-1;font-size:.8rem;opacity:.75;margin-top:-14px}\nfooter .staffline a{color:var(--on-brand)}\nfooter .faddr{')

# ---- loader: GitHub helpers, then fetch content, then start the page ----
loader = r'''<script>
(function(){
"use strict";
const OWNER=%s,REPO=%s,BRANCH="main",API="https://api.github.com/repos/"+OWNER+"/"+REPO;
const KEY="rhbc-gh-key";
const store={get(){try{return localStorage.getItem(KEY)||sessionStorage.getItem(KEY)}catch(e){return null}},
  set(v){try{localStorage.setItem(KEY,v)}catch(e){try{sessionStorage.setItem(KEY,v)}catch(x){}}},
  del(){try{localStorage.removeItem(KEY);sessionStorage.removeItem(KEY)}catch(e){}}};
const b64text=s=>{const u=new TextEncoder().encode(s);let b="";for(let i=0;i<u.length;i+=0x8000)b+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));return btoa(b)};
const untext=b=>new TextDecoder().decode(Uint8Array.from(atob(b.replace(/\s/g,"")),c=>c.charCodeAt(0)));
const fileB64=f=>new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(String(r.result).split(",")[1]);r.onerror=rej;r.readAsDataURL(f)});
const GH={ok:false,head:null,tree:null,notice:"",b64text,pending:{},local:{}};
let token=store.get();
async function api(path,opt={},tk=token){
  const r=await fetch(API+path,{...opt,cache:"no-store",headers:{Accept:"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28",...(tk?{Authorization:"Bearer "+tk}:{}),...(opt.body?{"Content-Type":"application/json"}:{})}});
  if(!r.ok){const e=new Error("github "+r.status);e.status=r.status;throw e}
  return r.status===204?null:r.json();
}
GH.check=async k=>{try{const r=await api("",{},k);return r.permissions&&r.permissions.push?"ok":"readonly"}catch(e){return e.status?"bad":"net"}};
GH.remember=k=>store.set(k);GH.forget=()=>store.del();
GH.put=(path,content,message,sha)=>api("/contents/"+path.split("/").map(encodeURIComponent).join("/"),{method:"PUT",body:JSON.stringify({message,content,branch:BRANCH,...(sha?{sha}:{})})});
const slug=n=>{const m=/\.([a-z0-9]{2,5})$/i.exec(n),ext=m?m[1].toLowerCase():"";let b=(m?n.slice(0,-m[0].length):n).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"").slice(0,60)||"file";return b+(ext?"."+ext:"")};
const exists=async path=>{if(GH.pending[path])return true;try{await api("/contents/"+path.split("/").map(encodeURIComponent).join("/")+"?ref="+BRANCH);return true}catch(e){if(e.status===404)return false;throw e}};
GH.assets={async upload(file,opt){
  const folder=(opt&&opt.folder)||"files",d=new Date(),day=d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");
  const content=await fileB64(file);const fixed=opt&&opt.name;let name=fixed?(opt.raw?opt.name:slug(opt.name)):slug(file.name);
  for(let k=0;k<8;k++){
    const path=fixed?folder+"/"+(k?name.replace(/(\.[a-z0-9]+)?$/,(opt.raw?" ("+(k+1)+")":"-"+(k+1))+"$1"):name):folder+"/"+day+"-"+(k?k+"-":"")+name;
    if(await exists(path))continue;
    GH.pending[path]=content;GH.local[path]=URL.createObjectURL(file);
    return{id:path,url:GH.local[path]};
  }
  throw new Error("name");
}};
/* one commit per save: new files + data/site.json together */
GH.commit=async body=>{
  const files=Object.keys(GH.pending).filter(p=>body.indexOf(JSON.stringify(p))>=0);
  const blob=async(content,encoding)=>(await api("/git/blobs",{method:"POST",body:JSON.stringify({content,encoding})})).sha;
  const tree=[];
  for(const p of files)tree.push({path:p,mode:"100644",type:"blob",sha:await blob(GH.pending[p],"base64")});
  tree.push({path:"data/site.json",mode:"100644",type:"blob",sha:await blob(body,"utf-8")});
  const t=await api("/git/trees",{method:"POST",body:JSON.stringify({base_tree:GH.tree,tree})});
  const msg="Update website content"+(files.length?"\n\nAdded:\n"+files.map(f=>"- "+f).join("\n"):"");
  const c=await api("/git/commits",{method:"POST",body:JSON.stringify({message:msg,tree:t.sha,parents:[GH.head]})});
  await api("/git/refs/heads/"+BRANCH,{method:"PATCH",body:JSON.stringify({sha:c.sha,force:false})});
  GH.head=c.sha;GH.tree=t.sha;files.forEach(p=>delete GH.pending[p]);
  return files.length;
};
window.__RHBC_GH=GH;
const start=d=>{window.__RHBC_DATA=d;const go=()=>window.__rhbcMain();document.readyState==="loading"?document.addEventListener("DOMContentLoaded",go):go()};
(async()=>{
  if(token){
    try{
      const [info,ref]=await Promise.all([api(""),api("/git/ref/heads/"+BRANCH)]);
      if(info.permissions&&info.permissions.push){
        const head=ref.object.sha;const [cm,file]=await Promise.all([api("/git/commits/"+head),api("/contents/data/site.json?ref="+head)]);
        GH.ok=true;GH.head=head;GH.tree=cm.tree.sha;return start(JSON.parse(untext(file.content)))}
      GH.notice="Your sign-in key can’t edit this site, so you’re seeing the public view.";
    }catch(e){
      if(e.status===401){store.del();GH.notice="Your staff sign-in key has expired. Sign in again with a new key."}
      else GH.notice="Couldn’t reach GitHub for editing, so you’re seeing the public view.";
    }
  }
  try{const r=await fetch("data/site.json?v="+Date.now(),{cache:"no-store"});start(await r.json())}
  catch(e){start(null)}
})();
})();
</script>
''' % (json.dumps(owner), json.dumps(repo))
src = src.rstrip() + '\n' + loader + '</body>\n</html>\n'

# ---- write the site ----
if os.path.exists(out):
    for f in os.listdir(out):
        if f == '.git':
            continue
        p = os.path.join(out, f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(src)
for sub in ['data', 'images', 'bulletins', 'newsletters', 'photos', 'staff', 'files', '.github/workflows']:
    os.makedirs(os.path.join(out, sub), exist_ok=True)
shutil.copy(os.path.join(D, 'logo/logo.png'), os.path.join(out, 'images/logo.png'))
shutil.copy(os.path.join(D, 'logo3/logo-wide-web.png'), os.path.join(out, 'images/logo-wide.png'))
shutil.copy(os.path.join(D, 'logo3/logo-wide-dark-web.png'), os.path.join(out, 'images/logo-wide-dark.png'))
shutil.copy(os.path.join(D, 'logo3/logo-text-hero.png'), os.path.join(out, 'images/logo-text.png'))
open(os.path.join(out, '.nojekyll'), 'w').write('')

# ---- content: move old-site files into folders ----
data = json.load(open(live, encoding='utf-8'))
imports = []
def local(url, folder):
    name = posixpath.basename(urllib.parse.urlparse(url).path)
    path = folder + '/' + name
    imports.append({'url': url, 'path': path})
    return path
OLD = 'rockyhockbaptistchurch.org/wp-content/uploads/'
for kind in ('bulletins', 'newsletters'):
    for it in data.get(kind, []):
        u = it.get('u', '')
        if OLD in u:
            it['a'] = local(u, kind)
            it.pop('u', None)
for sp in data.get('specials', []):
    for l in sp.get('links', []):
        if OLD in l.get('url', ''):
            l['a'] = local(l['url'], 'files'); l.pop('url', None)
for j in data.get('careers', []):
    if OLD in j.get('u', ''):
        j['a'] = local(j['u'], 'files'); j.pop('u', None)
# assets uploaded in the Claude version
adir = os.path.join(D, 'artifact-files/47d80149-dc60-45ad-ade2-a592d45d07ee')
def move_asset(aid, folder):
    if not aid or '/' in aid:
        return aid
    hits = [f for f in os.listdir(adir) if f.startswith(aid)] if os.path.isdir(adir) else []
    assert hits, 'missing asset ' + aid
    ext = os.path.splitext(hits[0])[1]
    path = f'{folder}/imported-{aid[:8]}{ext}'
    shutil.copy(os.path.join(adir, hits[0]), os.path.join(out, path))
    return path
for p in data.get('photos', []):
    p['a'] = move_asset(p.get('a'), 'photos')
for m in data.get('staff', []):
    if m.get('photo'):
        m['photo'] = move_asset(m['photo'], 'staff')
for kind in ('bulletins', 'newsletters'):
    for it in data.get(kind, []):
        if it.get('a') and '/' not in it['a']:
            it['a'] = move_asset(it['a'], kind)
json.dump(data, open(os.path.join(out, 'data/site.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(os.path.join(out, 'data/site.json'), 'a').write('\n')
json.dump(imports, open(os.path.join(out, 'data/import-list.json'), 'w'), indent=1)

READMES = {
 'bulletins': 'Weekly bulletin PDFs. Files uploaded with the website’s “Add bulletin” button are saved here automatically.',
 'newsletters': 'Monthly newsletter (The Rocky Hock Anchor) PDFs. Files uploaded with the website’s “Add newsletter” button are saved here automatically.',
 'photos': 'Photo gallery pictures. Photos added on the website’s Photos page are saved here automatically.',
 'staff': 'Staff photos uploaded from the Our Staff page.',
 'files': 'Other documents, such as league rules and job descriptions, uploaded from the Special Events and Careers pages.',
}
for k, v in READMES.items():
    open(os.path.join(out, k, 'README.md'), 'w', encoding='utf-8').write(f'# {k.capitalize()}\n\n{v}\n\nPlease add or remove files through the website’s edit buttons, so the site’s lists stay in step with this folder.\n')
open(os.path.join(out, 'data/README.md'), 'w', encoding='utf-8').write('# Data\n\n`site.json` holds the website’s editable content: calendar events, banners, the closing/delay alert, the weekly schedule, staff, special events, careers, photo captions and the bulletin/newsletter lists. It is updated automatically when staff press “Save Changes” on the website.\n')

wf = r'''name: Copy files from the old website
on:
  push:
    paths: ["data/import-list.json", ".github/workflows/import-old-files.yml"]
  workflow_dispatch:
permissions:
  contents: write
jobs:
  copy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Download files
        run: |
          python3 - <<'PY'
          import json, os, urllib.request
          items = json.load(open("data/import-list.json"))
          ok = skip = fail = 0
          for it in items:
              p = it["path"]
              if os.path.exists(p):
                  skip += 1
                  continue
              os.makedirs(os.path.dirname(p), exist_ok=True)
              try:
                  req = urllib.request.Request(it["url"], headers={"User-Agent": "Mozilla/5.0 (RHBC site migration)"})
                  with urllib.request.urlopen(req, timeout=90) as r:
                      body = r.read()
                  open(p, "wb").write(body)
                  ok += 1
              except Exception as e:
                  print("FAILED", it["url"], e)
                  fail += 1
          print(f"copied {ok}, already there {skip}, failed {fail}")
          PY
      - name: Save to the repository
        run: |
          git config user.name "rhbc-website"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add bulletins newsletters files
          git diff --cached --quiet || (git commit -m "Copy files from the old website" && git push)
'''
open(os.path.join(out, '.github/workflows/import-old-files.yml'), 'w').write(wf)

readme = f'''# Rocky Hock Baptist Church website

The public website for Rocky Hock Baptist Church, 113 Rocky Hock Church Road, Edenton, NC.

## How it’s organized

| Folder | What’s in it |
|---|---|
| `index.html` | The website itself (all pages) |
| `data/site.json` | Editable content: events, banners, alert, weekly schedule, staff, special events, careers, photo captions, bulletin and newsletter lists |
| `bulletins/` | Weekly bulletin PDFs |
| `newsletters/` | Monthly newsletter PDFs |
| `photos/` | Photo gallery pictures |
| `staff/` | Staff photos |
| `files/` | Other PDFs (league rules, job descriptions, flyers) |
| `images/` | Site images such as the logo |

## Editing the site

Staff edit the site from the website itself: scroll to the bottom of any page, click **Staff Sign In**, paste a sign-in key, and use the edit buttons. Pressing **Save Changes** updates `data/site.json`; uploads go into the folders above. The public site refreshes about a minute after each save.

A sign-in key is a GitHub *fine-grained personal access token* limited to the `{owner}/{repo}` repository with **Contents: Read and write** permission.
'''
open(os.path.join(out, 'README.md'), 'w', encoding='utf-8').write(readme)
print('built', out, len(src), 'bytes;', len(imports), 'files to copy from old site')

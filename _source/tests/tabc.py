import asyncio,datetime,json,json,base64,os
from playwright.async_api import async_playwright
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'')
SITE=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'out','')
puts=[];blobs=[];trees=[];commits=[];refs=[]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    async def handler(route):
      req=route.request;u=req.url
      if u.startswith('https://api.github.com/repos/hctynch/rhbc-website'):
        auth=req.headers.get('authorization','')
        if auth!='Bearer GOODKEY': return await route.fulfill(status=401,body='{}',content_type='application/json')
        path=u.split('rhbc-website',1)[1]
        if req.method=='GET' and path=='': return await route.fulfill(body=json.dumps({'permissions':{'push':True}}),content_type='application/json')
        if req.method=='GET' and path.startswith('/git/ref/heads/main'): return await route.fulfill(body=json.dumps({'object':{'sha':'head1'}}),content_type='application/json')
        if req.method=='GET' and path.startswith('/git/commits/'): return await route.fulfill(body=json.dumps({'tree':{'sha':'tree1'}}),content_type='application/json')
        if req.method=='GET' and path.startswith('/contents/') and not path.startswith('/contents/data/site.json'): return await route.fulfill(status=404,body='{}',content_type='application/json')
        if req.method=='POST' and path=='/git/blobs':
          bd=json.loads(req.post_data);blobs.append(bd);return await route.fulfill(status=201,body=json.dumps({'sha':'b%d'%len(blobs)}),content_type='application/json')
        if req.method=='POST' and path=='/git/trees':
          bd=json.loads(req.post_data);trees.append(bd);return await route.fulfill(status=201,body=json.dumps({'sha':'tree2'}),content_type='application/json')
        if req.method=='POST' and path=='/git/commits':
          bd=json.loads(req.post_data);commits.append(bd);return await route.fulfill(status=201,body=json.dumps({'sha':'c2'}),content_type='application/json')
        if req.method=='PATCH':
          refs.append(json.loads(req.post_data));return await route.fulfill(body='{}',content_type='application/json')
        if req.method=='GET' and path.startswith('/contents/data/site.json'):
          c=base64.b64encode(open(SITE+'data/site.json','rb').read()).decode()
          return await route.fulfill(body=json.dumps({'content':c,'sha':'sha1'}),content_type='application/json')
        if req.method=='PUT':
          bd=json.loads(req.post_data);puts.append((path,bd.get('sha'),bd['message'],len(bd['content'])))
          if path.endswith('site.json'):
            open(D+'shots/saved-site.json','wb').write(base64.b64decode(bd['content']))
          return await route.fulfill(status=201,body=json.dumps({'content':{'sha':'sha2','path':path}}),content_type='application/json')
        return await route.fulfill(status=404,body='{}')
      if u.startswith('http://rhbc.test/'):
        rel=u[len('http://rhbc.test/'):].split('?')[0].split('#')[0] or 'index.html'
        fp=SITE+rel
        if os.path.isfile(fp):
          ct={'html':'text/html','json':'application/json','png':'image/png','jpg':'image/jpeg'}.get(rel.rsplit('.',1)[-1],'application/octet-stream')
          return await route.fulfill(path=fp,content_type=ct)
        return await route.fulfill(status=404,body='nf')
      if u.startswith('https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/legacy/build/'):
        return await route.fulfill(path=D+'pj/node_modules/pdfjs-dist/legacy/build/'+u.rsplit('/',1)[1],content_type='text/javascript',headers={'access-control-allow-origin':'*'})
      if 'vimeo.com' in u: return await route.fulfill(body='<body style="background:#222;color:#fff;font:20px sans-serif;display:grid;place-items:center;height:100vh;margin:0">Vimeo live player</body>',content_type='text/html')
      return await route.abort()
    ctx=await b.new_context(viewport={'width':1280,'height':900});await ctx.route('**/*',handler);pg=await ctx.new_page()
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.clock.set_fixed_time(datetime.datetime.fromisoformat('2026-11-08T13:00:00-05:00'))
    await pg.goto('http://rhbc.test/#calendar');await pg.wait_for_timeout(900)
    await pg.click('#staffLink');await pg.fill('#gh-key','GOODKEY');await pg.click('#gh-go');await pg.wait_for_timeout(1500)
    await pg.goto('http://rhbc.test/#calendar');await pg.wait_for_timeout(400)
    print('hero',await pg.evaluate('[...document.querySelectorAll("[data-route=calendar] .phero button")].filter(b=>!b.hidden).map(b=>b.textContent)'))
    await pg.click("[data-route=calendar] .edit-toggle");await pg.wait_for_timeout(300)
    S=lambda n:pg.screenshot(path=D+'shots/abc_'+n+'.png')
    async def day(k):
      await pg.click('[data-k="%s"]'%k);await pg.wait_for_timeout(200);await pg.evaluate('document.querySelector("#dayPanel").scrollIntoView()')
    # chooser
    await pg.evaluate('document.querySelector("#addBtn").scrollIntoView()');await pg.click('#addBtn');await pg.wait_for_timeout(200);await S('chooser')
    await pg.click('.choice:has-text("A Weekly Activity")');await pg.wait_for_timeout(200);await S('addweekly')
    await pg.fill('#wList .w-title','Pickleball');await pg.select_option('#wList .w-dow','1');await pg.fill('#wList .w-start','18:00');await pg.fill('#wList .w-end','19:30')
    await pg.click('#wForm button[type=submit]');await pg.wait_for_timeout(300)
    print('after add: overlays open',await pg.evaluate('[...document.querySelectorAll(".overlay")].filter(o=>!o.hidden).map(o=>o.id)'),'toast',await pg.evaluate('document.getElementById("toast").textContent'))
    await day('2026-11-09');print('mon',await pg.evaluate('document.querySelector("#dayList").innerText.replace(/\\n+/g," | ")'))
    # chooser -> cancel returns to chooser
    await pg.click('#addBtn');await pg.click('.choice:has-text("A One-Time Event")');await pg.wait_for_timeout(150);await S('addevent')
    await pg.click('#cancelBtn');await pg.wait_for_timeout(150)
    print('back to chooser',await pg.evaluate('!document.getElementById("overlay16").hidden&&document.getElementById("g-title").textContent'))
    await pg.click('.choice:has-text("Cancel Activities")');await pg.wait_for_timeout(150);await S('addchange')
    await pg.click('#scCancel');await pg.click('#g-body .dialog-actions button');await pg.wait_for_timeout(100)
    # manage
    await pg.click('[data-route=calendar] .phero .ms-edit');await pg.wait_for_timeout(200);await S('manage_week')
    await pg.click('.ms-tabs button:has-text("Monthly")');await pg.wait_for_timeout(100);await S('manage_mo')
    await pg.click('.ms-row:has-text("Deacon") button');await pg.wait_for_timeout(150);await S('edit_mo')
    await pg.click('#mCancel');await pg.wait_for_timeout(100)
    print('back to manage',await pg.evaluate('document.getElementById("g-title").textContent'),await pg.evaluate('document.querySelector(".ms-tabs [aria-selected=true]").textContent'))
    await pg.click('.ms-tabs button:has-text("Weekly")');await pg.click('.ms-row:has-text("Deep Dive") button');await pg.wait_for_timeout(150)
    await pg.fill('#wList .w-end','19:15');await pg.click('#wForm button[type=submit]');await pg.wait_for_timeout(200)
    print('after save back in manage',await pg.evaluate('!document.getElementById("overlay16").hidden'),await pg.evaluate('document.getElementById("toast").textContent'))
    await pg.click('#g-body .dialog-actions button');await pg.wait_for_timeout(100)
    # change menu on Wed Nov 11
    await day('2026-11-11');await S('day_wed')
    await pg.click('#dayList .ev:has-text("Sanctuary Choir") .chg-wrap button');await pg.wait_for_timeout(150);await S('menu_wk')
    await pg.click('.chg-menu button:has-text("Cancel This Date")');await pg.wait_for_timeout(150);await S('cancel_dlg')
    await pg.click('#g-body button[type=submit]');await pg.wait_for_timeout(200);await S('day_canceled')
    print('cx rows',await pg.evaluate('[...document.querySelectorAll("#dayList .ev-cx")].map(x=>x.innerText.replace(/\\n/g,"|"))'))
    await pg.click('#dayList .ev:has-text("Worship Seeds") .chg-wrap button');await pg.click('.chg-menu button:has-text("Change Time")');await pg.wait_for_timeout(150)
    await pg.fill('#g-body input[type=time] >> nth=0','18:30');await pg.fill('#g-body input[type=time] >> nth=1','19:30');await S('override_dlg')
    await pg.click('#g-body button[type=submit]');await pg.wait_for_timeout(200)
    await pg.click('#dayList .ev:has-text("Mission Friends") .chg-wrap button');await pg.click('.chg-menu button:has-text("Add a Label")');await pg.fill('#g-body input','Thanksgiving Offering');await pg.click('#g-body button[type=submit]');await pg.wait_for_timeout(200)
    await S('day_changed')
    print('day',await pg.evaluate('document.querySelector("#dayList").innerText.replace(/\\n+/g," | ")'))
    await pg.click('#dayList .ev-cx button');await pg.wait_for_timeout(200)
    print('restored',await pg.evaluate('document.getElementById("toast").textContent'),await pg.evaluate('document.querySelectorAll("#dayList .ev-cx").length'))
    # monthly menu: Deacon's Meeting Nov 23
    await day('2026-11-23')
    await pg.click('#dayList .ev:has-text("Deacon") .chg-wrap button');await pg.wait_for_timeout(150);await S('menu_mo')
    await pg.click('.chg-menu button:has-text("Move This Date")');await pg.wait_for_timeout(150);await S('move_dlg')
    await pg.keyboard.press('Escape')
    # Dec 30 church conference cancels seeds -> restore
    await pg.click('[data-route=calendar] .phero .ms-edit');await pg.click('.ms-tabs button:has-text("Changes")');await pg.wait_for_timeout(150)
    print('manage changes',await pg.evaluate('document.querySelector("#g-body").innerText.replace(/\\n+/g," | ")'));await S('manage_chg')
    await pg.keyboard.press('Escape')
    # visitor view: done editing -> canceled hidden
    print('errs',errs)
    # phone
    await pg.set_viewport_size({'width':390,'height':844});await pg.wait_for_timeout(300)
    await day('2026-11-11');await S('day_phone')
    await pg.click('#dayList .ev:has-text("Worship Seeds") .chg-wrap button');await pg.wait_for_timeout(150);await S('menu_phone')
    await pg.keyboard.press('Escape')
    await pg.click('#dayList .ev:has-text("Worship Seeds") .chg-wrap button');await pg.click('.chg-menu button:has-text("Edit Worship")');await pg.wait_for_timeout(150);await S('editwk_phone');await pg.keyboard.press('Escape')
    await pg.click('#dayList .ev:has-text("Worship Seeds") .chg-wrap button');await pg.click('.chg-menu button:has-text("Undo This")');await pg.wait_for_timeout(150)
    await pg.click('#dayList .ev:has-text("Worship Seeds") .chg-wrap button');await pg.click('.chg-menu button:has-text("Change Time")');await pg.wait_for_timeout(150);await S('override_phone');await pg.keyboard.press('Escape')
    await pg.click('[data-route=calendar] .phero .ms-edit');await pg.wait_for_timeout(150);await S('manage_phone')
    await pg.click('.ms-tabs button:has-text("Monthly")');await pg.click('.ms-row:has-text("Deacon") button');await pg.wait_for_timeout(150);await S('editmo_phone');await pg.keyboard.press('Escape')
    await pg.click('#addBtn');await pg.wait_for_timeout(150);await S('chooser_phone')
    await pg.click('.choice:has-text("A One-Time Event")');await pg.wait_for_timeout(150);await S('event_phone')
    print('sw',await pg.evaluate('document.documentElement.scrollWidth'))
    await pg.keyboard.press('Escape')
    await pg.set_viewport_size({'width':1280,'height':900})
    await pg.click('#saveBtn') if await pg.locator('#saveBtn').count() else print('no saveBtn')
    await pg.wait_for_timeout(1500)
    import base64 as B
    for bl in blobs:
      t=bl['content'];t=B.b64decode(t).decode() if bl.get('encoding')=='base64' else t
      if '"weekly"' in t:
        d=json.loads(t);print('saved overrides',d.get('overrides'));print('saved changes',d.get('schedChanges'));print('pickle',[w for w in d['weekly'] if w['title']=='Pickleball']);print('labels',[e for e in d['events'] if e.get('attach')][-1:]);print('deepdive end',[w['end'] for w in d['weekly'] if w['id']=='deepdive'])
    print('errs',errs)
    await b.close()
asyncio.run(main())

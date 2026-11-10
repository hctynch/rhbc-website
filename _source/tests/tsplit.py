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
    await pg.clock.set_fixed_time(datetime.datetime.fromisoformat('2026-11-04T09:00:00-05:00'))
    up='[...document.querySelectorAll("#upList .ev h4")].map(h=>h.firstChild.textContent)'
    await pg.goto('http://rhbc.test/#calendar');await pg.wait_for_timeout(900)
    print('rows',await pg.evaluate('[...document.querySelectorAll("#filters .frow")].map(r=>r.innerText.replace(/\\n/g,"|"))'))
    print('ALL',len(await pg.evaluate(up)))
    await pg.click('#filters .chip:has-text("Fellowship")');await pg.click('#filters .chip-aud:has-text("Kids")');await pg.wait_for_timeout(200)
    print('Fellowship+Kids',await pg.evaluate(up))
    await pg.click('#filters .chip-aud:has-text("Senior Adults")');await pg.wait_for_timeout(200)
    print('Fellowship+Kids/Seniors',await pg.evaluate(up))
    await pg.click('#filters .frow:nth-child(1) .chip-all');await pg.click('#filters .frow:nth-child(2) .chip-all')
    await pg.click('#filters .chip-aud:has-text("Students")');await pg.wait_for_timeout(200)
    print('Students',await pg.evaluate(up))
    await pg.evaluate('document.querySelector("#filters").scrollIntoView()');await pg.screenshot(path=D+'shots/split_filters.png')
    await pg.click('#filters .frow:nth-child(2) .chip-all');await pg.wait_for_timeout(100)
    await pg.evaluate('document.querySelector("#upList").scrollIntoView()');await pg.screenshot(path=D+'shots/split_up.png')
    await pg.set_viewport_size({'width':390,'height':900});await pg.wait_for_timeout(300)
    await pg.evaluate('document.querySelector("#filters").scrollIntoView()');await pg.screenshot(path=D+'shots/split_filters_phone.png')
    await pg.evaluate('document.querySelector("#upList").scrollIntoView()');await pg.screenshot(path=D+'shots/split_up_phone.png')
    print('sw',await pg.evaluate('document.documentElement.scrollWidth'))
    await pg.set_viewport_size({'width':1280,'height':900})
    await pg.click('#staffLink');await pg.fill('#gh-key','GOODKEY');await pg.click('#gh-go');await pg.wait_for_timeout(1500)
    await pg.goto('http://rhbc.test/#calendar');await pg.wait_for_timeout(400)
    await pg.click("[data-route=calendar] .edit-toggle");await pg.wait_for_timeout(300)
    await pg.evaluate('document.querySelector("#addBtn").scrollIntoView()');await pg.click('#addBtn');await pg.wait_for_timeout(200)
    await pg.fill('#f-title','Test Prayer Night');await pg.click('#f-cats .cat-opt:has(input[value=prayer])');await pg.click('#f-auds .cat-opt:has(input[value=all])')
    await pg.screenshot(path=D+'shots/split_form.png')
    await pg.click('#evForm button[type=submit]');await pg.wait_for_timeout(300)
    print('new ev',await pg.evaluate('document.querySelector("#upList").innerText.includes("Test Prayer")'))
    await pg.click('[data-route=calendar] .phero .wk-edit');await pg.wait_for_timeout(200)
    r=pg.locator('#wList .nrow').nth(0);await r.locator('.nrow-tools button').first.click()
    print('wk0 checked',await r.evaluate('n=>[...n.querySelectorAll("input:checked")].map(i=>i.value)'))
    await r.locator('.w-auds .cat-opt:has(input[value=kids])').click()
    await pg.screenshot(path=D+'shots/split_wform.png')
    await pg.click('#wForm button[type=submit]');await pg.wait_for_timeout(300)
    print('wk0',await pg.evaluate('1'))
    await pg.click('[data-route=calendar] .phero .mo-edit');await pg.wait_for_timeout(200)
    r=pg.locator('#mList .mrow').nth(0);await r.locator('.nrow-tools button').first.click()
    print('mo0 checked',await r.evaluate('n=>[...n.querySelectorAll(".cat-opts input:checked")].map(i=>i.value)'))
    await pg.click('#mForm button[type=submit]');await pg.wait_for_timeout(300)
    print('mo',await pg.evaluate('1'))
    await pg.click('#saveBtn');await pg.wait_for_timeout(1500)
    d=None
    for bl in blobs:
      c=bl['content'];c=base64.b64decode(c).decode() if bl.get('encoding')=='base64' else c
      if '"events"' in c: d=json.loads(c)
    print('blobs',len(blobs),'puts',puts)
    print('saved ev',[ (e['title'],e.get('cats'),e.get('auds')) for e in d['events'] if 'Prayer' in e['title']])
    print('saved ss',[(w['cats'],w['auds']) for w in d['weekly'] if w['id']=='ss'],'mo',[(m['cats'],m.get('auds')) for m in d['monthly']])
    print('errs',errs)
    await b.close()
asyncio.run(main())

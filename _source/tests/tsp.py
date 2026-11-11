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

    sp='[...document.querySelectorAll("#specialList > .special h2")].map(h=>h.textContent)'
    hd='[...document.querySelectorAll("#specialList .sp-hidden .special h2")].map(h=>h.textContent)'
    await pg.goto('http://rhbc.test/#special-events');await pg.wait_for_timeout(900)
    print('visitor visible',await pg.evaluate(sp),'hidden section',await pg.evaluate('!!document.querySelector(".sp-hidden")'))
    await pg.click('#staffLink');await pg.fill('#gh-key','GOODKEY');await pg.click('#gh-go');await pg.wait_for_timeout(1500)
    await pg.goto('http://rhbc.test/#special-events');await pg.wait_for_timeout(500)
    await pg.click("[data-route=special-events] .edit-toggle");await pg.wait_for_timeout(300)
    await pg.click('#specialList > .special:nth-of-type(2) .sp-tools button:has-text("Hide")');await pg.wait_for_timeout(200)
    print('after hide CK: visible',await pg.evaluate(sp),'hidden',await pg.evaluate(hd))
    # add a new one as hidden
    await pg.click('#addSpecial');await pg.wait_for_timeout(200)
    await pg.fill('#sp-title','Vacation Bible School');await pg.fill('#sp-desc','Summer week for kids.')
    await pg.uncheck('#sp-show');await pg.screenshot(path=D+'shots/sp_dialog.png')
    await pg.click('#sp-apply');await pg.wait_for_timeout(300)
    print('after add hidden: visible',await pg.evaluate(sp),'hidden',await pg.evaluate(hd))
    # reorder within hidden
    await pg.click('.sp-hidden .special:has(h2:text-is("Vacation Bible School")) button:has-text("Up")');await pg.wait_for_timeout(200)
    print('after up: hidden',await pg.evaluate(hd))
    await pg.evaluate('document.querySelector(".sp-hidden").scrollIntoView()');await pg.screenshot(path=D+'shots/sp_desktop.png',full_page=False)
    # edit hidden one, keep hidden; check box state
    await pg.click('.sp-hidden .special:has(h2:text-is("CentriKid Camp")) button:has-text("Edit")');await pg.wait_for_timeout(200)
    print('dialog show checked for hidden',await pg.is_checked('#sp-show'),await pg.text_content('#sp-del'))
    await pg.fill('#sp-desc','Updated 2027 dates.');await pg.click('#sp-apply');await pg.wait_for_timeout(200)
    print('after edit hidden still',await pg.evaluate(hd))
    # show on site
    await pg.click('.sp-hidden .special:has(h2:text-is("CentriKid Camp")) button:has-text("Show on Site")');await pg.wait_for_timeout(200)
    print('after show: visible',await pg.evaluate(sp),'hidden',await pg.evaluate(hd))
    # delete
    await pg.click('.sp-hidden .special:has(h2:text-is("Vacation Bible School")) button:has-text("Edit")');await pg.wait_for_timeout(200)
    await pg.click('#sp-del');print('armed',await pg.text_content('#sp-del'));await pg.click('#sp-del');await pg.wait_for_timeout(200)
    print('after delete hidden',await pg.evaluate(hd))
    # hide basketball, phone + dark screenshots
    await pg.click('#specialList > .special:has(h2:text-is("Church League Basketball")) button:has-text("Hide")');await pg.wait_for_timeout(200)
    await pg.set_viewport_size({'width':390,'height':900});await pg.wait_for_timeout(300)
    await pg.evaluate('document.querySelector(".sp-hidden").scrollIntoView()');await pg.screenshot(path=D+'shots/sp_phone.png')
    print('phone sw',await pg.evaluate('document.documentElement.scrollWidth'))
    await pg.emulate_media(color_scheme='dark');await pg.wait_for_timeout(300);await pg.screenshot(path=D+'shots/sp_phone_dark.png')
    await pg.emulate_media(color_scheme='light');await pg.set_viewport_size({'width':1280,'height':900})
    await pg.click('#saveBtn');await pg.wait_for_timeout(1500)
    d=None
    for bl in blobs:
      c=bl['content'];c=base64.b64decode(c).decode() if bl.get('encoding')=='base64' else c
      if '"specials"' in c: d=json.loads(c)
    print('saved',[(x['title'],x.get('hidden')) for x in d['specials']] if d else 'NO SAVE')
    # visitor view of saved data
    open(SITE+'data/site.json','w').write(json.dumps(d))
    ctx2=await b.new_context(viewport={'width':1280,'height':900});await ctx2.route('**/*',handler);p2=await ctx2.new_page()
    await p2.goto('http://rhbc.test/#special-events');await p2.wait_for_timeout(900)
    print('visitor after save',await p2.evaluate(sp),'hidden in DOM',await p2.evaluate('document.body.innerText.includes("Hidden Events")'))
    print('errs',errs)
    await b.close()
asyncio.run(main())

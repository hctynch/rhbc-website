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
    for vw,tag in [((1280,900),'d'),((390,844),'p')]:
      ctx=await b.new_context(viewport={'width':vw[0],'height':vw[1]});await ctx.route('**/*',handler);pg=await ctx.new_page()
      errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('http://rhbc.test/#bulletins');await pg.wait_for_timeout(900)
      print(tag,'visitor sees add',await pg.is_visible('[data-add=bulletins]'))
      await pg.click('#staffLink');await pg.fill('#gh-key','GOODKEY');await pg.click('#gh-go');await pg.wait_for_timeout(1500)
      await pg.goto('http://rhbc.test/#bulletins');await pg.wait_for_timeout(500)
      print(tag,'staff sees add',await pg.is_visible('[data-add=bulletins]'),await pg.evaluate('[...document.querySelectorAll("[data-route=bulletins] .phero button:not([hidden])")].map(b=>b.textContent+":"+Math.round(b.getBoundingClientRect().height))'))
      await pg.locator('[data-route=bulletins] .phero').screenshot(path=D+'shots/docadd_%s.png'%tag)
      await pg.click('[data-add=bulletins]');await pg.wait_for_timeout(300)
      opts=await pg.evaluate('[...document.querySelectorAll("#d-title-sel option")].map(o=>o.textContent)');print(tag,len(opts),opts[:6],opts[-2:])
      await pg.screenshot(path=D+'shots/docdlg_%s.png'%tag)
      await pg.select_option('#d-title-sel','__new');await pg.fill('#d-title','Thanksgiving Sunday')
      await pg.check('input[name=d-src][value=link]');await pg.fill('#d-url','https://example.org/b.pdf');await pg.fill('#d-date','2026-11-22')
      await pg.click('#d-apply');await pg.wait_for_timeout(400)
      print(tag,'savebar',await pg.is_visible('#saveBtn'),await pg.evaluate('document.querySelector("#bulletinList").innerText.slice(0,80)'))
      await pg.goto('http://rhbc.test/#newsletters');await pg.wait_for_timeout(400)
      await pg.click('[data-add=newsletters]');await pg.wait_for_timeout(300)
      print(tag,'nl opts',await pg.evaluate('[...document.querySelectorAll("#d-title-sel option")].map(o=>o.textContent)'),await pg.evaluate('document.getElementById("d-title-label").textContent'))
      await pg.screenshot(path=D+'shots/nldlg_%s.png'%tag)
      print(tag,'errs',errs);await ctx.close()
    await b.close()
asyncio.run(main())

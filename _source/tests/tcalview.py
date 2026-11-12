# Loads the site with each saved Calendar view (Month / List) on desktop and phone (dark),
# and checks the real data loads (no silent fallback) with no page errors.
import asyncio,os
from playwright.async_api import async_playwright
SITE=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'out','')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch();bad=0
    async def h(route):
      u=route.request.url
      if u.startswith('http://rhbc.test/'):
        rel=u[17:].split('?')[0].split('#')[0] or 'index.html';fp=SITE+rel
        if os.path.isfile(fp):return await route.fulfill(path=fp)
        return await route.fulfill(status=404,body='nf')
      return await route.abort()
    for mode in ['month','agenda']:
      for vp,dark in [((1280,900),False),((390,900),True)]:
        c=await b.new_context(viewport={'width':vp[0],'height':vp[1]},color_scheme='dark' if dark else 'light');await c.route('**/*',h);pg=await c.new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://rhbc.test/');await pg.evaluate(f'localStorage.setItem("rhbc-calview","{mode}")')
        for route in ['special-events','calendar','']:
          await pg.goto('http://rhbc.test/#'+route);await pg.reload();await pg.wait_for_timeout(700)
          r=await pg.evaluate('({d:window.__RHBC_DATA?"loaded":"NULL",sp:[...document.querySelectorAll("#specialList > .special h2")].map(h=>h.textContent),ag:document.querySelectorAll("#agView li").length})')
          ok=r['d']=='loaded' and not errs;bad+=not ok
          print('OK ' if ok else 'BAD',mode,vp[0],'#'+route,r,errs)
        if mode=='agenda' and vp[0]==390:
          await pg.goto('http://rhbc.test/#calendar');await pg.wait_for_timeout(500);await pg.screenshot(path=os.path.dirname(os.path.abspath(__file__))+'/shots/agenda_phone_dark.png')
        await c.close()
    await b.close();print('FAILURES',bad)
asyncio.run(main())

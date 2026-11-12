# Tests the self-correcting start-up: each demo on the test page, plus the normal site.
import asyncio,os,sys
from playwright.async_api import async_playwright
SITE=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'out','')
SH=os.path.dirname(os.path.abspath(__file__))+'/shots/'
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    async def h(route):
      u=route.request.url
      if u.startswith('http://rhbc.test/'):
        rel=u[17:].split('?')[0].split('#')[0] or 'index.html';fp=SITE+rel
        if os.path.isfile(fp):return await route.fulfill(path=fp)
        return await route.fulfill(status=404,body='nf')
      return await route.abort()
    Q='''({log:window.__RHBC_LOG,sp:[...document.querySelectorAll("#specialList > .special h2")].map(h=>h.textContent),spErr:!!document.querySelector("#specialList .load-err"),
      fail:(document.getElementById("loadFail")||{}).textContent||"",agenda:document.querySelector(".cal").classList.contains("agmode"),calview:localStorage.getItem("rhbc-calview"),
      cells:document.querySelectorAll("#grid .cell").length,staff:document.querySelectorAll("#staffList > *").length,dows:document.querySelectorAll("#dows .dow").length})'''
    if '--net' not in sys.argv:
     for vp,dark,tag in [((1280,900),False,'desk'),((390,900),True,'phone')]:
       c=await b.new_context(viewport={'width':vp[0],'height':vp[1]},color_scheme='dark' if dark else 'light');await c.route('**/*',h);pg=await c.new_page()
       errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
       await pg.goto('http://rhbc.test/startup-test.html#special-events');await pg.wait_for_timeout(900)
       for demo in ['agenda','section','data','']:
         await pg.click(f'#testBanner [data-demo="{demo}"]');await pg.wait_for_timeout(1800)
         r=await pg.evaluate(Q);print(tag,'DEMO',repr(demo),r,'errs',errs);errs.clear()
         await pg.evaluate('window.scrollTo(0,0)');await pg.screenshot(path=SH+f'su_{tag}_{demo or "off"}.png')
         if demo=='section':
           await pg.goto('http://rhbc.test/startup-test.html#special-events');await pg.wait_for_timeout(900)
           await pg.evaluate('document.querySelector("#specialList").scrollIntoView({block:"center"})');await pg.screenshot(path=SH+f'su_{tag}_section_spot.png')
       await c.close()
    # reload safety net: a start-up crash outside any section, only while Agenda view is remembered
    c=await b.new_context();await c.route('**/*',h);pg=await c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.add_init_script('''(()=>{let m;Object.defineProperty(window,"__rhbcMain",{configurable:true,get(){return m},set(f){m=function(){if(localStorage.getItem("rhbc-calview")==="agenda")throw new Error("Test: start-up bug");return f.apply(this,arguments)}}})})()''')
    await pg.goto('http://rhbc.test/#special-events');await pg.evaluate('localStorage.setItem("rhbc-calview","agenda");setTimeout(()=>location.reload(),50)');await pg.wait_for_timeout(4000)
    print('RELOAD NET',await pg.evaluate(Q),errs)
    await c.close()
    c=await b.new_context();await c.route('**/*',h);pg=await c.new_page()
    await pg.add_init_script('''(()=>{let m;Object.defineProperty(window,"__rhbcMain",{configurable:true,get(){return m},set(f){m=function(){throw new Error("Test: always broken")}}})})()''')
    await pg.goto('http://rhbc.test/#special-events');await pg.wait_for_timeout(2500)
    print('ALWAYS BROKEN',await pg.evaluate('({log:window.__RHBC_LOG,fail:(document.getElementById("loadFail")||{}).textContent})'))
    await b.close()
asyncio.run(main())

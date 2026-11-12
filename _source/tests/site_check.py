# Website Check: loads the site the way visitors do (Full Calendar and Agenda views remembered)
# and reports any section that can't load. Used by .github/workflows/website-check.yml.
#   python3 site_check.py [--demo] [--root DIR] [--out result.json] [--body body.md]
# --demo loads startup-test.html with the broken Special Events demo, to send a sample email.
import asyncio, datetime, functools, http.server, json, os, sys, threading, zoneinfo
from playwright.async_api import async_playwright

args = sys.argv[1:]
DEMO = '--demo' in args
def opt(name, default):
    return args[args.index(name) + 1] if name in args else default
ROOT = os.path.abspath(opt('--root', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')))
OUT, BODY = opt('--out', 'result.json'), opt('--body', 'body.md')
SITE = 'https://hctynch.github.io/rhbc-website/'
ADMIN = os.environ.get('ADMIN', 'hctynch')

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d/' % srv.server_address[1]

async def visit(b, view):
    c = await b.new_context()
    page_file = 'startup-test.html' if DEMO else 'index.html'
    init = 'try{localStorage.setItem("rhbc-calview",%s)}catch(e){}' % json.dumps(view)
    if DEMO: init += 'try{sessionStorage.setItem("rhbc-demo","section")}catch(e){}'
    await c.add_init_script(init)
    pg = await c.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(BASE + page_file + '#special-events'); await pg.wait_for_timeout(4000)
    r = await pg.evaluate('''({fails:window.__RHBC_FAILS||[],fixed:window.__RHBC_FIXED||[],log:window.__RHBC_LOG||[],
        bar:(document.getElementById("loadFail")||{}).textContent||"",loaded:!!window.__RHBC_DATA})''')
    await c.close()
    r['errs'] = errs; r['view'] = 'Agenda' if view == 'agenda' else 'Full Calendar'
    return r

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        runs = [await visit(b, v) for v in ('month', 'agenda')]
        await b.close()
    fails = {}
    for r in runs:
        for f in r['fails']:
            k = f['section']; fails.setdefault(k, dict(f, views=[], sees='“This section couldn’t load right now.”'))['views'].append(r['view'])
        for f in r['fixed']:
            k = f['section']; fails.setdefault(k, dict(f, views=[], sees='A normal page: it fixed itself by resetting their remembered Calendar view'))['views'].append(r['view'])
        if any('Page reloaded with remembered choices cleared' in x or 'Start-up failed' in x for x in r['log']) and not r['bar']:
            k = 'Page Start-Up'; fails.setdefault(k, {'section': k, 'page': 'Every', 'route': '', 'error': next((x for x in r['log'] if 'Start-up failed' in x), ''), 'views': [], 'sees': 'A normal page after one automatic reload'})['views'].append(r['view'])
        if r['bar'] and not r['fails']:
            k = 'Whole Site'
            fails.setdefault(k, {'section': k, 'page': 'Every', 'route': '', 'error': r['bar'], 'views': [], 'sees': 'A red “couldn’t load” bar at the top'})['views'].append(r['view'])
    fails = list(fails.values())
    now = datetime.datetime.now(zoneinfo.ZoneInfo('America/New_York')).strftime('%B %-d, %Y at %-I:%M %p ET')
    pages = sorted({f['page'] for f in fails})
    title = ('[Demo] ' if DEMO else '') + 'Website Error: ' + (pages[0] + ' page' if len(pages) == 1 else '%d pages' % len(pages))
    sig = 'sig:' + '|'.join(sorted(f['section'] + '=' + f['error'] for f in fails))
    rows = '\n'.join('| [%s](%s#%s) | %s | %s | %s | `%s` |' % (
        f['page'], SITE, f['route'], f['section'], f['sees'], ' and '.join(f['views']), f['error'].replace('|', '/')) for f in fails)
    body = f'''{'**This is a demo.** It was sent on purpose using the test page’s broken Special Events section, to show what an error email looks like. The live site is fine.' + chr(10) + chr(10) if DEMO else ''}The automatic **Website Check** found a problem on the Rocky Hock Baptist Church website.

| Page | Section | What visitors see | Calendar view | Error |
| --- | --- | --- | --- | --- |
{rows}

- **Found:** {now}
- **The rest of the site is working.** Only the section(s) above are affected; visitors never see old or hidden events. A section that “fixed itself” still has a bug that needs fixing.
- Signed-in staff see a red **Staff Only: Website Error** bar on every page until this is fixed.
- This issue **closes itself** (and emails you) when the Website Check passes again.

@{ADMIN} (site administrator)

<!-- {sig} -->
'''
    json.dump({'failed': len(fails), 'title': title, 'sig': sig, 'fails': fails, 'runs': runs}, open(OUT, 'w'), indent=1)
    open(BODY, 'w').write(body)
    print(json.dumps({'failed': len(fails), 'title': title, 'fails': fails}, indent=1))

asyncio.run(main())

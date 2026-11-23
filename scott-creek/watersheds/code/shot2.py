import asyncio, http.server, threading, functools, sys
from playwright.async_api import async_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
port=int(sys.argv[2]) if len(sys.argv)>2 else 8772
s=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Q,directory='site')); threading.Thread(target=s.serve_forever,daemon=True).start()
tabs=sys.argv[1].split(',')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1400,'height':950}); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e))); pg.on('response',lambda r: errs.append(r.url) if r.status>=400 else None)
        await pg.goto(f'http://127.0.0.1:{port}/index.html'); await pg.wait_for_timeout(3000)
        await pg.screenshot(path='/tmp/s_init.png')
        print('checked at start',await pg.evaluate("['ov-chm','ov-tree','ov-twi'].map(i=>document.getElementById(i).checked)"))
        for n,k in enumerate(tabs):
            await pg.click('#tab-'+k); await pg.wait_for_timeout(2500); await pg.click('#years button:last-child'); await pg.wait_for_timeout(1500)
            for o in ('ov-chm','ov-tree','ov-twi'): await pg.uncheck('#'+o)
            lay=('ov-chm','ov-tree') if n%2==0 else ('ov-twi',)
            for o in lay: await pg.check('#'+o)
            await pg.wait_for_timeout(2500); await (await pg.query_selector('#stage')).screenshot(path=f'/tmp/s_{k}.png')
        print(errs); await b.close()
asyncio.run(main())

"""Headless test driver (Playwright + Chromium/SwiftShader). Serve the test folder first:
    cd test && python3 -m http.server 8765 --bind 127.0.0.1
then:  python3 run.py '<json list of steps>'
Steps: [cmd, {args}, [reply keys]]  -> sends a debug command to the game (see CLAUDE.md "Debug channel")
       ["shot", path] / ["js", expr] / ["wait", ms]
Screenshots go wherever you point them (use test/out/)."""
import asyncio, os
URL = os.environ.get("LLA_URL", "http://127.0.0.1:8765/game.html")
import asyncio, json, sys
from playwright.async_api import async_playwright
STEPS = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page(viewport={"width": 1280, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(6000)
        await pg.evaluate("""() => { window.dbg = (cmd, extra={}) => new Promise(res => { const id = Math.random(); const h = e => { if (e.data && e.data.dbg==='lla-r' && e.data.id===id){ removeEventListener('message',h); res(e.data.r);} }; addEventListener('message', h); window.postMessage(Object.assign({dbg:'lla',id,cmd},extra),'*'); setTimeout(()=>res('timeout'),20000); }); }""")
        for st in STEPS:
            if st[0] == 'shot':
                await pg.screenshot(path=st[1]); print('shot', st[1]); continue
            if st[0] == 'js':
                print('js', await pg.evaluate(st[1])); continue
            if st[0] == 'wait':
                await pg.wait_for_timeout(st[1]); continue
            r = await pg.evaluate("([c, x]) => dbg(c, x)", [st[0], st[1] if len(st) > 1 else {}])
            keys = st[2] if len(st) > 2 else ['error']
            print(st[0], json.dumps({k: (r.get(k) if isinstance(r, dict) else r) for k in keys})[:600])
        print('ERRORS:', errs[:10])
        await b.close()
asyncio.run(main())

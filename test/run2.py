"""Headless test driver (Playwright + Chromium/SwiftShader). Serve the test folder first:
    cd test && python3 -m http.server 8765 --bind 127.0.0.1
then:  python3 run2.py '<json list of steps>'
Steps: [cmd, {args}, [reply keys]]  -> sends a debug command to the game (see CLAUDE.md "Debug channel")
       ["shot", path] / ["js", expr] / ["wait", ms]
       Two-player version: every command step starts with the page index 0 or 1, e.g. [0, "net", {"code": "t1"}]; ["shot", i, path].
Screenshots go wherever you point them (use test/out/)."""
import asyncio, os
URL = os.environ.get("LLA_URL", "http://127.0.0.1:8765/game.html")
import asyncio, json, sys
from playwright.async_api import async_playwright
STEPS = json.loads(sys.argv[1])
INIT = """() => { window.dbg = (cmd, extra={}) => new Promise(res => { const id = Math.random(); const h = e => { if (e.data && e.data.dbg==='lla-r' && e.data.id===id){ removeEventListener('message',h); res(e.data.r);} }; addEventListener('message', h); window.postMessage(Object.assign({dbg:'lla',id,cmd},extra),'*'); setTimeout(()=>res('timeout'),20000); }); }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width": 960, "height": 540})
        pages, errs = [], [[], []]
        for i in range(2):
            if pages:
                await pages[0].evaluate(INIT); await pages[0].evaluate("dbg('norender', {on: true})")
            pg = await ctx.new_page()
            await pg.add_init_script("Object.defineProperty(document,'visibilityState',{get:()=>'visible'});Object.defineProperty(document,'hidden',{get:()=>false});document.hasFocus=()=>true;")
            pg.on("pageerror", lambda e, i=i: errs[i].append(str(e)))
            pg.on("console", lambda m, i=i: errs[i].append(m.text) if m.type == "error" else None)
            await pg.goto(URL, wait_until="domcontentloaded", timeout=90000); pages.append(pg)
        await asyncio.sleep(3)
        for pg in pages:
            await pg.evaluate(INIT); await pg.evaluate("document.getElementById('menu').style.display='none'"); await pg.evaluate("dbg('norender', {on: true})")
        for st in STEPS:
            if st[0] == 'wait': await asyncio.sleep(st[1] / 1000); continue
            if st[0] == 'shot':
                await pages[st[1]].evaluate("dbg('norender', {on: false})"); await asyncio.sleep(1.5); await pages[st[1]].screenshot(path=st[2], timeout=60000); await pages[st[1]].evaluate("dbg('norender', {on: true})"); print('shot', st[2]); continue
            if st[0] == 'js': print('js', st[1], await pages[st[1]].evaluate(st[2])); continue
            i, cmd = st[0], st[1]; args = st[2] if len(st) > 2 else {}; keys = st[3] if len(st) > 3 else ['error']
            r = await pages[i].evaluate("([c, x]) => dbg(c, x)", [cmd, args])
            print(i, cmd, json.dumps({k: (r.get(k) if isinstance(r, dict) else r) for k in keys})[:900])
        print('ERRORS0:', [e for e in errs[0] if 'TUNNEL' not in e][:8]); print('ERRORS1:', [e for e in errs[1] if 'TUNNEL' not in e][:8])
        await b.close()
asyncio.run(main())

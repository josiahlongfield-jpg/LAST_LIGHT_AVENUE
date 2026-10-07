# Last Light Avenue

A browser first-person shooter built with three.js r128. It's set on an abandoned New York avenue at sunset.
The whole game ships as **one self-contained HTML file** with every model and sound inlined.

- **Live version:** published as a claude.ai artifact (private to the owner): https://claude.ai/artifact/HX5UWp8mAHDcAh4i1KX9C1
  It's published with the `room` capability, which online deathmatch needs.
- **Standalone copy:** `dist/last-light-avenue.html`. Double-click it to play. Online play doesn't work from this copy: it falls back to same-browser tabs only.

## Modes
- **Survival:** waves of AI soldiers. A 12-minute day/night cycle takes you from sunset through night (night-vision goggles on N, weapon torch on T). You can climb the fire escapes to the rooftops.
- **Deathmatch · online:** free-for-all for up to 8 players on a room code. The match is first to 20 kills or 10 minutes, with respawns. Hold Tab for the scoreboard.
- **The figure:** a horror element at night. It's only visible through the night vision, gets closer every time the goggles go up and down, vanishes if you stare at it or walk toward it, and ends in a jump scare that knocks out the goggles.

## Layout
```
src/game_template.html   THE source. All HTML, CSS and game JS live here (one IIFE). Data is injected at build time.
data/weapon_hd.json      Weapon models + first-person arms + per-weapon anim metadata (built by tools/weapons_export.py)
data/weapon_hd.base.json The base weapon file weapons_export.py starts from (carbine/sniper from earlier tools)
data/soldier_lp.json     Low-poly soldier used for enemies and other players (built by tools/lp_soldier.py)
data/city_sounds.json    Every sound as base64 WAV (the editable audio master, ~20 MB)
data/city_sounds_mp3.json  Same sounds as MP3, which is what the game actually inlines (built by tools/compress_sounds.py)
tools/                   Python generators: models (knight.py, hd_lib.py, wlib.py, weapons_export.py, lp_soldier.py)
                         and audio (real_sounds.py, asset_audio.py, horror_audio.py, compress_sounds.py)
assets/wav, assets/wav2  Source recordings (openly licensed; credits are in the game's "Sound credits" panel)
build.py                 Inlines data into the template -> dist/ and test/game.html, then syntax-checks the script with node
test/run.py, run2.py     Headless Playwright drivers (single player / two players)
test/three.min.js        three.js r128 for offline tests
```

## Build
```
python3 build.py
```
Needs Python 3, plus Node for the syntax check. After changing the template, always rebuild and check that `syntax: ok` prints.

Rebuilding models (only when you change the model tools). Run these from `data/`:
```
cd data && cp weapon_hd.base.json weapon_hd.json && python3 ../tools/weapons_export.py && python3 ../tools/lp_soldier.py
```
Rebuilding sounds (only when you change the audio tools). Run from `data/`; needs numpy, scipy and ffmpeg with libmp3lame:
```
cd data && python3 ../tools/asset_audio.py && python3 ../tools/horror_audio.py && python3 ../tools/compress_sounds.py
```
`real_sounds.py` (gun recordings) also writes into `city_sounds.json`; run it first if you change the guns.
Every new sound needs a `GAIN` entry in the template, and a credit in the Sound credits panel if it comes from a new source.

## Template map (search for the `// ====` section headers)
renderer/sky → materials → static batching → street layout → buildings (fire escapes, roofs) → vehicles → street furniture →
day/night + lamps + torch + night vision (NV post-process shader `nvMat`) → **the figure** (`FIG`, `buildFigureModel`, `poseFigure`,
`updateFigure`) → player viewmodels (`WEAPONS`, `RIGS`, reload keyframes `ARMK`, `animateReload`, shotgun shells, pump, bolt, slide) →
audio (`sfx`, positional `sfxAt` with HRTF, occlusion, reverb) → state (`P` player, `Wp` weapon) → collision → enemies (`makeBot`, `updateBot` AI)
→ effects → HUD → menu/input/loadout → survival waves → climbing → weapon actions (`shoot`, `reload`) → main loop `step()` →
**online deathmatch** (`NET`, transports, puppets, hits, match clock) → debug channel.

Conventions:
- Shared helpers: `rand`, `randi`, `clamp`, `lerp`, `damp(k, dt)`, `angDiff`, `pick`, `V3` (THREE.Vector3), `tmp`/`tmp2` scratch vectors.
- Static scenery goes through `vis()/vbox()/vgeo()`, which batch it into one draw call per material. Colliders go through `solid()/proxy()`.
- Player yaw 0 looks down -Z. Bots and puppets face +Z at rotation 0, so a remote player's puppet uses `yaw + PI`.
- Comments say *why*, briefly, in plain words.

## Online deathmatch (how it works)
- Transport: on claude.ai, `await window.claude.use('room')` then `room.join('lla-' + code)`. Each player publishes one presence object
  (`netPublish`, ~25/s, under 4 KiB): position/aim, weapon, alive, hp, kills/deaths, last death `ld`, shot counter `f` + direction `fd`,
  and a rolling list `h` of hits they landed `[seq, targetPeer, dmg, head]`. Anywhere else, it falls back to a `BroadcastChannel`
  (same browser only). That fallback is also how the tests run two players.
- The shooter decides hits (shooter-authoritative): the victim applies any `h` entries addressed to its own peer id. Kills are credited
  when the killer sees the victim's `ld` name them. Deaths from an older match number (`e`) are ignored.
- Host = the earliest joiner (`electHost`). The host owns the match clock, time of day, winner and match number (`M`) in its presence;
  everyone else follows. If the host leaves, the next earliest joiner carries on from the last `M` it saw.
- Remote players are drawn as soldier puppets (`makePuppet`), interpolated about 110 ms behind (`animatePuppet`).
- Untested on real claude.ai between two people. Everything above was verified with two headless tabs.

## Debug channel (for automated checks)
The page listens for `postMessage({dbg:'lla', id, cmd, ...args})` and replies `{dbg:'lla-r', id, r}` with a big state snapshot
(player, weapon, bots, wave, tod, fig incl. `fig.net`, audio...). Commands: start, reset, set {pos,yaw,pitch,hp,difficulty}, sim {s}
(advance s seconds at 60 fps without rendering), key {code,ms}, fire {n}, ads, look, ray, weapon, loadout, tune, tod {th}, nv, torch,
climb, approach, audiotest, figD {D} (place the figure D metres away), forget, pause, norender {on}, net {code,name,color},
aimNet {i,head}, netClock {t}, leaveNet. `test/run.py` and `test/run2.py` wrap this.

Testing tips:
- Serve `test/` over http (`python3 -m http.server 8765 --bind 127.0.0.1`). The page needs a UTF-8 charset, which `test/game.html` has.
- Hide the menu before screenshots: `["js", "document.getElementById('menu').style.display='none'"]`.
- In two-page tests, background tabs throttle requestAnimationFrame. Drive time with `sim` on each page alternately, with short `wait`s
  in between so BroadcastChannel messages get delivered, and keep `norender` on except for screenshots (run2.py does this).
- Night: `["tod", {"th": -1.0}]`. Figure: `["figD", {"D": 12}]` with NV on.

## Publishing
`dist/artifact.html` is what gets published to the artifact URL above. Keep the `room` capability when republishing.

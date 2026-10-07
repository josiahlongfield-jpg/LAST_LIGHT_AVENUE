# Last Light Avenue

A browser first-person shooter built with three.js r128. It's set on an abandoned New York avenue at sunset.
The whole game ships as **one self-contained HTML file** with every model and sound inlined.

- **Live version:** published as a claude.ai artifact (private to the owner): https://claude.ai/artifact/HX5UWp8mAHDcAh4i1KX9C1
  It's published with the `room` capability, which online deathmatch needs.
- **Standalone copy:** `dist/last-light-avenue.html`. Double-click it to play. Online play doesn't work from this copy: it falls back to same-browser tabs only.

## Modes
- **Survival:** waves of AI soldiers. A 6-minute day/night cycle takes you from sunset through night (night-vision goggles on N, weapon torch on T). You can climb the fire escapes to the rooftops.
- **Deathmatch · online:** free-for-all for up to 8 players on a room code. The match is first to 20 kills or 10 minutes, with respawns. Hold Tab for the scoreboard.
- **Hunted:** the avenue's barricades come down and its cross streets run on into a grid city about 240 x 260 m (built the first time
  the mode is picked). Find three radios (hold E for 6 s, which is loud), then hold out for 60 s at the evac flare until the helicopter comes.
  It starts mid-morning, with about 2½ minutes of daylight. **By day** Survival soldiers come for you through the streets (they steer round
  the blocks with `navDir`): up to 3 / 5 / 7 alive at once, one every ~14 / 9 / 6 s, by difficulty. Every soldier you kill stays where he fell
  as a body (`bakeCorpse`, one vertex-coloured mesh, up to 40). **At night** each body's ghost (a **husk**, dressed in that soldier's squad kit)
  gets up out of it within 25 s: they always know where you are, move fast, fire accurate 3–4 round bursts and club you up close. Ordinary rounds
  pass straight through them. At dawn they lie down and fade, and get up again the next night. **The Veil:** your 6th soldier kill drops a
  glowing violet case; walk over it, then press V to fit it (about a second, no firing). Fitted, every gun gets violet rings, side lines,
  a canister and a glowing mag slot, purple flash and tracers; its rounds kill husks (which burst apart outward from the killing shot, and
  that body never gets up again) but do 60% damage to living soldiers. **The figure** is still there (same rules as Survival, but its scare does 35 damage).
- **Carbine attachments** (loadout screen, "Carbine attachments" panel with a live 3D preview; saved in localStorage `lla-att`):
  magazine 20 / 30 / 40 / 60 drum, barrel short / standard / long, optic irons / red dot / holographic / 4x scope (the scope uses the
  sniper's full-screen `#scope` overlay with a red chevron, class `acog`), grip none / vertical / angled, muzzle flash hider / suppressor.
  Each option scales the stats in `ATT_SLOTS`. The suppressor swaps the shot sound to `shot_sup0-2`, shrinks the flash, and cuts how far
  the shot is heard (bots alerted, Hunted noise) from 70 m to 22 m; online, presence `sp` tells other players to play the suppressed sound.
  The sniper and SMG get a suppressor too (rows under the panel, `SUPX`, `applySuppressors`, saved as `ATT.sx`), each with its own
  sounds (`Wd.supSnd`: carbine `sup_m0-2` (De Lisle), sniper `sup_s0-1`, SMG `shot_sup0-2` (Sabacky)).
- **The figure:** a horror element at night. It's only visible through the night vision, gets closer every time the goggles go up and down, vanishes if you stare at it or walk toward it, and ends in a jump scare that knocks out the goggles.
  It only moves when the goggles come down, and its distance carries over from night to night. Night vision whites out in daylight (`uBlind`), so the goggles
  have to come off every morning. During the scare it is pinned to your view (`pinFigure`).

## Layout
```
src/game_template.html   THE source. All HTML, CSS and game JS live here (one IIFE). Data is injected at build time.
data/weapon_hd.json      Weapon models + first-person arms + per-weapon anim metadata (built by tools/weapons_export.py)
data/weapon_hd.base.json The base weapon file weapons_export.py starts from (carbine/sniper from earlier tools)
data/soldier_lp.json     Low-poly soldier used for enemies and other players (built by tools/lp_soldier.py)
data/city_sounds.json    Every sound as base64 WAV (the editable audio master, ~20 MB)
data/city_sounds_mp3.json  Same sounds as MP3, which is what the game actually inlines (built by tools/compress_sounds.py)
tools/                   Python generators: models (knight.py, hd_lib.py, wlib.py, weapons_export.py, lp_soldier.py)
                         and audio (real_sounds.py, asset_audio.py, horror_audio.py, hunt_audio.py, supp_audio.py, compress_sounds.py)
assets/wav, wav2, wav3 Source recordings (wav3: suppressed shots; the Sonniss De Lisle take is trimmed to three shots, keep raw bundle WAVs out of git) (openly licensed; credits are in the game's "Sound credits" panel)
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
cd data && python3 ../tools/asset_audio.py && python3 ../tools/horror_audio.py && python3 ../tools/hunt_audio.py && python3 ../tools/supp_audio.py && python3 ../tools/compress_sounds.py
```
`real_sounds.py` (gun recordings) also writes into `city_sounds.json`; run it first if you change the guns.
Every new sound needs a `GAIN` entry in the template, and a credit in the Sound credits panel if it comes from a new source.

## Template map (search for the `// ====` section headers)
renderer/sky → materials → static batching (+ layers) → street layout → buildings (fire escapes, roofs) → vehicles → street furniture →
day/night + lamps + torch + night vision (NV post-process shader `nvMat`) → **the figure** (`FIG`, `buildFigureModel`, `poseFigure`,
`updateFigure`) → player viewmodels (`WEAPONS`, `RIGS`, carbine attachments: `CARB` (the carbine split into body / front / turrets at load so the barrel can
slide), `ATT_SLOTS`, `AP` parts, `applyAttachments()`, the loadout picker `renderAtt`/`attPreview`; reload keyframes `ARMK`, `animateReload`, shotgun shells, pump, bolt, slide) →
audio (`sfx`, positional `sfxAt` with HRTF, occlusion, reverb) → state (`P` player, `Wp` weapon) → collision → enemies (`makeBot`, `updateBot` AI)
→ effects → HUD → menu/input/loadout → survival waves → climbing → weapon actions (`shoot`, `reload`) →
**Hunted** (`CITY`/`buildCity`, nav grid `NAV`/`navFlow`, horror models and minds `HZ`; husks: `ghostMat` shader, `HUSK_LOOKS` (one per squad), `buildHusk`,
`setLook`, `poseHusk`, `updateHusk`, `huskFire`, `shatterHusk`; the bodies `CORPSES`/`bakeCorpse`/`huskRise`; ammo cans `DROPS`; the Veil
(`VEIL`, `veilKit` per rig, `veilApply`, `veilFit`, case `VCASE`, `updateVeil`); day soldiers `huntBot`; radios/`EVAC`, `huntReset`, `updateHunt`) → main loop `step()` →
**online deathmatch** (`NET`, transports, puppets, hits, match clock) → debug channel.

Conventions:
- Shared helpers: `rand`, `randi`, `clamp`, `lerp`, `damp(k, dt)`, `angDiff`, `pick`, `V3` (THREE.Vector3), `tmp`/`tmp2` scratch vectors.
- Static scenery goes through `vis()/vbox()/vgeo()`, which batch it into one draw call per material. Colliders go through `solid()/proxy()`.
- Layers: anything built inside `layerBuild(L, fn)` (batches, colliders, proxies, lamps) belongs to layer `L`, and `setLayer(L, on)` shows or
  removes all of it. `AVE` holds the avenue-only barricades (off in Hunted); `CITY.layer` holds the city (on only in Hunted).
- Husks share one shader (`ghostMat`, a fresnel rim, rising bands, feet that fade out) but each has its own material instance so it can
  fade in when it rises and fade out when shot. Their kit is baked into vertex colours, one mesh per joint, and they cast no shadow.
- Enemy bullets (soldiers and husks) go through `shotAtPlayer(from, sigma)`. In `shoot()`, when the Veil is off a husk in front is
  skipped (`ghostRipple`) and the round carries on to whatever is behind it.
- Hunted's horrors path-find with a flow field: `navFlow()` runs a breadth-first search out from the player over a 2 m grid a few times a
  second, and `navDir()` tells a horror which neighbouring cell is closer to you.
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
climb, approach, audiotest, figD {D} (place the figure D metres away), hunt (switch to Hunted and start), horror {D,state,team} (bring a husk in
D metres ahead), rise (wake the body nearest you), bot {D} (a Hunted soldier D m ahead), botKill {i}, veil {have,on,kills,fit}, att {mag,barrel,optic,grip,muzzle,sx:{sniper,smg}}, radio {i} (stand at radio i), god {on} (take no damage), forget, pause, norender {on}, net {code,name,color},
aimNet {i,head}, netClock {t}, leaveNet. `test/run.py` and `test/run2.py` wrap this.

Testing tips:
- Serve `test/` over http (`python3 -m http.server 8765 --bind 127.0.0.1`). The page needs a UTF-8 charset, which `test/game.html` has.
- Hide the menu before screenshots: `["js", "document.getElementById('menu').style.display='none'"]`.
- In two-page tests, background tabs throttle requestAnimationFrame. Drive time with `sim` on each page alternately, with short `wait`s
  in between so BroadcastChannel messages get delivered, and keep `norender` on except for screenshots (run2.py does this).
- Night: `["tod", {"th": -1.0}]`. Figure: `["figD", {"D": 12}]` with NV on.

## Publishing
`dist/artifact.html` is what gets published to the artifact URL above. Keep the `room` capability when republishing.

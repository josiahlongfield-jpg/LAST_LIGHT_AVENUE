"""Build the game into single self-contained HTML files.

  python3 build.py

Reads src/game_template.html and inlines the three data files from data/:
  __GAME__    <- data/weapon_hd.json      (weapon models, arms, reload/anim metadata)
  __SOLDIER__ <- data/soldier_lp.json     (low-poly soldier model used for enemies and other players)
  __SOUNDS__  <- data/city_sounds_mp3.json (every sound, base64 MP3)

Writes:
  dist/last-light-avenue.html  - standalone page (double-click to play; three.js from cdnjs)
  dist/artifact.html           - same page without the <html>/<head> wrapper, for publishing as a claude.ai artifact
  test/game.html               - standalone page that loads test/three.min.js instead of the CDN (for offline headless tests)
"""
import os, re, subprocess, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
rd = lambda p: open(os.path.join(ROOT, p), encoding='utf-8').read()
t = rd('src/game_template.html')
page = t.replace('__GAME__', rd('data/weapon_hd.json')).replace('__SOLDIER__', rd('data/soldier_lp.json')).replace('__SOUNDS__', rd('data/city_sounds_mp3.json'))
head = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
open(os.path.join(ROOT, 'dist/artifact.html'), 'w', encoding='utf-8').write(page)
full = head + page + '\n</html>\n'
open(os.path.join(ROOT, 'dist/last-light-avenue.html'), 'w', encoding='utf-8').write(full)
open(os.path.join(ROOT, 'test/game.html'), 'w', encoding='utf-8').write(full.replace('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', 'three.min.js'))
# syntax check of the game script (data placeholders swapped for {} so it stays small)
js = re.findall(r'<script>(.*?)</script>', t, re.S)[0].replace('__GAME__', '{}').replace('__SOLDIER__', '{}').replace('__SOUNDS__', '{}')
os.makedirs(os.path.join(ROOT, 'test/out'), exist_ok=True)
open(os.path.join(ROOT, 'test/out/game.js'), 'w', encoding='utf-8').write(js)
try:
    r = subprocess.run(['node', '--check', os.path.join(ROOT, 'test/out/game.js')], capture_output=True, text=True)
    print('syntax:', 'ok' if r.returncode == 0 else r.stderr[:2000])
except FileNotFoundError:
    print('syntax: skipped (node not installed)')
print(round(len(full) / 1e6, 2), 'MB')

#!/usr/bin/env python3
"""Render tools-preview.png — the 1200x630 social/OG preview for cyberdeck.tools.

Not a screenshot of the site: it's a stylised CRT terminal "running" the deck —
a jack-in sequence, then `deck ls` printing the program list, which overflows
off the bottom of the screen. The program rows are read from the cards in
index.html (name, status, description), so re-running after adding/activating
a tool keeps the preview in sync.

How: builds a self-contained HTML page and screenshots it with headless
Chrome/Edge (fonts load from Google Fonts, so a network connection is needed).

Usage:
    python make_preview.py                # writes tools-preview.png
    python make_preview.py --html out.html  # also keep the HTML for tweaking
    python make_preview.py --seed 7       # different glitch characters

Browser lookup: $CHROME, then chrome/chromium/msedge on PATH, then the usual
install locations on Windows / macOS.
"""
import argparse
import html
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
OUT = ROOT / "tools-preview.png"
W, H = 1200, 630

KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン壊死無空虚断線電脳侵入錯誤"


# --------------------------------------------------------------------------- data

def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def read_cards():
    """Pull (kind, name, status, desc) for each tool card in index.html."""
    src = INDEX.read_text(encoding="utf-8")
    cards = []
    main = re.search(r'<main class="grid">(.*?)</main>', src, re.S).group(1)
    # Cards are <a>/<div> with nested <div>s, so split on each card opener
    # instead of trying to match balanced tags.
    for chunk in re.split(r'(?=<(?:a|div) class="card )', main)[1:]:
        kind, body = re.match(r'<\w+ class="card (\w+)', chunk).group(1), chunk
        get = lambda cls: strip_tags((re.search(rf'class="{cls}"[^>]*>(.*?)</div>', body, re.S) or [None, ""])[1])
        name = get("name").lstrip(">").strip().rstrip("_")
        desc = get("desc")
        desc = re.sub(r"^Cyberpunk\s+", "", desc).split(".")[0]
        cards.append((kind, name, desc))
    return cards


def glitch(text, rng, amount=0.3):
    return "".join(rng.choice(KATAKANA) if c not in " /" and rng.random() < amount else c for c in text)


def program_rows(rng):
    """Rows for the `deck ls` table — real cards first, then filler that
    overflows off the bottom of the screen."""
    rows = []
    for i, (kind, name, desc) in enumerate(read_cards(), 1):
        if kind == "live":
            status, cls = "ONLINE", "ok"
        elif kind == "corrupt":
            status, cls, name, desc = "ERR::0xDEAD", "err", glitch(name, rng), glitch(desc, rng, 0.35)
        else:
            status, cls = "COMPILING", "warn"
        rows.append((f"0x{i:02X}", name, status, cls, desc))
    n = len(rows)
    filler = [
        (glitch("UNKNOWN_SIG", rng, .4), "QUEUED", "warn", "awaiting decrypt ▓▓▓▓▓▓▓▓"),
        ("▓▓▓▓▓▓▓▓", "LOCKED", "dim", "black ice detected — access denied"),
        (glitch("DAEMON_", rng, .5), "QUEUED", "warn", "payload streaming ░░░░░░░░"),
        ("????????", "LOCKED", "dim", "signature unknown"),
        (glitch("SPECTRE", rng, .3), "QUEUED", "warn", "handshake pending ░░░░░░"),
        ("▓▓▓▓▓▓", "LOCKED", "dim", "corrupted sector"),
        (glitch("RELAY_7", rng, .4), "QUEUED", "warn", "unpacking ▓▓▓▓░░░░░░░░"),
        ("????????", "LOCKED", "dim", "signature unknown"),
        (glitch("WRAITH", rng, .5), "QUEUED", "warn", "decrypting ░░░░░░░░░░░░"),
    ]
    for j, (name, status, cls, desc) in enumerate(filler, n + 1):
        rows.append((f"0x{j:02X}", name, status, cls, desc))
    return rows, n


# --------------------------------------------------------------------------- page

def esc(s):
    return html.escape(s, quote=True)


def build_html(seed):
    rng = random.Random(seed)
    rows, real = program_rows(rng)
    online = sum(1 for r in rows[:real] if r[3] == "ok")

    def trunc(s, n):
        """Truncate to n terminal cells — katakana/kanji count as two."""
        out, used = "", 0
        for c in s:
            w = 2 if c in KATAKANA else 1
            if used + w > n:
                return out.rstrip() + "…"
            out, used = out + c, used + w
        return out

    table = "\n".join(
        f'<div class="row {cls}"><span class="pid">{pid}</span>'
        f'<span class="nm">{esc(trunc(name, 11))}</span>'
        f'<span class="st">{esc(status)}</span>'
        f'<span class="ds">{esc(trunc(desc, 30))}</span></div>'
        for pid, name, status, cls, desc in rows
    )

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Share+Tech+Mono&display=block" rel="stylesheet">
<style>
  :root {{
    --yellow:#fcee0a; --cyan:#00f0ff; --magenta:#ff003c;
    --bg:#050507; --panel:#0b0b10; --text:#e8e8ee; --dim:#7a7a88;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  html, body {{ width:{W}px; height:{H}px; overflow:hidden; }}
  body {{
    background:
      radial-gradient(ellipse at 20% 0%, rgba(252,238,10,.08), transparent 55%),
      radial-gradient(ellipse at 90% 100%, rgba(0,240,255,.08), transparent 55%),
      var(--bg);
    font-family:'JetBrains Mono', monospace;
    color:var(--text);
  }}

  /* ---- monitor shell ---- */
  .bezel {{
    position:absolute; inset:16px 22px 16px 22px;
    border-radius:30px;
    background:linear-gradient(160deg, #1b1b22 0%, #0d0d12 45%, #08080b 100%);
    box-shadow:
      0 0 0 2px #000,
      inset 0 2px 0 rgba(255,255,255,.06),
      inset 0 -3px 0 rgba(0,0,0,.6),
      0 0 60px rgba(0,240,255,.10);
  }}
  .bezel::after {{  /* maker strip under the glass */
    content:'CYBERDECK // CRT-2077'; position:absolute; left:50%; bottom:6px; transform:translateX(-50%);
    font-family:'Share Tech Mono', monospace; font-size:11px; letter-spacing:4px; color:#3a3a46;
  }}
  .led {{
    position:absolute; right:30px; bottom:10px; width:8px; height:8px; border-radius:50%;
    background:var(--cyan); box-shadow:0 0 8px var(--cyan), 0 0 18px var(--cyan);
  }}
  .screen {{
    position:absolute; inset:20px 22px 26px 22px;
    border-radius:38px / 30px;
    overflow:hidden;
    background:radial-gradient(ellipse at 50% 45%, #0b1418 0%, #060a0c 60%, #020304 100%);
    box-shadow:inset 0 0 0 2px #000, inset 0 0 90px rgba(0,0,0,.95);
    padding:26px 34px;
    display:grid; grid-template-columns:1fr 300px; gap:28px;
  }}
  /* CRT overlays: scanlines, rolling band, vignette, glass glare */
  .screen::before {{
    content:''; position:absolute; inset:0; pointer-events:none; z-index:5;
    background:
      repeating-linear-gradient(0deg, rgba(0,0,0,.28) 0 1px, transparent 1px 3px),
      linear-gradient(180deg, transparent 0 62%, rgba(0,240,255,.05) 62% 66%, transparent 66%);
  }}
  .screen::after {{
    content:''; position:absolute; inset:0; pointer-events:none; z-index:6; border-radius:inherit;
    background:
      radial-gradient(ellipse at 22% 12%, rgba(255,255,255,.07), transparent 38%),
      radial-gradient(ellipse at 50% 50%, transparent 58%, rgba(0,0,0,.75) 100%);
  }}

  /* ---- console ---- */
  .console {{ font-size:15.5px; line-height:1.5; min-width:0; text-shadow:0 0 6px rgba(0,240,255,.35); }}
  .logo {{
    font-family:'Share Tech Mono', monospace; font-size:56px; line-height:1; letter-spacing:4px;
    color:var(--yellow); white-space:nowrap;
    text-shadow:2px 0 var(--magenta), -2px 0 var(--cyan), 0 0 22px rgba(252,238,10,.45);
  }}
  .logo i {{ font-style:normal; color:var(--magenta); }}
  .tag {{ color:var(--dim); font-size:13px; letter-spacing:2px; text-transform:uppercase; margin:8px 0 14px; text-shadow:none; }}
  .ln {{ white-space:pre; color:#b9f8ff; }}
  .p  {{ color:var(--yellow); text-shadow:0 0 6px rgba(252,238,10,.5); }}
  .ok-tag {{ color:var(--cyan); }}
  .d  {{ color:var(--dim); text-shadow:none; }}
  .table {{ margin-top:2px; }}
  .row {{ display:grid; grid-template-columns:52px 128px 128px 1fr; white-space:nowrap; }}
  .row span {{ overflow:hidden; padding-right:10px; }}
  .row.hd {{ color:var(--dim); text-shadow:none; border-bottom:1px dashed rgba(122,122,136,.4); margin-bottom:2px; }}
  .row .pid {{ color:var(--dim); text-shadow:none; }}
  .row .ds {{ color:rgba(185,248,255,.6); }}
  .row.ok .nm {{ color:var(--yellow); text-shadow:0 0 6px rgba(252,238,10,.5); }}
  .row.ok .st {{ color:var(--cyan); }}
  .row.warn .nm {{ color:var(--cyan); }}
  .row.warn .st {{ color:var(--magenta); text-shadow:0 0 6px rgba(255,0,60,.5); }}
  .row.err {{ color:var(--magenta); text-shadow:2px 0 rgba(0,240,255,.5), -2px 0 rgba(252,238,10,.35); transform:translateX(3px); }}
  .row.err .ds {{ color:rgba(255,0,60,.7); }}
  .row.dim {{ opacity:.55; }}
  .row.dim .st {{ color:var(--magenta); }}

  /* ---- side panel ---- */
  .side {{ position:relative; z-index:1; padding-top:6px; }}
  .box {{
    position:relative; padding:16px 18px; margin-bottom:16px;
    background:rgba(0,240,255,.5);
    clip-path:polygon(14px 0,100% 0,100% calc(100% - 14px),calc(100% - 14px) 100%,0 100%,0 14px);
    font-size:13px; line-height:1.75;
    text-shadow:0 0 6px rgba(0,240,255,.3);
  }}
  .box::before {{
    content:''; position:absolute; inset:1.5px; background:#080b0e;
    clip-path:polygon(13.4px 0,100% 0,100% calc(100% - 13.4px),calc(100% - 13.4px) 100%,0 100%,0 13.4px);
  }}
  .box > * {{ position:relative; }}
  .box h3 {{
    font-family:'Share Tech Mono', monospace; font-weight:400; font-size:16px; letter-spacing:3px;
    color:var(--yellow); margin-bottom:8px;
  }}
  .kv {{ display:flex; justify-content:space-between; color:var(--dim); text-shadow:none; }}
  .kv b {{ font-weight:400; color:var(--cyan); text-shadow:0 0 6px rgba(0,240,255,.4); }}
  .kv b.m {{ color:var(--magenta); text-shadow:0 0 6px rgba(255,0,60,.5); }}
  .bar {{ height:8px; margin:3px 0 8px; background:rgba(0,240,255,.12); position:relative; }}
  .bar::after {{ content:''; position:absolute; inset:0; width:var(--v); background:repeating-linear-gradient(90deg, var(--cyan) 0 6px, transparent 6px 8px); box-shadow:0 0 8px rgba(0,240,255,.6); }}
  .bar.y::after {{ background:repeating-linear-gradient(90deg, var(--yellow) 0 6px, transparent 6px 8px); box-shadow:0 0 8px rgba(252,238,10,.6); }}
  .url {{
    font-family:'Share Tech Mono', monospace; font-size:22px; letter-spacing:2px; color:var(--cyan);
    text-shadow:0 0 10px rgba(0,240,255,.6); text-align:center; margin-top:4px;
  }}
  .url i {{ font-style:normal; color:var(--magenta); }}
  .cursor {{ display:inline-block; width:10px; height:18px; background:var(--yellow); vertical-align:-3px; box-shadow:0 0 8px var(--yellow); }}
</style></head>
<body>
  <div class="bezel"><div class="led"></div>
    <div class="screen">
      <div class="console">
        <div class="logo">&gt; CYBERDECK<i>.</i>TOOLS_</div>
        <div class="tag">// netrunner toolkit — cyberpunk / ttrpg browser programs</div>
        <div class="ln"><span class="p">runner@deck:~$</span> jack-in --target cyberdeck.tools</div>
        <div class="ln"><span class="ok-tag">[ ok ]</span> neural handshake <span class="d">..........</span> 12ms</div>
        <div class="ln"><span class="ok-tag">[ ok ]</span> ice countermeasures <span class="d">.......</span> bypassed</div>
        <div class="ln"><span class="p">runner@deck:~$</span> deck ls --programs --all</div>
        <div class="table">
          <div class="row hd"><span>PID</span><span>PROGRAM</span><span>STATUS</span><span>DESCRIPTION</span></div>
          {table}
        </div>
      </div>

      <div class="side">
        <div class="box">
          <h3>// DECK STATUS</h3>
          <div class="kv">programs loaded <b>{real:02d}</b></div>
          <div class="kv">online <b>{online:02d}</b></div>
          <div class="kv">signal integrity <b class="m">UNSTABLE</b></div>
          <div class="bar" style="--v:{round(online / max(real, 1) * 100)}%"></div>
          <div class="kv">ram <b>2077 MB</b></div>
          <div class="bar y" style="--v:68%"></div>
        </div>
        <div class="box">
          <h3>// RUNTIME</h3>
          <div class="kv">host <b>your browser</b></div>
          <div class="kv">backend <b>none</b></div>
          <div class="kv">build step <b>none</b></div>
          <div class="kv">export <b>PNG</b></div>
          <div class="kv">cost <b>0 €$</b></div>
        </div>
        <div class="url">cyberdeck<i>.</i>tools <span class="cursor"></span></div>
      </div>
    </div>
  </div>
</body></html>
"""


# --------------------------------------------------------------------------- render

def find_browser():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for name in ("chrome", "google-chrome", "chromium", "chromium-browser", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    for p in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ):
        if Path(p).exists():
            return p
    sys.exit("No Chrome/Edge found — set $CHROME to a Chromium-based browser.")


def render(page_html, out):
    browser = find_browser()
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "preview.html"
        src.write_text(page_html, encoding="utf-8")
        shot = Path(tmp) / "shot.png"
        subprocess.run([
            browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=1", f"--window-size={W},{H}",
            "--virtual-time-budget=8000",  # let Google Fonts arrive before the shot
            f"--user-data-dir={Path(tmp) / 'profile'}",
            f"--screenshot={shot}", src.as_uri(),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Headless may hand back a slightly different canvas — normalise to WxH.
        from PIL import Image
        img = Image.open(shot).convert("RGB")
        if img.size != (W, H):
            canvas = Image.new("RGB", (W, H), (5, 5, 7))
            canvas.paste(img.crop((0, 0, min(W, img.width), min(H, img.height))))
            img = canvas
        img.save(out, optimize=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT, help=f"output PNG (default: {OUT.name})")
    ap.add_argument("--html", type=Path, help="also write the generated HTML here")
    ap.add_argument("--seed", type=int, default=2077, help="seed for the glitch characters")
    args = ap.parse_args()

    page = build_html(args.seed)
    if args.html:
        args.html.write_text(page, encoding="utf-8")
    render(page, args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

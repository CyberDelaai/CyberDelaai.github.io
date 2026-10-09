#!/usr/bin/env python3
"""Render previews/og-<lang>.png — the 1200x630 social/OG previews for cyberdeck.tools,
one per hub language.

Not a screenshot of the site: it's a stylised CRT terminal "running" the deck —
a jack-in sequence, then `deck ls` printing the program list, which overflows
off the bottom of the screen. The program rows are read from the cards in
index.html (name, status, description) — for a language, from its generated
<lang>/index.html (run make_langs.py first), so the tagline and descriptions are
translated while the shell commands stay English. Re-run after adding /
activating a tool or changing the copy, then run make_langs.py again so every
page points at its image.

How: builds a self-contained HTML page and screenshots it with headless
Chrome/Edge (fonts load from Google Fonts, so a network connection is needed).

Usage:
    python make_preview.py                # all 8 languages -> previews/og-<lang>.png
    python make_preview.py ru ja          # just these
    python make_preview.py --html out.html  # also keep the (last) HTML for tweaking
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
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
OUT_DIR = ROOT / "previews"
LANGS = ["en", "ru", "fr", "de", "es", "it", "ja", "zh"]
W, H = 1200, 630

# Terminal copy per language: the STATUS column and the filler rows'
# descriptions (bars kept). Shell commands, headers and the side panel stay
# English, as a real terminal would.
STATUS = {
    "en": dict(online="ONLINE", compiling="COMPILING", queued="QUEUED", locked="LOCKED"),
    "ru": dict(online="ОНЛАЙН", compiling="КОМПИЛЯЦИЯ", queued="В ОЧЕРЕДИ", locked="ЗАКРЫТ"),
    "fr": dict(online="EN LIGNE", compiling="COMPILATION", queued="EN ATTENTE", locked="VERROUILLÉ"),
    "de": dict(online="ONLINE", compiling="KOMPILIERT", queued="WARTET", locked="GESPERRT"),
    "es": dict(online="EN LÍNEA", compiling="COMPILANDO", queued="EN COLA", locked="BLOQUEADO"),
    "it": dict(online="ONLINE", compiling="IN COMPILAZ.", queued="IN CODA", locked="BLOCCATO"),
    "ja": dict(online="オンライン", compiling="コンパイル中", queued="待機中", locked="ロック"),
    "zh": dict(online="在线", compiling="编译中", queued="排队中", locked="已锁定"),
}
FILLER = {  # one per filler row, in order
    "en": ["awaiting decrypt ▓▓▓▓▓▓▓▓", "black ice detected — access denied", "payload streaming ░░░░░░░░", "signature unknown",
           "handshake pending ░░░░░░", "corrupted sector", "unpacking ▓▓▓▓░░░░░░░░", "signature unknown", "decrypting ░░░░░░░░░░░░"],
    "ru": ["ожидает расшифровки ▓▓▓▓▓▓▓▓", "обнаружен чёрный лёд — доступ запрещён", "загрузка пейлоада ░░░░░░░░", "сигнатура неизвестна",
           "ожидание рукопожатия ░░░░░░", "повреждённый сектор", "распаковка ▓▓▓▓░░░░░░░░", "сигнатура неизвестна", "расшифровка ░░░░░░░░░░░░"],
    "fr": ["déchiffrement en attente ▓▓▓▓▓▓▓▓", "glace noire détectée — accès refusé", "transfert de charge ░░░░░░░░", "signature inconnue",
           "poignée de main en attente ░░░░░░", "secteur corrompu", "décompression ▓▓▓▓░░░░░░░░", "signature inconnue", "déchiffrement ░░░░░░░░░░░░"],
    "de": ["warte auf Entschlüsselung ▓▓▓▓▓▓▓▓", "Black ICE entdeckt — Zugriff verweigert", "Payload wird übertragen ░░░░░░░░", "Signatur unbekannt",
           "Handshake ausstehend ░░░░░░", "beschädigter Sektor", "entpacke ▓▓▓▓░░░░░░░░", "Signatur unbekannt", "entschlüssele ░░░░░░░░░░░░"],
    "es": ["esperando descifrado ▓▓▓▓▓▓▓▓", "hielo negro detectado — acceso denegado", "transmitiendo carga ░░░░░░░░", "firma desconocida",
           "saludo pendiente ░░░░░░", "sector corrupto", "desempaquetando ▓▓▓▓░░░░░░░░", "firma desconocida", "descifrando ░░░░░░░░░░░░"],
    "it": ["in attesa di decifratura ▓▓▓▓▓▓▓▓", "ghiaccio nero rilevato — accesso negato", "payload in trasmissione ░░░░░░░░", "firma sconosciuta",
           "handshake in attesa ░░░░░░", "settore corrotto", "estrazione ▓▓▓▓░░░░░░░░", "firma sconosciuta", "decifratura ░░░░░░░░░░░░"],
    "ja": ["復号待ち ▓▓▓▓▓▓▓▓", "ブラックICE検知 — アクセス拒否", "ペイロード転送中 ░░░░░░░░", "署名不明",
           "ハンドシェイク待機 ░░░░░░", "破損セクタ", "展開中 ▓▓▓▓░░░░░░░░", "署名不明", "復号中 ░░░░░░░░░░░░"],
    "zh": ["等待解密 ▓▓▓▓▓▓▓▓", "检测到黑冰 — 拒绝访问", "载荷传输中 ░░░░░░░░", "签名未知",
           "握手等待中 ░░░░░░", "扇区损坏", "解包中 ▓▓▓▓░░░░░░░░", "签名未知", "解密中 ░░░░░░░░░░░░"],
}

SIDE = {  # the DECK STATUS / RUNTIME panels (values like 2077 MB, PNG, 0 €$ stay)
    "en": dict(deck="// DECK STATUS", programs="programs loaded", online="online", signal="signal integrity", unstable="UNSTABLE", ram="ram",
               runtime="// RUNTIME", host="host", browser="your browser", backend="backend", none="none", build="build step", export="export", cost="cost"),
    "ru": dict(deck="// СТАТУС ДЕКИ", programs="загружено программ", online="в сети", signal="целостность сигнала", unstable="НЕСТАБИЛЬНО", ram="озу",
               runtime="// СРЕДА", host="хост", browser="ваш браузер", backend="бэкенд", none="нет", build="сборка", export="экспорт", cost="цена"),
    "fr": dict(deck="// ÉTAT DU DECK", programs="programmes chargés", online="en ligne", signal="intégrité du signal", unstable="INSTABLE", ram="ram",
               runtime="// EXÉCUTION", host="hôte", browser="votre navigateur", backend="backend", none="aucun", build="compilation", export="export", cost="coût"),
    "de": dict(deck="// DECK-STATUS", programs="Programme geladen", online="online", signal="Signalintegrität", unstable="INSTABIL", ram="RAM",
               runtime="// LAUFZEIT", host="Host", browser="dein Browser", backend="Backend", none="keins", build="Build-Schritt", export="Export", cost="Kosten"),
    "es": dict(deck="// ESTADO DEL DECK", programs="programas cargados", online="en línea", signal="integridad de señal", unstable="INESTABLE", ram="ram",
               runtime="// ENTORNO", host="host", browser="tu navegador", backend="backend", none="ninguno", build="compilación", export="exportación", cost="coste"),
    "it": dict(deck="// STATO DEL DECK", programs="programmi caricati", online="online", signal="integrità segnale", unstable="INSTABILE", ram="ram",
               runtime="// RUNTIME", host="host", browser="il tuo browser", backend="backend", none="nessuno", build="build", export="esportazione", cost="costo"),
    "ja": dict(deck="// デッキ状態", programs="ロード済み", online="オンライン", signal="信号強度", unstable="不安定", ram="RAM",
               runtime="// ランタイム", host="ホスト", browser="ブラウザ", backend="バックエンド", none="なし", build="ビルド", export="書き出し", cost="コスト"),
    "zh": dict(deck="// 终端状态", programs="已载入程序", online="在线", signal="信号完整性", unstable="不稳定", ram="内存",
               runtime="// 运行环境", host="主机", browser="你的浏览器", backend="后端", none="无", build="构建步骤", export="导出", cost="费用"),
}

KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン壊死無空虚断線電脳侵入錯誤"


# --------------------------------------------------------------------------- data

def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def page(lang):
    return INDEX if lang == "en" else ROOT / lang / "index.html"


def read_tagline(lang):
    m = re.search(r'<div class="tagline">(.*?)</div>', page(lang).read_text(encoding="utf-8"), re.S)
    return strip_tags(m.group(1)) if m else ""


def read_cards(lang):
    """Pull (kind, name, status, desc) for each tool card in the page."""
    src = page(lang).read_text(encoding="utf-8")
    cards = []
    main = re.search(r'<main class="grid">(.*?)</main>', src, re.S).group(1)
    # Cards are <a>/<div> with nested <div>s, so split on each card opener
    # instead of trying to match balanced tags.
    for chunk in re.split(r'(?=<(?:a|div) class="card )', main)[1:]:
        kind, body = re.match(r'<\w+ class="card (\w+)', chunk).group(1), chunk
        get = lambda cls: strip_tags((re.search(rf'class="{cls}"[^>]*>(.*?)</div>', body, re.S) or [None, ""])[1])
        name = get("name").lstrip(">").strip().rstrip("_")
        desc = get("desc")
        desc = re.split(r"[.。]", re.sub(r"^Cyberpunk\s+", "", desc))[0]
        cards.append((kind, name, desc))
    return cards


def glitch(text, rng, amount=0.3):
    return "".join(rng.choice(KATAKANA) if c not in " /" and rng.random() < amount else c for c in text)


def program_rows(rng, lang):
    """Rows for the `deck ls` table — real cards first, then filler that
    overflows off the bottom of the screen."""
    rows = []
    st, fd = STATUS[lang], FILLER[lang]
    for i, (kind, name, desc) in enumerate(read_cards(lang), 1):
        if kind == "live":
            status, cls = st["online"], "ok"
        elif kind == "corrupt":
            status, cls, name, desc = "ERR::0xDEAD", "err", glitch(name, rng), glitch(desc, rng, 0.35)
        else:
            status, cls = st["compiling"], "warn"
        rows.append((f"0x{i:02X}", name, status, cls, desc))
    n = len(rows)
    filler = [
        (glitch("UNKNOWN_SIG", rng, .4), st["queued"], "warn", fd[0]),
        ("▓▓▓▓▓▓▓▓", st["locked"], "dim", fd[1]),
        (glitch("DAEMON_", rng, .5), st["queued"], "warn", fd[2]),
        ("????????", st["locked"], "dim", fd[3]),
        (glitch("SPECTRE", rng, .3), st["queued"], "warn", fd[4]),
        ("▓▓▓▓▓▓", st["locked"], "dim", fd[5]),
        (glitch("RELAY_7", rng, .4), st["queued"], "warn", fd[6]),
        ("????????", st["locked"], "dim", fd[7]),
        (glitch("WRAITH", rng, .5), st["queued"], "warn", fd[8]),
    ]
    for j, (name, status, cls, desc) in enumerate(filler, n + 1):
        rows.append((f"0x{j:02X}", name, status, cls, desc))
    return rows, n


# --------------------------------------------------------------------------- page

def esc(s):
    return html.escape(s, quote=True)


def build_html(seed, lang="en"):
    rng = random.Random(seed)
    rows, real = program_rows(rng, lang)
    tagline = read_tagline(lang)
    sd = {k: esc(v) for k, v in SIDE[lang].items()}
    online = sum(1 for r in rows[:real] if r[3] == "ok")

    def trunc(s, n):
        """Truncate to n terminal cells — wide (CJK) characters count as two."""
        out, used = "", 0
        for c in s:
            w = 2 if unicodedata.east_asian_width(c) in "WF" else 1
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
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Share+Tech+Mono&family=Noto+Sans+JP:wght@400;700&family=Noto+Sans+SC:wght@400;700&display=block" rel="stylesheet">
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
    font-family:'JetBrains Mono', 'Noto Sans JP', monospace;
    color:var(--text);
  }}
  body.zh {{ font-family:'JetBrains Mono', 'Noto Sans SC', monospace; }}
  body.zh .box h3 {{ font-family:'Share Tech Mono', 'JetBrains Mono', 'Noto Sans SC', monospace; }}

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
    font-family:'Share Tech Mono', 'JetBrains Mono', 'Noto Sans JP', monospace; font-weight:400; font-size:16px; letter-spacing:3px;
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
<body class="{lang}">
  <div class="bezel"><div class="led"></div>
    <div class="screen">
      <div class="console">
        <div class="logo">&gt; CYBERDECK<i>.</i>TOOLS_</div>
        <div class="tag">{esc(tagline)}</div>
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
          <h3>{sd['deck']}</h3>
          <div class="kv">{sd['programs']} <b>{real:02d}</b></div>
          <div class="kv">{sd['online']} <b>{online:02d}</b></div>
          <div class="kv">{sd['signal']} <b class="m">{sd['unstable']}</b></div>
          <div class="bar" style="--v:{round(online / max(real, 1) * 100)}%"></div>
          <div class="kv">{sd['ram']} <b>2077 MB</b></div>
          <div class="bar y" style="--v:68%"></div>
        </div>
        <div class="box">
          <h3>{sd['runtime']}</h3>
          <div class="kv">{sd['host']} <b>{sd['browser']}</b></div>
          <div class="kv">{sd['backend']} <b>{sd['none']}</b></div>
          <div class="kv">{sd['build']} <b>{sd['none']}</b></div>
          <div class="kv">{sd['export']} <b>PNG</b></div>
          <div class="kv">{sd['cost']} <b>0 €$</b></div>
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
    ap.add_argument("langs", nargs="*", help="languages to render (default: all)")
    ap.add_argument("--html", type=Path, help="also write the generated HTML here")
    ap.add_argument("--seed", type=int, default=2077, help="seed for the glitch characters")
    args = ap.parse_args()
    bad = [l for l in args.langs if l not in LANGS]
    if bad:
        sys.exit(f"unknown language(s): {', '.join(bad)} — use {', '.join(LANGS)}")

    OUT_DIR.mkdir(exist_ok=True)
    for lang in args.langs or LANGS:
        if not page(lang).exists():
            print(f"skip {lang}: {lang}/index.html missing — run make_langs.py first")
            continue
        html_page = build_html(args.seed, lang)
        if args.html:
            args.html.write_text(html_page, encoding="utf-8")
        out = OUT_DIR / f"og-{lang}.png"
        render(html_page, out)
        print(f"wrote previews/{out.name}")


if __name__ == "__main__":
    main()

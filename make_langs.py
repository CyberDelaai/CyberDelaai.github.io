#!/usr/bin/env python3
"""Generate the per-language hub pages: ru/, fr/, de/, es/, it/, ja/, zh/.

The hub is a static page (no app code), so each language gets a fully
translated copy of index.html — every visible string swapped in from the
table below, which is the best case for search engines. Each copy also gets

  - <html lang> + data-url-lang (the language picker reads it)
  - its own canonical / og:url / og:locale, hreflang links, JSON-LD
  - tool cards linking to the same language's tool pages (/commlink-ui/ru/ …)
  - its own preview image, previews/og-<lang>.png (make_preview.py), when present
  - relative asset paths prefixed with ../

It also keeps the hreflang + og:locale blocks in index.html in sync and
rewrites the hub's own entries in sitemap.xml (the tools' make_langs.py manage
their own entries there).

index.html (English) is the only source: NEVER edit the generated folders.
Run it after any index.html change:

    python make_langs.py
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://cyberdeck.tools/"
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"

LANGS = ["en", "ru", "fr", "de", "es", "it", "ja", "zh"]
LOCALES = {"en": "en_US", "ru": "ru_RU", "fr": "fr_FR", "de": "de_DE",
           "es": "es_ES", "it": "it_IT", "ja": "ja_JP", "zh": "zh_CN"}
TOOLS = ["commlink-ui", "chronos-ui", "gridmap-ui", "eidolon-ui", "sinforge-ui"]

# Exact English source strings in index.html (each must occur once) — the
# keys of the translation table below.
EN = {
    "title": "CYBERDECK.TOOLS — Free Cyberpunk TTRPG Browser Tools",
    "desc": "Free cyberpunk / TTRPG browser tools for game masters: chat screenshot constructor, calendar maker, battle-map grid detector and token maker. PNG export.",
    "og_desc": "A deck of free cyberpunk / TTRPG browser tools — chat screenshots, calendars, battle-map grids, character tokens. Client-side, PNG export.",
    "alt": "A CRT terminal running the CYBERDECK.TOOLS netrunner toolkit, listing its cyberpunk / TTRPG programs and their status",
    "site_desc": "Free cyberpunk / TTRPG browser tools for game masters: chat screenshots, calendars, battle-map grids and character tokens. Client-side, PNG export.",
    "list_name": "CYBERDECK.TOOLS programs",
    "h1": "CYBERDECK.TOOLS — free cyberpunk TTRPG browser tools for game masters",
    "tagline": "// netrunner toolkit — load a program",
    "commlink": "Cyberpunk dialog / chat screenshot constructor. PNG export.",
    "chronos": "Cyberpunk calendar constructor. Different colors, PNG export.",
    "gridmap": "Cyberpunk battle-map grid detector. Reports NN×MM, PNG export.",
    "eidolon": "Cyberpunk token / avatar maker for TTRPG characters. Frames, badges, PNG export.",
    "sinforge": "Cyberpunk document constructor. ID cards, badges, keycards.",
    # the decorative NULL//SECTOR card: keep ▓▓▓▓ and the 0x…… address (its glitch script rewrites it)
    "corrupt": "Segment fault in ▓▓▓▓. Program image unreadable. Checksum mismatch at 0x7F3A.",
    "about1": """<strong>CYBERDECK.TOOLS</strong> is a deck of free browser tools for cyberpunk tabletop RPGs —
          Cyberpunk RED, Cyberpunk 2020, Shadowrun — and for any game master who wants in-world props
          without opening an image editor.""",
    "about2": """Everything runs locally in your browser: no signup, no upload, no install. Each program exports
          a clean PNG, ready for Roll20, Foundry VTT, Discord or print.""",
}

T = {
    "ru": {
        "title": "CYBERDECK.TOOLS — бесплатные киберпанк-инструменты для НРИ",
        "desc": "Бесплатные браузерные инструменты для мастеров НРИ в стиле киберпанк: скриншоты переписки, календари, сетка боевых карт и токены. Экспорт PNG.",
        "og_desc": "Сборка бесплатных браузерных инструментов для киберпанк-НРИ: скриншоты переписки, календари, сетка боевых карт, токены персонажей. Экспорт PNG.",
        "alt": "CRT-терминал с запущенным набором нетраннера CYBERDECK.TOOLS: список киберпанк-программ для НРИ и их статус",
        "list_name": "Программы CYBERDECK.TOOLS",
        "h1": "CYBERDECK.TOOLS — бесплатные киберпанк-инструменты для мастеров НРИ",
        "tagline": "// набор нетраннера — загрузи программу",
        "commlink": "Конструктор киберпанк-диалогов и скриншотов чата. Экспорт PNG.",
        "chronos": "Конструктор киберпанк-календарей. Разные цвета, экспорт PNG.",
        "gridmap": "Определение сетки на боевых картах. Показывает NN×MM, экспорт PNG.",
        "eidolon": "Конструктор токенов и аватаров персонажей НРИ. Рамки, значки, экспорт PNG.",
        "sinforge": "Конструктор киберпанк-документов. Удостоверения, бейджи, ключ-карты.",
        "corrupt": "Ошибка сегментации в ▓▓▓▓. Образ программы не читается. Несовпадение контрольной суммы в 0x7F3A.",
        "about1": "<strong>CYBERDECK.TOOLS</strong> — сборка бесплатных браузерных инструментов для киберпанк-НРИ — Cyberpunk RED, Cyberpunk 2020, Shadowrun — и для любого мастера, которому нужен игровой реквизит без графического редактора.",
        "about2": "Всё работает прямо в браузере: без регистрации, загрузки и установки. Каждая программа сохраняет чистый PNG — для Roll20, Foundry VTT, Discord или печати.",
    },
    "fr": {
        "title": "CYBERDECK.TOOLS — Outils cyberpunk gratuits pour le JDR",
        "desc": "Outils de navigateur gratuits pour MJ de JDR cyberpunk : captures de chat, calendriers, détection de grille de cartes de combat et jetons. Export PNG.",
        "og_desc": "Un deck d'outils de navigateur gratuits pour le JDR cyberpunk : captures de chat, calendriers, grilles de cartes de combat, jetons de personnage. Export PNG.",
        "alt": "Un terminal CRT qui exécute la boîte à outils du netrunner CYBERDECK.TOOLS et liste ses programmes cyberpunk / JDR",
        "list_name": "Programmes CYBERDECK.TOOLS",
        "h1": "CYBERDECK.TOOLS — outils cyberpunk gratuits pour les MJ de JDR",
        "tagline": "// boîte à outils du netrunner — charge un programme",
        "commlink": "Constructeur de dialogues et captures de chat cyberpunk. Export PNG.",
        "chronos": "Constructeur de calendriers cyberpunk. Plusieurs couleurs, export PNG.",
        "gridmap": "Détecteur de grille de cartes de combat. Affiche NN×MM, export PNG.",
        "eidolon": "Créateur de jetons et d'avatars pour personnages de JDR. Cadres, badges, export PNG.",
        "sinforge": "Constructeur de documents cyberpunk. Cartes d'identité, badges, cartes d'accès.",
        "corrupt": "Erreur de segmentation dans ▓▓▓▓. Image du programme illisible. Somme de contrôle invalide à 0x7F3A.",
        "about1": "<strong>CYBERDECK.TOOLS</strong> est un deck d'outils de navigateur gratuits pour les JDR cyberpunk — Cyberpunk RED, Cyberpunk 2020, Shadowrun — et pour tout MJ qui veut des accessoires de jeu sans ouvrir un logiciel de retouche.",
        "about2": "Tout fonctionne dans votre navigateur : sans inscription, sans envoi, sans installation. Chaque programme exporte un PNG propre, prêt pour Roll20, Foundry VTT, Discord ou l'impression.",
    },
    "de": {
        "title": "CYBERDECK.TOOLS — Kostenlose Cyberpunk-Rollenspiel-Tools",
        "desc": "Kostenlose Browser-Tools für Cyberpunk-Spielleiter: Chat-Screenshots, Kalender, Battlemap-Raster-Erkennung und Token-Ersteller. PNG-Export.",
        "og_desc": "Ein Deck kostenloser Browser-Tools für Cyberpunk-Rollenspiele: Chat-Screenshots, Kalender, Battlemap-Raster, Charakter-Tokens. Läuft im Browser, PNG-Export.",
        "alt": "Ein CRT-Terminal mit dem Netrunner-Toolkit CYBERDECK.TOOLS, das seine Cyberpunk- und Rollenspiel-Programme und ihren Status auflistet",
        "list_name": "CYBERDECK.TOOLS-Programme",
        "h1": "CYBERDECK.TOOLS — kostenlose Cyberpunk-Tools für Spielleiter",
        "tagline": "// Netrunner-Toolkit — lade ein Programm",
        "commlink": "Cyberpunk-Dialog- und Chat-Screenshot-Konstruktor. PNG-Export.",
        "chronos": "Cyberpunk-Kalender-Konstruktor. Verschiedene Farben, PNG-Export.",
        "gridmap": "Battlemap-Raster-Erkennung. Zeigt NN×MM, PNG-Export.",
        "eidolon": "Token- und Avatar-Ersteller für Rollenspiel-Charaktere. Rahmen, Abzeichen, PNG-Export.",
        "sinforge": "Cyberpunk-Dokument-Konstruktor. Ausweise, Badges, Keycards.",
        "corrupt": "Speicherzugriffsfehler in ▓▓▓▓. Programmabbild unlesbar. Prüfsummenfehler bei 0x7F3A.",
        "about1": "<strong>CYBERDECK.TOOLS</strong> ist ein Deck kostenloser Browser-Tools für Cyberpunk-Rollenspiele — Cyberpunk RED, Cyberpunk 2020, Shadowrun — und für alle Spielleiter, die Requisiten ohne Bildbearbeitung wollen.",
        "about2": "Alles läuft lokal im Browser: keine Anmeldung, kein Upload, keine Installation. Jedes Programm exportiert ein sauberes PNG für Roll20, Foundry VTT, Discord oder den Druck.",
    },
    "es": {
        "title": "CYBERDECK.TOOLS — Herramientas cyberpunk gratis para rol",
        "desc": "Herramientas de navegador gratuitas para másteres de rol cyberpunk: capturas de chat, calendarios, cuadrículas de mapas y tokens. Exportación PNG.",
        "og_desc": "Un mazo de herramientas de navegador gratuitas para rol cyberpunk: capturas de chat, calendarios, cuadrículas de mapas de batalla y tokens. Exportación PNG.",
        "alt": "Un terminal CRT que ejecuta el kit del netrunner CYBERDECK.TOOLS y lista sus programas cyberpunk / de rol",
        "list_name": "Programas de CYBERDECK.TOOLS",
        "h1": "CYBERDECK.TOOLS — herramientas cyberpunk gratuitas para másteres de rol",
        "tagline": "// kit del netrunner — carga un programa",
        "commlink": "Constructor de diálogos y capturas de chat cyberpunk. Exportación PNG.",
        "chronos": "Constructor de calendarios cyberpunk. Varios colores, exportación PNG.",
        "gridmap": "Detector de cuadrícula de mapas de batalla. Muestra NN×MM, exportación PNG.",
        "eidolon": "Creador de tokens y avatares para personajes de rol. Marcos, insignias, exportación PNG.",
        "sinforge": "Constructor de documentos cyberpunk. Carnés, acreditaciones, tarjetas de acceso.",
        "corrupt": "Fallo de segmentación en ▓▓▓▓. Imagen del programa ilegible. Suma de verificación errónea en 0x7F3A.",
        "about1": "<strong>CYBERDECK.TOOLS</strong> es un mazo de herramientas de navegador gratuitas para rol cyberpunk — Cyberpunk RED, Cyberpunk 2020, Shadowrun — y para cualquier máster que quiera atrezo de partida sin abrir un editor de imágenes.",
        "about2": "Todo funciona en tu navegador: sin registro, sin subidas, sin instalación. Cada programa exporta un PNG limpio, listo para Roll20, Foundry VTT, Discord o imprimir.",
    },
    "it": {
        "title": "CYBERDECK.TOOLS — Strumenti cyberpunk gratuiti per GDR",
        "desc": "Strumenti gratuiti nel browser per master di GDR cyberpunk: screenshot di chat, calendari, griglie per mappe di battaglia e token. Esportazione PNG.",
        "og_desc": "Un mazzo di strumenti gratuiti nel browser per GDR cyberpunk: screenshot di chat, calendari, griglie di mappe di battaglia, token. Esportazione PNG.",
        "alt": "Un terminale CRT che esegue il toolkit del netrunner CYBERDECK.TOOLS ed elenca i suoi programmi cyberpunk / GDR",
        "list_name": "Programmi di CYBERDECK.TOOLS",
        "h1": "CYBERDECK.TOOLS — strumenti cyberpunk gratuiti per master di GDR",
        "tagline": "// toolkit del netrunner — carica un programma",
        "commlink": "Costruttore di dialoghi e screenshot di chat cyberpunk. Esportazione PNG.",
        "chronos": "Costruttore di calendari cyberpunk. Colori diversi, esportazione PNG.",
        "gridmap": "Rilevatore di griglia per mappe di battaglia. Mostra NN×MM, esportazione PNG.",
        "eidolon": "Creatore di token e avatar per personaggi di GDR. Cornici, badge, esportazione PNG.",
        "sinforge": "Costruttore di documenti cyberpunk. Carte d'identità, pass, keycard.",
        "corrupt": "Errore di segmentazione in ▓▓▓▓. Immagine del programma illeggibile. Checksum non valido a 0x7F3A.",
        "about1": "<strong>CYBERDECK.TOOLS</strong> è un mazzo di strumenti gratuiti nel browser per GDR cyberpunk — Cyberpunk RED, Cyberpunk 2020, Shadowrun — e per ogni master che vuole oggetti di scena senza aprire un editor di immagini.",
        "about2": "Tutto gira nel tuo browser: niente registrazione, niente caricamenti, niente installazione. Ogni programma esporta un PNG pulito, pronto per Roll20, Foundry VTT, Discord o la stampa.",
    },
    "ja": {
        "title": "CYBERDECK.TOOLS — 無料のサイバーパンクTRPGツール集",
        "desc": "サイバーパンクTRPGのGM向け無料ブラウザツール集：チャットスクリーンショット、カレンダー、戦闘マップのグリッド検出、トークン作成。PNG書き出し対応。",
        "og_desc": "サイバーパンクTRPG向けの無料ブラウザツール集。チャット画像、カレンダー、戦闘マップのグリッド、キャラクタートークン。ブラウザ完結、PNG書き出し。",
        "alt": "CYBERDECK.TOOLSのネットランナー・ツールキットを実行するCRT端末。サイバーパンクTRPG用プログラムとその状態の一覧",
        "list_name": "CYBERDECK.TOOLSのプログラム",
        "h1": "CYBERDECK.TOOLS — GM向け無料サイバーパンクTRPGツール集",
        "tagline": "// ネットランナー・ツールキット — プログラムをロード",
        "commlink": "サイバーパンク風の会話・チャット画面メーカー。PNG書き出し。",
        "chronos": "サイバーパンク風カレンダーメーカー。多彩なカラー、PNG書き出し。",
        "gridmap": "戦闘マップのグリッド検出。NN×MMを表示、PNG書き出し。",
        "eidolon": "TRPGキャラクターのトークン・アバターメーカー。フレーム、バッジ、PNG書き出し。",
        "sinforge": "サイバーパンク風書類メーカー。IDカード、バッジ、キーカード。",
        "corrupt": "▓▓▓▓でセグメンテーション違反。プログラムイメージを読み取れません。0x7F3Aでチェックサム不一致。",
        "about1": "<strong>CYBERDECK.TOOLS</strong>は、サイバーパンクTRPG（Cyberpunk RED、Cyberpunk 2020、Shadowrun）や、画像編集ソフトを使わずに世界観のある小道具を作りたいすべてのGMのための無料ブラウザツール集です。",
        "about2": "すべてブラウザ内で動作し、登録・アップロード・インストールは不要。各プログラムはRoll20、Foundry VTT、Discord、印刷にそのまま使えるPNGを書き出します。",
    },
    "zh": {
        "title": "CYBERDECK.TOOLS — 免费赛博朋克跑团工具集",
        "desc": "面向赛博朋克跑团主持人的免费浏览器工具：聊天截图、日历、战斗地图网格检测和令牌制作，均可导出 PNG。",
        "og_desc": "一套免费的赛博朋克跑团浏览器工具：聊天截图、日历、战斗地图网格、角色令牌。全部在浏览器中运行，导出 PNG。",
        "alt": "运行 CYBERDECK.TOOLS 网络行者工具包的 CRT 终端，列出其赛博朋克跑团程序及状态",
        "list_name": "CYBERDECK.TOOLS 程序",
        "h1": "CYBERDECK.TOOLS — 面向主持人的免费赛博朋克跑团工具",
        "tagline": "// 网络行者工具包 — 载入程序",
        "commlink": "赛博朋克对话与聊天截图构造器。导出 PNG。",
        "chronos": "赛博朋克日历构造器。多种配色，导出 PNG。",
        "gridmap": "战斗地图网格检测器。显示 NN×MM，导出 PNG。",
        "eidolon": "跑团角色令牌与头像制作器。边框、徽标，导出 PNG。",
        "sinforge": "赛博朋克证件构造器。身份证、胸牌、门禁卡。",
        "corrupt": "▓▓▓▓ 段错误。程序映像无法读取。0x7F3A 处校验和不匹配。",
        "about1": "<strong>CYBERDECK.TOOLS</strong> 是一套免费的浏览器工具，面向赛博朋克跑团——《赛博朋克 RED》《赛博朋克 2020》《暗影狂奔》——以及所有想不用修图软件就做出游戏道具的主持人。",
        "about2": "一切都在你的浏览器本地运行：无需注册、无需上传、无需安装。每个程序都能导出干净的 PNG，可直接用于 Roll20、Foundry VTT、Discord 或打印。",
    },
}

# JSON-LD ItemList names: each tool's own localized og:title (its make_langs.py SEO table)
TOOL_NAMES = {
    "commlink-ui": {"ru": "COMMLINK — конструктор киберпанк-диалогов", "fr": "COMMLINK — Constructeur de dialogues cyberpunk", "de": "COMMLINK — Cyberpunk-Dialog-Konstruktor", "es": "COMMLINK — Constructor de diálogos cyberpunk", "it": "COMMLINK — Costruttore di dialoghi cyberpunk", "ja": "COMMLINK — サイバーパンク会話コンストラクター", "zh": "COMMLINK — 赛博朋克对话构造器"},
    "chronos-ui": {"ru": "CHRONOS — конструктор киберпанк-календарей", "fr": "CHRONOS — Constructeur de calendrier cyberpunk", "de": "CHRONOS — Cyberpunk-Kalender-Konstruktor", "es": "CHRONOS — Constructor de calendarios cyberpunk", "it": "CHRONOS — Costruttore di calendari cyberpunk", "ja": "CHRONOS — サイバーパンク風カレンダーメーカー", "zh": "CHRONOS — 赛博朋克日历生成器"},
    "gridmap-ui": {"ru": "GRIDMAP — детектор сетки боевых карт", "fr": "GRIDMAP — Détecteur de grille de carte de combat", "de": "GRIDMAP — Battlemap-Raster-Erkennung", "es": "GRIDMAP — Detector de cuadrícula de mapas de batalla", "it": "GRIDMAP — Rilevatore di griglia per mappe di battaglia", "ja": "GRIDMAP — 戦闘マップのグリッド検出", "zh": "GRIDMAP — 战斗地图网格检测器"},
    "eidolon-ui": {"ru": "EIDOLON — конструктор киберпанк-токенов", "fr": "EIDOLON — Créateur de jetons JDR cyberpunk", "de": "EIDOLON — Cyberpunk-Token-Ersteller", "es": "EIDOLON — Creador de tokens cyberpunk", "it": "EIDOLON — Creatore di token cyberpunk", "ja": "EIDOLON — サイバーパンク風トークンメーカー", "zh": "EIDOLON — 赛博朋克令牌制作器"},
}

HREFLANG_START = "<!-- hreflang: generated by make_langs.py -->"
HREFLANG_END = "<!-- /hreflang -->"
GENERATED = "<!-- GENERATED by make_langs.py from ../index.html — edit index.html, then re-run -->"


def url(lang):
    return BASE if lang == "en" else f"{BASE}{lang}/"


def esc(s):
    return html.escape(s, quote=True)


def sub1(text, pattern, repl, what):
    text, n = re.subn(pattern, repl, text, count=1)
    if n != 1:
        sys.exit(f"error: {what} not found in index.html")
    return text


def set_meta(text, attr, name, value):
    return sub1(text, rf'(<meta {attr}="{re.escape(name)}" content=")[^"]*(" />)',
                lambda m: m.group(1) + esc(value) + m.group(2), f"{attr}={name}")


def swap(text, old, new, what):
    if text.count(old) != 1:
        sys.exit(f"error: {what}: expected exactly one {old[:50]!r} in index.html")
    return text.replace(old, new)


def head_blocks(text, lang):
    """hreflang links (after canonical) + og:locale block (after og:url)."""
    links = [f'<link rel="alternate" hreflang="{l}" href="{url(l)}" />' for l in LANGS]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}" />')
    block = "\n".join([HREFLANG_START, *links, HREFLANG_END])
    if HREFLANG_START in text:
        text = re.sub(re.escape(HREFLANG_START) + r".*?" + re.escape(HREFLANG_END), lambda m: block, text, flags=re.S)
    else:
        text = sub1(text, r'(<link rel="canonical" href="[^"]*" />\n)', lambda m: m.group(1) + block + "\n", "canonical")
    locales = [f'<meta property="og:locale" content="{LOCALES[lang]}" />'] + [
        f'<meta property="og:locale:alternate" content="{LOCALES[l]}" />' for l in LANGS if l != lang]
    loc = re.compile(r'<meta property="og:locale" content="[^"]*" />\n(?:<meta property="og:locale:alternate" content="[^"]*" />\n)*')
    if loc.search(text):
        return loc.sub(lambda m: "\n".join(locales) + "\n", text, count=1)
    return sub1(text, r'(<meta property="og:url" content="[^"]*" />\n)', lambda m: m.group(1) + "\n".join(locales) + "\n", "og:url")


def with_preview(text, lang):
    if not (ROOT / "previews" / f"og-{lang}.png").exists():
        return text
    img = f"{BASE}previews/og-{lang}.png"
    text = set_meta(text, "property", "og:image", img)
    return set_meta(text, "name", "twitter:image", img)


def prefix_paths(text):
    """../ before relative src / href attributes (favicons etc.); inside a
    <script> block only the opening tag is touched."""
    rel = re.compile(r'(\s(?:src|href)=")(?!https?:|data:|#|/|mailto:|javascript:|\.\./)([^"]+")')

    def fix(part):
        if not part.startswith("<script"):
            return rel.sub(r"\1../\2", part)
        tag_end = part.index(">") + 1
        return rel.sub(r"\1../\2", part[:tag_end]) + part[tag_end:]

    return "".join(fix(p) for p in re.split(r"(<script\b.*?</script>)", text, flags=re.S))


def localize(src, lang):
    t, s = T[lang], src
    s = sub1(s, r"<!DOCTYPE html>\n", "<!DOCTYPE html>\n" + GENERATED + "\n", "doctype")
    s = swap(s, '<html lang="en">', f'<html lang="{lang}" data-url-lang="{lang}">', "<html>")
    s = swap(s, f"<title>{EN['title']}</title>", f"<title>{esc(t['title'])}</title>", "title")
    s = set_meta(s, "name", "description", t["desc"])
    for prop in ("og:description",):
        s = set_meta(s, "property", prop, t["og_desc"])
    s = set_meta(s, "name", "twitter:description", t["og_desc"])
    s = set_meta(s, "property", "og:image:alt", t["alt"])
    s = set_meta(s, "name", "twitter:image:alt", t["alt"])
    s = set_meta(s, "property", "og:url", url(lang))
    s = sub1(s, r'(<link rel="canonical" href=")[^"]*(" />)', lambda m: m.group(1) + url(lang) + m.group(2), "canonical")
    # JSON-LD: the site in this language, the tool list pointing at its language pages
    s = swap(s, f'"url": "{BASE}",', f'"url": "{url(lang)}",', 'JSON-LD WebSite "url"')
    s = swap(s, f'"description": "{EN["site_desc"]}"', f'"description": "{t["desc"]}"', "JSON-LD description")
    s = swap(s, '"inLanguage": "en"', f'"inLanguage": "{lang}"', "JSON-LD inLanguage")
    s = swap(s, f'"name": "{EN["list_name"]}"', f'"name": "{t["list_name"]}"', "JSON-LD list name")
    for tool, names in TOOL_NAMES.items():
        s = sub1(s, rf'"name": "[^"]*", "url": "{re.escape(BASE + tool)}/"',
                 lambda m, n=names[lang], tl=tool: f'"name": "{n}", "url": "{BASE}{tl}/{lang}/"', f"JSON-LD {tool}")
    # visible copy
    s = swap(s, f'<h1 class="sr-only">{EN["h1"]}</h1>', f'<h1 class="sr-only">{esc(t["h1"])}</h1>', "h1")
    s = swap(s, f'<div class="tagline">{EN["tagline"]}</div>', f'<div class="tagline">{esc(t["tagline"])}</div>', "tagline")
    for key in ("commlink", "chronos", "gridmap", "eidolon", "sinforge"):
        s = swap(s, f'<div class="desc">{EN[key]}</div>', f'<div class="desc">{esc(t[key])}</div>', f"{key} card")
    s = swap(s, f'<div class="desc" data-glitch>{EN["corrupt"]}</div>', f'<div class="desc" data-glitch>{esc(t["corrupt"])}</div>', "NULL//SECTOR card")
    s = swap(s, f"<p>{EN['about1']}</p>", f"<p>{t['about1']}</p>", "about 1")
    s = swap(s, f"<p>{EN['about2']}</p>", f"<p>{esc(t['about2'])}</p>", "about 2")
    # tool cards -> the same language's tool pages
    for tool in TOOLS:
        s = swap(s, f'href="/{tool}/"', f'href="/{tool}/{lang}/"', f"{tool} card link")
    s = with_preview(head_blocks(s, lang), lang)
    return prefix_paths(s)


def url_entries(lastmod):
    alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{url(l)}" />' for l in LANGS)
    alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}" />'
    return "".join(
        f"  <url>\n    <loc>{url(l)}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>weekly</changefreq>\n"
        f"    <priority>{'1.0' if l == 'en' else '0.9'}</priority>{alts}\n  </url>\n" for l in LANGS)


def update_sitemap(lastmod):
    text = SITEMAP.read_text(encoding="utf-8")
    mine = {url(l) for l in LANGS}
    blocks = [b for b in re.finditer(r"  <url>\n.*?\n  </url>\n", text, flags=re.S)
              if re.search(r"<loc>([^<]+)</loc>", b.group(0)).group(1) in mine]
    if not blocks:
        sys.exit("error: hub entry not found in sitemap.xml")
    out, pos = [], 0
    for i, b in enumerate(blocks):
        out.append(text[pos:b.start()])
        if i == 0:
            out.append(url_entries(lastmod))
        pos = b.end()
    out.append(text[pos:])
    text = re.sub(r"<urlset[^>]*>", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">', "".join(out), count=1)
    SITEMAP.write_text(text, encoding="utf-8")


def main():
    for lang, t in T.items():
        for k, limit in (("title", 60), ("desc", 165)):
            if len(t[k]) > limit:
                print(f"warning: {lang} {k} is {len(t[k])} chars (> {limit})")
    src = with_preview(head_blocks(INDEX.read_text(encoding="utf-8"), "en"), "en")
    INDEX.write_text(src, encoding="utf-8")
    for lang in LANGS[1:]:
        out = ROOT / lang / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(localize(src, lang), encoding="utf-8")
    lastmod = __import__("datetime").date.today().isoformat()
    update_sitemap(lastmod)
    print(f"langs: wrote {', '.join(l + '/' for l in LANGS[1:])} (lastmod {lastmod})")


if __name__ == "__main__":
    main()

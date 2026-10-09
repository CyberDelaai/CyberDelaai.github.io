# CYBERDECK.TOOLS — Netrunner Toolkit

The landing page for [cyberdeck.tools](https://cyberdeck.tools/) — a deck of cyberpunk / TTRPG browser tools. A single static `index.html` (markup + inline CSS) served via GitHub Pages. No backend, no build step.

## The deck

| Tool | Status | Description |
| --- | --- | --- |
| **COMMLINK** | online | Cyberpunk dialog / chat screenshot constructor. PNG export. → [`/commlink-ui/`](https://cyberdeck.tools/commlink-ui/) |
| **CHRONOS** | online | Cyberpunk calendar constructor. Different colors, PNG export. → [`/chronos-ui/`](https://cyberdeck.tools/chronos-ui/) |
| **GRIDMAP** | online | Cyberpunk battle-map grid detector. Reports NN×MM, PNG export. → [`/gridmap-ui/`](https://cyberdeck.tools/gridmap-ui/) |
| **EIDOLON** | online | Cyberpunk token / avatar maker for TTRPG characters. Frames, badges, PNG export. → [`/eidolon-ui/`](https://cyberdeck.tools/eidolon-ui/) |
| **SINFORGE** | alpha (hidden) | Cyberpunk document constructor. ID cards, badges, keycards. → [`/sinforge-ui/`](https://cyberdeck.tools/sinforge-ui/) |

Live cards link out to the deployed tool; `compiling…` cards are placeholders for tools not yet shipped. Alpha tools (< 1.0.0) are deployed but hide behind a `compiling…` card — see below.

## Alpha tools (< 1.0.0)

A tool that's deployed but still below `1.0.0` gets a **hidden alpha card**: it looks like `compiling…`, but it's a real link.

- **Clicks 1–2** glitch the card for ~0.5 s (`.waking`) and flash `▸ alpha build // online` — a hint that it's actually alive.
- **Click 3** saves `cyberdeck:unlocked:<key>` in `localStorage` and opens the tool.
- **Later visits** (same browser): the card renders as live, with a yellow `▸ online [alpha] _` status.
- Ctrl / Shift / Cmd / middle clicks open the link straight away without counting; `prefers-reduced-motion` skips the jitter but keeps the counter.

To hide a new pre-1.0 tool this way, write its card as an `<a>` with class `soon` and a `data-unlock` key — the script at the bottom of `index.html` picks up every `[data-unlock]` card, no JS changes needed:
```html
<a class="card soon" href="/<tool>-ui/" data-unlock="<tool>" data-augmented-ui="tl-clip br-clip border">
  <div class="name">&gt; TOOLNAME_</div>
  <div class="desc">One-line description.</div>
  <div class="status">▸ compiling…</div>
</a>
```
Keep it out of `sitemap.xml`, the JSON-LD `ItemList` and the meta descriptions while it's hidden, and set its README row to `alpha (hidden)` with the link. `make_preview.py` still lists it as `COMPILING`.

**At 1.0.0**, make it a normal live card: `class="card live"`, drop `data-unlock`, status `▸ online <span class="blink">_</span>`; then add it to the sitemap / JSON-LD / descriptions, set the README row to `online`, and regenerate the preview. (Leftover `cyberdeck:unlocked:<key>` entries in visitors' browsers are harmless.)

## Running it

Just open the file:
```
xdg-open index.html          # Linux
open index.html              # macOS
start index.html             # Windows
```

No server needed — augmented-ui and the fonts load from CDN.

## Social preview

`tools-preview.png` (the 1200×630 `og:image` / `twitter:image`) is generated, not screenshotted: a CRT terminal running `deck ls`, with the program list overflowing off-screen. The rows are read from the cards in `index.html`, so regenerate after adding or activating a tool:
```
python make_preview.py
```
Needs Python 3 + Pillow and a Chromium-based browser (Chrome/Edge, or set `$CHROME`); fonts come from Google Fonts, so it needs a network connection. `--html out.html` keeps the generated page for tweaking, `--seed N` reshuffles the glitch characters.

## Deployment

Served from the `CyberDelaai/CyberDelaai.github.io` repo via GitHub Pages, with the `cyberdeck.tools` apex domain set in `CNAME`. The sibling tools (`commlink-ui`, `chronos-ui`, …) live at their own paths under the same domain.

## Style notes

- **Fonts**: Share Tech Mono (console-style logo + tool names) and JetBrains Mono (body), loaded from Google Fonts.
- **Clipped corners**: [augmented-ui v2](https://augmented-ui.com) (CDN) shapes the tool cards (`tl-clip br-clip border`) and the donate button.
- **Scanlines**: a fixed full-viewport `body::before` overlay (`z-index: 9999`, `pointer-events: none`) tints the whole page like a CRT.
- **Status alignment**: cards are flex columns; the `▸ online _` line uses `margin-top: auto` so it pins to the bottom of every card regardless of description length. Only the `_` after `online` blinks.
- **Donate button**: a fixed bottom-right "ghost" link. Invisible by default, occasionally flickers into view (`donateGhost` loop); on hover/focus it materializes through a short heavy glitch burst (`donateGlitchIn`) and stays solid. Falls back to a dim static button for touch devices and `prefers-reduced-motion`.

## Support

If you find these tools useful, you can support development here: [boosty.to/cyberdelaai/donate](https://boosty.to/cyberdelaai/donate)

## License

[MIT](LICENSE) © 2026 CyberDelaai

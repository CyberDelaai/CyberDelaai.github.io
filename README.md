# CYBERDECK.TOOLS — Netrunner Toolkit

The landing page for [cyberdeck.tools](https://cyberdeck.tools/) — a deck of cyberpunk / TTRPG browser tools. A single static `index.html` (markup + inline CSS) served via GitHub Pages. No backend, no build step.

## The deck

| Tool | Status | Description |
| --- | --- | --- |
| **COMMLINK** | online | Cyberpunk dialog / chat screenshot constructor. PNG export. → [`/commlink-ui/`](https://cyberdeck.tools/commlink-ui/) |
| **CHRONOS** | online | Cyberpunk calendar constructor. Different colors, PNG export. → [`/chronos-ui/`](https://cyberdeck.tools/chronos-ui/) |
| **GRIDMAP** | compiling | TTRPG map utility for tabletop sessions. |
| **EIDOLON** | compiling | Token / avatar maker for TTRPG characters. |
| **SINFORGE** | compiling | Cyberpunk document constructor. ID cards, badges, keycards. |

Live cards link out to the deployed tool; `compiling…` cards are placeholders for tools not yet shipped.

## Running it

Just open the file:
```
xdg-open index.html          # Linux
open index.html              # macOS
start index.html             # Windows
```

No server needed — augmented-ui and the fonts load from CDN.

## Deployment

Served from the `CyberDelaai/CyberDelaai.github.io` repo via GitHub Pages, with the `cyberdeck.tools` apex domain set in `CNAME`. The sibling tools (`commlink-ui`, `chronos-ui`, …) live at their own paths under the same domain.

## Style notes

- **Fonts**: Share Tech Mono (console-style logo + tool names) and JetBrains Mono (body), loaded from Google Fonts.
- **Clipped corners**: [augmented-ui v2](https://augmented-ui.com) (CDN) shapes the tool cards (`tl-clip br-clip border`) and the donate button.
- **Scanlines**: a fixed full-viewport `body::before` overlay (`z-index: 9999`, `pointer-events: none`) tints the whole page like a CRT.
- **Status alignment**: cards are flex columns; the `▸ online _` line uses `margin-top: auto` so it pins to the bottom of every card regardless of description length. Only the `_` after `online` blinks.
- **Donate button**: a fixed bottom-right "ghost" link. Invisible by default, occasionally flickers into view (`donateGhost` loop); on hover/focus it materializes through a short heavy glitch burst (`donateGlitchIn`) and stays solid. Falls back to a dim static button for touch devices and `prefers-reduced-motion`.

## License

[MIT](LICENSE) © 2026 CyberDelaai

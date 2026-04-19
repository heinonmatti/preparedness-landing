# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file static landing page for **preparedness.fi** — an index of research tools for the M-LIFE project (Meso-Level Influence Framework and Explorable tools). Each tool lives on its own subdomain (e.g. `villagereserve.preparedness.fi`, `attractors.preparedness.fi`) and is linked from this page as a card.

Everything the browser needs is in `index.html`: markup, inline `<style>`, inline SVGs, no JS framework, no build step, no package manager. `assets/` holds hero images and actant glyphs; `design/hero.excalidraw` is the editable source for the hero composition.

## Working with the site

- **Preview**: open `index.html` in a browser, or run any static server from the repo root (e.g. `python -m http.server`). There is no build, no lint, no test suite — don't invent one.
- **Deploy**: pushing to `master` on `origin` (GitHub: `heinonmatti/preparedness-landing`) is the deploy. Don't push without the user asking.
- **Fonts** come from Google Fonts at runtime — no local font files.

## Design system (defined in `:root`, `index.html:16-40`)

Colors: `--ink` / `--ink-raised` (backgrounds), `--paper` / `--paper-dim` / `--paper-mute` (text), `--rule` (borders), `--ochre` (accent / eyebrow / live-adjacent), `--teal` (hover, live badge, links). Use the tokens, don't hardcode hex values.

Type stack: `--serif` (Instrument Serif, for H1/accent), `--serif-text` (Newsreader, for prose and card titles), `--sans` (Geist, for UI/body), `--mono` (JetBrains Mono, for eyebrows/badges/legends/footer — always uppercase with wide letter-spacing).

Layout container is `--container: 720px`. The whole page lives inside one `.container` — stay within it.

## The one recurring edit: adding/updating a tool card

Cards live in the `.tools` flex column inside `<section aria-labelledby="tools-heading">`. Two variants:

- **Live tool** → `<a class="tool-card" href="https://<subdomain>.preparedness.fi">` with `<span class="badge badge-live">Live</span>`.
- **Coming soon** → `<div class="tool-card coming-soon">` (no href, no anchor) with `<span class="badge badge-soon">Soon</span>`. The `coming-soon` class dims opacity and disables pointer events — don't wrap it in an `<a>`.

Each card has three grid columns: glyph (inline 40×40 SVG using `currentColor`, `stroke-width="1.5"`), text block (`<h2>` + `<p>`), badge. Keep glyphs monochromatic line art — they inherit color and animate via the `.ping` span on hover.

When promoting "Soon" → "Live": change the wrapper from `<div class="tool-card coming-soon">` to `<a class="tool-card" href="...">`, swap the badge class, and update the reveal delay if ordering changed (see next section).

## Reveal animation choreography

Elements with `data-reveal` fade in via staggered `animation-delay` declared at `index.html:418-430`. Delays are hardcoded per selector (`.tool-card:nth-of-type(1)` through `(6)`), so **if you add a seventh card, extend that list** — otherwise it pops in with no delay. `prefers-reduced-motion` short-circuits all of this (`index.html:446-455`); don't add animations that bypass that guard.

## Copy and voice

Hero/about copy treats the reader as an adult: concrete scenario (storm knock-on effects), no hedging, no marketing tone. The word **antifragile** and the **M-LIFE** project name are load-bearing — don't paraphrase them into "resilience" or a generic acronym. Project owner is Matti T.J. Heino (linked in the About section and footer).

## Responsive & accessibility notes that are easy to miss

- Mobile breakpoint at 640px collapses the tool-card grid to two columns and moves the badge beneath the text (`index.html:434-442`).
- Hero image uses `onerror="this.remove()"` so a missing asset degrades to the contour background rather than a broken icon — preserve that pattern if swapping the hero.
- The contour SVG is `aria-hidden` and purely decorative; the stage figure also has `aria-hidden="true"` since the `<h1>` carries the semantic meaning.

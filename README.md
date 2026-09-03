# SailplaneCalc

A free desktop calculator for sizing and balancing RC gliders/sailplanes — wing and tail
geometry, center-of-gravity and neutral point, stall speed and lift distribution, and
conventional-vs-V-tail conversion. It's a from-scratch app built on top of two long-used RC
soaring spreadsheets (`SailplaneCalc.xls` and its metric successor), plus a wing lift
distribution calculator ported from `LIFTROLL.xlsx` — see the in-app Credits tab for full
attribution.

Every input and result updates live as you type, works in imperial or metric units, and can be
saved to/loaded from a file so you can keep a library of past designs.

## Download

Grab the latest build for your operating system from the
[Releases page](https://github.com/andrewschuler/SailplaneCalcApp/releases) — no Python
installation required. Each release includes a ready-to-run build for Windows, macOS, and
Linux.

1. Download the zip for your OS and extract it anywhere.
2. Run `SailplaneCalc.exe` (Windows), `SailplaneCalc.app` (macOS), or the `SailplaneCalc`
   binary (Linux).

These builds aren't code-signed, so your OS may show a warning the first time you open one:

- **Windows**: click "More info," then "Run anyway."
- **macOS**: right-click the app and choose "Open" (only needed the first time).
- **Linux**: requires a reasonably current distro (glibc 2.35+, e.g. Ubuntu 22.04 or newer).

## What it calculates

- **Wing** — up to four tapered/swept panels, total and dihedral-projected span/area/aspect
  ratio, wing loading, Reynolds number estimate, and a live planform drawing.
- **Cl Calcs** — the local lift coefficient along the span and how the wing's lift distribution
  compares to the ideal elliptical distribution, so you can spot where a wing is likely to stall
  first and how far a planform is from optimal.
- **Cruciform Tail / V-Tail** — horizontal stabilizer and vertical fin (or V-tail) sizing, with
  live planform drawings.
- **Cruciform Tail CG / V-Tail CG** — neutral point and center-of-gravity balance point, shown
  on a diagram, specifiable as static margin, %MAC, or a distance from the wing root.
- **Quick V-Tail Sizing** — converts between a conventional tail and an equal-area V-tail in
  either direction.
- **Tail Sizing Checks** — Mark Drela's spiral-stability and tail-volume design checks.
- **Speed / Cl / G-Load** (on the Wing tab) — stall speed, lift coefficient, and the G-load at
  an assumed max diving speed; specify whichever one you know and the others follow.

Every tab includes an Instructions/Glossary/Credits reference on the Setup tab, and a
metric/imperial toggle that applies everywhere at once.

## Saving your work

Setup tab → **Save Configuration** writes every input across every tab to a single `.json`
file; **Load Configuration** reads one back in.

## License

[MIT](LICENSE) — free to use, modify, and redistribute.

## For developers

See [`docs/Manual.html`](docs/Manual.html) for the architecture, the formulas/theory behind
each calculation, and how to build from source.

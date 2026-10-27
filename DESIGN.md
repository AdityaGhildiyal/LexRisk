---
name: LexRisk
description: Editorial-grade contract review and risk analysis platform
colors:
  bg-app: "#fbfaf8"
  bg-card: "#ffffff"
  bg-subtle: "#f4f3ef"
  bg-inset: "#eceae5"
  text-primary: "#18181b"
  text-secondary: "#52525b"
  text-muted: "#71717a"
  text-subtle: "#a1a1aa"
  border: "#e4e4e7"
  border-light: "#eeede8"
  border-strong: "#d4d4d8"
  risk-crit-text: "#991b1b"
  risk-crit-bg: "#fef2f2"
  risk-crit-border: "#fecaca"
  risk-crit-bar: "#dc2626"
  risk-high-text: "#9a3412"
  risk-high-bg: "#fff7ed"
  risk-high-border: "#ffedd5"
  risk-high-bar: "#ea580c"
  risk-mod-text: "#854d0e"
  risk-mod-bg: "#fefce8"
  risk-mod-border: "#fef08a"
  risk-mod-bar: "#ca8a04"
  risk-low-text: "#166534"
  risk-low-bg: "#f0fdf4"
  risk-low-border: "#bbf7d0"
  risk-low-bar: "#16a34a"
typography:
  display:
    fontFamily: "Newsreader, Georgia, serif"
    fontSize: "clamp(2rem, 3.5vw, 2.75rem)"
    fontWeight: 400
    lineHeight: 1.25
  heading:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.6
  legal:
    fontFamily: "Newsreader, Georgia, serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.7
  mono:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "0.8125rem"
    fontWeight: 500
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.text-primary}"
    textColor: "{colors.bg-card}"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  button-primary-hover:
    backgroundColor: "#27272a"
  button-secondary:
    backgroundColor: "{colors.bg-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
---

## Overview

LexRisk couples the rigor of legal scholarship with the clarity of fine editorial typography. Contracts are dense, high-stakes documents; the user interface exists to enhance reading comprehension, highlight legal anomalies, and remove ambiguity without artificial ornamentation or generic AI clichés.

## Colors

- Grounded paper palette: Warm whites (`#fbfaf8`) paired with pure white cards (`#ffffff`) and soft parchment insets (`#f4f3ef`).
- Restrained semantic status: Contrast-verified crimson, rust, amber, and forest greens. Zero neon, zero glowing gradients.
- High-contrast typography: Dark zinc (`#18181b`) on paper meets AAA accessibility standards.

## Typography

- **Legal Text**: Newsreader serif for authentic legal cadence, balanced line measures (65–75ch), and comfortable long-form scanning.
- **UI Hierarchy & Data**: Plus Jakarta Sans for crisp, modern interface affordances.
- **Metrics & Technical Signals**: JetBrains Mono with tabular numbers (`font-variant-numeric: tabular-nums`) for aligned statistics and score displays.

## Layout

- Clean container ceiling (980px) ensuring natural line measure and focused scanning.
- Asymmetric grid for clause matrices: Obligor, Trigger, Consequence, and Plain English summary.
- Generous spacing hierarchy: tight related groups, generous section separation.

## Elevation & Depth

- Shadows carry offset and soft natural blur (`0 1px 3px rgba(0,0,0,0.04)`).
- Strict refusal of hard offset 2D block shadows and tacky decorative borders.
- Depth achieved through subtle tonal surface layers rather than heavy dropshadows.

## Shapes

- Restrained border-radius (4px–6px) reflecting high-precision legal instruments.
- Crisp 1px borders using carefully calibrated zinc dividers.

## Components

- **Upload Drop Zone**: Tactile, dashed border that activates smoothly on hover/dragover, clear file-selected confirmation card with instant file size and format feedback.
- **Risk Spectrum**: Continuous visual proportion bar summarizing contract vulnerability at a glance.
- **Clause Audit Row**: Unified card presenting the exact contract excerpt, 4-cell interpretation grid, entailment badge, and rationale footer.
- **Action Pills & Buttons**: Solid high-contrast pill filters with clear active states and item counts.

## Do's and Don'ts

- **Do** use tabular figures for scores and metrics.
- **Do** allow direct copy of raw clause quotes and summaries.
- **Do** preserve the authorial dignity of the legal excerpt with authentic serif typography.
- **Don't** use colored `border-left` or `border-right` thicker than 1px.
- **Don't** use kickers/eyebrows above headings. Let the heading carry its own weight.
- **Don't** use decorative gradients on text or cards.
- **Don't** use Unicode emojis in place of clean, consistent SVGs.

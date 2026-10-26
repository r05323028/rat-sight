---
name: 見光鼠 RatSight
description: Evidence-aware urban rodent movement workspace for Taipei municipal analysts
colors:
  paper: "#f2efe6"
  surface: "#faf8f2"
  ink: "#17181a"
  muted: "#5f5d55"
  rule: "#cbc4b1"
  rule-soft: "#ddd7c6"
  carbon: "#2f4a63"
  seal: "#a52a1f"
  seal-deep: "#8a2118"
  basemap: "#8a8f83"
  stormwater: "#2563eb"
  rodent: "#a3243c"
  simulated: "#0f6b62"
  administrative: "#8a5a12"
typography:
  display:
    fontFamily: "Songti TC, Noto Serif TC, PingFang TC, serif"
    fontSize: "40px"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "0"
  headline:
    fontFamily: "Songti TC, Noto Serif TC, PingFang TC, serif"
    fontSize: "17px"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.5
  note:
    fontFamily: "PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: "11.5px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "SFMono-Regular, JetBrains Mono, ui-monospace, monospace"
    fontSize: "10px"
    fontWeight: 500
    letterSpacing: "0.12em"
  data:
    fontFamily: "SFMono-Regular, JetBrains Mono, ui-monospace, monospace"
    fontSize: "12px"
    fontWeight: 400
    fontFeature: "tnum"
rounded:
  none: "0"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  gutter: "30px"
components:
  button-primary:
    backgroundColor: "{colors.seal}"
    textColor: "#ffffff"
    rounded: "{rounded.none}"
    padding: "10px 14px"
    height: "46px"
  button-primary-hover:
    backgroundColor: "{colors.seal-deep}"
  button-primary-disabled:
    backgroundColor: "#d9d2c1"
    textColor: "#5f5d55"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    height: "38px"
    padding: "7px 9px"
  classification-stamp:
    backgroundColor: "transparent"
    textColor: "{colors.carbon}"
    rounded: "{rounded.none}"
    padding: "3px 6px"
---

# Design System: 見光鼠 RatSight

## Overview

**Creative North Star: "The Signed Inspection Sheet"**

RatSight looks like the field form an inspector actually signs: warm copy paper, ruled sections, numbered fields, and a single vermilion seal that says what the record is and is not. The world is Taiwanese public-health paperwork — not a dashboard theme laid over it. Paper and ink carry almost everything; one seal colour carries meaning, and it is rationed.

The density is that of a working document: 13.5px body, 11.5px notes, mono figures for coordinates, counts, seeds, and classification tokens. Headings are set in Songti so the masthead and section titles read as printed form headings rather than UI labels. Everything is square. There are no floating cards, no pill badges, no shadows: a rule, a numbered field, and paper tone do the work that cards were doing.

**Key Characteristics:**
- Paper ground (#f2efe6) with a lighter surface tone for fields, never white cards.
- One seal vermilion (#a52a1f) spent at most four times per screen.
- Songti headings over PingFang body text over mono data.
- Numbered sections (01, 02 …) and a 表號/版次 masthead.
- Zero radius, hairline rules, 1.5–2px stamps and masthead rules.
- Classification rendered as a bordered stamp, never a coloured pill.

## Colors

A three-ink document palette: paper, ink, and a single seal, with a cool carbon blue reserved for provenance and classification.

### Primary
- **Seal Vermilion** (#a52a1f): the data-boundary stamp, the primary action, the workspace status dot, and selection state. On a given viewport it appears at most four times.
- **Seal Deep** (#8a2118): hover for the primary action only.

### Secondary
- **Carbon Blue** (#2f4a63): classification stamps, provenance blocks, section numbers, eyebrows, links. It is the bureaucratic ink, not a brand colour.

### Neutral
- **Copy Paper** (#f2efe6): page ground.
- **Field Paper** (#faf8f2): inputs, map shell, and blocks that sit on the page.
- **Ink** (#17181a): text, masthead rules, map frame, brand block.
- **Muted Ink** (#5f5d55): notes, secondary metadata, unavailable-state text (≈5.9:1 on paper).
- **Ruled Line** (#cbc4b1) and **Soft Rule** (#ddd7c6): section and row separators.

### Data Series (functional, not decorative)
- **Basemap Grey** (#8a8f83), **Administrative Amber** (#8a5a12), **Stormwater Blue** (#2563eb), **Rodent Report Red** (#a3243c), **Simulated Teal** (#0f6b62). These follow the map's own legend and are never used for interface chrome.

**The Four Seals Rule.** Seal vermilion appears at most four times per screen: data-boundary stamp, primary action, status dot, selection. Every other emphasis is ink, carbon, or weight.

**The Data-Series Containment Rule.** Map series colours stay inside the map, its legend, and layer glyphs. They never tint panels, buttons, or headings.

## Typography

**Display Font:** Songti TC (with Noto Serif TC, PingFang TC fallback)
**Body Font:** PingFang TC (with Noto Sans TC, Microsoft JhengHei fallback)
**Label/Mono Font:** SFMono-Regular (with JetBrains Mono, ui-monospace fallback)

**Character:** A printed form: Songti majuscules with a slight letterpress density, plain humanist sans for reading and controls, and monospace only where a value must be compared digit by digit.

### Hierarchy
- **Display** (700, 40px, 1.08): the workspace title 移動分析工作區 and the mobile 30px variant.
- **Headline** (700, 17px, 1.3): panel titles 圖層, 模擬預覽, 分析.
- **Body** (400, 13.5px, 1.5): running copy and control labels; note copy measures ≤ 74ch.
- **Note** (400, 11.5px, 1.6): data-boundary text, provenance detail, validation messages.
- **Label** (500, 10px, 0.12em, mono): section numbers, classification stamps, document meta, table keys.
- **Data** (400, 12px, tabular figures, mono): coordinates, seeds, counts, hashes, timestamps.

**The One Line of Emphasis Rule.** A heading earns weight, not colour. Only the seal and carbon carry chromatic emphasis.

## Layout

A 1600px maximum shell with 40px gutters. The workspace is a two-column document: a bordered map sheet on the left and a 400px numbered rail on the right, 30px apart. The map column is sticky at 16px and its frame is clamp(420px, calc(100vh - 232px), 820px) tall, so the map stays present while the rail is read. The rail runs 01 圖層, 02 模擬預覽, 03 分析, then the record panels (行政區參考, 雨水下水道管線, 鼠類回報) — task order first, records after.

Panels are separated by 1px rules with 16–20px internal rhythm; there is no card chrome. Breakpoints: 1180px narrows the rail to 352px, 940px collapses to one column and un-sticks the map, 640px reduces gutters to 14px and stacks paired fields.

## Elevation & Depth

Flat by construction. There are no shadows and no radius; depth comes from paper tone (field surface against page ground), rule weight (1px rows, 1.5–2px masthead and stamp borders), and the map's own frame. Nothing floats.

**The No-Card Rule.** No surface gets a shadow, a rounded corner, or a floating card. Regions are separated by rules and whitespace; if a region needs to read as a document block, give it a border, not a shadow.

## Shapes

Squares and rules. Border radius is 0 everywhere, including inputs, buttons, and chips. Stamps use 1.5px borders; the data-boundary seal is a 2px bordered, −1.6° rotated rectangle. Checkboxes stay native. Circles appear only where nature requires them: the 7px status dot and map point glyphs.

## Components

### Buttons
- **Shape:** square (0 radius), full rail width.
- **Primary:** seal fill (#a52a1f), white 14px/700 label, 46px height, 0.06em tracking.
- **Hover / Focus:** seal-deep fill on hover; 2px seal outline with 2px offset on focus-visible.
- **Disabled:** #d9d2c1 fill with #5f5d55 text, no opacity change.

### Chips (selection)
- **Style:** 1px ruled border, transparent fill, mono 10.5px label, square corners.
- **State:** hover darkens the border to ink; selected switches border and text to seal with a 6% seal wash.

### Classification Stamps
- **Style:** 1.5px carbon border, carbon mono text, 9.5px, 0.1em tracking, transparent fill.
- **Rule:** OBSERVED / INFERRED / SIMULATED / UNVERIFIED are never abbreviated, never recoloured, never turned into pills.

### Panels
- **Border:** top or bottom 1px rule only; no background change, no radius.
- **Header:** Songti 17px title with a mono 01-style counter, stamp aligned right; no kicker above the title.
- **Padding:** 16px top, 20px bottom, 0 horizontal.

### Inputs / Fields
- **Style:** 1px #b9b3a2 border, field-paper fill, square, 38px height, mono 12px value.
- **Focus:** 2px seal outline at 1px offset.
- **Disabled:** #f0ece0 fill with muted text at full opacity, so disabled reads as unavailable rather than broken.

### Navigation
- **Style:** single top masthead rule with the brand block (ink square, Songti wordmark), and a mono status line at right: dot, 研究工作區 / 臺北市. No tabs, no sidebar nav; the numbered rail is the navigation.

### Layer Rows
- **Shape:** 50px row, 1px soft rule, glyph + name + state.
- **State:** unavailable rows keep full-contrast muted text and a 未載入 mono label — never opacity, never a dead checkbox.
- **Control:** native checkbox with carbon accent.

## Do's and Don'ts

### Do:
- **Do** keep seal vermilion to four appearances per screen and let ink, carbon, and weight carry the rest.
- **Do** number the rail sections 01…06 with the mono counter and keep the 表號/版次 line under the workspace title.
- **Do** render classifications as carbon-bordered stamps with the English token intact.
- **Do** state absence in full-contrast muted text (尚未載入, 未估計) instead of hiding or graying out the region.
- **Do** separate regions with rules and whitespace; the page should read as one sheet.

### Don't:
- **Don't** add shadows, rounded corners, or floating cards; the No-Card Rule is absolute.
- **Don't** turn classification into coloured pills or use seal red for layer status.
- **Don't** tint interface chrome with data-series colours from the map.
- **Don't** use body copy below 11.5px or labels below 10px.
- **Don't** present simulated output, counts, or absence of data as observation; the UI's language rule outranks any visual idea.

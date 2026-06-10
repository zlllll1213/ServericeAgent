---
name: ServiceFlow Agent Demo
description: Evidence-first customer service agent console for workflow, retrieval, and handoff demos
colors:
  background: "#eef2ef"
  surface: "#ffffff"
  surface-strong: "#101316"
  surface-muted: "#f6f8f6"
  ink: "#111827"
  muted: "#4e5d68"
  line: "#d4ddd5"
  line-strong: "#b9c6be"
  accent: "#1f6f5b"
  accent-strong: "#134e40"
  accent-soft: "#e5f0eb"
  info: "#244f79"
  info-soft: "#e7eef5"
  danger: "#a33a2b"
typography:
  display:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"
    fontSize: "2.55rem"
    fontWeight: 700
    lineHeight: 1.06
    letterSpacing: "normal"
  headline:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"
    fontSize: "1.45rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "normal"
  title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"
    fontSize: "1.1rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "normal"
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"
    fontSize: "0.82rem"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "normal"
rounded:
  control: "8px"
  panel: "8px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  shell: "24px"
components:
  button-primary:
    backgroundColor: "{colors.accent-strong}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "8px 10px"
    height: "36px"
    typography: "{typography.label}"
  button-utility:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "8px 11px"
    height: "36px"
    typography: "{typography.label}"
  chip-status:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "8px 13px"
    height: "38px"
    typography: "{typography.label}"
  input-field:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "12px 14px"
    typography: "{typography.body}"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "16px"
  table-cell:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    padding: "11px 12px"
    typography: "{typography.body}"
---

# Design System: ServiceFlow Agent Demo

## 1. Overview

**Creative North Star: "Evidence Console"**

ServiceFlow uses a restrained product UI built for inspecting an agent, not selling one. The screen should feel like a working service console: calm, precise, and dense enough to explain decisions while leaving the answer, route, tools, retrieval hits, and handoff state visible at the same time.

The visual system is intentionally familiar. It uses a cool gray-green background, white operational panels, a deep service green accent, 8px controls, and a single system sans stack. The interface rejects generic chatbot marketing, opaque AI magic, decorative SaaS metrics, and fake glassmorphism. Evidence is the design material.

**Key Characteristics:**
- Evidence-first composition with chat and debug surfaces visible together.
- Restrained green accent used for primary actions, active navigation, and service status.
- White panels, thin borders, and soft elevation for long-running demo comfort.
- Fixed product typography with readable Chinese copy and tabular numerals for IDs, traces, metrics, and scores.
- Reduced-motion-safe interaction feedback that supports state changes instead of staging a show.

## 2. Colors

The palette is a cool operational neutral system with one service-green accent and a small set of semantic states.

### Primary
- **Service Green** (`accent`): The primary accent for status dots, hover borders, knowledge score text, and service identity.
- **Deep Service Green** (`accent-strong`): The primary action and active navigation color. Use it when the user is committing an action or reading the current section.
- **Evidence Mint** (`accent-soft`): The assistant message surface. It separates agent output from white panels without making the chat feel promotional.

### Secondary
- **Trace Blue** (`info`): The informational semantic color for routing decisions and technical evidence.
- **Trace Blue Soft** (`info-soft`): The decision card and system message surface. Use it for explanation, not decoration.
- **Danger Red** (`danger`): Error text and destructive or failed states only.

### Neutral
- **Console Background** (`background`): The full-page background for chat and admin shells.
- **Panel White** (`surface`): The default panel, button, table, and admin surface.
- **Strong Ink Surface** (`surface-strong`): The user message bubble and high-contrast dark surface.
- **Muted Panel Surface** (`surface-muted`): Headers, prompt strips, table headers, and input backgrounds.
- **Ink** (`ink`): Primary text, table values, button labels, and agent evidence values.
- **Operational Muted Text** (`muted`): Secondary copy, labels, IDs in low-emphasis positions, and empty evidence hints.
- **Hairline Border** (`line`): Default panel, control, card, table, and divider stroke.
- **Strong Hairline Border** (`line-strong`): Secondary structural strokes when the default line needs more separation.

### Named Rules
**The One Accent Rule.** Service Green is the only brand accent on a screen. Do not add decorative accent colors beyond semantic states.

**The Evidence Color Rule.** Blue explains, green acts, red warns. If a color does not communicate state or action, remove it.

## 3. Typography

**Display Font:** system UI sans stack with browser-native fallbacks.
**Body Font:** system UI sans stack with browser-native fallbacks.
**Label/Mono Font:** system UI sans stack with tabular numerals where data appears.

**Character:** Typography is practical and fixed-scale. It should feel like an operations product: clear labels, compact panels, readable Chinese copy, and numbers that align.

### Hierarchy
- **Display** (700, 2.55rem, 1.06): Product title and main workspace headline only. On mobile it steps down to 2rem.
- **Headline** (700, 1.45rem, 1.2): Admin sidebar title and major shell labels.
- **Title** (700, 1.1rem, 1.25): Panel headings, admin page titles, and compact view headers.
- **Body** (400, 1rem, 1.55): Chat explanations, panel prose, and form copy. Keep long prose around 65 to 75 characters per line when it is not table data.
- **Label** (700 to 800, 0.75rem to 0.9rem, 1.2): Product marks, panel kickers, message labels, chips, nav items, table headers, and compact controls.
- **Data** (700 to 800, compact sizes, tabular numerals): Conversation IDs, confidence, tickets, route trace values, scores, and metrics.

### Named Rules
**The No Display Labels Rule.** Buttons, table headers, form labels, and evidence labels use the same product sans scale. Do not introduce display fonts or oversized type into dense UI.

**The Data Alignment Rule.** Any value that can change length or format uses tabular numerals and wrapping guards so the evidence panel never breaks layout.

## 4. Elevation

ServiceFlow uses a hybrid of tonal layering, borders, and restrained shadows. Panels are lifted enough to distinguish the console from the page background, while chips and messages use small shadows only to clarify local stacking.

### Shadow Vocabulary
- **Console Panel Shadow** (`0 18px 42px rgba(17, 24, 39, 0.10)`): Main chat and debug panels. Use for primary work surfaces only.
- **Micro Surface Shadow** (`0 1px 2px rgba(17, 24, 39, 0.06)`): Status chips and compact controls that sit on the background.
- **Message Shadow** (`0 1px 2px rgba(17, 24, 39, 0.05)`): Message bubbles inside the chat stream.

### Named Rules
**The Quiet Lift Rule.** Shadows explain hierarchy, never mood. If a surface already has a border and tonal contrast, do not add another shadow.

**The No Glass Rule.** Do not use blur, frosted panels, or decorative transparency. ServiceFlow is an evidence console, not a glass marketing surface.

## 5. Components

### Buttons
Buttons are compact, rectangular, and operational. They should look reliable, not decorative.

- **Shape:** Gently curved controls (8px radius).
- **Primary:** Deep Service Green background with white text, bold label, and at least 36px height. The composer submit button grows to 58px height for touch comfort.
- **Utility:** White background, Ink text, Hairline Border, and 8px radius for prompt buttons, refresh, clear, table actions, and secondary operations.
- **Hover / Focus:** Hover may translate up by 1px and shift the border to Service Green within 160ms. Focus uses a 3px green outline with 3px offset.
- **Disabled:** Keep the control visible and reduce opacity to 0.72. Do not hide disabled actions.

### Chips
Chips are status and identity containers, not decorative tags.

- **Style:** White background, Hairline Border, pill radius (999px), compact height around 30px to 38px.
- **State:** Active status may include a 9px Service Green dot. Muted chips use Operational Muted Text and medium weight.

### Cards / Containers
Containers are evidence surfaces with clear borders and restrained fill.

- **Corner Style:** 8px radius across panels, cards, trace cards, admin forms, and table wraps.
- **Background:** Panel White for primary surfaces, Muted Panel Surface for headers and prompt strips, near-white evidence cards for trace and metrics.
- **Shadow Strategy:** Main work panels use Console Panel Shadow. Internal cards generally use borders and tonal layering instead of additional shadows.
- **Border:** Hairline Border is the default. Stronger or semantic borders are reserved for assistant, system, tool, and human message variants.
- **Internal Padding:** Dense UI uses 10px to 16px. Main message and evidence areas use 18px to 20px.

### Message Bubbles
Message bubbles are the signature conversation component.

- **User:** Strong Ink Surface with white text, aligned to the right.
- **Assistant:** Evidence Mint surface with green-tinted border, aligned to the left.
- **System:** Trace Blue Soft surface for confirmation and explanation.
- **Tool:** Warm utility surface for tool outputs only.
- **Human:** Soft indigo surface for human-agent messages.
- **Sizing:** Max width is `min(74ch, 86%)`, expanding to 100% on small screens.

### Inputs / Fields
Inputs are quiet, full-width, and close to the action that uses them.

- **Style:** Hairline Border, 8px radius, muted or white background, Ink text.
- **Focus:** 3px green focus outline with offset. Do not rely on color alone.
- **Textarea:** Chat input uses 58px minimum height and vertical resize within a bounded max height.
- **Error:** Error text appears under the composer in Danger Red and remains attached to the failed action.

### Tables
Tables carry operational density.

- **Structure:** White table wrapper, 8px radius, overflow auto, and a minimum width for dense admin data.
- **Headers:** Muted Panel Surface, Operational Muted Text, bold labels.
- **Cells:** 11px to 12px padding, Hairline Border row dividers, left alignment, and compact body size.
- **Actions:** Row actions use the same utility button vocabulary as the rest of the UI.

### Navigation
Navigation is a stable product rail, not a brand statement.

- **Sidebar:** 260px desktop rail with sticky full-height behavior and Panel White background.
- **Active State:** Deep Service Green with white text.
- **Default State:** White background, Ink text, Hairline Border, bold labels.
- **Mobile:** Sidebar becomes static and the content collapses into one column below 900px.

### Metrics, Trace Cards, and Debug Evidence Lists
Evidence components should make agent behavior inspectable at a glance.

- **Metrics:** Two-column grid on desktop, one column on narrow screens, tabular numerals, bold values, muted labels.
- **Trace Cards:** Bordered near-white containers with scrollable preformatted content and compact type.
- **Knowledge Hits:** White list items with a bold knowledge base, muted source file, and green score metadata.
- **Route Trace:** Ordered list with spacing and tabular numerals. Do not replace it with hidden tabs.

## 6. Do's and Don'ts

### Do:
- **Do** keep chat, route trace, tool calls, retrieval hits, citations, and evaluation visible as first-class evidence.
- **Do** use Deep Service Green for primary actions and active navigation only.
- **Do** keep panels at 8px radius, thin borders, and restrained elevation.
- **Do** use `min-height: 100dvh`, safe-area padding, and responsive one-column fallbacks for narrow screens.
- **Do** keep motion tied to state: entry hints, hover feedback, and changed evidence updates only.
- **Do** use `text-wrap: balance` for headings, `text-wrap: pretty` for prose, and tabular numerals for IDs, scores, metrics, and traces.
- **Do** show errors next to the chat or admin action that failed.

### Don't:
- **Don't** create a generic chatbot landing page. This is a working evidence console, not a marketing hero.
- **Don't** use decorative SaaS hero metrics, big-number stat blocks, or conversion-page sections inside the product UI.
- **Don't** imply opaque AI magic. The route, tools, retrieval, and handoff status must remain inspectable.
- **Don't** use fake glassmorphism, frosted cards, glow-heavy affordances, or blur as surface decoration.
- **Don't** overbuild admin chrome. Keep admin navigation familiar, dense, and stable.
- **Don't** bury routing evidence behind tabs when the page has room to show it.
- **Don't** introduce React, Tailwind, framework-only primitives, or build tooling into this visual system documentation.
- **Don't** animate layout properties such as width, height, top, left, margin, or padding.
- **Don't** add a second accent palette or purple/multicolor gradients.

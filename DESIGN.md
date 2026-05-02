---
version: alpha
name: Key Bank
base: VoltAgent-inspired agent infrastructure, customized with Coinbase-style banking clarity
description: >
  Key Bank should feel like an Agent Network fuel terminal with institutional
  ledger discipline. The interface uses a carbon-black canvas, emerald signal
  accents, monospace request/usage surfaces, and precise financial tables for
  lease, credit, settlement, and audit workflows.
---

# Key Bank Design Contract

This file is the visual and interaction contract for future Key Bank UI work.
Use it when generating pages, dashboards, docs-adjacent product surfaces, or
agent-facing control panels.

## Product Tone

Key Bank is not a generic fintech product and not a decorative AI landing page.
It is API Key banking infrastructure for Agent Network fuel.

The UI should communicate:

- **Operational confidence**: deposits, leases, proxy usage, and settlements are traceable.
- **Agent fuel energy**: emerald signal accents imply availability, routing, and powered-on execution.
- **Bank-grade clarity**: usage, credit, balances, and audit state must be legible before they are stylish.
- **Developer credibility**: code blocks, request metadata, route IDs, key fingerprints, and meter readings are first-class content.

Preferred language is concise and concrete: `Deposit`, `Lease`, `Proxy`,
`Settle`, `Credit`, `Fuel`, `Relay`, `Ledger`, `Audit`.

Avoid vague AI hype, tokenized-finance language, crypto speculation, or
consumer banking metaphors. Key Bank explicitly does not feel like a coin,
wallet, exchange, or governance product.

## Visual Direction

The base direction is VoltAgent-style:

- Carbon-black product canvas.
- Emerald green as the active signal color.
- Warm charcoal panels and hairline containment.
- Dense developer-console presentation.
- Code, logs, tables, and flow diagrams as primary visual material.

Key Bank customization adds Coinbase-style discipline:

- Clean ledger tables with aligned numbers.
- Credit ratings and utilization shown with restrained status colors.
- Audit and settlement state visible in compact badges.
- Lightly elevated white or near-white panels only when a banking report needs maximum readability.

## Color Tokens

### Core

| Token | Value | Use |
| --- | --- | --- |
| `canvas` | `#050507` | Main app background and dark marketing sections. |
| `surface` | `#101010` | Primary panels, nav, modals, controls. |
| `surface-raised` | `#151515` | Active panels, table wrappers, focused modules. |
| `surface-soft` | `#1b1b1c` | Subtle nested rows, hover surfaces, secondary cards. |
| `hairline` | `#3d3a39` | Default borders and separators. |
| `hairline-strong` | `#54504d` | Active panel borders and table frame emphasis. |
| `ink` | `#f2f2f2` | Primary text on dark surfaces. |
| `ink-muted` | `#b8b3b0` | Body text, secondary labels. |
| `ink-subtle` | `#8b949e` | Metadata, timestamps, inactive nav. |

### Brand and Status

| Token | Value | Use |
| --- | --- | --- |
| `signal` | `#00d992` | Key Bank active signal, focus, primary CTA text, route live state. |
| `signal-soft` | `#2fd6a1` | Softer emerald text and icon accents. |
| `signal-bg` | `rgba(0, 217, 146, 0.12)` | Success/active badge background. |
| `trust-blue` | `#0052ff` | Rare banking/trust accent for verified ledgers or external provider trust. |
| `credit-gold` | `#f4b000` | Credit tier, yield, rate, or premium status. |
| `warning` | `#ffba00` | Rate limit, pending settlement, degraded relay. |
| `danger` | `#fb565b` | Failed audit, expired lease, key revoked, blocked proxy. |
| `info` | `#4cb3d4` | Neutral system notices and provider metadata. |

### Light Report Mode

Use light panels sparingly for reports, receipts, and printable ledger views.

| Token | Value | Use |
| --- | --- | --- |
| `report-canvas` | `#ffffff` | Ledger exports and settlement receipts. |
| `report-surface` | `#f7f7f7` | Report section background. |
| `report-ink` | `#0a0b0d` | Primary text on light surfaces. |
| `report-muted` | `#5b616e` | Secondary report text. |
| `report-hairline` | `#dee1e6` | Report table borders. |

## Typography

Use system fonts for speed and credibility. Do not rely on decorative display
fonts. Keep letter spacing at `0`.

| Role | Family | Size | Weight | Line height | Use |
| --- | --- | --- | --- | --- | --- |
| Display | `system-ui, -apple-system, Segoe UI, sans-serif` | `56px` | `500` | `1.05` | First-screen product statement. |
| Page title | `system-ui, -apple-system, Segoe UI, sans-serif` | `40px` | `500` | `1.12` | Dashboard or section title. |
| Section title | `Inter, system-ui, sans-serif` | `28px` | `600` | `1.2` | Major module heading. |
| Card title | `Inter, system-ui, sans-serif` | `20px` | `600` | `1.3` | Panel and metric titles. |
| Body | `Inter, system-ui, sans-serif` | `16px` | `400` | `1.5` | Main explanatory and UI text. |
| Small | `Inter, system-ui, sans-serif` | `14px` | `400` | `1.45` | Metadata, helper text, table labels. |
| Micro | `Inter, system-ui, sans-serif` | `12px` | `500` | `1.35` | Badges, compact labels. |
| Mono | `SFMono-Regular, Menlo, Monaco, Consolas, monospace` | `13px` | `400` | `1.45` | Key fingerprints, request IDs, code, ledger refs. |

## Layout Principles

- Use a dense control-console layout by default.
- Use full-width dark bands for major page sections.
- Keep content constrained to readable widths: `1120px` for marketing/docs, `1440px` for dashboards.
- Use 8px as the base spacing unit.
- Use cards only for individual panels, table wrappers, repeated items, and modals.
- Do not put cards inside cards.
- Keep cards at `8px` radius or less.
- Use stable dimensions for tables, metric rows, boards, and controls so live data does not shift layout.
- Prefer real product UI, ledger tables, flow diagrams, and terminal excerpts over abstract decoration.

## Component Rules

### Navigation

- Background: `surface`.
- Border bottom: `1px solid hairline`.
- Height: `64px`.
- Logo lockup should include a small emerald signal mark plus `Key Bank`.
- Primary nav items: `Overview`, `Ledger`, `Leases`, `Credit`, `Audit`, `Docs`.
- Active item uses `signal` text or a thin emerald bottom border.

### Buttons

Primary CTA:

- Background: `surface`.
- Text: `signal-soft`.
- Border: `1px solid signal`.
- Radius: `6px`.
- Hover: `signal-bg`.

Secondary button:

- Background: `transparent`.
- Text: `ink`.
- Border: `1px solid hairline`.
- Radius: `6px`.
- Hover: `surface-soft`.

Danger button:

- Background: `rgba(251, 86, 91, 0.12)`.
- Text: `danger`.
- Border: `1px solid rgba(251, 86, 91, 0.4)`.

Use icon buttons for tool actions such as copy, reveal, refresh, filter, export,
and inspect.

### Cards and Panels

- Background: `surface`.
- Border: `1px solid hairline`.
- Radius: `8px`.
- Padding: `20px` or `24px`.
- Active panel border: `1px solid signal`.
- Use subtle emerald glows only for live/active relay states, never as page decoration.

### Ledger Tables

Ledger tables are a signature component.

- Wrapper: `surface` with `1px solid hairline`.
- Header background: `surface-raised`.
- Row hover: `surface-soft`.
- Numeric columns must be right-aligned.
- Mono columns: `lease_token`, `key_id`, `request_id`, `ledger_ref`, key fingerprints.
- Use compact status badges for settlement and audit state.
- Keep row height between `44px` and `56px`.

Recommended columns:

- `Time`
- `Agent`
- `Provider`
- `Model`
- `Lease`
- `Tokens`
- `Cost`
- `Credit`
- `Status`
- `Audit`

### Status Badges

Badges are compact and data-like, not decorative pills.

| State | Background | Text | Border |
| --- | --- | --- | --- |
| `Live` | `signal-bg` | `signal` | `rgba(0, 217, 146, 0.35)` |
| `Settled` | `rgba(0, 82, 255, 0.12)` | `#7aa2ff` | `rgba(0, 82, 255, 0.35)` |
| `Pending` | `rgba(255, 186, 0, 0.12)` | `warning` | `rgba(255, 186, 0, 0.35)` |
| `Failed` | `rgba(251, 86, 91, 0.12)` | `danger` | `rgba(251, 86, 91, 0.35)` |
| `Verified` | `signal-bg` | `signal` | `rgba(0, 217, 146, 0.35)` |

### Credit Rating

Credit is displayed as a bank-grade signal, not as a gamified badge.

- Use `A+`, `A`, `B`, `C`, `Watch`, `Blocked`.
- `A+` and `A`: emerald.
- `B`: info blue.
- `C` and `Watch`: warning.
- `Blocked`: danger.
- Pair rating with utilization, repayment history, and rate when space allows.

Example:

```text
A    18.4% utilization    0.8% lease rate
```

### Audit Trail

Audit state must be visible wherever usage or settlement appears.

Recommended states:

- `Verified`
- `Metered`
- `Pending`
- `Mismatch`
- `Revoked`

Audit views should include:

- Request timestamp.
- Relay ID.
- Provider/model.
- Key fingerprint.
- Lease token hash.
- Token count.
- Cost estimate vs actual.
- Settlement reference.

### Code and Request Blocks

Code blocks should look like live infrastructure.

- Background: `#080808`.
- Border: `1px solid hairline`.
- Text: `ink`.
- Accent line or prompt marker: `signal`.
- Include copy action as an icon button.
- Prefer concise, runnable examples over long snippets.

## Page Patterns

### Landing / Overview

First viewport should immediately signal Key Bank:

- Hero title: `Key Bank` or `API Key Bank for Agent Network Fuel`.
- Supporting copy should mention deposit, lease, relay, and settle.
- Visual should be a real product-style console: flow diagram plus ledger preview.
- Avoid abstract gradients, decorative orbs, or generic AI imagery.

Recommended first-screen modules:

- Fuel available.
- Active leases.
- Settlement volume.
- Audit pass rate.
- Deposit -> Lease -> Proxy -> Settle flow.

### Dashboard

Dashboard should prioritize operational scanability:

- Top metric strip: fuel pool, active leases, pending settlements, credit exposure.
- Main area: ledger table.
- Side rail: credit tier summary and relay health.
- Secondary area: recent audit events.

### Lease Detail

Lease detail should feel like inspecting a transaction:

- Header: lease state, provider, model, expires at.
- Body: request path, token meter, cost estimate, actual cost.
- Footer: settlement and audit references.

### Docs / Developer Surface

Docs can keep the dark terminal theme but should reduce visual density:

- Use code blocks and endpoint tables.
- Show `anet svc discover`, deposit, lease, proxy, and settle examples.
- Keep API references precise and sparse.

## Motion

Motion should imply signal and routing, not entertainment.

- Live relay indicators may pulse gently.
- Table row updates may fade in.
- Flow diagram edges may animate only when demonstrating a request lifecycle.
- Avoid large page transitions, floating shapes, or decorative ambient animation.

## Accessibility

- Maintain high contrast on dark surfaces.
- Do not communicate status by color alone; pair color with text or icon.
- Use visible focus outlines with `signal`.
- Keep table headers sticky when tables exceed viewport height.
- Support keyboard navigation for filters, table rows, and detail drawers.

## Do

- Lead with product UI, ledger tables, and agent fuel flows.
- Use emerald as the active energy signal.
- Use clear financial/accounting alignment for balances, costs, and token counts.
- Show audit state next to settlement state.
- Keep copy short, operational, and concrete.

## Do Not

- Do not use crypto wallet, coin, exchange, or governance visual language.
- Do not use pastel AI gradients as the main identity.
- Do not overuse emerald; it is a signal, not wallpaper.
- Do not make dashboards look like marketing cards.
- Do not hide accounting details behind abstract charts.
- Do not use rounded pill-heavy UI for core financial data.
- Do not add decorative orbs, bokeh, or generic network-glow backgrounds.

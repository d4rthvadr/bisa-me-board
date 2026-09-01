# DESIGN

## Purpose

This document records the approved visual direction for QnA Board so the production implementation stays consistent across pages and future iterations.

It captures:
- brand direction
- theme strategy
- color usage
- typography
- spacing and shape choices
- UI decisions approved from the prototype

This file is the default UI contract for the project. If a future change alters an approved visual pattern, update this document in the same change so the implementation and the design record stay aligned.

## Brand direction

QnA Board should feel:
- calm
- focused
- meeting-friendly
- modern, but not flashy
- lightweight enough for live participation

The product should not feel like a marketing site or a generic admin dashboard. The visual language should support one main activity: asking, scanning, and moderating questions quickly.

## Core product cues

- Green is the primary brand signal.
- Rounded forms and cards keep the experience approachable.
- Surfaces should feel clean and structured rather than decorative.
- Contrast should come from hierarchy, spacing, and surface separation, not shadows or gradients.
- DaisyUI semantic tokens should be the default foundation, with limited custom colors only where necessary for the approved brand look.

## Approved theme strategy

- Support both **light** and **dark** themes app-wide.
- Theme choice should persist **per browser**.
- Theme should be rendered server-side from persisted state to avoid mismatched first paint.
- The public board, owner pages, auth pages, and landing page should all respect the same theme system.

## Approved prototype decision

The chosen direction is based on **Option A** from the standalone prototype:

- inline composer at the top of the public board
- composer expands on focus
- visible character count in the composer
- optional name field revealed on focus
- question list immediately below the composer
- first/highlighted card can use a soft green emphasis treatment
- no “Question AI” helpers or suggestion chips
- no decorative gradients
- minimal to no shadow reliance
- top navigation should stay simple; prefer a single Q&A cue instead of extra product tabs

## Color system

These are implementation targets, not a rigid token library. Prefer DaisyUI theme tokens first, then map custom accents where needed.

### Brand green

- Header green: `#1f6b35`
- Dark header green: `#0f3b1c`
- Bright accent green / active Q&A badge: `#43d067`
- Featured border green: `#8fc49a`

### Light theme surfaces

- App background: `#f2f5ef`
- Primary card surface: `#ffffff`
- Soft highlighted card: `#eef8ee`
- Reply inset surface: `#f4f8f2`
- Light border: `#d5ddd0` to `#dde5d9`

### Dark theme surfaces

- App background: `#171a17`
- Primary card surface: `#1d211e`
- Featured card surface: `#162319`
- Reply inset surface: `#202622`
- Dark border: `#2d3830` to `#2f3c32`

### Text contrast targets

- On dark green headers, use explicit light text rather than relying on inherited DaisyUI tokens when custom backgrounds are applied.
- Body copy must remain high contrast in both themes.
- Secondary text should still be comfortably readable; do not let muted text become low-contrast decoration.

## Typography

Use the existing system sans stack already present in the project:

- `Inter`
- `ui-sans-serif`
- `system-ui`
- `-apple-system`
- `"Segoe UI"`
- `sans-serif`

### Type scale guidance

- App/page title: `text-2xl`
- Section title: `text-lg`
- Card/person name: base to `text-lg` emphasis
- Body copy: `text-base`
- Composer prompt:
  - mobile: `text-xl`
  - larger screens: near `2rem`
- Metadata / helper text: `text-sm`
- Small supporting labels: `text-xs` to `text-sm`

### Typography rules

- Prioritize legibility over density.
- The composer prompt should feel visually prominent.
- Question text should remain easy to scan in a live setting.
- Use medium/semibold weight for important labels and names; avoid over-boldening the whole UI.

## Shape, spacing, and layout

### Shape

- Large cards: approximately `1.5rem` to `2rem` corner radius
- Inputs: pill or soft rounded treatment where appropriate
- Vote badges: fully rounded pills

### Spacing

- Keep generous vertical spacing between composer and question list.
- Card internals should breathe, especially in the public board feed.
- Reply blocks should be visually nested but not cramped.

### Layout

- Public board should stay in a focused central column rather than stretching too wide.
- The composer must appear before the question list.
- The hierarchy should read:
  1. board identity
  2. composer
  3. sorting controls
  4. question feed

## Component decisions

### Shared shell

- Keep the top bar simple.
- Add theme toggle in the shared shell.
- Avoid heavy decorative backgrounds that only work in one theme.
- Landing hero should be open on the page rather than wrapped in a large card, with the participant join flow presented as a prominent horizontal pill above the headline.

### Inputs and field styling

- Avoid browser-default input chrome wherever a custom shell already defines the interaction.
- When an input sits inside a larger framed component, the outer component should carry the border/background and the input itself should usually be:
  - borderless
  - backgroundless
  - shadowless
  - visually integrated with surrounding content
- Placeholder copy should remain readable but quieter than entered text.
- Focus should be communicated with subtle accent changes, spacing, or adjacent UI reactions rather than stacking multiple outlines and borders.
- Rounded full-width pill inputs are appropriate for entry points like join-by-code and optional short metadata fields.
- Standard DaisyUI bordered inputs are acceptable on auth-style standalone forms, where the field itself is the primary control surface.

### Buttons and CTA styling

- Primary CTAs should use the brand green/success family.
- Destructive or state-changing management actions like **Close board** should remain outlined and clearly separated from primary creation flows.
- Compact inline actions should use rounded pills.
- In integrated controls, such as the landing join flow, the submit affordance may live inside the same pill as the text input when it improves fidelity to the approved reference.
- Avoid oversized button stacks inside already-dense surfaces.

### Tabs and segmented controls

- Keep tabs simple, horizontal, and familiar.
- Public board sorting tabs should feel light and secondary to the question feed.
- Owner moderation tabs should live outside the summary card and directly on the page, not inside another card-like container.
- Use tabs for a small number of mutually exclusive states only; do not turn them into decorative navigation.

### Avatars

- Use simple circular initial avatars.
- Initials must be vertically and horizontally centered explicitly; do not rely on fragile library placeholder wrappers.
- Public board composer avatars should be smaller and lighter.
- Question card avatars can be slightly larger for scanability.
- Featured/active states may use green-tinted avatar fills; default states should use neutral surfaces with readable contrast in both themes.

### Public board composer

- Inline, always visible.
- Expands on focus.
- Includes character count.
- Reveals optional name field on focus.
- The composer card is the only frame; do not add nested bordered inputs inside it.
- Question and name inputs should feel borderless and backgroundless, with focus indicated through spacing, typography, and small accent cues instead of extra chrome.
- The prompt area should start compact and simple, closer to a prompt row than a large form block.
- The expanded section should remain visually light; avoid adding extra pill containers or boxed rows unless needed for clarity.
- Character count should stay tucked into the composer chrome and not compete with the prompt.
- Optional metadata like the name field should read as supporting information, not as a second primary form.
- The send button can share the expanded composer area, but the composer should still read as one unified surface.
- Should preserve current POST/redirect behavior when implemented for production.

### Question cards

- Use clean bordered cards.
- Featured/top card may use a soft green surface.
- Vote count should live in a compact pill at the top-right.
- Vote pills must use explicit readable styling in dark mode; do not rely on fragile token combinations that can collapse contrast.
- Metadata should sit above the question content and stay compact.
- Support copy under the question should remain subdued but still readable in dark mode.
- Moderator/host reply should appear as an inset block inside the card.

### Landing page

- The landing page should not use a giant enclosing hero card.
- The composition should read top-to-bottom:
  1. participant join pill
  2. oversized headline
  3. short supporting copy
  4. primary CTA
  5. secondary low-emphasis link
- The participant join flow should use a blue horizontal pill with a white inner entry area.
- The join submit button should feel integrated with the entry control rather than detached as a second large button.
- The white join field border should be subtle, not high-contrast or attention-stealing.
- Headline scale should be large and bold enough to carry the page without extra decorative sections.
- Supporting copy should stay concise and centered.

### Owner board index

- The owner boards page should use a compact table/list management layout, not a card grid.
- Column priorities are:
  1. board identity
  2. code
  3. created date
  4. status
  5. actions
- The table should use restrained row separators and light hover feedback.
- Actions may remain inline buttons as long as the layout stays compact and scannable.
- Empty states should be simple and instructional, not overly illustrated.

### Owner board detail

- The owner board detail page should separate summary information from operational controls.
- Board identity/status belongs in a top summary card.
- Moderation tabs and **Close board** belong on their own row outside that card.
- That controls row should sit directly on the page without another surrounding card or framed box.
- Question moderation cards can remain card-based because they are content objects, not page scaffolding.

### Owner and auth pages

- Use the same surface language as the public board:
  - bordered cards
  - restrained backgrounds
  - strong readable text contrast
  - consistent button and tab treatments
- Owner board indexes should prefer a compact table/list management view over a grid of cards when scanning multiple boards.
- Auth forms may use more standard input framing than the public composer, but should still avoid decorative excess.

### Card usage rules

- Use cards for content objects and self-contained utility modules:
  - question items
  - share/QR modules
  - summary blocks
- Do not wrap every layout section in a card by default.
- If a row already reads clearly through spacing and alignment, prefer no extra box.
- When a card is used, keep it clean:
  - soft border
  - no heavy shadow
  - generous radius
  - readable interior spacing

### Form behavior rules

- Prefer simple progressive disclosure over multiple stacked fields shown at once.
- Preserve PRG behavior for production forms.
- Use one dominant input goal per surface.
- Do not let optional fields visually overpower the primary action.
- Align form behavior and visual hierarchy: primary input first, supporting metadata second, submit last.

## Surface-by-surface default decisions

### Landing

- Open hero layout, not card-wrapped.
- Blue join bar above the hero headline.
- White integrated code-entry pill inside the join bar.
- Small embedded arrow submit inside that white pill.
- One primary CTA and one low-emphasis secondary link below the supporting copy.

### Public board

- Title/status row first.
- Inline ask composer second.
- Sorting tabs third.
- Question feed fourth.
- Share/QR card may appear below the feed for owners.

### Owner boards index

- Management table, not card grid.
- Light row hover state.
- Compact action buttons aligned to the right.

### Owner board detail

- Summary card at top.
- Tabs and board-level CTA on a separate unboxed row.
- Question items remain individual cards.
- QR/share module remains a utility card in the side column.

### Auth forms

- Conventional form structure is acceptable here.
- Fields may keep clearer standalone input borders than the public composer.
- Layout should still be simple, centered, and free of decorative noise.

## Things to avoid

- gradients as a primary surface treatment
- shadow-heavy elevation systems
- low-contrast muted text on custom dark surfaces
- extra chrome that competes with asking/viewing questions
- copying prototype code directly into production without adapting it to existing app behavior

## Implementation notes

- Prefer DaisyUI semantic tokens for maintainability.
- When using custom background colors, explicitly verify foreground contrast.
- HTMX partials must use the same theme-safe styles as full-page renders.
- The prototype route is a reference only; production code should reimplement the approved decisions cleanly.

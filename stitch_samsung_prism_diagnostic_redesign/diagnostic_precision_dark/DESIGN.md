---
name: Diagnostic Precision Dark
colors:
  surface: '#0f131d'
  surface-dim: '#0f131d'
  surface-bright: '#353944'
  surface-container-lowest: '#0a0e18'
  surface-container-low: '#171b26'
  surface-container: '#1c1f2a'
  surface-container-high: '#262a35'
  surface-container-highest: '#313540'
  on-surface: '#dfe2f1'
  on-surface-variant: '#ccc3d8'
  inverse-surface: '#dfe2f1'
  inverse-on-surface: '#2c303b'
  outline: '#958da1'
  outline-variant: '#4a4455'
  surface-tint: '#d2bbff'
  primary: '#d2bbff'
  on-primary: '#3f008e'
  primary-container: '#7c3aed'
  on-primary-container: '#ede0ff'
  inverse-primary: '#732ee4'
  secondary: '#aec6ff'
  on-secondary: '#002e6b'
  secondary-container: '#508eff'
  on-secondary-container: '#00275e'
  tertiary: '#4cd7f6'
  on-tertiary: '#003640'
  tertiary-container: '#007184'
  on-tertiary-container: '#b7efff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#eaddff'
  primary-fixed-dim: '#d2bbff'
  on-primary-fixed: '#25005a'
  on-primary-fixed-variant: '#5a00c6'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#aec6ff'
  on-secondary-fixed: '#001a43'
  on-secondary-fixed-variant: '#004397'
  tertiary-fixed: '#acedff'
  tertiary-fixed-dim: '#4cd7f6'
  on-tertiary-fixed: '#001f26'
  on-tertiary-fixed-variant: '#004e5c'
  background: '#0f131d'
  on-background: '#dfe2f1'
  surface-variant: '#313540'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.005em
  label-code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: -0.01em
  label-code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.25rem
  gutter-sm: 0.75rem
  gutter-lg: 2rem
  margin: 1.5rem
  margin-sm: 1rem
  margin-lg: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes an ultra-refined, engineering-grade diagnostic aesthetic combining the tactile clarity of Samsung One UI, the disciplined density and speed of Linear, and the luminous edge-lit polish of Vercel. 

The visual persona is authoritative, analytical, and frictionless. Crafted for elite engineers, field technicians, and automated diagnostic workflows, the system replaces clinical sterility with sophisticated deep-space luminance. Interfaces convey absolute confidence through rapid visual parsing, crystalline telemetry readouts, high-contrast status feedback, and frictionless multi-state transitions.

## Colors

The system uses a dark-first foundation built on cosmic slate and absolute near-black layers, illuminated by focused spectral highlights.

### Foundations & Surfaces
- **Canvas Base (`#0B0F19`)**: Background anchor providing pure visual silence.
- **Surface Level 1 (`#0F172A`)**: Primary structural panels, sidebars, and tab containers.
- **Surface Level 2 (`#111827`)**: Standard card containers, interactive module blocks, and dialog canvases.
- **Surface Level 3 (`#1E293B`)**: Elevated overlays, dropdowns, tooltips, and secondary hover states.

### Core Accents
- **Primary Violet (`#7C3AED` / Hover: `#8B5CF6` / Active: `#6D28D9`)**: Drives cognitive focus, AI processing cues, and primary interactive resolutions.
- **Secondary Cyan & Blue (`#0070F3` / Accent: `#06B6D4` / Highlight: `#38BDF8`)**: Signals dynamic data pathways, active connections, telemetry filters, and secondary actions.

### Semantic Status Palette
- **Success & Verified (`#10B981` / Dark: `#059669`)**: Reserved exclusively for verified solutions, passed health-checks, and confirmed resolutions.
- **Warning & Clarification (`#F59E0B` / Dark: `#D97706`)**: Denotes ambiguous diagnostic states, missing telemetry parameters, and user clarification prompts.
- **Danger & Alert (`#EF4444` / Dark: `#B91C1C`)**: Signifies hardware failures, critical diagnostic exceptions, and unresolvable system states.

### Structural Lines & Borders
- **Base Stroke (`#1E293B`)**: Structural partition line for layout dividers.
- **Subtle Glass Stroke (`rgba(255, 255, 255, 0.08)`)**: 1px crisp outline on card perimeters and floating interactive micro-panels.

## Typography

The typographic hierarchy prioritizes rapid scanability across deep data structures and technical outputs.

- **Primary Interface Typeface (`Inter`)**: Deployed across all functional UI hierarchy, headers, metric displays, and body copy. Numerical metrics and step indicators must enforce tabular figures (`font-variant-numeric: tabular-nums`) to prevent horizontal jitter during real-time streaming diagnostics.
- **Monospace Technical Tagging (`JetBrains Mono`)**: Applied to all hardware identifiers, device serials, model hashes, JSON response payloads, and step-index chips.
- **Hierarchy Rules**: Display headings use tight tracking and bold weights to project structural clarity. Secondary body copy remains restrained to slate-tinted neutrals (`#94A3B8`) to elevate core data parameters.

## Layout & Spacing

The layout is built upon a high-density, adaptable 12-column fluid grid tailored for diagnostic consoles, multi-pane telemetry monitors, and responsive inspection panels.

### Form Factor Adaptations
- **Desktop (1280px+)**: 12 columns with 32px (`margin-lg`) canvas margins and 20px (`gutter`) column separation. Three-tier split views: navigation/context sidebar (280px fixed), primary diagnostic canvas (fluid, 6–8 cols), and resolution/telemetry inspector (380px fixed).
- **Tablet (768px – 1279px)**: 8 columns with 24px (`margin`) margins and 16px gutters. Collapses the telemetry inspector into an off-canvas drawer or vertical lower stack.
- **Mobile (< 768px)**: Single column stream with 16px (`margin-sm`) edge margins and 12px vertical gaps. Horizontal swipe-rail navigation handles operational stage transitions.

### Spacing Philosophy
Internal component padding follows a strict 4px sub-grid rhythm:
- Micro badges and status chips utilize `space-xs` (4px) vertical and `space-sm` (8px) horizontal padding.
- Diagnostic actionable cards and control panels leverage `space-md` (16px) to `space-lg` (24px) internal clearances to maintain ergonomic touch and click precision.

## Elevation & Depth

Visual hierarchy operates through atmospheric tonal stacking, translucent frosted boundaries, and directional edge glow rather than heavy drop shadows.

### Surface Tiers
- **Backdrop Canvas (`#0B0F19`)**: Base background layer.
- **Base Card Tier (`#111827` at 70% opacity + `backdrop-filter: blur(12px)`)**: Ambient diagnostic modules resting on canvas.
- **Elevated Interactive Tier (`#1E293B` at 85% opacity + `backdrop-filter: blur(16px)`)**: Active flyouts, modal overlays, dropdown menus, and popovers.

### Luminescent Boundaries & Ambient Light
- **Ghost Borders**: Every card and micro-panel features a 1px solid hairline border using `rgba(255, 255, 255, 0.08)`.
- **Active Edge Glow**: Focused or hovered interactive cards introduce an inset ambient highlight: `box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.15), 0 0 20px -5px rgba(124, 58, 237, 0.25)`.
- **Diagnostic Success Bloom**: Resolved states transition their border to `rgba(16, 185, 129, 0.4)` accompanied by a soft, diffused green underglow: `0 4px 24px -6px rgba(16, 185, 129, 0.2)`.

## Shapes

The design system incorporates intentional, curvature-controlled geometries inspired by Samsung One UI's soft squircle sensibilities, balanced with Linear’s precise technical density.

- **Base Components (Inputs, Chips, Tab Triggers, Buttons)**: Defined at `rounded-md` (8px) to `rounded-lg` (12px) for crisp operational efficiency.
- **Diagnostic Container Panels & Surface Cards**: Standardized at `rounded-xl` (16px) with primary floating modals utilizing `rounded-2xl` (24px) for architectural grounding.
- **Status Pills & Progress Trackers**: Rendered with full continuous curvature (`rounded-full`) to immediately differentiate continuous state monitors from structural cards.

## Components

### Buttons & Action Controls
- **Primary Resolve Button**: Solid Electric Violet (`#7C3AED`) background with pure white text, 12px rounded corners, subtle top-edge bevel highlight, and 200ms ease transitions. Active click drops scale to `0.98`.
- **Secondary / Action Ghost**: Deep slate translucent fill (`rgba(30, 41, 59, 0.6)`) with `rgba(255, 255, 255, 0.08)` hairline border, shifting to `#334155` on hover.
- **Verified Primary**: Emerald Green (`#10B981`) solid fill with Lucide checkmark icon, reserved strictly for committing verified fixes.

### Diagnostic State Tabs
- Segmented, pill-shaped horizontal container (`#0F172A`) containing tab buttons for the operational lifecycle: `Initial State`, `Clarification Flow`, `Processing`, `Verified Results`, and `System Architecture`.
- Active tab features a floating frosted highlight (`#1E293B`) with a 1px translucent stroke and an electric cyan or violet indicator line.

### Diagnostic & Metric Cards
- Constructed with frosted dark slate backdrops (`#111827` at 80% opacity, 16px blur) and 1px glass perimeter strokes.
- Hover triggers subtle upward translate (-1px) and illuminates a faint radial gradient spotlight centered on the cursor position.
- Header contains a categorical status badge alongside a crisp Lucide icon (e.g., `Cpu`, `ShieldCheck`, `AlertCircle`, `Terminal`).

### Chips & Segmented Controls
- **Technical Tags**: Monospaced font (`JetBrains Mono`, 11px), dark container (`rgba(15, 23, 42, 0.8)`), padded with 4px vertical / 8px horizontal, displaying hardware model codes, error numbers, and protocol names.
- **Status Chips**: Glowing dot indicator (4px) with semantic color mapping: Emerald (Verified), Amber (Clarification Required), Red (Hardware Fault), Violet (AI Inferring).

### Inputs & Terminal Fields
- Dark recessed inputs (`#080C14`) with a persistent `rgba(255, 255, 255, 0.08)` border.
- Focus state activates an electric cyan glow (`0 0 0 2px rgba(6, 182, 212, 0.25)`) with an active stroke of `#0070F3`.
- Technical prompt terminals feature a leading `$` prompt in muted slate with monospace code syntax coloring.

### Selection Controls (Checkboxes & Radios)
- Squircle checkboxes with 6px border-radius; radio elements feature concentric rings.
- Inactive state: 1px border `#334155` on `#0F172A`.
- Selected state: Electric Violet fill with crisp white Lucide checkmark icon.
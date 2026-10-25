---
name: Cybernetic Observability Cockpit
colors:
  surface: '#0f131c'
  surface-dim: '#0f131c'
  surface-bright: '#353942'
  surface-container-lowest: '#0a0e16'
  surface-container-low: '#181c24'
  surface-container: '#1c2028'
  surface-container-high: '#262a33'
  surface-container-highest: '#31353e'
  on-surface: '#dfe2ee'
  on-surface-variant: '#c3c6d7'
  inverse-surface: '#dfe2ee'
  inverse-on-surface: '#2c3039'
  outline: '#8d90a0'
  outline-variant: '#434655'
  surface-tint: '#b4c5ff'
  primary: '#b4c5ff'
  on-primary: '#002a78'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#0053db'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#c0c1ff'
  on-tertiary: '#1000a9'
  tertiary-container: '#585be6'
  on-tertiary-container: '#f1eeff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#e1e0ff'
  tertiary-fixed-dim: '#c0c1ff'
  on-tertiary-fixed: '#07006c'
  on-tertiary-fixed-variant: '#2f2ebe'
  background: '#0f131c'
  on-background: '#dfe2ee'
  surface-variant: '#31353e'
typography:
  headline-xl:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: '0'
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: '0'
  label-code-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.01em
  label-code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.05em
  badge-status:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.08em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.25rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 1.75rem
---

## Brand & Style

The design system establishes a mission-critical, deep-space cybernetic command center designed for automated Site Reliability Engineering (SRE) and closed-loop autonomic operations. Its target audience encompasses tier-3 platform architects, infrastructure engineers, and autonomous agent supervisors who require instant situational comprehension under severe stress. 

The aesthetic is precision-driven **Cybernetic Glassmorphism & Obsidian Dark-Mode**:
- **High-density operational telemetry**: Surfaces are dark, quiet, and unobtrusive, allowing high-luminescence status states to command immediate tactical focus.
- **Architectural discipline**: Every layout strictly aligns to metric grids, mono-spaced data columns, and hairline boundaries to eliminate visual clutter and cognitive latency.
- **Controlled luminescence**: Statuses are not just static colors—they act as cybernetic energy lines (neon emerald for nominal state, incandescent amber for degraded thresholds, laser crimson for hard SLA violations, and electric indigo/cyan for active synthetic intervention).

## Colors

The palette balances low-reflectivity obsidian foundations with high-chroma cybernetic status emitters:

- **Foundation Layers**: 
  - Canvas / Void: `#080B10`
  - Base Surface (`surface-0`): `#0B0F17`
  - HUD Card Container (`surface-1`): `#111827` (with 80% opacity backdrop blur)
  - Interactive Panels (`surface-2`): `#1E293B`
- **Hairline Dividers & Outlines**:
  - Ghost border: `rgba(255, 255, 255, 0.08)`
  - Active structural border: `#1E293B`
  - Focus / Accent stroke: `#334155`
- **Signal & Status Diagnostics**:
  - Nominal / Healthy: `#10B981` (Base), `#059669` (Dark), with glow aura `rgba(16, 185, 129, 0.25)`
  - Warning / Drift: `#F59E0B`, glow aura `rgba(245, 158, 11, 0.25)`
  - Critical / Fault: `#F43F5E`, glow aura `rgba(244, 63, 94, 0.3)`
  - Telemetry Accent: Electric Cyan `#06B6D4` and Hyper Violet `#6366F1`
  - Command Primary: `#2563EB` to `#3B82F6`
- **Typography & Content**:
  - Primary Telemetry & Readouts: `#F8FAFC`
  - Secondary Labels & Meta: `#94A3B8`
  - De-emphasized Code & Footnotes: `#64748B`

## Typography

The type ecosystem unifies three high-performance type families:
1. **Space Grotesk (Display & Section Headings)**: Infuses technical rigor and modern telemetry aesthetics without degrading legibility.
2. **Inter (Interface & Prose)**: Powers fast scannability across metadata, descriptions, tooltips, and system status context.
3. **JetBrains Mono (Telemetry & Payload Ledger)**: Serves as the bedrock for all tabular metrics, latencies, timestamps, hexadecimal identifiers, and live JSON traces. 

Tabular figures (`tnum`) and slashed zeros must be enabled globally on all numerical elements to prevent shifting layouts during real-time data streaming.

## Layout & Spacing

The layout is built for mission control density, relying on a 12-column fluid grid system across an ultra-wide desktop canvas (up to 1920px max-width) with compact gutters (`1rem` to `1.25rem`). 

- **Density Rules**: Components leverage compact vertical paddings (`space-sm` to `space-md`) to maximize vertical screen real estate, preserving visibility for dynamic graphs and dependency topologies simultaneously.
- **Breakpoint Dynamics**:
  - **Desktop (>1280px)**: Multi-panel horizontal telemetry strips, persistent sticky top status rail, split-view topology and metrics stream.
  - **Tablet (768px - 1279px)**: Topology and incident tables wrap into stacked cards; secondary stats scroll horizontally.
  - **Mobile (<768px)**: Strict 1-column emergency incident view; navigation switches to a compact command sheet drawer.

## Elevation & Depth

Visual hierarchy uses **tonal stacking with dark-mode hairline borders** rather than diffuse drop shadows, preserving tactical sharpness:

- **Level 0 (Backdrop)**: Pure obsidian void (`#080B10`) with an optional fine 32px radial grid mesh pattern at 3% opacity.
- **Level 1 (Panels & Cockpit Cards)**: `#111827` at 90% opacity with `backdrop-filter: blur(12px)` and a continuous hairline outline: `1px solid rgba(255, 255, 255, 0.08)`.
- **Level 2 (Active Tiles & Hover States)**: `#1E293B` elevated with a directional edge highlight: `inset 0 1px 0 0 rgba(255, 255, 255, 0.12)`.
- **Level 3 (Modal & Critical Overlays)**: `#0F172A` with a subtle cybernetic aura: `box-shadow: 0 0 30px rgba(0, 0, 0, 0.8), 0 0 1px 1px rgba(99, 102, 241, 0.3)`.

## Shapes

The interface utilizes a precision-milled radius scale:
- Metric stat HUD tiles, primary cards, and timeline windows utilize `0.5rem` (`rounded-md`).
- Status indicators, execution tags, and quick-action trigger pills use `rounded-full` or `rounded-sm` (`0.25rem`) to convey functional purpose.
- Interactive controls and input forms retain uniform `0.375rem` boundaries to mirror mechanical cockpit toggles.

## Components

### Buttons & Interactive Controls
- **Primary Command**: Vibrant `#2563EB` solid fill with white bold typography, subtle top bevel stroke (`rgba(255,255,255,0.2)`), and crisp hover scaling.
- **Chaos Injection Triggers**: Bordered in high-contrast contextual status colors (e.g., `#F59E0B` for Traffic Surge, `#F43F5E` for DB Deadlock) over dark `#1E293B` with hover glow.
- **Segmented Cockpit Tabs**: Pill-shaped grouped controls set on `#0F172A` backing. The active tab glows with primary blue fill and crisp white text.

### Badges, Status Dots & Indicators
- **Autonomous Pulse Node**: 8px circular status indicator featuring an ambient radial ping animation (`#10B981` with an outer ring fading to `opacity: 0`).
- **Telemetry Chips**: Monospaced micro-badges (`0.625rem` font size) with translucent background pills (`rgba(16, 185, 129, 0.12)`) and saturated text borders (`#10B981`).

### HUD Metric Cards
- Compact data blocks featuring small, uppercase tracking labels (`#94A3B8`), massive monospaced readout digits (`Space Grotesk` or `JetBrains Mono` in `#F8FAFC`), and an inline SLO threshold badge (`#64748B`).

### Incident Audit Ledger & Data Tables
- Continuous horizontal rows separated by `1px solid #1E293B`.
- Zero row striping; hover states reveal a translucent blue highlight (`rgba(37, 99, 235, 0.06)`).
- Monospaced timestamp and hex ID columns styled in `#64748B` and `#94A3B8`.

### Service Topology Nodes
- Deep-slate containers bordered with active health strokes (Green `#10B981`, Amber `#F59E0B`, Crimson `#F43F5E`).
- Flow arrows rendered in sharp dashed `#334155` vectors with directional pulsing pings.
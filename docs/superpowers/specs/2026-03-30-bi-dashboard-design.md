# Illini Intel — BI Dashboard Design

**Date:** 2026-03-30
**Scope:** Replace text-only BI report panel with a real visual dashboard

---

## Goal

The right panel of the dashboard should look and feel like a sports analytics tool — not a chatbot. All content is dynamic, driven by agent-fetched data, and works for any Illinois game across any season.

---

## Layout

Two-panel layout (unchanged):
- **Left panel:** Live agent trace — thoughts, tool calls, streaming in real time
- **Right panel:** BI report — visual components that populate as SSE events arrive

---

## Right Panel — Component Stack (top to bottom)

### 1. Team Header
Dynamic — populated from agent data, not hardcoded.
- Team names, AP rankings, game context (e.g. "Final Four", "Regular Season", "Big Ten Tournament")
- Illinois always on the left in orange, opponent on the right in their color (default blue if unknown)
- Live indicator dot while analysis is running

### 2. Hero Stats
Three big-number cards side by side:
- PPG (Illinois vs opponent)
- A second key stat (3PT% or FG% depending on what agent surfaces)
- Win probability (Illinois)

### 3. Category Bar Charts
Horizontal bar chart for each dimension the agent analyzes:
- Each bar shows Illinois % share of the matchup (orange = Illinois edge, blue = opponent edge)
- Categories stream in as the agent surfaces them — not a fixed list
- Legend: orange = Illinois edge, blue = opponent edge

### 4. Dimension Report Cards
2×N grid of grade cards (A+, A, B+, etc.) for each dimension:
- Offense, Defense, 3-Point, Pace, Rebounding, Turnovers — whatever the agent grades
- Each card shows the grade, a one-line explanation, and the key stat
- Cards stream in as the narrator emits them

### 5. Narrator Prediction
Pinned at the bottom — the full narrative prediction from the Narrator agent.
- Orange-accented card
- Free-form text, not structured

---

## New SSE Event Types

The existing `insight_card` (key-value only) is replaced/extended with richer structured events:

| Event | Payload | Renders as |
|-------|---------|------------|
| `team_header` | `{ illinois_rank, opponent_name, opponent_rank, game_context }` | Team header with rankings |
| `stat_comparison` | `{ label, illinois_value, opponent_value, illinois_pct }` | One bar in the category chart |
| `report_card` | `{ dimension, grade, stat, explanation }` | One card in the report card grid |
| `win_probability` | `{ probability, favored_team }` | Win prob hero number |
| `prediction` | `{ content }` | Narrator prediction (already exists) |
| `matchup_preview` | `{ content }` | Already exists, kept as-is |

Existing `agent_thought`, `tool_call`, `tool_result`, `done` events are unchanged.

---

## Narrator Tool Changes

The Narrator agent needs new tools to emit the structured events above:

- `emit_team_header(illinois_rank, opponent_name, opponent_rank, game_context)`
- `emit_stat_comparison(label, illinois_value, opponent_value, illinois_pct)`
- `emit_report_card(dimension, grade, stat, explanation)`
- `emit_win_probability(probability)`

The existing `generate_matchup_preview` and `generate_prediction` tools are kept.

---

## Frontend Changes

- Add `recharts` for bar charts
- Replace `InsightCard` (key-value grid) with new components:
  - `TeamHeader` — team names, rankings, game context, live dot
  - `StatComparisonChart` — accumulates `stat_comparison` events into a bar chart
  - `ReportCardGrid` — accumulates `report_card` events into grade cards
  - `WinProbability` — hero number card
- `BiReportPanel` renders these components in order as events arrive
- `StreamState` updated to hold structured data for each component

---

## Data Flow

```
Agent fetches data (Scout + Analyst)
      ↓
Narrator receives summaries
      ↓
Narrator calls emit_team_header → SSE → TeamHeader renders
Narrator calls emit_stat_comparison × N → SSE → bars stream in
Narrator calls emit_report_card × N → SSE → cards stream in
Narrator calls emit_win_probability → SSE → hero number updates
Narrator calls generate_prediction → SSE → prediction card renders
      ↓
done event → live indicator turns off
```

---

## Constraints

- All displayed data comes from agent SSE events — nothing hardcoded in the frontend
- Works for any Illinois game query, any season
- Components degrade gracefully if an event type isn't emitted (e.g. no AP ranking available)
- No charts render until data arrives — components appear as events stream in

# Lot7 Cost Estimate API — spec for Inspectagram integration

Draft handoff doc for IG's developer, matching the toggle flow already
mocked up at `C:\Users\Baz\Downloads\ig_embedded_costs_mockup.html`:
buyer/realtor flips "Show Cost Estimates — Powered by Lot7" inside the IG
report → IG calls Lot7 with its item list → Lot7 prices each item using
the same cost engine as the main Lot7 report → IG renders a cost badge
inline next to each finding (their page, their DOM). Toggle off = hidden.

## Why a live callback, not a data dump

We could batch-export Lot7's output and hand IG a file to import, but that
creates a staleness problem the moment either side's data changes. A
callback keeps it real-time; IG caches the response per report so
re-toggling is instant without a second network call.

## One cost engine, not a new one for this integration

This endpoint must price off the SAME source as the buyer dashboard and
the realtor report: `cost_lookup.py` (deterministic category ranges) with
the 3x range cap. No separate/looser prompt for this feature — that's how
Lot7's own numbers stayed consistent across surfaces, and it's the whole
reason IG can trust the badge matches what a buyer would see in the full
Lot7 report.

## Endpoint

```
POST https://api.lot7.ai/v1/cost-estimate/batch
```

### Auth
Header: `Authorization: Bearer <api_key>` — Lot7 issues IG a dedicated key
(separate from Lot7 end-user auth) so usage is metered/rate-limited per
partner.

### Request

IG sends its own report's item list. `item_id` is IG's own identifier —
opaque to Lot7, just echoed back so IG can match responses to DOM rows.

```json
{
  "report_id": "ig-uuid-optional-for-caching",
  "location": "Calgary, AB",
  "currency": "CAD",
  "items": [
    {
      "item_id": "garage-slab-crack",
      "finding": "Garage Slab — Large Crack",
      "section": "Garage",
      "severity": "attention"
    },
    {
      "item_id": "garage-drywall-slab",
      "finding": "Garage Drywall Too Close to Slab",
      "section": "Garage",
      "severity": "attention"
    }
  ]
}
```

Only `item_id` and `finding` are required per item. `section`, `severity`,
`location`, `currency` sharpen the match but degrade gracefully if
omitted.

### Response — `200 OK`

Matches the mockup's `[{item_id, most_likely, low, high}]` exactly, plus a
couple of fields IG's UI can optionally use:

```json
{
  "results": [
    {
      "item_id": "garage-slab-crack",
      "most_likely": 650,
      "low": 400,
      "high": 1200,
      "currency": "CAD",
      "trade": "Concrete/Foundation",
      "confidence": "matched"
    },
    {
      "item_id": "garage-drywall-slab",
      "most_likely": 500,
      "low": 300,
      "high": 900,
      "currency": "CAD",
      "trade": "General Contractor",
      "confidence": "matched"
    }
  ]
}
```

`most_likely` = midpoint of the range, rounded to nearest $50 — same
calculation the buyer dashboard already uses for budget totals, so a
number shown in IG matches what the same finding would show in Lot7.

`confidence`: `"matched"` (hit our cost_lookup table — tight, table-backed
range) or `"estimated"` (no clean table match, wider inferred range). IG
can visually distinguish these if useful, e.g. a lighter badge for
`"estimated"`.

Any `item_id` Lot7 can't price (empty/unusable `finding`) is simply
omitted from `results` — IG shows no badge for that row rather than the
call failing entirely.

### Errors

| Status | Meaning |
|---|---|
| 400 | Missing/empty `items` array |
| 401 | Bad or missing API key |
| 429 | Rate limit exceeded |
| 500 | Lot7-side failure — IG should hide the toggle/badges for this report, not block the page |

## Performance & caching

- Single batch call per report (per the mockup) — not one call per
  finding. A typical report is 10-40 items; keep this to one round trip.
- Target p95: under 2s for a full-report batch of table-matched items.
- IG caches the response per report (per the mockup's "cached per report
  so re-toggling is instant and consistent") — no need to re-call on
  toggle-off/on within the same session.
- Rate limit: propose 30 batch req/min per API key to start.

## Open questions for IG's developer

1. Where does IG assign `item_id` — is it stable across report views (so
   Lot7-side caching by `report_id` + `item_id` is safe), or regenerated
   per render?
2. Server-side render (IG's backend calls us) or client-side (browser
   calls us on toggle)? Server-side avoids exposing the API key to the
   browser — recommended.
3. Volume estimate — reports/day, average items/report — to size rate
   limits.
4. Does the realtor's standalone Lot7 report (separate flow, itemized
   issues with deep links back into the IG report) need this same
   endpoint, or does it stay entirely inside Lot7 since Lot7 already has
   the report text there? Currently built as a separate internal
   pipeline (`generate_realtor_issues_report` in Lot7's `utils.py`) that
   also uses `cost_lookup.py` — same engine, no shared network call
   needed since Lot7 already has the source text for that flow.

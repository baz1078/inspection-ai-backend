# Lot7 Cost Estimate API — spec for Inspectagram integration

Draft handoff doc for IG's developer, matching the toggle flow already
mocked up at `C:\Users\Baz\Downloads\ig_embedded_costs_mockup.html`:
buyer/realtor flips "Show Cost Estimates — Powered by Lot7" inside the IG
report → IG calls Lot7 with its item list → Lot7 prices each item using
the same cost engine as the main Lot7 report → IG renders a cost badge
inline next to each finding (their page, their DOM). Toggle off = hidden.

## Implementation status (updated July 19, 2026)

Shipped and verified end-to-end against live pricing calls: `POST
/v1/cost-estimate/batch` in `app.py`. Request/response shape matches this
spec exactly. **Not yet done:**
- Served on the same Flask app/domain, not yet on a dedicated `api.lot7.ai`
  subdomain — that's a later DNS/infra step, not a code change.
- Auth is a single shared key via `IG_COST_API_KEY` in `.env` (checked
  against `Authorization: Bearer <key>`) — no per-partner key issuance
  system yet since there's only one partner so far.
- Rate limiting (429, proposed 30 req/min) is NOT enforced — no
  Flask-Limiter/Redis in place. Fine for a single low-volume partner at
  launch; needs real enforcement before onboarding more partners or if IG
  sends unexpectedly high volume.

## Why a live callback, not a data dump

We could batch-export Lot7's output and hand IG a file to import, but that
creates a staleness problem the moment either side's data changes. A
callback keeps it real-time; IG caches the response per report so
re-toggling is instant without a second network call.

## One cost engine, not a new one for this integration

This endpoint prices off the SAME engine as the buyer dashboard and the
realtor report: `price_findings_with_ai()` in `utils.py` — a judgment-based
pricing pass anchored to `cost_lookup.py`'s category ranges, with the 3x
range cap enforced in code. Earlier drafts of this spec described a blind
`category_key -> cost_lookup.py` lookup; that was tried and dropped (see
`generate_realtor_issues_report`'s Pass 2 comment) because it had no way to
catch a finding whose wording coincidentally overlapped an unrelated
category — e.g. a Garage finding pricing itself off a Roof category. The
table is still the anchor (same low/high ranges, same trades), it's just
not a blind dictionary lookup anymore. No separate/looser prompt for this
feature — that's how Lot7's own numbers stay consistent across surfaces,
and it's the whole reason IG can trust the badge matches what a buyer
would see in the full Lot7 report. `confidence: "matched"` means the
model's price landed essentially on one of the table's categories;
`"estimated"` means it reasoned beyond the table.

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

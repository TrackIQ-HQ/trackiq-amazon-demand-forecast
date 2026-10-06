---
name: trackiq-amazon-demand-forecast
description: Turns trailing sales and last year's seasonal shape into a week-by-week demand forecast per Amazon product, then converts it into order quantities and order-by dates that account for lead time, safety stock and the service level the brand wants — with the forecast error stated so nobody treats it as certain. Use when the user asks how much to order, a demand forecast, a reorder plan, purchase order planning, safety stock, how much inventory to buy, or planning for a seasonal peak.
---

# Demand Forecast & Reorder Plan

`trackiq-restock-priority` answers *what is about to run out*. This answers the
harder question that comes next: **how much do we order, and by when?**

Forecast, then safety stock, then order quantity, then order date.

Output is a branded HTML report with a per-product order plan.

## Requires

- The TrackIQ MCP, for `list_marketplaces`, `get_product_performance` and
  `get_inventory_snapshot`.
- **A lead time** and **a service level** — ask for both. Defaults 45 days and
  95%, labelled assumptions.
- Nothing else. No filesystem, no shell, no internet.
  `assets/forecast.py` computes it if a shell is available; the method is in
  prose either way.
- **Without the MCP:** works from 13 months of weekly or monthly units by ASIN
  plus a current inventory export.

## First run

Fill in a copy of `assets/account.example.md` saved as account.md beside the
skill. Every TrackIQ skill reads the same file, so an account already set up
for another TrackIQ report needs nothing added here.

If the runtime has no filesystem, print the same block and ask the user to
paste it into their project instructions once.

## Read first

- `assets/pulls.md` — the calls, the seller/vendor branch, and how much history
  actually exists
- `assets/method.md` — the forecast, the error band, and the order arithmetic
- `assets/checks.md` — what to verify before anything is ordered

Copy `assets/report-template.html` and replace every `{{TOKEN}}`.

## Non-negotiables

1. **Branch on `account_type` before calling anything.** `list_marketplaces`
   returns `SELLER` or `VENDOR`. `get_vendor_forecasting` refuses on a seller
   account with an explicit error — *"This tool is for vendor accounts only"* —
   so check first rather than calling and handling the failure. Vendor accounts
   get Amazon's own forecast; seller accounts get the one derived here.
2. **No daily series exists.** `get_product_performance` silently ignores
   `granularity="daily"`. The weekly history is one call per week, over explicit
   ranges. Do not divide an aggregate.
3. **Say how much history was actually available.** A seasonal index from one
   prior year is a single observation, not a pattern. With less than 13 months,
   there is no seasonality — say so and forecast on the trailing level alone.
4. **Every forecast ships with its error.** State the mean absolute percentage
   error from a backtest on the history you have. A forecast without an error
   band gets treated as a fact and someone orders against it.
5. **Safety stock comes from forecast error, not from a rule of thumb.** The
   arithmetic is in `assets/method.md`. "Two weeks of cover" is not safety stock,
   it is a guess wearing a number.
6. **Roll up to ASIN.** Inventory and sales both arrive per SKU; ordering
   decisions are made per ASIN. See `trackiq-restock-priority` for why a per-SKU
   join fails in both directions at once.
7. **A promotion in the history is not demand.** A week with a Prime event or a
   deep coupon will inflate the level and the seasonal index. Ask about known
   promotions in the window and exclude or damp those weeks. Say which were.
8. **No MOQ, case pack or container logic.** The output is a quantity a buyer
   rounds. State that plainly beside every number.
9. **Nothing is ordered.** This is a plan a human turns into a purchase order.
10. **Never print `account_id`.**

## The honest ceiling

This is a trailing-level-plus-seasonality forecast, which is the right amount of
machinery for one brand's catalogue and no more. It will be wrong on new
products, on products whose price changed materially, and on anything driven by
a promotion calendar it cannot see.

Say that on the report. A forecast that claims more than it can do is how a
brand ends up with a warehouse full of the wrong thing.

## What it pairs with

`trackiq-restock-priority` is the weekly triage; this is the quarterly plan. Run
restock every Monday and this once a quarter, or before a season.
`trackiq-excess-inventory` is what happens when this one is too optimistic.

## Delivery

The output is produced in the chat first. Delivery is the last step and the
method comes from the Delivery block in account.md — never ask per run.

| Method | What to do | Needs |
|---|---|---|
| `in-chat` | Return the report. The default, and the fallback for every other method. | nothing |
| `file` | Write it beside the skill, dated. | a filesystem |
| `slack` | Post the headline findings as text, then upload the file. | a connected Slack tool |
| `n8n` | POST it to the configured webhook. | network access |
| `email` | Hand it to the connected mail tool. | a connected mail tool |

Confirm before the first outward send of a session, fall back to in-chat
loudly when a method is unavailable, and never substitute a different
outward channel.

## Version

`trackiq-amazon-demand-forecast` v1.0.0 (2026-09-18).

If the user asks whether this skill is current, fetch
`https://trackiq.com/skills/registry.json`, compare the `version` field for
`trackiq-amazon-demand-forecast`, and if it is newer, give them the download link and
the one-line changelog. Do not fetch at any other time.

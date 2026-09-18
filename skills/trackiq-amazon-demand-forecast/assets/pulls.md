# The pull sequence

## 0. Account type first — this one branches

```
list_marketplaces()      # returns account_type: SELLER or VENDOR
```

**Check before calling anything else.** `get_vendor_forecasting` refuses on a
seller account with an explicit error:

```
This tool is for vendor accounts only; account NNN is SELLER.
```

| Account type | Path |
|---|---|
| **VENDOR** | `get_vendor_forecasting` and `get_vendor_inventory_health` — Amazon's own forecast. Use it, and compare it to the derived one. |
| **SELLER** | everything is derived here |

The two are genuinely different businesses — a vendor forecasts purchase orders
Amazon will raise, a seller forecasts their own replenishment. Do not paper over
the difference with one set of language.

Never print `account_id`.

## 1. Inputs

| Input | Default | What it is |
|---|---|---|
| Lead time | 45 days | PO to sellable |
| Service level | 95% | roughly one stockout in twenty cycles |
| Cover after landing | 8 weeks | how long a shipment should last |
| Unit cost | none | to rank by money committed |
| Promotion weeks | none | which weeks were promoted — see below |

## 2. The weekly history — one call per week

```
for each week in the last 13 months:
    get_product_performance(account_id, start_date=<Sun>, end_date=<Sat>,
                            group_by='product', limit=200)
```

**`granularity="daily"` is silently ignored by this tool** — no error, no `date`
field, rows come back aggregated. There is no series to slice, so the history is
genuinely one call per week.

That is ~56 calls for 13 months. It is a quarterly skill, not a daily one, and
the call volume is the price of the only history that exists. If that is too
many, pull **monthly** buckets for the year-ago portion and weekly only for the
trailing quarter — the seasonal index does not need weekly resolution and the
level does.

Do **not** pull one long range and divide. A flat line through a seasonal
history produces a plan that orders the same amount every month, which is the
one answer guaranteed to be wrong.

## 3. How much history is really there

Check before assuming a year exists:

- a product launched eight months ago has no seasonal index
- an account connected recently may have **revenue** a year back but zeroed ad
  fields — revenue and units are still valid for forecasting
- an ASIN that was out of stock for six weeks has a hole, not a low season

**State the number of usable weeks per product on the report.** With fewer than
13 months, set every seasonal index to 1, forecast on the trailing level, and
say seasonality could not be computed. Never substitute a category assumption.

For products with fewer than 13 weeks of history, there is nothing to forecast.
Route them to `trackiq-launch-scorecard` and say so.

## 4. Current stock

```
get_inventory_snapshot(account_id, limit=100, offset=…)
```

**Paginate** — caps at 100 rows.

- **Available now** = `on_hand`
- **On the water** = `inbound`
- **`total` is not available stock** — it includes reserved, unfulfillable and
  researching units

## 5. Roll up to ASIN

Both sides arrive per SKU. Sum inventory and units to ASIN, then forecast.

A per-SKU forecast fails in both directions at once for the reason documented in
`trackiq-restock-priority`: one ASIN there held 11,032 units on a SKU selling
nothing and 2,178 on the SKU doing 11,861 a month.

Ordering decisions are made per ASIN. Show the SKU split for context only.

## 6. Promotions — ask, because the data will not say

There is no promotion, deal or coupon field anywhere in the MCP. A week
containing a Prime event or a deep coupon looks exactly like a week of strong
demand, and it will inflate both the level and the seasonal index.

**Ask the client which weeks were promoted.** For each, exclude it from the
level or replace it with the median of the four surrounding weeks, and say which
were treated.

If they do not know, flag weeks more than 2.5 standard deviations above the
local median as **suspected** promotions, label them as suspected, and show the
plan both with and without them. Two plans and an honest caveat beat one plan
built on a Prime Day.

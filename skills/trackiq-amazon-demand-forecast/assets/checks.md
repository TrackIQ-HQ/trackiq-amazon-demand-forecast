# Before you send it

## 1. The account branch

- `list_marketplaces` was called and `account_type` checked **before** any
  vendor tool.
- Vendor accounts use `get_vendor_forecasting`; seller accounts use the derived
  forecast. The report says which.
- On a vendor account, Amazon's forecast and the derived one are **both shown**
  where they disagree. A large gap is a finding, not an error to hide.

## 2. The history is real

- **One call per week** (or per month for the year-ago portion). No week came
  from dividing a long aggregate.
- **Usable weeks are stated per product.**
- Products with fewer than 13 months have **every seasonal index set to 1**, and
  the report says seasonality could not be computed.
- Products with fewer than 13 weeks are routed to `trackiq-launch-scorecard`,
  not forecast.
- An out-of-stock stretch is described as a hole, not read as low season.

## 3. The forecast ships with its error

- **Every product has a MAPE from a backtest**, and it is on the page.
- Where there was not enough history to backtest, the report says the forecast
  is untested rather than showing a blank.
- Products with a MAPE above about 60% are labelled not forecastable, with the
  recommendation to order on the trailing rate and a wider buffer.
- The seasonal damping and clamp values are stated.

## 4. Safety stock

- Derived from **forecast error**, not from a cover rule.
- The service level is stated **and explained** — 95% means one stockout in
  twenty cycles, not 95% of days in stock.
- The square root of lead weeks was used, not the lead time itself. Sanity
  check: doubling the lead time must **not** double the safety stock.

## 5. Promotions

- The client was asked which weeks were promoted.
- Treated weeks are listed, with how they were treated.
- Where promotions were only suspected, they are labelled suspected and the plan
  is shown **both ways**.

## 6. The order plan

- Rolled up to **ASIN**. No per-SKU order quantity.
- No negative quantities.
- Stock consumption is walked against the **forecast**, not a flat average.
- `order_by` dates in the past are flagged **overdue**, with the arithmetic
  beside them.
- Every quantity carries the line that it contains no MOQ, case pack or
  container fill.
- Ranked by money committed, with overdue first.

## 7. The ceiling is stated

- The report says plainly that this is a trailing-level-plus-seasonality
  forecast and names what it will be wrong about: new products, price changes,
  and a promotion calendar it cannot see.
- Nothing on the page implies more precision than a MAPE of that size supports.

Run `python assets/forecast.py` with no arguments; its self-check must pass.

## 8. Sanity

- Total units to order is plausible against the catalogue's annual volume. More
  than about half a year of total units means the lead time, the cover or a
  seasonal index is wrong.
- No product's forecast peak exceeds 2.5x its trailing level — that is the clamp
  and it should be visible in the numbers.
- The sum of ordered value is a number the client could actually pay.

## 9. Render check

```js
({ overflows: document.documentElement.scrollWidth > document.documentElement.clientWidth,
   tables: document.querySelectorAll('table').length,
   rows: [...document.querySelectorAll('table')].map(t => t.querySelectorAll('tbody tr').length),
   logos: [...document.images].map(i => i.naturalWidth > 0),
   tokens: (document.body.innerHTML.match(/\{\{[A-Z0-9_]+\}\}/g) || []).length,
   // every forecast row must carry an error figure
   mape: document.querySelectorAll('[data-mape]').length })
```

`overflows` false, `logos` all true, `tokens` zero, and `mape` equal to the
number of forecast rows. Then look at it; if it will not paint, say the check
was structural.

## 10. Ship

Save as `<client>-demand-forecast-<YYYY-MM-DD>.html`.

Lead with the overdue orders and the total money the plan commits. A buyer needs
to know what to sign before they read a forecast.

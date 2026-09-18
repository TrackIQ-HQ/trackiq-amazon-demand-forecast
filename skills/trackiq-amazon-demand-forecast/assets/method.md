# Method

## The forecast

Trailing level times a seasonal index. That is the whole model, and for one
brand's catalogue it is the right amount of machinery.

```
level      = mean(units per week over the last 8 weeks)
index[w]   = units in week w last year / mean(units per week last year)
forecast[w] = level x index[w]                      # w = each future week
```

**Damp the index.** A single prior year is one observation, not a pattern, and a
raw index of 3.4 will order three times too much on the strength of one Prime
Day:

```
index[w] = 1 + damping x (raw_index[w] - 1)          # damping = 0.7 default
index[w] = clamp(index[w], 0.4, 2.5)
```

Both numbers are defaults. State them.

**With fewer than 13 months of history there is no seasonality.** Set every
index to 1, forecast on the level alone, and say on the report that seasonality
could not be computed. Do not substitute a category assumption — that is
inventing data.

## The error band, from a backtest

Never ship a forecast without its error.

```
# hold out the last 8 weeks, forecast them from what came before, compare
for each held-out week:
    ape = abs(actual - predicted) / actual          # skip weeks with zero actual
mape = mean(ape)
```

Report the MAPE per product and for the catalogue. It is the number that tells a
buyer how much to trust the plan, and it feeds the safety stock directly.

A MAPE above about 60% means the product is not forecastable by this method.
**Say so and recommend ordering on the trailing rate with a wider buffer**,
rather than dressing a bad forecast in arithmetic.

## Safety stock — from error, not from habit

"Two weeks of cover" is not safety stock, it is a guess with a unit attached.
Safety stock exists to absorb forecast error over the lead time:

```
sigma_weekly = stdev(actual - predicted) over the backtest weeks
lead_weeks   = lead_time_days / 7
z            = 1.65 for 95% service, 1.28 for 90%, 2.33 for 99%

safety_stock = z x sigma_weekly x sqrt(lead_weeks)
```

The square root is there because errors over successive weeks partly cancel;
multiplying by the lead time instead over-orders badly on long lead times.

State the service level and what it means: 95% means roughly one stockout in
twenty replenishment cycles, not 95% of days in stock.

## The order quantity

```
demand_over_horizon = sum(forecast[w] for w in the next lead_weeks + cover_weeks)
order_qty = demand_over_horizon + safety_stock - on_hand - inbound
order_qty = max(0, order_qty)
```

`cover_weeks` defaults to 8 — how long the shipment should last after it lands.

**This is a quantity a buyer rounds.** No MOQ, no case pack, no pallet or
container fill, no supplier price breaks. Say that beside the number, every
time.

## The order-by date

```
weeks_of_stock = (on_hand + inbound) consumed against the forecast,
                 week by week, until it reaches safety_stock
runs_low       = today + that many weeks
order_by       = runs_low - lead_time
```

Consume against the **forecast**, not against a flat average. That is the whole
reason to forecast: a product entering its season runs out sooner than its
trailing rate suggests, and that is precisely when getting the order date wrong
is expensive.

`order_by` in the past is **overdue**. Flag it, show the arithmetic beside it,
and do not quietly print a past date as if it were a plan.

## Promotions poison the history

A week containing a Prime event, a lightning deal or a deep coupon is not demand
— it is demand plus a discount. Left in, it inflates both the level and the
seasonal index, and the plan orders for a promotion that is not happening again.

**Ask the client which weeks had promotions.** For each:

- exclude it from the `level` calculation, or
- replace it with the median of the surrounding four weeks

State which weeks were treated and how. If the client does not know, flag weeks
more than 2.5 standard deviations above the local median as suspected
promotions, say they are suspected, and show the plan both ways.

## Ranking the output

By **units to order x unit cost** if cost is known, otherwise by units x price.
A buyer works a purchase order in order of money committed, not alphabetically.

Overdue orders come first regardless.

## What this skill does not do

- **No causal model.** Price, advertising and competitor behaviour are not
  inputs. A product whose price changed materially will forecast badly and the
  report should say which ones those are if the client knows.
- **No new products.** Under 13 weeks of history, there is nothing to forecast.
  Route those to `trackiq-launch-scorecard`.
- **No supplier logic.** No MOQ, case pack, container fill or price breaks.
- **Nothing is ordered.**

"""Weekly demand forecast, safety stock and order quantity.

An accelerant, never a dependency. The method is in assets/method.md and is
short enough to do by hand; this exists so the backtest is not skipped.

Run with no arguments for the self-check:  python forecast.py
"""
import json
import math
import statistics as st
import sys

Z = {90: 1.28, 95: 1.65, 99: 2.33}


def seasonal_index(last_year, damping=0.7, lo=0.4, hi=2.5):
    """Damped weekly index from one prior year. Flat 1.0 when there is no year."""
    if not last_year or sum(last_year) == 0:
        return None
    mean = sum(last_year) / len(last_year)
    if mean == 0:
        return None
    return [min(hi, max(lo, 1 + damping * (v / mean - 1))) for v in last_year]


def level(history, weeks=8):
    """Trailing level. Uses what exists when the history is shorter."""
    recent = history[-weeks:]
    return sum(recent) / len(recent) if recent else 0.0


def forecast(history, index, horizon):
    """level x index, walking the index forward and wrapping at the year."""
    lv = level(history)
    if not index:
        return [lv] * horizon
    start = len(history) % len(index)
    return [lv * index[(start + i) % len(index)] for i in range(horizon)]


def backtest(history, index, holdout=8):
    """MAPE and the error sigma, from forecasting the last `holdout` weeks.

    Returns (mape, sigma). Both None when there is not enough history to test —
    which the report must then say, rather than showing a forecast with no error.
    """
    if len(history) < holdout * 2:
        return None, None
    train, actual = history[:-holdout], history[-holdout:]
    pred = forecast(train, index, holdout)
    apes = [abs(a - p) / a for a, p in zip(actual, pred) if a > 0]
    errs = [a - p for a, p in zip(actual, pred)]
    mape = sum(apes) / len(apes) if apes else None
    sigma = st.pstdev(errs) if len(errs) > 1 else None
    return mape, sigma


def safety_stock(sigma, lead_days, service=95):
    """z x sigma x sqrt(lead weeks). Errors partly cancel across weeks, so sqrt."""
    if sigma is None:
        return None
    return Z[service] * sigma * math.sqrt(lead_days / 7.0)


def order_plan(history, last_year, on_hand, inbound, lead_days,
               cover_weeks=8, service=95):
    idx = seasonal_index(last_year)
    lead_weeks = lead_days / 7.0
    horizon = int(math.ceil(lead_weeks + cover_weeks))
    fc = forecast(history, idx, horizon)
    mape, sigma = backtest(history, idx)
    ss = safety_stock(sigma, lead_days, service) or 0.0

    qty = max(0, round(sum(fc) + ss - on_hand - inbound))

    # Weeks until the forecast eats the stock down to the safety level. Strictly
    # below, not at: a week that lands exactly on the safety level was covered.
    stock, weeks = on_hand + inbound, 0
    for w in fc:
        if stock - w < ss:
            break
        stock -= w
        weeks += 1

    return dict(order_qty=qty,
                weeks_of_stock=weeks,
                order_by_weeks=round(weeks - lead_weeks, 1),
                overdue=weeks < lead_weeks,
                safety_stock=round(ss),
                mape=round(mape, 3) if mape is not None else None,
                seasonal=idx is not None,
                forecast=[round(v, 1) for v in fc])


def demo():
    flat = [100] * 60
    p = order_plan(flat, None, on_hand=400, inbound=0, lead_days=28)
    assert p["seasonal"] is False, "no prior year means no seasonality"
    assert p["mape"] is not None and p["mape"] < 0.01, "flat demand must forecast exactly"
    # 4 weeks lead + 8 weeks cover = 12 weeks x 100 = 1200, less 400 on hand.
    assert 790 <= p["order_qty"] <= 810, p["order_qty"]
    assert p["weeks_of_stock"] == 4, p["weeks_of_stock"]
    assert p["overdue"] is False

    # Stock already below the lead time: must read as overdue.
    p = order_plan(flat, None, on_hand=100, inbound=0, lead_days=56)
    assert p["overdue"] is True, "one week of stock against an eight-week lead is overdue"

    # A seasonal year must lift the index and be damped below the raw ratio.
    year = [50] * 39 + [200] * 13          # a Q4 peak
    idx = seasonal_index(year)
    raw_peak = 200 / (sum(year) / len(year))
    assert max(idx) < raw_peak, "the index must be damped below the raw ratio"
    assert max(idx) <= 2.5 and min(idx) >= 0.4, "the index must be clamped"

    # Safety stock must grow with the service level and with the lead time.
    assert safety_stock(10, 28, 99) > safety_stock(10, 28, 95) > safety_stock(10, 28, 90)
    assert safety_stock(10, 56) > safety_stock(10, 28)
    # ...but less than linearly. Doubling the lead time must not double the buffer.
    assert safety_stock(10, 56) < 2 * safety_stock(10, 28)

    # Short history: no backtest, and the report must be told so.
    assert backtest([100] * 10, None) == (None, None)

    # Never a negative order.
    assert order_plan(flat, None, on_hand=99999, inbound=0, lead_days=28)["order_qty"] == 0
    print("self-check passed")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        print(json.dumps(order_plan(**json.load(open(sys.argv[1], encoding="utf-8"))), indent=2))
    else:
        demo()

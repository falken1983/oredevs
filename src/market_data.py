"""
market_data.py
--------------
Provides sample EUR market data for Hull-White calibration:
  - EUR discount curve (flat at ~3%)
  - Caplet (optionlet) volatilities — Black Normal (Bachelier), flat at ~60 bps
"""

import QuantLib as ql


def get_eur_yield_curve_handle(
    rate: float = 0.03,
    day_count: ql.DayCounter = None,
    calendar: ql.Calendar = None,
    settlement_date: ql.Date = None,
) -> ql.YieldTermStructureHandle:
    """
    Return a QuantLib YieldTermStructureHandle backed by a flat EUR forward
    curve at the given rate.

    Parameters
    ----------
    rate : float
        Continuously-compounded flat rate (default 3 %).
    day_count : ql.DayCounter
        Day-count convention (default Actual/365 Fixed).
    calendar : ql.Calendar
        Calendar used for business-day adjustments (default TARGET).
    settlement_date : ql.Date
        Curve reference date; if None, uses the global evaluation date.

    Returns
    -------
    ql.YieldTermStructureHandle
    """
    if day_count is None:
        day_count = ql.Actual365Fixed()
    if calendar is None:
        calendar = ql.TARGET()
    if settlement_date is None:
        settlement_date = ql.Settings.instance().evaluationDate

    flat_curve = ql.FlatForward(
        settlement_date,
        ql.QuoteHandle(ql.SimpleQuote(rate)),
        day_count,
        ql.Continuous,
        ql.Annual,
    )
    return ql.YieldTermStructureHandle(flat_curve)


def get_caplet_vol_handle(
    vol: float = 0.0060,
    day_count: ql.DayCounter = None,
    calendar: ql.Calendar = None,
    settlement_date: ql.Date = None,
) -> ql.OptionletVolatilityStructureHandle:
    """
    Return a QuantLib OptionletVolatilityStructureHandle backed by a flat
    Black Normal (Bachelier) constant volatility surface.

    Volatilities are expressed in absolute rate terms (e.g. 0.0060 = 60 bps),
    as is standard for EUR caplets quoted in the Normal convention.

    Parameters
    ----------
    vol : float
        Flat Normal (Bachelier) caplet vol in rate units (default 60 bps).
    day_count : ql.DayCounter
        Day-count convention (default Actual/365 Fixed).
    calendar : ql.Calendar
        Calendar used for date adjustments (default TARGET).
    settlement_date : ql.Date
        Reference date; if None, uses the global evaluation date.

    Returns
    -------
    ql.OptionletVolatilityStructureHandle
    """
    if day_count is None:
        day_count = ql.Actual365Fixed()
    if calendar is None:
        calendar = ql.TARGET()
    if settlement_date is None:
        settlement_date = ql.Settings.instance().evaluationDate

    constant_vol = ql.ConstantOptionletVolatility(
        settlement_date,
        calendar,
        ql.ModifiedFollowing,
        ql.QuoteHandle(ql.SimpleQuote(vol)),
        day_count,
        ql.Normal,  # Black Normal (Bachelier) convention
    )
    return ql.OptionletVolatilityStructureHandle(constant_vol)

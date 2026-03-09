"""
main.py
-------
Entry point for the Hull-White model calibration.

Usage
-----
    python -m arc.main
or
    python arc/main.py
"""

import QuantLib as ql

from arc.market_data import get_eur_yield_curve_handle, get_caplet_vol_handle
from arc.hull_white_calibrator import HullWhiteCalibrator


def main() -> None:
    # ---------------------------------------------------------------
    # 1. Set the global QuantLib evaluation date
    # ---------------------------------------------------------------
    today = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = today
    print(f"Evaluation date : {today}")

    # ---------------------------------------------------------------
    # 2. Load market data
    # ---------------------------------------------------------------
    yield_curve = get_eur_yield_curve_handle(rate=0.03)
    caplet_vols = get_caplet_vol_handle(vol=0.20)
    print("EUR yield curve  : flat 3 %")
    print("Caplet flat vol  : 20 %")

    # ---------------------------------------------------------------
    # 3. Calibrate
    # ---------------------------------------------------------------
    mean_reversion = 0.10
    calibrator = HullWhiteCalibrator(yield_curve, caplet_vols)
    result = calibrator.calibrate(mean_reversion=mean_reversion)

    # ---------------------------------------------------------------
    # 4. Report results
    # ---------------------------------------------------------------
    print("\n--- Hull-White calibration results ---")
    print(f"  a     (mean reversion) : {result['a']:.6f}")
    print(f"  sigma (volatility)     : {result['sigma']:.6f}")
    print(f"  RMS calibration error  : {result['error']:.6e}")


if __name__ == "__main__":
    main()

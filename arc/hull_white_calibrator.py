"""
hull_white_calibrator.py
------------------------
Calibrates a Hull-White 1-factor model to caplet/cap market data using
QuantLib.

The standard approach is:
  - Fix the mean-reversion speed ``a`` (or pass it in).
  - Optimise the volatility parameter ``sigma`` to reproduce observed
    caplet implied volatilities.
"""

import QuantLib as ql


class HullWhiteCalibrator:
    """
    Calibrate a Hull-White 1-factor short-rate model to cap/caplet data.

    Parameters
    ----------
    yield_curve_handle : ql.YieldTermStructureHandle
        EUR discount curve used both for pricing and as the model's term
        structure.
    vol_handle : ql.OptionletVolatilityStructureHandle
        Flat or surface caplet volatility structure.
    """

    _CAP_TENORS = ["1Y", "2Y", "3Y", "4Y", "5Y", "7Y", "10Y"]
    _DAY_COUNT = ql.Actual365Fixed()
    _IBOR_TENOR = ql.Period(6, ql.Months)

    def __init__(
        self,
        yield_curve_handle: ql.YieldTermStructureHandle,
        vol_handle: ql.OptionletVolatilityStructureHandle,
    ) -> None:
        self._yield_curve = yield_curve_handle
        self._vol_handle = vol_handle

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def calibrate(self, mean_reversion: float = 0.10) -> dict:
        """
        Calibrate the Hull-White model.

        The mean-reversion parameter ``a`` is fixed to *mean_reversion*.
        The volatility ``sigma`` is optimised to minimise the squared
        difference between model and market cap prices.

        Parameters
        ----------
        mean_reversion : float
            Hull-White mean-reversion speed ``a`` (default 0.10).

        Returns
        -------
        dict with keys:
            ``a``      – calibrated (fixed) mean-reversion speed
            ``sigma``  – calibrated short-rate volatility
            ``error``  – root-mean-square calibration error in vol units
        """
        model = ql.HullWhite(self._yield_curve)

        # Initialise 'a' to the supplied mean-reversion value so it is fixed
        # at that level during optimisation.  ql.HullWhite parameter order:
        # [a, sigma].  Passing fixParameters=[True, False] keeps 'a' fixed
        # and lets the optimiser adjust 'sigma' only.
        model.setParams(ql.Array([mean_reversion, model.params()[1]]))

        helpers = self._build_helpers(model)

        optimization_method = ql.LevenbergMarquardt()
        end_criteria = ql.EndCriteria(1000, 100, 1e-8, 1e-8, 1e-8)

        model.calibrate(
            helpers,
            optimization_method,
            end_criteria,
            ql.NoConstraint(),
            [],           # per-helper weights (empty = uniform)
            [True, False],  # True=fixed for a, False=free for sigma
        )

        params = model.params()
        calibrated_a = params[0]
        calibrated_sigma = params[1]

        rms_error = self._rms_error(helpers)

        return {
            "a": calibrated_a,
            "sigma": calibrated_sigma,
            "error": rms_error,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_helpers(self, model: ql.HullWhite) -> list:
        """Build CapHelper objects for each cap tenor."""
        calendar = ql.TARGET()
        settlement_date = ql.Settings.instance().evaluationDate
        helpers = []

        for tenor_str in self._CAP_TENORS:
            tenor = ql.Period(tenor_str)
            expiry_date = calendar.advance(
                settlement_date, tenor, ql.ModifiedFollowing
            )
            atm_vol = self._vol_handle.currentLink().volatility(
                expiry_date, 0.03, True
            )
            vol_quote = ql.QuoteHandle(ql.SimpleQuote(atm_vol))

            ibor_index = ql.Euribor6M(self._yield_curve)

            helper = ql.CapHelper(
                tenor,
                vol_quote,
                ibor_index,
                ql.Annual,
                self._DAY_COUNT,
                True,  # include first caplet
                self._yield_curve,
                ql.CapHelper.RelativePriceError,
            )
            engine = ql.AnalyticCapFloorEngine(model, self._yield_curve)
            helper.setPricingEngine(engine)
            helpers.append(helper)

        return helpers

    @staticmethod
    def _rms_error(helpers: list) -> float:
        """Root-mean-square calibration error across helpers."""
        if not helpers:
            return 0.0
        sse = sum(h.calibrationError() ** 2 for h in helpers)
        return (sse / len(helpers)) ** 0.5

"""
test_hull_white_calibrator.py
-----------------------------
Unit tests for HullWhiteCalibrator.
"""

import unittest
import QuantLib as ql

from src.market_data import get_eur_yield_curve_handle, get_caplet_vol_handle
from src.hull_white_calibrator import HullWhiteCalibrator


class TestHullWhiteCalibrator(unittest.TestCase):
    """Tests that calibration runs and returns sensible parameters."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up a fixed evaluation date and shared market data."""
        cls.today = ql.Date(9, ql.March, 2026)
        ql.Settings.instance().evaluationDate = cls.today

        cls.yield_curve = get_eur_yield_curve_handle(rate=0.03)
        # Normal (Bachelier) vol: 60 bps
        cls.caplet_vols = get_caplet_vol_handle(vol=0.0060)

    def _make_calibrator(self) -> HullWhiteCalibrator:
        return HullWhiteCalibrator(self.yield_curve, self.caplet_vols)

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_calibrate_returns_dict_with_expected_keys(self) -> None:
        result = self._make_calibrator().calibrate(mean_reversion=0.10)
        self.assertIn("a", result)
        self.assertIn("sigma", result)
        self.assertIn("error", result)

    def test_mean_reversion_is_fixed(self) -> None:
        fixed_a = 0.05
        result = self._make_calibrator().calibrate(mean_reversion=fixed_a)
        self.assertAlmostEqual(result["a"], fixed_a, places=6)

    def test_sigma_is_positive(self) -> None:
        result = self._make_calibrator().calibrate(mean_reversion=0.10)
        self.assertGreater(result["sigma"], 0.0)

    def test_calibration_error_is_non_negative(self) -> None:
        result = self._make_calibrator().calibrate(mean_reversion=0.10)
        self.assertGreaterEqual(result["error"], 0.0)

    def test_different_mean_reversions_give_different_sigma(self) -> None:
        result_low = self._make_calibrator().calibrate(mean_reversion=0.01)
        result_high = self._make_calibrator().calibrate(mean_reversion=0.50)
        # sigma values should differ when a changes
        self.assertNotAlmostEqual(result_low["sigma"], result_high["sigma"], places=4)

    def test_market_data_yield_curve_is_handle(self) -> None:
        handle = get_eur_yield_curve_handle(rate=0.03)
        self.assertIsInstance(handle, ql.YieldTermStructureHandle)
        # Verify the curve is usable by computing a discount factor
        discount = handle.discount(ql.Date(9, ql.March, 2027))
        self.assertGreater(discount, 0.0)
        self.assertLess(discount, 1.0)

    def test_market_data_vol_handle_is_normal(self) -> None:
        handle = get_caplet_vol_handle(vol=0.0060)
        self.assertIsInstance(handle, ql.OptionletVolatilityStructureHandle)
        # Verify the surface returns the correct Normal vol value (60 bps)
        vol = handle.currentLink().volatility(
            ql.Date(9, ql.March, 2027), 0.03, True
        )
        self.assertAlmostEqual(vol, 0.0060, places=6)
        # Normal vols are small absolute values (bps range), not percentages
        self.assertLess(vol, 0.05)


if __name__ == "__main__":
    unittest.main()

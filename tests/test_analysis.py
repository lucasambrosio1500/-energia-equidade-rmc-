import unittest
import numpy as np
import pandas as pd
from energia_equidade.analysis import annualize, parse_decimal, association, municipal_summary


def fixture():
    return pd.DataFrame([{"cnpj": "001", "set_id": "1", "year": 2022, "month": m,
                          "indicator": i, "value": value}
                         for m in range(1, 13) for i, value in [("DEC", 1.), ("FEC", .5), ("NumCon", 100.)]])


class EngineeringTests(unittest.TestCase):
    def test_constant_consumers_known_result(self):
        a = annualize(fixture()).iloc[0]
        self.assertTrue(a.complete)
        self.assertAlmostEqual(a.dec_h, 12.)
        self.assertAlmostEqual(a.fec_n, 6.)

    def test_changing_consumers_requires_weighting(self):
        x = fixture()
        x.loc[(x.month == 12) & x.indicator.eq("NumCon"), "value"] = 200
        x.loc[(x.month == 12) & x.indicator.eq("DEC"), "value"] = 4
        a = annualize(x).iloc[0]
        self.assertAlmostEqual(a.dec_h, 1900 / (1300 / 12))
        self.assertNotAlmostEqual(a.dec_h, a.dec_sum)

    def test_missing_month_is_not_zero(self):
        a = annualize(fixture().query('month != 6')).iloc[0]
        self.assertFalse(a.complete)
        self.assertEqual(a.months_complete, 11)
        self.assertNotIn("dec_h", a.index)

    def test_missing_one_indicator_invalidates_year(self):
        x = fixture()
        a = annualize(x[~(x.month.eq(6) & x.indicator.eq("FEC"))]).iloc[0]
        self.assertFalse(a.complete)
        self.assertEqual(a.months_observed, 12)

    def test_duplicate_rejected(self):
        x = fixture()
        with self.assertRaises(ValueError): annualize(pd.concat([x, x.iloc[:1]]))

    def test_period_13_rejected(self):
        x = fixture(); x.loc[0, "month"] = 13
        with self.assertRaises(ValueError): annualize(x)

    def test_negative_rejected(self):
        x = fixture(); x.loc[0, "value"] = -1
        with self.assertRaises(ValueError): annualize(x)

    def test_nonfinite_rejected(self):
        x = fixture(); x.loc[0, "value"] = np.inf
        with self.assertRaises(ValueError): annualize(x)

    def test_zero_consumers_invalidates(self):
        x = fixture(); x.loc[x.indicator.eq("NumCon") & x.month.eq(3), "value"] = 0
        self.assertFalse(annualize(x).iloc[0].complete)

    def test_zero_outage_is_valid(self):
        x = fixture(); x.loc[x.indicator.isin(["DEC", "FEC"]), "value"] = 0
        a = annualize(x).iloc[0]
        self.assertTrue(a.complete); self.assertEqual(a.dec_h, 0)

    def test_decimal_comma(self):
        self.assertEqual(parse_decimal(pd.Series([",08", " 12,35 "])).tolist(), [.08, 12.35])

    def test_unknown_decimal_is_error(self):
        with self.assertRaises(ValueError): parse_decimal(pd.Series(["-"]))

    def test_correlation_and_leave_one_out(self):
        d = pd.DataFrame({"income_mean": [1,2,3,4,5], "dec_median": [5,4,3,2,1]})
        result = association(d)
        self.assertAlmostEqual(result["rho"], -1)
        self.assertAlmostEqual(result["loo_max"], -1)

    def test_constant_correlation_not_reported(self):
        d = pd.DataFrame({"income_mean": [1,1,1,1], "dec_median": [1,2,3,4]})
        self.assertIsNone(association(d)["rho"])

    def test_shared_set_degree_is_national(self):
        annual = pd.DataFrame({"set_id": ["1", "2"], "year": [2022,2022], "complete": [True,True],
                               "dec_h": [4.,8.], "fec_n": [2.,3.], "dec_sum": [4.,8.], "dec_limit_ratio": [.5,1.]})
        cw = pd.DataFrame({"set_id": ["1","1","2"], "municipality_id": ["A","OUTSIDE_RMC","A"]})
        inc = pd.DataFrame({"municipality_id": ["A"], "income_mean": [1000]})
        all_rows, _ = municipal_summary(annual,cw,inc)
        exclusive, _ = municipal_summary(annual,cw,inc,exclusive=True)
        self.assertEqual(all_rows.iloc[0].dec_median, 6)
        self.assertEqual(all_rows.iloc[0].n_shared, 1)
        self.assertEqual(exclusive.iloc[0].dec_median, 8)

    def test_ambiguous_agent_mapping_is_error(self):
        annual = pd.DataFrame({"set_id": ["1","1"], "year": [2022,2022], "complete": [True,True]})
        cw = pd.DataFrame({"set_id": ["1"], "municipality_id": ["A"]})
        with self.assertRaises(ValueError): municipal_summary(annual,cw,pd.DataFrame({"municipality_id":["A"]}))


if __name__ == "__main__": unittest.main()

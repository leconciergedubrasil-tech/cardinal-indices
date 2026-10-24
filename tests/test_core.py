import unittest, numpy as np, pandas as pd
from cardinal.core import pct_exp, score, combine

class T(unittest.TestCase):
    def test_sem_lookahead(self):
        s = pd.Series([1, 2, 3, 4, 5.0]); o = pct_exp(s, 3)
        self.assertTrue(np.isnan(o.iloc[0]) and np.isnan(o.iloc[1]))
        self.assertEqual(o.iloc[2], 100.0); self.assertEqual(o.iloc[4], 100.0)
    def test_futuro_nao_altera_passado(self):
        a = pd.Series(np.random.default_rng(1).normal(size=80))
        b = a.copy(); b.iloc[60:] += 100
        pd.testing.assert_series_equal(pct_exp(a).iloc[:60], pct_exp(b).iloc[:60])
    def test_direcao(self):
        s = pd.Series(np.arange(1, 50.0))
        self.assertAlmostEqual(score(s, 1).iloc[-1] + score(s, -1).iloc[-1], 100.0)
    def test_renormaliza_pesos(self):
        sc = pd.DataFrame({"a": [80.0], "b": [np.nan]})
        self.assertAlmostEqual(combine(sc, {"a": .5, "b": .5}).iloc[0], 80.0)

if __name__ == "__main__":
    unittest.main()

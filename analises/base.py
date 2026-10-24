"""Base comum das analises: painel, scores por componente, retornos futuros reais."""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cardinal import indices as I
from cardinal.core import pct_exp, score, combine, moving_block_boot
from cardinal.retorno_usd import indice_real

def painel(caminho="data/painel_mensal.csv"):
    return I.prepara(pd.read_csv(caminho, index_col=0))

def scores_cbbi(p, fim=I.FIM):
    out, sc = I.cbbi(p, fim, detalhe=True)
    return out, sc

def retornos_futuros(p, h):
    """Retorno real futuro em h meses (a partir do fim do mes m): NTN-B longa (indice aproximado), Ibovespa (preco), Tesouro Selic."""
    ipca = 1 + p["IPCA_MES"] / 100
    real = indice_real(p["RY"], p["MAT_LONGA"])
    selic = 1 + p["SELIC_OVER_MES"] / 100
    ibov = p["IBOV"]
    res = {k: {} for k in ["NTNB_longa", "Ibovespa", "Tesouro_Selic"]}
    for m in p.index:
        e = m + h
        if e not in p.index: continue
        win = pd.period_range(m + 1, e, freq="M")
        inf = ipca.reindex(win)
        if inf.notna().sum() < 0.9 * h: continue
        P_inf = inf.prod()
        if m in real.index and e in real.index:
            res["NTNB_longa"][m] = real[e] / real[m] - 1
        if not np.isnan(ibov.get(m, np.nan)) and not np.isnan(ibov.get(e, np.nan)):
            res["Ibovespa"][m] = (ibov[e] / ibov[m]) / P_inf - 1
        s = selic.reindex(win)
        if s.notna().sum() >= 0.9 * h:
            res["Tesouro_Selic"][m] = s.prod() / P_inf - 1
    return pd.DataFrame(res)

def teste(x, r, h, n_boot=2000):
    """Pearson e IC 95% (bootstrap em blocos moveis, bloco = h)."""
    d = pd.concat([x, r], axis=1).dropna()
    if len(d) < 24: return None
    lo, hi = moving_block_boot(d.iloc[:, 0].values, d.iloc[:, 1].values, h, n_boot, seed=0)
    return dict(n=len(d), corr=d.iloc[:, 0].corr(d.iloc[:, 1]), ic_lo=lo, ic_hi=hi)

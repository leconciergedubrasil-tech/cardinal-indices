"""Retorno da NTN-B longa em reais, em dolar e com hedge aproximado (capitulo 'Retorno em dolar e hedge').

APROXIMACOES (declaradas no livro):
- o indice mensal da NTN-B longa usa carrego (taxa real / 12) menos duration modificada x variacao da taxa,
  com cupom de 6% e vencimento medio do bucket; sem convexidade;
- o custo do hedge e aproximado por Selic acumulada contra Fed Funds acumulado (juros cobertos), nao pelo
  cupom cambial de mercado (dado pago da B3);
- retorno bruto: sem imposto, custodia, corretagem ou IOF.
"""
import numpy as np
import pandas as pd


def duration_mod(y_pct, T):
    y = y_pct / 100.0
    T = max(T, 0.5)
    k = np.arange(1, int(round(T * 2)) + 1)
    c = 0.06 / 2 * 100
    cf = np.full(len(k), c); cf[-1] += 100
    pv = cf / (1 + y / 2) ** k
    return (k / 2 * pv).sum() / pv.sum() / (1 + y / 2)


def indice_real(y_pct: pd.Series, mat: pd.Series) -> pd.Series:
    """Indice real mensal: carrego + efeito da duration. Exige meses consecutivos."""
    r = {}
    ms = list(y_pct.dropna().index)
    for a, b in zip(ms[:-1], ms[1:]):
        if b != a + 1 or pd.isna(mat.get(a)):
            continue
        r[b] = (y_pct[a] / 100) / 12 - duration_mod(y_pct[a], mat[a]) * (y_pct[b] - y_pct[a]) / 100
    return (1 + pd.Series(r)).cumprod()


def janelas(p: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Para cada mes de compra: retorno em reais, em dolar (sem hedge), com hedge aproximado, variacao da PTAX e custo."""
    real = indice_real(p["RY"], p["MAT_LONGA"])
    ix = real.index
    ipca = (1 + p["IPCA_MES"] / 100).reindex(ix).fillna(1).cumprod()
    nom = real * ipca
    ptax = p["PTAX"].reindex(ix)
    usd = nom / ptax
    selic = 1 + p["SELIC_OVER_MES"].reindex(ix) / 100
    ffm = (1 + p["FEDFUNDS"].reindex(ix) / 100) ** (1 / 12)
    linhas = []
    for m in ix:
        e = m + horizonte
        if e not in ix or np.isnan(usd[m]) or np.isnan(usd[e]):
            continue
        rb = nom[e] / nom[m] - 1
        ru = usd[e] / usd[m] - 1
        win = pd.period_range(m + 1, e, freq="M")
        if selic.reindex(win).isna().any() or ffm.reindex(win).isna().any():
            custo = rh = np.nan
        else:
            custo = selic.reindex(win).prod() / ffm.reindex(win).prod() - 1
            rh = (1 + rb) / (1 + custo) - 1
        linhas.append((m, rb, ru, rh, ptax[e] / ptax[m] - 1, custo))
    return pd.DataFrame(linhas, columns=["mes", "reais", "dolar", "hedge", "ptax", "custo_hedge"]).set_index("mes")


def resumo(p: pd.DataFrame, horizontes=(12, 24, 36)) -> pd.DataFrame:
    linhas = []
    for h in horizontes:
        d = janelas(p, h)
        for c in ["reais", "dolar", "hedge"]:
            s = d[c].dropna()
            linhas.append(dict(horizonte=h, serie=c, n=len(s), mediana=s.median(), p10=s.quantile(.1),
                               p90=s.quantile(.9), minimo=s.min(), maximo=s.max(), pct_negativas=(s < 0).mean()))
    return pd.DataFrame(linhas)

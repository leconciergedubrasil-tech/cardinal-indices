"""Os quatro indices Cardinal a partir de um painel mensal (ver data/SCHEMA.md).
Pesos, direcoes, janelas e defasagens identicos aos do Memorial Cardinal v1.0."""
import numpy as np
import pandas as pd
from .core import pct_exp, score, combine

PESOS = {
    "CBBI": {"RY": .25, "FISCAL": .20, "INFL": .15, "CURVA": .15, "CAMBIO": .10, "GLOBAL": .10, "LIQUIDEZ": .05},
    "TPI":  {"INFL": .20, "EXPECT": .20, "SELIC": .15, "NTNB": .15, "BRL": .15, "CDS": .15},
    "CERI": {"RR": .25, "FISCAL": .20, "VAL": .20, "EARN": .15, "BRL": .10, "FLOW": .10},
    "NBP":  {"RYBR": .30, "RYUS": .25, "CDS": .25, "DIF": .20},
}
DIRECAO = {
    "CBBI": {"RY": 1, "FISCAL": -1, "INFL": -1, "CURVA": 1, "CAMBIO": 1, "GLOBAL": -1, "LIQUIDEZ": 1},
    "TPI":  {k: -1 for k in PESOS["TPI"]},          # score = 100 - percentil da variacao de 6 meses
    "CERI": {"RR": -1, "FISCAL": -1, "VAL": -1, "EARN": 1, "BRL": 1, "FLOW": 1},
    "NBP":  {"RYBR": 1, "RYUS": -1, "CDS": -1, "DIF": 1},
}
FIM = "2026-08"


def _p(idx_ini, fim=FIM):
    return pd.period_range(idx_ini, fim, freq="M")


def prepara(painel: pd.DataFrame) -> pd.DataFrame:
    """Indexa por periodo mensal."""
    p = painel.copy()
    p.index = pd.PeriodIndex(p.index, freq="M")
    return p


def _scores(df, dirs, min_hist=36):
    return pd.DataFrame({k: score(df[k], d, min_hist) for k, d in dirs.items()})


def _insumos_cbbi(p, fim=FIM):
    """Janela 2010-01..fim; defasagem maxima: FISCAL 3 meses, INFL 2 meses (ffill limitado)."""
    ins = p.loc["2010-01":fim].copy()
    ins["CURVA"] = ins["RY"] - ins["CURTA"]
    ins["FISCAL"] = ins["FISCAL"].ffill(limit=3)
    ins["INFL"] = ins["INFL"].ffill(limit=2)
    return ins


def cbbi(p, fim=FIM, detalhe=False):
    ins = _insumos_cbbi(p, fim)
    sc = _scores(ins, DIRECAO["CBBI"])
    out = combine(sc, PESOS["CBBI"], exigidos=["RY"], min_comp=6)
    return (out, sc) if detalhe else out


def tpi(p, fim=FIM, detalhe=False):
    ins = _insumos_cbbi(p, fim)
    ix = _p("2009-01", fim)
    t = pd.DataFrame(index=ix)
    t["INFL"] = ins["INFL"]; t["NTNB"] = ins["RY"]          # entram a partir de 2010-01
    for k_dst, k_src in [("EXPECT", "EXPECT"), ("SELIC", "SELIC"), ("BRL", "PTAX"), ("CDS", "CDS")]:
        t[k_dst] = p[k_src].reindex(ix)
    d = t - t.shift(6)                                       # variacao de 6 meses
    sc = pd.DataFrame({k: score(d[k], -1) for k in PESOS["TPI"]})
    out = combine(sc, PESOS["TPI"], min_comp=6)              # exige os 6 componentes
    return (out, sc) if detalhe else out


def ceri(p, fim=FIM, detalhe=False):
    ins = _insumos_cbbi(p, fim)
    ix = _p("2010-01", fim)
    c = pd.DataFrame(index=ix)
    c["RR"] = ins["RY"]; c["FISCAL"] = ins["FISCAL"]
    c["VAL"] = p["PL"].reindex(ix); c["EARN"] = p["LUCRO"].reindex(ix); c["BRL"] = p["PTAX"].reindex(ix)
    # fluxo: saldo ANUAL do ano anterior (conhecido em janeiro), constante no ano -> sem look-ahead
    anual = p["FLUXO_ANUAL"].groupby(p.index.year).last()
    c["FLOW"] = [anual.get(m.year - 1, np.nan) for m in ix]
    sc = _scores(c, DIRECAO["CERI"])
    base = [k for k in PESOS["CERI"] if k != "FLOW"]         # FLOW e opcional (renormaliza se ausente)
    out = combine(sc, PESOS["CERI"], exigidos=base)
    return (out, sc) if detalhe else out


def nbp(p, fim=FIM, detalhe=False):
    ins = _insumos_cbbi(p, fim)
    ix = _p("2010-01", fim)
    n = pd.DataFrame(index=ix)
    n["RYBR"] = ins["RY"]; n["RYUS"] = p["USRY"].reindex(ix); n["CDS"] = p["CDS"].reindex(ix)
    n["DIF"] = (p["SELIC"] - p["FEDFUNDS"]).reindex(ix)      # Selic meta - Fed Funds
    sc = _scores(n, DIRECAO["NBP"])
    out = combine(sc, PESOS["NBP"], min_comp=4)
    return (out, sc) if detalhe else out


def todos(p, fim=FIM):
    p = prepara(p) if not isinstance(p.index, pd.PeriodIndex) else p
    return pd.DataFrame({"CBBI": cbbi(p, fim), "TPI": tpi(p, fim), "CERI": ceri(p, fim), "NBP": nbp(p, fim)})

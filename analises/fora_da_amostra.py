"""Teste fora da amostra (janela expansiva): o indice preve o retorno real futuro melhor que a media historica?
Referencia: Goyal e Welch (2008); Campbell e Thompson (2008); estatistica de Clark e West (2007) com erro-padrao de Newey e West (1987)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import base
from base import I

p = base.painel()
IND = I.todos(p)
IND["RY (nivel)"] = p["RY"]          # concorrente simples: a taxa real da NTN-B longa
ALVOS = ["NTNB_longa", "Ibovespa", "Tesouro_Selic"]

def nw_t(f, lag):
    f = np.asarray(f, float); n = len(f); m = f.mean(); e = f - m
    v = (e @ e) / n
    for L in range(1, lag + 1):
        w = 1 - L / (lag + 1); v += 2 * w * (e[L:] @ e[:-L]) / n
    return m / np.sqrt(v / n)

def oos(x, r, h, min_train=36):
    d = pd.concat([x.rename("x"), r.rename("r")], axis=1)
    idx = d.index
    prev, cm, y, mean_err, mod_err = [], [], [], [], []
    rows = []
    for t in idx:
        if np.isnan(d.loc[t, "x"]) or np.isnan(d.loc[t, "r"]): continue
        tr = d.loc[:t - h].dropna()               # so pares com retorno ja realizado em t
        if len(tr) < min_train: continue
        b = np.polyfit(tr.x.values, tr.r.values, 1)
        rows.append((t, d.loc[t, "r"], tr.r.mean(), b[0] * d.loc[t, "x"] + b[1]))
    o = pd.DataFrame(rows, columns=["t", "r", "media", "modelo"]).set_index("t")
    if len(o) < 24: return None
    e0 = o.r - o.media; e1 = o.r - o.modelo
    r2 = 1 - (e1 ** 2).sum() / (e0 ** 2).sum()
    f = e0 ** 2 - (e1 ** 2 - (o.media - o.modelo) ** 2)
    cw = nw_t(f.values, h - 1)
    return dict(n=len(o), inicio=str(o.index[0]), r2_oos=r2, cw_t=cw)

rows = []
for h in (12, 24):
    R = base.retornos_futuros(p, h)
    for ind in IND.columns:
        for alvo in ALVOS:
            res = oos(IND[ind], R[alvo], h)
            if res: rows.append(dict(horizonte=h, preditor=ind, alvo=alvo, **res))
T = pd.DataFrame(rows)
T["r2_oos_pct"] = (100 * T.r2_oos).round(1); T["cw_t"] = T.cw_t.round(2)
T.drop(columns="r2_oos").to_csv("resultados/fora_da_amostra.csv", index=False)
pd.set_option("display.width", 200)
print(T.pivot_table(index=["horizonte", "preditor"], columns="alvo", values="r2_oos_pct").to_string())
print(); print(T.pivot_table(index=["horizonte", "preditor"], columns="alvo", values="cw_t").to_string())
print(); print(T.groupby(["horizonte"]).n.agg(["min", "max"]), T.inicio.min(), T.inicio.max())
print("melhores:", T.sort_values("r2_oos_pct", ascending=False).head(5)[["horizonte", "preditor", "alvo", "r2_oos_pct", "cw_t"]].to_string(index=False))

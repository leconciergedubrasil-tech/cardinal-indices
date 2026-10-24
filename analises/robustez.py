"""Robustez do CBBI: pesos, componentes, composicao no tempo e definicao do percentil."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import base
from base import I, combine, score, pct_exp

p = base.painel()
ins = I._insumos_cbbi(p)
DIR = I.DIRECAO["CBBI"]; W0 = I.PESOS["CBBI"]
cb0, sc0 = I.cbbi(p, detalhe=True)
AG = pd.Period("2026-08", "M")

def idx(sc, w, exig=("RY",), minc=6):
    w = {k: v for k, v in w.items() if k in sc.columns}
    return combine(sc[list(w)], w, exigidos=[e for e in exig if e in w], min_comp=min(minc, len(w)))

def resumo(nome, s):
    c = pd.concat([cb0, s], axis=1).dropna()
    return dict(variante=nome, agosto_2026=round(float(s.get(AG, np.nan)), 1), meses=int(s.notna().sum()),
                corr_com_base=round(c.iloc[:, 0].corr(c.iloc[:, 1]), 3), maximo=round(float(s.max()), 1), minimo=round(float(s.min()), 1))

rows = [resumo("Base (pesos do livro)", cb0)]
# 1) pesos iguais
rows.append(resumo("Pesos iguais", idx(sc0, {k: 1 / 7 for k in W0})))
# 2) pesos perturbados +-5 pontos (renormalizados)
pert = []
for k in W0:
    for d in (+.05, -.05):
        w = dict(W0); w[k] = max(w[k] + d, 0); t = sum(w.values()); w = {a: b / t for a, b in w.items()}
        s = idx(sc0, w); pert.append((f"{k} {d:+.2f}", s))
vals = pd.concat([s for _, s in pert], axis=1)
corrs = [pd.concat([cb0, s], axis=1).dropna().corr().iloc[0, 1] for _, s in pert]
rows.append(dict(variante="14 perturbações de ±5 pontos (faixa)", agosto_2026=f"{vals.loc[AG].min():.1f} a {vals.loc[AG].max():.1f}", meses=int(vals.notna().any(axis=1).sum()),
                 corr_com_base=f"{min(corrs):.3f} a {max(corrs):.3f}", maximo=round(vals.max().max(), 1), minimo=round(vals.min().min(), 1)))
# 3) retirar um componente por vez
loo = {}
for k in W0:
    w = {a: b for a, b in W0.items() if a != k}; t = sum(w.values()); w = {a: b / t for a, b in w.items()}
    loo[k] = idx(sc0, w, minc=5)
    rows.append(resumo(f"Sem {k}", loo[k]))
# 4) primeira componente principal (meses com os 7 scores)
full = sc0.dropna()
Z = (full - full.mean()) / full.std()
u, s_, vt = np.linalg.svd(Z.values, full_matrices=False)
pc1 = pd.Series(u[:, 0] * s_[0], index=full.index)
load = pd.Series(vt[0], index=full.columns)
if np.corrcoef(pc1, full.mean(axis=1))[0, 1] < 0: pc1, load = -pc1, -load
pc1s = (pc1 - pc1.min()) / (pc1.max() - pc1.min()) * 100
expl = s_[0] ** 2 / (s_ ** 2).sum()
r = resumo("1ª componente principal (7 scores, reescalada 0-100)", pc1s); r["agosto_2026"] = round(float(pc1s.get(AG, np.nan)), 1); rows.append(r)
# 5) composicao fixa: 6 componentes sem LIQUIDEZ (serie inteira) e 7 componentes (so periodo completo)
w6 = {k: v for k, v in W0.items() if k != "LIQUIDEZ"}; t = sum(w6.values()); w6 = {a: b / t for a, b in w6.items()}
c6 = combine(sc0[list(w6)], w6, exigidos=list(w6))
c7 = combine(sc0, W0, exigidos=list(W0))
rows.append(resumo("Composição fixa: 6 componentes (sem Liquidez)", c6))
rows.append(resumo("Composição fixa: 7 componentes (só meses completos)", c7))
# 6) definicao do percentil
def sc_alt(fn):
    return pd.DataFrame({k: (fn(ins[k]) if d > 0 else 100 - fn(ins[k])) for k, d in DIR.items()})
def roll120(s, minh=36):
    v = s.values; out = np.full(len(v), np.nan)
    for i in range(len(v)):
        if np.isnan(v[i]): continue
        h = v[max(0, i - 119): i + 1]; h = h[~np.isnan(h)]
        if len(h) >= minh: out[i] = 100 * (h <= v[i]).sum() / len(h)
    return pd.Series(out, index=s.index)
def desvio60(s):  # percentil do desvio em relação à média dos 60 meses anteriores (tira a tendência)
    d = s - s.rolling(60, min_periods=36).mean().shift(1)
    return pct_exp(d, 36)
sc_r = sc_alt(roll120); sc_d = sc_alt(desvio60); sc_60 = pd.DataFrame({k: score(ins[k], d, 60) for k, d in DIR.items()})
cb_r = idx(sc_r, W0); cb_d = idx(sc_d, W0); cb_60 = idx(sc_60, W0)
rows.append(resumo("Percentil em janela móvel de 120 meses", cb_r))
rows.append(resumo("Percentil do desvio da média móvel de 60 meses (sem tendência)", cb_d))
rows.append(resumo("Percentil expandindo, mínimo de 60 meses", cb_60))
R = pd.DataFrame(rows)
R.to_csv("resultados/robustez_cbbi.csv", index=False)
pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 70)
print(R.to_string(index=False))
print("\nPC1: variancia explicada", round(expl, 3), "meses", len(full)); print(load.round(2).to_dict())
# 7) saturacao dos scores por componente (expandindo x janela x sem tendencia)
sat = []
for k in W0:
    for nome, sc in [("expandindo", sc0), ("janela 120m", sc_r), ("sem tendência", sc_d)]:
        s = sc[k].dropna(); sat.append(dict(componente=k, definicao=nome, n=len(s), pct_acima_90=round(100 * (s > 90).mean(), 1), pct_abaixo_10=round(100 * (s < 10).mean(), 1), agosto_2026=round(float(sc[k].get(AG, np.nan)), 1)))
S = pd.DataFrame(sat); S.to_csv("resultados/saturacao_scores.csv", index=False)
print(); print(S[S.definicao.isin(["expandindo", "janela 120m", "sem tendência"])].pivot(index="componente", columns="definicao", values=["pct_acima_90", "pct_abaixo_10"]).to_string())
# 8) a conclusao do teste muda? (correlacao com retorno real futuro, NTN-B longa e Ibovespa)
tests = []
variantes = {"Base": cb0, "Pesos iguais": idx(sc0, {k: 1 / 7 for k in W0}), "PC1": pc1s, "6 componentes fixos": c6, "Janela 120m": cb_r, "Sem tendência": cb_d}
for h in (12, 24, 36):
    Rf = base.retornos_futuros(p, h)
    for nome, s in variantes.items():
        for alvo in ["NTNB_longa", "Ibovespa", "Tesouro_Selic"]:
            t = base.teste(s, Rf[alvo], h)
            if t: tests.append(dict(variante=nome, horizonte=h, alvo=alvo, **{k: round(v, 3) if isinstance(v, float) else v for k, v in t.items()}))
T = pd.DataFrame(tests); T.to_csv("resultados/robustez_testes.csv", index=False)
T["inclui_zero"] = (T.ic_lo <= 0) & (T.ic_hi >= 0)
print("\nIC inclui zero:", int(T.inclui_zero.sum()), "de", len(T)); print(T[~T.inclui_zero].to_string(index=False))

"""Tres episodios: como os indices liam cada momento e o que veio depois (retorno real em 12 meses)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import base
from base import I

p = base.painel(); IND = I.todos(p); R12 = base.retornos_futuros(p, 12)
EP = {
 "2015 (crise fiscal e rebaixamento)": ["2014-12", "2015-06", "2015-09", "2015-12", "2016-06"],
 "2020 (pandemia)": ["2020-01", "2020-03", "2020-06", "2020-12"],
 "2022 (eleição e juros altos)": ["2022-03", "2022-06", "2022-10", "2022-12"],
}
rows = []
for nome, ms in EP.items():
    for m in ms:
        P = pd.Period(m, "M")
        rows.append(dict(episodio=nome, mes=m,
            CBBI=IND.CBBI.get(P), TPI=IND.TPI.get(P), CERI=IND.CERI.get(P), NBP=IND.NBP.get(P),
            juro_real=p.RY.get(P), selic=p.SELIC.get(P), ptax=p.PTAX.get(P), cds=p.CDS.get(P), divida_pib=p.FISCAL.ffill(limit=3).get(P),
            ret12_ntnb=R12.NTNB_longa.get(P), ret12_ibov=R12.Ibovespa.get(P), ret12_selic=R12.Tesouro_Selic.get(P)))
E_ = pd.DataFrame(rows)
E_.to_csv("resultados/episodios.csv", index=False)
pd.set_option("display.width", 250)
print(E_.round(2).to_string(index=False))
# efeito do peso efetivo: contribuicao de cada score para a variancia do CBBI (meses completos)
out, sc = I.cbbi(p, detalhe=True)
full = sc.dropna(); w = pd.Series(I.PESOS["CBBI"])[full.columns]
idx7 = (full * w).sum(axis=1)
contrib = {k: float(np.cov(w[k] * full[k], idx7)[0, 1] / idx7.var()) for k in full.columns}
C = pd.DataFrame({"peso_nominal_pct": (100 * w).round(1), "contribuicao_variancia_pct": (100 * pd.Series(contrib)).round(1)})
C.to_csv("resultados/peso_efetivo_cbbi.csv"); print(); print(C.to_string()); print("meses completos:", len(full))

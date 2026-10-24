"""Reproduz a tabela do capitulo 'Retorno em dolar e hedge'. Uso: python verify_usd.py data/painel_mensal.csv"""
import sys
import pandas as pd
from cardinal import indices as I
from cardinal.retorno_usd import resumo

p = I.prepara(pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "data/painel_mensal.csv", index_col=0))
r = resumo(p)
pd.set_option("display.width", 160)
print(r.assign(**{c: (r[c] * 100).round(1) for c in ["mediana", "p10", "p90", "minimo", "maximo", "pct_negativas"]}).to_string(index=False))

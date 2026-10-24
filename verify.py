"""Confere os quatro valores de agosto de 2026 publicados no livro.
Uso: python verify.py data/painel_mensal.csv"""
import sys
import pandas as pd
from cardinal import indices as I

LIVRO = {"CBBI": 48.8, "TPI": 41.4, "CERI": 40.0, "NBP": 65.5}

def main(caminho):
    p = I.prepara(pd.read_csv(caminho, index_col=0))
    res = I.todos(p).loc["2026-08"]
    ok = True
    for k, v in LIVRO.items():
        calc = round(float(res[k]), 1)
        flag = "OK " if abs(calc - v) < 0.05 else "DIFERE"
        ok &= flag == "OK "
        print(f"{k:5s} livro {v:5.1f}  calculado {res[k]:8.3f}  -> {flag}")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/painel_mensal.csv")

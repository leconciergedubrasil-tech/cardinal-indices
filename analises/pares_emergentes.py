"""Compara o juro real brasileiro com pares emergentes.

Entrada: data/pares_emergentes.csv (nao publicado; fontes com licenca propria), colunas:
  DATA (AAAA-MM), PAIS (BR, MX, CL, CO, ZA), YIELD_REAL (% a.a., titulo indexado a inflacao ~10 anos),
  IPCA_12M (% inflacao em 12 meses), CDS_5A (pb, opcional)
Saida: resultados/pares_emergentes.csv (mediana, posicao do Brasil e percentil historico por mes).
"""
import sys
import pandas as pd

def main(entrada="data/pares_emergentes.csv", saida="resultados/pares_emergentes.csv"):
    d = pd.read_csv(entrada, parse_dates=["DATA"])
    p = d.pivot(index="DATA", columns="PAIS", values="YIELD_REAL")
    pares = [c for c in p.columns if c != "BR"]
    out = pd.DataFrame({"BR": p["BR"], "MEDIANA_PARES": p[pares].median(axis=1)})
    out["DIF_BR_MENOS_PARES"] = out.BR - out.MEDIANA_PARES
    out["RANK_BR"] = p.rank(axis=1, ascending=False)["BR"]
    out["PCT_DIF_EXP"] = out.DIF_BR_MENOS_PARES.expanding(36).apply(lambda x: (x <= x.iloc[-1]).mean() * 100, raw=False)
    out.round(3).to_csv(saida)
    return out

if __name__ == "__main__":
    print(main(*sys.argv[1:]).tail())

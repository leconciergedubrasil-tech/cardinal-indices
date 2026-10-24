# Esquema do painel mensal / Monthly panel schema

Arquivo `data/painel_mensal.csv` (nao versionado). Uma linha por mes, `ano_mes` no formato `AAAA-MM`, de `2009-01` a `2026-08`.
Use **precisao total** ao salvar (nao arredonde): o percentil usa `<=` e o arredondamento cria empates.

| Coluna | Conteudo | Fonte sugerida | Observacao |
|---|---|---|---|
| RY | Taxa real NTN-B longa (% a.a.), ultimo dia util do mes | Tesouro Transparente | media dos titulos do bucket "longa" no ultimo dia |
| CURTA | Taxa real NTN-B curta (% a.a.) | Tesouro Transparente | CURVA = RY - CURTA |
| FISCAL | Divida bruta/PIB (%) | BCB | defasagem maxima 3 meses (ffill limitado no codigo) |
| INFL | IPCA 12 meses (%) | IBGE/BCB | defasagem maxima 2 meses |
| CAMBIO | PTAX venda, ultimo valor do mes | BCB | |
| GLOBAL | Treasury 10 anos (%) | FRED DGS10 | |
| LIQUIDEZ | Liquidez secundaria | BCB | |
| EXPECT | Focus IPCA 12m, mediana suavizada, ultimo do mes | BCB Olinda | |
| SELIC | Selic meta, ultimo valor do mes | BCB | |
| PTAX | PTAX venda, ultimo valor do mes | BCB | |
| CDS | CDS Brasil 5a (bps), fim de mes | Investing.com | **licenca propria: traga seu proprio dado** |
| USRY | TIPS 10 anos (%) | FRED DFII10 | |
| FEDFUNDS | Fed Funds (%), ultimo do mes | FRED/Fed | |
| PL | P/L agregado do Ibovespa | CVM (pipeline proprio) | vies de sobrevivencia declarado no livro |
| LUCRO | Lucro agregado | CVM | |
| MAT_LONGA | Vencimento medio (anos) do bucket NTN-B longa | Tesouro Transparente | usado so em `retorno_usd.py` |
| IPCA_MES | IPCA mensal (%) | IBGE | usado em `analises/` e `retorno_usd.py` |
| SELIC_OVER_MES | Selic over acumulada no mês (%) | BCB | usado em `retorno_usd.py` |
| IBOV | Ibovespa, fechamento do mês | B3 | usado em `analises/episodios.py`; dado com licença própria, não publicado |
| IPCA_MES | IPCA mensal (%) | IBGE/BCB | usado so em `retorno_usd.py` |
| SELIC_OVER_MES | Selic over acumulada no mes (%) | BCB | usado so em `retorno_usd.py` |
| FLUXO_ANUAL | Saldo anual de investidor estrangeiro (R$ mi), repetido em todos os meses do ano | B3 | o codigo usa o saldo do **ano anterior** |

Meses ausentes ficam em branco. Nunca preencha lacuna com 50 ou interpolacao.

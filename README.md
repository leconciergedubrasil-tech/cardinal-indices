# Cardinal Indices — replicação / replication

**PT.** Código para recalcular os quatro índices do *Memorial Cardinal* (CBBI, TPI, CERI, NBP) a partir de um painel mensal. Os índices descrevem regimes do mercado de renda fixa brasileiro. **Não são recomendação de investimento**, não preveem retorno e não substituem julgamento. Conteúdo educacional.

**EN.** Code to recompute the four indices of the *Cardinal Memorial* (CBBI, TPI, CERI, NBP) from a monthly panel. The indices describe regimes in the Brazilian fixed-income market. **They are not investment advice**, do not predict returns and do not replace judgment. Educational content.

## O que está / what is here
- `cardinal/core.py`: percentil expandindo (mínimo 36 meses, sem look-ahead), score, média ponderada com pesos renormalizados, bootstrap em blocos móveis.
- `cardinal/indices.py`: pesos, direções, janelas e defasagens dos quatro índices.
- `verify.py`: confere os valores de agosto de 2026 publicados no livro (48,8 / 41,4 / 40,0 / 65,5).
- `tests/`: testes do núcleo (sem look-ahead, direção, renormalização).
- `data/SCHEMA.md`: colunas que o painel precisa ter.

**Os dados não estão no repositório.** Várias fontes têm licença própria (B3, Investing.com, CVM, FRED). Monte `data/painel_mensal.csv` conforme `data/SCHEMA.md`.

## Uso / Usage
```bash
pip install pandas numpy
python -m unittest discover -s tests
python verify.py data/painel_mensal.csv
```
```python
import pandas as pd
from cardinal import indices as I
p = I.prepara(pd.read_csv("data/painel_mensal.csv", index_col=0))
print(I.todos(p).tail())
```

## Regras / Rules
1. Percentil de cada mês contra o histórico **até aquele mês**, mínimo 36 observações.
2. Direção "−": score = 100 − percentil. No TPI o percentil é o da variação de 6 meses.
3. Defasagem máxima: fiscal 3 meses, inflação 2 meses.
4. Média ponderada só dos componentes presentes, pesos renormalizados. Nunca imputar 50.
5. Janelas: CBBI, CERI e NBP desde 2010-01; TPI calculado desde 2009-01 (inflação e NTN-B entram a partir de 2010-01). O fluxo estrangeiro do CERI usa o saldo anual do ano anterior.

## Conferência / Check
Valores calculados para agosto de 2026: CBBI 48,83, TPI 41,40, CERI 39,99, NBP 65,54. Diferenças na segunda casa decimal podem vir de revisão de dados. Salve o painel com precisão total: arredondar para 6 casas já mudou 3 meses da série por causa de empates no percentil.

## Limitações / Limitations
Pesos e bandas sem calibração estatística. Janelas de retorno sobrepostas, por isso o IC por bootstrap em blocos. Os índices não cobrem retorno em dólar nem IR de não residente. O livro documenta que os ICs de correlação com retornos futuros incluem zero.

## Licença / License
Código sob MIT (ver `LICENSE`). Dados de terceiros seguem as licenças das fontes.

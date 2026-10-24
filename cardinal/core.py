"""Nucleo comum dos indices Cardinal: percentil expandindo, score, media ponderada,
bootstrap em blocos. Sem look-ahead: cada mes usa apenas o historico ate aquele mes."""
import numpy as np
import pandas as pd


def pct_exp(s: pd.Series, min_hist: int = 36) -> pd.Series:
    """Percentil (0-100) de cada valor dentro do historico ate o proprio mes.
    NaN se houver menos de `min_hist` observacoes validas."""
    v = s.values.astype(float)
    out = np.full(len(v), np.nan)
    for i in range(len(v)):
        if np.isnan(v[i]):
            continue
        h = v[: i + 1]
        h = h[~np.isnan(h)]
        if len(h) >= min_hist:
            out[i] = 100.0 * (h <= v[i]).sum() / len(h)
    return pd.Series(out, index=s.index)


def score(s: pd.Series, direcao: int = +1, min_hist: int = 36) -> pd.Series:
    """Score 0-100. direcao +1: score = percentil; -1: score = 100 - percentil."""
    p = pct_exp(s, min_hist)
    return p if direcao > 0 else 100.0 - p


def combine(scores: pd.DataFrame, pesos: dict, exigidos=None, min_comp=None) -> pd.Series:
    """Media ponderada dos scores presentes, com pesos renormalizados (sem imputacao).
    exigidos: colunas que precisam existir no mes. min_comp: numero minimo de componentes."""
    w = pd.Series(pesos)[scores.columns]
    presente = scores.notna()
    num = (scores.fillna(0) * w).sum(axis=1)
    den = (presente * w).sum(axis=1)
    out = num / den.where(den > 0)
    ok = pd.Series(True, index=scores.index)
    if exigidos is not None:
        ok &= presente[list(exigidos)].all(axis=1)
    if min_comp is not None:
        ok &= presente.sum(axis=1) >= min_comp
    return out.where(ok)


def moving_block_boot(x, y, bloco, n_boot=2000, seed=0):
    """IC 95% para a correlacao de Pearson por bootstrap em blocos moveis
    (bloco = horizonte do retorno, pois as janelas se sobrepoem)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    rng = np.random.default_rng(seed)
    n = len(x)
    nb = int(np.ceil(n / bloco))
    rs = []
    for _ in range(n_boot):
        st = rng.integers(0, n - bloco + 1, nb)
        ix = np.concatenate([np.arange(s, s + bloco) for s in st])[:n]
        rs.append(np.corrcoef(x[ix], y[ix])[0, 1])
    return tuple(np.percentile(rs, [2.5, 97.5]))

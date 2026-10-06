"""Cálculos puros: validação, anualização e associação exploratória."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

KEY = ["cnpj", "set_id", "year", "month", "indicator"]


def parse_decimal(series):
    text = series.astype(str).str.strip().str.replace(",", ".", regex=False)
    result = pd.to_numeric(text, errors="coerce")
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError("Valor ausente ou não numérico na base elétrica; revisão necessária.")
    return result


def annualize(monthly):
    """Reconstrução anual por conjunto, ajustada pelo número mensal de UCs.

    DEC_a = sum(DEC_m * N_m) / mean(N_m), analogamente para FEC.
    Os indicadores mensais arredondados não permitem reprodução regulatória exata.
    Nenhum mês ausente é preenchido com zero.
    """
    df = monthly.copy()
    if df.duplicated(KEY).any():
        raise ValueError("Chave mensal duplicada: não é seguro somar os registros.")
    if not df.month.isin(range(1, 13)).all():
        raise ValueError("Período fora de 1–12; mistura de granularidades.")
    if not df.indicator.isin(["DEC", "FEC", "NumCon"]).all():
        raise ValueError("Indicador não previsto na anualização.")
    if not np.isfinite(df.value).all() or (df.value < 0).any():
        raise ValueError("Valores elétricos devem ser finitos e não negativos.")
    ids = ["cnpj", "set_id", "year"]
    wide = df.pivot(index=ids + ["month"], columns="indicator", values="value")
    for col in ["DEC", "FEC", "NumCon"]:
        if col not in wide:
            wide[col] = np.nan
    wide["valid"] = wide[["DEC", "FEC", "NumCon"]].notna().all(axis=1) & (wide.NumCon > 0)
    rows = []
    for key, group in wide.groupby(level=ids):
        complete = len(group) == 12 and bool(group.valid.all())
        record = dict(zip(ids, key))
        record.update(months_observed=len(group), months_complete=int(group.valid.sum()), complete=complete)
        if complete:
            nmean = group.NumCon.mean()
            record.update(dec_h=float((group.DEC * group.NumCon).sum() / nmean),
                          fec_n=float((group.FEC * group.NumCon).sum() / nmean),
                          dec_sum=float(group.DEC.sum()), fec_sum=float(group.FEC.sum()),
                          uc_mean=float(nmean), uc_ratio=float(group.NumCon.max() / group.NumCon.min()))
        rows.append(record)
    return pd.DataFrame(rows)


def association(frame, x="income_mean", y="dec_median"):
    """Correlação descritiva, sem p-valor por dependência dos conjuntos compartilhados."""
    d = frame[[x, y]].dropna()
    if len(d) < 4 or d[x].nunique() < 2 or d[y].nunique() < 2:
        return {"n": len(d), "rho": None, "loo_min": None, "loo_max": None}
    rho = float(spearmanr(d[x], d[y]).statistic)
    leave_one_out = []
    for idx in d.index:
        rest = d.drop(idx)
        if rest[x].nunique() > 1 and rest[y].nunique() > 1:
            leave_one_out.append(float(spearmanr(rest[x], rest[y]).statistic))
    return {"n": len(d), "rho": rho,
            "loo_min": min(leave_one_out) if leave_one_out else None,
            "loo_max": max(leave_one_out) if leave_one_out else None}


def municipal_summary(annual, crosswalk, income, exclusive=False):
    """Medianas de conjuntos associados, nunca DEC/FEC municipal oficial.

    A contagem de municípios de cada conjunto é nacional, antes do recorte RMC.
    """
    cw = crosswalk.drop_duplicates(["set_id", "municipality_id"]).copy()
    degree = cw.groupby("set_id").municipality_id.nunique().rename("municipalities_served")
    cw = cw.merge(degree, on="set_id", validate="many_to_one")
    if exclusive:
        cw = cw[cw.municipalities_served.eq(1)]
    active = annual[annual.complete].copy()
    if active.duplicated(["set_id", "year"]).any():
        raise ValueError("Conjunto com múltiplos agentes no mesmo ano; cruzamento municipal ambíguo.")
    linked = active.merge(cw, on="set_id", validate="many_to_many")
    linked = linked[linked.municipality_id.isin(income.municipality_id)]
    rows = []
    for (mid, year), g in linked.groupby(["municipality_id", "year"]):
        rows.append({"municipality_id": mid, "year": year, "n_sets": g.set_id.nunique(),
                     "n_shared": g.loc[g.municipalities_served.gt(1), "set_id"].nunique(),
                     "dec_median": g.dec_h.median(), "dec_min": g.dec_h.min(), "dec_max": g.dec_h.max(),
                     "fec_median": g.fec_n.median(), "fec_min": g.fec_n.min(), "fec_max": g.fec_n.max(),
                     "dec_simple_median": g.dec_sum.median(),
                     "dec_limit_ratio_median": g.dec_limit_ratio.dropna().median() if g.dec_limit_ratio.notna().any() else np.nan})
    result = pd.DataFrame(rows)
    if result.empty:
        return result, linked
    return result.merge(income, on="municipality_id", validate="many_to_one"), linked

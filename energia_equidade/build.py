"""Constrói tabelas, banco SQLite e diagnósticos a partir de snapshot auditável."""
import argparse
import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from .acquire import ROOT, RAW, MUNICIPALITIES
from .analysis import annualize, parse_decimal, municipal_summary, association

OUT = ROOT / "data/processed"
YEARS = [2022, 2023, 2024, 2025]
RENAME = {"NumCNPJ": "cnpj", "IdeConjUndConsumidoras": "set_id", "AnoIndice": "year",
          "NumPeriodoIndice": "month", "SigIndicador": "indicator", "VlrIndiceEnviado": "value",
          "DscConjUndConsumidoras": "set_name", "SigAgente": "agent"}


def raw_source(name):
    """Aceita o original atualizado ou sua cópia gzip sem perda, incluída no Git."""
    original = RAW / name
    return original if original.exists() else RAW / (name + ".gz")


def extract():
    parts = []
    scanned = 0
    with zipfile.ZipFile(RAW / "continuity.zip") as archive:
        csvs = [n for n in archive.namelist() if n.endswith(".csv")]
        if len(csvs) != 1:
            raise ValueError("Esperado exatamente um CSV no ZIP oficial.")
        with archive.open(csvs[0]) as handle:
            for chunk in pd.read_csv(handle, sep=";", dtype=str, chunksize=250000):
                scanned += len(chunk)
                chunk = chunk.apply(lambda col: col.str.strip())
                selected = chunk[chunk.SigIndicador.isin(["DEC", "FEC", "NumCon"]) &
                                 chunk.AnoIndice.isin([str(y) for y in YEARS])]
                parts.append(selected)
    frame = pd.concat(parts, ignore_index=True).rename(columns=RENAME)
    frame.to_csv(OUT / "monthly_snapshot.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    provenance = {"input_sha256": json.loads((RAW / "continuity.zip.source.json").read_text())["sha256"],
                  "rows_scanned": scanned, "rows_selected": len(frame), "years": YEARS,
                  "indicators": ["DEC", "FEC", "NumCon"]}
    provenance["snapshot_sha256"] = hashlib.sha256((OUT / "monthly_snapshot.csv.gz").read_bytes()).hexdigest()
    (OUT / "extraction.json").write_text(json.dumps(provenance, indent=2))


def read_income():
    records = json.loads((RAW / "income.json").read_text())
    if not isinstance(records, list) or len(records) < 2:
        raise ValueError("Resposta SIDRA inválida.")
    raw = pd.DataFrame(records[1:])
    if not (raw.D3C.eq("2022") & raw.D4C.eq("6794") & raw.D5C.eq("95251") & raw.D6C.eq("95253")).all():
        raise ValueError("Recorte SIDRA inesperado; não combinar subgrupos com o total.")
    raw["value"] = pd.to_numeric(raw.V, errors="coerce")  # supressões não são zero
    if raw.duplicated(["D1C", "D2C"]).any():
        raise ValueError("SIDRA: mais de um valor por território e variável.")
    inc = raw.pivot(index="D1C", columns="D2C", values="value").rename(columns={
        "13431": "income_mean", "13534": "income_median", "13604": "income_population"}).reset_index()
    inc = inc.rename(columns={"D1C": "municipality_id"})
    inc["municipality"] = inc.municipality_id.map(MUNICIPALITIES | {"1": "Brasil", "35": "São Paulo"})
    inc["income_year"] = 2022
    classes = pd.DataFrame(json.loads((RAW / "income_classes.json").read_text())[1:])
    if not (classes.D3C.eq("2022") & classes.D4C.eq("6794") & classes.D5C.eq("95251") & classes.D2C.eq("13604")).all():
        raise ValueError("Recorte de classes de renda inesperado.")
    classes["value"] = pd.to_numeric(classes.V, errors="coerce")
    counts = classes.pivot(index="D1C", columns="D6C", values="value")
    # Classes mutuamente exclusivas: sem rendimento, até 1/4, mais de 1/4 até 1/2 SM.
    # min_count impede transformar supressões em zero.
    low = counts[["9692", "9681", "9682"]].sum(axis=1, min_count=3)
    total = counts["9680"].where(counts["9680"] > 0)
    partition = counts.drop(columns="9680").sum(axis=1, min_count=len(counts.columns)-1)
    if ((partition - total).abs() > len(counts.columns)).any():
        raise ValueError("Classes de renda não fecham com o total, além de tolerância de arredondamento.")
    if ((low < 0) | (low > total)).any():
        raise ValueError("Numerador de baixa renda inválido.")
    share = (100 * low / total).rename("low_income_pct").reset_index().rename(columns={"D1C": "municipality_id"})
    inc = inc.merge(share, on="municipality_id", validate="one_to_one")
    if set(MUNICIPALITIES) - set(inc.municipality_id):
        raise ValueError("Faltam municípios da RMC na resposta de renda.")
    return inc


def build(reextract=False):
    OUT.mkdir(parents=True, exist_ok=True)
    if reextract or not (OUT / "monthly_snapshot.csv.gz").exists():
        extract()
    expected = json.loads((OUT / "extraction.json").read_text())["snapshot_sha256"]
    if hashlib.sha256((OUT / "monthly_snapshot.csv.gz").read_bytes()).hexdigest() != expected:
        raise ValueError("Snapshot mensal alterado: hash diferente do registrado.")
    monthly = pd.read_csv(OUT / "monthly_snapshot.csv.gz", dtype=str)
    for col in ["year", "month"]:
        monthly[col] = pd.to_numeric(monthly[col], errors="raise").astype(int)
    monthly["value"] = parse_decimal(monthly.value)
    cw = pd.read_csv(raw_source("crosswalk.csv"), sep=";", dtype=str, encoding="cp1252").apply(lambda x: x.str.strip())
    cw = cw.rename(columns={"IdeConjUnidConsumidoras": "set_id", "CodMunicipio": "municipality_id", "NomMunicipio": "municipality", "SigUF": "state"})
    cw = cw.drop_duplicates(["set_id", "municipality_id"])
    # Não tratar totais de distribuidora ou conjuntos sem vínculo como conjuntos territoriais.
    all_annual = annualize(monthly)
    annual = all_annual[all_annual.set_id.isin(cw.set_id)].copy()
    names = monthly.sort_values("month").drop_duplicates(["cnpj", "set_id", "year"], keep="last")
    annual = annual.merge(names[["cnpj", "set_id", "year", "set_name", "agent"]], on=["cnpj", "set_id", "year"], validate="one_to_one")
    limits = pd.read_csv(raw_source("limits.csv"), sep=";", dtype=str).apply(lambda x: x.str.strip())
    limits = limits.rename(columns=RENAME | {"AnoLimiteQualidade": "year", "VlrLimite": "limit"})
    limits["year"] = limits.year.astype(int)
    limits = limits[limits.year.isin(YEARS) & limits.indicator.isin(["DEC", "FEC"])]
    limits["limit"] = parse_decimal(limits.limit)
    if limits.duplicated(["cnpj", "set_id", "year", "indicator"]).any():
        raise ValueError("Limites duplicados; revisar antes de calcular razões.")
    limits = limits.pivot(index=["cnpj", "set_id", "year"], columns="indicator", values="limit").reset_index().rename(columns={"DEC": "dec_limit", "FEC": "fec_limit"})
    annual = annual.merge(limits, how="left", on=["cnpj", "set_id", "year"], validate="one_to_one")
    for metric in ["dec", "fec"]:
        annual[f"{metric}_limit_ratio"] = annual[f"{metric}_{'h' if metric == 'dec' else 'n'}"] / annual[f"{metric}_limit"].where(annual[f"{metric}_limit"] > 0)
    inc = read_income()
    regional_inc = inc[inc.municipality_id.isin(MUNICIPALITIES)]
    municipal, linked = municipal_summary(annual, cw, regional_inc)
    exclusive, _ = municipal_summary(annual, cw, regional_inc, exclusive=True)
    available = annual.merge(cw[["set_id", "municipality_id"]], on="set_id")
    coverage = available.groupby(["municipality_id", "year"]).agg(n_sets_observed=("set_id", "nunique"), n_sets_complete=("complete", "sum")).reset_index()
    municipal = municipal.merge(coverage, on=["municipality_id", "year"], validate="one_to_one")
    municipal["set_coverage_pct"] = 100 * municipal.n_sets_complete / municipal.n_sets_observed
    regional_ids = set(cw[cw.municipality_id.isin(MUNICIPALITIES)].set_id)
    regional = annual[annual.set_id.isin(regional_ids)].copy()
    benchmarks = []
    scopes = {"Brasil": set(cw.set_id), "São Paulo": set(cw[cw.state.eq("SP")].set_id), "RMC": regional_ids}
    for name, ids in scopes.items():
        for year, g in annual[annual.set_id.isin(ids) & annual.complete].groupby("year"):
            benchmarks.append({"scope": name, "year": year, "n_sets": len(g), "dec_median": g.dec_h.median(),
                               "fec_median": g.fec_n.median(), "dec_p25": g.dec_h.quantile(.25), "dec_p75": g.dec_h.quantile(.75)})
    balanced = []
    complete_counts = annual[annual.complete].groupby(["cnpj", "set_id"]).year.nunique()
    balanced_keys = complete_counts[complete_counts.eq(len(YEARS))].reset_index()[["cnpj", "set_id"]]
    fixed = annual.merge(balanced_keys, on=["cnpj", "set_id"], validate="many_to_one")
    for name, ids in scopes.items():
        for year, g in fixed[fixed.set_id.isin(ids)].groupby("year"):
            balanced.append({"scope": name, "year": year, "n_sets": len(g), "dec_median": g.dec_h.median(), "fec_median": g.fec_n.median()})
    correlations = []
    for year in YEARS:
        for label, frame, x, y in [
            ("todos_conjuntos_renda_media", municipal, "income_mean", "dec_median"),
            ("todos_conjuntos_renda_mediana", municipal, "income_median", "dec_median"),
            ("somente_conjuntos_exclusivos", exclusive, "income_mean", "dec_median"),
            ("soma_mensal_sem_ajuste", municipal, "income_mean", "dec_simple_median"),
            ("fec_renda_media", municipal, "income_mean", "fec_median"),
            ("baixa_renda_dec", municipal, "low_income_pct", "dec_median"),
            ("baixa_renda_fec", municipal, "low_income_pct", "fec_median"),
            ("baixa_renda_exclusivos", exclusive, "low_income_pct", "dec_median"),
        ]:
            correlations.append({"year": year, "scenario": label, **association(frame[frame.year.eq(year)], x, y)})
    degree = cw.groupby("set_id").municipality_id.nunique()
    active_regional_ids = set(regional[regional.complete].set_id)
    diagnostics = {
        "years": YEARS, "municipalities_target": len(MUNICIPALITIES),
        "municipalities_with_income": int(regional_inc.income_mean.notna().sum()),
        "monthly_records": len(monthly), "regional_monthly_records": int(monthly.set_id.isin(regional_ids).sum()),
        "regional_sets_any_complete_year": len(active_regional_ids),
        "regional_shared_sets": int(degree.loc[list(active_regional_ids)].gt(1).sum()),
        "regional_exclusive_sets": int(degree.loc[list(active_regional_ids)].eq(1).sum()),
        "regional_set_years_incomplete": int((~regional.complete).sum()),
        "national_set_years_incomplete": int((~annual.complete).sum()),
        "set_years_without_crosswalk": int((~all_annual.set_id.isin(cw.set_id)).sum()),
        "regional_missing_dec_limits_complete": int(regional.loc[regional.complete, "dec_limit"].isna().sum()),
        "national_uc_ratio_gt2": int(annual.uc_ratio.gt(2).sum()),
        "regional_uc_ratio_gt2": int(regional.uc_ratio.gt(2).sum()),
        "crosswalk_snapshot": sorted(cw.DatGeracaoConjuntoDados.unique().tolist()),
        "continuity_snapshot": sorted(monthly.DatGeracaoConjuntoDados.unique().tolist()),
              "income_reference_year": 2022,
        "municipal_indicator_kind": "mediana não ponderada dos conjuntos associados; não é DEC municipal",
    }
    tables = {"annual_sets": annual, "regional_sets": regional,
              "municipal_context": municipal, "municipal_exclusive": exclusive,
              "regional_links": linked, "income": inc, "benchmarks": pd.DataFrame(benchmarks),
              "sensitivity": pd.DataFrame(correlations),
              "regional_monthly": monthly[monthly.set_id.isin(regional_ids)],
              "crosswalk": cw[cw.set_id.isin(regional_ids)]}
    tables["balanced_benchmarks"] = pd.DataFrame(balanced)
    for name, df in tables.items():
        df.to_csv(OUT / f"{name}.csv", index=False, float_format="%.8f")
    with sqlite3.connect(OUT / "energia_equidade.sqlite") as conn:
        for name, df in tables.items():
            df.to_sql(name, conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sets ON annual_sets(set_id, year)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_context ON municipal_context(municipality_id, year)")
    mesh = json.loads((RAW / "sp_mesh.json").read_text())
    mesh["features"] = [f for f in mesh["features"] if f["properties"]["codarea"] in MUNICIPALITIES]
    if len(mesh["features"]) != len(MUNICIPALITIES):
        raise ValueError("A malha não cobre todos os municípios previstos.")
    (OUT / "rmc.geojson").write_text(json.dumps(mesh, ensure_ascii=False))
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False))
    print(json.dumps(diagnostics, indent=2, ensure_ascii=False))
    return tables, diagnostics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", action="store_true", help="Regenerar snapshot mensal a partir do ZIP original")
    build(parser.parse_args().extract)

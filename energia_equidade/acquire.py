"""Aquisição de fontes oficiais, com cache e hashes SHA-256."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
MUNICIPALITIES = {
    "3501608": "Americana", "3503802": "Artur Nogueira", "3509502": "Campinas",
    "3512803": "Cosmópolis", "3515152": "Engenheiro Coelho", "3519055": "Holambra",
    "3519071": "Hortolândia", "3520509": "Indaiatuba", "3523404": "Itatiba",
    "3524709": "Jaguariúna", "3531803": "Monte Mor", "3532009": "Morungaba",
    "3533403": "Nova Odessa", "3536505": "Paulínia", "3537107": "Pedreira",
    "3545803": "Santa Bárbara d'Oeste", "3548005": "Santo Antônio de Posse",
    "3552403": "Sumaré", "3556206": "Valinhos", "3556701": "Vinhedo",
}


def download(name, url, refresh=False):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / name
    metadata = RAW / (name + ".source.json")
    if path.exists() and metadata.exists() and not refresh:
        record = json.loads(metadata.read_text())
        with path.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != record["sha256"]:
            raise ValueError(f"Cache alterado: {name}. Revise o arquivo ou use --refresh.")
        return record
    request = urllib.request.Request(url, headers={"User-Agent": "EnergiaEquidadeResearch/0.1", "Accept-Encoding": "identity"})
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        # Algumas APIs retornam gzip mesmo quando identity é solicitado.
        with temporary.open("rb") as f:
            is_gzip = f.read(2) == b"\x1f\x8b"
        if is_gzip:
            temporary.write_bytes(gzip.decompress(temporary.read_bytes()))
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    record = {"file": name, "url": url, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
              "bytes": path.stat().st_size, "sha256": digest}
    metadata.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Obtido: {name} ({record['bytes']:,} bytes)", flush=True)
    return record


def collect(refresh=False):
    catalog_url = "https://dadosabertos.aneel.gov.br/api/3/action/package_show?id="
    catalogs = [("aneel_catalog.json", "indicadores-coletivos-de-continuidade-dec-e-fec"),
                ("crosswalk_catalog.json", "indqual-municipio")]
    for name, slug in catalogs:
        download(name, catalog_url + slug, refresh)
    catalogs_data = [json.loads((RAW / name).read_text())["result"]["resources"] for name, _ in catalogs]
    resources = [r for group in catalogs_data for r in group]
    selection = {
        "indicadores-continuidade-coletivos-2020-2029": "continuity.zip",
        "indicadores-continuidade-coletivos-limite": "limits.csv",
        "dominio-indicadores-indqual": "indicator_dictionary.csv",
        "indqual-municipio": "crosswalk.csv",
    }
    jobs = [(selection[r['name']], r['url']) for r in resources if r['name'] in selection]
    if len(jobs) != len(selection):
        raise ValueError("Catálogo ANEEL mudou: revise os nomes dos recursos antes de continuar.")
    locations = ",".join(MUNICIPALITIES)
    jobs += [
        ("ibge_income_metadata.json", "https://servicodados.ibge.gov.br/api/v3/agregados/10295/metadados"),
        ("ibge_10296_metadata.json", "https://servicodados.ibge.gov.br/api/v3/agregados/10296/metadados"),
        ("income_classes.json", "https://apisidra.ibge.gov.br/values/t/10296/n6/" + locations + "/n3/35/n1/1/v/13604/p/2022/c2/6794/c86/95251/c386/all?formato=json"),
        ("income.json", "https://apisidra.ibge.gov.br/values/t/10295/n6/" + locations + "/n3/35/n1/1/v/13431,13534,13604/p/2022/c2/6794/c86/95251/c58/95253?formato=json"),
        ("municipality_names.json", "https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios"),
        ("sp_mesh.json", "https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio"),
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda job: download(*job, refresh=refresh), jobs))
    (ROOT / "data/sources.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    collect(parser.parse_args().refresh)

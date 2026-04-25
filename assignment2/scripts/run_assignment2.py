#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as et
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


USER_AGENT = "bioinf-assignment2/1.0 (+local-script)"
RANK_ORDER = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]


@dataclass
class BlastHit:
    accession: str
    scientific_name: str
    description: str
    evalue: float
    percent_identity: float | None = None
    query_cover: float | None = None
    bitscore: float | None = None
    gene_symbol: str = "TYR"
    gbif: dict[str, str] = field(default_factory=dict)
    major_group: str = "other"
    russian_name: str = ""
    fasta_header: str = ""
    sequence: str = ""


def log(message: str) -> None:
    print(message, flush=True)


def http_get_text(url: str, retries: int = 4, timeout: int = 60) -> str:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt == retries:
                break
            time.sleep(1.2 * attempt)
    assert last_exc is not None
    raise last_exc


def http_post_form(url: str, params: dict[str, str], retries: int = 4, timeout: int = 60) -> str:
    payload = urllib.parse.urlencode(params).encode("utf-8")
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, data=payload, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt == retries:
                break
            time.sleep(1.2 * attempt)
    assert last_exc is not None
    raise last_exc


def parse_fasta_text(text: str) -> tuple[str, str] | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].startswith(">"):
        return None
    header = lines[0][1:].strip()
    raw = "".join(lines[1:]).upper().replace("U", "T")
    seq = "".join(ch for ch in raw if ch in {"A", "C", "G", "T", "N", "R", "Y", "K", "M", "S", "W", "B", "D", "H", "V"})
    if not header or len(seq) < 50:
        return None
    return header, seq


def read_first_fasta(path: Path) -> tuple[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {path}")
    parsed = parse_fasta_text(path.read_text(encoding="utf-8", errors="replace"))
    if parsed is None:
        raise ValueError(f"Cannot parse FASTA file: {path}")
    return parsed


def detect_dialect(text: str) -> csv.Dialect:
    sample = text[:8000]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        return csv.get_dialect("excel")


def parse_float(value: str | None, default: float | None = None) -> float | None:
    if value is None:
        return default
    v = value.strip().replace(",", ".").replace("%", "")
    if not v or v.lower() in {"na", "n/a", "nan", "-"}:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def normalize_accession(value: str) -> str:
    v = value.strip()
    if "|" in v:
        parts = [p for p in v.split("|") if p.strip()]
        if parts:
            v = parts[-1]
    v = v.split()[0]
    return v.strip(",;")


def pick_first(row: dict[str, str], names: list[str]) -> str:
    direct = {k.strip(): (v or "").strip() for k, v in row.items()}
    lowered = {k.lower(): v for k, v in direct.items()}
    for name in names:
        if name in direct and direct[name]:
            return direct[name]
        alt = lowered.get(name.lower(), "")
        if alt:
            return alt
    return ""


def extract_species_from_description(description: str) -> str:
    matches = re.findall(r"\[([^\[\]]+)\]", description)
    if matches:
        return matches[-1].strip()
    return ""


def infer_gene_symbol(description: str) -> str:
    match = re.search(r"\(([A-Za-z0-9\-]{2,15})\)", description)
    if match:
        candidate = match.group(1)
        if any(ch.isalpha() for ch in candidate):
            return candidate.upper()
    if "tyrosinase" in description.lower():
        return "TYR"
    return "TYR"


def is_likely_accession(value: str) -> bool:
    v = normalize_accession(value)
    return bool(re.fullmatch(r"[A-Za-z]{1,6}_?\d+(?:\.\d+)?", v))


def merge_best_by_species(hits: list[BlastHit]) -> list[BlastHit]:
    by_species: dict[str, BlastHit] = {}
    for hit in hits:
        key = hit.scientific_name.lower().strip()
        if not key:
            continue
        prev = by_species.get(key)
        if prev is None:
            by_species[key] = hit
            continue
        prev_metric = (prev.evalue, -(prev.bitscore or 0.0))
        curr_metric = (hit.evalue, -(hit.bitscore or 0.0))
        if curr_metric < prev_metric:
            by_species[key] = hit
    merged = list(by_species.values())
    merged.sort(key=lambda h: (h.evalue, -(h.bitscore or 0.0)))
    return merged


def parse_hits_from_header_table(text: str, dialect: csv.Dialect) -> list[BlastHit]:
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    raw_rows = [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader]
    if not raw_rows:
        return []

    parsed: list[BlastHit] = []
    for row in raw_rows:
        accession = pick_first(
            row,
            [
                "Accession",
                "Subject acc.ver",
                "Subject acc.",
                "saccver",
                "sacc",
                "accession",
            ],
        )
        accession = normalize_accession(accession) if accession else ""
        if not accession:
            continue

        description = pick_first(
            row,
            [
                "Description",
                "Subject title",
                "subject title",
                "title",
            ],
        )
        scientific_name = pick_first(
            row,
            [
                "Scientific Name",
                "scientific name",
                "Organism",
                "organism",
                "Species",
            ],
        )
        if not scientific_name:
            scientific_name = extract_species_from_description(description)
        scientific_name = scientific_name.strip()
        if not scientific_name:
            continue
        if scientific_name.lower() in {"homo sapiens", "human"}:
            continue

        evalue = parse_float(
            pick_first(
                row,
                ["E value", "Expect value", "expect", "evalue", "E-value"],
            ),
            default=999.0,
        )
        bitscore = parse_float(
            pick_first(
                row,
                ["Max Score", "Bit score", "score", "Total score"],
            )
        )
        pident = parse_float(
            pick_first(
                row,
                ["Per. Ident", "Percent identity", "% identity", "pident"],
            )
        )
        qcov = parse_float(
            pick_first(
                row,
                ["Query Cover", "Query cover", "qcovs", "qcovhsp"],
            )
        )
        parsed.append(
            BlastHit(
                accession=accession,
                scientific_name=scientific_name,
                description=description,
                evalue=float(evalue if evalue is not None else 999.0),
                percent_identity=pident,
                query_cover=qcov,
                bitscore=bitscore,
                gene_symbol=infer_gene_symbol(description),
            )
        )
    return merge_best_by_species(parsed)


def parse_hits_from_accession_table(text: str, dialect: csv.Dialect) -> list[BlastHit]:
    reader = csv.reader(io.StringIO(text), dialect=dialect)
    by_acc: dict[str, BlastHit] = {}
    for row in reader:
        if not row:
            continue
        if len(row) < 2:
            continue
        qacc = normalize_accession(row[0])
        sacc = normalize_accession(row[1])
        if not is_likely_accession(sacc):
            continue
        if qacc and sacc == qacc:
            continue
        pident = parse_float(row[2] if len(row) > 2 else None)
        evalue = parse_float(row[10] if len(row) > 10 else None, default=999.0)
        bitscore = parse_float(row[11] if len(row) > 11 else None)

        candidate = BlastHit(
            accession=sacc,
            scientific_name="",
            description="",
            evalue=float(evalue if evalue is not None else 999.0),
            percent_identity=pident,
            query_cover=None,
            bitscore=bitscore,
            gene_symbol="TYR",
        )
        prev = by_acc.get(sacc)
        if prev is None:
            by_acc[sacc] = candidate
            continue
        prev_metric = (prev.evalue, -(prev.bitscore or 0.0))
        curr_metric = (candidate.evalue, -(candidate.bitscore or 0.0))
        if curr_metric < prev_metric:
            by_acc[sacc] = candidate

    hits = list(by_acc.values())
    hits.sort(key=lambda h: (h.evalue, -(h.bitscore or 0.0)))
    return hits


def read_blast_hits(csv_path: Path) -> list[BlastHit]:
    text = csv_path.read_text(encoding="utf-8-sig", errors="replace")
    if not text.strip():
        raise ValueError(f"BLAST CSV is empty: {csv_path}")

    dialect = detect_dialect(text)
    preview_reader = csv.reader(io.StringIO(text), dialect=dialect)
    first_row = next(preview_reader, [])
    first_row_stripped = [cell.strip() for cell in first_row]
    lowered = {cell.lower() for cell in first_row_stripped}
    header_markers = {
        "accession",
        "subject acc.ver",
        "subject title",
        "scientific name",
        "description",
        "e value",
        "expect value",
        "per. ident",
        "query cover",
    }

    has_header = bool(lowered.intersection(header_markers))
    if has_header:
        hits = parse_hits_from_header_table(text, dialect)
        if hits:
            return hits

    # Fallback: BLAST alignment-style table without header
    hits = parse_hits_from_accession_table(text, dialect)
    if hits:
        return hits
    return []


def gbif_match(scientific_name: str) -> dict[str, str]:
    url = "https://api.gbif.org/v1/species/match?name=" + urllib.parse.quote(scientific_name)
    try:
        data = json.loads(http_get_text(url, retries=3))
    except Exception:  # noqa: BLE001
        return {}
    result: dict[str, str] = {}
    for key in ["kingdom", "phylum", "class", "order", "family", "genus", "species"]:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            result[key] = value.strip()
    usage_key = data.get("usageKey")
    if usage_key is not None:
        result["usageKey"] = str(usage_key)
    return result


def gbif_russian_name(usage_key: str) -> str:
    url = f"https://api.gbif.org/v1/species/{usage_key}/vernacularNames"
    try:
        payload = json.loads(http_get_text(url, retries=3))
    except Exception:  # noqa: BLE001
        return ""
    results = payload.get("results", [])
    if not isinstance(results, list):
        return ""
    for entry in results:
        if not isinstance(entry, dict):
            continue
        lang = str(entry.get("language") or "").lower()
        if lang in {"ru", "rus", "russian"}:
            value = str(entry.get("vernacularName") or "").strip()
            if value:
                return value
    return ""


def wikidata_ru_name_by_sciname(scientific_name: str) -> str:
    escaped = scientific_name.replace("\\", "\\\\").replace('"', '\\"')
    query = (
        "SELECT ?ru WHERE { "
        f'?item wdt:P225 "{escaped}" . '
        'OPTIONAL { ?item rdfs:label ?ru FILTER (lang(?ru)="ru") } '
        "} LIMIT 1"
    )
    url = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(query)
    try:
        text = http_get_text(url, retries=3, timeout=70)
        data = json.loads(text)
    except Exception:  # noqa: BLE001
        return ""
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return ""
    ru = bindings[0].get("ru", {}).get("value", "")
    return str(ru).strip()


def determine_major_group(gbif_data: dict[str, str]) -> str:
    cls = gbif_data.get("class", "").lower()
    if cls == "mammalia":
        return "mammal"
    if cls == "aves":
        return "bird"
    if cls == "amphibia":
        return "amphibian"
    if cls in {"actinopterygii", "chondrichthyes", "sarcopterygii"}:
        return "fish"
    if cls in {"reptilia", "sauropsida"}:
        return "reptile"
    return "other"


def annotate_hits_with_taxonomy(hits: list[BlastHit]) -> None:
    for hit in hits:
        hit.gbif = gbif_match(hit.scientific_name)
        hit.major_group = determine_major_group(hit.gbif)
        usage_key = hit.gbif.get("usageKey", "")
        hit.russian_name = gbif_russian_name(usage_key) if usage_key else ""


def choose_hits(hits: list[BlastHit], target_count: int) -> list[BlastHit]:
    non_mammals = [h for h in hits if h.major_group != "mammal"]
    mammals = [h for h in hits if h.major_group == "mammal"]

    selected: list[BlastHit] = []
    for hit in non_mammals:
        if len(selected) >= target_count:
            break
        selected.append(hit)
    if len(selected) < target_count:
        for hit in mammals:
            if len(selected) >= target_count:
                break
            selected.append(hit)

    if len(selected) < target_count:
        raise RuntimeError(
            f"Not enough unique homolog species in CSV: got {len(selected)}, expected at least {target_count}."
        )
    return selected


def fetch_fasta_for_accession(accession: str) -> tuple[str, str]:
    ncbi_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
        "db=nuccore&id="
        + urllib.parse.quote(accession)
        + "&rettype=fasta&retmode=text"
    )
    dbfetch_refseq_url = (
        "https://www.ebi.ac.uk/Tools/dbfetch/dbfetch?db=refseqn&id="
        + urllib.parse.quote(accession)
        + "&format=fasta&style=raw"
    )
    dbfetch_embl_url = (
        "https://www.ebi.ac.uk/Tools/dbfetch/dbfetch?db=embl&id="
        + urllib.parse.quote(accession)
        + "&format=fasta&style=raw"
    )
    for url in [dbfetch_refseq_url, dbfetch_embl_url, ncbi_url]:
        try:
            parsed = parse_fasta_text(http_get_text(url, retries=3))
            if parsed is not None:
                return parsed
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError(f"Failed to fetch FASTA for accession: {accession}")


def extract_scientific_name_from_header(header: str) -> str:
    if not header:
        return ""
    text = re.sub(r"^\S+\s*", "", header).strip()
    if "PREDICTED:" in text:
        text = text.split("PREDICTED:", 1)[1].strip()
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]*", text)
    for i in range(len(tokens) - 1):
        genus = tokens[i]
        species = tokens[i + 1]
        if len(genus) < 2 or len(species) < 2:
            continue
        if genus[0].isupper() and genus[1:].islower() and species.islower():
            return f"{genus} {species}"
    return ""


def hydrate_hits_from_accessions(raw_hits: list[BlastHit], target_count: int) -> list[BlastHit]:
    by_species: dict[str, BlastHit] = {}
    seen_acc: set[str] = set()
    max_fetch = max(80, target_count * 8)
    fetch_count = 0

    for hit in raw_hits:
        acc = normalize_accession(hit.accession)
        if not acc or acc in seen_acc:
            continue
        seen_acc.add(acc)

        if fetch_count >= max_fetch and len(by_species) >= target_count * 3:
            break

        try:
            header, seq = fetch_fasta_for_accession(acc)
        except Exception:  # noqa: BLE001
            continue
        fetch_count += 1

        scientific_name = extract_scientific_name_from_header(header)
        if not scientific_name:
            continue
        if scientific_name.lower() in {"homo sapiens", "human"}:
            continue

        candidate = BlastHit(
            accession=acc,
            scientific_name=scientific_name,
            description=header,
            evalue=hit.evalue,
            percent_identity=hit.percent_identity,
            query_cover=hit.query_cover,
            bitscore=hit.bitscore,
            gene_symbol=hit.gene_symbol,
            fasta_header=header,
            sequence=seq,
        )
        ensure_gene_symbol(candidate)
        key = scientific_name.lower()
        prev = by_species.get(key)
        if prev is None:
            by_species[key] = candidate
            continue
        prev_metric = (prev.evalue, -(prev.bitscore or 0.0))
        curr_metric = (candidate.evalue, -(candidate.bitscore or 0.0))
        if curr_metric < prev_metric:
            by_species[key] = candidate

    hydrated = list(by_species.values())
    hydrated.sort(key=lambda h: (h.evalue, -(h.bitscore or 0.0)))
    return hydrated


def ensure_gene_symbol(hit: BlastHit) -> None:
    if hit.gene_symbol and hit.gene_symbol != "TYR":
        return
    lower_header = hit.fasta_header.lower()
    if "tyrosinase" in lower_header:
        hit.gene_symbol = "TYR"
        return
    match = re.search(r"\(([A-Za-z0-9\-]{2,15})\)", hit.fasta_header)
    if match:
        hit.gene_symbol = match.group(1).upper()
    else:
        hit.gene_symbol = "TYR"


def build_output_header(hit: BlastHit, index: int) -> str:
    species_tag = re.sub(r"[^A-Za-z0-9]+", "_", hit.scientific_name).strip("_")
    symbol_tag = re.sub(r"[^A-Za-z0-9]+", "_", hit.gene_symbol).strip("_")
    return f"hit{index:02d}_{species_tag}_{symbol_tag}_{hit.accession}"


def write_fasta(path: Path, records: list[tuple[str, str]]) -> None:
    with path.open("w", encoding="ascii") as fh:
        for header, seq in records:
            fh.write(f">{header}\n")
            for i in range(0, len(seq), 70):
                fh.write(seq[i : i + 70] + "\n")


def clustalo_run(fasta_text: str, title: str) -> tuple[str, str]:
    submit_url = "https://www.ebi.ac.uk/Tools/services/rest/clustalo/run"
    params = {
        "email": "student@example.com",
        "title": title,
        "stype": "dna",
        "outfmt": "clustal_num",
        "sequence": fasta_text,
    }
    job_id = http_post_form(submit_url, params, retries=3, timeout=90).strip()
    if not job_id:
        raise RuntimeError("Failed to submit Clustal Omega job.")

    status_url = f"https://www.ebi.ac.uk/Tools/services/rest/clustalo/status/{job_id}"
    for _ in range(120):
        status = http_get_text(status_url, retries=3, timeout=60).strip().upper()
        if status == "FINISHED":
            break
        if status in {"ERROR", "FAILURE"}:
            raise RuntimeError(f"Clustal Omega job failed: {job_id} ({status})")
        time.sleep(3)
    else:
        raise RuntimeError(f"Clustal Omega job timeout: {job_id}")

    types_url = f"https://www.ebi.ac.uk/Tools/services/rest/clustalo/resulttypes/{job_id}"
    types_xml = http_get_text(types_url, retries=3, timeout=60)
    result_id = "aln-clustal_num"
    try:
        root = et.fromstring(types_xml)
        all_ids = [node.text for node in root.findall(".//identifier") if node.text]
        for identifier in all_ids:
            if "clustal" in identifier:
                result_id = identifier
                break
    except et.ParseError:
        pass

    result_url = f"https://www.ebi.ac.uk/Tools/services/rest/clustalo/result/{job_id}/{result_id}"
    alignment = http_get_text(result_url, retries=3, timeout=120)
    return job_id, alignment


def parse_clustal_alignment(text: str) -> dict[str, str]:
    seqs: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        upper = line.upper()
        if upper.startswith("CLUSTAL") or upper.startswith("MUSCLE"):
            continue
        if line[0].isspace():
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        name, fragment = parts[0], parts[1]
        if not re.fullmatch(r"[A-Za-z\-]+", fragment):
            continue
        seqs[name] = seqs.get(name, "") + fragment.upper()
    return seqs


def contiguous_intervals(values: list[int], min_len: int = 15) -> list[tuple[int, int]]:
    if not values:
        return []
    intervals: list[tuple[int, int]] = []
    start = values[0]
    prev = values[0]
    for pos in values[1:]:
        if pos == prev + 1:
            prev = pos
            continue
        if prev - start + 1 >= min_len:
            intervals.append((start, prev))
        start = pos
        prev = pos
    if prev - start + 1 >= min_len:
        intervals.append((start, prev))
    return intervals


def analyze_conservation(seqs: dict[str, str]) -> dict[str, object]:
    if not seqs:
        raise ValueError("No sequences found in Clustal alignment.")
    names = list(seqs.keys())
    lengths = {len(seqs[name]) for name in names}
    if len(lengths) != 1:
        raise ValueError("Alignment has inconsistent sequence lengths.")
    aln_len = lengths.pop()

    full_identity: list[int] = []
    high_identity: list[int] = []
    fractions: list[float] = []
    min_non_gap = max(3, int(round(len(names) * 0.8)))

    for idx in range(aln_len):
        column = [seqs[name][idx] for name in names]
        residues = [ch for ch in column if ch != "-"]
        if not residues:
            fractions.append(0.0)
            continue
        top_count = max(Counter(residues).values())
        frac = top_count / len(residues)
        fractions.append(frac)
        pos = idx + 1
        if len(residues) == len(names) and frac == 1.0:
            full_identity.append(pos)
        if len(residues) >= min_non_gap and frac >= 0.9:
            high_identity.append(pos)

    high_runs = contiguous_intervals(high_identity, min_len=15)
    full_runs = contiguous_intervals(full_identity, min_len=8)
    avg_identity = sum(fractions) / len(fractions) if fractions else 0.0

    return {
        "sequence_count": len(names),
        "alignment_length": aln_len,
        "avg_column_identity": avg_identity,
        "full_identity_positions": full_identity,
        "high_identity_positions": high_identity,
        "high_identity_runs": high_runs,
        "full_identity_runs": full_runs,
    }


def rank_label_ru(rank: str) -> str:
    mapping = {
        "kingdom": "царство",
        "phylum": "тип",
        "class": "класс",
        "order": "отряд",
        "family": "семейство",
        "genus": "род",
        "species": "вид",
    }
    return mapping.get(rank, rank)


def compute_lca(hits: list[BlastHit]) -> tuple[str, str]:
    lca_rank = ""
    lca_name = ""
    for rank in RANK_ORDER:
        values = [h.gbif.get(rank, "").strip() for h in hits]
        if not values or any(not v for v in values):
            break
        unique = sorted(set(values))
        if len(unique) == 1:
            lca_rank = rank
            lca_name = unique[0]
            continue
        break
    if not lca_name:
        return "kingdom", "Animalia"
    return lca_rank, lca_name


def write_homologs_table(path: Path, hits: list[BlastHit]) -> None:
    cols = [
        "accession",
        "gene_symbol",
        "scientific_name",
        "russian_name",
        "major_group",
        "evalue",
        "query_cover",
        "percent_identity",
        "description",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        for h in hits:
            writer.writerow(
                {
                    "accession": h.accession,
                    "gene_symbol": h.gene_symbol,
                    "scientific_name": h.scientific_name,
                    "russian_name": h.russian_name,
                    "major_group": h.major_group,
                    "evalue": f"{h.evalue:.3e}",
                    "query_cover": "" if h.query_cover is None else f"{h.query_cover:.2f}",
                    "percent_identity": "" if h.percent_identity is None else f"{h.percent_identity:.2f}",
                    "description": h.description,
                }
            )


def write_markdown_conservation(path: Path, stats: dict[str, object]) -> None:
    high_runs = stats["high_identity_runs"]
    full_runs = stats["full_identity_runs"]
    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Анализ консервативности множественного выравнивания\n\n")
        fh.write(f"- Число последовательностей: {stats['sequence_count']}\n")
        fh.write(f"- Длина выравнивания: {stats['alignment_length']}\n")
        fh.write(f"- Средняя идентичность по колонкам: {stats['avg_column_identity'] * 100:.2f}%\n")
        fh.write(f"- Полностью консервативных позиций: {len(stats['full_identity_positions'])}\n")
        fh.write(f"- Высококонсервативных позиций (>=90%): {len(stats['high_identity_positions'])}\n\n")
        fh.write("## Консервативные участки\n\n")
        if high_runs:
            fh.write("Участки с идентичностью >=90% (длина >=15):\n")
            for start, end in high_runs:
                fh.write(f"- позиции {start}-{end} (длина {end - start + 1})\n")
            fh.write("\n")
        else:
            fh.write("Длинные участки с идентичностью >=90% не обнаружены.\n\n")
        if full_runs:
            fh.write("Полностью консервативные непрерывные участки (длина >=8):\n")
            for start, end in full_runs:
                fh.write(f"- позиции {start}-{end} (длина {end - start + 1})\n")
            fh.write("\n")
        else:
            fh.write("Длинные полностью консервативные участки не обнаружены.\n\n")
        fh.write(
            "Итог: для выбранных ортологов TYR наблюдаются консервативные области, "
            "вероятно связанные с функционально важными регионами гена.\n"
        )


def write_taxon_summary(path: Path, lca_rank: str, lca_name: str, lca_name_ru: str, hits: list[BlastHit]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Объединяющий таксон\n\n")
        fh.write(f"- Ближайший общий таксон (лат.): **{lca_name}**\n")
        if lca_name_ru:
            fh.write(f"- Название таксона (рус.): **{lca_name_ru}**\n")
        else:
            fh.write("- Название таксона (рус.): **не найдено автоматически**\n")
        fh.write(f"- Таксономический ранг: **{rank_label_ru(lca_rank)}**\n\n")
        fh.write("## Краткое описание\n\n")
        fh.write(
            f"Таксон {lca_name} является ближайшим общим таксоном для выбранных видов, "
            "полученных по результатам BLAST. Он объединяет все исследованные последовательности "
            "и отражает их эволюционное родство.\n\n"
        )
        fh.write("Виды, использованные для определения таксона:\n")
        for hit in hits:
            ru = f" ({hit.russian_name})" if hit.russian_name else ""
            fh.write(f"- {hit.scientific_name}{ru}\n")


def write_report(
    path: Path,
    gene_symbol: str,
    target_count: int,
    selected_hits: list[BlastHit],
    lca_rank: str,
    lca_name: str,
    lca_name_ru: str,
) -> None:
    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Домашнее задание 2: представленность гена в таксонах\n\n")
        fh.write("## 1) Ответы на разминочные вопросы\n\n")
        fh.write(
            "По уточнению преподавателя фразу про разминочные вопросы в этом задании "
            "нужно игнорировать, поэтому отдельные ответы не требуются.\n\n"
        )
        fh.write("## 2) Название выбранного гена (Gene Symbol)\n\n")
        fh.write(f"- **{gene_symbol}**\n\n")
        fh.write("## 3) Параметры BLAST\n\n")
        fh.write("- Платформа: NCBI BLAST (веб-интерфейс)\n")
        fh.write("- Program: blastn\n")
        fh.write("- Database: nt\n")
        fh.write("- Program selection: More dissimilar sequences (discontiguous megablast)\n")
        fh.write("- Exclude: Homo sapiens (NOT txid9606[ORGN])\n")
        fh.write("- Max target sequences: 250\n")
        fh.write(f"- Отобрано гомологов для анализа: {target_count} видов\n\n")
        fh.write("## 4) Таблица гомологичных генов и видов\n\n")
        fh.write("- Файл: `assignment2/results/homologs_table.csv`\n")
        fh.write("- В таблице указаны: Gene Symbol, латинское название вида, русское название вида.\n\n")
        fh.write("## 5) Файл множественного выравнивания (Clustal)\n\n")
        fh.write("- Файл: `assignment2/results/multiple_alignment.aln`\n\n")
        fh.write("## 6) Краткий анализ консервативности\n\n")
        fh.write("- Файл: `assignment2/results/conservation_analysis.md`\n\n")
        fh.write("## 7) Объединяющий таксон\n\n")
        fh.write(f"- Латинское название: **{lca_name}**\n")
        if lca_name_ru:
            fh.write(f"- Русское название: **{lca_name_ru}**\n")
        else:
            fh.write("- Русское название: **не найдено автоматически**\n")
        fh.write(f"- Ранг: **{rank_label_ru(lca_rank)}**\n")
        fh.write("- Краткое описание: см. `assignment2/results/taxon_summary.md`\n\n")
        fh.write("## Использованные виды\n\n")
        for hit in selected_hits:
            ru = f" ({hit.russian_name})" if hit.russian_name else ""
            fh.write(f"- {hit.scientific_name}{ru}, accession {hit.accession}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Assignment 2 pipeline: TYR homologs, MSA, conservation, taxonomy.")
    parser.add_argument("--csv", default="assignment2/input/blast_hits.csv", help="Path to BLAST CSV (Hit table)")
    parser.add_argument(
        "--query-fasta",
        default="assignment1/data/fasta/TYR_Homo_sapiens_NM_000372.5.fasta",
        help="Path to human TYR FASTA query",
    )
    parser.add_argument("--target-hits", type=int, default=10, help="Minimum number of homolog species to keep")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    csv_path = (root / args.csv).resolve()
    query_path = (root / args.query_fasta).resolve()
    out_data = root / "assignment2" / "data"
    out_results = root / "assignment2" / "results"
    out_data.mkdir(parents=True, exist_ok=True)
    out_results.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        log(f"BLAST CSV not found: {csv_path}")
        log("Put Hit table CSV into assignment2/input/blast_hits.csv and rerun.")
        return 2

    log("Reading BLAST CSV...")
    hits = read_blast_hits(csv_path)
    if not hits:
        raise RuntimeError("Could not parse BLAST CSV. Re-export Hit table in CSV format.")

    if not any(h.scientific_name for h in hits):
        log("Detected accession-only BLAST table. Resolving species metadata from accession...")
        hits = hydrate_hits_from_accessions(hits, args.target_hits)
        if not hits:
            raise RuntimeError("Failed to resolve species from accession list. Please export full BLAST Hit table CSV.")

    hits = [h for h in hits if h.scientific_name and h.scientific_name.lower() not in {"homo sapiens", "human"}]
    if len(hits) < args.target_hits:
        raise RuntimeError(
            f"Only {len(hits)} unique non-human species available after metadata enrichment. Need at least {args.target_hits}."
        )

    log("Annotating taxonomy and Russian names...")
    annotate_hits_with_taxonomy(hits)
    selected = choose_hits(hits, args.target_hits)
    selected.sort(key=lambda h: (h.evalue, h.scientific_name.lower()))

    log("Loading human TYR query FASTA...")
    query_header, query_seq = read_first_fasta(query_path)
    write_fasta(out_data / "query_human_TYR.fasta", [("human_Homo_sapiens_TYR_NM_000372_5", query_seq)])

    log("Fetching FASTA for selected homologs...")
    for idx, hit in enumerate(selected, start=1):
        if not hit.sequence:
            header, seq = fetch_fasta_for_accession(hit.accession)
            hit.fasta_header = header
            hit.sequence = seq
        if not hit.scientific_name:
            hit.scientific_name = extract_scientific_name_from_header(hit.fasta_header)
        if not hit.description:
            hit.description = hit.fasta_header
        ensure_gene_symbol(hit)
        if not hit.russian_name:
            hit.russian_name = wikidata_ru_name_by_sciname(hit.scientific_name)
        hit.fasta_header = build_output_header(hit, idx)

    records: list[tuple[str, str]] = [("human_Homo_sapiens_TYR_NM_000372_5", query_seq)]
    records.extend((hit.fasta_header, hit.sequence) for hit in selected)
    homologs_fasta_path = out_data / "homologs.fasta"
    write_fasta(homologs_fasta_path, records)

    write_homologs_table(out_results / "homologs_table.csv", selected)
    with (out_results / "selected_hits.json").open("w", encoding="utf-8") as fh:
        json.dump(
            [
                {
                    "accession": h.accession,
                    "gene_symbol": h.gene_symbol,
                    "scientific_name": h.scientific_name,
                    "russian_name": h.russian_name,
                    "major_group": h.major_group,
                    "evalue": h.evalue,
                    "query_cover": h.query_cover,
                    "percent_identity": h.percent_identity,
                    "description": h.description,
                }
                for h in selected
            ],
            fh,
            ensure_ascii=False,
            indent=2,
        )

    log("Submitting Clustal Omega alignment job...")
    fasta_text = homologs_fasta_path.read_text(encoding="ascii")
    job_id, alignment = clustalo_run(fasta_text, title="bioinf-assignment2-tyr")
    alignment_path = out_results / "multiple_alignment.aln"
    alignment_path.write_text(alignment, encoding="utf-8")
    log(f"Clustal Omega job finished: {job_id}")

    seqs = parse_clustal_alignment(alignment)
    stats = analyze_conservation(seqs)
    with (out_results / "conservation_stats.json").open("w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)
    write_markdown_conservation(out_results / "conservation_analysis.md", stats)

    lca_rank, lca_name = compute_lca(selected)
    lca_name_ru = wikidata_ru_name_by_sciname(lca_name)
    write_taxon_summary(out_results / "taxon_summary.md", lca_rank, lca_name, lca_name_ru, selected)

    write_report(
        out_results / "report.md",
        gene_symbol="TYR",
        target_count=args.target_hits,
        selected_hits=selected,
        lca_rank=lca_rank,
        lca_name=lca_name,
        lca_name_ru=lca_name_ru,
    )

    log("Done.")
    log(f"Generated files in: {out_results}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

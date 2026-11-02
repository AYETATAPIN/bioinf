from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
INPUT_VCF = ROOT / "data" / "student_18.vcf"
RAW_DIR = ROOT / "results" / "raw"
TABLE_DIR = ROOT / "results" / "tables"

ENSEMBL_URL = "https://rest.ensembl.org/vep/human/region"
NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@dataclass(frozen=True)
class Variant:
    chrom: str
    pos: int
    rsid: str
    ref: str
    alt: str

    @property
    def coordinate(self) -> str:
        return f"chr{self.chrom}:{self.pos}:{self.ref}>{self.alt}"

    @property
    def vep_input(self) -> str:
        return f"{self.chrom} {self.pos} {self.rsid} {self.ref} {self.alt} . . ."


def read_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "bioinf-assignment-4/1.0"})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def post_json(url: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "bioinf-assignment-4/1.0",
        },
    )
    with urlopen(request, timeout=120) as response:
        result: list[dict[str, Any]] = json.load(response)
    return result


def parse_vcf(path: Path) -> list[Variant]:
    variants: list[Variant] = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("#"):
                continue
            chrom, pos, rsid, ref, alt, *_ = line.rstrip("\n").split("\t")
            variants.append(Variant(chrom=chrom, pos=int(pos), rsid=rsid, ref=ref, alt=alt))
    return variants


def fetch_vep(variants: list[Variant]) -> list[dict[str, Any]]:
    payload = {
        "variants": [variant.vep_input for variant in variants],
        "canonical": 1,
        "mane": 1,
        "hgvs": 1,
        "variant_class": 1,
    }
    return post_json(ENSEMBL_URL, payload)


def fetch_clinvar(rsid: str) -> dict[str, Any] | None:
    search_query = urlencode(
        {"db": "clinvar", "term": f"{rsid}[variant id]", "retmode": "json"}
    )
    search = read_json(f"{NCBI_EUTILS}/esearch.fcgi?{search_query}")
    identifiers = search["esearchresult"]["idlist"]
    if not identifiers:
        return None
    summary_query = urlencode(
        {"db": "clinvar", "id": ",".join(identifiers), "retmode": "json"}
    )
    summary = read_json(f"{NCBI_EUTILS}/esummary.fcgi?{summary_query}")
    records = [summary["result"][identifier] for identifier in identifiers]
    return {"rsid": rsid, "records": records}


def consequence_rank(term: str) -> int:
    order = [
        "transcript_ablation",
        "splice_acceptor_variant",
        "splice_donor_variant",
        "stop_gained",
        "frameshift_variant",
        "stop_lost",
        "start_lost",
        "transcript_amplification",
        "inframe_insertion",
        "inframe_deletion",
        "missense_variant",
        "protein_altering_variant",
        "splice_region_variant",
        "incomplete_terminal_codon_variant",
        "start_retained_variant",
        "stop_retained_variant",
        "synonymous_variant",
        "coding_sequence_variant",
        "mature_miRNA_variant",
        "5_prime_UTR_variant",
        "3_prime_UTR_variant",
        "non_coding_transcript_exon_variant",
        "intron_variant",
        "NMD_transcript_variant",
        "non_coding_transcript_variant",
        "upstream_gene_variant",
        "downstream_gene_variant",
        "TFBS_ablation",
        "TFBS_amplification",
        "TF_binding_site_variant",
        "regulatory_region_ablation",
        "regulatory_region_amplification",
        "feature_elongation",
        "regulatory_region_variant",
        "feature_truncation",
        "intergenic_variant",
    ]
    try:
        return order.index(term)
    except ValueError:
        return len(order)


def choose_transcript(annotation: dict[str, Any]) -> dict[str, Any]:
    transcripts = annotation.get("transcript_consequences", [])
    if not transcripts:
        return {}
    severe_term = annotation.get("most_severe_consequence", "")
    matching = [
        transcript
        for transcript in transcripts
        if severe_term in transcript.get("consequence_terms", [])
    ] or transcripts

    def priority(transcript: dict[str, Any]) -> tuple[int, int, int, str]:
        terms = transcript.get("consequence_terms", [])
        best_term_rank = min((consequence_rank(term) for term in terms), default=999)
        return (
            0 if transcript.get("mane_select") else 1,
            0 if transcript.get("canonical") else 1,
            0 if transcript.get("biotype") == "protein_coding" else 1,
            f"{best_term_rank:03d}:{transcript.get('transcript_id', '')}",
        )

    return min(matching, key=priority)


def matching_colocated(annotation: dict[str, Any], variant: Variant) -> dict[str, Any]:
    for colocated in annotation.get("colocated_variants", []):
        if colocated.get("id") == variant.rsid:
            return colocated
        alleles = colocated.get("allele_string", "").split("/")
        if variant.ref in alleles and variant.alt in alleles:
            return colocated
    return {}


def summarize_clinvar(payload: dict[str, Any] | None) -> tuple[str, str, str, str]:
    if payload is None:
        return "нет", "", "", ""
    records = payload["records"]
    descriptions: list[str] = []
    reviews: list[str] = []
    accessions: list[str] = []
    traits: list[str] = []
    for record in records:
        accessions.append(record.get("accession_version") or record.get("accession", ""))
        classification = record.get("germline_classification", {})
        if classification.get("description"):
            descriptions.append(classification["description"])
        if classification.get("review_status"):
            reviews.append(classification["review_status"])
        for trait in classification.get("trait_set", []):
            if trait.get("trait_name"):
                traits.append(trait["trait_name"])
    return (
        "да",
        "; ".join(dict.fromkeys(descriptions)) or "не указана",
        "; ".join(dict.fromkeys(reviews)) or "не указан",
        "; ".join(dict.fromkeys(accessions + traits)),
    )


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    variants = parse_vcf(INPUT_VCF)
    if len(variants) != 50:
        raise ValueError(f"Ожидалось 50 вариантов, найдено {len(variants)}")

    vep = fetch_vep(variants)
    (RAW_DIR / "vep_response.json").write_text(
        json.dumps(vep, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    vep_by_input = {record["input"]: record for record in vep}

    clinvar: list[dict[str, Any]] = []
    for index, variant in enumerate(variants):
        record = fetch_clinvar(variant.rsid)
        clinvar.append({"rsid": variant.rsid, "result": record})
        if index < len(variants) - 1:
            time.sleep(0.35)
    (RAW_DIR / "clinvar_response.json").write_text(
        json.dumps(clinvar, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    clinvar_by_rsid = {item["rsid"]: item["result"] for item in clinvar}

    fields = [
        "variant",
        "chromosome",
        "position_grch38",
        "ref",
        "alt",
        "rsid",
        "gene",
        "most_severe_consequence",
        "impact",
        "selected_transcript",
        "transcript_selection_rule",
        "hgvsc",
        "hgvsp",
        "sift",
        "polyphen",
        "gnomad_exomes_af",
        "gnomad_genomes_af",
        "clinvar_present",
        "clinvar_significance",
        "clinvar_review_status",
        "clinvar_accession_and_traits",
    ]
    rows: list[dict[str, Any]] = []
    gnomad_export: list[dict[str, Any]] = []
    for variant in variants:
        annotation = vep_by_input[variant.vep_input]
        transcript = choose_transcript(annotation)
        colocated = matching_colocated(annotation, variant)
        frequencies = colocated.get("frequencies", {}).get(variant.alt, {})
        gnomad_exomes = frequencies.get("gnomade")
        gnomad_genomes = frequencies.get("gnomadg")
        clinvar_present, significance, review_status, clinvar_details = summarize_clinvar(
            clinvar_by_rsid[variant.rsid]
        )
        row = {
            "variant": variant.coordinate,
            "chromosome": variant.chrom,
            "position_grch38": variant.pos,
            "ref": variant.ref,
            "alt": variant.alt,
            "rsid": variant.rsid,
            "gene": transcript.get("gene_symbol") or transcript.get("gene_id", ""),
            "most_severe_consequence": annotation.get("most_severe_consequence", ""),
            "impact": transcript.get("impact", ""),
            "selected_transcript": transcript.get("transcript_id", ""),
            "transcript_selection_rule": "most severe consequence; MANE Select > canonical > protein-coding > first",
            "hgvsc": transcript.get("hgvsc", ""),
            "hgvsp": transcript.get("hgvsp", ""),
            "sift": transcript.get("sift_prediction", ""),
            "polyphen": transcript.get("polyphen_prediction", ""),
            "gnomad_exomes_af": gnomad_exomes if gnomad_exomes is not None else "",
            "gnomad_genomes_af": gnomad_genomes if gnomad_genomes is not None else "",
            "clinvar_present": clinvar_present,
            "clinvar_significance": significance,
            "clinvar_review_status": review_status,
            "clinvar_accession_and_traits": clinvar_details,
        }
        rows.append(row)
        gnomad_export.append(
            {
                "variant": variant.coordinate,
                "rsid": variant.rsid,
                "alt": variant.alt,
                "gnomad_exomes_af": gnomad_exomes,
                "gnomad_genomes_af": gnomad_genomes,
                "all_vep_frequencies": frequencies,
            }
        )

    (RAW_DIR / "gnomad_from_vep.json").write_text(
        json.dumps(gnomad_export, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for delimiter, name in [("\t", "variants_annotated.tsv"), (",", "variants_annotated.csv")]:
        with (TABLE_DIR / name).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()

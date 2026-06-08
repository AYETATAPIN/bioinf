#!/usr/bin/env python3
"""Download the NCBI assembly linked to the BioSample of an SRA run."""

from __future__ import annotations

import argparse
import gzip
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def fetch_bytes(url: str, attempts: int = 5) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "bioinf-assignment3/1.0"},
            )
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(2 * attempt)
    raise RuntimeError(f"NCBI request failed after {attempts} attempts: {last_error}")


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8", "replace")


def first_match(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"Could not find {label}")
    return match.group(1)


def sra_uid(run: str) -> str:
    query = urllib.parse.urlencode({"db": "sra", "term": run})
    xml = fetch_text(f"{BASE}/esearch.fcgi?{query}")
    return first_match(r"<Id>(\d+)</Id>", xml, f"SRA UID for {run}")


def biosample_from_sra(uid: str) -> tuple[str, str]:
    query = urllib.parse.urlencode({"db": "sra", "id": uid, "retmode": "xml"})
    xml = fetch_text(f"{BASE}/efetch.fcgi?{query}")
    biosample = first_match(r'<EXTERNAL_ID namespace="BioSample">([^<]+)</EXTERNAL_ID>', xml, "BioSample accession")
    strain_match = re.search(r"<SAMPLE_ATTRIBUTE>\s*<TAG>strain</TAG>\s*<VALUE>([^<]+)</VALUE>", xml)
    strain = strain_match.group(1) if strain_match else "unknown"
    return biosample, strain


def assembly_uid_for_biosample(biosample: str) -> str:
    query = urllib.parse.urlencode({"db": "assembly", "term": biosample})
    xml = fetch_text(f"{BASE}/esearch.fcgi?{query}")
    return first_match(r"<Id>(\d+)</Id>", xml, f"assembly UID for {biosample}")


def assembly_ftp(uid: str) -> tuple[str, str, str]:
    query = urllib.parse.urlencode({"db": "assembly", "id": uid, "retmode": "xml"})
    xml = fetch_text(f"{BASE}/esummary.fcgi?{query}")
    accession = first_match(r"<AssemblyAccession>([^<]+)</AssemblyAccession>", xml, "assembly accession")
    name = first_match(r"<AssemblyName>([^<]+)</AssemblyName>", xml, "assembly name")
    refseq = re.search(r"<FtpPath_RefSeq>([^<]+)</FtpPath_RefSeq>", xml)
    genbank = re.search(r"<FtpPath_GenBank>([^<]+)</FtpPath_GenBank>", xml)
    ftp = (refseq.group(1) if refseq and refseq.group(1) else genbank.group(1)) if genbank or refseq else ""
    if not ftp:
        raise RuntimeError(f"No FTP path found for assembly UID {uid}")
    return accession, name, ftp


def download_reference(ftp_path: str, output_fasta: Path) -> str:
    https_path = ftp_path.replace("ftp://", "https://", 1)
    base_name = https_path.rstrip("/").split("/")[-1]
    url = f"{https_path}/{base_name}_genomic.fna.gz"
    output_gz = Path(f"{output_fasta}.gz")
    output_fasta.parent.mkdir(parents=True, exist_ok=True)
    output_gz.write_bytes(fetch_bytes(url))
    with gzip.open(output_gz, "rb") as source, output_fasta.open("wb") as target:
        shutil.copyfileobj(source, target)
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sra_run", help="SRA run accession, for example SRR22784690")
    parser.add_argument("--out", default=None, help="Output FASTA path")
    args = parser.parse_args()

    uid = sra_uid(args.sra_run)
    biosample, strain = biosample_from_sra(uid)
    asm_uid = assembly_uid_for_biosample(biosample)
    accession, name, ftp = assembly_ftp(asm_uid)
    output = Path(args.out or f"data/{accession}_{name}_genomic.fna")
    url = download_reference(ftp, output)
    contigs = sum(1 for line in output.read_text(encoding="utf-8").splitlines() if line.startswith(">"))

    print(f"sra_uid={uid}")
    print(f"biosample={biosample}")
    print(f"strain={strain}")
    print(f"assembly={accession}_{name}")
    print(f"downloaded_contigs={contigs}")
    print(f"url={url}")
    print(f"output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

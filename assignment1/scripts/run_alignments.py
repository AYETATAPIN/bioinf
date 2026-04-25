#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path


DIAG = 1
UP = 2
LEFT = 3
STOP = 0


@dataclass
class AlignmentResult:
    method: str
    score: int
    seq1_start: int
    seq1_end: int
    seq2_start: int
    seq2_end: int
    aligned_seq1: str
    aligned_seq2: str
    runtime_seconds: float


@dataclass
class AlignmentMetrics:
    matches: int
    mismatches: int
    gap_columns: int
    aligned_length: int
    identity_percent: float


def read_fasta(path: Path) -> tuple[str, str]:
    header = ""
    seq_parts: list[str] = []
    with path.open("r", encoding="ascii") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if not header:
                    header = line[1:]
                continue
            seq_parts.append(line.upper())
    sequence = "".join(c for c in "".join(seq_parts) if c in {"A", "C", "G", "T", "N"})
    if not header:
        header = path.stem
    return header, sequence


def needleman_wunsch(
    seq1: str, seq2: str, match: int = 2, mismatch: int = -1, gap: int = -2
) -> AlignmentResult:
    start_ts = time.perf_counter()
    n = len(seq1)
    m = len(seq2)
    width = m + 1

    dirs = bytearray((n + 1) * width)
    prev = [0] * (m + 1)
    curr = [0] * (m + 1)

    for j in range(1, m + 1):
        prev[j] = prev[j - 1] + gap
        dirs[j] = LEFT

    for i in range(1, n + 1):
        curr[0] = prev[0] + gap
        dirs[i * width] = UP
        ch1 = seq1[i - 1]
        for j in range(1, m + 1):
            diag = prev[j - 1] + (match if ch1 == seq2[j - 1] else mismatch)
            up = prev[j] + gap
            left = curr[j - 1] + gap
            best = diag
            direction = DIAG
            if up > best:
                best = up
                direction = UP
            if left > best:
                best = left
                direction = LEFT
            curr[j] = best
            dirs[i * width + j] = direction
        prev, curr = curr, prev

    score = prev[m]

    i = n
    j = m
    aligned1: list[str] = []
    aligned2: list[str] = []
    while i > 0 or j > 0:
        direction = dirs[i * width + j]
        if direction == DIAG and i > 0 and j > 0:
            aligned1.append(seq1[i - 1])
            aligned2.append(seq2[j - 1])
            i -= 1
            j -= 1
        elif direction == UP and i > 0:
            aligned1.append(seq1[i - 1])
            aligned2.append("-")
            i -= 1
        elif direction == LEFT and j > 0:
            aligned1.append("-")
            aligned2.append(seq2[j - 1])
            j -= 1
        elif i > 0:
            aligned1.append(seq1[i - 1])
            aligned2.append("-")
            i -= 1
        else:
            aligned1.append("-")
            aligned2.append(seq2[j - 1])
            j -= 1

    aligned1.reverse()
    aligned2.reverse()
    runtime = time.perf_counter() - start_ts

    return AlignmentResult(
        method="Needleman-Wunsch (global)",
        score=score,
        seq1_start=1,
        seq1_end=n,
        seq2_start=1,
        seq2_end=m,
        aligned_seq1="".join(aligned1),
        aligned_seq2="".join(aligned2),
        runtime_seconds=runtime,
    )


def smith_waterman(
    seq1: str, seq2: str, match: int = 2, mismatch: int = -1, gap: int = -2
) -> AlignmentResult:
    start_ts = time.perf_counter()
    n = len(seq1)
    m = len(seq2)
    width = m + 1

    dirs = bytearray((n + 1) * width)
    prev = [0] * (m + 1)
    curr = [0] * (m + 1)

    max_score = 0
    max_i = 0
    max_j = 0

    for i in range(1, n + 1):
        curr[0] = 0
        ch1 = seq1[i - 1]
        for j in range(1, m + 1):
            diag = prev[j - 1] + (match if ch1 == seq2[j - 1] else mismatch)
            up = prev[j] + gap
            left = curr[j - 1] + gap

            best = 0
            direction = STOP
            if diag > best:
                best = diag
                direction = DIAG
            if up > best:
                best = up
                direction = UP
            if left > best:
                best = left
                direction = LEFT

            curr[j] = best
            dirs[i * width + j] = direction
            if best > max_score:
                max_score = best
                max_i = i
                max_j = j
        prev, curr = curr, prev

    i = max_i
    j = max_j
    aligned1: list[str] = []
    aligned2: list[str] = []
    while i > 0 and j > 0:
        direction = dirs[i * width + j]
        if direction == STOP:
            break
        if direction == DIAG:
            aligned1.append(seq1[i - 1])
            aligned2.append(seq2[j - 1])
            i -= 1
            j -= 1
        elif direction == UP:
            aligned1.append(seq1[i - 1])
            aligned2.append("-")
            i -= 1
        else:
            aligned1.append("-")
            aligned2.append(seq2[j - 1])
            j -= 1

    aligned1.reverse()
    aligned2.reverse()
    runtime = time.perf_counter() - start_ts

    return AlignmentResult(
        method="Smith-Waterman (local)",
        score=max_score,
        seq1_start=i + 1,
        seq1_end=max_i,
        seq2_start=j + 1,
        seq2_end=max_j,
        aligned_seq1="".join(aligned1),
        aligned_seq2="".join(aligned2),
        runtime_seconds=runtime,
    )


def calculate_metrics(aln: AlignmentResult) -> AlignmentMetrics:
    matches = 0
    mismatches = 0
    gap_columns = 0

    for a, b in zip(aln.aligned_seq1, aln.aligned_seq2):
        if a == "-" or b == "-":
            gap_columns += 1
        elif a == b:
            matches += 1
        else:
            mismatches += 1

    aligned_length = len(aln.aligned_seq1)
    non_gap = matches + mismatches
    identity = (matches / non_gap * 100.0) if non_gap else 0.0

    return AlignmentMetrics(
        matches=matches,
        mismatches=mismatches,
        gap_columns=gap_columns,
        aligned_length=aligned_length,
        identity_percent=identity,
    )


def build_markers(seq1: str, seq2: str) -> str:
    chars: list[str] = []
    for a, b in zip(seq1, seq2):
        if a == "-" or b == "-":
            chars.append(" ")
        elif a == b:
            chars.append("|")
        else:
            chars.append(".")
    return "".join(chars)


def format_alignment(aln: AlignmentResult, label1: str, label2: str, width: int = 70) -> str:
    lines: list[str] = []
    marker = build_markers(aln.aligned_seq1, aln.aligned_seq2)

    pos1 = aln.seq1_start
    pos2 = aln.seq2_start
    for i in range(0, len(aln.aligned_seq1), width):
        block1 = aln.aligned_seq1[i : i + width]
        block2 = aln.aligned_seq2[i : i + width]
        blockm = marker[i : i + width]

        consumed1 = sum(1 for c in block1 if c != "-")
        consumed2 = sum(1 for c in block2 if c != "-")
        end1 = pos1 + consumed1 - 1 if consumed1 else pos1 - 1
        end2 = pos2 + consumed2 - 1 if consumed2 else pos2 - 1

        lines.append(f"{label1:10} {pos1:>6} {block1} {end1:>6}")
        lines.append(f"{'':10} {'':>6} {blockm}")
        lines.append(f"{label2:10} {pos2:>6} {block2} {end2:>6}")
        lines.append("")

        pos1 = end1 + 1
        pos2 = end2 + 1

    return "\n".join(lines).rstrip() + "\n"


def write_alignment_report(
    out_path: Path,
    gene_name: str,
    seq1_header: str,
    seq2_header: str,
    aln: AlignmentResult,
    metrics: AlignmentMetrics,
) -> None:
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write(f"Gene: {gene_name}\n")
        fh.write(f"Method: {aln.method}\n")
        fh.write(f"Score: {aln.score}\n")
        fh.write(f"Identity (%): {metrics.identity_percent:.2f}\n")
        fh.write(f"Aligned length: {metrics.aligned_length}\n")
        fh.write(f"Matches: {metrics.matches}\n")
        fh.write(f"Mismatches: {metrics.mismatches}\n")
        fh.write(f"Gap columns: {metrics.gap_columns}\n")
        fh.write(f"Seq1 interval: {aln.seq1_start}-{aln.seq1_end}\n")
        fh.write(f"Seq2 interval: {aln.seq2_start}-{aln.seq2_end}\n")
        fh.write(f"Runtime (s): {aln.runtime_seconds:.4f}\n")
        fh.write(f"Seq1 header: {seq1_header}\n")
        fh.write(f"Seq2 header: {seq2_header}\n")
        fh.write("\n")
        fh.write(format_alignment(aln, "human", "mouse"))


def build_summary_row(gene: str, aln: AlignmentResult, metrics: AlignmentMetrics) -> dict[str, object]:
    return {
        "gene": gene,
        "method": aln.method,
        "score": aln.score,
        "identity_percent": round(metrics.identity_percent, 2),
        "aligned_length": metrics.aligned_length,
        "matches": metrics.matches,
        "mismatches": metrics.mismatches,
        "gap_columns": metrics.gap_columns,
        "seq1_interval": f"{aln.seq1_start}-{aln.seq1_end}",
        "seq2_interval": f"{aln.seq2_start}-{aln.seq2_end}",
        "runtime_seconds": round(aln.runtime_seconds, 4),
    }


def save_summary_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    cols = [
        "gene",
        "method",
        "score",
        "identity_percent",
        "aligned_length",
        "matches",
        "mismatches",
        "gap_columns",
        "seq1_interval",
        "seq2_interval",
        "runtime_seconds",
    ]
    with path.open("w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[c]) for c in cols) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pairwise alignments for eye color phenotype genes.")
    parser.add_argument("--fasta-dir", default="data/fasta", help="Input directory with FASTA files")
    parser.add_argument("--out-dir", default="results", help="Output directory")
    args = parser.parse_args()

    fasta_dir = Path(args.fasta_dir)
    out_dir = Path(args.out_dir)
    align_dir = out_dir / "alignments"
    out_dir.mkdir(parents=True, exist_ok=True)
    align_dir.mkdir(parents=True, exist_ok=True)

    pairs = [
        (
            "OCA2",
            fasta_dir / "OCA2_Homo_sapiens_NM_000275.3.fasta",
            fasta_dir / "Oca2_Mus_musculus_NM_021879.3.fasta",
        ),
        (
            "TYR",
            fasta_dir / "TYR_Homo_sapiens_NM_000372.5.fasta",
            fasta_dir / "Tyr_Mus_musculus_NM_011661.3.fasta",
        ),
    ]

    summary_rows: list[dict[str, object]] = []
    json_rows: list[dict[str, object]] = []

    for gene_name, human_path, mouse_path in pairs:
        h_header, h_seq = read_fasta(human_path)
        m_header, m_seq = read_fasta(mouse_path)

        global_aln = needleman_wunsch(h_seq, m_seq)
        local_aln = smith_waterman(h_seq, m_seq)

        for method_slug, aln in [("needle", global_aln), ("water", local_aln)]:
            metrics = calculate_metrics(aln)
            out_path = align_dir / f"{gene_name}_human_vs_mouse_{method_slug}.txt"
            write_alignment_report(out_path, gene_name, h_header, m_header, aln, metrics)
            summary_rows.append(build_summary_row(gene_name, aln, metrics))

            json_rows.append(
                {
                    "gene": gene_name,
                    "human_header": h_header,
                    "mouse_header": m_header,
                    "alignment": asdict(aln),
                    "metrics": asdict(metrics),
                    "report_file": str(out_path.as_posix()),
                }
            )

    save_summary_tsv(out_dir / "alignment_summary.tsv", summary_rows)
    with (out_dir / "alignment_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(json_rows, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

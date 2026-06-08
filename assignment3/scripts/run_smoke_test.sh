#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SMOKE_DIR="${ROOT_DIR}/results/smoke_test"
mkdir -p "${SMOKE_DIR}/fastqc"

for tool in fastqc minimap2 samtools python3; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    echo "Missing required tool for smoke test: ${tool}"
    exit 1
  fi
done

REF="${SMOKE_DIR}/smoke_ref.fa"
FASTQ="${SMOKE_DIR}/smoke_reads.fastq"
MMI="${REF}.mmi"
SAM="${SMOKE_DIR}/smoke.sam"
BAM="${SMOKE_DIR}/smoke.bam"
FLAGSTAT="${SMOKE_DIR}/flagstat.txt"
QC_RESULT="${SMOKE_DIR}/mapping_qc_result.txt"
LOG="${SMOKE_DIR}/pipeline_log.txt"

python3 - "${REF}" "${FASTQ}" <<'PY'
from pathlib import Path
import random
import sys

ref_path = Path(sys.argv[1])
fastq_path = Path(sys.argv[2])

random.seed(3)
ref = ''.join(random.choice('ACGT') for _ in range(1200))
starts = [120, 430, 760]
reads = [ref[start:start + 180] for start in starts]

ref_path.write_text('>smoke_ecoli_like_reference\n' + ref + '\n', encoding='ascii')
with fastq_path.open('w', encoding='ascii') as fh:
    for i, read in enumerate(reads, 1):
        fh.write(f'@read_{i}\n{read}\n+\n{"I" * len(read)}\n')
PY

: > "${LOG}"
echo "[smoke] FastQC" | tee -a "${LOG}"
fastqc -o "${SMOKE_DIR}/fastqc" "${FASTQ}" >> "${LOG}" 2>&1

echo "[smoke] minimap2 index" | tee -a "${LOG}"
minimap2 -d "${MMI}" "${REF}" >> "${LOG}" 2>&1

echo "[smoke] minimap2 map" | tee -a "${LOG}"
minimap2 -ax map-ont "${MMI}" "${FASTQ}" > "${SAM}" 2>> "${LOG}"

echo "[smoke] samtools view" | tee -a "${LOG}"
samtools view -bS "${SAM}" -o "${BAM}" >> "${LOG}" 2>&1

echo "[smoke] samtools flagstat" | tee -a "${LOG}"
samtools flagstat "${BAM}" > "${FLAGSTAT}"

python3 "${ROOT_DIR}/scripts/parse_flagstat.py" "${FLAGSTAT}" --threshold 90 --out "${QC_RESULT}"
cat "${QC_RESULT}" | tee -a "${LOG}"

echo "[smoke] done: ${QC_RESULT}" | tee -a "${LOG}"

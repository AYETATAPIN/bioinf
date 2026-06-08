#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT_DIR}/data"
RESULTS_DIR="${ROOT_DIR}/results"
LOG_DIR="${ROOT_DIR}/logs"

SRA_RUN="${SRA_RUN:-SRR22784690}"
THREADS="${THREADS:-4}"
MAPPED_THRESHOLD="${MAPPED_THRESHOLD:-90}"
RUN_FREEBAYES="${RUN_FREEBAYES:-0}"
RUN_FASTQC="${RUN_FASTQC:-1}"
FASTQC_THREADS="${FASTQC_THREADS:-8}"
FASTQ_URL="${FASTQ_URL:-}"

DEFAULT_REF_URL="https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/027/278/225/GCF_027278225.1_ASM2727822v1/GCF_027278225.1_ASM2727822v1_genomic.fna.gz"
DEFAULT_REF_FASTA="${DATA_DIR}/GCF_027278225.1_ASM2727822v1_genomic.fna"
REF_URL="${REF_URL:-${DEFAULT_REF_URL}}"
REF_FASTA="${REF_FASTA:-${DEFAULT_REF_FASTA}}"
REF_GZ="${REF_GZ:-${REF_FASTA}.gz}"
REF_INDEX="${REF_INDEX:-${REF_FASTA}.mmi}"
FASTQ="${DATA_DIR}/${SRA_RUN}.fastq"
FASTQ_GZ="${FASTQ}.gz"
FASTQ_ALT="${DATA_DIR}/${SRA_RUN}_1.fastq"
FASTQ_ALT_GZ="${FASTQ_ALT}.gz"
SAM="${RESULTS_DIR}/${SRA_RUN}.sam"
BAM="${RESULTS_DIR}/${SRA_RUN}.bam"
SORTED_BAM="${RESULTS_DIR}/${SRA_RUN}.sorted.bam"
FLAGSTAT="${RESULTS_DIR}/flagstat.txt"
QC_RESULT="${RESULTS_DIR}/mapping_qc_result.txt"
PIPELINE_LOG="${RESULTS_DIR}/pipeline_log.txt"
FASTQC_DIR="${RESULTS_DIR}/fastqc"
VCF="${RESULTS_DIR}/${SRA_RUN}.vcf"

mkdir -p "${DATA_DIR}" "${RESULTS_DIR}" "${LOG_DIR}" "${FASTQC_DIR}"
: > "${PIPELINE_LOG}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "${PIPELINE_LOG}"
}

require_tool() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Missing required tool: $1"
    log "Install tools with: bash scripts/install_tools_wsl.sh"
    exit 1
  fi
}

if [[ "${RUN_FASTQC}" == "1" ]]; then
  require_tool fastqc
fi
require_tool minimap2
require_tool samtools
require_tool python3

if [[ "${RUN_FREEBAYES}" == "1" ]]; then
  require_tool freebayes
fi

log "Assignment 3 mapping QC pipeline started"
log "SRA run: ${SRA_RUN}"
log "Reference FASTA: ${REF_FASTA}"

if [[ -s "${FASTQ_ALT}" && ! -s "${FASTQ}" ]]; then
  log "Using FASTQ file: ${FASTQ_ALT}"
  FASTQ="${FASTQ_ALT}"
  FASTQ_GZ="${FASTQ_ALT_GZ}"
elif [[ -s "${FASTQ_ALT_GZ}" && ! -s "${FASTQ}" && ! -s "${FASTQ_GZ}" ]]; then
  log "Using compressed FASTQ file: ${FASTQ_ALT_GZ}"
  FASTQ="${FASTQ_ALT}"
  FASTQ_GZ="${FASTQ_ALT_GZ}"
fi

if [[ ! -s "${FASTQ}" && ! -s "${FASTQ_GZ}" && -n "${FASTQ_URL}" ]]; then
  require_tool wget
  log "Downloading FASTQ from FASTQ_URL"
  wget -O "${FASTQ_GZ}" "${FASTQ_URL}" 2>&1 | tee "${LOG_DIR}/download_fastq_url.log"
fi

if [[ ! -s "${FASTQ}" && ! -s "${FASTQ_GZ}" ]]; then
  require_tool fasterq-dump
  log "Downloading FASTQ from SRA"
  fasterq-dump "${SRA_RUN}" --outdir "${DATA_DIR}" --threads "${THREADS}" 2>&1 | tee "${LOG_DIR}/fasterq_dump.log"
  if [[ -s "${FASTQ_ALT}" && ! -s "${FASTQ}" ]]; then
    FASTQ="${FASTQ_ALT}"
    FASTQ_GZ="${FASTQ_ALT_GZ}"
  fi
fi

if [[ -s "${FASTQ_GZ}" && ! -s "${FASTQ}" ]]; then
  require_tool gzip
  log "Decompressing FASTQ: ${FASTQ_GZ}"
  gzip -dk "${FASTQ_GZ}"
fi

if [[ ! -s "${FASTQ}" ]]; then
  log "FASTQ file was not found after download/decompression: ${FASTQ}"
  exit 1
fi

if [[ ! -s "${REF_FASTA}" ]]; then
  require_tool wget
  require_tool gzip
  log "Downloading E. coli reference genome"
  wget -O "${REF_GZ}" "${REF_URL}" 2>&1 | tee "${LOG_DIR}/download_reference.log"
  gzip -dk "${REF_GZ}"
fi

if [[ ! -s "${REF_INDEX}" ]]; then
  log "Indexing reference with minimap2"
  minimap2 -d "${REF_INDEX}" "${REF_FASTA}" 2>&1 | tee "${LOG_DIR}/minimap2_index.log"
fi

if [[ "${RUN_FASTQC}" == "1" ]]; then
  log "Running FastQC with FASTQC_THREADS=${FASTQC_THREADS} (~$((FASTQC_THREADS * 250)) MB Java heap)"
  if fastqc --threads "${FASTQC_THREADS}" -o "${FASTQC_DIR}" "${FASTQ}" 2>&1 | tee "${LOG_DIR}/fastqc.log"; then
    log "FastQC finished"
  else
    log "FastQC failed; continuing because mapping QC is evaluated by minimap2 + samtools flagstat"
  fi
else
  log "Skipping FastQC because RUN_FASTQC=${RUN_FASTQC}"
fi

log "Mapping reads with minimap2"
minimap2 -ax map-ont -t "${THREADS}" "${REF_INDEX}" "${FASTQ}" > "${SAM}" 2> "${LOG_DIR}/minimap2_map.log"

log "Converting SAM to BAM"
samtools view -@ "${THREADS}" -bS "${SAM}" -o "${BAM}" 2>&1 | tee "${LOG_DIR}/samtools_view.log"

log "Running samtools flagstat"
samtools flagstat "${BAM}" > "${FLAGSTAT}"

log "Parsing mapped-read percentage"
python3 "${ROOT_DIR}/scripts/parse_flagstat.py" "${FLAGSTAT}" --threshold "${MAPPED_THRESHOLD}" --out "${QC_RESULT}"
cat "${QC_RESULT}" | tee -a "${PIPELINE_LOG}"

STATUS="$(awk -F= '/^status=/{print $2}' "${QC_RESULT}")"
if [[ "${STATUS}" == "OK" ]]; then
  log "Mapping quality decision: OK"
else
  log "Mapping quality decision: not OK"
fi

log "Sorting BAM"
samtools sort -@ "${THREADS}" "${BAM}" -o "${SORTED_BAM}" 2>&1 | tee "${LOG_DIR}/samtools_sort.log"
samtools index "${SORTED_BAM}" 2>&1 | tee "${LOG_DIR}/samtools_index.log"

if [[ "${RUN_FREEBAYES}" == "1" ]]; then
  log "Calling variants with freebayes"
  freebayes -f "${REF_FASTA}" "${SORTED_BAM}" > "${VCF}" 2> "${LOG_DIR}/freebayes.log"
fi

log "Finished"

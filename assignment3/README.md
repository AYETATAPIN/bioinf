# Assignment 3: Variant-calling pipeline

Student: Демидов Дмитрий Викторович

Chosen setup:

- Sequencing platform: Oxford Nanopore MinION/GridION/PromethION (ONT)
- Mapping tool: `minimap2`
- Pipeline framework: Mage
- Test organism: `Escherichia coli`
- SRA run: `SRR22784690`
- Reference assembly: `GCF_027278225.1_ASM2727822v1` for BioSample `SAMN32247506`

## What this assignment does

This assignment builds a small pipeline for mapping ONT reads to a reference genome and evaluating mapping quality using `samtools flagstat`.

The repository contains:

- bash workflow: `scripts/run_mapping_qc.sh`
- matched-reference downloader: `scripts/download_linked_wgs_reference.py`
- flagstat parser: `scripts/parse_flagstat.py`
- WSL installer: `scripts/install_tools_wsl.sh`
- Mage project: `mage_project/`
- report and result templates: `results/`
- selected SRA/reference metadata: `metadata/`

Large FASTQ/SAM/BAM/VCF files are intentionally not committed.

## Manual steps in WSL

Open Ubuntu/WSL and run:

```bash
cd /mnt/d/prg/bioinf/assignment3
bash scripts/install_tools_wsl.sh
```

If Mage installation through `pip` is slow or hangs, install the command-line bioinformatics tools first:

```bash
INSTALL_MAGE=0 bash scripts/install_tools_wsl.sh
```

Then install Mage separately when network access to PyPI is stable:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install mage-ai
```

Then run the command-line mapping QC pipeline:

```bash
cd /mnt/d/prg/bioinf/assignment3
RUN_FASTQC=0 bash scripts/run_mapping_qc.sh
```

If the downloaded file is named `SRR22784690_1.fastq.gz`, leave it in `data/`; the script detects this ENA/SRA naming pattern automatically.

The default reference is `GCF_027278225.1_ASM2727822v1`, the NCBI assembly linked to the same BioSample as `SRR22784690`. If the reference FASTA is missing, the script downloads it automatically. You can also refresh it manually:

```bash
python3 scripts/download_linked_wgs_reference.py SRR22784690
```

For the real ONT FASTQ file, FastQC can be memory-hungry. The checked command above skips only this optional FastQC step and keeps the required mapping QC. If you want to try FastQC too, run:

```bash
FASTQC_THREADS=8 bash scripts/run_mapping_qc.sh
```

Expected output files:

- `results/flagstat.txt`
- `results/mapping_qc_result.txt`
- `results/pipeline_log.txt`
- `results/SRR22784690.sorted.bam`
- `results/SRR22784690.sorted.bam.bai`

If you also want FreeBayes variant calling:

```bash
RUN_FREEBAYES=1 bash scripts/run_mapping_qc.sh
```

## Mage steps

Start Mage:

```bash
cd /mnt/d/prg/bioinf/assignment3
bash scripts/start_mage.sh
```

Open:

```text
http://localhost:6789
```

Check two pipelines:

- `hello_world`
- `mapping_qc`

For visualization:

1. Open pipeline `mapping_qc`.
2. Open graph/DAG view.
3. Save a screenshot as `assignment3/results/mage_pipeline_dag.png`.

An automatic static diagram is already included as `results/pipeline_dag.svg`, but the screenshot from Mage UI is better for the assignment.

## Quick parser test

The file `results/flagstat.txt` currently contains the example from the assignment PDF.

Run:

```bash
python3 scripts/parse_flagstat.py results/flagstat.txt
```

Expected:

```text
mapped_percent=99.83
threshold=90.00
status=OK
```

## Local smoke test

If SRA download is unavailable because of network/DNS issues, test the executable part of the workflow on a tiny synthetic dataset:

```bash
cd /mnt/d/prg/bioinf/assignment3
bash scripts/run_smoke_test.sh
```

Smoke-test outputs are written to `results/smoke_test/`. This does not replace the real SRA run, but it verifies FastQC, minimap2, samtools, and the flagstat parser.

On this machine the command-line tools were installed and the smoke test completed with `mapped_percent=100.00` and `status=OK`. The real FASTQ was then provided locally as `data/SRR22784690_1.fastq.gz`; the final real run completed with `mapped_percent=99.57` and `status=OK` when mapped to the BioSample-matched assembly `GCF_027278225.1_ASM2727822v1`.

## Assignment checklist

- SRA link: `metadata/sra_source.md`
- Bash algorithm: `scripts/run_mapping_qc.sh`
- `samtools flagstat` result: `results/flagstat.txt`
- Flagstat parser: `scripts/parse_flagstat.py`
- Framework install instruction: `scripts/install_tools_wsl.sh`
- Hello world pipeline: `mage_project/pipelines/hello_world/`
- Mapping QC pipeline: `mage_project/pipelines/mapping_qc/`
- Pipeline result files: `results/`
- Pipeline visualization description: `results/visualization_description.md`
- Static DAG figure: `results/pipeline_dag.svg`

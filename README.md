# Bioinformatics Homework Repository

This repository contains three assignments:

- `assignment1/` - phenotype of eye color, ortholog pairwise alignments
- `assignment2/` - taxonomic representation of TYR homologs, BLAST + MSA analysis
- `assignment3/` - ONT read mapping QC and variant-calling pipeline with minimap2, samtools, and Mage

## Assignment 1 quick run

```bash
python assignment1/scripts/run_alignments.py --fasta-dir assignment1/data/fasta --out-dir assignment1/results
```

## Assignment 2 quick run

1. Export BLAST hit table CSV to `assignment2/input/blast_hits.csv` (see `assignment2/README.md`).
2. Run:

```bash
python assignment2/scripts/run_assignment2.py --repo-root .
```

## Assignment 3 quick run

Run from Ubuntu/WSL:

```bash
cd /mnt/d/prg/bioinf/assignment3
bash scripts/install_tools_wsl.sh
RUN_FASTQC=0 bash scripts/run_mapping_qc.sh
```

Mage:

```bash
cd /mnt/d/prg/bioinf/assignment3
bash scripts/start_mage.sh
```

# Bioinformatics Homework Repository

This repository contains two assignments:

- `assignment1/` - phenotype of eye color, ortholog pairwise alignments
- `assignment2/` - taxonomic representation of TYR homologs, BLAST + MSA analysis

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

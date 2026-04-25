# Assignment 2: Gene Representation Across Taxa (`TYR`)

## Manual step (required once)

1. Open NCBI BLASTN:
   `https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&PAGE_TYPE=BlastSearch`
2. Use query sequence from:
   `assignment1/data/fasta/TYR_Homo_sapiens_NM_000372.5.fasta`
3. Set parameters:
   - Database: `nt`
   - Program selection: `More dissimilar sequences (discontiguous megablast)`
   - Exclude: `Homo sapiens` (or `NOT txid9606[ORGN]`)
   - Max target sequences: `250`
4. Download `Hit table (CSV)` and save as:
   `assignment2/input/blast_hits.csv`

## Automated pipeline

Run from repository root:

```bash
python assignment2/scripts/run_assignment2.py --repo-root .
```

Generated outputs:

- `assignment2/data/query_human_TYR.fasta`
- `assignment2/data/homologs.fasta`
- `assignment2/results/homologs_table.csv`
- `assignment2/results/multiple_alignment.aln`
- `assignment2/results/conservation_analysis.md`
- `assignment2/results/taxon_summary.md`
- `assignment2/results/report.md`

# Источник данных SRA

Для ДЗ3 выбран небольшой набор long-read данных для **Escherichia coli**, полученный на Oxford Nanopore MinION.

- SRA run: `SRR22784690`
- Ссылка: https://www.ncbi.nlm.nih.gov/sra/SRR22784690
- Организм: `Escherichia coli`
- Платформа: `Oxford Nanopore MinION`
- Стратегия: `WGS`
- Layout: `single`
- Размер загрузки: около 189 MB
- Причина выбора: подходит под выбранный прибор ONT и значительно компактнее, чем Homo sapiens WES/WGS.

Референсный геном:

- BioSample: `SAMN32247506`
- Штамм: `EC_8630_1L1_D`
- Assembly: `GCF_027278225.1_ASM2727822v1`
- Ссылка: https://www.ncbi.nlm.nih.gov/assembly/GCF_027278225.1/
- FASTA для скрипта: https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/027/278/225/GCF_027278225.1_ASM2727822v1/GCF_027278225.1_ASM2727822v1_genomic.fna.gz
- Причина выбора: это assembly, связанный с тем же BioSample, что и `SRR22784690`; при маппинге на общий лабораторный референс K-12 часть accessory genome/plasmid reads не картируется.

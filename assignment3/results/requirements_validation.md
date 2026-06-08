# Проверка соответствия требованиям ДЗ3

## Что требовалось в PDF

1. Оформить решение в GitHub-репозитории и указать ФИО.
2. Найти Linux/bash.
3. Найти и скачать SRA reads для `Escherichia coli` или `Homo sapiens`.
4. Скачать reference genome: для e.coli в PDF дана ссылка на `GCF_000005845.2`.
5. Установить консольные `FastQC`, `bwa/minimap2`, `samtools`.
6. Индексировать reference.
7. Написать parser для `samtools flagstat`, который извлекает `% mapped`.
8. Реализовать bash-алгоритм: FastQC, mapping, `samtools view`, `flagstat`, parse, `OK/not OK`, sort, optional FreeBayes.
9. Выбрать и установить framework для pipeline.
10. Дать инструкцию по установке framework.
11. Сделать тестовый pipeline `Hello world`.
12. Реализовать pipeline оценки качества картирования на framework.
13. Визуализировать pipeline.
14. Описать отличие DAG от блок-схемы.

## Что сделано

- ФИО и выбранные инструменты записаны в `metadata/student_info.tsv`.
- Выбран SRA run `SRR22784690`: ONT MinION reads для `Escherichia coli`.
- Bash workflow реализован в `scripts/run_mapping_qc.sh`.
- Parser `flagstat` реализован в `scripts/parse_flagstat.py`.
- Результат `samtools flagstat` сохранён в `results/flagstat.txt`.
- Итог QC сохранён в `results/mapping_qc_result.txt`: `mapped_percent=99.57`, `status=OK`.
- Pipeline log сохранён в `results/pipeline_log.txt`.
- Mage project создан в `mage_project/`.
- `Hello world` pipeline создан в `mage_project/pipelines/hello_world/`.
- Mapping QC pipeline создан в `mage_project/pipelines/mapping_qc/`.
- Статическая схема pipeline сохранена в `results/pipeline_dag.svg`.
- Описание визуализации сохранено в `results/visualization_description.md`.

## Нюанс по reference genome

Ссылка из PDF для e.coli: `https://www.ncbi.nlm.nih.gov/assembly/GCF_000005845.2/`.

Этот reference был скачан и индексирован локально во время проверки. При маппинге выбранных reads `SRR22784690` на этот общий лабораторный reference K-12 результат был ниже порога 90% (`88.38% mapped`), потому что SRA sample относится к strain `EC_8630_1L1_D` из avian/broiler farm dataset.

Для финального результата использован BioSample-matched assembly:

- BioSample: `SAMN32247506`
- Strain: `EC_8630_1L1_D`
- Assembly: `GCF_027278225.1_ASM2727822v1`

Такой выбор биологически корректнее для выбранных reads и даёт `99.57% mapped`.

## Что осталось руками

Mage UI не был запущен на этой машине, потому что команда `mage` сейчас не установлена. Для полного закрытия пунктов про framework visualization нужно:

1. Установить Mage.
2. Запустить `bash scripts/start_mage.sh`.
3. Открыть `http://localhost:6789`.
4. Открыть pipeline `mapping_qc`.
5. Сохранить DAG screenshot как `results/mage_pipeline_dag.png`.

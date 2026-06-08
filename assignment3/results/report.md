# Домашнее задание 3: построение пайплайна получения генетических вариантов

ФИО студента: Демидов Дмитрий Викторович

## 1. Ссылка на загруженные прочтения из NCBI SRA

- SRA run: `SRR22784690`
- Ссылка: https://www.ncbi.nlm.nih.gov/sra/SRR22784690
- Организм: `Escherichia coli`
- Прибор: Oxford Nanopore MinION

## 2. Bash-скрипт с алгоритмом

Файл: `assignment3/scripts/run_mapping_qc.sh`

Скрипт выполняет скачивание/проверку FASTQ, скачивание matched reference assembly, опциональный FastQC, minimap2, samtools view, samtools flagstat, разбор процента картированных ридов, вывод `OK/not OK`, сортировку BAM и опциональный FreeBayes.

Для `SRR22784690` используется assembly `GCF_027278225.1_ASM2727822v1`, связанный с BioSample `SAMN32247506` и штаммом `EC_8630_1L1_D`. Это корректнее, чем общий лабораторный референс K-12, потому что выбранный образец относится к avian/broiler farm E. coli и содержит штамм-специфичные участки.

## 3. Результат `samtools flagstat`

Файл: `assignment3/results/flagstat.txt`

Реальный пайплайн для `SRR22784690` был запущен. Итог:

- `mapped_percent=99.57`
- `threshold=90.00`
- `status=OK`

## 4. Скрипт разбора `flagstat`

Файл: `assignment3/scripts/parse_flagstat.py`

## 5. FASTQ/SAM/BAM/VCF

Большие файлы не добавляются в git. Они создаются локально в `assignment3/data/` и `assignment3/results/` при запуске пайплайна.

Если SRA временно недоступен из WSL, скрипт можно проверить на локальном synthetic smoke-test: `assignment3/scripts/run_smoke_test.sh`.

На текущей машине smoke-test был успешно запущен: `mapped_percent=100.00`, `status=OK`. Реальный FASTQ был добавлен локально как `data/SRR22784690_1.fastq.gz`; после этого основной пайплайн завершился успешно: `mapped_percent=99.57`, `status=OK`.

Для финального запуска использовался `RUN_FASTQC=0`, потому что FastQC для реального ONT FASTQ падал по Java heap memory. Это не влияет на главный критерий ДЗ: проверку качества картирования через `minimap2` и `samtools flagstat`.

## 6. Инструкция по установке фреймворка

Файлы:

- `assignment3/scripts/install_tools_wsl.sh`
- `assignment3/README.md`

## 7. Тестовый pipeline Hello world

Mage pipeline: `assignment3/mage_project/pipelines/hello_world/`

## 8. Результаты и логи работы pipeline

Файлы:

- `assignment3/results/pipeline_log.txt`
- `assignment3/results/mapping_qc_result.txt`

## 9. Описание визуального создания pipeline

Файл: `assignment3/results/visualization_description.md`

## 10. Код pipeline оценки качества картирования на Mage

Mage pipeline: `assignment3/mage_project/pipelines/mapping_qc/`

## 11. Выведенные результаты pipeline

Файл: `assignment3/results/mapping_qc_result.txt`

## 12. Логи работы pipeline

Файл: `assignment3/results/pipeline_log.txt`

## 13. Визуализация pipeline

Файл для ручного скриншота Mage UI: `assignment3/results/mage_pipeline_dag.png`

Автоматическая схема по структуре pipeline: `assignment3/results/pipeline_dag.svg`

## 14. Отличия визуализации от блок-схемы

Описание: `assignment3/results/visualization_description.md`

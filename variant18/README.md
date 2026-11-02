# Домашнее задание 4. Вариант 18

Репозиторная папка содержит исходный VCF, воспроизводимый скрипт аннотации, полные ответы сервисов, итоговую таблицу на 50 вариантов и краткий отчет.

## Структура

- `data/student_18.vcf` - исходный VCF, GRCh38.
- `scripts/annotate.py` - загрузка VEP, ClinVar и формирование таблиц.
- `results/tables/variants_annotated.csv` - итоговая таблица, 50 строк.
- `results/tables/variants_annotated.tsv` - та же таблица в TSV.
- `results/tables/variants_annotated.xlsx` - оформленная версия для Excel.
- `results/raw/vep_response.json` - полный экспорт Ensembl VEP.
- `results/raw/clinvar_response.json` - полный экспорт ClinVar E-utilities.
- `results/raw/gnomad_from_vep.json` - частоты gnomAD и исходные frequency-поля VEP.
- `results/annotation_settings.json` - дата, сборка, release и параметры аннотации.
- `REPORT.md` - краткий отчет с разбором трех вариантов.
- `docs/sources.md` - первичные источники и ограничения интерпретации.

## Воспроизведение

Требуется Python 3.11 или новее и доступ к интернету. Дополнительные Python-пакеты не нужны.

```powershell
python scripts/annotate.py
```

Скрипт перезаписывает JSON-экспорты и CSV/TSV актуальными данными. Поскольку внешние базы обновляются, повторный запуск может дать отличающиеся значения.

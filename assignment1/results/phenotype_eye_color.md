# Домашнее задание 1: фенотип цвета глаз

## 1) Фенотип и краткое описание (OMIM)

Выбран фенотип: **цвет глаз (вариабельность окраски радужки)**.  
Запись OMIM: **EYE COLOR 1 (EYCL1), MIM: 227240**.

Краткое описание: цвет радужки зависит от количества и распределения меланина.  
При более высокой концентрации пигмента чаще наблюдается карий цвет, при более низкой — голубой/серый.

Ссылка на OMIM:
- https://www.omim.org/entry/227240

## 2) Ассоциированные гены

Использованы два гена, связанные с пигментацией радужки:

- **OCA2** (человек), ортолог **Oca2** (мышь)
- **TYR** (человек), ортолог **Tyr** (мышь)

NCBI Gene:

- OCA2 (Homo sapiens): https://www.ncbi.nlm.nih.gov/gene/4948
- Oca2 (Mus musculus): https://www.ncbi.nlm.nih.gov/gene/18431
- TYR (Homo sapiens): https://www.ncbi.nlm.nih.gov/gene/7299
- Tyr (Mus musculus): https://www.ncbi.nlm.nih.gov/gene/22173

## 3) FASTA-файлы генов

Файлы сохранены в `data/fasta/`:

- `OCA2_Homo_sapiens_NM_000275.3.fasta`
- `Oca2_Mus_musculus_NM_021879.3.fasta`
- `TYR_Homo_sapiens_NM_000372.5.fasta`
- `Tyr_Mus_musculus_NM_011661.3.fasta`

Источник последовательностей: NCBI Nucleotide (RefSeq mRNA).

## 4) Парные выравнивания (2 инструмента)

Использованы два инструмента парного выравнивания:

- **Needleman-Wunsch** (глобальное выравнивание)
- **Smith-Waterman** (локальное выравнивание)

Файлы выравниваний в `results/alignments/`:

- `OCA2_human_vs_mouse_needle.txt`
- `OCA2_human_vs_mouse_water.txt`
- `TYR_human_vs_mouse_needle.txt`
- `TYR_human_vs_mouse_water.txt`

## 5) Оценка качества выравниваний

Сводная таблица: `results/alignment_summary.tsv`.

Ключевые метрики:

- **OCA2**
  - Needleman-Wunsch: score=3915, identity=79.09%, gaps=146
  - Smith-Waterman: score=3956, identity=78.91%, gaps=116
  - Вывод: лучше **Smith-Waterman** (выше score, меньше разрывов, сопоставимая идентичность).

- **TYR**
  - Needleman-Wunsch: score=817, identity=88.58%, gaps=1283
  - Smith-Waterman: score=2708, identity=81.01%, gaps=77
  - Вывод: лучше **Smith-Waterman**, так как глобальное выравнивание сильно штрафуется за длинные неконсервативные участки и UTR.

Общий вывод: для данных ортологов (человек–мышь, mRNA) локальное выравнивание Smith-Waterman даёт более биологически интерпретируемые результаты.

---

Воспроизведение:

```bash
python scripts/run_alignments.py
```

# Домашнее задание 1: фенотип цвета глаз

## 1) Фенотип и краткое описание (OMIM)

Выбран фенотип: **вариабельность цвета радужки (голубой/карий цвет глаз)**.  
На OMIM этот фенотип исторически описывается как:

- **EYE COLOR 1 (EYCL1), MIM: 227240**
- **EYE COLOR 3 (EYCL3), MIM: 227220**

Коротко: цвет глаз определяется количеством и распределением меланина в радужке.  
Более высокий уровень эумеланина обычно связан с карим цветом, более низкий — с голубым/серым.

Ссылка на OMIM:
- https://www.omim.org/entry/227240

Примечание: при автоматическом доступе OMIM может возвращать 403 (anti-crawling), поэтому для проверки MIM ID также использована обзорная статья:
- https://www.sciencedirect.com/science/article/pii/S016895250400151X

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

Использованы два алгоритма:

- **Needleman-Wunsch** (глобальное выравнивание; аналог Needle)
- **Smith-Waterman** (локальное выравнивание; аналог Water)

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
  - Вывод: лучше **Smith-Waterman**, т.к. глобальное выравнивание сильно штрафуется за длинные неконсервативные участки/UTR.

Общий вывод: для данных ортологов (человек–мышь, mRNA) локальное выравнивание Smith-Waterman даёт более биологически интерпретируемые результаты.

---

Воспроизведение:

```bash
python scripts/run_alignments.py
```

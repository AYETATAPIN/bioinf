# Источники и правила интерпретации

Дата доступа: 02.11.2026.

## Ensembl VEP

- Ensembl VEP предсказывает последствия варианта отдельно для перекрывающихся транскриптов, белковых последовательностей и регуляторных элементов. Поэтому один вариант может иметь несколько строк и несколько последствий. Источник: [Ensembl Variant Effect Predictor](https://www.ensembl.org/info/docs/tools/vep/index.html).
- Для итоговой таблицы следует заранее определить правило выбора одной аннотации. В этой работе сначала выбирается наиболее тяжелое последствие по рангу Sequence Ontology, затем представляющий его транскрипт выбирается по приоритету `MANE Select` -> `CANONICAL` -> protein-coding -> первый доступный. Параметр `--mane` отмечает MANE Select/MANE Plus Clinical, `--canonical` отмечает канонический транскрипт, а `--pick` выбирает одну запись с учетом тяжести последствия и свойств транскрипта. Источники: [VEP script documentation](https://www.ensembl.org/info/docs/tools/vep/script/vep_options.html), [VEP FAQ](https://www.ensembl.org/info/docs/tools/vep/vep_faq.html), [VEP consequence types](https://www.ensembl.org/info/genome/variation/prediction/predicted_data.html).
- Поле `Consequence` является прогнозом молекулярного последствия, а не доказательством клинической патогенности. Выбор только одной строки неизбежно скрывает часть транскрипт-специфичной информации, поэтому полный экспорт VEP необходимо сохранять отдельно. Источники: [VEP output formats](https://www.ensembl.org/info/docs/tools/vep/vep_formats.html), [VEP web documentation](https://www.ensembl.org/info/docs/tools/vep/online/index.html).
- Координаты исходного VCF относятся к GRCh38, поэтому все запросы и сопоставления должны выполняться на GRCh38. Смешение GRCh37 и GRCh38 может привести к неверному сопоставлению аллелей и записей.

## ClinVar

- ClinVar агрегирует представленные организациями классификации варианта для заболеваний и может показывать как согласие, так и конфликтующие интерпретации. Наличие записи ClinVar само по себе не означает патогенность. Источник: [What is ClinVar?](https://www.ncbi.nlm.nih.gov/clinvar/intro/).
- Для отчета нужно фиксировать не только aggregate clinical significance (`Benign`, `Likely benign`, `Uncertain significance`, `Likely pathogenic`, `Pathogenic`, `Conflicting classifications` и другие значения), но и условие/фенотип, дату последней оценки и `review status`, если они доступны. Один и тот же вариант может входить в несколько RCV-записей для разных состояний. Источники: [ClinVar record details](https://www.ncbi.nlm.nih.gov/clinvar/docs/details/), [ClinVar classification terms](https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/).
- `Review status` отражает уровень проверки и прозрачности представленных утверждений. Для germline-классификаций шкала включает: 0 звезд - критерии не представлены или нет классификации; 1 звезда - критерии представлены одним submitter либо есть согласованные данные нескольких submitter; 2 звезды - согласованные классификации нескольких submitter с критериями; 3 звезды - expert panel; 4 звезды - practice guideline. Конфликтующие представления не получают консенсусный двухзвездочный статус. Источник: [Review status in ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/).
- ClinVar сообщает представленные клинические утверждения и рассчитанные молекулярные последствия, но не заменяет самостоятельную клиническую интерпретацию и не доказывает функциональный эффект. Источник: [ClinVar record details](https://www.ncbi.nlm.nih.gov/clinvar/docs/details/).

## gnomAD

- gnomAD v4 использует GRCh38; это соответствует сборке исходного VCF. Релиз v4 включает объединенные данные крупных exome- и genome-проектов. Источник: [gnomAD v4.0](https://gnomad.broadinstitute.org/news/2023-11-gnomad-v4-0/).
- Allele frequency определяется как число копий альтернативного аллеля (`AC`), деленное на число исследованных хромосом (`AN`). Для таблицы следует указывать dataset/release и общий AF, а при клиническом обсуждении учитывать максимальную частоту по ancestry group, если она существенно отличается. Источник: [gnomAD Genetic Ancestry](https://gnomad.broadinstitute.org/news/2023-11-genetic-ancestry/).
- Отсутствие варианта в gnomAD не равно нулевой частоте и не доказывает патогенность. Если `AN = 0`, частота неизвестна; браузер показывает прочерк, а не ноль. Источник: [Population frequency display modified](https://gnomad.broadinstitute.org/news/2023-08-modify-population-frequency-table/).
- Частоты зависят от покрытия, качества вызова, состава выборки и представленности ancestry groups. Нужно проверять `FILTER`, покрытие и возможные технические флаги. В gnomAD v4.1.1 отдельно отмечены гены с низким exome coverage или плохой mappability, где частоты и constraint-метрики могут быть ненадежны. Источник: [gnomAD v4.1.1](https://gnomad.broadinstitute.org/news/2026-03-gnomad-v4-1-1/).
- На дату доступа актуальное изменение v4.1.2 затрагивает ранги gene constraint, но не variant frequency и filtering status; для этой работы частотные поля остаются сопоставимыми с v4.1.1. Источник: [gnomAD changelog](https://gnomad.broadinstitute.org/news/changelog/).

## Ограничения совместного использования баз

- VEP, ClinVar и gnomAD отвечают на разные вопросы: VEP прогнозирует молекулярное последствие, ClinVar агрегирует клинические утверждения, gnomAD сообщает наблюдаемую популяционную частоту. Ни один источник отдельно не определяет клиническую патогенность.
- Сведения меняются со временем. Для воспроизводимости в результатах нужно сохранить дату доступа, сборку генома, версии/release и исходные экспорты.
- При расхождении источников приоритет следует отдавать корректному сопоставлению `CHROM:POS:REF:ALT` на GRCh38, затем проверять транскрипт, condition-specific ClinVar assertions, review status и качество частот gnomAD.

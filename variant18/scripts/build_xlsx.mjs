import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = new URL("../", import.meta.url);
const inputPath = new URL("results/tables/variants_annotated.tsv", root);
const outputPath = new URL("results/tables/variants_annotated.xlsx", root);
const previewPath = new URL("results/tables/variants_annotated_preview.png", root);

const text = await fs.readFile(inputPath, "utf8");
const lines = text.replace(/^\uFEFF/, "").trimEnd().split(/\r?\n/);
const sourceHeaders = lines[0].split("\t");
const sourceRows = lines.slice(1).map((line) => line.split("\t"));

const columns = [
  ["variant", "Вариант"],
  ["chromosome", "Хромосома"],
  ["position_grch38", "Позиция GRCh38"],
  ["ref", "REF"],
  ["alt", "ALT"],
  ["rsid", "rsID"],
  ["gene", "Ген"],
  ["most_severe_consequence", "Наиболее значимое последствие VEP"],
  ["impact", "IMPACT"],
  ["selected_transcript", "Выбранный транскрипт"],
  ["transcript_selection_rule", "Правило выбора транскрипта"],
  ["hgvsc", "HGVSc"],
  ["hgvsp", "HGVSp"],
  ["sift", "SIFT"],
  ["polyphen", "PolyPhen"],
  ["gnomad_exomes_af", "gnomAD exomes AF"],
  ["gnomad_genomes_af", "gnomAD genomes AF"],
  ["clinvar_present", "ClinVar"],
  ["clinvar_significance", "ClinVar significance"],
  ["clinvar_review_status", "ClinVar review status"],
  ["clinvar_accession_and_traits", "ClinVar accession и состояния"],
];

const indices = new Map(sourceHeaders.map((name, index) => [name, index]));
const numericKeys = new Set([
  "chromosome",
  "position_grch38",
  "gnomad_exomes_af",
  "gnomad_genomes_af",
]);
const rows = sourceRows.map((sourceRow) =>
  columns.map(([key]) => {
    const raw = sourceRow[indices.get(key)] ?? "";
    if (numericKeys.has(key) && raw !== "") return Number(raw);
    return raw;
  }),
);

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Аннотация");
sheet.showGridLines = false;
sheet.getRange("A1:U51").values = [columns.map(([, label]) => label), ...rows];

const used = sheet.getRange("A1:U51");
used.format.font = { name: "Arial", size: 10, color: "#222222" };
used.format.verticalAlignment = "center";

const header = sheet.getRange("A1:U1");
header.format = {
  fill: "#3F4E5E",
  font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "all", style: "thin", color: "#FFFFFF" },
};
header.format.rowHeight = 42;

sheet.getRange("A2:U51").format.borders = {
  insideHorizontal: { style: "thin", color: "#E1E4E8" },
};
sheet.getRange("B2:F51").format.horizontalAlignment = "center";
sheet.getRange("I2:I51").format.horizontalAlignment = "center";
sheet.getRange("P2:Q51").format.numberFormat = "0.000000";
sheet.getRange("R2:R51").format.horizontalAlignment = "center";
sheet.getRange("H2:U51").format.wrapText = true;
sheet.getRange("A2:U51").format.rowHeight = 48;

const widths = [20, 11, 16, 7, 7, 15, 12, 26, 10, 20, 32, 27, 28, 18, 18, 18, 19, 10, 24, 30, 34];
for (let index = 0; index < widths.length; index += 1) {
  sheet.getRangeByIndexes(0, index, 51, 1).format.columnWidth = widths[index];
}

sheet.freezePanes.freezeRows(1);
sheet.freezePanes.freezeColumns(1);
const table = sheet.tables.add("A1:U51", true, "AnnotatedVariants");
table.style = "TableStyleMedium2";
table.showBandedRows = false;
table.showFilterButton = true;

sheet.getRange("S2:S51").conditionalFormats.add("containsText", {
  text: "Uncertain significance",
  format: { fill: "#FFF2CC", font: { color: "#7F6000", bold: true } },
});
sheet.getRange("S2:S51").conditionalFormats.add("containsText", {
  text: "Benign",
  format: { fill: "#E2F0D9", font: { color: "#375623" } },
});

sheet.getRange("W1:W5").values = [
  ["Источники и параметры"],
  ["Ensembl VEP REST, release 116, GRCh38, 02.11.2026"],
  ["https://rest.ensembl.org/vep/human/region"],
  ["NCBI ClinVar E-utilities, 02.11.2026"],
  ["gnomAD AF: поля gnomade и gnomadg из ответа VEP"],
];
sheet.getRange("W1").format.font = { name: "Arial", size: 10, bold: true, color: "#222222" };
sheet.getRange("W2:W5").format.font = { name: "Arial", size: 9, italic: true, color: "#555555" };
sheet.getRange("W1:W5").format.wrapText = true;
sheet.getRange("W1:W5").format.columnWidth = 42;

workbook.recalculate();

const inspection = await workbook.inspect({
  kind: "table",
  range: "Аннотация!A1:U8",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 21,
});
console.log(inspection.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({
  sheetName: "Аннотация",
  range: "A1:U12",
  scale: 1,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(fileURLToPath(outputPath));

# Saved Excel table references: observed behavior

The lab previously rejected every structured table reference. We downloaded three unmodified Apache POI XLSX fixtures plus the actual `FormulaParser.java` and `TestXSSFFormulaParser.java` source. URLs and hashes are in the adjacent SOURCES.json and `examples/public-tables/SOURCES.json`; Apache license/notice are preserved.

The actual upstream test has 19 structured-reference cases: data/headers/totals, this-row selectors, adjacent column ranges, combined headers+data, whitespace and empty `Table[]` meaning data. Its expected coordinates provide an external parser reference. Our new test asserts the independently specified Name, escaped `calc=#*#`, Number header and current-row ranges. Apache's Java tests were read, not executed.

The new resolver uses the saved table name, column metadata, range, header count and total count. It handles qualified/bare table names, unqualified references inside one containing table, `@` / `#This Row`, row selectors, column ranges and apostrophe-escaped special characters. It preserves distinct workbook identities and applies a 10,000-cell expansion bound before materialization. Special characters inside headers are not treated as worksheet separators or column operators.

Two observed differences matter for reliability:

- Microsoft's prose says `#Totals` without totals returns null, but Apache's executable test expects a reference error. The lab leaves this unresolved instead of producing an empty dependency set. `#Headers` without headers is also unresolved.
- Microsoft's prose excludes header/total rows for `#This Row`; the read Apache method's initial bounds check includes the whole table. The lab requires a data row and does not inherit that permissive bound. We do not claim complete semantic equivalence to either Excel or Apache from these tests.

[Microsoft syntax reference](https://support.microsoft.com/en-us/excel/using-structured-references-with-excel-tables), [actual Apache parser](https://github.com/apache/poi/blob/trunk/poi/src/main/java/org/apache/poi/ss/formula/FormulaParser.java), [actual Apache expected-range tests](https://github.com/apache/poi/blob/trunk/poi-ooxml/src/test/java/org/apache/poi/xssf/usermodel/TestXSSFFormulaParser.java).

Observed public files: `StructuredReferences.xlsx` resolves 9/9 formulas from 0; `evaluate_formula_with_structured_table_references.xlsx` resolves 1/1 from 0. The larger `StructuredRefs-lots-with-lookups.xlsx` fails the unchanged 20,000-populated-cell collection bound both before and after. The failure remains visible; it is not silently cropped, converted or counted as analyzed. These are real software engineering workbooks, not client audit workpapers or general field accuracy data.

The output is static potential lineage. Functions are not evaluated; caches are not evidence. All referenced columns/branches remain potential dependencies, so dynamic implicit intersection without an explicit row selector may be conservative. Missing metadata, unsupported combinations, dynamic spill/INDIRECT/OFFSET and downstream unresolved nodes remain excluded. Table extent reflects the supplied saved file, not live external refresh.
